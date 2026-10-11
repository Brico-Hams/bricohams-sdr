#!/bin/bash
# Despliega el mapa local sin reinstalar ni reconfigurar RadarBox/MLAT.
set -euo pipefail
[[ $EUID = 0 ]] || { echo "Ejecutar con sudo" >&2; exit 1; }
KIT=$(cd "$(dirname "$0")/.." && pwd)
HTDOCS=/usr/lib/python3/dist-packages/htdocs
BACKUP="/var/backups/bricohams-mapa-$(date +%Y%m%d-%H%M%S)"
install -d -m 700 "$BACKUP"
for f in /etc/default/readsb /etc/bricohams/bricohams.env "$KIT/bricohams.env" \
         /usr/local/bin/bricohams-api /usr/local/bin/bricohams-rak-aprs \
         /usr/local/bin/bricohams-mesh-admin \
         "$HTDOCS/plugins/map/init.js" /var/lib/openwebrx/settings.json; do
    [ ! -f "$f" ] || cp -a --parents "$f" "$BACKUP/"
done
rb_hash=$(sha256sum /etc/rbfeeder.ini)
python3 - "$KIT" "${1:-}" <<'PY'
import importlib.machinery
import importlib.util
import pathlib
import re
import sys
kit = pathlib.Path(sys.argv[1])
loader = importlib.machinery.SourceFileLoader('admin', str(kit / 'files/bin/bricohams-mesh-admin'))
spec = importlib.util.spec_from_loader('admin', loader)
admin = importlib.util.module_from_spec(spec)
loader.exec_module(admin)
e = admin.leer_env(str(kit / 'bricohams.env'))
serial = sys.argv[2] or e['SERIAL_ADSB']
if not re.fullmatch(r'[A-Za-z0-9_-]+', serial):
    raise SystemExit('SERIAL_ADSB no valida')
for path in (str(kit / 'bricohams.env'), '/etc/bricohams/bricohams.env'):
    admin.escribir_env(path, {'SERIAL_ADSB': serial, 'RAK_OWRX_CHAT': e.get('RAK_OWRX_CHAT', 'yes')})
p = pathlib.Path('/etc/default/readsb')
s = p.read_text()
s, n = re.subn(r'(--device\s+)[A-Za-z0-9_-]+', lambda m: m[1] + serial, s)
if n != 1:
    raise SystemExit('readsb: no encuentro un unico selector --device; no se modifica')
p.write_text(s)
print('readsb: USB seleccionado ' + serial)
PY
install -m 755 "$KIT/files/bin/bricohams-api.py" /usr/local/bin/bricohams-api
install -m 755 "$KIT/files/bin/bricohams-rak-aprs" /usr/local/bin/bricohams-rak-aprs
install -m 755 "$KIT/files/bin/bricohams-mesh-admin" /usr/local/bin/bricohams-mesh-admin
install -d "$HTDOCS/plugins/map/bricohams_live"
install -m 644 "$KIT/files/htdocs/plugins/map/init.js" "$HTDOCS/plugins/map/init.js"
install -m 644 "$KIT/files/htdocs/plugins/map/bricohams_live/bricohams_live.js" \
    "$HTDOCS/plugins/map/bricohams_live/bricohams_live.js"
install -m 644 "$KIT/files/htdocs/plugins/map/bricohams_live/bricohams_live.css" \
    "$HTDOCS/plugins/map/bricohams_live/bricohams_live.css"
python3 "$KIT/files/bin/bricohams-mqtt-settings.py" /var/lib/openwebrx/settings.json --lora --chat
chown openwebrx:openwebrx /var/lib/openwebrx/settings.json
systemctl restart readsb bricohams-api bricohams-rak-aprs bricohams-mesh-admin openwebrx
sleep 5
systemctl is-active readsb bricohams-api bricohams-rak-aprs openwebrx rbfeeder
[[ "$(sha256sum /etc/rbfeeder.ini)" = "$rb_hash" ]] || { echo "ERROR: ha cambiado rbfeeder.ini" >&2; exit 1; }
pgrep -f '/usr/bin/mlat-client' >/dev/null || { echo "MLAT no esta en marcha" >&2; exit 1; }
curl --fail --silent http://127.0.0.1:8075/bricohams/api/aviones >/dev/null
echo "Mapa activo; rbfeeder.ini intacto y MLAT en marcha. Copia: $BACKUP"
