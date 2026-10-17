#!/bin/bash
set -Eeuo pipefail
umask 077
[[ $EUID -eq 0 ]] || { echo "Ejecuta con sudo." >&2; exit 1; }
NUEVO="${1:?Ruta del kit nuevo}"
KIT="${2:?Ruta del kit instalado}"
[[ "$NUEVO" = /* && "$KIT" = /* ]] || exit 1
python3 - "$NUEVO" "$KIT" <<'PY'
import ast
import json
from pathlib import Path
import sys
import time

nuevo, kit = map(Path, sys.argv[1:])
for nombre in ("bricohams-mesh-admin", "bricohams-satrec.py", "bricohams-owrx-botones"):
    ast.parse((nuevo / "files/bin" / nombre).read_text())
if not (kit / "bricohams.env").is_file():
    raise RuntimeError("Kit instalado no valido")
base = Path("/usr/lib/python3/dist-packages/htdocs/plugins/receiver/satelites")
for nombre, clave in (("pases.json", "pases"), ("grabaciones.json", "plan")):
    for p in json.loads((base / nombre).read_text())[clave]:
        if p["aos"] - 60 <= time.time() <= p["los"] + 60:
            raise RuntimeError("Pase en curso o inminente: repetir al terminar")
PY
B="/var/backups/bricohams/agendas-$(date +%Y%m%d-%H%M%S)-$$"
install -d -m 700 "$B"
for f in /usr/local/bin/bricohams-mesh-admin /usr/local/bin/bricohams-satrec \
    /usr/local/bin/bricohams-owrx-botones /etc/systemd/system/bricohams-mesh-admin.service \
    /usr/lib/python3/dist-packages/htdocs/settings.html \
    /usr/lib/python3/dist-packages/htdocs/css/admin.css \
    /usr/lib/python3/dist-packages/htdocs/css/login.css \
    /usr/lib/python3/dist-packages/htdocs/css/openwebrx-header.css \
    "$KIT/install.sh" "$KIT/files/bin/bricohams-mesh-admin" \
    "$KIT/files/bin/bricohams-satrec.py" "$KIT/files/bin/bricohams-owrx-botones"; do
    [[ -f "$f" && ! -L "$f" ]] || { echo "Destino no valido: $f" >&2; exit 1; }
    printf '%s\n' "${f#/}"
done >"$B/archivos.txt"
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
systemctl daemon-reload
systemctl restart bricohams-mesh-admin bricohams-satrec
EOF
chmod 700 "$B/RESTAURAR.sh"
bash -n "$B/RESTAURAR.sh"
echo "BACKUP_VERIFICADO=$B"
echo "RESTAURACION: sudo bash $B/RESTAURAR.sh"
trap 'echo "ERROR: restaura con sudo bash $B/RESTAURAR.sh" >&2' ERR
install -m 755 "$NUEVO/files/bin/bricohams-mesh-admin" /usr/local/bin/bricohams-mesh-admin
install -m 755 "$NUEVO/files/bin/bricohams-satrec.py" /usr/local/bin/bricohams-satrec
install -m 755 "$NUEVO/files/bin/bricohams-owrx-botones" /usr/local/bin/bricohams-owrx-botones
for f in bricohams-mesh-admin bricohams-satrec.py bricohams-owrx-botones; do
    install -m 755 "$NUEVO/files/bin/$f" "$KIT/files/bin/$f"
done
python3 - "$KIT" <<'PY'
from pathlib import Path
import sys
kit = Path(sys.argv[1])
line = "ReadWritePaths=-/var/backups/bricohams\n"
for path in (Path("/etc/systemd/system/bricohams-mesh-admin.service"), kit / "install.sh"):
    text = path.read_text()
    if line not in text:
        lines = text.splitlines(keepends=True)
        indexes = [i for i, s in enumerate(lines) if s.startswith("ReadWritePaths=/etc/bricohams ")]
        if len(indexes) != 1:
            raise RuntimeError("No se identifica ReadWritePaths: " + str(path))
        lines.insert(indexes[0] + 1, line)
        path.write_text("".join(lines))
PY
bash -n "$KIT/install.sh"
/usr/local/bin/bricohams-owrx-botones
systemctl daemon-reload
systemctl restart bricohams-mesh-admin bricohams-satrec
systemctl is-active --quiet bricohams-mesh-admin bricohams-satrec
echo "Settings: paneles satelites/agendas y clima instalados. Sin cambios RF ni AMSAT."
