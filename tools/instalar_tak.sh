#!/bin/bash
# OpenTAKServer independiente: no sustituye nginx ni los servicios del SDR.
set -euo pipefail
umask 077
trap 'printf "TAK: fallo en la linea %s\n" "$LINENO" >&2' ERR
[[ $(id -u) = 0 ]] || { echo "Ejecuta con sudo bash tools/instalar_tak.sh" >&2; exit 1; }
BASE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# IP/LAN/ciudad/usuarios: variables TAK_* o bricohams.env (si existe); si no, se detectan.
ENVF=${BRICOHAMS_ENV:-/etc/bricohams/bricohams.env}
# shellcheck source=/dev/null
if [[ -r $ENVF ]]; then set -a; . "$ENVF"; set +a; fi
IP=${TAK_IP:-$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<NF;i++) if($i=="src"){print $(i+1); exit}}')}
LAN=${TAK_LAN:-$(ip -4 -o addr show | awk -v ip="$IP" '$4 ~ "^"ip"/" {print $4; exit}')}
[[ -n $IP && -n $LAN ]] || { echo "No se pudo detectar la IP/LAN: define TAK_IP y TAK_LAN" >&2; exit 1; }
LAN=$(python3 -c 'import ipaddress,sys; print(ipaddress.ip_network(sys.argv[1], strict=False))' "$LAN")
export TAK_IP_REAL=$IP TAK_CIUDAD=${TAK_CA_CITY:-${STATION_QTH:-QTH}} TAK_ESTADO=${TAK_CA_STATE:-Espana}
export TAK_ADMIN_USER=${TAK_ADMIN_USER:-admin} TAK_USER=${TAK_USER:-tak}
# OpenTAKServer (UsernameValidator) solo admite letras, numeros, '_' y '.': un guion impide el login.
for _u in "$TAK_ADMIN_USER" "$TAK_USER"; do
    [[ $_u =~ ^[A-Za-z0-9_.]{1,64}$ ]] || { echo "Usuario TAK invalido '$_u': usa solo letras, numeros, '_' o '.' (sin guiones)" >&2; exit 1; }
done
HOME_TAK=/var/lib/bricohams-tak
VENV=/opt/bricohams-tak/venv312
CONFIG=$HOME_TAK/ots/config.yml
[[ $(uname -m) = aarch64 ]] || { echo "Instalacion verificada para ARM64" >&2; exit 1; }
ip -4 addr show | grep -Fq "inet $IP/" || { echo "La IP $IP no pertenece al servidor" >&2; exit 1; }

install -d -m 755 /etc/bricohams /opt/bricohams-tak
cat >/etc/bricohams/tak-fw.nft <<EOF
table inet bricohams_tak
delete table inet bricohams_tak
table inet bricohams_tak {
    chain input {
        type filter hook input priority -20; policy accept;
        iifname "lo" accept
        tcp dport { 4369, 5672, 15672, 25672, 5432, 8081 } drop
        ip saddr $LAN tcp dport { 8089, 8445, 8446, 8447 } accept
        tcp dport { 8087, 8088, 8089, 8445, 8446, 8447 } drop
        udp dport 8087 drop
    }
}
EOF
nft -c -f /etc/bricohams/tak-fw.nft
nft -f /etc/bricohams/tak-fw.nft
cat >/etc/systemd/system/bricohams-tak-fw.service <<'EOF'
[Unit]
Description=BricoHams TAK LAN isolation
Before=rabbitmq-server.service postgresql.service bricohams-tak.service bricohams-tak-cot.service bricohams-tak-ssl.service nginx.service
[Service]
Type=oneshot
ExecStart=/usr/sbin/nft -f /etc/bricohams/tak-fw.nft
RemainAfterExit=yes
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now bricohams-tak-fw.service
export DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=l
apt-get update
apt-get install -y --no-install-recommends python3-venv python3-dev build-essential libpq-dev rabbitmq-server postgresql openssl unzip curl
id opentakserver >/dev/null 2>&1 || useradd --system --create-home --home-dir "$HOME_TAK" --shell /usr/sbin/nologin opentakserver
install -d -o opentakserver -g opentakserver -m 750 "$HOME_TAK/ots"
umask 022
BOOTSTRAP=/opt/bricohams-tak/venv
[[ -x $BOOTSTRAP/bin/python ]] || python3 -m venv "$BOOTSTRAP"
"$BOOTSTRAP/bin/pip" install uv==0.13.0
export UV_PYTHON_INSTALL_DIR=/opt/bricohams-tak/python
"$BOOTSTRAP/bin/uv" python install 3.12
[[ -x $VENV/bin/python ]] || "$BOOTSTRAP/bin/uv" venv --seed --python 3.12 "$VENV"
"$VENV/bin/pip" install -r "$BASE/tak-requirements.txt"
"$VENV/bin/pip" check
chmod -R a+rX "$VENV"
umask 077
install -m 644 "$BASE/tak-requirements.txt" /opt/bricohams-tak/requirements.txt

