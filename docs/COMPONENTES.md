# Componentes de BricoHams SDR (v5.0)

Ficha de cada componente: **qué hace, qué paso de `install.sh` lo instala, qué
servicios y puertos usa, dónde guarda su configuración, desde dónde se gestiona,
qué prueba lo cubre y qué manual lo explica**. El detalle fichero a fichero está en
[ESTRUCTURA_FICHEROS.md](ESTRUCTURA_FICHEROS.md) y las decisiones de diseño en
[ARQUITECTURA.md](ARQUITECTURA.md) (ADR-1 … ADR-64).

## Reglas comunes a todos los componentes

- **Una sola fuente de verdad:** `/etc/bricohams/bricohams.env` (plantilla
  [`bricohams.env.example`](../bricohams.env.example)). `install.sh` la lee con
  `files/bin/bricohams-env.py`, que no ejecuta el fichero.
- **Nada configurable desde la página pública.** Todo lo que cambia algo
  (Meshtastic 433/868, APRS, TAK, monitorización, repetidores, bookmarks,
  subtonos) vive bajo `/settings`, protegido con la sesión de administrador de
  OpenWebRX+. nginx comprueba la sesión con `auth_request` contra
  `bricohams-mesh-admin` (127.0.0.1:8076).
- **Idempotente y reversible:** cada paso se puede repetir
  (`sudo bash install.sh --solo paso1,paso2`); los parcheadores de OpenWebRX+
  tienen `--quitar` y un gancho de apt que los reaplica tras actualizar.
- **Servicios en loopback:** todo escucha en `127.0.0.1` salvo lo que nginx
  publica; el cortafuegos (`bricohams-blindaje`, nftables) descarta el resto.

## Mapa de puertos

| Puerto | Componente | Alcance |
|---|---|---|
| 80 / 443 | nginx (portal, OpenWebRX+, `/settings`, tar1090, cámara) | público |
| 8073 | OpenWebRX+ | 127.0.0.1 (detrás de nginx; opcional público) |
| 8075 | `bricohams-api` (indicativos, aviones) | 127.0.0.1 |
| 8076 | `bricohams-mesh-admin` (paneles `/settings/bricohams/` y `auth_request`) | 127.0.0.1 |
| 8443 | nginx → cliente web de Meshtastic (solo admin) | LAN |
| 9443 | Webserver de `meshtasticd` (sin contraseña) | solo la Pi (`bricohams-meshweb-fw`) |
| 4403 | API TCP de `meshtasticd` | LAN |
| 1883 | Mosquitto (MQTT interno) | 127.0.0.1 |
| 2947 | gpsd | 127.0.0.1 |
| 8504 | lighttpd (tar1090) | 127.0.0.1 |
| 8554 / 8889 / 8888 / 9997 | MediaMTX RTSP / WebRTC / HLS / API | LAN / LAN / 127.0.0.1 / 127.0.0.1 |
| 8081 | OpenTAKServer (API y web) | 127.0.0.1 |
| 8089 / 8445–8447 | OpenTAKServer (CoT TLS, enrolamiento) | LAN |
| 3000 | Grafana | 127.0.0.1 (vía `/settings/bricohams/grafana/`) |
| 9090 / 9100 | Prometheus / node-exporter | 127.0.0.1 |

## Fichas

### 1. Instalador y sistema base
- **Función:** prepara la Pi, comprueba requisitos y orquesta los pasos.
- **Paso:** `comprobar`, `base`, `red`, `arranque`, `hat`.
- **Ficheros:** [`install.sh`](../install.sh) (orden en `PASOS=`), `files/bin/bricohams-env.py`, `files/bin/bricohams-check`, `files/motd/20-bricohams`, `files/bin/bricohams-banner`.
- **Servicios:** `bricohams-hat-power.service`.
- **Pruebas:** `test_instalador_os.py`, `test_instalador_perfil.py`, `test_env_red.py`.
- **Manuales:** 01, 02, 09.

### 2. OpenWebRX+ (receptor web)
- **Función:** receptor SDR web; nativo (paquete) o en Docker.
- **Paso:** `openwebrx`, `rtlsdr`, `sdrplay`, `configuracion`, `plugins`.
- **Ficheros:** `files/openwebrx/settings.json.tmpl`, `files/openwebrx/bookmarks.json`, `files/htdocs/` (plugins), `files/bin/bricohams-render-settings.py`, `files/bin/bricohams-sdr-serials`, `files/bin/bricohams-docker-compose.py`, `owrx-clone/`.
- **Servicios:** `openwebrx.service` (o contenedor).
- **Configuración:** `/var/lib/openwebrx/settings.json`, `/var/lib/openwebrx/bookmarks.json`.
- **Pruebas:** `test_render_settings.py`, `test_audio_plugins.py`, `test_audio_navegador.py`, `test_owrx_clone*.py`, `test_instalador_docker.py`.
- **Manuales:** 03, 08, 27, 30, 31, 33.

