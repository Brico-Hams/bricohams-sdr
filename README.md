# BricoHams SDR · EA5KAO · Mi QTH (Región de Murcia)

Repositorio para montar **desde cero** (o restaurar) la estación SDR multiusuario de BricoHams en una Raspberry Pi 5 con **Raspberry Pi OS Lite 64-bit, Trixie o Bookworm** (v4.3):

- OpenWebRX+ con 3 receptores (y un 4.º SDRplay preparado).
- ADS-B para AirNav RadarBox con MLAT.
- Dos nodos Meshtastic (868 y 433) y un iGate LoRa APRS.
- Estación meteorológica propia publicada en APRS.
- Cámara del mástil e imagen BricoHams con Murcia.
- **Caja de intemperie impresa en 3D** (PETG + TPU) para el mástil Televés, con compartimento de potencia aparte.
- **v3.0:**
  - **antenas propias** simuladas con NEC2, con STL, lista de materiales y manuales: quad 2 m/70 cm, dos discones, ADS-B con LNA, protección del lazo MLA-30 y soportes del mástil;
  - **plan de mástil** con cálculo de viento;
  - **caja v3** en dos módulos al pie del mástil, con **ventilación controlada**;
  - **viento y lluvia** en el WX APRS;
  - **repetidores con subtono** en los marcadores y **Wifon FM** la primera.
- **v4.0:**
  - **Pico «bricohams-io» por USB** para sensores y ventiladores: con el HAT puesto la cabecera de 40 pines está tapada;
  - **cámara Waveshare (F)** OV5647 NoIR con cinta 15→22 pines para el conector de la Pi 5;
  - **anclajes impresos** (crucetas con tuercas cautivas) para la fibra 433, la quad, la ADS-B, los sensores de viento y el pluviómetro;
  - **marcadores nuevos:** Radio Club Región de Murcia (RU-75, 145,325, 430,325, CB canal 32, PMR 5), CB 40 canales, PMR446, FM (Radio María), DAB+, FT8/FT4/FT2, modos digitales, aviación y marina de Cartagena y Mazarrón;
  - **plugins web:** banderas en FT8/FT4/FT2, ficha QRZ/RadioID en DMR/YSF, banner de próximos pases con ▶ Escuchar (Doppler), plan de bandas, oyentes (opcional), logo más pequeño;
  - **FT2** (experimental, decodium-rx);
  - **https con Let's Encrypt** detrás de nginx, portal de servicios y página de privacidad;
  - **visitas:** contador, país/ciudad e IP truncada, aviso por **Telegram**;
  - **tareas automáticas** por cron con una **cuenta de servicio** sin contraseña.
- **v4.2:**
  - **owrx-clone:** exporta todo tu OpenWebRX+ (configuración, plugins, sistema y paquetes) a un fichero y lo importa en cualquier otro equipo. Es genérico, para la comunidad ([owrx-clone/](owrx-clone/README.md), [manual 31](docs/manuales/31_CLONAR_OPENWEBRX.md));
  - **FILTRO y DSP de audio** en el navegador de cada oyente: paso banda, notch automático, ecualizador, puerta de ruido y AGC ([manual 30](docs/manuales/30_AUDIO_DSP.md));
  - **SSL solo en la administración:** el receptor por HTTP y `/login` y `/settings` forzados a HTTPS (`SSL_MODO`);
  - **ficha DMR/YSF con HamQTH** primero (aportación de EA5KAO);
  - **arreglos de la instalación real:** claves con `$` en `bricohams.env`, cortes de red tras el paso `red`, descargas sin reintento;
  - [ayuda rápida](docs/AYUDA_RAPIDA.md) con todas las órdenes.
