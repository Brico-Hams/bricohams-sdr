#!/bin/bash
# Despliegue acotado; no ejecuta el instalador completo ni modifica parametros RF.
set -Eeuo pipefail
umask 077
[[ $EUID -eq 0 ]] || { echo "Ejecuta con sudo; no incluyas contrasenas en la orden." >&2; exit 1; }
KIT="$(cd "$(dirname "$0")/.." && pwd)"
KIT_ENV="${1:?Indica la ruta absoluta del bricohams.env del kit instalado}"
[[ "$KIT_ENV" = /* && -f "$KIT_ENV" ]] || exit 1
ETC_ENV=/etc/bricohams/bricohams.env
[[ ! -L "$KIT_ENV" && ! -L "$ETC_ENV" ]] || { echo "Resuelve los enlaces de configuracion antes de desplegar." >&2; exit 1; }
PY=/opt/pipx/venvs/meshtastic/bin/python
NGINX="$(readlink -f /etc/nginx/sites-enabled/bricohams-sdr)"
[[ "$NGINX" = /etc/nginx/sites-available/bricohams-sdr && -f "$ETC_ENV" && -x "$PY" ]] || exit 1
nginx -t
[[ -d /usr/share/meshtasticd/web ]] || { echo "Falta el cliente oficial." >&2; exit 1; }
"$PY" "$KIT/files/bin/bricohams-meshweb" --check --adapter "$KIT/files/meshweb/favoritos.js"
if grep -Eq 'listen .*8444' "$NGINX"; then
    echo "8444 ya configurado: revisa el estado existente antes de desplegar." >&2
    exit 1
fi
systemctl is-active --quiet meshtasticd
curl --fail --silent --insecure https://127.0.0.1:9443/ >/dev/null
DOM="$(awk '$1=="server_name" {print $2; exit}' "$NGINX")"
CERT="$(awk '$1=="ssl_certificate" {gsub(/;/,"",$2); print $2; exit}' "$NGINX")"
KEY="$(awk '$1=="ssl_certificate_key" {gsub(/;/,"",$2); print $2; exit}' "$NGINX")"
[[ -n "$DOM" && -f "$CERT" && -f "$KEY" ]] || exit 1
for bin in bricohams-mesh-puente bricohams-mesh-owrx bricohams-mesh-admin bricohams-owrx-botones bricohams-servicios; do
    [[ -f "$KIT/files/bin/$bin" ]] || exit 1
done
B="/var/backups/bricohams/mesh-dual-$(date +%Y%m%d-%H%M%S)-$$"
install -d -m 700 "$B"
paths=(
    usr/local/bin/bricohams-mesh-puente
    usr/local/bin/bricohams-mesh-owrx
    usr/local/bin/bricohams-mesh-admin
    usr/local/bin/bricohams-owrx-botones
    usr/local/bin/bricohams-servicios
    usr/local/bin/bricohams-meshweb
    usr/local/share/bricohams/meshweb/favoritos.js
    usr/share/meshtasticd/web/index.html
    etc/systemd/system/bricohams-mesh-puente.service
    etc/bricohams/bricohams.env
    "${KIT_ENV#/}"
    "${NGINX#/}"
    usr/lib/python3/dist-packages/htdocs/settings.html
    usr/lib/python3/dist-packages/htdocs/css/admin.css
    usr/lib/python3/dist-packages/htdocs/css/login.css
    usr/lib/python3/dist-packages/htdocs/css/openwebrx-header.css
    run/bricohams-mesh/mesh.json
    run/bricohams-mesh/chat.json
)
: >"$B/presentes.txt"
: >"$B/ausentes.txt"
for p in "${paths[@]}"; do
    if [[ -f "/$p" ]]; then echo "$p" >>"$B/presentes.txt"; else echo "$p" >>"$B/ausentes.txt"; fi
done
for svc in bricohams-mesh-puente bricohams-mesh-owrx bricohams-mesh-admin; do
    activo=no; habilitado=no
    systemctl is-active --quiet "$svc" && activo=yes
    systemctl is-enabled --quiet "$svc" && habilitado=yes
    printf '%s %s %s\n' "$svc" "$activo" "$habilitado"
done >"$B/servicios.txt"
cat >"$B/RESTAURAR.sh" <<'EOF'
#!/bin/bash
set -Eeuo pipefail
B="$(cd "$(dirname "$0")" && pwd)"
sha256sum -c "$B/previo.tar.gz.sha256"
for svc in bricohams-mesh-owrx bricohams-mesh-puente bricohams-mesh-admin; do
    if systemctl cat "$svc" >/dev/null 2>&1; then systemctl stop "$svc"; fi
done
tar --acls --xattrs -xzf "$B/previo.tar.gz" -C /
if grep -qx 'etc/systemd/system/bricohams-mesh-puente.service' "$B/ausentes.txt" &&
    systemctl cat bricohams-mesh-puente >/dev/null 2>&1; then
    systemctl disable bricohams-mesh-puente
fi
while IFS= read -r p; do
    case "$p" in
        usr/local/bin/bricohams-mesh-puente|etc/systemd/system/bricohams-mesh-puente.service|usr/local/bin/bricohams-meshweb|usr/local/share/bricohams/meshweb/favoritos.js)
            rm -f -- "/$p" ;;
    esac
done <"$B/ausentes.txt"
systemctl daemon-reload
while read -r svc activo habilitado; do
    if [[ "$habilitado" = yes ]]; then systemctl enable "$svc"; else
        if systemctl cat "$svc" >/dev/null 2>&1; then systemctl disable "$svc"; fi
    fi
    if [[ "$activo" = yes ]]; then systemctl start "$svc"; fi
done <"$B/servicios.txt"
nginx -t
systemctl reload nginx
EOF
chmod 700 "$B/RESTAURAR.sh"
bash -n "$B/RESTAURAR.sh"
# El historial RAM cambia mientras esta en marcha; se guarda separado y no se compara.
grep -v '^run/' "$B/presentes.txt" >"$B/estables.txt"
tar --acls --xattrs -czf "$B/previo.tar.gz" -C / -T "$B/estables.txt"
tar --compare --gzip --file "$B/previo.tar.gz" -C /
if [[ -f /run/bricohams-mesh/chat.json ]]; then
    cp -p /run/bricohams-mesh/chat.json "$B/chat-previo.json"
    sha256sum "$B/chat-previo.json" >"$B/chat-previo.json.sha256"
    sha256sum -c "$B/chat-previo.json.sha256"
fi
sha256sum "$B/previo.tar.gz" >"$B/previo.tar.gz.sha256"
sha256sum -c "$B/previo.tar.gz.sha256"
echo "BACKUP_VERIFICADO=$B"
trap 'echo "DESPLIEGUE INCOMPLETO. Restauracion: sudo bash $B/RESTAURAR.sh" >&2' ERR
systemctl stop bricohams-mesh-owrx bricohams-mesh-admin
for bin in bricohams-mesh-puente bricohams-mesh-owrx bricohams-mesh-admin bricohams-owrx-botones bricohams-servicios; do
    install -m 755 "$KIT/files/bin/$bin" "/usr/local/bin/$bin"
done
install -m 644 "$KIT/files/systemd/bricohams-mesh-puente.service" /etc/systemd/system/bricohams-mesh-puente.service
install -m 755 "$KIT/files/bin/bricohams-meshweb" /usr/local/bin/bricohams-meshweb
install -d /usr/local/share/bricohams/meshweb
install -m 644 "$KIT/files/meshweb/favoritos.js" /usr/local/share/bricohams/meshweb/favoritos.js
/usr/local/bin/bricohams-meshweb
BRICOHAMS_KIT_ENV="$KIT_ENV" "$PY" - <<'PY'
import importlib.machinery
import importlib.util
ldr = importlib.machinery.SourceFileLoader('admin', '/usr/local/bin/bricohams-mesh-admin')
m = importlib.util.module_from_spec(importlib.util.spec_from_loader('admin', ldr))
ldr.exec_module(m)
from meshtastic.tcp_interface import TCPInterface
i = TCPInterface(hostname='127.0.0.1', timeout=30)
try:
    url_actual = i.localNode.getURL(includeAll=True)
finally:
    i.close()
m.guardar({'MESH_WEB': 'yes', 'MESH433_WEB': 'yes', 'MESH_CHAT': 'yes',
           'MESH433_OWRX': 'yes', 'MESH868_OWRX': 'yes', 'OWRX_MAPA_LORA': 'yes',
           'MESH_CHANNEL_URL': url_actual})
PY
"$PY" - "$KIT/files/nginx/bricohams-sdr.conf.tmpl" "$NGINX" <<'PY'
from pathlib import Path
import sys
template = Path(sys.argv[1]).read_text()
inicio = template.index('#@MW@    # bricohams-favoritos-api:inicio')
fin = template.index('#@MW@    # bricohams-favoritos-api:fin')
locations = template[inicio:fin].replace('#@MW@', '')
destino = Path(sys.argv[2])
texto = destino.read_text()
if texto.count('location /api/ {') != 1:
    raise RuntimeError('No se identifica el bloque API original; no se modifica nginx')
destino.write_text(texto.replace('    location /api/ {', locations + '    location /api/ {', 1))
PY
sed -n 's/^#@M43@//p' "$KIT/files/nginx/bricohams-sdr.conf.tmpl" |
    sed -e "s#__DOMINIO__#$DOM#g" -e "s#__CERT__#$CERT#g" -e "s#__KEY__#$KEY#g" >>"$NGINX"
nginx -t
systemctl daemon-reload
systemctl enable bricohams-mesh-puente
INICIO="$("$PY" -c 'import time; print(time.time())')"
systemctl start bricohams-mesh-puente
systemctl start bricohams-mesh-owrx bricohams-mesh-admin
/usr/local/bin/bricohams-owrx-botones
systemctl reload nginx
for svc in bricohams-mesh-puente bricohams-mesh-owrx bricohams-mesh-admin; do
    systemctl is-active --quiet "$svc"
done
MESH_DESPLIEGUE_INICIO="$INICIO" "$PY" - <<'PY'
import json
import os
import time
for _ in range(60):
    try:
        with open('/run/bricohams-mesh/mesh.json') as f:
            d = json.load(f)
        nuevo = os.stat('/run/bricohams-mesh/mesh.json').st_mtime >= float(os.environ['MESH_DESPLIEGUE_INICIO'])
        if nuevo and all(d.get('fuentes', {}).get(k, {}).get('conectado') for k in ('mesh433', 'mesh868')):
            print('AMBOS_NODOS_CONECTADOS')
            break
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    time.sleep(2)
else:
    raise RuntimeError('No se conectaron ambos nodos; revisa journalctl y restaura si procede')
PY
echo "SERVICIOS_VERIFICADOS; comprueba canales y cuadro de mensajes en :8443 y :8444. No se ha enviado texto RF."