# RabbitMQ dedicado a TAK. No se reemplaza una configuracion ajena.
install -d -m 755 /etc/rabbitmq/conf.d
cat >/etc/rabbitmq/conf.d/90-bricohams-tak.conf <<'EOF'
listeners.tcp.1 = 127.0.0.1:5672
distribution.listener.interface = 127.0.0.1
loopback_users.guest = true
EOF
chmod 644 /etc/rabbitmq/conf.d/90-bricohams-tak.conf
systemctl enable --now rabbitmq-server postgresql
systemctl restart rabbitmq-server
runuser -u postgres -- psql -v ON_ERROR_STOP=1 <<'SQL'
SELECT 'CREATE ROLE opentakserver LOGIN'
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'opentakserver') \gexec
SELECT 'CREATE DATABASE bricohams_tak OWNER opentakserver'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'bricohams_tak') \gexec
SQL

if [[ ! -e $CONFIG ]]; then
    runuser -u opentakserver -- env HOME="$HOME_TAK" TAK_IP_REAL="$TAK_IP_REAL" TAK_CIUDAD="$TAK_CIUDAD" TAK_ESTADO="$TAK_ESTADO" "$VENV/bin/python" - <<'PY'
import os
import re
import secrets
from pathlib import Path

import yaml
from opentakserver.defaultconfig import DefaultConfig

config = {
    key: value
    for key, value in vars(DefaultConfig).items()
    if key.isupper() and key != "OTS_LANGUAGES"
}
config.update(
    OTS_LISTENER_ADDRESS="127.0.0.1",
    OTS_LISTENER_PORT=8081,
    OTS_STREAMING_INTERFACE=os.environ["TAK_IP_REAL"],
    OTS_ENABLE_TCP_STREAMING_PORT=False,
    OTS_SSL_STREAMING_PORT=8089,
    OTS_MARTI_HTTPS_PORT=8447,
    OTS_CERTIFICATE_ENROLLMENT_PORT=8446,
    OTS_MEDIAMTX_ENABLE=False,
    OTS_ENABLE_MESHTASTIC=False,
    OTS_ENABLE_MUMBLE_AUTHENTICATION=False,
    OTS_ENABLE_EMAIL=False,
    OTS_ENABLE_PLUGINS=False,
    OTS_CA_NAME="BricoHams-TAK-CA",
    OTS_CA_PASSWORD=secrets.token_hex(16),
    OTS_CA_COUNTRY="ES",
    OTS_CA_STATE=re.sub(r"[^A-Za-z0-9 .-]", "", os.environ["TAK_ESTADO"]) or "ES",
    OTS_CA_CITY=re.sub(r"[^A-Za-z0-9 .-]", "", os.environ["TAK_CIUDAD"]) or "QTH",
    OTS_CA_ORGANIZATION="BricoHams",
    OTS_CA_SUBJECT="/C=ES/O=BricoHams/OU=TAK",
    OTS_CA_EXPIRATION_TIME=825,
    OTS_LOG_ROTATE_INTERVAL=1,
    SQLALCHEMY_DATABASE_URI="postgresql+psycopg:///bricohams_tak",
    SESSION_COOKIE_SECURE=True,
    REMEMBER_COOKIE_SECURE=True,
    DEBUG=False,
)
path = Path.home() / "ots" / "config.yml"
path.write_text(yaml.safe_dump(config), encoding="utf-8")
path.chmod(0o600)
PY
fi
run_tak() { runuser -u opentakserver -- env HOME="$HOME_TAK" TAK_ADMIN_USER="$TAK_ADMIN_USER" TAK_USER="$TAK_USER" FLASK_APP=opentakserver.app "$@"; }
cd "$HOME_TAK/ots"
run_tak "$VENV/bin/flask" db upgrade --directory "$VENV"/lib/python*/site-packages/opentakserver/migrations
run_tak "$VENV/bin/flask" ots create-ca

