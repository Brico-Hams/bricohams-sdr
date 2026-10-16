# Conjuntos de datos de la estación

> Generado por `tools/datos.py` a partir de `files/openwebrx/settings.json.tmpl`, `files/openwebrx/bookmarks.json` y `bricohams.env.example`. No lo edites a mano: cambia la fuente y vuelve a generarlo.

## 1. Receptores SDR

| Id OpenWebRX | Nombre | Tipo | Serie (EEPROM) | Perfiles | Activo | Notas |
|---|---|---|---|---|---|---|
| `sat` | SATÉLITES · HAT | rtl_sdr | 00000101 | 3 | sí | bias-tee: SAT_BIAS_TEE |
| `ham` | RADIOAFICIONADOS · MINI | rtl_sdr | 00000102 | 7 | sí |  |
| `multi` | MULTIPERFIL · AIRE · MAR · FM · HF (V3) | rtl_sdr | 00000103 | 34 | sí | muestreo directo por perfil (HF) |
| `hf` | HF · SDRPLAY · 160-6 m | sdrplay | — | 12 | según HF_SDRPLAY | escucha automática: día sp20 · crepúsculo sp40 · noche sp80 |
| — | ADS-B (fuera de OpenWebRX) | readsb rtlsdr | 00001090 | — | ADSB_ENABLE | FlightStick de RadarBox: Beast :30005 → rbfeeder + MLAT |

## 2.a Perfiles de `sat` · SATÉLITES · HAT

| Id | Nombre | Centro (MHz) | Muestreo (MS/s) | Cubre (MHz) | Inicio (MHz) | Modo | Paso | Muestreo directo |
|---|---|---|---|---|---|---|---|---|
| `sat2m` | 145,8-146 MHz · Satélites 2m · ISS · APRS | 145,9 | 2,048 | 144,9784 – 146,8216 | 145,8 | nfm | 1000 |  |
| `sat70` | 435-438 MHz · Satélites 70cm · SO-50 · RS-44 | 436,7 | 2,4 | 435,62 – 437,78 | 436,795 | nfm | 1000 |  |
| `meteor` | 137 MHz · Meteorológicos · METEOR LRPT | 137,5 | 1,024 | 137,0392 – 137,9608 | 137,9 | nfm | 1000 |  |

## 2.b Perfiles de `ham` · RADIOAFICIONADOS · MINI

| Id | Nombre | Centro (MHz) | Muestreo (MS/s) | Cubre (MHz) | Inicio (MHz) | Modo | Paso | Muestreo directo |
|---|---|---|---|---|---|---|---|---|
| `2m` | 144-146 MHz · HAM 2m | 145 | 2,4 | 143,92 – 146,08 | 145,6 | nfm | 12500 |  |
| `70rep` | 438-440 MHz · HAM 70cm Repetidores · DMR | 438,8 | 2,4 | 437,72 – 439,88 | 438,775 | nfm | 12500 |  |
| `70in` | 430-432 MHz · HAM 70cm Entradas/Enlaces | 431 | 2,4 | 429,92 – 432,08 | 431,175 | nfm | 12500 |  |
| `433` | 432-434 MHz · SSB · LoRa APRS | 433,2 | 2,4 | 432,12 – 434,28 | 433,775 | nfm | 12500 |  |
| `pmr` | PMR446 / DMR446 · Canales 1-16 | 446,1 | 1,024 | 445,6392 – 446,5608 | 446,0063 | nfm | 6250 |  |
| `868` | 868 MHz · Meshtastic · LoRa · ISM | 868,8 | 2,4 | 867,72 – 869,88 | 869,525 | nfm | 25000 |  |
| `tetra` | 420-422,4 MHz · Scan · TETRA | 421,2 | 2,4 | 420,12 – 422,28 | 421,2 | tetra | 25000 |  |

## 2.c Perfiles de `multi` · MULTIPERFIL · AIRE · MAR · FM · HF (V3)

