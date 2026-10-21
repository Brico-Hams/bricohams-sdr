#!/bin/bash
# Pruebas del repositorio (en cualquier Linux con python3, node y shellcheck)
set -e
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/.."
echo "== shellcheck";  shellcheck -x -S warning install.sh files/bin/bricohams-check files/bin/bricohams-sdr-serials files/bin/bricohams-lilygo files/bin/bricohams-ft2 files/bin/bricohams-servicios files/bin/bricohams-tarea files/bin/bricohams-telegram files/bin/bricohams-blindaje files/bin/bricohams-banner files/motd/20-bricohams owrx-clone/instalar.sh tools/*.sh tests/run_tests.sh
echo "== bash -n";     bash -n install.sh
bash -n files/bin/bricohams-backup-limpieza
shellcheck -S warning files/bin/bricohams-backup-limpieza tests/test_backup_limpieza.sh
echo "== python";      python3 -m py_compile files/bin/*.py files/bin/bricohams-ft2-decode files/bin/bricohams-locator files/bin/bricohams-rak-aprs files/bin/bricohams-dispositivos files/bin/bricohams-mesh-url files/bin/bricohams-mesh-owrx files/bin/bricohams-mesh-admin files/bin/bricohams-google-auth files/bin/bricohams-bloqueo files/bin/bricohams-login-aviso files/bin/bricohams-oyentes files/bin/bricohams-owrx-bookmarks-io files/bin/bricohams-owrx-repeaterbook files/bin/bricohams-owrx-mapflights files/bin/bricohams-owrx-ctcss files/bin/bricohams-owrx-rbimport files/share/bricohams-ctcss/*.py files/share/bricohams-rbimport/*.py owrx-clone/owrx-clone tools/*.py hardware/antenas/sim/*.py firmware/pico-io/main.py && find . -name __pycache__ -prune -exec rm -rf {} +
echo "== javascript"
for f in files/htdocs/plugins/receiver/{idioma,marca,consentimiento,solar,meteo,camara,bricohams,banderas,dvficha,satelites,visitas,identificacion,ea5hkx_puente,audio_cadena,filtro_audio,dsp_audio}/*.js files/htdocs/plugins/receiver/init.js files/htdocs/plugins/map/init.js files/htdocs/plugins/map/bricohams_live/*.js; do
    sed -e 's/__LAT__/42.23/;s/__LON__/-8.71/;s/__CAM_SNAPSHOT_SECONDS__/60/;s/__OPERADOR__/N0CALL/g;s/__QTH__/Mi QTH/g' "$f" > /tmp/bh-check.js && node --check /tmp/bh-check.js
done
node --check files/share/bricohams-ctcss/bricohams-ctcss.js
echo "== pruebas"
bash tests/test_backup_limpieza.sh
python3 tests/test_wx_bme280.py
python3 tests/test_render_settings.py
python3 tests/test_locator_bookmarks.py
python3 tests/test_locator_es.py
python3 tests/test_meteo.py
python3 tests/test_caja.py
python3 tests/test_viento_lluvia.py
python3 tests/test_fan.py
python3 tests/test_v3_hardware.py
python3 tests/test_instalador_os.py
python3 tests/test_instalador_docker.py
python3 tests/test_pico_io.py
python3 tests/test_satpass.py
python3 tests/test_satpass_fuentes.py
python3 tests/test_visitas.py
python3 tests/test_api.py
python3 tests/test_registro_oyentes.py
python3 tests/test_chat_registro.py
python3 tests/test_plugins_ea5hkx.py
python3 tests/test_politicas_mapa_local.py
python3 tests/test_fuentes.py
python3 tests/test_systemd_unidades.py
python3 tests/test_live_map.py
python3 tests/test_ft2.py
python3 tests/test_anclajes.py
python3 tests/test_actualizar.py
python3 tests/test_env_red.py
python3 tests/test_ssl_admin.py
python3 tests/test_login_rate.py
python3 tests/test_blindaje.py
python3 tests/test_audio_plugins.py
python3 tests/test_audio_navegador.py
python3 tests/test_owrx_clone.py
python3 tests/test_owrx_clone_docker.py
python3 tests/test_instalador_perfil.py
python3 tests/test_rak_aprs.py
python3 tests/test_wx_red.py
python3 tests/test_wspr.py
python3 tests/test_satrec.py
python3 tests/test_archivo_files.py
python3 tests/test_clima_web.py
python3 tests/test_v45_dispositivos.py
python3 tests/test_mesh_owrx.py
python3 tests/test_mesh_admin.py
python3 tests/test_google_auth.py
python3 tests/test_mesh_puente.py
python3 tests/test_meshweb.py
node tests/test_meshweb_favoritos.cjs
node tests/test_satelites_filtros.cjs
python3 tests/test_agendas_admin.py
python3 tests/test_files_protegidos.py
python3 tests/test_finalizar_satelites_ctcss.py
python3 tests/test_bookmarks_io.py
python3 tests/test_repeaterbook.py
python3 tests/test_ctcss_patch.py
python3 tests/test_rbimport.py
python3 tests/test_monitorizacion.py
python3 tests/test_bloqueo_web.py
python3 tests/test_bloqueo_helper.py
python3 tests/test_chat_moderador.py
python3 tests/test_wx_rak.py
python3 tests/test_avion.py
python3 tests/test_mapflights_api.py
python3 tests/test_telegram_avisos.py
python3 tests/test_mapflights.py
python3 tests/test_anonimato.py
python3 tools/marcadores.py --comprobar
python3 tools/locator_catalogo.py --comprobar
echo "TODO OK"
