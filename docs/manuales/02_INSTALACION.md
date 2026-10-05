# 02 · Instalación

## 1. Personalizar `bricohams.env`
Antes de instalar, copia `bricohams.env.example` a `bricohams.env`. El ejemplo no contiene contraseñas y deja vacíos el correo y las redes WiFi. Cambia como mínimo el indicativo, QTH, país, latitud, longitud y altitud; usa `N0CALL` y `0,0` solo como valores de muestra, nunca para emitir.

- **Claves según los servicios que habilites:**

  | Variable | Qué es |
  |---|---|
  | `APRS_PASSCODE` | código APRS-IS de tu indicativo; necesario para `WX_APRS` y el iGate APRS |
  | `APRS_IGATE_ENABLE` | vacío = activar el iGate de OpenWebRX solo si hay indicativo propio y passcode; `yes/no` lo fuerza |
  | `MAGIC_KEY` | clave opcional de OpenWebRX+ |
  | `RECEIVERBOOK_KEY` | clave opcional de Receiverbook |
  | `OPENWEATHERMAP_KEY` | clave opcional para las capas de OpenWeatherMap |
  | `ADMIN_EMAIL` / `SSL_EMAIL` | correo para Let's Encrypt; opcional con certificado autofirmado |

- **Ajustes de la estación:**

  | Variable | Qué es |
  |---|---|
  | `STATION_QTH`, `STATION_COUNTRY`, `STATION_LAT`, `STATION_LON`, `STATION_ASL` | nombre/país y coordenadas de tu estación; país ISO de dos letras |
  | `WIFI_COUNTRY`, `WIFI_SSID_1`, `WIFI_SSID_2`, `WIFI_PASS` | código regulatorio y redes WiFi propias; deja los SSID vacíos si usas Ethernet |
  | `LILYGO_WIFI_SSID`, `LILYGO_WIFI_PASS` | WiFi de 2,4 GHz del ESP32, si instalas el iGate |
  | `CALLSIGN`, `IGATE_CALLSIGN`, `WX_APRS_CALLSIGN`, `WXLORA_CALLSIGN` | usa indicativos tuyos y con sufijos asignados; no dejes los valores de muestra |
  | `LISTENERS_COUNTRY` | código ISO del país del receptor para la bandera de LST; vacío usa `STATION_COUNTRY` |
  | `RADARBOX_KEY` | clave de compartición si ya tienes una estación en RadarBox |
  | `AEMET_API_KEY` | opcional, gratis en https://opendata.aemet.es/centrodedescargas/altaUsuario |
  | `MESH868_PRIVATE_PSK` | clave AES-256 (base64) del canal privado del nodo Meshtastic 868 |
  | `HAMQTH_USER` / `HAMQTH_PASS` | cuenta gratuita HamQTH para la ficha de indicativos |

- Revisa también las series `SERIAL_*`, los pines `HAT_*`, `IO_MODE`, `CAM_SOURCE` y los interruptores `*_ENABLE`. El QR `MESH_CHANNEL_URL` y los marcadores son de la red de referencia: sustitúyelos por los de tu región/red.

## Alcance y compatibilidad
El instalador solo admite **Raspberry Pi OS arm64 Bookworm (Debian 12) o Trixie (Debian 13)** y está diseñado alrededor de Raspberry Pi 5. La receta completa espera el HAT HackerGadgets, SDR USB con sus series configuradas, FlightStick RadarBox, dispositivos LilyGO, Pico y periféricos descritos en los manuales. No está validado para Raspberry Pi anteriores, Docker ni otras distribuciones.

Los archivos `files/openwebrx/settings.json.tmpl`, `files/openwebrx/bookmarks.json`, branding y datos de radio incluyen decisiones/perfiles de EA5KAO y Murcia. Indicativo, QTH y país del receptor ya se toman de `bricohams.env`, pero debes revisar y reemplazar los marcadores, servicios regionales, imágenes y cualquier hotspot propio. `--solo` evita pasos seleccionados; no adapta el cableado ni la configuración de hardware. Si no tienes un periférico, desactiva su función en `bricohams.env` y comprueba sus dependencias antes de ejecutar la receta completa.