| Id | Nombre | Centro (MHz) | Muestreo (MS/s) | Cubre (MHz) | Inicio (MHz) | Modo | Paso | Muestreo directo |
|---|---|---|---|---|---|---|---|---|
| `air1` | 118-120,4 MHz · AIRBAND · LERI Alcantarilla | 119,2 | 2,4 | 118,12 – 120,28 | 119,2 | am | 8330 |  |
| `air2` | 120,3-122,7 MHz · AIRBAND · LEMI Corvera · 121,5 Emergencia | 121,5 | 2,4 | 120,42 – 122,58 | 121,5 | am | 8330 |  |
| `air3` | 122,7-125,1 MHz · AIRBAND · LELC San Javier · Aeródromos | 123,9 | 2,4 | 122,82 – 124,98 | 123,9 | am | 8330 |  |
| `air4` | 125,1-127,5 MHz · AIRBAND | 126,3 | 2,4 | 125,22 – 127,38 | 126,3 | am | 8330 |  |
| `air5` | 127,5-129,9 MHz · AIRBAND | 128,7 | 2,4 | 127,62 – 129,78 | 128,7 | am | 8330 |  |
| `air6` | 129,9-132,3 MHz · AIRBAND · San Javier APP · ACARS | 131,1 | 2,4 | 130,02 – 132,18 | 131,1 | am | 8330 |  |
| `marina` | 155,8-158,2 MHz · VHF Marina | 157 | 2,4 | 155,92 – 158,08 | 156,8 | nfm | 25000 |  |
| `costeras` | 160,2-162,5 MHz · Estaciones Costeras + AIS | 161,35 | 2,4 | 160,27 – 162,43 | 161,975 | ais | 25000 |  |
| `fm_wifon` | FM ⭐ Wifon FM 97,5 (Murcia) | 97,5 | 2,4 | 96,42 – 98,58 | 97,5 | wfm | 50000 |  |
| `fm1` | FM 87,5-89,8 MHz | 88,6 | 2,4 | 87,52 – 89,68 | 88,6 | wfm | 50000 |  |
| `fm2` | FM 89,6-92,0 MHz | 90,8 | 2,4 | 89,72 – 91,88 | 90,8 | wfm | 50000 |  |
| `fm3` | FM 91,8-94,2 MHz | 93 | 2,4 | 91,92 – 94,08 | 93 | wfm | 50000 |  |
| `fm4` | FM 94,0-96,4 MHz | 95,2 | 2,4 | 94,12 – 96,28 | 95,2 | wfm | 50000 |  |
| `fm5` | FM 96,2-98,6 MHz | 97,4 | 2,4 | 96,32 – 98,48 | 97,4 | wfm | 50000 |  |
| `fm6` | FM 98,4-100,8 MHz | 99,6 | 2,4 | 98,52 – 100,68 | 99,6 | wfm | 50000 |  |
| `fm7` | FM 100,6-103,0 MHz | 101,8 | 2,4 | 100,72 – 102,88 | 101,8 | wfm | 50000 |  |
| `fm8` | FM 102,8-105,2 MHz | 104 | 2,4 | 102,92 – 105,08 | 104 | wfm | 50000 |  |
| `fm9` | FM 105,0-107,4 MHz | 106,2 | 2,4 | 105,12 – 107,28 | 106,2 | wfm | 50000 |  |
| `fm10` | FM 105,8-108,0 MHz | 107 | 2,4 | 105,92 – 108,08 | 107 | wfm | 50000 |  |
| `dab8C` | DAB+ Bloque 8C · 199,360 MHz | 199,36 | 2,048 | 198,4384 – 200,2816 | 199,36 | dab |  |  |
| `dab9A` | DAB+ Bloque 9A · 202,928 MHz | 202,928 | 2,048 | 202,0064 – 203,8496 | 202,928 | dab |  |  |
| `dab9C` | DAB+ Bloque 9C · 206,352 MHz | 206,352 | 2,048 | 205,4304 – 207,2736 | 206,352 | dab |  |  |
| `hf160` | 1,8 MHz  HAM 160m (solo con el V3 como HF) | 1,9 | 1,024 | 1,4392 – 2,3608 | 1,84 | ft8 | 1000 | rama Q |
| `hf80` | 3,5 MHz  HAM 80m (solo con el V3 como HF) | 2,8 | 2,4 | 1,72 – 3,88 | 3,573 | ft8 | 1000 | rama Q |
| `hf60` | 5,3 MHz  HAM 60m (solo con el V3 como HF) | 5,3 | 1,024 | 4,8392 – 5,7608 | 5,357 | ft8 | 1000 | rama Q |
| `hf40` | 7 MHz  HAM 40m (solo con el V3 como HF) | 7,09 | 1,024 | 6,6292 – 7,5508 | 7,11 | lsb | 1000 | rama Q |
| `hf30` | 10 MHz  HAM 30m (solo con el V3 como HF) | 10,125 | 1,024 | 9,6642 – 10,5858 | 10,136 | ft8 | 1000 | rama Q |
| `hf20` | 14 MHz  HAM 20m (solo con el V3 como HF) | 14,175 | 1,024 | 13,7142 – 14,6358 | 14,074 | ft8 | 1000 | rama Q |
| `hf17` | 18 MHz  HAM 17m (solo con el V3 como HF) | 18,118 | 1,024 | 17,6572 – 18,5788 | 17,967 | hfdl | 1000 | rama Q |
| `hf15` | 21 MHz  HAM 15m (solo con el V3 como HF) | 21,225 | 1 | 20,775 – 21,675 | 21,074 | ft8 | 1000 | rama Q |
| `hf12` | 24 MHz  HAM 12m (solo con el V3 como HF) | 24,94 | 1,024 | 24,4792 – 25,4008 | 24,915 | ft8 | 1000 | no |
| `hf11` | 27 MHz · CB 11 m · 40 canales (Radio Club: canal 32 · 27,325) (solo con el V3 como HF) | 27,185 | 1 | 26,735 – 27,635 | 27,185 | nfm | 1000 | no |
| `hf10` | 28 MHz  HAM 10m (solo con el V3 como HF) | 28,85 | 2,4 | 27,77 – 29,93 | 28,074 | ft8 | 1000 | no |
| `hf6` | 50-52 MHz  HAM 6m (solo con el V3 como HF) | 51 | 2,4 | 49,92 – 52,08 | 50,313 | ft8 | 1000 | no |

## 2.d Perfiles de `hf` · HF · SDRPLAY · 160-6 m

