# 51 · Radiosondas meteorológicas (AEMET)

> Cada día AEMET suelta globos con una **radiosonda** que emite su posición, altitud y temperatura en
> **400,05–406 MHz**. BricoHams las recibe con un RTL-SDR propio, las pone en el **mapa** de OpenWebRX+
> y en la pestaña **Tiempo** (`/bricohams/clima.html`) y, si quieres, las publica por **MQTT**.
> **Solo recepción**: el módulo no transmite nada.

## 1. Qué añade el kit
- Servicio `bricohams-sondas-rx`: **radiosonde_auto_rx** (projecthorus) en Docker, con el RTL-SDR de
  radiosondas. Su consola solo escucha en `127.0.0.1:5000` (no se publica).
- Servicio `bricohams-sondas`: puente propio que recibe los paquetes UDP de auto_rx
  (`127.0.0.1:55673`), los valida, guarda la **traza** de cada sonda, calcula el **reventón** y la
  **predicción de aterrizaje** y escribe `plugins/receiver/meteo/sondas.json`.
- Capa **«Radiosondas (AEMET)»** en `/map`: sonda actual (serie, tipo, frecuencia, altitud, velocidad
  vertical, temperatura), traza, reventón, aterrizaje previsto y el sitio de lanzamiento 08430.
- Sección **🎈 Radiosondas (AEMET)** en la pestaña Tiempo: tabla de sondas, próximo lanzamiento (00/12 UTC)
  y estado de MQTT (solo servidor, puerto y tema; nunca usuario ni clave).

## 2. Frecuencias
| Sitio | WMO | Sonda | Frecuencia | Lanzamientos |
|---|---|---|---|---|
| **AEMET Murcia** (38,002 N, 1,171 O; a 4 km de la estación) | 08430 | Meteomodem M10 | **403,4 MHz** | 00 y 12 UTC |
| Base Aérea de Alcantarilla (37,952 N, 1,233 O) | — | Meteomodem M20 (ocasional) | 401,5 MHz | variable |
| Mallorca (a 378 km) | 08302 | Vaisala RS41 | 402,0 MHz | 00 y 12 UTC |
| Madrid (a 348 km) | 08221 | Vaisala RS41 | según el lanzamiento | 00 y 12 UTC |
| Dar-El-Beida (Argel) | — | Vaisala RS41 | 401,15 / 402,15 MHz | 00 y 12 UTC |

Banda de búsqueda por defecto: **400,05–406,0 MHz**; `SONDAS_ALWAYS_SCAN="403.4"` mira siempre la de Murcia.
Los datos de frecuencia proceden de los metadatos de SondeHub y pueden cambiar.

## 3. Hardware
- Un **RTL-SDR propio** (no el de OpenWebRX+, ni el de ADS-B ni el de AIS): el instalador se niega si
  `SONDAS_SDR_SERIAL` coincide con otro SDR del kit. Sácalo con `rtl_test` o `bricohams-sdr-serials`.
- Mejor con **TCXO** (RTL-SDR Blog V3/V4): las sondas se desvían y los cristales baratos pierden la señal.
  Ajusta `SONDAS_PPM` si hace falta.
- **Antena de 400 MHz** (un cuarto de onda ≈ 18 cm, o una dipolo/turnstile para 400 MHz) lo más alta y despejada
  posible. La del ADS-B (1090) o la de VHF no sirven bien.
- La Pi ya bloquea `dvb_usb_rtl28xxu` (`/etc/modprobe.d/bricohams-rtlsdr-blacklist.conf`): sin eso Linux
  se queda con el RTL-SDR y auto_rx no puede abrirlo.

## 4. Puesta en marcha
1. En `bricohams.env`:
   ```bash
   SONDAS_ENABLE="yes"
   SONDAS_SDR_SERIAL="00000123"   # serie del RTL-SDR de radiosondas
   # opcionales (valores por defecto):
   SONDAS_MIN_FREQ="400.05"  SONDAS_MAX_FREQ="406.0"  SONDAS_ALWAYS_SCAN="403.4"
   SONDAS_PPM="0"  SONDAS_GAIN="-1"            # -1 = ganancia automática
   SONDAS_PREDICCION="yes"                     # predicción de aterrizaje de SondeHub
   SONDAS_SONDEHUB="no"                        # subir lo recibido a SondeHub (revela tu posición)
   ```