if [[ ! -e /etc/bricohams/tak-access.txt ]]; then
    install -o opentakserver -g opentakserver -m 600 /dev/null "$HOME_TAK/ots/access.txt"
    run_tak "$VENV/bin/python" - <<'PY'
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path

from flask_security import hash_password
from opentakserver.app import create_app
from opentakserver.extensions import db

app = create_app()
with app.app_context():
    app.security.datastore.find_or_create_role(
        name="user", permissions={"user-read", "user-write"}
    )
    app.security.datastore.find_or_create_role(
        name="administrator", permissions={"administrator"}
    )
    credentials = []
    for username, role in ((os.environ.get("TAK_ADMIN_USER", "admin"), "administrator"), (os.environ.get("TAK_USER", "tak"), "user")):
        if app.security.datastore.find_user(username=username):
            raise RuntimeError(f"Ya existe {username}; no se cambia su clave")
        password = secrets.token_urlsafe(24)
        app.security.datastore.create_user(
            username=username, password=hash_password(password), roles=[role], active=True,
            # OpenTAKServer exige cuenta confirmada: sin esto el login responde 400
            confirmed_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        credentials.append(f"{username}: {password}")
    db.session.commit()
    (Path.home() / "ots" / "access.txt").write_text(
        "\n".join(credentials) + "\n", encoding="utf-8"
    )
PY
    install -o root -g root -m 600 "$HOME_TAK/ots/access.txt" /etc/bricohams/tak-access.txt
    rm -- "$HOME_TAK/ots/access.txt"
fi

CA=$HOME_TAK/ots/ca
CERT=$CA/certs/opentakserver
if ! openssl x509 -in "$CERT/opentakserver.pem" -noout -checkip "$IP" | grep -Fq "does match certificate"; then
    cat >"$CERT/lan-cert.cfg" <<EOF
[server]
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth,clientAuth
subjectAltName=IP:$IP,DNS:sdr.local,DNS:opentakserver
EOF
    chmod 644 "$CERT/lan-cert.cfg"
    run_tak "$VENV/bin/python" - <<'PY'
import secrets
import subprocess
from pathlib import Path

import yaml

config = yaml.safe_load((Path.home() / "ots" / "config.yml").read_text())
ca = Path(config["OTS_CA_FOLDER"])
cert = ca / "certs" / "opentakserver"
subprocess.run(
    [
        "openssl", "x509", "-req", "-sha256", "-days", "825",
        "-in", str(cert / "opentakserver.csr"),
        "-CA", str(ca / "ca.pem"), "-CAkey", str(ca / "ca-do-not-share.key"),
        "-passin", "stdin", "-set_serial", "0x" + secrets.token_hex(16),
        "-out", str(cert / "opentakserver.pem"),
        "-extensions", "server", "-extfile", str(cert / "lan-cert.cfg"),
    ],
    input=config["OTS_CA_PASSWORD"] + "\n", text=True, check=True,
)
PY
fi
install -d -o root -g root -m 700 /etc/bricohams/tak-tls
install -m 644 "$CA/ca.pem" /etc/bricohams/tak-tls/ca.pem
install -m 644 "$CERT/opentakserver.pem" /etc/bricohams/tak-tls/server.pem
install -m 600 "$CERT/opentakserver.nopass.key" /etc/bricohams/tak-tls/server.key
openssl verify -CAfile "$CA/ca.pem" "$CERT/opentakserver.pem"
openssl x509 -in "$CERT/opentakserver.pem" -noout -checkip "$IP" | grep -F "does match certificate"

if [[ ! -e /var/www/bricohams-tak/index.html ]]; then
    TMP=$(mktemp -d /tmp/bricohams-tak-ui.XXXXXX)
    curl --fail --location --retry 3 https://github.com/brian7704/OpenTAKServer-UI/releases/download/v1.7.5/OpenTAKServer-UI-v1.7.5.zip -o "$TMP/ui.zip"
    echo "d1b1a604bd8d8980fee3be6ca642a6597522487716e9573b6d0b35e8ee88bbd4  $TMP/ui.zip" | sha256sum -c -
    unzip -q "$TMP/ui.zip" -d "$TMP/ui"
    [[ -e $TMP/ui/opentakserver/index.html ]] || { echo "Estructura del cliente web inesperada" >&2; exit 1; }
    install -d -m 755 /var/www/bricohams-tak
    cp -a "$TMP/ui/opentakserver/." /var/www/bricohams-tak/
    chown -R root:root /var/www/bricohams-tak
    find /var/www/bricohams-tak -type d -exec chmod 755 {} +
    find /var/www/bricohams-tak -type f -exec chmod 644 {} +
    find "$TMP" -depth -delete
fi

run_tak "$VENV/bin/python" - <<'PY'
import pika

with pika.BlockingConnection(pika.ConnectionParameters(host="127.0.0.1")) as connection:
    connection.channel().exchange_declare("cot_parser", durable=True, exchange_type="direct")
PY

for name in bricohams-tak bricohams-tak-cot bricohams-tak-ssl; do
    case "$name" in
        bricohams-tak) COMMAND="$VENV/bin/opentakserver"; DEPENDENCIES="bricohams-tak-cot.service bricohams-tak-ssl.service" ;;
        bricohams-tak-cot) COMMAND="$VENV/bin/cot_parser"; DEPENDENCIES="" ;;
        bricohams-tak-ssl) COMMAND="$VENV/bin/eud_handler --ssl"; DEPENDENCIES="" ;;
    esac
    cat >"/etc/systemd/system/$name.service" <<EOF