| Id | Nombre | Centro (MHz) | Muestreo (MS/s) | Cubre (MHz) | Inicio (MHz) | Modo | Paso | Muestreo directo |
|---|---|---|---|---|---|---|---|---|
| `sp160` | 1,8 MHz  HAM 160m | 1,9 | 0,384 | 1,7272 – 2,0728 | 1,84 | ft8 | 1000 |  |
| `sp80` | 3,5 MHz  HAM 80m | 2,8 | 3 | 1,45 – 4,15 | 3,573 | ft8 | 1000 |  |
| `sp60` | 5,3 MHz  HAM 60m | 5,36 | 0,384 | 5,1872 – 5,5328 | 5,357 | ft8 | 1000 |  |
| `sp40` | 7 MHz  HAM 40m | 7,09 | 0,384 | 6,9172 – 7,2628 | 7,11 | lsb | 1000 |  |
| `sp30` | 10 MHz  HAM 30m | 10,125 | 0,384 | 9,9522 – 10,2978 | 10,136 | ft8 | 1000 |  |
| `sp20` | 14 MHz  HAM 20m | 14,175 | 0,5 | 13,95 – 14,4 | 14,074 | ft8 | 1000 |  |
| `sp17` | 18 MHz  HAM 17m | 18,118 | 0,384 | 17,9452 – 18,2908 | 17,967 | hfdl | 1000 |  |
| `sp15` | 21 MHz  HAM 15m | 21,225 | 1 | 20,775 – 21,675 | 21,074 | ft8 | 1000 |  |
| `sp12` | 24 MHz  HAM 12m | 24,94 | 0,384 | 24,7672 – 25,1128 | 24,915 | ft8 | 1000 |  |
| `sp11` | 27 MHz · CB 11 m · 40 canales (Radio Club: canal 32 · 27,325) | 27,185 | 1 | 26,735 – 27,635 | 27,185 | nfm | 1000 |  |
| `sp10` | 28 MHz  HAM 10m | 28,85 | 2 | 27,95 – 29,75 | 28,074 | ft8 | 1000 |  |
| `sp6` | 50-52 MHz  HAM 6m | 51 | 3 | 49,65 – 52,35 | 50,313 | ft8 | 1000 |  |

## 3. Marcadores

Total en el kit: **376**. Hotspots de casa y repetidores digitales de Sierra Espuña:

| Frecuencia (MHz) | Modo | Nombre | Descripción | Perfil que la cubre |
|---|---|---|---|---|
| 431,35 | dmr | Sierra Espuña entrada | Subida al repetidor digital de Sierra Espuña | 70in (429,9–432,1) |
| 431,775 | ysf | YSF Hotspot N0CALL entrada | Subida al hotspot YSF local | 70in (429,9–432,1) |
| 431,85 | dmr | DMR Hotspot N0CALL entrada | Subida al hotspot local | 70in (429,9–432,1) |
| 438,25 | dmr | DMR ED5ZAN Sierra Espuña | BrandMeister ID 214520 · CC1 · Entrada 430.650 | 70rep (437,7–439,9) |
| 438,95 | dmr | Sierra Espuña · repetidor digital | Repetidor digital de la Región de Murcia · Entrada 431.350 | 70rep (437,7–439,9) |
| 439,375 | ysf | YSF Hotspot N0CALL (local) | Hotspot de casa · Entrada 431.775 | 70rep (437,7–439,9) |
| 439,45 | dmr | DMR Hotspot N0CALL (local) | MMDVM_HS_Dual_Hat dúplex · Entrada 431.850 | 70rep (437,7–439,9) |

⚠ En los marcadores anteriores ya estaba **ED5ZAN** (DMR BrandMeister, 438,250 / entrada 430,650). N0CALL indica ahora **438,950 / 431,350** como repetidor digital de Sierra Espuña: se han dejado los dos hasta confirmar cuál está activo.

Convención: la **salida** del hotspot/repetidor es lo que oyes (TX del equipo), la **entrada** es donde transmites (RX del equipo).

## 4. Puertos de red

