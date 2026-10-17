#!/bin/bash
set -Eeuo pipefail
umask 077
[[ $EUID -eq 0 ]] || { echo "Ejecuta con sudo." >&2; exit 1; }
KIT="${1:?Ruta absoluta del kit instalado}"
[[ "$KIT" = /* ]] || exit 1
SITE=/etc/nginx/sites-available/bricohams-sdr
TMPL="$KIT/files/nginx/bricohams-sdr.conf.tmpl"
RUTAS=/etc/nginx/snippets/bricohams-sdr-rutas.conf
RUTAS_KIT="$KIT/files/nginx/bricohams-sdr-rutas.conf"
transformar() {
python3 - "$1" "$2" <<'PY'
from pathlib import Path
import re
import sys
src, dst = map(Path, sys.argv[1:])
text = src.read_text()
old = 'limit_req_zone $binary_remote_addr zone=bh_login:10m rate=12r/m;'
new = ('map $request_method $bh_login_key {\n    default "";\n'
       '    POST $binary_remote_addr;\n}\n'
       'limit_req_zone $bh_login_key zone=bh_login_post:10m rate=12r/m;')
if old in text:
    if text.count(old) != 1:
        raise RuntimeError('Zona login ambigua')
    text = text.replace(old, new)
elif 'limit_req_zone $bh_login_key zone=bh_login:10m rate=12r/m;' in text:
    text = text.replace('zone=bh_login:10m', 'zone=bh_login_post:10m')
elif 'limit_req_zone $bh_login_key zone=bh_login_post:10m rate=12r/m;' not in text:
    raise RuntimeError('Zona login desconocida')
for prefix in ('', '#@MW@', '#@M43@'):
    if prefix:
        if prefix not in text:
            continue
        lines = text.splitlines(keepends=True)
        lines = [l for l in lines if l not in (
            prefix + '    error_page 401 = @bh_login;\n',
            prefix + '        error_page 401 = @bh_login;\n')]
        text = ''.join(lines)
        anchor = prefix + '    location / {\n'
        if text.count(anchor) != 1:
            raise RuntimeError('Location raiz desconocida: ' + prefix)
        text = text.replace(anchor, anchor + prefix + '        error_page 401 = @bh_login;\n')
    else:
        text = re.sub(r'^    error_page 401 = @bh_login;\n', '', text, flags=re.M)
        # Solo servidores Meshtastic; el receptor principal no tiene este root.
        text = re.sub(r'(    location / \{\n)(        auth_request /_bh_auth;\n'
                      r'        root /usr/share/meshtasticd/web;)',
                      r'\1        error_page 401 = @bh_login;\n\2', text)
        if src.name == 'bricohams-sdr' and text.count('        error_page 401 = @bh_login;') != 2:
            raise RuntimeError('No se identifican ambos clientes Meshtastic')
dst.write_text(text)
PY
}
[[ -f "$SITE" && ! -L "$SITE" && -f "$TMPL" && ! -L "$TMPL" ]] || exit 1
[[ -f "$RUTAS" && ! -L "$RUTAS" && -f "$RUTAS_KIT" && ! -L "$RUTAS_KIT" ]] || exit 1
TEMP="$(mktemp -d)"
trap 'rm -f -- "$TEMP/site" "$TEMP/template"; rmdir -- "$TEMP"' EXIT
transformar "$SITE" "$TEMP/site"
transformar "$TMPL" "$TEMP/template"
B="/var/backups/bricohams/login-429-$(date +%Y%m%d-%H%M%S)-$$"
install -d -m 700 "$B"
printf '%s\n' "${SITE#/}" "${TMPL#/}" "${RUTAS#/}" "${RUTAS_KIT#/}" >"$B/archivos.txt"
tar --acls --xattrs -czf "$B/previo.tar.gz" -C / -T "$B/archivos.txt"
tar --compare --gzip --file "$B/previo.tar.gz" -C /
sha256sum "$B/previo.tar.gz" >"$B/SHA256SUMS"
sha256sum -c "$B/SHA256SUMS"
cat >"$B/RESTAURAR.sh" <<'EOF'
#!/bin/bash
set -Eeuo pipefail
[[ $EUID -eq 0 ]] || exit 1
B="$(cd "$(dirname "$0")" && pwd)"
sha256sum -c "$B/SHA256SUMS"
tar --acls --xattrs -xzf "$B/previo.tar.gz" -C /
nginx -t
systemctl reload nginx
EOF
chmod 700 "$B/RESTAURAR.sh"
bash -n "$B/RESTAURAR.sh"
echo "BACKUP_VERIFICADO=$B"
echo "RESTAURACION: sudo bash $B/RESTAURAR.sh"
trap 'echo "ERROR: restaura con sudo bash $B/RESTAURAR.sh" >&2' ERR
cat "$TEMP/site" >"$SITE"
cat "$TEMP/template" >"$TMPL"
sed -i 's/zone=bh_login /zone=bh_login_post /g' "$RUTAS" "$RUTAS_KIT"
if ! nginx -t; then
    bash "$B/RESTAURAR.sh"
    echo "Configuracion rechazada y restaurada." >&2
    exit 1
fi
systemctl reload nginx
systemctl is-active --quiet nginx
for puerto in 8443 8444; do
    for intento in {1..10}; do
        estado="$(curl --max-time 5 -ksS -o /dev/null -w '%{http_code}' "https://127.0.0.1:$puerto/api/v1/fromradio")"
        [[ "$estado" == 401 ]] && break
        sleep 1
    done
    [[ "$estado" == 401 ]] || {
        echo "La recarga aun no esta confirmada: API $puerto HTTP $estado; comprueba logs nginx." >&2
        exit 1
    }
done
echo "Corregido429: API sin sesion devuelve401; login GET libre y POST protegido. Sin reiniciar OpenWebRX."
