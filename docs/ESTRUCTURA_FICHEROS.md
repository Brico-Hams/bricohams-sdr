# Estructura de ficheros

> Documento **generado** por `python3 tools/estructura.py`. No lo edites a mano:
> cambia la cabecera del fichero o `DESCRIPCIONES` en el generador y vuelve a ejecutarlo.

El repositorio tiene **538 ficheros** en **104 carpetas**.

## Árbol de carpetas

```
.                                     6  Raíz del repositorio
  .vscode/                            1
  data/                               3  Datos de entrada: repetidores, marcadores, satélites y catálogo de localizadores
    locator/                          2  Catálogo de localidades → locator Maidenhead y repetidores por zona (bricohams-locator)
      fuentes/                        5
  docs/                              11  Documentación: arquitectura (ADR), componentes, datos, hardware y esta estructura
    esquemas/                        46  Diagramas generados por tools/esquemas.py (SVG fuente + PNG)
    manuales/                        38  Manuales paso a paso numerados (instalación, cada servicio y cada panel)
  files/                              0  Todo lo que install.sh copia al sistema
    bin/                             41  Ejecutables instalados en /usr/local/bin: servicios, parcheadores de OpenWebRX+ y utilidades
    branding/                         4  Imagen BricoHams (cabecera, avatar, favicon) que se aplica a OpenWebRX+
    grafana/                          1  Paneles de Grafana aprovisionados por install.sh
    htdocs/                           0  Recursos web servidos por OpenWebRX+ (plugins del cliente)
      plugins/                        0  Plugins del cliente web de OpenWebRX+ (init.js los carga)
        map/                          2
          bricohams_live/             2
          layer_qth_maidenhead/       3
          reduce_map_legend_sections/    3
        receiver/                     2
          accessible_bookmark_search/    2
          antenna_switcher/           6
          audio_cadena/               1
          banderas/                   1
          bricohams/                  1
          camara/                     1
          colorful_spectrum/          3
          compact_analog_modes/       3
          connect_notify/             3
          doppler/                    6
          dsp_audio/                  1
          dvficha/                    1
          example/                    2
          example_theme/              3
          example_uikit/              2
          filtro_audio/               1
          freq_scanner/               4
          frequency_far_jump/         2
          keyboard_shortcuts/         4
          magic_key/                  3
          map/                        1
          meteo/                      1
          minimap/                    2
          mouse_freq/                 3
          notify/                     3
          rig_skin/                   3
          satelites/                  1
          screen_reader/              3
          screenshot/                 4
          search_bookmarks/           3
          set_waterfall_theme/        2
          show_band_plan/             2
          smeter/                     3
          solar/                      1
          sort_profiles/              2
          thumbtune/                  4
          toggle_scannable/           4
          tune_checkbox/              2
          tune_precise/               3
          ui_basic_theme/             3
          ui_chat/                    3
          ui_magic_key/               2
          ui_status/                  3
          uikit/                     10
          utils/                      2
          visitas/                    1
    motd/                             1  Mensaje de bienvenida de la consola
    nginx/                            2  Plantillas del sitio nginx (proxy, TLS, rutas /settings/bricohams/...)
    openwebrx/                        2  Plantillas de configuración de OpenWebRX+ (settings, marcadores, conf.d)
      conf.d/                         2
    share/                            0  Módulos compartidos que los parcheadores insertan en OpenWebRX+
      bricohams-ctcss/                2
      bricohams-rbimport/             1
    web/                              2  Portal estático /bricohams/ y página de privacidad
  firmware/                           0  Firmware para los microcontroladores de la estación
    pico-io/                          1  MicroPython de la Raspberry Pi Pico (sensores y ventiladores)
    rak4631-lora-aprs/               18  Firmware iGate LoRa APRS (solo RX) para RAK4631 y placas compatibles (PlatformIO)
      bin/                            5
      test/                           1
        shim/                         1
  hardware/                           0  Diseño mecánico y de RF (OpenSCAD, STL, NEC2)
    anclajes/                         1  Crucetas y soportes impresos del mástil
      render/                         1
      stl/                           16
    antenas/                          1  Antenas propias: modelo OpenSCAD, piezas STL y simulación NEC2
      render/                         1
      sim/                            5
        resultados/                   5
      stl/                           30
    caja/                             2  Caja de intemperie v2 (mástil)
      render/                        15
      stl/                           16
    caja_v3/                          1  Caja v3 en dos módulos (electrónica + potencia)
      render/                         5
      stl/                           30
    gcode/                            1
  owrx-clone/                         6  Herramienta independiente (MIT) para clonar una instalación de OpenWebRX+
  tests/                             41  Pruebas automáticas (bash tests/run_tests.sh)
    datos/                            2  Datos de prueba (fixtures) usados por los tests
      owrx/                           0
        htdocs/                       0
          lib/                        2
        owrx/                         2
      owrx-1.2.126/                   5
  tools/                             21  Generadores y herramientas de desarrollo (esquemas, datos, STL, TAK, compilación RAK)
```

## Qué hace cada fichero

### `/ (raíz)`

Raíz del repositorio.

| Fichero | Qué hace |
|---|---|
| `.gitattributes` | Fuerza finales de línea LF (los scripts se ejecutan en Linux) |
| `.gitignore` | Excluye claves (bricohams.env), cachés y artefactos de compilación |
| `bricohams.env.example` | Plantilla pública de configuración de la estación, sin credenciales (copiar a bricohams.env) |
| `CHANGELOG.md` | Historial de versiones y de cada cambio |
| `install.sh` | Instalador por pasos, idempotente: dependencias, servicios, parches de OpenWebRX+, nginx, Meshtastic, APRS, TAK, Grafana/Prometheus y copias (--lista, --solo, --backup, --actualizar) |
| `README.md` | Presentación del proyecto, puesta en marcha rápida, estructura resumida y reglas |

### `.vscode/`

| Fichero | Qué hace |
|---|---|
| `settings.json` | Datos JSON: settings |

### `data/`

Datos de entrada: repetidores, marcadores, satélites y catálogo de localizadores.

| Fichero | Qué hace |
|---|---|
| `marcadores_v4.json` | 🏛️ RU-75 ED5YBF · Radio Club Región de Murcia |
| `repetidores_EA5KGV_zonaEA5.csv` | Tabla de datos: repetidores EA5KGV zonaEA5 |
| `satelites.json` | Datos JSON: satelites |

### `data/locator/`

Catálogo de localidades → locator Maidenhead y repetidores por zona (bricohams-locator).

| Fichero | Qué hace |
|---|---|
| `catalogo_es.json` | ✈️ ES-0001 TWR Jerez Tower |
| `LEEME.md` | data/locator · catálogo de zona de España (v4.3) |

### `data/locator/fuentes/`

| Fichero | Qué hace |
|---|---|
| `aemet_estaciones.csv` | Tabla de datos: aemet estaciones |
| `otros_es.csv` | Tabla de datos: otros es |
| `ourairports_es_aeropuertos.csv` | Tabla de datos: ourairports es aeropuertos |
| `ourairports_es_frecuencias.csv` | Tabla de datos: ourairports es frecuencias |
| `puertos_es.csv` | Tabla de datos: puertos es |

### `docs/`

Documentación: arquitectura (ADR), componentes, datos, hardware y esta estructura.

| Fichero | Qué hace |
|---|---|
| `ARQUITECTURA.md` | Decisiones de arquitectura (ADR-01 en adelante): contexto, decisión y consecuencias |
| `AYUDA_RAPIDA.md` | Ayuda rápida · BricoHams SDR (v4.2) |
| `CANALES_Y_FRECUENCIAS.md` | Canales y frecuencias de todos los grupos de marcadores (generado por tools/canales.py) |
| `COMPONENTES.md` | Ficha de cada componente: función, ficheros, servicio, puertos, configuración y pruebas |
| `DATOS.md` | Conjuntos de datos: SDR, perfiles, marcadores, puertos, servicios, I2C (generado por tools/datos.py) |
| `DESPLIEGUE_EA5KAO_2026-10-11.md` | Despliegue en la estación de EA5KAO · 11/10/2026 |
| `ESTRUCTURA_FICHEROS.md` | Este documento (generado por tools/estructura.py) |
| `EVALUACION_MODULOS.md` | Evaluación de módulos |
| `HARDWARE_Y_GPIO.md` | Hardware, GPIO, buses y alimentación |
| `MEMORIA_TECNICA.md` | Memoria técnica · Estación BricoHams SDR · EA5KAO · Mi QTH (v3.0) |
| `REFERENCIAS.md` | Referencias |

### `docs/esquemas/`

Diagramas generados por tools/esquemas.py (SVG fuente + PNG).