| Puerto | Servicio | Alcance |
|---|---|---|
| 443/tcp | v4.2 · nginx https: /login y /settings forzados (y todo, si se quiere) | **abrir al exterior** |
| 80/tcp | v4.2 · nginx: receptor público por HTTP (SSL_MODO=admin), Let's Encrypt | **abrir al exterior** |
| 8073/tcp | OpenWebRX+ (detrás de nginx desde v4) | LAN |
| 8504/tcp | v4 · lighttpd · tar1090 (detrás de nginx) | 127.0.0.1 |
| 8075/tcp | v4 · bricohams-api (indicativos) | 127.0.0.1 |
| 1883/tcp | v4 · mosquitto (informes de clientes de OpenWebRX) | 127.0.0.1 |
| 8889/tcp + 8189/udp | MediaMTX WebRTC (vídeo en directo) | opcional |
| 8888/tcp | MediaMTX HLS | LAN |
| 8554/tcp | MediaMTX RTSP `rtsp://<pi>:8554/mastil` | LAN |
| 9997/tcp | MediaMTX API | 127.0.0.1 |
| 8076/tcp | v4.5 · bricohams-mesh-admin (panel Meshtastic, detrás de nginx en /settings/bricohams/meshtastic, exige sesión de admin de OpenWebRX+) | 127.0.0.1 |
| 8443/tcp | v4.5 · nginx: cliente web oficial de Meshtastic (proxy a 9443 con autenticación de sesión de /settings) | LAN (admin only) |
| 8445/tcp | v4.6 · nginx: interfaz web de OpenTAKServer (usuario TAK) | LAN |
| 8089/tcp | v4.6 · OpenTAKServer CoT TLS con certificado de cliente | LAN |
| 8446/tcp | v4.6 · nginx: alta de certificados TAK (enrollment) | LAN |
| 8447/tcp | v4.6 · nginx: Marti API TAK con certificado de cliente | LAN |
| 8081/tcp | v4.6 · OpenTAKServer interno | 127.0.0.1 |
| 5432, 5672/tcp | v4.6 · PostgreSQL y RabbitMQ de TAK (cortafuegos `bricohams-tak-fw`) | 127.0.0.1 |
| 9443/tcp | meshtasticd web: **bloqueada por firewall** `bricohams-meshweb-fw` (nftables) desde todas las IPs excepto localhost | 127.0.0.1 |
| 4403/tcp | meshtasticd API | LAN |
| 30005/tcp | readsb salida Beast | local |
| 30003, 30002, 30104/tcp | readsb SBS / raw / entrada Beast | local |
| 2947/tcp | gpsd | local |
| 14580/tcp saliente | APRS-IS (iGate, WX, OpenWebRX) | saliente |
| 443/tcp saliente | AEMET, Open-Meteo, NOAA, RadarBox, apt, GitHub | saliente |

## 5. Servicios systemd

| Unidad | Qué hace | Paso de install.sh |
|---|---|---|
| `openwebrx` | receptor web | openwebrx / configuracion |
| `sdrplay` | API del SDRplay | sdrplay (pendiente) |
| `bricohams-hat-power` | GPIO de alimentación de módulos del HAT | hat |
| `gpsd` | GPS del HAT | hat |
| `chrony` | hora NMEA + PPS | hat |
| `meshtasticd` | nodo Meshtastic 868 | meshtastic |
| `mediamtx` | vídeo de la cámara | camara |
| `bricohams-camsnap` | foto para la web | camara |
| `bricohams-meteo.timer` | AEMET + Open-Meteo cada 10 min | meteo |
| `bricohams-wx` | sensor BME280 + viento RS485 + lluvia + WX APRS | sensor |
| `bricohams-fan` | ventiladores de la caja v3 (PWM + tacómetros + DS18B20) | ventilacion |
| `readsb` | decodificador ADS-B | adsb |
| `rbfeeder` | envío a RadarBox + MLAT | adsb |
| `lighttpd` | tar1090 | adsb |
| `bricohams-backup.timer` | copia diaria 04:30 (v4: desactivado, lo hace cron) | herramientas |
| `bricohams-io` | v4 · puente USB con la Pico (sensores y ventiladores) | io |
| `bricohams-satpass.timer` | v4 · próximos pases de satélites | satelites |
| `nginx` | v4 · https y proxy | web |
| `bricohams-api` | v4 · ficha de indicativos (RadioID/QRZ) | web |
| `mosquitto` | v4 · MQTT local | visitas |
| `bricohams-visitas` | v4 · oyentes, GeoIP y Telegram | visitas |
| `cron (`/etc/cron.d/bricohams`)` | v4 · copias, actualización, reinicio, salud, resumen | tareas |

## 6. Bus I2C-1 (GPIO2/GPIO3)

| Dirección | Dispositivo | Uso |
|---|---|---|
| 0x51 | PCF85063A (HAT) | RTC, `dtoverlay=i2c-rtc,pcf85063a` → /dev/rtc0 |
| 0x76 / 0x77 | BME280 (ID 0x60) o BMP280 (ID 0x58) | `bricohams-wx` |

## 7. Indicativos y WiFi

| Indicativo | Qué es | Dónde |
|---|---|---|
| N0CALL | iGate APRS de OpenWebRX (packet 144,800) | settings.json `aprs_callsign` |
| N0CALL-10 | iGate LoRa APRS 433,775 (LilyGO, solo RX) | `IGATE_CALLSIGN` |
| N0CALL-13 | Estación meteorológica (BME280 + viento + lluvia) | `WX_APRS_CALLSIGN` |
| N0CALL-14 | Estación WX LoRa alternativa (3.er LilyGO, CA2RXU) | `WXLORA_CALLSIGN` |
| SDR BricoHams 868 / SB86 | Nodo Meshtastic 868 (HAT) | `MESH_LONG_NAME` |
| SDR BricoHams 433 / SB43 | Nodo Meshtastic 433 (LilyGO) | `MESH433_LONG_NAME` |

## 8. Canales Meshtastic (QR de la red)

Origen: `MESH_CHANNEL_URL` (QR aportado por N0CALL el 04/10/2026). Claves por defecto públicas (índices 1 y 2).

| Índice | Canal | Clave |
|---|---|---|
| 0 (principal) | SFNarrow | por defecto (AQ==) |
| 1 | Murcia | por defecto |
| 2 | Cartagena | por defecto |
| 3 | Test | por defecto nº 2 · posición activada |
| 4 | Alicante | por defecto |
| 5 | BricoHams (`MESH868_PRIVATE_NAME`) | **privada AES-256** (`MESH868_PRIVATE_PSK`, solo en bricohams.env) · **solo nodo 868** |

