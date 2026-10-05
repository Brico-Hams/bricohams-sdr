#!/bin/bash
# Pruebas del repositorio (en cualquier Linux con python3, node y shellcheck)
set -e
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/.."
echo "== shellcheck";  shellcheck -x -S warning install.sh files/bin/bricohams-check files/bin/bricohams-sdr-serials files/bin/bricohams-lilygo files/bin/bricohams-ft2 files/bin/bricohams-servicios files/bin/bricohams-tarea files/bin/bricohams-telegram owrx-clone/instalar.sh tools/*.sh tests/run_tests.sh
echo "== bash -n";     bash -n install.sh
echo "== python";      python3 -m py_compile files/bin/*.py files/bin/bricohams-ft2-decode owrx-clone/owrx-clone tools/*.py hardware/antenas/sim/*.py firmware/pico-io/main.py && find . -name __pycache__ -prune -exec rm -rf {} +
echo "== javascript"
for f in files/htdocs/plugins/receiver/{solar,meteo,camara,bricohams,banderas,dvficha,satelites,visitas,audio_cadena,filtro_audio,dsp_audio}/*.js files/htdocs/plugins/receiver/init.js; do
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
python3 tests/test_pico_io.py
python3 tests/test_satpass.py
python3 tests/test_visitas.py
python3 tests/test_api.py
python3 tests/test_ft2.py
python3 tests/test_anclajes.py
python3 tests/test_actualizar.py
python3 tests/test_env_red.py
python3 tests/test_ssl_admin.py
python3 tests/test_audio_plugins.py
python3 tests/test_audio_navegador.py
python3 tests/test_owrx_clone.py
python3 tests/test_instalador_perfil.py
python3 tools/marcadores.py --comprobar
echo "TODO OK"
