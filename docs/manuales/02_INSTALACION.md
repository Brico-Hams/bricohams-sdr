# 02 · Instalación

## 1. Rellenar `bricohams.env`
- **Claves obligatorias:**

  | Variable | Qué es |
  |---|---|
  | `APRS_PASSCODE` | código de APRS-IS de EA5KAO |
  | `MAGIC_KEY` | clave mágica de OpenWebRX |
  | `RECEIVERBOOK_KEY` | clave de receiverbook |
  | `OPENWEATHERMAP_KEY` | clave de OpenWeatherMap |

- **Recomendadas:**

  | Variable | Qué es |
  |---|---|
  | `AEMET_API_KEY` | clave de AEMET, gratis en https://opendata.aemet.es/centrodedescargas/altaUsuario |
  | `WIFI_SSID_1` / `WIFI_SSID_2` / `WIFI_PASS` | WiFi de casa para la Pi: `BiohazardIT-5G` (preferida) y `biohazard-it` |
  | `LILYGO_WIFI_SSID` / `LILYGO_WIFI_PASS` | WiFi para el iGate: `biohazard-it` (el ESP32 solo ve 2,4 GHz) |
  | `RADARBOX_KEY` | clave de compartición si ya tienes una estación en RadarBox |
  | `MESH868_PRIVATE_PSK` | clave AES-256 (base64) del canal privado del nodo Meshtastic 868 |

- **Revisa también:** las coordenadas (`STATION_*`), las series de los SDR, las variables `HAT_*` (A VERIFICAR) y `MESH_CHANNEL_URL` (ya trae los canales de la red).

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
sudo bash install.sh --backup ~/backup-openwebrx-2026-10-03.tar.gz   # o sin --backup en una instalación nueva
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

> **¿`rtl-sdr : Depends: librtlsdr0 (= 0.7.0~rtlsdrblog1) but 2.0.2-2+b1 is to be installed`?** En la Pi quedó el driver rtl-sdr-blog de una instalación anterior, retenido, y en Trixie choca con el de Debian. La v3.3 lo arregla sola. A mano:
> ```bash
> sudo apt-mark unhold librtlsdr0 librtlsdr-dev rtl-sdr
> sudo apt-get install --allow-downgrades librtlsdr0 librtlsdr-dev rtl-sdr
> ```

Pasos (`sudo bash install.sh --lista`, 24 en v4.0):

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
| web | v4: nginx + SSL (Let's Encrypt), portal `/bricohams/`, privacidad, `bricohams-api` |
| visitas | v4: mosquitto + `bricohams-visitas` (GeoIP local, Telegram) |
| herramientas | `bricohams-check`, `bricohams-sdr-serials`, copia diaria, kit en `/opt/bricohams/kit` |
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