Radio del QR: EU_868, **869,618 MHz**, BW 62,5 kHz, SF7, CR 4/5, saltos 3, potencia 27 dBm (el SX1262 del HAT se queda en 22 dBm), ganancia RX reforzada. En el LilyGO 433 se cargan los mismos canales y luego la radio pasa a EU_433 LONG_FAST.

## 9. Rutas importantes en la Raspberry

| Ruta | Contenido |
|---|---|
| `/etc/bricohams/bricohams.env` | configuración y claves (600 root) |
| `/etc/bricohams/meteo.env, wx.env` | variables de los servicios (640 root:openwebrx) |
| `/var/lib/openwebrx/` | settings.json, users.json, bookmarks.json, imágenes |
| `/usr/lib/python3/dist-packages/htdocs/plugins/` | plugins web |
| `…/plugins/receiver/meteo/meteo.json, sensor.json` | datos del tiempo para la web |
| `…/plugins/receiver/camara/snap/` | foto de la cámara (tmpfs) |
| `/var/lib/bricohams/wx-history.json` | histórico 24 h del sensor |
| `/var/lib/bricohams/lluvia.json` | contador del pluviómetro (v3) |
| `/etc/bricohams/fan.env` | curva de los ventiladores (v3) |
| `/run/bricohams/caja.json, …/meteo/caja.json` | estado de la caja y ventiladores (v3) |
| `/etc/udev/rules.d/99-bricohams-rs485.rules` | /dev/rs485 (adaptador USB-RS485, v3) |
| `/etc/meshtasticd/config.d/hackergadgets-hat.yaml` | pines LoRa del HAT |
| `/etc/mediamtx/mediamtx.yml` | cámara |
| `/etc/default/readsb, /etc/rbfeeder.ini` | ADS-B |
| `/etc/udev/rules.d/99-bricohams-lilygo.rules` | /dev/lilygo-mesh y /dev/lilygo-igate |
| `/boot/firmware/config.txt` | bloque `# >>> BricoHams` |
| `/var/backups/bricohams/` | copias diarias (retención local de cinco días) |
| `/opt/bricohams/kit/` | copia del kit (sin claves) |
| `/var/log/bricohams-install.log` | registro del instalador |
| `/etc/bricohams/{web,api,visitas,telegram}.env` | v4 · variables de los servicios web (640) |
| `/var/lib/bricohams/visitas.sqlite` | v4 · oyentes (IP parcial, 90 días) |
| `/var/lib/bricohams/dbip-city-lite.mmdb` | v4 · GeoIP local (DB-IP Lite) |
| `/var/lib/bricohams/indicativos.sqlite` | v4 · caché de RadioID/QRZ (7 días) |
| `/var/lib/bricohams/tle.json` | v4 · elementos orbitales de CelesTrak |
| `/etc/cron.d/bricohams, /etc/sudoers.d/bricohams` | v4 · tareas de la cuenta de servicio |
| `/dev/bricohams-io` | v4 · Pico (udev 2e8a:0005) |
| `/run/bricohams/io.json, fan.cmd` | v4 · lecturas de la Pico y orden de ventiladores |
| `/var/lib/bricohams/kit-estado` | v4.1 · huellas de los pasos para `install.sh --actualizar` (600) |
| `/var/lib/bricohams/bookmarks.kit.json` | v4.1 · marcadores del kit instalado (para conservar los propios) |
| `/var/lib/bricohams/actualizaciones.log` | v4.1 · historial de actualizaciones |
| `/var/lib/bricohams/locator/{aemet,fmdx}.json` | v4.3 · datos de zona bajados en la Pi (caché 30 días) |
| `/usr/local/lib/bricohams/, /usr/local/bin/bricohams-locator` | v4.3 · zona por locator (manual 32) |
| `/opt/owrx-docker/{docker-compose.yaml,etc,var,plugins}` | v4.3 · OpenWebRX+ en Docker (OWRX_BACKEND=docker, manual 33) |
| `/usr/local/sbin/bricohams-blindaje, /etc/bricohams/cortafuegos.nft` | v4.4 · blindaje y cortafuegos del host (manual 34) |
| `/etc/ssh/sshd_config.d/90-bricohams.conf, /etc/fail2ban/jail.d/bricohams.conf, /etc/sysctl.d/90-bricohams.conf` | v4.4 · SSH, fail2ban y núcleo endurecidos |
| `/var/backups/bricohams-blindaje/` | v4.4 · copias de «aplicar» para «deshacer» (700) |
| `/run/bricohams-rak/rak-aprs.json` | v4.5 · estado del RAK4631: firmware, caja, GPS redondeado, oídos (manual 35) |
| `/run/bricohams-mesh/mesh.json` | v4.5 · nodos Meshtastic 433/868 y lo publicado en el mapa de OpenWebRX+ |
| `/opt/bricohams/firmware/rak4631-lora-aprs/bin/` | v4.5 · firmware del RAK4631 (.zip DFU, .uf2, .hex) |
| `/etc/udev/rules.d/99-bricohams-dispositivos.rules` | v4.5 · /dev/rak-aprs y /dev/lilygo-mesh por VID:PID y serie |
| `/etc/issue.net, /etc/update-motd.d/20-bricohams` | v4.5 · banner SSH: aviso legal y estado al entrar |
| `/etc/nginx/snippets/bricohams-sdr-rutas.conf` | v4.2 · rutas comunes HTTP/HTTPS de nginx |
| `/usr/local/bin/owrx-clone, /var/backups/owrx-clone/` | v4.2 · perfiles de OpenWebRX+ y copias previas de cada importación |
| `/var/backups/bricohams/perfil-owrx-*.owrx.tar.gz` | v4.2 · perfil diario de OpenWebRX+ (retención local de cinco días) |
| `/etc/bricohams/perfil-importado` | v4.2 · marca: la configuración viene de un perfil importado |