- **v4.3:**
  - **OpenWebRX+ en Docker** desde `bricohams.env` (`OWRX_BACKEND="docker"`): el instalador crea el `docker-compose.yaml` y el contenedor; owrx-clone 1.1 pasa una estación de nativo a Docker y al revés ([manual 33](docs/manuales/33_OPENWEBRX_DOCKER.md));
  - **zona por locator:** con `STATION_LOCATOR` (cualquier locator de España) salen los aeropuertos, estaciones AEMET, puertos, NAVTEX y emisoras de FM regionales y locales más cercanos, como marcadores y `METEO_STATIONS`. Lejos de Mi QTH se quitan los de Murcia ([manual 32](docs/manuales/32_ZONA_LOCATOR.md), `bricohams-locator`);
  - plantilla genérica (`N0CALL`), indicativo y QTH en `settings.json` y oyentes con bandera y enlace al perfil (aportaciones de EA5KAO).
- **v4.1:** `sudo bash install.sh --actualizar` pone al día kit (git), `bricohams.env` (variables nuevas), sistema (apt) y solo los pasos que han cambiado, conservando tus marcadores ([manual 29](docs/manuales/29_ACTUALIZAR.md)).

![Arquitectura](docs/esquemas/01_arquitectura.png)

## Qué hay en la estación

| Función | Hardware | Software |
|---|---|---|
| 🛰️ Satélites 2 m / 70 cm / 137 MHz | RTL-SDR del **HAT HackerGadgets** (R860, TCXO, bias-tee) + LNA | OpenWebRX+ |
| 🟢 Radioaficionados, hotspots DMR/YSF, Sierra Espuña, PMR, LoRa, TETRA | **Mini RTL-SDR HackerGadgets** (R860, TCXO) | OpenWebRX+ |
| 🔵 Aire, marina, AIS, FM, DAB+ y **HF 160-6 m** | **RTL-SDR Blog V3** (HF por muestreo directo) | OpenWebRX+ |
| 🟡 HF 160-6 m (cuando llegue) | **SDRplay** | OpenWebRX+ (`HF_SDRPLAY=yes`) |
| ✈️ ADS-B 1090 MHz + MLAT | **FlightStick de AirNav RadarBox** | readsb + rbfeeder + tar1090 |
| 📡 Meshtastic 868 (SFNarrow, Murcia, Cartagena, Test, Alicante) | LoRa SX1262 del HAT | meshtasticd |
| 📡 Meshtastic 433 (mismos canales) | LilyGO T3 V1.6.1 por USB | firmware Meshtastic + CLI |
| 📍 iGate LoRa APRS 433,775 (solo RX) | LilyGO T3 V1.6.1 por USB | LoRa_APRS_iGate (CA2RXU) |
| 🕒 Hora exacta | GPS + PPS y RTC PCF85063A del HAT | gpsd + chrony |
| 🌡️ Tiempo propio + estación WX APRS (EA5KAO-13) | **BME280/BMP280** (GYBMEP) por I2C + **anemómetro y veleta RS485** + **pluviómetro** (v3) | bricohams-wx |
| 🌬️ Estación WX LoRa alternativa (EA5KAO-14) | 3.er LilyGO con los mismos sensores | LoRa_APRS_Wx_Station (CA2RXU) · `bricohams-lilygo wxstation` |
| 🌦️ Estaciones AEMET cercanas + previsión | — | bricohams-meteo (AEMET + Open-Meteo) |
| 📷 Cámara del mástil con visión nocturna | **cámara IP PoE por RTSP** (recomendada, v3) o WPI408 / Camera Module 3 por CSI | MediaMTX + foto para la web |
| ☀️ Radiación solar, DX cluster, imagen BricoHams | — | plugins `solar`, `rig_skin`, `meteo`, `camara`, `bricohams` |
| 📶 WiFi de casa (5 GHz preferida, 2,4 GHz de respaldo) | WiFi de la Pi 5 | NetworkManager (paso `red`) |
| 📦 Caja del mástil + alimentación por cargador USB de 45 W | PETG + TPU (Anycubic Kobra S1) | `hardware/caja/` (OpenSCAD) |
| 📦 **Caja v3** al pie del mástil: electrónica + potencia (120 W, bus de 12 V) | ASA/PETG + TPU | `hardware/caja_v3/` |
| 🌀 Ventilación con control PWM, tacómetros y DS18B20 | 2 × 60 mm 12 V de 4 hilos | `bricohams-fan` |
| 📡 Antenas: quad 2 m/70, discones, ADS-B + LNA, MLA-30 | aluminio, fibra, piezas impresas | `hardware/antenas/` (NEC2 + OpenSCAD) |
| 🔌 **v4** · Sensores y ventiladores con el HAT puesto | **Raspberry Pi Pico** por USB + 2 × 2N7002 | `firmware/pico-io` + `bricohams-io` |
| 🔩 **v4** · Anclajes al mástil y a los brazos | crucetas impresas, M6 + tuercas cautivas | `hardware/anclajes/` |
| 🛰️ **v4** · Próximos pases y escucha con Doppler | — | `bricohams-satpass` + plugin `satelites` (+ SatDump para METEOR) |
| 🔒 **v4** · https, portal y API de indicativos | — | nginx + certbot + `bricohams-api` |
| 👥 **v4** · Visitas y aviso por Telegram | — | mosquitto + `bricohams-visitas` (GeoIP DB-IP Lite) |
| ⏰ **v4** · Copias, actualización, reinicio y salud | — | `/etc/cron.d/bricohams` + cuenta `bricohams` |