2. `sudo bash install.sh --solo sondas` (instala Docker si falta, baja la imagen
   `ghcr.io/projecthorus/radiosonde_auto_rx:latest` y arranca los dos servicios).
3. Comprueba con `sudo bricohams-check` y `sudo bricohams-servicios`; los registros:
   `journalctl -u bricohams-sondas-rx -u bricohams-sondas -f`.
4. Con `SONDAS_ENABLE="no"` y `--solo sondas`, se paran los servicios y se borra el contenedor.

El `station.cfg` de auto_rx (`/etc/bricohams/sondas/station.cfg`, 600) **se genera**: el instalador extrae de la
propia imagen la plantilla oficial (`/opt/auto_rx/station.cfg.example`, guardada en
`/etc/bricohams/sondas/station.cfg.example`) y `bricohams-sondas --station-cfg PLANTILLA` sustituye solo
nuestras claves (SDR, banda, posición, indicativo, SondeHub, UDP a 127.0.0.1:55673 y consola web en
127.0.0.1:5000 sin control) con los valores de `bricohams.env`; el resto de claves de la plantilla se
conservan, así auto_rx arranca con la configuración completa. No lo edites a mano, se sobrescribe al repetir
el paso. Con `--solo sondas` no hace falta reiniciar nada más.

## 5. Predicción de aterrizaje (SondeHub)
Con `SONDAS_PREDICCION="yes"` el puente consulta `api.v2.sondehub.org/predictions` como **mucho una vez cada
5 minutos por sonda** y solo mientras esa sonda está activa, con un `User-Agent` de BricoHams. Los datos son de
[SondeHub](https://sondehub.org) bajo **CC BY-SA**: la página los atribuye. Pon `SONDAS_PREDICCION="no"` para
no salir a Internet.

## 6. MQTT (opcional)
```bash
SONDAS_MQTT="yes"  SONDAS_MQTT_HOST="127.0.0.1"  SONDAS_MQTT_PORT="1883"
SONDAS_MQTT_USER="" SONDAS_MQTT_PASS=""  SONDAS_MQTT_TOPIC="bricohams/sondas"
```
| Tema | Contenido |
|---|---|
| `<tema>/<serie>/telemetria` | último estado de la sonda (JSON, retenido) |
| `<tema>/<serie>/aterrizaje` | predicción de aterrizaje (JSON, retenido) |
| `<tema>/estado` | `online` / `offline` (retenido; `offline` lo publica el broker si el puente cae) |

El tema no puede llevar comodines (`+`, `#`). **Usuario y clave** se guardan solo en
`/etc/bricohams/sondas.env` (modo 600, solo root) y el servicio los recibe por `LoadCredential`; nunca salen en
`sondas.json` ni en la web. Si el broker cae, el puente sigue y reconecta solo.
Con el Mosquitto local del kit (`127.0.0.1:1883`, sin clave) no hace falta usuario ni clave; para un broker
remoto con clave usa MQTT dentro de una VPN o con el broker de confianza.

## 7. Aspectos legales y privacidad
- **Recepción solamente**: escuchar radiosondas meteorológicas es legal en España y la UE; el módulo no
  emite.
- Las sondas que se encuentran en el suelo son de AEMET: no las abras ni las manipules (hay baterías).
  Avisa a AEMET o a Protección Civil si encuentras una.
- `SONDAS_SONDEHUB="no"` por defecto: subir datos a SondeHub publica la posición de tu estación.

## 8. Problemas frecuentes
| Síntoma | Causa y arreglo |
|---|---|
| `SONDAS_SDR_SERIAL` rechazado | Es el mismo que ADS-B/AIS u otro SDR del kit: usa un RTL-SDR distinto |
| El contenedor no arranca | `journalctl -u bricohams-sondas-rx`; ¿está el SDR conectado? ¿Falta Docker o la imagen? |
| Sin sondas | Es normal entre lanzamientos (00 y 12 UTC); antena de 400 MHz y `SONDAS_PPM` |
| La web dice «Servicio no disponible» | `SONDAS_ENABLE="no"` o el puente parado: `systemctl status bricohams-sondas` |
| Instalación con datos web separados (`web-data.env`) | `sondas.json` no se enlaza a `/var/lib/bricohams/web`: el mapa y Tiempo lo leen directo de `plugins/receiver/meteo` |

Ver también: ADR-72 en [ARQUITECTURA](../ARQUITECTURA.md) y módulo 24 en [DESARROLLO_MODULOS](../DESARROLLO_MODULOS.md).