## 10. Caja v2 (en el mástil): conectores de la cara inferior (de izquierda a derecha)

Origen: `SMA_LABELS` de `hardware/caja/caja_bricohams.scad`.

| Pos. | Rótulo | Tipo | Va a |
|---|---|---|---|
| 0 | 230 V | prensaestopas PG9 | cargador USB 45 W (compartimento de potencia) |
| 1 | SAT | SMA hembra pasamuros | RTL del HAT (eggbeater + LNA) |
| 2 | HAM | SMA hembra pasamuros | Mini RTL-SDR (colineal) |
| 3 | VHF | SMA hembra pasamuros | diplexor VHF/UHF → V3 (discone) |
| 4 | HF | SMA hembra pasamuros | diplexor HF → V3 (hilo largo) |
| 5 | ADSB | SMA hembra pasamuros | FlightStick (1090 MHz) |
| 6 | 868 | SMA hembra pasamuros | SX1262 del HAT |
| 7 | GPS | SMA hembra pasamuros | GPS del HAT (antena activa) |
| 8 | M433 | SMA hembra pasamuros | LilyGO Meshtastic (transmite) |
| 9 | IG433 | SMA hembra pasamuros | LilyGO iGate (solo RX) |
| 2.ª fila | WX | prensaestopas PG7 | cable del BME280 |
| 2.ª fila | LAN | prensaestopas M20 | Ethernet (opcional) |

## 11. Alimentación en la caja v2 (la v3 está en MEMORIA_TECNICA y en el esquema 15)

| Puerto del cargador 45 W | Consumidor | Típico | Máximo del puerto |
|---|---|---|---|
| USB-C PD 5 V 3 A | Raspberry Pi 5 + HAT + cámara | 8–12 W | 15 W |
| USB-A 5 V 2,4 A | hub alimentado: Mini, V3, FlightStick, 2 LilyGO | 5–7 W | 12 W |
| — | **Total** | **13–19 W** | **45 W** |

## 12. Redes WiFi (NetworkManager)

| Conexión | SSID | Prioridad | Quién |
|---|---|---|---|
| bricohams-wifi-1 | `WIFI_SSID_1` | 20 | Raspberry Pi (5 GHz) |
| bricohams-wifi-2 | `WIFI_SSID_2` | 10 | Raspberry Pi (respaldo 2,4 GHz) |
| — | `LILYGO_WIFI_SSID` | — | iGate LilyGO (solo 2,4 GHz) |

La contraseña solo está en `bricohams.env` (`WIFI_PASS`, `LILYGO_WIFI_PASS`).

## 13. Caja v3: pasamuros N de la cara inferior

Origen: `N_ROWS` de `hardware/caja_v3/caja_v3.scad` (manual 17).

| Fila (altura z) | Rótulo | Va a |
|---|---|---|
| z = 26 mm | SAT | RTL del HAT (eggbeater + LNA) |
| z = 26 mm | HAM | Mini RTL-SDR (quad 2 m/70 + diplexor) |
| z = 26 mm | VHF | diplexor → V3 (discone grande) |
| z = 26 mm | HF | inyector MLA-30 → diplexor → V3 |
| z = 26 mm | ADSB | bias-tee 5 V → FlightStick (LNA en la antena) |
| z = 26 mm | 868 | SX1262 del HAT (Bigsignal 868) |
| z = 26 mm | GPS | GPS del HAT |
| z = 56 mm | M433 | LilyGO Meshtastic (fibra 433) |
| z = 56 mm | IG433 | FBP-433s → LilyGO iGate (Bigsignal 433) |
| z = 56 mm | DISC2 | discone compacta → bahía de expansión |
| z = 56 mm | HF2 | SDRplay antena B (futura) |
| z = 56 mm | R1 | reserva |
| z = 56 mm | R2 | reserva |
| z = 56 mm | R3 | reserva |
| z = 88 mm | M25 PWR · M20 LAN · PG7 WX · PG7 VIENTO · PG7 LLUVIA · PG7 RES | prensaestopas |

## 14. v4 · Pico «bricohams-io» (con el HAT puesto, `IO_MODE="pico"`)