## Puesta en marcha rápida

```bash
git clone https://github.com/anatolbricoham/bricohams-sdr.git && cd bricohams-sdr
cp bricohams.env.example bricohams.env && nano bricohams.env     # identidad, QTH, hardware y claves
sudo bash install.sh                                               # instalación nueva
# solo al restaurar una estación: sudo bash install.sh --backup copia.tar.gz
sudo bricohams-sdr-serials --grabar        # una vez: series de los 4 RTL-SDR
sudo bricohams-lilygo identificar          # una vez: nombres fijos de los LilyGO
sudo reboot
sudo bricohams-lilygo meshtastic && sudo bricohams-lilygo igate
sudo bricohams-check
sudo bricohams-io --instalar               # v4: graba el firmware de la Pico (una vez)
bricohams-servicios                        # v4: direcciones de todos los servicios web
```

**Llevar tu OpenWebRX+ a otro equipo** (v4.2, [manual 31](docs/manuales/31_CLONAR_OPENWEBRX.md)):

```bash
sudo owrx-clone exportar --cifrar                         # en el viejo
sudo owrx-clone importar perfil.owrx.tar.gz.enc --todo    # en el nuevo (o: sudo bash install.sh --importar …)
```

**Zona por locator y OpenWebRX+ en Docker** (v4.3, manuales [32](docs/manuales/32_ZONA_LOCATOR.md) y [33](docs/manuales/33_OPENWEBRX_DOCKER.md)):

```bash
# bricohams.env: STATION_LOCATOR="IN52pf"  ·  OWRX_BACKEND="docker" (opcional)
bricohams-locator info                          # aeropuertos, AEMET, puertos, FM y NAVTEX cercanos
sudo bricohams-locator marcadores --aplicar     # marcadores de la zona en OpenWebRX+
sudo owrx-clone --docker owrx-mbe importar perfil.owrx.tar.gz   # tu estación nativa, dentro del contenedor
```

**Actualizar una estación ya instalada** (v4.1):

```bash
cd ~/bricohams-sdr
sudo bash install.sh --actualizar --simular   # qué haría
sudo bash install.sh --actualizar             # hacerlo
```

Desde la v4 la estación se abre en **https://&lt;tu dominio&gt;/** (router: puertos 80 y 443 a la Pi; [manual 23](docs/manuales/23_WEB_SSL_SERVICIOS.md)).

### Alcance para otros equipos

