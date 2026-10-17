#!/bin/bash
set -Eeuo pipefail
umask 077
[[ $EUID -eq 0 ]] || { echo "Ejecuta con sudo." >&2; exit 1; }
KIT="${1:?Indica la ruta absoluta del kit instalado}"
[[ "$KIT" = /* && -f "$KIT/bricohams.env" && -f "$KIT/data/satelites.json" ]] || {
    echo "Kit instalado no valido." >&2; exit 1;
}
INIT=/usr/lib/python3/dist-packages/htdocs/plugins/receiver/init.js
CATALOGO=/opt/bricohams/kit/data/satelites.json
ESTADO=/usr/lib/python3/dist-packages/htdocs/plugins/receiver/satelites/grabaciones.json
python3 - "$KIT" "$INIT" "$ESTADO" <<'PY'
import json
from pathlib import Path
import re
import sys
import time

kit, init, estado = map(Path, sys.argv[1:])
for path in [kit / "bricohams.env", kit / "install.sh", init,
             Path("/etc/bricohams/bricohams.env"),
             Path("/opt/bricohams/kit/data/satelites.json")]:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("Destino no valido: " + str(path))
data = json.loads((kit / "data/satelites.json").read_text())
required = {27607, 43017, 44909, 44881}
if not required.issubset({s["norad"] for s in data["satelites"] if s.get("amsat")}):
    raise RuntimeError("El catalogo no contiene las cuatro asociaciones AMSAT.")
now = time.time()
for p in json.loads(estado.read_text())["plan"]:
    if p["aos"] - 60 <= now <= p["los"] + 60:
        raise RuntimeError("Hay un pase en curso o inminente; repite al terminar.")
option = r"(?m)^([ \t]*tone_detector:[ \t]*)(?:true|false|'(?:yes|no)'[ \t]*===[ \t]*'yes')(?=[ \t]*,)"
if len(re.findall(option, init.read_text())) != 1:
    raise RuntimeError("No se identifica de forma unica la opcion CTCSS externa.")
PY
B="/var/backups/bricohams/satelites-ctcss-$(date +%Y%m%d-%H%M%S)-$$"
install -d -m 700 "$B"
printf '%s\n' "${INIT#/}" "${CATALOGO#/}" etc/bricohams/bricohams.env \
    "${KIT#/}/bricohams.env" "${KIT#/}/install.sh" >"$B/archivos.txt"
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
install -m 644 "$KIT/data/satelites.json" "$CATALOGO"
cmp "$KIT/data/satelites.json" "$CATALOGO"
systemctl restart bricohams-satrec
systemctl is-active --quiet bricohams-satrec
echo "Catalogo AMSAT actualizado; grabador activo. Informes automaticos sin cambios."
python3 - "$KIT" "$INIT" <<'PY'
from pathlib import Path
import re
import sys

kit, init = map(Path, sys.argv[1:])
for path in [Path("/etc/bricohams/bricohams.env"), kit / "bricohams.env"]:
    original = path.read_text()
    lines = [line for line in original.splitlines()
             if not re.match(r"^\s*(?:export\s+)?PLUGIN_TONE_DETECTOR=", line)]
    lines.append("PLUGIN_TONE_DETECTOR='no'")
    path.write_text("\n".join(lines) + "\n")
option = r"(?m)^([ \t]*tone_detector:[ \t]*)(?:true|false|'(?:yes|no)'[ \t]*===[ \t]*'yes')(?=[ \t]*,)"
text, count = re.subn(option, r"\g<1>false", init.read_text())
if count != 1:
    raise RuntimeError("No se ha actualizado la opcion unica del panel externo.")
init.write_text(text)
installer = kit / "install.sh"
text = installer.read_text()
text = text.replace('${PLUGIN_TONE_DETECTOR:-yes}', '${PLUGIN_TONE_DETECTOR:-no}')
line = '    install -D -m 644 "$KIT/data/satelites.json" /opt/bricohams/kit/data/satelites.json\n'
if line not in text:
    marker = "paso_satelites() {\n"
    if text.count(marker) != 1:
        raise RuntimeError("No se identifica el paso de satelites del instalador.")
    text = text.replace(marker, marker + line)
installer.write_text(text)
PY
bash -n "$KIT/install.sh"
if command -v node >/dev/null 2>&1; then
    node --check "$INIT"
elif command -v nodejs >/dev/null 2>&1; then
    nodejs --check "$INIT"
else
    echo "AVISO: Node.js no instalado; falta validar JavaScript en el navegador." >&2
fi
echo "Panel CTCSS externo desactivado; Subtono FM integrado intacto. Recarga la web."