[Unit]
Description=$name OpenTAKServer
Wants=network-online.target
After=network-online.target rabbitmq-server.service postgresql.service bricohams-tak-fw.service
Requires=rabbitmq-server.service postgresql.service bricohams-tak-fw.service $DEPENDENCIES
[Service]
User=opentakserver
Group=opentakserver
Environment=HOME=$HOME_TAK
WorkingDirectory=$HOME_TAK/ots
ExecStart=$COMMAND
Restart=always
RestartSec=5
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$HOME_TAK
MemoryMax=2G
CPUQuota=150%
[Install]
WantedBy=multi-user.target
EOF
done

cat >/etc/nginx/sites-available/bricohams-tak.conf <<EOF
server {
    listen $IP:8445 ssl;
    server_name $IP sdr.local;
    ssl_certificate /etc/bricohams/tak-tls/server.pem;
    ssl_certificate_key /etc/bricohams/tak-tls/server.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    allow $LAN;
    allow 127.0.0.1;
    deny all;
    root /var/www/bricohams-tak;
    index index.html;
    client_max_body_size 100M;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Robots-Tag noindex always;
    location /Marti { return 404; }
    location /api {
        proxy_pass http://127.0.0.1:8081;
        proxy_cache off;
        proxy_hide_header Cache-Control;
        add_header Cache-Control "no-store" always;
        add_header X-Content-Type-Options nosniff always;
        add_header X-Robots-Tag noindex always;
        proxy_set_header Host \$http_host;
        proxy_set_header X-Forwarded-For \$remote_addr;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Ssl-Cert "";
    }
    location /socket.io {
        proxy_pass http://127.0.0.1:8081;
        proxy_cache off;
        proxy_hide_header Cache-Control;
        add_header Cache-Control "no-store" always;
        add_header X-Content-Type-Options nosniff always;
        add_header X-Robots-Tag noindex always;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$http_host;
        proxy_set_header X-Forwarded-For \$remote_addr;
        proxy_set_header X-Ssl-Cert "";
        proxy_buffering off;
    }
    location / { try_files \$uri /index.html; }
}
server {
    listen $IP:8447 ssl;
    server_name $IP;
    ssl_certificate /etc/bricohams/tak-tls/server.pem;
    ssl_certificate_key /etc/bricohams/tak-tls/server.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_client_certificate /etc/bricohams/tak-tls/ca.pem;
    ssl_verify_client on;
    allow $LAN;
    allow 127.0.0.1;
    deny all;
    client_max_body_size 100M;
    location /Marti/api/tls { return 404; }
    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_cache off;
        proxy_hide_header Cache-Control;
        add_header Cache-Control "no-store" always;
        add_header X-Content-Type-Options nosniff always;
        add_header X-Robots-Tag noindex always;
        proxy_set_header Host \$http_host;
        proxy_set_header X-Forwarded-For \$remote_addr;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Ssl-Cert \$ssl_client_escaped_cert;
    }
}
server {
    listen $IP:8446 ssl;
    server_name $IP;
    ssl_certificate /etc/bricohams/tak-tls/server.pem;
    ssl_certificate_key /etc/bricohams/tak-tls/server.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    allow $LAN;
    allow 127.0.0.1;
    deny all;
    location /Marti/api/tls {
        proxy_pass http://127.0.0.1:8081;
        proxy_cache off;
        proxy_hide_header Cache-Control;
        add_header Cache-Control "no-store" always;
        add_header X-Content-Type-Options nosniff always;
        add_header X-Robots-Tag noindex always;
        proxy_set_header Host \$http_host;
        proxy_set_header X-Forwarded-For \$remote_addr;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Ssl-Cert "";
    }
    location /oauth {
        proxy_pass http://127.0.0.1:8081;
        proxy_cache off;
        proxy_hide_header Cache-Control;
        add_header Cache-Control "no-store" always;
        add_header X-Content-Type-Options nosniff always;
        add_header X-Robots-Tag noindex always;
        proxy_set_header Host \$http_host;
        proxy_set_header X-Forwarded-For \$remote_addr;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Ssl-Cert "";
    }
    location / { return 404; }
}
EOF
ln -sfn /etc/nginx/sites-available/bricohams-tak.conf /etc/nginx/sites-enabled/bricohams-tak.conf
nginx -t
systemctl daemon-reload
systemctl enable bricohams-tak.service bricohams-tak-cot.service bricohams-tak-ssl.service
systemctl restart bricohams-tak-cot.service bricohams-tak-ssl.service bricohams-tak.service
systemctl reload nginx
curl --fail --silent --show-error --retry 12 --retry-delay 2 --retry-connrefused \
    --cacert /etc/bricohams/tak-tls/ca.pem "https://$IP:8445/api/health"
