# BricoHams SDR · estación de ejemplo

**Versión coordinada: v5.4.3 · 2026-10-27.** [VERSION](VERSION) es la fuente
del número de publicación. Público y privado comparten versión, fecha y etiqueta
Git `v5.4.3`, pero no hashes ni historial: solo se exporta código anonimizado.
Toda publicación futura debe actualizar VERSION, el historial y la etiqueta en ambos.

**Configurar cada módulo:** [paso a paso, URLs y credenciales](docs/manuales/47_CONFIGURACION_MODULOS.md).
También dentro de cada panel privado, botón «Configuración paso a paso».
Google, compatibilidad Entra ID y tokens de backup Drive/OneDrive, SMB/NFS/SFTP.

**Demostración SDR:** [vídeo narrado en español, subtítulos y capítulos](docs/demo-sdr/README.md),
con datos sensibles ocultados y escenas privadas sustituidas por tarjetas explicativas.

> **Rama `openwebrxplus-generico`: kit anonimizado para cualquier estación OpenWebRX+.**
> No lleva el indicativo, el QTH, el locator, la red local ni los usuarios de la estación
> original, y `tests/test_anonimato.py` comprueba que no vuelvan a entrar.
> Los ejemplos usan **N0CALL**, el locator de muestra **IN52pf** y valores de red ficticios.
> Para tu estación: `cp bricohams.env.example bricohams.env` y rellena al menos
> `CALLSIGN`, `STATION_LOCATOR` (o `STATION_LAT`/`STATION_LON`), `ADSB_ANT_ALT` y las claves
> (RadarBox, map.flights, Telegram, ReceiverBook). Esas claves las pones tú y no se suben al repositorio.
> Después ejecuta `sudo ./install.sh`. Los datos regionales (repetidores, aeropuertos y AEMET de Murcia)
> solo se usan si tu QTH está a menos de `LOCATOR_KIT_ZONA_KM` del centro de la zona.

**Módulo map.flights:** [panel privado de integración ADS-B](docs/manuales/38_MAPFLIGHTS_PLUGIN.md)
en `/settings`, con estado local e instrucciones; conserva RadarBox.
Documentación / Documentation: [Español](docs/manuales/38_MAPFLIGHTS_PLUGIN.md) ·
[English](docs/en/MAPFLIGHTS_PLUGIN.md). Generado, sin desplegar / Generated, not deployed.

**Módulos y plugins:** [desarrollo de cada módulo y plugins de OpenWebRX+](docs/DESARROLLO_MODULOS.md) · [English](docs/en/MODULE_DEVELOPMENT.md).

**Primera instalación o nuevo módulo:** abre la
[guía visual de módulos](docs/GUIA_VISUAL_MODULOS.md), con ilustraciones,
capturas reales anonimizadas y cuadros de comandos por módulo.

**Laboratorio RF:** [hojas rellenables y trazabilidad](docs/laboratorio-rf/README.md),
[procedimientos de cualificación](docs/manuales/44_LABORATORIO_RF.md) y
[NanoVNA: calibración y medidas paso a paso](docs/manuales/45_NANOVNA.md),
con ilustraciones BricoHams y capturas de referencia identificadas.

**Impresión 3D de las cajas:** [guía BricoHams para ASA en la Kobra S1 Combo](docs/manuales/43_KOBRA_S1_ASA.md):
calibración, perfiles personalizados, capturas oficiales, pruebas de aceptación
y mantenimiento preventivo. Las tapas grandes caben sin brim, pero **no con
un brim exterior de 5 mm**; revisar la huella final antes de imprimir.

Kit para montar **desde cero** (o restaurar) la estación SDR multiusuario de BricoHams en una Raspberry Pi 5 con **Raspberry Pi OS Lite 64-bit, Trixie o Bookworm** (**v5.4.3**):