Este repositorio es un **kit de instalación de referencia**, no un instalador universal de Linux. Está probado para Raspberry Pi 5, arm64, Raspberry Pi OS Bookworm o Trixie y el conjunto de receptores/periféricos descrito arriba. El arranque, HAT, GPIO, serie USB, ADS-B, Meshtastic, Pico, cámara y ventilación presuponen hardware compatible; `--solo` omite pasos, pero no convierte un equipo distinto en compatible.

Antes de instalar en otra estación, personaliza `bricohams.env` (indicativo, QTH, coordenadas, país, WiFi, números de serie y servicios habilitados). La plantilla de perfiles y los marcadores de radio de `files/openwebrx/` son de Murcia/EA5KAO: cambia frecuencias, repetidores, branding y descripciones que no correspondan a tu zona. No habilites APRS ni conectes nodos transmisores hasta configurar tus propios indicativos, claves y parámetros de radio. El [manual 02](docs/manuales/02_INSTALACION.md) contiene la lista previa y los límites soportados.

El paso a paso completo está en [docs/manuales/](docs/manuales/). La caja del mástil, en el [manual 10](docs/manuales/10_CAJA_3D.md).

**v3.0:**
- [Memoria técnica](docs/MEMORIA_TECNICA.md): todos los componentes, cables y orden de instalación.
- [Mástil y antenas](docs/manuales/11_MASTIL_Y_ANTENAS.md) (manuales 11–16).
- [Caja v3](docs/manuales/17_CAJA_V3.md), [ventilación](docs/manuales/18_VENTILACION.md) y [viento y lluvia](docs/manuales/19_VIENTO_Y_LLUVIA.md).

**v4.0:**
- [20 Pico IO](docs/manuales/20_PICO_IO.md) · [21 Anclajes](docs/manuales/21_ANCLAJES.md) · [22 Firmware WX LoRa](docs/manuales/22_WX_LORA_FIRMWARE.md)
- [23 Web, SSL y servicios](docs/manuales/23_WEB_SSL_SERVICIOS.md) · [24 Visitas y Telegram](docs/manuales/24_VISITAS_TELEGRAM.md) · [25 Tareas automáticas](docs/manuales/25_TAREAS_AUTOMATICAS.md)
- [26 Satélites](docs/manuales/26_SATELITES.md) · [27 Plugins web](docs/manuales/27_PLUGINS_WEB_V4.md) · [28 FT2](docs/manuales/28_FT2.md) · [29 Actualizar](docs/manuales/29_ACTUALIZAR.md)
- v4.2: [30 Audio FILTRO y DSP](docs/manuales/30_AUDIO_DSP.md) · [31 Clonar OpenWebRX+](docs/manuales/31_CLONAR_OPENWEBRX.md) · [Ayuda rápida](docs/AYUDA_RAPIDA.md)
- v4.3: [32 Zona por locator](docs/manuales/32_ZONA_LOCATOR.md) · [33 OpenWebRX+ en Docker](docs/manuales/33_OPENWEBRX_DOCKER.md) · [catálogo de zona](data/locator/LEEME.md)
- [Canales y frecuencias](docs/CANALES_Y_FRECUENCIAS.md): Radio Club, CB, PMR, FM, DAB+, digitales, aviación y marina.

> **¿`sudo: ./install.sh: command not found`?** Se han perdido los permisos al copiar el kit. Usa `sudo bash install.sh …` ([manual 02](docs/manuales/02_INSTALACION.md)).

![Caja del mástil](hardware/caja/render/montaje.png)

## Estructura

