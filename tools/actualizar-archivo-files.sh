#!/bin/bash
# Instala bricohams-archivo-files (archivo permanente de «Files» y Files con los
# 2 últimos) en una estación existente. Copia de seguridad verificada antes.
# Uso: sudo bash tools/actualizar-archivo-files.sh /ruta/kit-nuevo /ruta/kit-instalado
set -Eeuo pipefail
umask 077
[[ $EUID -eq 0 ]] || { echo "Ejecuta con sudo." >&2; exit 1; }
NUEVO="${1:?Ruta absoluta del kit nuevo}"
KIT="${2:?Ruta absoluta del kit instalado}"
[[ "$NUEVO" = /* && "$KIT" = /* ]] || exit 1
OWRX_SETTINGS="${OWRX_SETTINGS:-/var/lib/openwebrx/settings.json}"
ARCHIVO="$NUEVO/files/bin/bricohams-archivo-files.py"
SATREC="$NUEVO/files/bin/bricohams-satrec.py"
python3 - "$ARCHIVO" "$SATREC" <<'PY'
import ast
import json
from pathlib import Path
import sys
import time
for f in sys.argv[1:]:
    ast.parse(Path(f).read_text())
base = Path('/usr/lib/python3/dist-packages/htdocs/plugins/receiver/satelites')
for nombre, clave in (('pases.json', 'pases'), ('grabaciones.json', 'plan')):
    try:
        pases = json.loads((base / nombre).read_text())[clave]
    except (OSError, ValueError, KeyError):
        continue
    for p in pases:
        if p['aos'] - 120 <= time.time() <= p['los'] + 120:
            raise SystemExit('Pase en curso o inminente: repetir al terminar.')
PY

RUTAS=()
for f in /usr/local/bin/bricohams-satrec "$KIT/files/bin/bricohams-satrec.py" "$OWRX_SETTINGS" \
         /usr/local/bin/bricohams-archivo-files "$KIT/files/bin/bricohams-archivo-files.py" \
         /etc/systemd/system/bricohams-archivo-files.service /etc/systemd/system/bricohams-archivo-files.timer; do
    [[ -e "$f" ]] && RUTAS+=("${f#/}")
done
B="/var/backups/bricohams/archivo-files-$(date +%Y%m%d-%H%M%S)-$$"
install -d -m 700 "$B"
printf '%s\n' "${RUTAS[@]}" >"$B/archivos.txt"
tar --acls --xattrs -czf "$B/previo.tar.gz" -C / -T "$B/archivos.txt"
tar --compare --gzip --file "$B/previo.tar.gz" -C /
sha256sum "$B/previo.tar.gz" >"$B/previo.tar.gz.sha256"
sha256sum -c "$B/previo.tar.gz.sha256"
cat >"$B/RESTAURAR.sh" <<'EOF'
#!/bin/bash
set -Eeuo pipefail
[[ $EUID -eq 0 ]] || exit 1
B="$(cd "$(dirname "$0")" && pwd)"
sha256sum -c "$B/previo.tar.gz.sha256"
systemctl disable --now bricohams-archivo-files.timer 2>/dev/null || true
grep -qx 'etc/systemd/system/bricohams-archivo-files.timer' "$B/archivos.txt" || \
    rm -f /etc/systemd/system/bricohams-archivo-files.timer /etc/systemd/system/bricohams-archivo-files.service
tar --acls --xattrs -xzf "$B/previo.tar.gz" -C /
systemctl daemon-reload
systemctl restart bricohams-satrec openwebrx
echo "Restaurado. El archivo /var/lib/bricohams/satelites/archivo se conserva."
EOF
chmod 700 "$B/RESTAURAR.sh"
bash -n "$B/RESTAURAR.sh"
echo "BACKUP_VERIFICADO=$B"
echo "RESTAURACION: sudo bash $B/RESTAURAR.sh"
trap 'echo "ERROR: restaura con sudo bash $B/RESTAURAR.sh" >&2' ERR

install -m 755 "$ARCHIVO" /usr/local/bin/bricohams-archivo-files
install -m 755 "$SATREC" /usr/local/bin/bricohams-satrec
if [[ -d "$KIT/files/bin" ]]; then
    install -m 755 "$ARCHIVO" "$KIT/files/bin/bricohams-archivo-files.py"
    install -m 755 "$SATREC" "$KIT/files/bin/bricohams-satrec.py"
else
    echo "AVISO: $KIT/files/bin no existe; solo se actualizan los ejecutables de /usr/local/bin"
fi
cat >/etc/systemd/system/bricohams-archivo-files.service <<'EOF'
[Unit]
Description=BricoHams: archiva los ficheros de Files (satélites, SSTV, FAX, MP3) y deja los últimos

[Service]
Type=oneshot
User=openwebrx
StateDirectory=bricohams/satelites
Environment="ARCHIVO_DIR=/var/lib/bricohams/satelites/archivo" "ARCHIVO_FILES_ULTIMOS=2"
Environment="ARCHIVO_MIN_LIBRE_MB=500"
ExecStart=/usr/local/bin/bricohams-archivo-files
EOF
cat >/etc/systemd/system/bricohams-archivo-files.timer <<'EOF'
[Unit]
Description=BricoHams: archivo de Files cada minuto

[Timer]
OnBootSec=2min
OnUnitActiveSec=1min
AccuracySec=10s

[Install]
WantedBy=timers.target
EOF

# keep_files de OpenWebRX+ como red de seguridad (con 2, SatDump perdería imágenes antes de archivarlas)
REINICIAR_OWRX=no
if [[ -f "$OWRX_SETTINGS" ]]; then
    REINICIAR_OWRX=$(python3 - "$OWRX_SETTINGS" <<'PY'
import json, os, sys
p = sys.argv[1]
d = json.load(open(p, encoding='utf-8'))
if int(d.get('keep_files', 20)) >= 100:
    print('no')
else:
    d['keep_files'] = 100
    st = os.stat(p)
    tmp = p + '.bricohams-tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=4, ensure_ascii=False)
    os.chown(tmp, st.st_uid, st.st_gid)
    os.chmod(tmp, st.st_mode & 0o7777)
    os.replace(tmp, p)
    print('yes')
PY
)
fi

systemctl daemon-reload
systemctl restart bricohams-satrec
systemctl is-active --quiet bricohams-satrec
[[ "$REINICIAR_OWRX" = yes ]] && { echo "keep_files -> 100: reiniciando OpenWebRX+ (breve desconexión)"; systemctl restart openwebrx; }
sudo -u openwebrx env ARCHIVO_FILES_ULTIMOS=2 /usr/local/bin/bricohams-archivo-files --simular || true
systemctl enable --now bricohams-archivo-files.timer
systemctl start bricohams-archivo-files.service || echo "AVISO: la primera pasada informó de errores (ver registro)."
journalctl -u bricohams-archivo-files -n 15 --no-pager || true
systemctl is-active --quiet bricohams-archivo-files.timer
echo "Archivo: /var/lib/bricohams/satelites/archivo · Files deja los 2 últimos (+2 de satrec)."