- OpenWebRX+ con 3 receptores (y un 4.º SDRplay preparado).
- ADS-B para AirNav RadarBox con MLAT y, opcionalmente, también para map.flights.
- Dos nodos Meshtastic (868 y 433) y un iGate LoRa APRS.
- Estación meteorológica propia publicada en APRS.
- Cámara del mástil e imagen BricoHams con Murcia.
- **Caja de intemperie impresa en 3D** (PETG + TPU) para el mástil Televés, con compartimento de potencia aparte.
- **Funciones de la línea v5, consolidadas en v5.4.1:**
  - **Seguridad desde `/settings`:** bloqueo por IP/red y país, desbaneo de Fail2ban, estado de cortafuegos/nginx, usuarios y avisos de login ([manual 34](docs/manuales/34_BLINDAJE_SEGURIDAD.md)).
  - **Ficha de aviones** con foto, modelo, operador y ruta mediante un proxy con caché, y **envío opcional a map.flights** además de RadarBox ([manual 04](docs/manuales/04_ADSB.md)).
  - **Meteo desde el RAK4631** y posición APRS desde su GPS, con respaldo Pico/I2C; corrección del arranque de lgpio y nombre por defecto «BricoHams WX» ([manual 06](docs/manuales/06_SENSOR_WX.md)).
  - **Copias remotas verificadas** por SMB, NFS, SFTP, Google Drive u OneDrive ([manual 09](docs/manuales/09_MANTENIMIENTO.md)).
  - **Moderador automático del chat** y avisos por Telegram ([manual 24](docs/manuales/24_VISITAS_TELEGRAM.md)), y **spots DX** en la barra de frecuencias ([manual 27](docs/manuales/27_PLUGINS_WEB_V4.md)).
  - Correcciones de los sets nftables y de logrotate para el registro opcional de MLAT. Detalles y pruebas en el [historial](CHANGELOG.md).
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
  - **ficha DMR/YSF con HamQTH** primero (aportación de N0CALL);
  - **arreglos de la instalación real:** claves con `$` en `bricohams.env`, cortes de red tras el paso `red`, descargas sin reintento;
  - [ayuda rápida](docs/AYUDA_RAPIDA.md) con todas las órdenes.
- **v4.4:** **blindaje de seguridad** (`sudo bricohams-blindaje auditar | aplicar`): cortafuegos del host con vuelta atrás, SSH, Fail2ban para SSH y ataques al login web, permisos de las claves, búsqueda de fugas, límite de intentos en `/login`, y la **posición pública redondeada** a ~1 km ([manual 34](docs/manuales/34_BLINDAJE_SEGURIDAD.md)).
- **v4.5:** **iGate LoRa APRS en un RAK4631** con firmware propio (port de CA2RXU, GPS y temperatura de la caja), **Meshtastic 433/868** con las URL de la red, y todo **en el mapa de OpenWebRX+**; banner SSH e inventario de dispositivos ([manual 35](docs/manuales/35_LORA_APRS_MESHTASTIC.md)).
- **v4.6:** **servidor TAK local** (OpenTAKServer aislado), aviones de readsb en el mapa sin interrumpir RadarBox/MLAT, trayectorias APRS, mensajes APRS en el CHAT común y capa TAK privada para administradores ([manual 36](docs/manuales/36_TAK_MAPA_LOCAL.md), justificación en el [manual 37](docs/manuales/37_JUSTIFICACION_CAMBIOS_V4_6.md)).
- **v4.3:**
  - **OpenWebRX+ en Docker** desde `bricohams.env` (`OWRX_BACKEND="docker"`): el instalador crea el `docker-compose.yaml` y el contenedor; owrx-clone 1.1 pasa una estación de nativo a Docker y al revés ([manual 33](docs/manuales/33_OPENWEBRX_DOCKER.md));
  - **zona por locator:** con `STATION_LOCATOR` (cualquier locator de España) salen los aeropuertos, estaciones AEMET, puertos, NAVTEX y emisoras de FM regionales y locales más cercanos, como marcadores y `METEO_STATIONS`. Lejos de tu QTH se quitan los de Murcia ([manual 32](docs/manuales/32_ZONA_LOCATOR.md), `bricohams-locator`);
  - plantilla genérica (`N0CALL`), indicativo y QTH en `settings.json` y oyentes con bandera y enlace al perfil (aportaciones de N0CALL).
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
| 🌡️ Tiempo propio + estación WX APRS (N0CALL-13) | **BME280/BMP280** (GYBMEP) por I2C + **anemómetro y veleta RS485** + **pluviómetro** (v3) | bricohams-wx |
| 🌬️ Estación WX LoRa alternativa (N0CALL-14) | 3.er LilyGO con los mismos sensores | LoRa_APRS_Wx_Station (CA2RXU) · `bricohams-lilygo wxstation` |
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
| 🌦️ **v5.0** · Clima en red, WSPR, grabación de pases y AMSAT | — | `bricohams-wx-red` + `bricohams-wspr` + `bricohams-satrec` → `/bricohams/clima.html` |

## ¿Quieres que otros monten una estación como la tuya?