| Fichero | Qué hace |
|---|---|
| `01_arquitectura.png` | Imagen / vista renderizada: 01 arquitectura |
| `01_arquitectura.svg` | Diagrama vectorial: 01 arquitectura |
| `02_gpio_pi5.png` | Imagen / vista renderizada: 02 gpio pi5 |
| `02_gpio_pi5.svg` | Diagrama vectorial: 02 gpio pi5 |
| `03_cableado_bme280.png` | Imagen / vista renderizada: 03 cableado bme280 |
| `03_cableado_bme280.svg` | Diagrama vectorial: 03 cableado bme280 |
| `04_rf_antenas_alimentacion.png` | Imagen / vista renderizada: 04 rf antenas alimentacion |
| `04_rf_antenas_alimentacion.svg` | Diagrama vectorial: 04 rf antenas alimentacion |
| `05_red_puertos.png` | Imagen / vista renderizada: 05 red puertos |
| `05_red_puertos.svg` | Diagrama vectorial: 05 red puertos |
| `06_alimentacion_caja.png` | Imagen / vista renderizada: 06 alimentacion caja |
| `06_alimentacion_caja.svg` | Diagrama vectorial: 06 alimentacion caja |
| `07_caja_distribucion.png` | Imagen / vista renderizada: 07 caja distribucion |
| `07_caja_distribucion.svg` | Diagrama vectorial: 07 caja distribucion |
| `08_quad_2m70.png` | Imagen / vista renderizada: 08 quad 2m70 |
| `09_discones.png` | Imagen / vista renderizada: 09 discones |
| `10_adsb_gp.png` | Imagen / vista renderizada: 10 adsb gp |
| `11_plan_mastil.png` | Imagen / vista renderizada: 11 plan mastil |
| `12_cadena_rf.png` | Imagen / vista renderizada: 12 cadena rf |
| `12_cadena_rf.svg` | Diagrama vectorial: 12 cadena rf |
| `13_ventiladores.png` | Imagen / vista renderizada: 13 ventiladores |
| `13_ventiladores.svg` | Diagrama vectorial: 13 ventiladores |
| `14_sensores_wx.png` | Imagen / vista renderizada: 14 sensores wx |
| `14_sensores_wx.svg` | Diagrama vectorial: 14 sensores wx |
| `15_alimentacion_v3.png` | Imagen / vista renderizada: 15 alimentacion v3 |
| `15_alimentacion_v3.svg` | Diagrama vectorial: 15 alimentacion v3 |
| `16_pico_io.png` | Imagen / vista renderizada: 16 pico io |
| `16_pico_io.svg` | Diagrama vectorial: 16 pico io |
| `17_filtros_lna.png` | Imagen / vista renderizada: 17 filtros lna |
| `17_filtros_lna.svg` | Diagrama vectorial: 17 filtros lna |
| `18_red_servicios.png` | Imagen / vista renderizada: 18 red servicios |
| `18_red_servicios.svg` | Diagrama vectorial: 18 red servicios |
| `19_actualizar.png` | Imagen / vista renderizada: 19 actualizar |
| `19_actualizar.svg` | Diagrama vectorial: 19 actualizar |
| `20_audio_navegador.png` | Imagen / vista renderizada: 20 audio navegador |
| `20_audio_navegador.svg` | Diagrama vectorial: 20 audio navegador |
| `21_clonar_openwebrx.png` | Imagen / vista renderizada: 21 clonar openwebrx |
| `21_clonar_openwebrx.svg` | Diagrama vectorial: 21 clonar openwebrx |
| `22_zona_locator.png` | Imagen / vista renderizada: 22 zona locator |
| `22_zona_locator.svg` | Diagrama vectorial: 22 zona locator |
| `23_openwebrx_docker.png` | Imagen / vista renderizada: 23 openwebrx docker |
| `23_openwebrx_docker.svg` | Diagrama vectorial: 23 openwebrx docker |
| `24_blindaje.png` | Imagen / vista renderizada: 24 blindaje |
| `24_blindaje.svg` | Diagrama vectorial: 24 blindaje |
| `25_lora_owrx.png` | Imagen / vista renderizada: 25 lora owrx |
| `25_lora_owrx.svg` | Diagrama vectorial: 25 lora owrx |

### `docs/manuales/`

Manuales paso a paso numerados (instalación, cada servicio y cada panel).

| Fichero | Qué hace |
|---|---|
| `01_PREPARACION.md` | 01 · Preparación del hardware y de la tarjeta |
| `02_INSTALACION.md` | 02 · Instalación |
| `03_SDR_Y_SERIES.md` | 03 · SDR y números de serie |
| `04_ADSB.md` | 04 · ADS-B con el FlightStick de RadarBox (readsb + rbfeeder + MLAT) |
| `05_LILYGO.md` | 05 · LilyGO T3 V1.6.1 de 433 MHz: nodo Meshtastic e iGate LoRa APRS |
| `06_SENSOR_WX.md` | 06 · Sensor BME280/BMP280 y estación WX APRS |
| `07_CAMARA.md` | 07 · Cámara del mástil (Waveshare RPi Camera (F) · OV5647 con visión nocturna) |
| `08_SDRPLAY.md` | 08 · Cuando llegue el SDRplay |
| `09_MANTENIMIENTO.md` | 09 · Mantenimiento, copias y restauración |
| `10_CAJA_3D.md` | 10 · Caja de intemperie impresa en 3D (PETG + TPU, Anycubic Kobra S1) |
| `11_MASTIL_Y_ANTENAS.md` | 11 · Mástil, plan de antenas, soportes y carga de viento |
| `12_QUAD_2M70.md` | 12 · Quad de doble resonancia 2 m / 70 cm (RADIOAFICIONADOS) |
| `13_DISCONES.md` | 13 · Discones de banda ancha (MULTIPERFIL y futuro SDR) |
| `14_ADSB_LNA.md` | 14 · Antena ADS-B 1090 MHz con el LNA en la base |
| `15_LAZO_MLA30.md` | 15 · Lazo MLA-30 para HF: protección de intemperie y montaje |
| `16_FILTROS_Y_PREAMPLIFICADORES.md` | 16 · Filtros, preamplificadores y bias-tee |
| `17_CAJA_V3.md` | 17 · Caja v3: dos módulos al pie del mástil |
| `18_VENTILACION.md` | 18 · Ventilación de la caja: conexión y control |
| `19_VIENTO_Y_LLUVIA.md` | 19 · Viento y lluvia para el WX APRS |
| `20_PICO_IO.md` | 20 · Pico «bricohams-io»: sensores y ventiladores por USB |
| `21_ANCLAJES.md` | 21 · Anclajes impresos al mástil, brazos y sensores |
| `22_WX_LORA_FIRMWARE.md` | 22 · Estación meteorológica APRS con firmware LoRa (CA2RXU) en un LilyGO |
| `23_WEB_SSL_SERVICIOS.md` | 23 · Web con SSL, portal de servicios y cómo entrar a cada uno |
| `24_VISITAS_TELEGRAM.md` | 24 · Oyentes, estadísticas y avisos por Telegram |
| `25_TAREAS_AUTOMATICAS.md` | 25 · Tareas automáticas: copias, actualizaciones, reinicios y avisos |
| `26_SATELITES.md` | 26 · Satélites: aviso de próximos pases, ▶ Escuchar con Doppler e imágenes METEOR |
| `27_PLUGINS_WEB_V4.md` | 27 · Plugins nuevos de la web (v4) |
| `28_FT2.md` | 28 · FT2 en OpenWebRX+ (EXPERIMENTAL) |
| `29_ACTUALIZAR.md` | 29 · Actualizar la estación: `install.sh --actualizar` |
| `30_AUDIO_DSP.md` | 30 · Filtro de audio y DSP en el navegador (plugins `filtro_audio` y `dsp_audio`) |
| `31_CLONAR_OPENWEBRX.md` | 31 · Clonar una instalación de OpenWebRX+ a otro equipo (owrx-clone) |
| `32_ZONA_LOCATOR.md` | 32 · Zona de la estación por locator: aeropuertos, AEMET, puertos y FM (v4.3) |
| `33_OPENWEBRX_DOCKER.md` | 33 · OpenWebRX+ en Docker (v4.3) |
| `34_BLINDAJE_SEGURIDAD.md` | 34 · Blindaje de seguridad de la estación (v4.4) |
| `35_LORA_APRS_MESHTASTIC.md` | 35 · iGate LoRa APRS en un RAK4631 y Meshtastic 433/868, dentro de OpenWebRX+ (v4.5) |
| `36_TAK_MAPA_LOCAL.md` | TAK local, mapa ADS-B/APRS y CHAT |
| `37_JUSTIFICACION_CAMBIOS_V4_6.md` | 37 · Justificación de los cambios de la v4.6 |
| `38_GITHUB_SINCRONIZACION_PRIVACIDAD.md` | 38 · GitHub: sincronización y repositorio sin datos personales (v5.1) |