## 2. Lanzar el instalador

> **¿`sudo: ./install.sh: command not found`?** El kit se copió a la Pi por un camino que no guarda los permisos (Windows, un móvil, un pendrive FAT o un gestor de descargas). Al script le falta el permiso de ejecución y `sudo` responde «command not found» en vez de «permiso denegado». Lánzalo con `bash`, que no necesita ese permiso:
> ```bash
> cd ~/bricohams-sdr
> sudo bash install.sh --lista        # comprobar
> sudo bash install.sh --backup ~/backup-openwebrx-2026-10-03.tar.gz
> ```
> El instalador repara solo el resto de permisos y los finales de línea de Windows (CRLF). Si prefieres `./install.sh`, primero `chmod +x install.sh`. Lo mejor es clonar el git (`git clone …`), que mantiene los permisos.
> **Nombre del equipo:** `HOSTNAME_NEW=""` deja el nombre actual (`sdr`). Pon un nombre solo si quieres cambiarlo.

```bash
sudo bash install.sh                         # instalación nueva
sudo bash install.sh --backup copia.tar.gz   # solo para restaurar usuarios/marcadores existentes
```
- Tarda entre 30 y 60 minutos: compila readsb y, en Bookworm, también rtl-sdr-blog.
- **¿Ya tienes la estación instalada?** No hace falta reinstalar: `sudo bash install.sh --actualizar` ([manual 29](29_ACTUALIZAR.md)). La primera vez desde una versión anterior a la v4.1 aplica todos los pasos, sin perder usuarios, marcadores propios ni claves.
- **Te pedirá** la contraseña del admin de OpenWebRX (solo si no restauras `users.json` desde la copia).
- **Te avisará** de los pasos que quedan a mano: series, LilyGO y reinicio.

> **¿`Network is unreachable` con direcciones `2a00:…` y `no longer has a Release file` en el paso `base`?** La Pi tiene IPv6, pero tu router no lo deja salir a Internet. Desde la v3.2 el instalador lo detecta solo: fuerza IPv4 para apt y reintenta. Con una versión anterior, haz esto a mano y relanza:
> ```bash
> echo 'Acquire::ForceIPv4 "true";' | sudo tee /etc/apt/apt.conf.d/99bricohams-ipv4
> sudo bash install.sh
> ```

> **¿`bricohams.env: line 182: Ejemplo99: unbound variable`?** Una clave lleva un `$` entre comillas dobles (`QRZ_PASS="abc$Ejemplo99"`) y bash lo tomaba por una variable. **Desde la v4.2** el instalador LEE `bricohams.env` sin ejecutarlo: el `$` es literal y solo avisa. Aun así, lo más claro para claves con símbolos es usar **comillas simples**: `QRZ_PASS='abc$Ejemplo99'` (o escapar: `"abc\$Ejemplo99"`, que también vale).

> **¿`curl: (6) Could not resolve host: luarvique.github.io` / `gpg: no valid OpenPGP data found` en el paso `openwebrx`?** Pasaba justo después del paso `red`: al volver a lanzar el instalador, `red` **borraba y volvía a crear** la conexión WiFi por la que estaba conectada la Pi, que se quedaba sin red unos segundos. **Desde la v4.2:**
> - `red` modifica la conexión sin cortarla;
> - antes de cada paso el instalador espera a que haya DNS (hasta 2 min) y, si no llega, se para con el estado de la red;
> - las claves de los repositorios y los instaladores de terceros se bajan con reintentos y, si fallan, se para con un mensaje claro en vez de seguir a medias.
>
> Basta con volver a lanzar `sudo bash install.sh`: sigue donde se quedó.