Pon en `FUENTES_URL` (en `bricohams.env`) la dirección `https://` de tu copia de este repositorio: el portal (`/bricohams/`)
mostrará la tarjeta «¿Quieres una estación como esta?» y el receptor el botón 🛠️ «Monta la tuya». Vacío (por defecto) = no aparece
([manual 23](docs/manuales/23_WEB_SSL_SERVICIOS.md)).

## Puesta en marcha rápida

```bash
git clone https://github.com/TU_USUARIO/bricohams-sdr.git && cd bricohams-sdr
# Solo en el repositorio unificado (omite esta línea si publicaste el kit por separado):
cd kit-generico
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
cd ~/bricohams-sdr/kit-generico   # o la raíz del kit si lo publicaste por separado
sudo bash install.sh --actualizar --simular   # qué haría
sudo bash install.sh --actualizar             # hacerlo
```

Con `SSL_MODO="admin"`, el receptor público se abre en **http://&lt;tu dominio&gt;/** y `/login` y `/settings` usan **HTTPS**. Con `SSL_MODO="todo"`, toda la web usa HTTPS (router: puertos 80 y 443 a la Pi; [manual 23](docs/manuales/23_WEB_SSL_SERVICIOS.md)).

### Alcance para otros equipos

Este repositorio es un **kit de instalación de referencia**, no un instalador universal de Linux. Está probado para Raspberry Pi 5, arm64, Raspberry Pi OS Bookworm o Trixie y el conjunto de receptores/periféricos descrito arriba. El arranque, HAT, GPIO, serie USB, ADS-B, Meshtastic, Pico, cámara y ventilación presuponen hardware compatible; `--solo` omite pasos, pero no convierte un equipo distinto en compatible.

Antes de instalar en otra estación, personaliza `bricohams.env` (indicativo, QTH, coordenadas, país, WiFi, números de serie y servicios habilitados). La plantilla de perfiles y los marcadores de radio de `files/openwebrx/` son de Murcia/N0CALL: cambia frecuencias, repetidores, branding y descripciones que no correspondan a tu zona. No habilites APRS ni conectes nodos transmisores hasta configurar tus propios indicativos, claves y parámetros de radio. El [manual 02](docs/manuales/02_INSTALACION.md) contiene la lista previa y los límites soportados.

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
- v4.4: [34 Blindaje de seguridad](docs/manuales/34_BLINDAJE_SEGURIDAD.md)
- v4.5: [35 LoRa APRS (RAK4631) y Meshtastic en OpenWebRX+](docs/manuales/35_LORA_APRS_MESHTASTIC.md)
- v4.6: [36 TAK y mapa local](docs/manuales/36_TAK_MAPA_LOCAL.md) · [37 Justificación de los cambios v4.6](docs/manuales/37_JUSTIFICACION_CAMBIOS_V4_6.md)
- v4.3: [32 Zona por locator](docs/manuales/32_ZONA_LOCATOR.md) · [33 OpenWebRX+ en Docker](docs/manuales/33_OPENWEBRX_DOCKER.md) · [catálogo de zona](data/locator/LEEME.md)
- v5.0: [42 Clima en red, WSPR, grabación de pases y AMSAT](docs/manuales/42_CLIMA_RED_SATELITES_GRABACION.md)
- v5.4: Meshtastic dual 433/868 y puente USB ([35](docs/manuales/35_LORA_APRS_MESHTASTIC.md)), acceso y administración ([24](docs/manuales/24_VISITAS_TELEGRAM.md), [34](docs/manuales/34_BLINDAJE_SEGURIDAD.md)), agendas de satélites y grabador ([26](docs/manuales/26_SATELITES.md), [42](docs/manuales/42_CLIMA_RED_SATELITES_GRABACION.md)) y despliegues acotados con copia de seguridad.
- v5.5: [46 Acceso de administradores: usuarios locales y Google](docs/manuales/46_ACCESO_GOOGLE.md)
- [Canales y frecuencias](docs/CANALES_Y_FRECUENCIAS.md): Radio Club, CB, PMR, FM, DAB+, digitales, aviación y marina.

> **¿`sudo: ./install.sh: command not found`?** Se han perdido los permisos al copiar el kit. Usa `sudo bash install.sh …` ([manual 02](docs/manuales/02_INSTALACION.md)).

![Caja del mástil](hardware/caja/render/montaje.png)

### Esquemas de la v5.4

Todos llevan la cabecera y la franja de marca BricoHams SDR.