```
install.sh                 instalador por pasos e idempotente (--lista, --solo, --backup, --actualizar, --exportar, --importar)
owrx-clone/                v4.2: herramienta genérica para clonar OpenWebRX+ (README es/en, man, instalar.sh, MIT)
bricohams.env.example      configuración de la estación SIN claves (copiar a bricohams.env)
files/
  openwebrx/               plantilla de settings.json, marcadores, conf.d
  htdocs/plugins/          init.js y plugins web (solar, meteo, camara, bricohams + 0xAF)
  branding/                cabecera y avatar BricoHams con Murcia
  bin/                     herramientas y servicios (check, series, lilygo, wx, meteo, camsnap, fan, io, satpass,
                           visitas, api, ft2, servicios, tarea, telegram…)
  nginx/                   v4: plantilla del sitio y rutas comunes (v4.2: SSL_MODO)
  web/                     v4: portal /bricohams/ y página de privacidad
firmware/pico-io/          v4: firmware MicroPython de la Pico (sensores y ventiladores)
docs/
  ARQUITECTURA.md          decisiones de arquitectura (ADR)
  DATOS.md                 conjuntos de datos: SDR, perfiles, marcadores, puertos, servicios, I2C (generado)
  HARDWARE_Y_GPIO.md       pines GPIO, buses, USB, alimentación, antenas
  EVALUACION_MODULOS.md    evaluación de cada módulo (BME280, LX-LBU2C, WPI408, FlightStick…)
  MEMORIA_TECNICA.md       memoria técnica v3/v4: inventario, cables C1–C20, secuencia de instalación, BOM
  CANALES_Y_FRECUENCIAS.md v4: canales y frecuencias de todos los grupos de marcadores (generado)
  REFERENCIAS.md           fuentes y documentación externa
  esquemas/                diagramas SVG/PNG (bloques, GPIO, cableado, RF, red, alimentación y caja)
  manuales/                manuales paso a paso
hardware/caja/             caja de intemperie v2 (en el mástil): modelo OpenSCAD, STL listos para imprimir y vistas
hardware/caja_v3/          caja v3 de dos módulos (electrónica + potencia): OpenSCAD, 30 STL, vistas
hardware/antenas/          antenas: antenas_bricohams.scad + 30 STL, sim/ (modelos NEC2 y resultados)
hardware/anclajes/         v4: crucetas y soportes impresos (16 STL) y vista de montaje
data/                      repetidores EA5 (lista EA5KGV), marcadores_v4.json y satelites.json
tests/                     pruebas (run_tests.sh)
tools/                     esquemas.py, datos.py, caja.sh, caja_v3.sh, antenas.sh, mastil.py,
                           planos_antenas.py, marcadores.py, stl_util.py,
                           anclajes.sh, branding.py, canales.py (v4)
CHANGELOG.md               historial de versiones
```

## Pruebas

```bash
bash tests/run_tests.sh        # shellcheck, sintaxis, BME280, settings, meteo, viento/lluvia, ventiladores, STL
python3 tools/esquemas.py      # regenera los esquemas
python3 tools/datos.py         # regenera docs/DATOS.md
tools/caja.sh                  # regenera los STL de la caja y sus vistas (OpenSCAD)
tools/caja_v3.sh               # caja v3
tools/antenas.sh               # piezas de las antenas
python3 hardware/antenas/sim/quad_2m70.py --final   # simulación NEC2 (requiere nec2c)
python3 tools/mastil.py --png  # cálculo de viento del mástil
python3 tools/marcadores.py    # repetidores + marcadores_v4.json → marcadores (idempotente)
python3 tools/canales.py       # regenera docs/CANALES_Y_FRECUENCIAS.md
tools/anclajes.sh              # crucetas y soportes v4
```

## Reglas del repositorio

- `bricohams.env` **nunca** se sube: está en `.gitignore`. Desde la v4 también guarda `TELEGRAM_TOKEN`, las credenciales opcionales de HamQTH/QRZ, `DUCKDNS_TOKEN` y `LISTENERS_SUPABASE_KEY`.
- **No se ponen en los marcadores** comunicaciones privadas ni de seguridad pública (radiotaxis, TETRA de emergencias): ADR-36.
- Toda la configuración de OpenWebRX sale de `files/openwebrx/settings.json.tmpl` + `bricohams.env`. Para cambiar perfiles, edita la plantilla y regenera `docs/DATOS.md`.
- Lo marcado como **A VERIFICAR** (pines del HAT) se corrige en `bricohams.env`, nunca en el código.
