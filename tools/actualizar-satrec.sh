#!/bin/bash
set -Eeuo pipefail
umask 077
[[ $EUID -eq 0 ]] || { echo "Ejecuta con sudo." >&2; exit 1; }
NUEVO="${1:?Ruta absoluta del kit nuevo}"
KIT="${2:?Ruta absoluta del kit instalado}"
[[ "$NUEVO" = /* && "$KIT" = /* ]] || exit 1
DESTINO=/usr/local/bin/bricohams-satrec
FUENTE="$KIT/files/bin/bricohams-satrec.py"
python3 - "$NUEVO/files/bin/bricohams-satrec.py" <<'PY'
import ast
import json
from pathlib import Path
import sys
import time
ast.parse(Path(sys.argv[1]).read_text())
base = Path('/usr/lib/python3/dist-packages/htdocs/plugins/receiver/satelites')
for nombre, clave in (('pases.json', 'pases'), ('grabaciones.json', 'plan')):
    for p in json.loads((base / nombre).read_text())[clave]:
        if p['aos'] - 60 <= time.time() <= p['los'] + 60:
            raise RuntimeError('Pase en curso o inminente: repetir al terminar.')
PY
for f in "$DESTINO" "$FUENTE"; do
    [[ -f "$f" && ! -L "$f" ]] || { echo "Destino no valido: $f" >&2; exit 1; }
done
B="/var/backups/bricohams/satrec-perfil-$(date +%Y%m%d-%H%M%S)-$$"
install -d -m 700 "$B"
printf '%s\n' "${DESTINO#/}" "${FUENTE#/}" >"$B/archivos.txt"
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
tar --acls --xattrs -xzf "$B/previo.tar.gz" -C /
systemctl restart bricohams-satrec
EOF
chmod 700 "$B/RESTAURAR.sh"
bash -n "$B/RESTAURAR.sh"
echo "BACKUP_VERIFICADO=$B"
echo "RESTAURACION: sudo bash $B/RESTAURAR.sh"
trap 'echo "ERROR: restaura con sudo bash $B/RESTAURAR.sh" >&2' ERR
install -m 755 "$NUEVO/files/bin/bricohams-satrec.py" "$DESTINO"
install -m 755 "$NUEVO/files/bin/bricohams-satrec.py" "$FUENTE"
cmp "$NUEVO/files/bin/bricohams-satrec.py" "$DESTINO"
cmp "$NUEVO/files/bin/bricohams-satrec.py" "$FUENTE"
systemctl restart bricohams-satrec
systemctl is-active --quiet bricohams-satrec
echo "Grabador actualizado: espera confirmacion del perfil. Historial y configuracion conservados."