![Meshtastic dual 433/868 y puente USB](docs/esquemas/28_meshtastic_dual.png)

![Acceso, administración y Files protegidos](docs/esquemas/29_acceso_administracion.png)

![Despliegues acotados con copia de seguridad](docs/esquemas/30_despliegues_acotados.png)

Herramientas de despliegue ([manual 35](docs/manuales/35_LORA_APRS_MESHTASTIC.md), [24](docs/manuales/24_VISITAS_TELEGRAM.md) y [26](docs/manuales/26_SATELITES.md)): `tools/desplegar-mesh-dual.sh`, `tools/desplegar-agenda-telegram.sh` y `tools/finalizar-satelites-ctcss.sh`. Todas exigen `sudo`, hacen copia verificada antes de tocar nada y no admiten contraseñas en la orden. La unidad `files/systemd/bricohams-mesh-puente.service` arranca el puente del nodo 433 sin root.

## Estructura

Resumen. El detalle está en [docs/COMPONENTES.md](docs/COMPONENTES.md) (qué hace cada componente) y [docs/ESTRUCTURA_FICHEROS.md](docs/ESTRUCTURA_FICHEROS.md) (qué hace cada fichero).

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
  share/                   v5.0: subtonos CTCSS (bricohams-ctcss) e importador RepeaterBook (bricohams-rbimport)
  grafana/                 v5.0: panel Grafana de la estación (paso monitorizacion)
firmware/pico-io/          v4: firmware MicroPython de la Pico (sensores y ventiladores)
docs/
  ARQUITECTURA.md          decisiones de arquitectura (ADR)
  COMPONENTES.md           ficha de cada componente: paso, ficheros, servicios, puertos, panel, prueba y manual
  ESTRUCTURA_FICHEROS.md   árbol completo del repositorio y función de cada fichero (generado)
  DATOS.md                 conjuntos de datos: SDR, perfiles, marcadores, puertos, servicios, I2C (generado)
  HARDWARE_Y_GPIO.md       pines GPIO, buses, USB, alimentación, antenas
  EVALUACION_MODULOS.md    evaluación de cada módulo (BME280, LX-LBU2C, WPI408, FlightStick…)
  MEMORIA_TECNICA.md       memoria técnica v3/v4: inventario, cables C1–C20, secuencia de instalación, BOM
  CANALES_Y_FRECUENCIAS.md v4: canales y frecuencias de todos los grupos de marcadores (generado)
  REFERENCIAS.md           fuentes y documentación externa
  esquemas/                diagramas SVG/PNG (bloques, GPIO, cableado, RF, red, alimentación y caja)
  manuales/                manuales paso a paso
hardware/caja/             caja de intemperie v2 (en el mástil): modelo OpenSCAD, STL listos para imprimir y vistas
hardware/caja_v3/          caja v3 modular (electrónica + potencia + SAI opcional): OpenSCAD, 45 STL, vistas
hardware/antenas/          antenas: antenas_bricohams.scad + 30 STL, sim/ (modelos NEC2 y resultados)
hardware/anclajes/         v4: crucetas y soportes impresos (16 STL) y vista de montaje
data/                      repetidores EA5 (lista EA5KGV), marcadores_v4.json y satelites.json
tests/                     pruebas (run_tests.sh)
tools/                     esquemas.py, esquemas_modulos.py, desplegar-*.sh, finalizar-satelites-ctcss.sh,
                           datos.py, caja.sh, caja_v3.sh, antenas.sh, mastil.py,
                           planos_antenas.py, marcadores.py, stl_util.py,
                           anclajes.sh, branding.py, canales.py (v4)
CHANGELOG.md               historial de versiones
```

## Pruebas

```bash
bash tests/run_tests.sh        # shellcheck, sintaxis, BME280, settings, meteo, viento/lluvia, ventiladores, STL
python3 tools/esquemas.py      # regenera los esquemas
python3 tools/esquemas_modulos.py  # esquemas 28-30 (v5.4) y PNG de 26-27
python3 tests/test_mesh_puente.py  # puente Meshtastic
python3 tests/test_login_rate.py   # limitación de intentos de login
python3 tests/test_files_protegidos.py  # Files bloqueado
python3 tests/test_agendas_admin.py     # paneles privados de satélites y clima
python3 tests/test_satpass_fuentes.py   # catálogo y TLE por NORAD
python3 tests/test_finalizar_satelites_ctcss.py  # script de CTCSS externo
node tests/test_satelites_filtros.cjs   # filtros del panel de satélites
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