### `files/bin/`

Ejecutables instalados en /usr/local/bin: servicios, parcheadores de OpenWebRX+ y utilidades.

| Fichero | Qué hace |
|---|---|
| `bricohams-api.py` | bricohams-api · EA5KAO · BricoHams (v4) |
| `bricohams-banner` | bricohams-banner · EA5KAO · BricoHams (v4.5) |
| `bricohams-blindaje` | bricohams-blindaje · auditoría y blindaje de seguridad de la estación (v4.4) |
| `bricohams-camsnap.py` | bricohams-camsnap · EA5KAO · BricoHams |
| `bricohams-check` | Diagnóstico de la estación: SDR, servicios, GPS, sensores, red y certificados |
| `bricohams-dispositivos` | bricohams-dispositivos · EA5KAO · BricoHams (v4.5) |
| `bricohams-docker-compose.py` | v4.3 · docker-compose.yaml de OpenWebRX+ (imagen de slechev) a partir de bricohams.env. |
| `bricohams-env.py` | Lee y valida bricohams.env; lo usan install.sh y los servicios |
| `bricohams-fan.py` | bricohams-fan · EA5KAO · BricoHams |
| `bricohams-ft2` | bricohams-ft2 · EA5KAO · BricoHams (v4, EXPERIMENTAL) |
| `bricohams-ft2-decode` | bricohams-ft2-decode · EA5KAO · BricoHams (v4, experimental) |
| `bricohams-ft2-patch.py` | bricohams-ft2-patch · EA5KAO · BricoHams (v4, experimental) |
| `bricohams-io.py` | bricohams-io · EA5KAO · BricoHams |
| `bricohams-lilygo` | bricohams-lilygo · EA5KAO · BricoHams |
| `bricohams-locator` | Zona de la estación según su locator: coordenadas, AEMET y FM cercanas, marcadores [AUTO-LOCATOR] y METEO_STATIONS (manual 32) |
| `bricohams-merge-bookmarks.py` | Une marcadores de OpenWebRX (clave: frecuencia + modo). |
| `bricohams-mesh-admin` | Panel de administración (solo /settings, con sesión): Meshtastic 433/868, iGate RAK, APRS, TAK (credenciales) y Monitorización |
| `bricohams-mesh-owrx` | Integra Meshtastic en la web de OpenWebRX+ (solo información de nodos y registro APRS, sin configuración) |
| `bricohams-mesh-puente` | bricohams-mesh-puente · BricoHams SDR (v5.1, manual 35 §9, ADR-66) |
| `bricohams-mesh-url` | Genera/lee las URL de canales Meshtastic compartidas entre los nodos 433 y 868 |
| `bricohams-meteo.py` | bricohams-meteo · EA5KAO · BricoHams |
| `bricohams-mqtt-settings.py` | v4.2 · Tras importar un perfil (install.sh --importar), activa en settings.json el informe |
| `bricohams-owrx-bookmarks-io` | Parche de OpenWebRX+: importar/exportar bookmarks en /settings/bookmarks |
| `bricohams-owrx-botones` | Parche de OpenWebRX+: botones TAK y Monitorización en /settings (nunca en la página pública) |
| `bricohams-owrx-ctcss` | Parche de OpenWebRX+: subtono CTCSS (FM) en bookmarks y silenciador por tono |
| `bricohams-owrx-rbimport` | Parche de OpenWebRX+: importar repetidores de RepeaterBook por región a bookmarks (con subtono) |
| `bricohams-owrx-repeaterbook` | Parche de OpenWebRX+: campo de clave API de RepeaterBook en /settings/general |
| `bricohams-rak-aprs` | Puente del iGate RAK4631 (USB serie) hacia APRS-IS y el registro mostrado en la web |
| `bricohams-rbfeeder-ini.py` | BricoHams: deja /etc/rbfeeder.ini leyendo la salida Beast de readsb |
| `bricohams-render-settings.py` | bricohams-render-settings · EA5KAO · BricoHams |
| `bricohams-satpass.py` | bricohams-satpass · EA5KAO · BricoHams (v4) |
| `bricohams-sdr-serials` | bricohams-sdr-serials · EA5KAO · BricoHams |
| `bricohams-servicios` | Lista y controla los servicios BricoHams (estado, arranque, logs) |
| `bricohams-tarea` | bricohams-tarea · EA5KAO · BricoHams (v4) |
| `bricohams-telegram` | bricohams-telegram "texto" · manda un aviso al grupo/canal de Telegram de la estación. |
| `bricohams-visitas.py` | bricohams-visitas · EA5KAO · BricoHams (v4) |
| `bricohams-wx.py` | bricohams-wx · EA5KAO · BricoHams |
| `bricohams_locator.py` | Locator Maidenhead ⇄ coordenadas (v4.3). |
| `bricohams_locator_bookmarks.py` | Select nearby radio sites from a curated JSON catalog for an OpenWebRX+ QTH. |
| `bricohams_locator_online.py` | v4.3 · Datos de zona que se bajan EN LA PI al instalar (cambian a menudo, no van en el kit) |
| `bricohams_mqtt.py` | BricoHams v4.5 · publicador MQTT 3.1.1 mínimo (QoS 0, sin dependencias) para el broker local. |

### `files/branding/`

Imagen BricoHams (cabecera, avatar, favicon) que se aplica a OpenWebRX+.

| Fichero | Qué hace |
|---|---|
| `logo_tarjeta.png` | Imagen / vista renderizada: logo tarjeta |
| `receiver_avatar.png` | Imagen / vista renderizada: receiver avatar |
| `receiver_top_photo.png` | Imagen / vista renderizada: receiver top photo |
| `receiver_top_photo_v3.png` | Imagen / vista renderizada: receiver top photo v3 |

### `files/grafana/`

Paneles de Grafana aprovisionados por install.sh.

| Fichero | Qué hace |
|---|---|
| `bricohams.json` | Datos JSON: bricohams |

### `files/htdocs/plugins/map/`

| Fichero | Qué hace |
|---|---|
| `init.js` | EA5KAO · BricoHams · Plugins del MAPA OpenWebRX+ |
| `init.js.sample` | Plugin loader. |

### `files/htdocs/plugins/map/bricohams_live/`

| Fichero | Qué hace |
|---|---|
| `bricohams_live.css` | Hoja de estilos: bricohams live |
| `bricohams_live.js` | Plugin de mapa: capas en vivo de trazas APRS, aeronaves ADS-B y marcadores TAK sobre el mapa de OpenWebRX+ |

### `files/htdocs/plugins/map/layer_qth_maidenhead/`

| Fichero | Qué hace |
|---|---|
| `layer_qth_maidenhead.js` | Plugin: Add Maidenhead Locator (QTH) layer to the map. |
| `maidenhead.png` | Imagen / vista renderizada: maidenhead |
| `README.md` | Preview |

### `files/htdocs/plugins/map/reduce_map_legend_sections/`

| Fichero | Qué hace |
|---|---|
| `README.md` | Preview |
| `reduce_map_legend_sections.js` | Plugin de mapa: compacta las secciones de la leyenda |
| `reduce_map_legend_sections.png` | Imagen / vista renderizada: reduce map legend sections |

### `files/htdocs/plugins/receiver/`

| Fichero | Qué hace |
|---|---|
| `init.js` | EA5KAO · BricoHams · Plugins del RECEPTOR OpenWebRX+ |
| `init.js.sample` | Receiver plugins initialization. |

### `files/htdocs/plugins/receiver/accessible_bookmark_search/`

| Fichero | Qué hace |
|---|---|
| `accessible_bookmark_search.js` | Accessible Bookmark Search plugin for OpenWebRX+. |
| `README.md` | Features |

### `files/htdocs/plugins/receiver/antenna_switcher/`

| Fichero | Qué hace |
|---|---|
| `antenna_switcher.cfg` | Configuración del plugin conmutador de antenas (pines GPIO de salida) |
| `antenna_switcher.css` | Hoja de estilos: antenna switcher |
| `antenna_switcher.js` | Antenna switch UI plugin for OpenWebRX+ |
| `antenna_switcher.py` | Simple Flask backend to work with the JavaScript frontend for the antenna switcher by DL9UL |
| `install_backend.sh` | Install script for the antenna_switcher backend. |
| `README.md` | I. Front-end installation |

### `files/htdocs/plugins/receiver/audio_cadena/`