| Pin Pico | GP | Uso |
|---|---|---|
| 6 / 7 | GP4 / GP5 | I2C0 SDA / SCL · BME280 (0x76/0x77) |
| 29 | GP22 | DS18B20 1-Wire (4,7 kΩ a 3V3) |
| 20 | GP15 | pluviómetro (10 kΩ a 3V3 + 100 nF) |
| 21 / 22 | GP16 / GP17 | PWM 25 kHz ventiladores (2N7002, invertido) |
| 24 / 25 | GP18 / GP19 | tacómetros (10 kΩ a 3V3 + 1 kΩ) |
| 36 / 38 | 3V3(OUT) / GND | alimentación de sensores |

Protocolo: una línea JSON cada 2 s; órdenes `FAN d1 d2` y `PING`; sin órdenes en 60 s → ventiladores al 100 %. Modo actual: `IO_MODE=pico`.

### 14 bis. GPIO de la Pi (solo sin HAT, `IO_MODE="gpio"`)

| Pin | GPIO | Uso | Variable |
|---|---|---|---|
| 7 | GPIO4 | DS18B20 (1-Wire) | `W1_GPIO` |
| 11 | GPIO17 | pluviómetro | `RAIN_GPIO` |
| 15 | GPIO22 | tacómetro ventilador de entrada | `FAN_TACH_GPIOS` |
| 29 | GPIO5 | tacómetro ventilador de salida | `FAN_TACH_GPIOS` |
| 32 | GPIO12 | PWM ventilador de entrada (PWM0 c0) | `FAN_PWM_GPIOS` |
| 33 | GPIO13 | PWM ventilador de salida (PWM0 c1) | `FAN_PWM_GPIOS` |

Viento: RS485 Modbus RTU 4800 8N1 por `/dev/rs485` · anemómetro en dirección 1, veleta en 2 (`sector8`).
Curva de ventiladores: CPU 55–75 °C, caja 35–45 °C, mínimo 30 %, histéresis 3 °C.

## 15. Plan del mástil

Origen: `ANTENAS` de `tools/mastil.py` (esquema 11).

| Antena | Altura (m) | Brazo (m) | Rumbo | Banda | Transmite |
|---|---|---|---|---|---|
| Discone grande (MULTIPERFIL) | 2,90 | 0,00 | punta | 88–1300 MHz | no |
| ADS-B λ/4 + LNA | 1,70 | 0,80 | E | 1090 MHz | no |
| GPS activa | 1,70 | 0,40 | E | 1575 MHz | no |
| Meshtastic 433 (fibra) | 1,70 | 0,80 | O | 433 MHz | sí |
| Anemómetro RS485 | 1,50 | 0,80 | N | — | no |
| Veleta RS485 | 1,50 | 0,80 | S | — | no |
| Quad 2 m/70 cm (RADIOAFICIONADOS) | 0,95 | 0,00 | rumbo | 144/430 MHz | no |
| Bigsignal 868 (Meshtastic HAT) | 0,20 | 0,80 | N | 868 MHz | sí |
| Bigsignal 433 (iGate) | 0,20 | 0,80 | S | 433 MHz | no |
| Garita BME280 | 0,05 | 0,45 | N | — | no |

Mástil Ø40 × 2: 530 MPa a 130 km/h sin vientos (límite S235: 235 MPa) → **vientos a 2,0 m**: 92 MPa a 150 km/h.

## 16. Antenas construidas: resultados NEC2

Origen: `hardware/antenas/sim/resultados/*.json`.

| Antena | f (MHz) | Ganancia (dBi) | F/B (dB) | ROE 50 Ω |
|---|---|---|---|---|
| Quad 2 m | 144 | 8,7 | 24 | 2,13 (sin adaptar) |
| Quad 2 m | 145 | 8,5 | 33 | 1,29 (con λ/4 de 75 Ω) |
| Quad 2 m | 146 | 8,3 | 26 | 2,29 (sin adaptar) |
| Quad 70 cm | 432 | 9,8 | 26 | 1,55 |
| Quad 70 cm | 436 | 9,8 | 36 | 1,16 |
| Quad 70 cm | 440 | 9,7 | 22 | 1,52 |
| ADS-B λ/4 (62 / 68 mm) | 1090 | 2,25 (horizonte) | — | 1,17 |

Medidas de corte: manuales 12 (quad), 13 (discones) y 14 (ADS-B).

## 17. Repetidores en los marcadores (subtono en la descripción)

Origen: `data/repetidores_EA5KGV_zonaEA5.csv` → `tools/marcadores.py`. Primer marcador: **⭐ 97.5 Wifon FM**.

