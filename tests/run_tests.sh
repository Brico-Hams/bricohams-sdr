#!/bin/bash
# Pruebas del repositorio (en cualquier Linux con python3, node y shellcheck)
set -e
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/.."
echo "== shellcheck";  shellcheck -x -S warning install.sh files/bin/bricohams-check files/bin/bricohams-sdr-serials files/bin/bricohams-lilygo tools/*.sh tests/run_tests.sh
echo "== bash -n";     bash -n install.sh
echo "== python";      python3 -m py_compile files/bin/*.py tools/*.py hardware/antenas/sim/*.py && find . -name __pycache__ -prune -exec rm -rf {} +
echo "== javascript"
for f in files/htdocs/plugins/receiver/{solar,meteo,camara,bricohams}/*.js files/htdocs/plugins/receiver/init.js; do
    sed -e 's/__LAT__/38.08/;s/__LON__/-1.25/;s/__CAM_SNAPSHOT_SECONDS__/60/' "$f" > /tmp/bh-check.js && node --check /tmp/bh-check.js
done
echo "== pruebas"
python3 tests/test_wx_bme280.py
python3 tests/test_render_settings.py
python3 tests/test_meteo.py
python3 tests/test_caja.py
python3 tests/test_viento_lluvia.py
python3 tests/test_fan.py
python3 tests/test_v3_hardware.py
python3 tests/test_instalador_os.py
python3 tools/marcadores.py --comprobar
echo "TODO OK"