| Fichero | Qué hace |
|---|---|
| `audio_cadena.js` | audio_cadena: base común de los plugins de audio de BricoHams (v4.2) |

### `files/htdocs/plugins/receiver/banderas/`

| Fichero | Qué hace |
|---|---|
| `banderas.js` | banderas: bandera del país en los mensajes FT8 / FT4 / FT2 / WSPR / JT65… de OpenWebRX+ |

### `files/htdocs/plugins/receiver/bricohams/`

| Fichero | Qué hace |
|---|---|
| `bricohams.js` | bricohams: imagen de BricoHams (Mi QTH, Región de Murcia) para OpenWebRX+ |

### `files/htdocs/plugins/receiver/camara/`

| Fichero | Qué hace |
|---|---|
| `camara.js` | camara: cámara del mástil para OpenWebRX+ |

### `files/htdocs/plugins/receiver/colorful_spectrum/`

| Fichero | Qué hace |
|---|---|
| `colorful_spectrum.js` | Plugin: colorify the spectrum analyzer. |
| `colorful_spectrum.png` | Imagen / vista renderizada: colorful spectrum |
| `README.md` | Preview |

### `files/htdocs/plugins/receiver/compact_analog_modes/`

| Fichero | Qué hace |
|---|---|
| `compact_analog_modes.js` | Plugin de receptor: agrupa los modos analógicos en un selector compacto |
| `compact_analog_modes.png` | Imagen / vista renderizada: compact analog modes |
| `README.md` | Preview |

### `files/htdocs/plugins/receiver/connect_notify/`

| Fichero | Qué hace |
|---|---|
| `connect_notify.js` | Plugin: User connect notification |
| `connect_notify.png` | Imagen / vista renderizada: connect notify |
| `README.md` | Preview |

### `files/htdocs/plugins/receiver/doppler/`

| Fichero | Qué hace |
|---|---|
| `doppler.css` | Hoja de estilos: doppler |
| `doppler.js` | Plugin: Doppler - Track satellite frequency (Doppler shift/effect) |
| `doppler.png` | Imagen / vista renderizada: doppler |
| `doppler1.png` | Imagen / vista renderizada: doppler1 |
| `README.md` | Preview |
| `sat.js` | satellite-js v5.0.0 |

### `files/htdocs/plugins/receiver/dsp_audio/`

| Fichero | Qué hace |
|---|---|
| `dsp_audio.js` | dsp_audio: procesado de audio para el oyente de OpenWebRX+ (v4.2) |

### `files/htdocs/plugins/receiver/dvficha/`

| Fichero | Qué hace |
|---|---|
| `dvficha.js` | dvficha: ficha del operador en voz digital (DMR, YSF, NXDN, D-Star) para OpenWebRX+ |

### `files/htdocs/plugins/receiver/example/`

| Fichero | Qué hace |
|---|---|
| `example.js` | example UI plugin for OpenWebRx+ |
| `README.md` | New Developer Quickstart |

### `files/htdocs/plugins/receiver/example_theme/`

| Fichero | Qué hace |
|---|---|
| `example_theme.css` | colors for the new theme |
| `example_theme.js` | example plugin, creating a new theme for OpenWebRx+ |
| `README.md` | Code |

### `files/htdocs/plugins/receiver/example_uikit/`

| Fichero | Qué hace |
|---|---|
| `example_uikit.js` | Plugin: example_uikit - Demo plugin showcasing all UIKit features |
| `README.md` | What it demonstrates |

### `files/htdocs/plugins/receiver/filtro_audio/`

| Fichero | Qué hace |
|---|---|
| `filtro_audio.js` | filtro_audio: filtro de audio para el oyente de OpenWebRX+ (v4.2) |

### `files/htdocs/plugins/receiver/freq_scanner/`

| Fichero | Qué hace |
|---|---|
| `freq_scanner.jpg` | Imagen: freq scanner |
| `freq_scanner.js` | Frequency Scanner Plugin for OpenWebRX+ |
| `README-DE.md` | Vorschau |
| `README.md` | Preview |

### `files/htdocs/plugins/receiver/frequency_far_jump/`

| Fichero | Qué hace |
|---|---|
| `frequency_far_jump.js` | Plugin: Jump to a frequency outside the boundaries of the selected profile by typing it in the receiver's frequency dial. |
| `README.md` | Load |

### `files/htdocs/plugins/receiver/keyboard_shortcuts/`

| Fichero | Qué hace |
|---|---|
| `keyboard_shortcuts.css` | Plugin: Keyboard Shortcuts |
| `keyboard_shortcuts.js` | Plugin: Keyboard Shortcuts |
| `README.md` | preview |
| `shortcuts.png` | Imagen / vista renderizada: shortcuts |

### `files/htdocs/plugins/receiver/magic_key/`

| Fichero | Qué hace |
|---|---|
| `magic_key.js` | Plugin: MagicKey - Set the MagicKey without typing it in browser's address bar |
| `magic_key.png` | Imagen / vista renderizada: magic key |
| `README.md` | Preview |

### `files/htdocs/plugins/receiver/map/`

| Fichero | Qué hace |
|---|---|
| `README.md` | Enable |

### `files/htdocs/plugins/receiver/meteo/`

| Fichero | Qué hace |
|---|---|
| `meteo.js` | meteo: tiempo en vivo de las estaciones cercanas para OpenWebRX+ |

### `files/htdocs/plugins/receiver/minimap/`

| Fichero | Qué hace |
|---|---|
| `minimap.js` | Plugin: Minimap - Adds a minimap to receiver page. |
| `README.md` | Load |

### `files/htdocs/plugins/receiver/mouse_freq/`

| Fichero | Qué hace |
|---|---|
| `mouse_freq.js` | Plugin: Mouse Freq - show frequency under mouse pointer |
| `mouse_freq.png` | Imagen / vista renderizada: mouse freq |
| `README.md` | Preview |

### `files/htdocs/plugins/receiver/notify/`

| Fichero | Qué hace |
|---|---|
| `notify.css` | Plugin: Notifications for other plugins |
| `notify.js` | Plugin: Provides notifications for other plugins |
| `README.md` | Usage |

### `files/htdocs/plugins/receiver/rig_skin/`

| Fichero | Qué hace |
|---|---|
| `rig_skin.css` | rig_skin: dark receiver front-panel theme for OpenWebRX+. |
| `rig_skin.js` | rig_skin: dark receiver front-panel theme with a rotating VFO knob. |
| `rig_skin_map.js` | World land outlines for the DX cluster map, derived from the |

### `files/htdocs/plugins/receiver/satelites/`

| Fichero | Qué hace |
|---|---|
| `satelites.js` | satelites: aviso de próximos pases y «▶ Escuchar» con un clic (OpenWebRX+) |

### `files/htdocs/plugins/receiver/screen_reader/`

| Fichero | Qué hace |
|---|---|
| `README.md` | Preview |
| `screen_reader.js` | Plugin: Screen Reader - Provide spoken notifications to users with Assistive Technology |
| `screen_reader.png` | Imagen / vista renderizada: screen reader |

### `files/htdocs/plugins/receiver/screenshot/`

| Fichero | Qué hace |
|---|---|
| `html2canvas.min.js` | html2canvas 1.4.1 <https://html2canvas.hertzen.com> |
| `README.md` | Preview |
| `screenshot.js` | Plugin: Screenshot - Take a screenshot of the waterfall |
| `screenshot.png` | Imagen / vista renderizada: screenshot |

### `files/htdocs/plugins/receiver/search_bookmarks/`

