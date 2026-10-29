#!/bin/bash
set -Eeuo pipefail
umask 077
[[ $EUID -eq 0 ]] || { echo "Ejecuta con sudo." >&2; exit 1; }
KIT_ENV="${1:?Indica el bricohams.env del kit instalado}"
URL="${2:?Indica la URL publica HTTPS sin puerto}"
[[ "$KIT_ENV" = /* && -f "$KIT_ENV" && ! -L "$KIT_ENV" ]] || {
    echo "El entorno del kit debe ser un fichero absoluto, sin enlace simbolico." >&2; exit 1;
}
[[ "$URL" =~ ^https://[a-zA-Z0-9.-]+/$ ]] || { echo "URL HTTPS no valida." >&2; exit 1; }
ETC_ENV=/etc/bricohams/bricohams.env
CONF=/etc/openwebrx/openwebrx.conf.d/22-solo-local.conf
[[ -f "$ETC_ENV" && ! -L "$ETC_ENV" && ! -L "$CONF" ]] || {
    echo "Falta el entorno instalado o hay enlaces simbolicos en los destinos." >&2; exit 1;
}
systemctl is-active --quiet openwebrx || { echo "OpenWebRX+ no esta activo." >&2; exit 1; }
nginx -t
curl --fail --silent --show-error --max-time 20 "${URL}status.json" >/dev/null
B="/var/backups/bricohams/backend-local-$(date +%Y%m%d-%H%M%S)-$$"
install -d -m 700 "$B"
printf '%s\n' "${ETC_ENV#/}" "${KIT_ENV#/}" >"$B/presentes.txt"
if [[ -f "$CONF" ]]; then
    printf '%s\n' "${CONF#/}" >>"$B/presentes.txt"
else
    touch "$B/conf-ausente"
fi
cat >"$B/RESTAURAR.sh" <<'EOF'
#!/bin/bash
set -Eeuo pipefail
B="$(cd "$(dirname "$0")" && pwd)"
sha256sum -c "$B/previo.tar.gz.sha256"
tar --acls --xattrs -xzf "$B/previo.tar.gz" -C /
if [[ -f "$B/conf-ausente" ]]; then
    rm -f /etc/openwebrx/openwebrx.conf.d/22-solo-local.conf
fi
systemctl restart openwebrx
EOF
chmod 700 "$B/RESTAURAR.sh"
bash -n "$B/RESTAURAR.sh"
tar --acls --xattrs -czf "$B/previo.tar.gz" -C / -T "$B/presentes.txt"
tar --compare --gzip --file "$B/previo.tar.gz" -C /
sha256sum "$B/previo.tar.gz" >"$B/previo.tar.gz.sha256"
sha256sum -c "$B/previo.tar.gz.sha256"
echo "BACKUP_VERIFICADO=$B"
trap 'echo "ERROR: restauracion disponible con sudo bash $B/RESTAURAR.sh" >&2' ERR
for env in "$ETC_ENV" "$KIT_ENV"; do
    sed -i -E '/^[[:space:]]*(export[[:space:]]+)?(OWRX_SOLO_LOCAL|BLINDAJE_8073)=/d' "$env"
    printf "\nOWRX_SOLO_LOCAL='yes'\nBLINDAJE_8073='cerrado'\n" >>"$env"
done
install -d -m 755 "$(dirname "$CONF")"
printf '[web]\nbind_address = 127.0.0.1\n' >"$CONF"
chmod 644 "$CONF"
systemctl restart openwebrx
listo=no
for i in {1..60}; do
    if curl --fail --silent --max-time 2 http://127.0.0.1:8073/status.json >/dev/null; then
        listo=yes
        break
    fi
    sleep 1
done
[[ "$listo" = yes ]] || { echo "El backend no responde." >&2; exit 1; }
direcciones="$(ss -Hltn 'sport = :8073' | awk '{print $4}')"
[[ "$direcciones" = "127.0.0.1:8073" ]] || { echo "El backend no esta limitado a loopback." >&2; exit 1; }
curl --fail --silent --show-error --max-time 20 "${URL}status.json" >/dev/null
echo "VERIFICADO: backend solo loopback; receptor publico por $URL"
echo "RESTAURACION: sudo bash $B/RESTAURAR.sh"