systemctl is-active bricohams-tak.service bricohams-tak-cot.service bricohams-tak-ssl.service
# Conserva TAK en la whitelist LAN si mas adelante se aplica el blindaje general.
python3 - "$BASE/.." <<'PY'
import importlib.machinery
import importlib.util
import pathlib
import sys
kit = pathlib.Path(sys.argv[1]).resolve()
loader = importlib.machinery.SourceFileLoader('admin', str(kit / 'files/bin/bricohams-mesh-admin'))
spec = importlib.util.spec_from_loader('admin', loader)
admin = importlib.util.module_from_spec(spec)
loader.exec_module(admin)
for path in (kit / 'bricohams.env', pathlib.Path('/etc/bricohams/bricohams.env')):
    if path.exists():
        ports = admin.leer_env(str(path)).get('BLINDAJE_PUERTOS_LAN', '4403 8443 8554').split()
        for port in ('8089', '8445', '8446', '8447'):
            if port not in ports:
                ports.append(port)
        admin.escribir_env(str(path), {'BLINDAJE_PUERTOS_LAN': ' '.join(ports)})
PY
# el panel de /settings monta /var/lib/bricohams-tak escribible al arrancar: reinicio si ya corría
systemctl try-restart bricohams-mesh-admin.service 2>/dev/null || true
echo "TAK instalado. Web: https://$IP:8445"
echo "Credenciales: /settings → Servidor TAK → «Mostrar credenciales» (o sudo cat /etc/bricohams/tak-access.txt)"