| Fichero | Qué hace |
|---|---|
| `LICENSE` | Licencia del plugin de terceros search_bookmarks |
| `README.md` | owrx-search-bookmarks by [Yannis](https://github.com/ysamouhos) |
| `search_bookmarks.js` | Seaarch Bookmarks UI plugin for OpenWebRX+ >= v1.2.118 |

### `files/htdocs/plugins/receiver/set_waterfall_theme/`

| Fichero | Qué hace |
|---|---|
| `README.md` | Load |
| `set_waterfall_theme.js` | set_waterfall_theme |

### `files/htdocs/plugins/receiver/show_band_plan/`

| Fichero | Qué hace |
|---|---|
| `README.md` | Load |
| `show_band_plan.js` | Plugin de receptor: dibuja el plan de bandas sobre la cascada |

### `files/htdocs/plugins/receiver/smeter/`

| Fichero | Qué hace |
|---|---|
| `README.md` | Preview |
| `smeter.jpg` | Imagen: smeter |
| `smeter.js` | Plugin: smeter - Replaces the original S-meter with a new one. |

### `files/htdocs/plugins/receiver/solar/`

| Fichero | Qué hace |
|---|---|
| `solar.js` | solar: radiación solar y propagación HF para OpenWebRX+ |

### `files/htdocs/plugins/receiver/sort_profiles/`

| Fichero | Qué hace |
|---|---|
| `README.md` | Load |
| `sort_profiles.js` | Plugin: sort profiles by name. |

### `files/htdocs/plugins/receiver/thumbtune/`

| Fichero | Qué hace |
|---|---|
| `README.md` | ThumbTune |
| `thumbtune.css` | ThumbTune Main Container |
| `thumbtune.jpg` | Imagen: thumbtune |
| `thumbtune.js` | ThumbTune plugin for OpenWebRX+ |

### `files/htdocs/plugins/receiver/toggle_scannable/`

| Fichero | Qué hace |
|---|---|
| `README.md` | Preview |
| `toggle_scannable.css` | .bookmark.selected { |
| `toggle_scannable.js` | Plugin: ToggleScannable - Toggle scannable state of the bookmarks in the receiver |
| `toggle_scannable.png` | Imagen / vista renderizada: toggle scannable |

### `files/htdocs/plugins/receiver/tune_checkbox/`

| Fichero | Qué hace |
|---|---|
| `README.md` | Load |
| `tune_checkbox.js` | Plugin: Make the 'Hold mouse wheel down to tune' option checked by default. |

### `files/htdocs/plugins/receiver/tune_precise/`

| Fichero | Qué hace |
|---|---|
| `README.md` | Preview |
| `tune_precise.jpg` | Imagen: tune precise |
| `tune_precise.js` | Plugin: Tune Precise - add buttons to precisely tune the frequency |

### `files/htdocs/plugins/receiver/ui_basic_theme/`

| Fichero | Qué hace |
|---|---|
| `README.md` | Load |
| `ui_basic_theme.css` | ui_basic_theme — dark theme matching uikit's original built-in colors |
| `ui_basic_theme.js` | Plugin: ui_basic_theme - Dark theme matching uikit's original built-in colors |

### `files/htdocs/plugins/receiver/ui_chat/`

| Fichero | Qué hace |
|---|---|
| `README.md` | Load |
| `ui_chat.css` | ── Chat tab wrapper ──────────────────────────────────────────────────────── |
| `ui_chat.js` | Plugin: ui_chat - Chat/Log tab in the uikit panel |

### `files/htdocs/plugins/receiver/ui_magic_key/`

| Fichero | Qué hace |
|---|---|
| `README.md` | Load |
| `ui_magic_key.js` | Plugin: ui_magic_key - Set the MagicKey via a UIKit settings tab |

### `files/htdocs/plugins/receiver/ui_status/`

| Fichero | Qué hace |
|---|---|
| `README.md` | ui_status |
| `ui_status.css` | Hoja de estilos: ui status |
| `ui_status.js` | Plugin: ui_status - Status bar footer in the uikit panel |

### `files/htdocs/plugins/receiver/uikit/`

| Fichero | Qué hace |
|---|---|
| `README.md` | UI Kit (uikit) |
| `uikit-core.js` | uikit-core.js — DOM helpers, SVG/icon builders, button factory, slug utilities |
| `uikit-loading.js` | uikit-loading.js — Loading overlay with spinner |
| `uikit-modals.js` | uikit-modals.js — Plugin modal API (createModal, openModal, closeModal, |
| `uikit-panel.js` | uikit-panel.js — Dockable panel, tab system, layout sync, positioning, |
| `uikit-settings.js` | uikit-settings.js — Settings modal, settings rendering, load/save/apply |
| `uikit-toasts.js` | uikit-toasts.js — Toast notification system |
| `uikit.css` | Hoja de estilos: uikit |
| `uikit.js` | Plugin: uikit - UI helper toolkit for OpenWebRX+ plugins |
| `uikit.png` | Imagen / vista renderizada: uikit |

### `files/htdocs/plugins/receiver/utils/`

| Fichero | Qué hace |
|---|---|
| `README.md` | Features |
| `utils.js` | This is the utils plugin |

### `files/htdocs/plugins/receiver/visitas/`

| Fichero | Qué hace |
|---|---|
| `visitas.js` | visitas: oyentes conectados y contador de visitas (OpenWebRX+) |

### `files/motd/`

Mensaje de bienvenida de la consola.

| Fichero | Qué hace |
|---|---|
| `20-bricohams` | BricoHams v4.5 · estado de la estación al entrar por SSH (lo lanza pam_motd con |

### `files/nginx/`

Plantillas del sitio nginx (proxy, TLS, rutas /settings/bricohams/...).

| Fichero | Qué hace |
|---|---|
| `bricohams-sdr-rutas.conf` | nginx · BricoHams SDR · rutas comunes a HTTP y HTTPS (v4.2) |
| `bricohams-sdr.conf.tmpl` | nginx · BricoHams SDR · EA5KAO (v4.2) — lo genera install.sh (paso «web») |

### `files/openwebrx/`

Plantillas de configuración de OpenWebRX+ (settings, marcadores, conf.d).

| Fichero | Qué hace |
|---|---|
| `bookmarks.json` | ⭐ 97.5 Wifon FM |
| `settings.json.tmpl` | Plantilla de settings.json de OpenWebRX+ (receptor, perfiles, ubicación) rellenada desde bricohams.env |

### `files/openwebrx/conf.d/`

| Fichero | Qué hace |
|---|---|
| `20-temporary-directory.conf` | Configuración: 20 temporary directory |
| `21-disable-ipv6.conf` | Configuración: 21 disable ipv6 |

### `files/share/bricohams-ctcss/`

| Fichero | Qué hace |
|---|---|
| `bricohams-ctcss.js` | bricohams-ctcss.js · squelch por subtono CTCSS («Subtono FM») en la |
| `bricohams_ctcss.py` | BricoHams - Squelch por subtono CTCSS para la demodulacion FM (nfm) de OpenWebRX+. |

### `files/share/bricohams-rbimport/`

| Fichero | Qué hace |
|---|---|
| `bricohams_rbimport.py` | owrx/controllers/settings/bricohams_rbimport.py (BricoHams) |

### `files/web/`

Portal estático /bricohams/ y página de privacidad.

| Fichero | Qué hace |
|---|---|
| `index.html.tmpl` | Plantilla de la portada web de la estación rellenada desde bricohams.env |
| `privacidad.html` | Página HTML: privacidad |

### `firmware/pico-io/`

MicroPython de la Raspberry Pi Pico (sensores y ventiladores).

| Fichero | Qué hace |
|---|---|
| `main.py` | bricohams-io · EA5KAO · BricoHams — firmware MicroPython para Raspberry Pi Pico |

### `firmware/rak4631-lora-aprs/`

Firmware iGate LoRa APRS (solo RX) para RAK4631 y placas compatibles (PlatformIO).

| Fichero | Qué hace |
|---|---|
| `aprs_utils.cpp` | BricoHams RAK4631 LoRa APRS · EA5KAO / BricoHams · GPL-3.0-or-later (ver LICENSE). |
| `aprs_utils.h` | BricoHams RAK4631 LoRa APRS · EA5KAO / BricoHams · GPL-3.0-or-later (ver LICENSE). |
| `board_pinout.h` | BricoHams RAK4631 LoRa APRS · port de LoRa APRS iGate (CA2RXU) a WisBlock |
| `bricohams_rak_aprs.cpp` | BricoHams RAK4631 LoRa APRS · port de LoRa APRS iGate (CA2RXU) a WisBlock |
| `configuration.cpp` | BricoHams RAK4631 LoRa APRS · port de LoRa APRS iGate (CA2RXU) a WisBlock |
| `configuration.h` | BricoHams RAK4631 LoRa APRS · port de LoRa APRS iGate (CA2RXU) a WisBlock |
| `digi_utils.cpp` | BricoHams RAK4631 LoRa APRS · port de LoRa APRS iGate (CA2RXU) a WisBlock |
| `digi_utils.h` | BricoHams RAK4631 LoRa APRS · port de LoRa APRS iGate (CA2RXU) a WisBlock |
| `kiss_protocol.h` | Copyright (C) 2026 Ricardo Guzman - CA2RXU |
| `kiss_utils.cpp` | Copyright (C) 2026 Ricardo Guzman - CA2RXU |
| `kiss_utils.h` | Copyright (C) 2026 Ricardo Guzman - CA2RXU |
| `LEEME.md` | BricoHams RAK APRS · firmware LoRa APRS para RAK4631 (WisBlock) |
| `LICENSE` | Licencia del firmware iGate LoRa-APRS para RAK4631 |
| `lora_utils.cpp` | BricoHams RAK4631 LoRa APRS · port de LoRa APRS iGate (CA2RXU) a WisBlock |
| `lora_utils.h` | BricoHams RAK4631 LoRa APRS · port de LoRa APRS iGate (CA2RXU) a WisBlock |
| `rak4631-lora-aprs.ino` | BricoHams RAK4631 LoRa APRS (port de LoRa APRS iGate de CA2RXU a WisBlock RAK4631). |
| `sensor_utils.cpp` | BricoHams RAK4631 LoRa APRS · EA5KAO / BricoHams · GPL-3.0-or-later (ver LICENSE). |
| `sensor_utils.h` | BricoHams RAK4631 LoRa APRS · EA5KAO / BricoHams · GPL-3.0-or-later (ver LICENSE). |

### `firmware/rak4631-lora-aprs/bin/`

| Fichero | Qué hace |
|---|---|
| `bricohams-rak4631-lora-aprs.hex` | Firmware iGate precompilado (Intel HEX, para nrfutil/SWD) |
| `bricohams-rak4631-lora-aprs.uf2` | Firmware iGate precompilado (UF2, arrastrar a la unidad del bootloader) |
| `bricohams-rak4631-lora-aprs.zip` | Paquete DFU del firmware iGate (adafruit-nrfutil por USB serie, el que usa el instalador) |
| `SHA256SUMS` | Sumas SHA-256 de los binarios del firmware iGate |
| `VERSION.json` | Datos JSON: VERSION |

### `firmware/rak4631-lora-aprs/test/`

| Fichero | Qué hace |
|---|---|
| `host_test.cpp` | Prueba en el PC de la lógica del firmware (sin radio): la compila y la llama tests/test_rak_aprs.py. |

### `firmware/rak4631-lora-aprs/test/shim/`

| Fichero | Qué hace |
|---|---|
| `Arduino.h` | Arduino.h mínimo para compilar en el PC la lógica del firmware (KISS, digipeater, APRS) |

### `hardware/anclajes/`

Crucetas y soportes impresos del mástil.

| Fichero | Qué hace |
|---|---|
| `anclajes_bricohams.scad` | ANCLAJES IMPRESOS BricoHams SDR · EA5KAO (v4) |

### `hardware/anclajes/render/`

| Fichero | Qué hace |
|---|---|
| `montaje.png` | Imagen / vista renderizada: montaje |

### `hardware/anclajes/stl/`

| Fichero | Qué hace |
|---|---|
| `adsb_tapa_tubo.stl` | Pieza 3D lista para imprimir: adsb tapa tubo |
| `cruceta_brazo_fibra_cuerpo.stl` | Pieza 3D lista para imprimir: cruceta brazo fibra cuerpo |
| `cruceta_brazo_fibra_tapa_brazo.stl` | Pieza 3D lista para imprimir: cruceta brazo fibra tapa brazo |
| `cruceta_brazo_fibra_tapa_fibra.stl` | Pieza 3D lista para imprimir: cruceta brazo fibra tapa fibra |
| `cruceta_brazo_tubo_cuerpo.stl` | Pieza 3D lista para imprimir: cruceta brazo tubo cuerpo |
| `cruceta_brazo_tubo_tapa.stl` | Pieza 3D lista para imprimir: cruceta brazo tubo tapa |
| `cruceta_mastil_brazo_cuerpo.stl` | Pieza 3D lista para imprimir: cruceta mastil brazo cuerpo |
| `cruceta_mastil_brazo_tapa_brazo.stl` | Pieza 3D lista para imprimir: cruceta mastil brazo tapa brazo |
| `cruceta_mastil_brazo_tapa_mastil.stl` | Pieza 3D lista para imprimir: cruceta mastil brazo tapa mastil |
| `cruceta_mastil_quad_cuerpo.stl` | Pieza 3D lista para imprimir: cruceta mastil quad cuerpo |
| `cruceta_mastil_quad_tapa_boom.stl` | Pieza 3D lista para imprimir: cruceta mastil quad tapa boom |
| `cruceta_mastil_quad_tapa_mastil.stl` | Pieza 3D lista para imprimir: cruceta mastil quad tapa mastil |
| `pico_soporte.stl` | Pieza 3D lista para imprimir: pico soporte |
| `pluvio_plataforma.stl` | Pieza 3D lista para imprimir: pluvio plataforma |
| `pluvio_vaso.stl` | Pieza 3D lista para imprimir: pluvio vaso |
| `sensor_viento_brida.stl` | Pieza 3D lista para imprimir: sensor viento brida |

### `hardware/antenas/`

Antenas propias: modelo OpenSCAD, piezas STL y simulación NEC2.

| Fichero | Qué hace |
|---|---|
| `antenas_bricohams.scad` | Piezas impresas de las antenas y soportes BricoHams SDR · EA5KAO |

### `hardware/antenas/render/`

| Fichero | Qué hace |
|---|---|
| `piezas.png` | Imagen / vista renderizada: piezas |

### `hardware/antenas/sim/`

| Fichero | Qué hace |
|---|---|
| `discone.py` | Discone de banda ancha (MULTIPERFIL) con látigo opcional para bajar en frecuencia. |
| `gp1090.py` | Antena ADS-B 1090 MHz: plano de tierra λ/4 con 4 radiales a 45° («araña»). |
| `necsim.py` | Motor mínimo NEC2 (nec2c) para las antenas BricoHams. |
| `opt_quad.py` | Optimizador NEC de la antena quad 2 m/70 cm (longitudes y separación) |
| `quad_2m70.py` | Quad de doble resonancia 2 m / 70 cm para el receptor RADIOAFICIONADOS. |

### `hardware/antenas/sim/resultados/`

| Fichero | Qué hace |
|---|---|
| `discone.json` | Datos JSON: discone |
| `discone.png` | Imagen / vista renderizada: discone |
| `gp1090.json` | Datos JSON: gp1090 |
| `quad_2m70.json` | Datos JSON: quad 2m70 |
| `quad_2m70.png` | Imagen / vista renderizada: quad 2m70 |

### `hardware/antenas/stl/`

| Fichero | Qué hace |
|---|---|
| `adsb_base.stl` | Pieza 3D lista para imprimir: adsb base |
| `adsb_radomo.stl` | Pieza 3D lista para imprimir: adsb radomo |
| `adsb_tapa.stl` | Pieza 3D lista para imprimir: adsb tapa |
| `brazo_mastil.stl` | Pieza 3D lista para imprimir: brazo mastil |
| `clip_filtro.stl` | Pieza 3D lista para imprimir: clip filtro |
| `discone_adaptador_mastil.stl` | Pieza 3D lista para imprimir: discone adaptador mastil |
| `discone_aislador.stl` | Pieza 3D lista para imprimir: discone aislador |
| `discone_capuchon.stl` | Pieza 3D lista para imprimir: discone capuchon |
| `discone_plantilla_cono.stl` | Pieza 3D lista para imprimir: discone plantilla cono |
| `discone_plantilla_disco.stl` | Pieza 3D lista para imprimir: discone plantilla disco |
| `funda_n.stl` | Pieza 3D lista para imprimir: funda n |
| `funda_sma.stl` | Pieza 3D lista para imprimir: funda sma |
| `gps_soporte.stl` | Pieza 3D lista para imprimir: gps soporte |
| `mla_caja_base.stl` | Pieza 3D lista para imprimir: mla caja base |
| `mla_caja_tapa.stl` | Pieza 3D lista para imprimir: mla caja tapa |
| `mla_clip_lazo.stl` | Pieza 3D lista para imprimir: mla clip lazo |
| `mla_cruz.stl` | Pieza 3D lista para imprimir: mla cruz |
| `mla_junta.stl` | Pieza 3D lista para imprimir: mla junta |
| `quad_abrazadera.stl` | Pieza 3D lista para imprimir: quad abrazadera |
| `quad_alim_2m.stl` | Pieza 3D lista para imprimir: quad alim 2m |
| `quad_alim_70.stl` | Pieza 3D lista para imprimir: quad alim 70 |
| `quad_buje_2m.stl` | Pieza 3D lista para imprimir: quad buje 2m |
| `quad_buje_70.stl` | Pieza 3D lista para imprimir: quad buje 70 |
| `quad_clip_70.stl` | Pieza 3D lista para imprimir: quad clip 70 |
| `quad_puntera_6.stl` | Pieza 3D lista para imprimir: quad puntera 6 |
| `quad_puntera_8.stl` | Pieza 3D lista para imprimir: quad puntera 8 |
| `separador_coax.stl` | Pieza 3D lista para imprimir: separador coax |
| `soporte_fibra.stl` | Pieza 3D lista para imprimir: soporte fibra |
| `tapon_brazo.stl` | Pieza 3D lista para imprimir: tapon brazo |
| `tapon_varilla.stl` | Pieza 3D lista para imprimir: tapon varilla |

### `hardware/caja/`

Caja de intemperie v2 (mástil).

| Fichero | Qué hace |
|---|---|
| `caja_bricohams.scad` | Caja de intemperie BricoHams SDR · EA5KAO · Mi QTH (Región de Murcia) |
| `README.md` | Caja de intemperie BricoHams SDR |

### `hardware/caja/render/`

| Fichero | Qué hace |
|---|---|
| `cuerpo_impresion.png` | Imagen / vista renderizada: cuerpo impresion |
| `despiece.png` | Imagen / vista renderizada: despiece |
| `garita_base.png` | Imagen / vista renderizada: garita base |
| `interior.png` | Imagen / vista renderizada: interior |
| `montaje.png` | Imagen / vista renderizada: montaje |
| `montaje_inferior.png` | Imagen / vista renderizada: montaje inferior |
| `montaje_trasera.png` | Imagen / vista renderizada: montaje trasera |
| `pasamuros_usb.png` | Imagen / vista renderizada: pasamuros usb |
| `placa_electronica.png` | Imagen / vista renderizada: placa electronica |
| `soporte_camara.png` | Imagen / vista renderizada: soporte camara |
| `soporte_mastil.png` | Imagen / vista renderizada: soporte mastil |
| `tapa_interior.png` | Imagen / vista renderizada: tapa interior |
| `tapa_potencia.png` | Imagen / vista renderizada: tapa potencia |
| `tejadillo.png` | Imagen / vista renderizada: tejadillo |
| `visera.png` | Imagen / vista renderizada: visera |

### `hardware/caja/stl/`

| Fichero | Qué hace |
|---|---|
| `cuerpo.stl` | Pieza 3D lista para imprimir: cuerpo |
| `garita_base.stl` | Pieza 3D lista para imprimir: garita base |
| `garita_plato.stl` | Pieza 3D lista para imprimir: garita plato |
| `garita_tapa.stl` | Pieza 3D lista para imprimir: garita tapa |
| `junta_tapa.stl` | Pieza 3D lista para imprimir: junta tapa |
| `junta_ventana.stl` | Pieza 3D lista para imprimir: junta ventana |
| `pasamuros_usb.stl` | Pieza 3D lista para imprimir: pasamuros usb |
| `placa_electronica.stl` | Pieza 3D lista para imprimir: placa electronica |
| `placa_potencia.stl` | Pieza 3D lista para imprimir: placa potencia |
| `separador_ir.stl` | Pieza 3D lista para imprimir: separador ir |
| `soporte_camara.stl` | Pieza 3D lista para imprimir: soporte camara |
| `soporte_mastil.stl` | Pieza 3D lista para imprimir: soporte mastil |
| `tapa.stl` | Pieza 3D lista para imprimir: tapa |
| `tapa_potencia.stl` | Pieza 3D lista para imprimir: tapa potencia |
| `tejadillo.stl` | Pieza 3D lista para imprimir: tejadillo |
| `visera.stl` | Pieza 3D lista para imprimir: visera |

### `hardware/caja_v3/`

Caja v3 en dos módulos (electrónica + potencia).

| Fichero | Qué hace |
|---|---|
| `caja_v3.scad` | Caja v3 BricoHams SDR · EA5KAO — DOS MÓDULOS al pie del mástil (~5 m) |

### `hardware/caja_v3/render/`

| Fichero | Qué hace |
|---|---|
| `electronica_inferior.png` | Imagen / vista renderizada: electronica inferior |
| `electronica_interior.png` | Imagen / vista renderizada: electronica interior |
| `electronica_montaje.png` | Imagen / vista renderizada: electronica montaje |
| `potencia_interior.png` | Imagen / vista renderizada: potencia interior |
| `potencia_montaje.png` | Imagen / vista renderizada: potencia montaje |

### `hardware/caja_v3/stl/`

| Fichero | Qué hace |
|---|---|
| `electronica_bandeja.stl` | Pieza 3D lista para imprimir: electronica bandeja |
| `electronica_capota.stl` | Pieza 3D lista para imprimir: electronica capota |
| `electronica_cuerpo.stl` | Pieza 3D lista para imprimir: electronica cuerpo |
| `electronica_junta_tapa.stl` | Pieza 3D lista para imprimir: electronica junta tapa |
| `electronica_placa_rejilla.stl` | Pieza 3D lista para imprimir: electronica placa rejilla |
| `electronica_pletina_pared.stl` | Pieza 3D lista para imprimir: electronica pletina pared |
| `electronica_poste_bandeja.stl` | Pieza 3D lista para imprimir: electronica poste bandeja |
| `electronica_rejilla_ventilador.stl` | Pieza 3D lista para imprimir: electronica rejilla ventilador |
| `electronica_soporte_camara.stl` | Pieza 3D lista para imprimir: electronica soporte camara |
| `electronica_soporte_dongle.stl` | Pieza 3D lista para imprimir: electronica soporte dongle |
| `electronica_soporte_hub.stl` | Pieza 3D lista para imprimir: electronica soporte hub |
| `electronica_soporte_lilygo.stl` | Pieza 3D lista para imprimir: electronica soporte lilygo |
| `electronica_soporte_mastil.stl` | Pieza 3D lista para imprimir: electronica soporte mastil |
| `electronica_soporte_sdrplay.stl` | Pieza 3D lista para imprimir: electronica soporte sdrplay |
| `electronica_soporte_wago.stl` | Pieza 3D lista para imprimir: electronica soporte wago |
| `electronica_tapa.stl` | Pieza 3D lista para imprimir: electronica tapa |
| `electronica_tapon_n.stl` | Pieza 3D lista para imprimir: electronica tapon n |
| `electronica_tapon_pg.stl` | Pieza 3D lista para imprimir: electronica tapon pg |
| `electronica_tejadillo.stl` | Pieza 3D lista para imprimir: electronica tejadillo |
| `electronica_visera.stl` | Pieza 3D lista para imprimir: electronica visera |
| `potencia_brida_cargador.stl` | Pieza 3D lista para imprimir: potencia brida cargador |
| `potencia_cuerpo.stl` | Pieza 3D lista para imprimir: potencia cuerpo |
| `potencia_junta_tapa.stl` | Pieza 3D lista para imprimir: potencia junta tapa |
| `potencia_placa_rejilla.stl` | Pieza 3D lista para imprimir: potencia placa rejilla |
| `potencia_pletina_pared.stl` | Pieza 3D lista para imprimir: potencia pletina pared |
| `potencia_soporte_mastil.stl` | Pieza 3D lista para imprimir: potencia soporte mastil |
| `potencia_soporte_schuko.stl` | Pieza 3D lista para imprimir: potencia soporte schuko |
| `potencia_tapa.stl` | Pieza 3D lista para imprimir: potencia tapa |
| `potencia_tapon_pg.stl` | Pieza 3D lista para imprimir: potencia tapon pg |
| `potencia_tejadillo.stl` | Pieza 3D lista para imprimir: potencia tejadillo |

### `hardware/gcode/`

| Fichero | Qué hace |
|---|---|
| `1004-1742-electronica_tapa_plate(01)_PETG_0.16_8h42m34s.gcode` | HEADER_BLOCK_START |

### `owrx-clone/`

Herramienta independiente (MIT) para clonar una instalación de OpenWebRX+.

| Fichero | Qué hace |
|---|---|
| `instalar.sh` | Instala owrx-clone en este equipo (o lo quita con --quitar) |
| `LICENSE` | Licencia de owrx-clone |
| `owrx-clone` | owrx-clone · clonar una instalación de OpenWebRX+ a otro equipo |
| `owrx-clone.1` | Página de manual (man) de owrx-clone |
| `README.en.md` | owrx-clone · move your OpenWebRX+ to another machine |
| `README.md` | owrx-clone · lleva tu OpenWebRX+ a otro equipo |

### `tests/`

Pruebas automáticas (bash tests/run_tests.sh).

| Fichero | Qué hace |
|---|---|
| `meteo_ejemplo.json` | Molina de Segura (Los Valientes) |
| `run_tests.sh` | Lanza todas las pruebas: shellcheck, sintaxis y tests de Python |
| `test_actualizar.py` | v4.1 · install.sh --actualizar. |
| `test_anclajes.py` | v4: anclajes impresos. Cada pieza de tools/anclajes.sh tiene selector en el |
| `test_api.py` | v4: bricohams-api (ficha de indicativos) con HamQTH, RadioID y QRZ simulados. |
| `test_audio_navegador.py` | v4.2 · Plugins de audio en un navegador DE VERDAD (Chromium sin pantalla, Playwright). |
| `test_audio_plugins.py` | v4.2 · Plugins de audio (audio_cadena, filtro_audio, dsp_audio) con node |
| `test_blindaje.py` | v4.4 · bricohams-blindaje sobre un sistema de mentira (BH_RAIZ): el cortafuegos que genera |
| `test_bookmarks_io.py` | v5.0 · bricohams-owrx-bookmarks-io: botones Importar/Exportar en /settings/bookmarks (solo |
| `test_caja.py` | Comprueba la caja: que están todas las piezas, que caben en la Kobra S1 |
| `test_ctcss_patch.py` | v5.0 · bricohams-owrx-ctcss: subtono CTCSS («Subtono FM») en bookmarks y squelch CTCSS. |
| `test_env_red.py` | v4.2 · Los dos fallos de la instalación real en la Pi de EA5KAO |
| `test_fan.py` | Curva de los ventiladores de la caja (bricohams-fan). |
| `test_ft2.py` | v4 (experimental): FT2 en OpenWebRX+. |
| `test_git_sanear.py` | v5.1 · tools/git_sanear.sh y tools/datos_personales.py (manual 38). |
| `test_instalador_docker.py` | Verifica backend Docker de OpenWebRX+ sin requerir un daemon Docker. |
| `test_instalador_os.py` | v3.1: el instalador vale para Trixie (Debian 13) y Bookworm (Debian 12). |
| `test_instalador_perfil.py` | v4.2 · owrx-clone dentro del instalador BricoHams |
| `test_live_map.py` | ADS-B reciente, APRS-IS y mensajes de chat sin transmitir por RF. |
| `test_locator_bookmarks.py` | Locator conversion and geographic bookmark selection from a curated catalog. |
| `test_locator_es.py` | v4.3 · Marcadores y meteo de zona para CUALQUIER locator de España (manual 32) |
| `test_mesh_admin.py` | v4.5 · bricohams-mesh-admin: el panel Meshtastic 433/868 solo existe dentro de /settings |
| `test_mesh_owrx.py` | v4.5 · integración directa con OpenWebRX+ por su MQTT: el publicador MQTT mínimo contra un broker de |
| `test_meteo.py` | bricohams-meteo con respuestas simuladas de AEMET (una estación con 404) y Open-Meteo. |
| `test_monitorizacion.py` | v5.0 · paso_monitorizacion de install.sh (Prometheus + node-exporter + Grafana). |
| `test_owrx_clone.py` | v4.2 · owrx-clone: exportar una estación OpenWebRX+ de mentira (un árbol de ficheros con su |
| `test_owrx_clone_docker.py` | v4.3 · owrx-clone 1.1 con OpenWebRX+ en Docker, sin Docker de verdad: una orden «docker» de |
| `test_pico_io.py` | v4: puente USB con la Pico «bricohams-io». |
| `test_rak_aprs.py` | v4.5 · RAK4631 LoRa APRS: la lógica del firmware compilada en el PC (KISS, digipeater, baliza, |
| `test_rbimport.py` | v5.0 · bricohams-owrx-rbimport: importador de repetidores de RepeaterBook. |
| `test_render_settings.py` | Rellena settings.json.tmpl con bricohams.env.example y comprueba receptores, |
| `test_repeaterbook.py` | v5.0 · bricohams-owrx-repeaterbook: campo «RepeaterBook API key» en /settings/general (solo |
| `test_satpass.py` | v4: pases de satélites (bricohams-satpass) comparados con Skyfield cuando está |
| `test_ssl_admin.py` | v4.2 · SSL_MODO (decisión de EA5KAO: «el certificado SSL es solo para la página de settings»). |
| `test_v3_hardware.py` | v3: comprueba las piezas de antenas y de la caja v3 (selector en el .scad, |
| `test_v45_dispositivos.py` | v4.5 · inventario de dispositivos con un /sys de mentira (SDR por su serie, RAK4631, LilyGO, lo que falta |
| `test_v51_aprs_web.py` | v5.1 · Interfaz web del APRS: la pasarela del RAK (bricohams-rak-aprs) con su API local |
| `test_v51_mesh_puente.py` | v5.1 · bricohams-mesh-puente: interfaz web de Meshtastic para el LilyGO 433 por USB. |
| `test_viento_lluvia.py` | Viento RS485 (Modbus RTU), pluviómetro y paquete APRS WX completo. |
| `test_visitas.py` | v4: bricohams-visitas. IP parcial, GeoIP (simulada), avisos de Telegram con |
| `test_wx_bme280.py` | Compensación BME280/BMP280 contra el ejemplo de la hoja de datos de Bosch |

### `tests/datos/`

Datos de prueba (fixtures) usados por los tests.

| Fichero | Qué hace |
|---|---|
| `ft2_261004_120015.wav` | Audio de prueba: ft2 261004 120015 |
| `iss_omm.json` | Datos JSON: iss omm |

### `tests/datos/owrx/htdocs/lib/`

| Fichero | Qué hace |
|---|---|
| `jquery-3.7.1.min.js` | Copia de referencia de OpenWebRX+ usada por los tests de parches (jQuery) |
| `MessagePanel.js` | Copia de referencia de OpenWebRX+ (MessagePanel.js) para probar los parches |

### `tests/datos/owrx/owrx/`

| Fichero | Qué hace |
|---|---|
| `modes.py` | Copia de referencia de OpenWebRX+ (owrx/modes.py) para probar los parches |
| `wsjt.py` | Copia de referencia de OpenWebRX+ (owrx/wsjt.py) para probar el parche FT2 |

### `tests/datos/owrx-1.2.126/`

| Fichero | Qué hace |
|---|---|
| `htdocs_index.html` | Página HTML: htdocs index |
| `htdocs_lib_settings_BookmarkTable.js` | Original de OpenWebRX+ 1.2.126 (BookmarkTable.js) para probar parches de marcadores/CTCSS |
| `owrx_bookmarks.py` | Original de OpenWebRX+ 1.2.126 (owrx/bookmarks.py) para probar parches de marcadores |
| `owrx_controllers_settings_bookmarks.py` | Original de OpenWebRX+ 1.2.126 (controlador de marcadores) para probar parches |
| `owrx_dsp.py` | Original de OpenWebRX+ 1.2.126 (owrx/dsp.py) para probar el parche CTCSS |

### `tools/`

Generadores y herramientas de desarrollo (esquemas, datos, STL, TAK, compilación RAK).

| Fichero | Qué hace |
|---|---|
| `activar_mapa_local.sh` | Despliega el mapa local sin reinstalar ni reconfigurar RadarBox/MLAT. |
| `anclajes.sh` | Exporta los anclajes impresos (v4): crucetas para unir tubos sin abrazaderas en U, |
| `antenas.sh` | Exporta las piezas impresas de antenas y soportes, comprueba que caben en |
| `branding.py` | v4: rehace la imagen superior de OpenWebRX (files/branding/receiver_top_photo.png) |
| `caja.sh` | Exporta todas las piezas de la caja a STL, comprueba que caben en la |
| `caja_v3.sh` | Exporta las piezas de la caja v3 (módulos de electrónica y de potencia), |
| `canales.py` | v4: genera docs/CANALES_Y_FRECUENCIAS.md a partir de data/marcadores_v4.json y de |
| `compilar_rak.sh` | Compila el firmware iGate para todas las placas (PlatformIO) y deja los binarios |
| `datos.py` | Genera docs/DATOS.md a partir de los ficheros del repositorio |
| `datos_personales.py` | tools/datos_personales.py · BricoHams SDR (v5.1, manual 38) |
| `datos_personales_huellas.txt` | Huellas SHA-256 de datos personales que no deben ir al GitHub público (manual 38). |
| `esquemas.py` | Genera los esquemas de docs/esquemas/ (SVG, y PNG si hay cairosvg). |
| `estructura.py` | Genera docs/ESTRUCTURA_FICHEROS.md (este árbol con descripciones) |
| `git_sanear.sh` | tools/git_sanear.sh · BricoHams SDR (v5.1, manual 38) |
| `instalar_tak.sh` | Instala OpenTAKServer (venv, PostgreSQL, CA, usuarios con clave aleatoria en /etc/bricohams/tak-access.txt) |
| `locator_catalogo.py` | v4.3 · Construye data/locator/catalogo_es.json, el catálogo nacional que usa el instalador |
| `marcadores.py` | Genera y fusiona marcadores de OpenWebRX |
| `mastil.py` | Plan del mástil BricoHams: posición de cada antena, separaciones entre las |
| `planos_antenas.py` | Planos acotados de las antenas a partir de los resultados NEC2 |
| `stl_util.py` | Utilidades STL sin dependencias. |
| `tak-requirements.txt` | Versiones fijadas de Python para OpenTAKServer |
