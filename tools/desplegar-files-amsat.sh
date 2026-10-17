#!/bin/bash
set -Eeuo pipefail
umask 077
[[ $EUID -eq 0 ]] || { echo "Ejecuta con sudo." >&2; exit 1; }
NUEVO="${1:?Ruta absoluta del kit nuevo}"
KIT="${2:?Ruta absoluta del kit instalado}"
[[ "$NUEVO" = /* && "$KIT" = /* ]] || exit 1
CTRL=/usr/lib/python3/dist-packages/owrx/controllers/file.py
PATCH=/usr/local/bin/bricohams-owrx-files
HOOK=/etc/apt/apt.conf.d/99bricohams-owrx-files
python3 - "$NUEVO" "$KIT" "$CTRL" <<'PY'
import ast
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sys
import time
nuevo, kit, ctrl = map(Path, sys.argv[1:])
for nombre in ('bricohams-mesh-admin', 'bricohams-owrx-files'):
    ast.parse((nuevo / 'files/bin' / nombre).read_text())
loader = importlib.machinery.SourceFileLoader('preflight_files', str(nuevo / 'files/bin/bricohams-owrx-files'))
mod = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
loader.exec_module(mod)
mod.proteger(ctrl.read_text())
base = Path('/usr/lib/python3/dist-packages/htdocs/plugins/receiver/satelites')
for nombre, clave in (('pases.json', 'pases'), ('grabaciones.json', 'plan')):
    for p in json.loads((base / nombre).read_text())[clave]:
        if p['aos'] - 60 <= time.time() <= p['los'] + 60:
            raise RuntimeError('Pase en curso o inminente: repetir al terminar; no se ha modificado nada.')
PY
B="/var/backups/bricohams/files-amsat-$(date +%Y%m%d-%H%M%S)-$$"
install -d -m 700 "$B"
: >"$B/ausentes.txt"
for f in "$CTRL" /usr/local/bin/bricohams-mesh-admin "$KIT/install.sh" \
    "$KIT/files/bin/bricohams-mesh-admin" "$PATCH" "$HOOK" "$KIT/files/bin/bricohams-owrx-files"; do
    [[ ! -L "$f" ]] || { echo "Enlace no permitido: $f" >&2; exit 1; }
    if [[ -f "$f" ]]; then
        printf '%s\n' "${f#/}"
    elif [[ "$f" == "$PATCH" || "$f" == "$HOOK" || "$f" == "$KIT/files/bin/bricohams-owrx-files" ]]; then
        printf '%s\n' "$f" >>"$B/ausentes.txt"
    else
        echo "Destino ausente: $f" >&2; exit 1
    fi
done >"$B/archivos.txt"
tar --acls --xattrs -czf "$B/previo.tar.gz" -C / -T "$B/archivos.txt"
tar --compare --gzip --file "$B/previo.tar.gz" -C /
sha256sum "$B/previo.tar.gz" "$B/ausentes.txt" >"$B/SHA256SUMS"
sha256sum -c "$B/SHA256SUMS"
cat >"$B/RESTAURAR.sh" <<'EOF'
#!/bin/bash
set -Eeuo pipefail
[[ $EUID -eq 0 ]] || exit 1
B="$(cd "$(dirname "$0")" && pwd)"
sha256sum -c "$B/SHA256SUMS"
tar --acls --xattrs -xzf "$B/previo.tar.gz" -C /
while IFS= read -r f; do
    [[ -n "$f" && "$f" = /* && ! -d "$f" ]] || exit 1
    rm -f -- "$f"
done <"$B/ausentes.txt"
systemctl restart openwebrx bricohams-mesh-admin
EOF
chmod 700 "$B/RESTAURAR.sh"
bash -n "$B/RESTAURAR.sh"
echo "BACKUP_VERIFICADO=$B"
echo "RESTAURACION: sudo bash $B/RESTAURAR.sh"
trap 'echo "ERROR: restaura con sudo bash $B/RESTAURAR.sh" >&2' ERR
install -m 755 "$NUEVO/files/bin/bricohams-owrx-files" "$PATCH"
"$PATCH"
printf '%s\n' 'DPkg::Post-Invoke { "/usr/local/bin/bricohams-owrx-files"; };' >"$HOOK"
chmod 644 "$HOOK"
install -m 755 "$NUEVO/files/bin/bricohams-mesh-admin" /usr/local/bin/bricohams-mesh-admin
for f in bricohams-mesh-admin bricohams-owrx-files; do
    install -m 755 "$NUEVO/files/bin/$f" "$KIT/files/bin/$f"
done
python3 - "$NUEVO/install.sh" "$KIT/install.sh" <<'PY'
from pathlib import Path
import sys
src, dst = map(Path, sys.argv[1:])
lineas = src.read_text().splitlines(keepends=True)
inicio = next(i for i, x in enumerate(lineas) if 'install -m 755 "$FILES/bin/bricohams-owrx-files"' in x)
bloque = ''.join(lineas[inicio:inicio+4])
texto = dst.read_text()
if '99bricohams-owrx-files' not in texto:
    ancla = '    install -m 755 "$FILES/bin/bricohams-owrx-botones" /usr/local/bin/bricohams-owrx-botones\n'
    if texto.count(ancla) != 1:
        raise RuntimeError('No se identifica paso de instalacion de Files')
    dst.write_text(texto.replace(ancla, ancla + bloque))
PY
bash -n "$KIT/install.sh"
systemctl restart openwebrx bricohams-mesh-admin
systemctl is-active --quiet openwebrx bricohams-mesh-admin
echo "Files protegido y reportes manuales AMSAT en Settings instalados. Limpieza automatica sin cambios."