| Frecuencia (MHz) | Nombre | Descripción |
|---|---|---|
| 144,825 | EC5RCA (simplex) | Subtono 82,5 Hz para abrirlo (para escuchar no hace falta) · lista EA5KGV, posición 179 |
| 145,2875 | EA5ABE (simplex) | Subtono 77,0 Hz para abrirlo (para escuchar no hace falta) · lista EA5KGV, posición 174 |
| 145,3875 | EA5HTK (simplex) | Subtono 77,0 Hz para abrirlo (para escuchar no hace falta) · lista EA5KGV, posición 176 |
| 145,575 | ED5YAM | Entrada 144,975 MHz (-0,6 MHz) · Subtono 118,8 Hz para abrirlo (para escuchar no hace falta) · lista EA5KGV, posición 398 |
| 145,65 | R2 ED5YAG Alicante | Entrada 145,05 MHz (-0,6 MHz) · Subtono 88,5 Hz para abrirlo (para escuchar no hace falta) · lista EA5KGV, posición 35 [EA5KGV también ED5YAN: Entrada 145,05 MHz (-0,6 MHz) · Subtono 123,0 Hz para abrirlo (para escuchar no hace falta)] |
| 145,675 | R3 ED5YAW Albacete | Entrada 145,075 MHz (-0,6 MHz) · Subtono 123,0 Hz para abrirlo (para escuchar no hace falta) · lista EA5KGV, posición 50 |
| 145,6875 | R3X ED5ZAC | Entrada 145,0875 MHz (-0,6 MHz) · Sin subtono · lista EA5KGV, posición 172 |
| 145,7 | R4 ED5YAA | Entrada 145,1 MHz (-0,6 MHz) · Subtono 88,5 Hz para abrirlo (para escuchar no hace falta) · lista EA5KGV, posición 180 [EA5KGV también ED5YAF: Entrada 145,1 MHz (-0,6 MHz) · Subtono 77,0 Hz para abrirlo (para escuchar no hace falta)] [EA5KGV también ED5YAH: Entrada 145,1 MHz (-0,6 MHz) · Subtono 79,7 Hz para abrirlo (para escuchar no hace falta)] |
| 145,725 | R5 ED5YAI | Entrada 145,125 MHz (-0,6 MHz) · Subtono 77,0 Hz para abrirlo (para escuchar no hace falta) · lista EA5KGV, posición 191 |
| 145,75 | R6 ED5YAC | Entrada 145,15 MHz (-0,6 MHz) · Subtono 118,8 Hz para abrirlo (para escuchar no hace falta) · lista EA5KGV, posición 182 [EA5KGV también ED5YAO: Entrada 145,15 MHz (-0,6 MHz) · Sin subtono] |
| 145,775 | R7 ED5YAQ | Entrada 145,175 MHz (-0,6 MHz) · Subtono 77,0 Hz para abrirlo (para escuchar no hace falta) · lista EA5KGV, posición 196 |
| 430,925 | EA5ABE (simplex) | Subtono 77,0 Hz para abrirlo (para escuchar no hace falta) · lista EA5KGV, posición 175 |
| 431,025 | EA5IRD (simplex) | Subtono 88,5 Hz para abrirlo (para escuchar no hace falta) · lista EA5KGV, posición 177 |
| 438,275 | ED5YAU | Entrada 430,675 MHz (-7,6 MHz) · Sin subtono · lista EA5KGV, posición 171 |
| 438,3 | ED5ZAC | Entrada 430,7 MHz (-7,6 MHz) · Sin subtono · lista EA5KGV, posición 173 |
| 438,35 | ED5ZAB | Entrada 430,75 MHz (-7,6 MHz) · Sin subtono · lista EA5KGV, posición 170 |
| 438,725 | RU-73 ED5YAE | Entrada 431,125 MHz (-7,6 MHz) · Subtono 79,7 Hz para abrirlo (para escuchar no hace falta) · lista EA5KGV, posición 184 |
| 438,8 | RU-76 ED5YAD | Entrada 431,2 MHz (-7,6 MHz) · Subtono 118,8 Hz para abrirlo (para escuchar no hace falta) · lista EA5KGV, posición 183 |
| 438,825 | RU-77 ED5YAS | Entrada 431,225 MHz (-7,6 MHz) · Subtono 71,9 Hz para abrirlo (para escuchar no hace falta) · lista EA5KGV, posición 197 |
| 438,875 | RU-79 ED5YBC | Entrada 431,275 MHz (-7,6 MHz) · Subtono 77,0 Hz para abrirlo (para escuchar no hace falta) · lista EA5KGV, posición 402 |
| 439 | RU-84 ED5YAF | Entrada 431,4 MHz (-7,6 MHz) · Subtono 77,0 Hz para abrirlo (para escuchar no hace falta) · lista EA5KGV, posición 186 |
| 439,05 | RU-86 ED5YAM | Entrada 431,45 MHz (-7,6 MHz) · Subtono 118,8 Hz para abrirlo (para escuchar no hace falta) · lista EA5KGV, posición 193 |
| 439,075 | RU-87 ED5YAV | Entrada 431,475 MHz (-7,6 MHz) · Subtono 118,8 Hz para abrirlo (para escuchar no hace falta) · lista EA5KGV, posición 397 |
| 439,1 | RU-88 ED5YAA | Entrada 431,5 MHz (-7,6 MHz) · Sin subtono · lista EA5KGV, posición 181 |
| 439,15 | RU-90 ED5YAH | Entrada 431,55 MHz (-7,6 MHz) · Subtono 79,7 Hz para abrirlo (para escuchar no hace falta) · lista EA5KGV, posición 190 |
| 439,275 | RU-95 ED5YBD | Entrada 431,675 MHz (-7,6 MHz) · Subtono 77,0 Hz para abrirlo (para escuchar no hace falta) · lista EA5KGV, posición 403 |
| 439,3 | RU-96 ED5YBB | Entrada 431,7 MHz (-7,6 MHz) · Subtono 79,7 Hz para abrirlo (para escuchar no hace falta) · lista EA5KGV, posición 401 |

