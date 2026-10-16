# Módulos creados y su desarrollo

[English version](en/MODULE_DEVELOPMENT.md) · [Guía visual de instalación](GUIA_VISUAL_MODULOS.md) ·
[Catálogo técnico](COMPONENTES.md) · [Decisiones (ADR)](ARQUITECTURA.md) · [Historial](../CHANGELOG.md)

Este documento enumera los módulos desarrollados para BricoHams SDR y explica,
para cada uno, **por qué se creó, cómo se diseñó, qué ficheros lo forman, cómo se
instala, cómo se prueba y en qué estado está**. La instalación paso a paso con
capturas está en la guía visual; aquí se documenta el desarrollo.

> **Privacidad:** los ejemplos usan valores genéricos. Indicativos, coordenadas,
> IP, UUID, claves y contraseñas se configuran solo en `/etc/bricohams/bricohams.env`
> o en ficheros secretos de la Pi y nunca se copian en la documentación.

## Índice de módulos

| # | Módulo | Tipo | Paso/orden principal | Estado en el kit |
|---|---|---|---|---|
| 1 | [Instalador, configuración y actualizador](#1-instalador-configuración-y-actualizador) | sistema | `install.sh` | integrado |
| 2 | [OpenWebRX+ nativo y Docker](#2-openwebrx-nativo-y-docker) | receptor | `openwebrx`, `configuracion` | integrado |
| 3 | [owrx-clone](#3-owrx-clone) | herramienta | `--exportar`, `--importar` | integrado y publicable |
| 4 | [Plugins web y audio en el navegador](#4-plugins-web-y-audio-en-el-navegador) | interfaz | `plugins` | integrado |
| 5 | [Bookmarks, importación/exportación y CTCSS](#5-bookmarks-importaciónexportación-y-ctcss) | OpenWebRX+ | `configuracion`, `web` | integrado |
| 6 | [Importador de RepeaterBook](#6-importador-de-repeaterbook) | OpenWebRX+ | `web` | integrado |
| 7 | [Locator, zona y canales](#7-locator-zona-y-canales) | datos | `configuracion` | integrado |
| 8 | [Meshtastic 868/433 y panel privado](#8-meshtastic-868433-y-panel-privado) | radio/web | `meshtastic`, `lilygo` | integrado |
| 9 | [iGate LoRa APRS con RAK4631](#9-igate-lora-aprs-con-rak4631) | radio/firmware | `rak` | integrado |
| 10 | [ADS-B, RadarBox, mapa y ficha del avión](#10-ads-b-radarbox-mapa-y-ficha-del-avión) | ADS-B | `adsb`, `web` | integrado |
| 11 | [Envío ADS-B a map.flights](#11-envío-ads-b-a-mapflights) | ADS-B | `adsb` | opcional; verificado en una estación |
| 12 | [Plugin map.flights para OpenWebRX+](#12-plugin-mapflights-para-openwebrx) | mapa y `/settings` | `web` | integrado en el kit, no desplegado |
| 13 | [Meteorología, sensores, Pico I/O y ventilación](#13-meteorología-sensores-pico-io-y-ventilación) | sensores | `meteo`, `sensor`, `io`, `ventilacion` | integrado |
| 14 | [Cámara](#14-cámara) | vídeo | `camara` | integrado |
| 15 | [Satélites y FT2](#15-satélites-y-ft2) | radio | `satelites`, `ft2` | integrado; FT2 experimental |
| 16 | [Web, SSL, API, visitas y chat](#16-web-ssl-api-visitas-y-chat) | web | `web`, `visitas` | integrado |
| 17 | [TAK y mapa local](#17-tak-y-mapa-local) | servicio | `tak` | integrado |
| 18 | [Monitorización](#18-monitorización) | observabilidad | `monitorizacion` | opcional |
| 19 | [Seguridad y bloqueo](#19-seguridad-y-bloqueo) | seguridad | `bricohams-blindaje`, panel Seguridad | integrado |
| 20 | [Copias, copia remota y limpieza automática](#20-copias-copia-remota-y-limpieza-automática) | operación | `tareas`, `herramientas` | integrado |
| 21 | [Hardware y documentación generada](#21-hardware-y-documentación-generada) | diseño/documentación | `tools/` | integrado |
| 22 | [Registro voluntario de oyentes](#22-registro-voluntario-de-oyentes) | web/privacidad | `web` | integrado en el kit, no desplegado |
| 23 | [Solo HTTPS, mapa local ADS-B/AIS, políticas, idioma y logo](#23-solo-https-mapa-local-ads-bais-políticas-idioma-y-logo) | web/mapa/privacidad | `web`, `ais`, `configuracion`, `plugins` | integrado; AIS opcional |

**Leyenda de estado:** *integrado* = incluido en el kit y cubierto por pruebas;
*opcional* = solo actúa si se habilita en `bricohams.env`; *generado, no
desplegado* = código y pruebas listos, sin instalar en ninguna estación.

## Método de desarrollo común

1. **Requisito y decisión:** cada cambio de diseño se registra como ADR en
   [ARQUITECTURA.md](ARQUITECTURA.md).
2. **Configuración única:** las variables nuevas se añaden a
   [`bricohams.env.example`](../bricohams.env.example) con valores genéricos.
   `bricohams-env.py` lee el fichero sin ejecutarlo (ADR-38).
3. **Paso idempotente:** `install.sh` añade o amplía un `paso_*`, que se puede
   repetir con `--solo`. Los parches de OpenWebRX+ son reversibles.
4. **Seguridad:** servicios en `127.0.0.1`, administración bajo `/settings`,
   secretos con permisos `600` o `LoadCredential`.
5. **Pruebas:** cada módulo tiene pruebas en `tests/` con raíces falsas en `/tmp`.
   La suite completa se ejecuta con:

```bash
cd ~/bricohams-sdr
bash tests/run_tests.sh
```

6. **Documentación:** manual del módulo, ficha en [COMPONENTES.md](COMPONENTES.md),
   entrada en [CHANGELOG.md](../CHANGELOG.md) y ficha visual generada.
7. **Despliegue:** solo con autorización, copia previa verificada, ubicación
   anotada y procedimiento de restauración disponible.

```bash
# Instalar o repetir solo los pasos de un módulo
sudo bash install.sh --solo paso1,paso2
# Comprobar el estado general
sudo bricohams-check
```

---

## 1. Instalador, configuración y actualizador

- **Objetivo:** montar una estación completa en una Raspberry Pi 5 desde cero y
  poder repetir o actualizar cualquier parte sin perder la configuración.
- **Desarrollo:** v1.0 nace como instalador para Bookworm; v2.0 saca las claves
  del git (ADR-12); v3.1–v3.3 añade Trixie y corrige dependencias reales;
  v4.1 incorpora `--actualizar` con huellas por paso (ADR-37); ADR-38 cambia la
  lectura del `.env` para no ejecutarlo; ADR-39 evita que el instalador corte su
  propia red. Actualmente tiene 29 pasos.
- **Diseño:** orden declarado en `PASOS=`, una función `paso_*` por paso,
  huellas en `/var/lib/bricohams/kit-estado` para repetir solo lo modificado.
- **Ficheros:** [`install.sh`](../install.sh), `files/bin/bricohams-env.py`,
  `files/bin/bricohams-check`, `files/bin/bricohams-banner`, `files/motd/20-bricohams`.
- **Comandos:**

```bash
sudo bash install.sh                 # instalación completa
sudo bash install.sh --solo web      # repetir un paso
sudo bash install.sh --actualizar --simular
```

- **Pruebas:** `test_instalador_os.py`, `test_instalador_perfil.py`,
  `test_env_red.py`, `test_actualizar.py`.
- **Límites:** necesita Raspberry Pi OS de 64 bits y permisos de administrador.
- **Documentación:** [01](manuales/01_PREPARACION.md), [02](manuales/02_INSTALACION.md),
  [09](manuales/09_MANTENIMIENTO.md), [29](manuales/29_ACTUALIZAR.md).

## 2. OpenWebRX+ nativo y Docker

- **Objetivo:** ofrecer el receptor web con varios SDR, perfiles HF/VHF/UHF y
  marcadores, igual en instalación nativa o en contenedor.
- **Desarrollo:** v1.0 crea los receptores; ADR-02 asigna cada SDR por número de
  serie; ADR-03 resuelve HF por muestreo directo; ADR-27 prepara SDRplay;
  v4.3 añade Docker con red host y volúmenes en la Pi (ADR-44).
- **Diseño:** `settings.json` se genera desde plantilla y `bricohams.env`; los
  números de serie se resuelven con `bricohams-sdr-serials`.
- **Ficheros:** `files/openwebrx/settings.json.tmpl`, `files/openwebrx/bookmarks.json`,
  `files/bin/bricohams-render-settings.py`, `files/bin/bricohams-sdr-serials`,
  `files/bin/bricohams-docker-compose.py`.
- **Comandos:**

```bash
sudo bash install.sh --solo openwebrx,rtlsdr,configuracion,plugins
systemctl status openwebrx --no-pager
```

- **Pruebas:** `test_render_settings.py`, `test_instalador_docker.py`.
- **Documentación:** [03](manuales/03_SDR_Y_SERIES.md), [08](manuales/08_SDRPLAY.md),
  [33](manuales/33_OPENWEBRX_DOCKER.md).

## 3. owrx-clone

- **Objetivo:** exportar una instalación de OpenWebRX+ a un perfil portable e
  importarlo en otro equipo con copia previa y vuelta atrás.
- **Desarrollo:** creado en v4.2 como herramienta genérica con licencia MIT.
  Antes de publicarlo pasó dos revisiones de seguridad que corrigieron rutas
  peligrosas en `data_directory`, escritura a través de enlaces simbólicos,
  orden de copia previa y restos de importaciones interrumpidas. La versión 1.1
  unifica perfiles nativos y Docker (ADR-45).
- **Diseño:** niveles `config`, `etc`, `web`, `paquetes`, `sistema`, `parches` y
  `extra`; SHA-256 de contenido; lista de rutas permitidas; modo `--simular`;
  `--publico` para quitar datos privados y `--cifrar` para proteger el perfil.
- **Ficheros:** [owrx-clone/](../owrx-clone/) (`owrx-clone`, `owrx-clone.1`,
  `instalar.sh`, `README.md`, `README.en.md`, `LICENSE`).
- **Comandos:**

```bash
sudo owrx-clone exportar
owrx-clone ver perfil.owrx.tar.gz
sudo owrx-clone importar perfil.owrx.tar.gz --simular
sudo owrx-clone importar perfil.owrx.tar.gz
sudo owrx-clone deshacer
```

- **Pruebas:** `test_owrx_clone*.py`, con un caso por cada fallo de seguridad corregido.
- **Documentación:** [31](manuales/31_CLONAR_OPENWEBRX.md), ADR-42 y ADR-45.

## 4. Plugins web y audio en el navegador

- **Objetivo:** ampliar el receptor con controles locales, datos de estación,
  fichas digitales, seguimiento y tratamiento de audio sin trasladar el DSP al
  servidor.
- **Evolución:** v1.0 incorpora plugins locales (ADR-11); v4 los amplía; v4.2
  añade la cadena de audio de navegador (ADR-41); v5 incorpora las etiquetas DX
  en la integración Rig Skin y la ficha de aeronaves.
- **Diseño compartido:** `receiver/init.js` configura y carga cada plugin.
  Los secretos y las consultas con credenciales permanecen en servicios del
  servidor; al navegador solo se entregan datos necesarios para la interfaz.
  El cliente no debe cambiar la señal que consumen los decodificadores.

### `solar`

El plugin cliente calcula la presentación de día/noche con la ubicación
redondeada insertada por el instalador. Se separa configuración (`init.js`) de
presentación (`receiver/solar/solar.js`) y no envía la ubicación a un proveedor
externo.

### `meteo`

`receiver/meteo/meteo.js` representa estaciones cercanas y previsión desde JSON
local. `bricohams-meteo.py` obtiene y transforma los datos fuera del navegador;
la clave de AEMET no se distribuye al cliente. La caché y la actualización
periódica reducen peticiones. Prueba asociada: `test_meteo.py`.

### `camara`

`receiver/camara/camara.js` presenta capturas servidas por la estación. El
intervalo lo gobierna `CAM_SNAPSHOT_SECONDS`; las capturas se excluyen de la
copia general de código para no sobrescribir las imágenes generadas.

### `bricohams`

`receiver/bricohams/bricohams.js` agrega la identidad y el enlace institucional
sin alterar el núcleo de OpenWebRX+. Se carga junto al resto de plugins locales.

### `banderas`

`receiver/banderas/banderas.js` reutiliza el código de país (`ccode`) que entrega
OpenWebRX+ para las decodificaciones digitales. No hace geolocalización ni
consulta servicios externos desde el navegador.

### `dvficha`

`receiver/dvficha/dvficha.js` presenta los datos del operador digital a partir
del endpoint `/bricohams/api/indicativo`. `bricohams-api.py` consulta HamQTH,
RadioID y, si está configurado, QRZ XML; aplica caché y filtra los campos
devueltos. Las credenciales solo se leen en el servidor. Pruebas relacionadas:
`test_api.py`.

### `satelites`

`receiver/satelites/satelites.js` presenta los pases que prepara
`bricohams-satpass` en `satelites/pases.json` y enlaza el botón Escuchar con el
plugin Doppler externo. La lógica de predicción y la interfaz quedan separadas.
Prueba asociada: `test_satpass.py`.

### `visitas`

`receiver/visitas/visitas.js` presenta el contador y la información de visitas.
El cálculo y la conservación de datos están del lado del servidor; la interfaz
enlaza el aviso de privacidad. No requiere Supabase. Prueba: `test_visitas.py`.

### `audio_cadena`, `filtro_audio` y `dsp_audio`

`audio_cadena` proporciona el punto de conexión entre el `AudioWorklet` y el
volumen. `filtro_audio` y `dsp_audio` se registran como etapas separadas y se
cargan después de la base común. Cada visitante procesa su audio localmente;
ambas etapas están apagadas al entrar, y al apagarlas no alteran la ruta
original. Pruebas: `test_audio_plugins.py` y `test_audio_navegador.py`; esta
última mide la atenuación de un tono y la conservación de la voz.

### `bricohams_live`

El plugin del mapa agrupa las trayectorias APRS y las fichas ADS-B. Valida
posiciones y marcas temporales y limita las entradas retenidas en memoria para
evitar crecimiento sin cota. Los datos opcionales de la ficha se solicitan al
abrirla. Pruebas: `test_live_map.py` y `test_avion.py`.

### Integración Rig Skin

Rig Skin es externo. BricoHams lo carga desde `receiver/init.js` y añade el
comportamiento de la cinta DX sobre la barra de frecuencias: reemplaza spots
repetidos del mismo indicativo, aplica caducidad y permite sintonizar al pulsar.
La documentación distingue la integración local del código base de terceros.

- **Ficheros principales:** `files/htdocs/plugins/receiver/init.js`,
  `files/htdocs/plugins/receiver/` y `files/htdocs/plugins/map/`.
- **Pruebas de sintaxis:** `node --check` para los JavaScript locales, ejecutado
  por `tests/run_tests.sh`.
- **Instalación y uso:** el procedimiento único y la matriz de pasos para cada
  plugin están en [27 · Plugins web](manuales/27_PLUGINS_WEB_V4.md#instalacion-plugins-propios).
  Los detalles de audio están en [30 · Audio DSP](manuales/30_AUDIO_DSP.md).

## 5. Bookmarks, importación/exportación y CTCSS

- **Objetivo:** gestionar marcadores desde `/settings` y guardar el subtono de
  cada repetidor para filtrar por tono.
- **Desarrollo:** ADR-26 fija el subtono en la descripción; ADR-36 excluye
  comunicaciones privadas; v4.1 introduce mezcla a tres vías para no pisar los
  marcadores añadidos desde la web; v5.0 añade importación/exportación con el
  formulario nativo (ADR-58) y CTCSS con silenciador por tono (ADR-60).
  `OWRX_CTCSS_ENABLE` permite habilitarlo o retirarlo desde la configuración
  del instalador sin dejar el parche ni su gancho apt activos.
- **Ficheros:** `files/bin/bricohams-owrx-bookmarks-io`,
  `files/bin/bricohams-owrx-ctcss`, `files/share/bricohams-ctcss/`,
  `files/bin/bricohams-merge-bookmarks.py`.
- **Regla:** se guarda la frecuencia de salida del repetidor, que es la que
  escucha el SDR.
- **Pruebas:** `test_bookmarks_io.py`, `test_ctcss_patch.py`.
- **Documentación:** [32 §8 y §10](manuales/32_ZONA_LOCATOR.md).

## 6. Importador de RepeaterBook

- **Objetivo:** descargar repetidores de la zona e importarlos como bookmarks.
- **Desarrollo:** v5.0 guarda la clave en Ajustes generales (ADR-59) y crea un
  importador por zona (ADR-61) que reutiliza el formato CTCSS del módulo 5.
- **Ficheros:** `files/bin/bricohams-owrx-repeaterbook`,
  `files/bin/bricohams-owrx-rbimport`, `files/share/bricohams-rbimport/`.
- **Seguridad:** la clave se introduce desde `/settings` y no se escribe en el kit.
- **Pruebas:** `test_repeaterbook.py`, `test_rbimport.py`.
- **Documentación:** [32 §9 y §11](manuales/32_ZONA_LOCATOR.md).

## 7. Locator, zona y canales

- **Objetivo:** configurar cualquier ubicación de España a partir del locator.
- **Desarrollo:** v4.3 incorpora un catálogo nacional en el kit (ADR-43) y
  descarga en la Pi los datos que cambian, con caché y sin detener la instalación
  si falla la red (ADR-46).
- **Ficheros:** `files/bin/bricohams-locator`, `files/bin/bricohams_locator*.py`,
  `tools/locator_catalogo.py`, `tools/canales.py`, `tools/marcadores.py`.
- **Pruebas:** `test_locator_es.py`, `test_locator_bookmarks.py`.
- **Documentación:** [32](manuales/32_ZONA_LOCATOR.md),
  [CANALES_Y_FRECUENCIAS.md](CANALES_Y_FRECUENCIAS.md).

## 8. Meshtastic 868/433 y panel privado

- **Objetivo:** operar un nodo 868 MHz en el HAT y otro 433 MHz por USB, ver sus
  nodos y mensajes en OpenWebRX+ y configurarlos solo como administrador.
- **Desarrollo:** v1.0 instala `meshtasticd`; v2.0 añade LilyGO 433 y canales de
  red (ADR-06); v4.5 integra el mapa mediante un suscriptor MQTT propio (ADR-50)
  y protege las URL de canales (ADR-51); ADR-53 lleva la configuración a
  `/settings`.
- **Diseño:** `bricohams-mesh-admin` escucha en `127.0.0.1:8076` y también
  valida la sesión para nginx (`auth_request`).
- **Ficheros:** `files/bin/bricohams-mesh-admin`, `files/bin/bricohams-mesh-owrx`,
  `files/bin/bricohams-mesh-url`, `files/bin/bricohams-lilygo`,
  `files/bin/bricohams_mqtt.py`, `files/bin/bricohams-mqtt-settings.py`.
- **Pruebas:** `test_mesh_admin.py`, `test_mesh_owrx.py`.
- **Documentación:** [05](manuales/05_LILYGO.md), [35](manuales/35_LORA_APRS_MESHTASTIC.md).

## 9. iGate LoRa APRS con RAK4631

- **Objetivo:** recibir LoRa APRS en el RAK4631 y usar la conexión de la Pi para
  enviarlo a APRS-IS y al mapa.
- **Desarrollo:** el iGate original en LilyGO (ADR-07) evoluciona en v4.5 a
  firmware propio para RAK4631: radio en el RAK e Internet en la Pi (ADR-49).
  `tools/compilar_rak.sh` comprueba la compilación de 55 placas.
- **Ficheros:** `files/bin/bricohams-rak-aprs`, `firmware/`, `tools/compilar_rak.sh`.
- **Seguridad:** credenciales cargadas con `LoadCredential`.
- **Pruebas:** `test_rak_aprs.py`.
- **Documentación:** [22](manuales/22_WX_LORA_FIRMWARE.md), [35](manuales/35_LORA_APRS_MESHTASTIC.md).

## 10. ADS-B, RadarBox, mapa y ficha del avión

- **Objetivo:** recibir 1090 MHz con un SDR dedicado, alimentar RadarBox con MLAT
  y mostrar los aviones públicos en el mapa de OpenWebRX+.
- **Desarrollo:** v2.0 crea la cadena readsb → rbfeeder → MLAT → tar1090 fuera de
  OpenWebRX+ (ADR-04). v4.6 publica datos saneados en el mapa sin tocar
  RadarBox (ADR-55). v5.0 integra map.flights como proveedor principal de ruta,
  foto y ficha mediante un proxy local con caché, con adsbdb/Planespotters como
  respaldo (ADR-69/71). La selección se guarda desde General Settings y la clave
  de API no es necesaria. También se corrigió la rotación de logs de `mlat-client`.
- **Ficheros:** `files/bin/bricohams-rbfeeder-ini.py`, `files/bin/bricohams-api.py`,
  `bricohams_live.js`.
- **Comandos:**

```bash
sudo bash install.sh --solo adsb
systemctl status readsb rbfeeder --no-pager
```

- **Pruebas:** `test_avion.py`, `test_mapflights_api.py`, `test_live_map.py`.
- **Documentación:** [04](manuales/04_ADSB.md), [14](manuales/14_ADSB_LNA.md).

## 11. Envío ADS-B a map.flights

- **Objetivo:** enviar los mismos aviones a map.flights además de RadarBox.
- **Desarrollo:** se analizó el método del proveedor y se eligió un conector
  Beast adicional en readsb y un MLAT independiente (ADR-70). Primero se
  implementó y probó en un entorno aislado; después se desplegó en la estación
  principal con copia previa verificada. El proveedor confirmó recepción el
  15-10-2026. Durante el diagnóstico se aclaró que el feed usa el UUID de la
  estación y no la clave que empieza por `mf_feed_`.
- **Diseño:** `bricohams-mapflights.py` modifica `/etc/default/readsb` de forma
  idempotente y conserva otros conectores. Beast va a `feed.map.flights:30004`
  y MLAT a `mlat.map.flights:31090`.
- **Ficheros:** `files/bin/bricohams-mapflights.py`, unidad
  `bricohams-mapflights-mlat`, comprobaciones en `bricohams-check`.
- **Configuración:** `MAPFLIGHTS_FEED=yes` y UUID privado en `bricohams.env`;
  copia protegida en `/etc/bricohams/mapflights.env` (600).
- **Comandos:**

```bash
sudo nano /etc/bricohams/bricohams.env
sudo bash install.sh --solo adsb
systemctl status readsb rbfeeder bricohams-mapflights-mlat --no-pager
```

- **Pruebas:** `test_mapflights.py`.
- **Estado:** opcional y desactivado por defecto en instalaciones nuevas.
- **Documentación:** [04 · map.flights](manuales/04_ADSB.md#enviar-también-a-mapflights-v51).

## 12. Plugin map.flights para OpenWebRX+

- **Objetivo:** enriquecer los aviones locales que detecta readsb con ruta,
  destino, ficha y fotografía del endpoint de map.flights; atribuir el proveedor
  visiblemente en el mapa de OpenWebRX+.
- **Desarrollo:** primero se verificó el contrato público por ICAO
  (`/api/v1/aircraft/{hex}`) y que no requiere API key. La consulta sale del
  servidor, no del navegador. Se añadió el selector bajo General Settings con
  un parche idempotente/reversible y un gancho apt. La caché separa respuestas
  según el selector activo y, si map.flights no devuelve campos, se conservan
  adsbdb/Planespotters como respaldo con su crédito fotográfico.
- **Diseño:** las posiciones siguen siendo de readsb local; map.flights aporta
  únicamente detalles y ruta. El control del mapa usa el icono oficial enlazado
  a `https://map.flights`. La integración de fichas es independiente del feed
  Beast/MLAT, que mantiene el UUID privado y el panel de diagnóstico.
- **Ruta:** `/settings/bricohams/mapflights`.
- **Ficheros:** `files/bin/bricohams-api.py`, `files/bin/bricohams-owrx-mapflights`,
  `files/htdocs/plugins/map/bricohams_live/bricohams_live.js`,
  `files/bin/bricohams-mesh-admin`, `files/bin/bricohams-owrx-botones`.
- **Configuración:** General Settings → map.flights → **Use map.flights for
  aircraft details**; no se guarda una API key.
- **Pruebas:** `test_mapflights_api.py` (mapeo de respuesta, selector,
  cache-variante y atribución), `test_avion.py`, `test_mesh_admin.py` y
  `test_mapflights.py`.
- **Estado:** integrado en el kit, no desplegado. Aplicar los cambios en una
  estación requiere autorización y una copia previa verificada.
- **Documentación:** [38](manuales/38_MAPFLIGHTS_PLUGIN.md),
  [English](en/MAPFLIGHTS_PLUGIN.md).

## 13. Meteorología, sensores, Pico I/O y ventilación

- **Objetivo:** medir el entorno, publicar meteorología APRS y proteger el equipo
  con ventilación controlada.
- **Desarrollo:** v2.0 añade BME280/BMP280 (ADR-08); v3.0 incorpora ventilación,
  viento y lluvia (ADR-23, ADR-25); ADR-29 traslada sensores a una Pico cuando el
  HAT ocupa los GPIO; v5.0 permite usar sensores y GPS del RAK y elimina detalles
  internos del JSON público.
- **Ficheros:** `files/bin/bricohams-wx.py`, `bricohams-meteo.py`, `bricohams-io.py`,
  `bricohams-fan.py`.
- **Pruebas:** `test_wx_bme280.py`, `test_wx_rak.py`, `test_meteo.py`,
  `test_viento_lluvia.py`, `test_pico_io.py`, `test_fan.py`.
- **Documentación:** [06](manuales/06_SENSOR_WX.md), [18](manuales/18_VENTILACION.md),
  [19](manuales/19_VIENTO_Y_LLUVIA.md), [20](manuales/20_PICO_IO.md).

## 14. Cámara

- **Objetivo:** mostrar vídeo y una foto de la estación sin sobrecargar la Pi.
- **Desarrollo:** v1.0 usa cámara CSI con MediaMTX (ADR-09); v2.0 ajusta H.264
  por CPU; ADR-24 recomienda cámara IP RTSP en el mástil.
- **Ficheros:** `files/bin/bricohams-camsnap.py`; servicios `mediamtx` y
  `bricohams-camsnap`.
- **Documentación:** [07](manuales/07_CAMARA.md).

## 15. Satélites y FT2

- **Objetivo:** calcular pases de satélites y decodificar FT2 de forma experimental.
- **Desarrollo:** ADR-31 calcula pases en la Pi y abre la escucha con Doppler;
  ADR-35 añade FT2 con un adaptador compatible y parche reversible.
- **Ficheros:** `files/bin/bricohams-satpass.py`, `files/bin/bricohams-ft2*`.
- **Pruebas:** `test_satpass.py`, `test_ft2.py`.
- **Documentación:** [26](manuales/26_SATELITES.md), [28](manuales/28_FT2.md).

## 16. Web, SSL, API, visitas y chat

- **Objetivo:** publicar el portal y OpenWebRX+ mediante nginx, proteger la
  administración y registrar visitas sin exponer datos personales.
- **Desarrollo:** ADR-32 crea nginx con SSL y portal; ADR-33 añade visitas por
  MQTT, GeoIP local y Telegram con IP truncada; ADR-40 limita HTTPS obligatorio a
  la administración; ADR-48 redondea la posición pública; ADR-57 lleva APRS al
  chat común; ADR-68 añade el moderador automático.
- **Ficheros:** `files/nginx/`, `files/web/`, `files/bin/bricohams-api.py`,
  `files/bin/bricohams-visitas.py`, `files/bin/bricohams-telegram`.
- **Pruebas:** `test_ssl_admin.py`, `test_api.py`, `test_visitas.py`, `test_live_map.py`.
- **Documentación:** [23](manuales/23_WEB_SSL_SERVICIOS.md), [24](manuales/24_VISITAS_TELEGRAM.md).

## 17. TAK y mapa local

- **Objetivo:** ofrecer un servidor TAK local para ATAK/iTAK y una capa privada
  en el mapa.
- **Desarrollo:** v4.6 instala OpenTAKServer aislado con Python 3.12 (ADR-54) y
  una capa privada (ADR-56); v5.0 añade paneles bajo `/settings` (ADR-62) y
  credenciales aleatorias cambiables (ADR-63). Se corrigió la creación de
  usuarios con guion porque el servidor no los acepta en el inicio de sesión.
- **Ficheros:** `tools/instalar_tak.sh`, `tools/tak-requirements.txt`,
  `tools/activar_mapa_local.sh`, panel TAK de `bricohams-mesh-admin`.
- **Pruebas:** `test_mesh_admin.py`.
- **Documentación:** [36](manuales/36_TAK_MAPA_LOCAL.md).

## 18. Monitorización

- **Objetivo:** consultar métricas de la Pi en Grafana sin publicarlo fuera de
  `/settings`.
- **Desarrollo:** v5.0 integra Prometheus, node-exporter y Grafana (ADR-62) y
  adopta instalaciones manuales sin reinstalarlas (ADR-64).
- **Ficheros:** `paso_monitorizacion` en `install.sh`, `files/grafana/bricohams.json`,
  bloque `#@GF@` de `files/nginx/bricohams-sdr-rutas.conf`.
- **Comandos:**

```bash
# Requiere MONITORIZACION=yes en bricohams.env
sudo bash install.sh --solo monitorizacion
```

- **Pruebas:** `test_monitorizacion.py`.
- **Documentación:** [36](manuales/36_TAK_MAPA_LOCAL.md).

## 19. Seguridad y bloqueo

- **Objetivo:** auditar la estación y aplicar protección con posibilidad de
  volver atrás.
- **Desarrollo:** v4.4 crea `bricohams-blindaje` para auditar sin tocar y aplicar
  con copia (ADR-47); v5.0 añade bloqueo por IP y país con nftables (ADR-65),
  gestión de usuarios y cortafuegos desde `/settings` (ADR-66) y aviso de inicio
  de sesión por Telegram (ADR-67). Se corrigieron nombres de conjuntos nft que
  eran palabras reservadas.
- **Ficheros:** `files/bin/bricohams-blindaje`, `files/bin/bricohams-bloqueo`,
  `files/bin/bricohams-login-aviso`.
- **Comandos:**

```bash
sudo bricohams-blindaje auditar
```

- **Pruebas:** `test_blindaje.py`, `test_bloqueo_web.py`, `test_bloqueo_helper.py`.
- **Documentación:** [34](manuales/34_BLINDAJE_SEGURIDAD.md).

## 20. Copias, copia remota y limpieza automática

- **Objetivo:** conservar copias diarias, enviarlas opcionalmente a otro destino
  y evitar que las copias locales antiguas llenen la tarjeta.
- **Desarrollo:** la copia diaria existe desde v1.0 (ADR-13); ADR-34 automatiza
  mantenimiento sin credenciales guardadas; v5.0 añade copia remota por SMB,
  NFS, SFTP, Google Drive u OneDrive, con secretos en root `600` y verificación
  SHA256. Después se creó la limpieza automática: se probó la regla de 120 horas,
  el modo simulación y la exclusión de enlaces y carpetas; se desplegó en la
  estación principal con copia previa verificada.
- **Ficheros:** `files/bin/bricohams-backup-remoto`,
  `files/bin/bricohams-backup-limpieza`, `files/bin/bricohams-tarea`.
- **Servicios:** copia diaria, `bricohams-backup-remoto.timer` opcional y
  `bricohams-backup-limpieza.timer` diario a las 06:15.
- **Comandos:**

```bash
sudo bricohams-backup-limpieza --dry-run
systemctl list-timers 'bricohams-backup*' --no-pager
```

- **Pruebas:** `test_backup_limpieza.sh`, `test_mesh_admin.py`, `test_actualizar.py`.
- **Documentación:** [09](manuales/09_MANTENIMIENTO.md), [25](manuales/25_TAREAS_AUTOMATICAS.md).

## 21. Hardware y documentación generada

- **Objetivo:** que la caja, los anclajes, las antenas, los esquemas y la guía
  visual se regeneren desde código y se puedan comprobar.
- **Desarrollo:** v2.2 crea la caja impresa en 3D (ADR-15); v3.0 añade antenas,
  caja v3 y mástil (ADR-18 a ADR-23); ADR-30 sustituye abrazaderas en U por
  anclajes impresos. v5.0 incorpora la guía visual de 17 fichas, dos capturas
  reales anonimizadas por recorte y un comprobador de enlaces, cuadros de código,
  cobertura de pasos y privacidad.
- **Ficheros:** `hardware/`, `tools/caja*.sh`, `tools/anclajes.sh`, `tools/mastil.py`,
  `tools/planos_antenas.py`, `tools/esquemas.py`, `tools/datos.py`,
  `tools/estructura.py`; el generador de la guía visual está en la raíz del
  proyecto de mantenimiento.
- **Pruebas:** `test_caja.py`, `test_anclajes.py`, `test_v3_hardware.py`.
- **Documentación:** [10](manuales/10_CAJA_3D.md)–[17](manuales/17_CAJA_V3.md),
  [21](manuales/21_ANCLAJES.md), [GUIA_VISUAL_MODULOS.md](GUIA_VISUAL_MODULOS.md).

## Cómo documentar un módulo nuevo

Copia esta plantilla al final de este documento y complétala antes de desplegar:

```markdown
## N. Nombre del módulo

- **Objetivo:**
- **Desarrollo:** requisito, alternativas y decisión (ADR-NN)
- **Diseño:** flujo de datos, servicios y puertos
- **Ficheros:**
- **Configuración:** variables genéricas, sin secretos
- **Comandos:** instalación, comprobación y restauración
- **Pruebas:**
- **Estado:** integrado / opcional / generado, no desplegado
- **Límites:**
- **Documentación:**
```

## 22. Registro voluntario de oyentes

- **Objetivo:** permitir que el visitante comparta voluntariamente su indicativo
  o nombre con consentimiento explícito, o que continúe sin identificarse.
- **Desarrollo:** se diseñó para no capturar IP ni publicar la lista. El
  navegador conserva la decisión local; cada envío requiere consentimiento,
  mismo origen y validación del servidor. La retención se limita a 180 días y
  100.000 entradas.
- **Diseño:** `identificacion.js` muestra el formulario; `bricohams-api.py`
  recibe `POST /bricohams/api/oyentes`; SQLite queda en
  `/var/lib/bricohams/oyentes.sqlite`, accesible localmente por el operador.
- **Ficheros:** `files/htdocs/plugins/receiver/identificacion/`,
  `files/bin/bricohams-api.py`, `files/bin/bricohams-oyentes`,
  `files/nginx/bricohams-sdr-rutas.conf`.
- **Configuración:** requiere `VISITAS_ENABLE=yes`; `no` desactiva el registro y
  la bienvenida.
- **Pruebas:** `test_registro_oyentes.py` valida consentimiento, persistencia,
  retención, endpoint y exportación CSV.
- **Estado:** integrado en ambos kits, no desplegado.
- **Documentación:** [39](manuales/39_REGISTRO_OYENTES.md), [COMPONENTES](COMPONENTES.md).

## 23. Solo HTTPS, mapa local ADS-B/AIS, políticas, idioma y logo

- **Objetivo:** publicar todo por 443, retirar el 8073 de la red, mostrar en el
  mapa de OpenWebRX+ solo aviones y barcos de recepción propia (sin webs
  externas embebidas), informar de seguridad y datos, pedir consentimiento de
  cookies, ofrecer ES/EN y sustituir el logo de OpenWebRX+ por el de BricoHams.
- **Desarrollo:** se retiró el módulo `externos` (AstroRadio/meteo embebidos).
  La capa AIS se añadió al plugin de mapa existente en lugar de crear otro: la
  API valida los barcos de AIS-catcher y el mapa solo crea la capa si la API
  responde 200. El logo se cambia en nginx (`sub_filter`) para cubrir también
  `/settings`, y en el navegador como respaldo.
- **Diseño:** `paso_configuracion` escribe `22-solo-local.conf`
  (`bind_address = 127.0.0.1`); `paso_web` genera el sitio en modo `todo`
  (80 → 301, HSTS) y el snippet de tar1090; `paso_ais` crea `bricohams-ais`
  (AIS-catcher en `127.0.0.1:8100`) y desactiva el servicio del fabricante;
  `bricohams-blindaje` admite `BLINDAJE_8073="cerrado"`.
- **Ficheros:** `files/nginx/bricohams-sdr-rutas.conf`,
  `files/nginx/bricohams-sdr.conf.tmpl`, `files/bin/bricohams-api.py`,
  `files/bin/bricohams-blindaje`, `files/bin/bricohams-docker-compose.py`,
  `files/htdocs/plugins/map/bricohams_live/bricohams_live.js`,
  `files/htdocs/plugins/receiver/{consentimiento,idioma,marca}/`,
  `files/web/{politicas.html,privacidad.html,index.html.tmpl}`.
- **Configuración:** `SSL_MODO="todo"`, `OWRX_SOLO_LOCAL="yes"`,
  `BLINDAJE_8073="cerrado"`, `AIS_ENABLE`, `AIS_SDR_SERIAL`.
- **Pruebas:** `test_politicas_mapa_local.py` (sin externos, políticas, 443,
  AIS, logo), `test_instalador_docker.py`, `test_ssl_admin.py`,
  `test_mesh_admin.py`.
- **Estado:** integrado en ambos kits; AIS opcional (requiere un SDR de 162 MHz).
- **Documentación:** [40](manuales/40_HTTPS_MAPA_LOCAL_POLITICAS.md), [23](manuales/23_WEB_SSL_SERVICIOS.md), [34](manuales/34_BLINDAJE_SEGURIDAD.md), [COMPONENTES](COMPONENTES.md).