> **¿`rtl-sdr : Depends: librtlsdr0 (= 0.7.0~rtlsdrblog1) but 2.0.2-2+b1 is to be installed`?** En la Pi quedó el driver rtl-sdr-blog de una instalación anterior, retenido, y en Trixie choca con el de Debian. La v3.3 lo arregla sola. A mano:
> ```bash
> sudo apt-mark unhold librtlsdr0 librtlsdr-dev rtl-sdr
> sudo apt-get install --allow-downgrades librtlsdr0 librtlsdr-dev rtl-sdr
> ```

Pasos (`sudo bash install.sh --lista`, 25 desde la v4.2):

| Paso | Qué hace |
|---|---|
| comprobar | Pi 5, arm64, **Trixie o Bookworm** (elige los repositorios de cada una), Internet y repositorio de OpenWebRX+, kit completo |
| base | paquetes, nombre de equipo, zona horaria, `/etc/bricohams/bricohams.env` |
| red | país de WiFi y las dos redes de casa en NetworkManager (5 GHz con prioridad 20, 2,4 GHz con 10) |
| arranque | `config.txt` (I2C, RTC, UART0, PPS, SPI1, cámara, USB y, con `FAN_ENABLE`, `pwm-2chan` + `w1-gpio`), consola serie fuera, TDT bloqueada |
| hat | RTC, gpsd, chrony con PPS, encendido de módulos |
| openwebrx | repositorio de OpenWebRX+, paquetes `openwebrx` y `soapysdr-module-sdrplay3` |
| rtlsdr | Bookworm: compila rtl-sdr-blog y lo fija con `apt-mark hold` · Trixie: usa el rtl-sdr 2.0.2 de Debian y quita el fork si quedó de antes |
| sdrplay | API de SDRplay (solo con `INSTALL_SDRPLAY_API=yes`) |
| configuracion | `settings.json` desde la plantilla, marcadores (fusionados con la copia), imágenes, usuarios |
| plugins | `init.js` y plugins web |
| meteo | `bricohams-meteo` cada 10 min |
| io | v4: Pico «bricohams-io» por USB (sensores y ventiladores; manual 20) |
| sensor | `bricohams-wx` (BME280 + viento RS485 + pluviómetro + WX APRS), regla udev `/dev/rs485` |
| camara | MediaMTX (cámara CSI o IP por RTSP) + foto cada 60 s |
| ventilacion | `bricohams-fan` (2 ventiladores PWM + DS18B20, manual 18) |
| adsb | readsb + tar1090 + rbfeeder + MLAT |
| meshtastic | meshtasticd en el HAT + canales del QR + posición fija |
| lilygo | herramienta `bricohams-lilygo` (incluye `wxstation`) y CLI de Meshtastic |
| satelites | v4: pases de satélites cada 15 min + SatDump (imágenes METEOR) |
| ft2 | v4: compila `decodium-rx` y añade el modo FT2 (experimental, 20–40 min) |
| web | v4: nginx + Let's Encrypt (v4.2: `SSL_MODO`, por defecto HTTPS solo en la administración), portal `/bricohams/`, privacidad, `bricohams-api` |
| visitas | v4: mosquitto + `bricohams-visitas` (GeoIP local, Telegram) |
| herramientas | `bricohams-check`, `bricohams-sdr-serials`, `owrx-clone`, copia diaria, kit en `/opt/bricohams/kit` |
| importar | v4.2: solo con `--importar perfil.owrx.tar.gz`: aplica un perfil de OpenWebRX+ con owrx-clone (manual 31) |
| tareas | v4: cuenta de servicio «bricohams», sudoers limitado y `/etc/cron.d/bricohams` (manual 25) |

Para repetir pasos sueltos: `sudo bash install.sh --solo hat,meshtastic`.

## 3. Después del instalador
```bash
sudo bricohams-sdr-serials --grabar      # manual 03
sudo bricohams-lilygo identificar        # manual 05
sudo reboot
sudo bricohams-lilygo meshtastic
sudo bricohams-lilygo igate
sudo bricohams-check
```
Al final `bricohams-check` debe decir **0 fallos**. Los avisos pueden ser normales (por ejemplo, el GPS sin posición en los primeros minutos).