### 3. Bookmarks, importación/exportación y subtonos CTCSS
- **Función:** importar/exportar marcadores desde `/settings`, guardar el subtono CTCSS en el bookmark (modo «FM») y silenciador por tono.
- **Ficheros:** `files/bin/bricohams-owrx-bookmarks-io`, `files/bin/bricohams-owrx-ctcss`, `files/share/bricohams-ctcss/bricohams-ctcss.js`, `files/share/bricohams-ctcss/bricohams_ctcss.py`, `files/bin/bricohams-merge-bookmarks.py`.
- **Regla:** el bookmark guarda solo la **frecuencia de salida** del repetidor (lo que escucha el SDR) y su tono.
- **Pruebas:** `test_bookmarks_io.py`, `test_ctcss_patch.py`.
- **ADR:** 60.

### 4. RepeaterBook (importador por zona)
- **Función:** descargar los repetidores de la zona del SDR (p. ej. Región 5 de España) e importarlos como bookmarks con subtono.
- **Ficheros:** `files/bin/bricohams-owrx-repeaterbook` (API key en *General Settings*), `files/bin/bricohams-owrx-rbimport`, `files/share/bricohams-rbimport/bricohams_rbimport.py`.
- **Gestión:** `/settings` → General Settings (clave) y el panel de importación.
- **Pruebas:** `test_repeaterbook.py`, `test_rbimport.py`.
- **ADR:** 61.

### 5. Locator, zona y canales
- **Función:** valida el locator, calcula la zona y genera bookmarks locales y emisoras.
- **Ficheros:** `files/bin/bricohams-locator`, `files/bin/bricohams_locator*.py`, `tools/locator_catalogo.py`, `tools/canales.py`, `tools/marcadores.py`.
- **Pruebas:** `test_locator_es.py`, `test_locator_bookmarks.py`.
- **Manual:** 32; [CANALES_Y_FRECUENCIAS.md](CANALES_Y_FRECUENCIAS.md).

### 6. Meshtastic 868 (HAT) y 433 (LilyGO)
- **Función:** nodo `meshtasticd` en el HAT de 868 MHz, nodo LilyGO por USB en 433 MHz, mensajes y nodos pintados en el mapa de OpenWebRX+.
- **Paso:** `meshtastic`, `lilygo`.
- **Ficheros:** `files/bin/bricohams-mesh-admin` (panel), `files/bin/bricohams-mesh-owrx`, `files/bin/bricohams-mesh-url`, `files/bin/bricohams-lilygo`, `files/bin/bricohams_mqtt.py`, `files/bin/bricohams-mqtt-settings.py`.
- **Servicios:** `meshtasticd.service`, `bricohams-mesh-admin.service`, `bricohams-mesh-owrx.service`, `bricohams-meshweb-fw.service`, `mosquitto.service`.
- **Gestión:** `/settings/bricohams/` (solo admin); cliente web oficial por `https://<estación>:8443/` con la misma sesión.
- **Pruebas:** `test_mesh_admin.py`, `test_mesh_owrx.py`.
- **Manuales:** 05, 35.

### 7. RAK4631 LoRa-APRS (iGate)
- **Función:** firmware iGate para el RAK; solo la información del nodo y el log van al APRS/mapa.
- **Paso:** `rak`.
- **Ficheros:** `files/bin/bricohams-rak-aprs`, `firmware/`, `tools/compilar_rak.sh` (55 placas).
- **Servicios:** `bricohams-rak-aprs.service` (credenciales por `LoadCredential`).
- **Pruebas:** `test_rak_aprs.py`.
- **Manuales:** 22, 35.

### 8. ADS-B
- **Función:** readsb + tar1090 y feeders.
- **Paso:** `adsb`. **Ficheros:** `files/bin/bricohams-rbfeeder-ini.py`. **Puerto:** 8504 (lighttpd) tras `/tar1090/`.
- **Manuales:** 04, 14.

### 9. Meteorología y sensores
- **Función:** BME280, viento y lluvia, Pico I/O, estaciones meteo de la zona.
- **Paso:** `meteo`, `sensor`, `io`, `ventilacion`.
- **Ficheros:** `files/bin/bricohams-wx.py`, `bricohams-meteo.py`, `bricohams-io.py`, `bricohams-fan.py`.
- **Servicios:** `bricohams-wx`, `bricohams-meteo` (+ `.timer`), `bricohams-io`, `bricohams-fan`.
- **Pruebas:** `test_wx_bme280.py`, `test_meteo.py`, `test_viento_lluvia.py`, `test_pico_io.py`, `test_fan.py`.
- **Manuales:** 06, 18, 19, 20.

### 10. Cámara
- **Paso:** `camara`. **Servicios:** `mediamtx.service`, `bricohams-camsnap.service`. **Ficheros:** `files/bin/bricohams-camsnap.py`. **Manual:** 07.

### 11. Satélites y FT2
- **Paso:** `satelites`, `ft2`. **Servicios:** `bricohams-satpass` (+ `.timer`). **Ficheros:** `files/bin/bricohams-satpass.py`, `files/bin/bricohams-ft2*`.
- **Pruebas:** `test_satpass.py`, `test_ft2.py`. **Manuales:** 26, 28.

### 12. Web, SSL, API y visitas
- **Paso:** `web`, `visitas`.
- **Ficheros:** `files/nginx/bricohams-sdr.conf.tmpl`, `files/nginx/bricohams-sdr-rutas.conf`, `files/web/`, `files/bin/bricohams-api.py`, `files/bin/bricohams-visitas.py`, `files/bin/bricohams-telegram`.
- **Servicios:** `nginx`, `bricohams-api`, `bricohams-visitas`.
- **Pruebas:** `test_ssl_admin.py`, `test_api.py`, `test_visitas.py`, `test_live_map.py`.
- **Manuales:** 23, 24.

### 13. TAK (OpenTAKServer) y mapa local
- **Función:** servidor TAK para ATAK/iTAK; credenciales aleatorias, visibles y cambiables solo desde `/settings` (los nombres de usuario no admiten guiones).
- **Paso:** `tak`. **Ficheros:** `tools/instalar_tak.sh`, `tools/tak-requirements.txt`, `tools/activar_mapa_local.sh`, panel TAK en `bricohams-mesh-admin`.
- **Pruebas:** `test_mesh_admin.py` (panel y credenciales).
- **Manual:** 36. **ADR:** 62, 63.

### 14. Monitorización (Prometheus, node-exporter, Grafana)
- **Función:** métricas de la Pi y paneles Grafana dentro de `/settings`.
- **Paso:** `monitorizacion` (con `MONITORIZACION=yes`).
- **Comportamiento:** instala lo que falte o **adopta** instalaciones manuales con drop-ins a loopback; conserva trabajos ajenos de `prometheus.yml`; clave de `admin` = `GRAFANA_ADMIN_PASS` > `/etc/bricohams/grafana-access.txt` > aleatoria.
- **Ficheros:** `paso_monitorizacion` en `install.sh`, `files/grafana/bricohams.json`, bloque `#@GF@` de `files/nginx/bricohams-sdr-rutas.conf`.
- **Servicios:** `prometheus`, `prometheus-node-exporter`/`node_exporter`, `grafana-server`.
- **Pruebas:** `test_monitorizacion.py`. **Manual:** 36. **ADR:** 62, 64.

### 15. Seguridad (blindaje)
- **Ficheros:** `files/bin/bricohams-blindaje` (nftables + fail2ban + auditoría de permisos y secretos).
- **Pruebas:** `test_blindaje.py`. **Manual:** 34.

### 16. Tareas automáticas, copias y actualización
- **Paso:** `tareas`, `importar`, `herramientas`.
- **Ficheros:** `files/bin/bricohams-tarea`, `files/bin/bricohams-servicios`, `files/bin/bricohams-dispositivos`.
- **Servicios:** `bricohams-backup` (+ `.timer`).
- **Pruebas:** `test_actualizar.py`, `test_v45_dispositivos.py`.
- **Manuales:** 25, 29.

### 17. Hardware y documentación generada
- **Ficheros:** `hardware/` (STL, caja, anclajes, mástil), `tools/caja*.sh`, `tools/anclajes.sh`, `tools/mastil.py`, `tools/planos_antenas.py`, `tools/esquemas.py`, `tools/datos.py`, `tools/estructura.py`.
- **Pruebas:** `test_caja.py`, `test_anclajes.py`, `test_v3_hardware.py`.
- **Manuales:** 10–17, 21; [HARDWARE_Y_GPIO.md](HARDWARE_Y_GPIO.md), [MEMORIA_TECNICA.md](MEMORIA_TECNICA.md).

## Pruebas

`bash tests/run_tests.sh` ejecuta todas las pruebas, más `bash -n` y shellcheck
de los scripts, y `node --check` de los JavaScript. No necesita hardware: los
`test_*.py` montan raíces falsas en `/tmp`. Véase la sección «Pruebas» del
[README](../README.md).