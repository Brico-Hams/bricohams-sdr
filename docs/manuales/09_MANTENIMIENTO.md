# 09 · Mantenimiento, copias y restauración

## Comprobación general
`sudo bricohams-check` revisa todo de un vistazo:
- Sistema y alimentación.
- OpenWebRX y los cuatro RTL-SDR.
- SDRplay.
- HAT: RTC, GPS, PPS, hora y SPI.
- ADS-B, Meshtastic, LilyGO, sensor, cámara, meteo y plugins.

## Tareas automáticas (v4)
Las copias, las actualizaciones semanales, el reinicio preventivo, la comprobación de salud con aviso por Telegram y el resumen de visitas los lanza el cron de la cuenta de servicio `bricohams` ([manual 25](25_TAREAS_AUTOMATICAS.md)). Registro: `/var/log/bricohams-tareas.log`. Direcciones y estado de cada servicio: `bricohams-servicios`.

## Copias
- **Copia diaria:** `/var/backups/bricohams/backup-openwebrx-AAAA-MM-DD.tar.gz` a las 04:30 (se guardan las 14 últimas). Para hacer una al momento: `sudo /usr/local/sbin/bricohams-backup`.
- **Qué incluye:**
  - settings, usuarios, marcadores e imágenes de OpenWebRX.
  - plugins.
  - `/etc/bricohams`.
  - meshtasticd, mediamtx, gpsd y chrony.
  - `config.txt`.
  - readsb y rbfeeder.
  - regla udev de los LilyGO.
  - histórico del sensor.
- **v4.2 · Perfil de OpenWebRX+:** la copia diaria guarda además `/var/backups/bricohams/perfil-owrx-AAAA-MM-DD.owrx.tar.gz` (los 7 últimos), hecho con **owrx-clone**. Sirve para llevar el OpenWebRX+ tal cual a otro equipo: `sudo owrx-clone importar …` ([manual 31](31_CLONAR_OPENWEBRX.md)). Uno al momento: `sudo owrx-clone exportar --cifrar`.
- **Fuera de la Pi:** copia esas copias a otro sitio (NAS o el git interno, **sin** `bricohams.env`). Los perfiles llevan las contraseñas de administración: guárdalos cifrados.

## Restaurar tras un fallo de tarjeta
1. Graba una tarjeta nueva ([manual 01](01_PREPARACION.md)).
2. `git clone` del repositorio y copia tu `bricohams.env` (guárdalo aparte, por ejemplo en un gestor de contraseñas).
3. `sudo bash install.sh --backup /ruta/backup-openwebrx-AAAA-MM-DD.tar.gz`
4. **No** hace falta volver a grabar las series de los SDR ni a identificar los LilyGO si son los mismos: las series están en su EEPROM. La regla udev de los LilyGO sí hay que volver a crearla, salvo que la restaures desde la copia.

## Actualizar
- **Todo de una vez (v4.1, recomendado):** `sudo bash install.sh --actualizar`. Baja el kit con git, añade las variables nuevas a `bricohams.env`, hace copia, actualiza paquetes y repite **solo** los pasos que han cambiado. Antes, para ver qué hará: `--actualizar --simular`. Detalle en el [manual 29](29_ACTUALIZAR.md).
- **Solo sistema y OpenWebRX:** `sudo apt update && sudo apt full-upgrade` (o la tarea semanal del cron). En Bookworm, el driver rtl-sdr-blog está fijado con `apt-mark hold`. En Trixie se usa el rtl-sdr de Debian y se actualiza con el sistema.
- **Un paso concreto:** `sudo bash install.sh --solo plugins,configuracion`.
- **Meshtastic del HAT:** se actualiza con apt.
- **LilyGO:** Meshtastic desde flasher.meshtastic.org. El iGate con `sudo bricohams-lilygo igate`, que vuelve a clonar y grabar.

## Problemas frecuentes

| Síntoma | Mirar |
|---|---|
| Un receptor de OpenWebRX no arranca | `rtl_test -t`, series ([manual 03](03_SDR_Y_SERIES.md)), `journalctl -u openwebrx` |
| `get_throttled` distinto de 0x0 | fuente o hub: los SDR se reinician por falta de corriente |
| RTC no aparece en 0x51 | pines del HAT, `dtoverlay=i2c-rtc,pcf85063a` |
| GPS sin datos | `HAT_GPS_DEV`, `HAT_GPS_BAUD`, consola serie desactivada, `gpsmon` |
| meshtasticd «radio init failed» | `HAT_LORA_*` en bricohams.env → `sudo bash install.sh --solo arranque,meshtastic` y reiniciar |
| Sin foto de la cámara | `journalctl -u mediamtx -u bricohams-camsnap`, cable CSI |
| Sin datos de AEMET | `AEMET_API_KEY`, `journalctl -u bricohams-meteo` |
| Ventilador parado (⚠ en la web) | `sudo bricohams-fan --estado`, cable TACH y pull-up ([manual 18](18_VENTILACION.md)) |
| Sin viento en el WX | `ls -l /dev/rs485`, `sudo bricohams-wx --rs485-buscar` ([manual 19](19_VIENTO_Y_LLUVIA.md)) |
| Lluvia que sube sin llover | pluviómetro en el mástil (vibra) o falta el condensador de 100 nF |
| Cámara IP sin imagen | `CAM_RTSP_URL` en bricohams.env, `journalctl -u mediamtx`, ping a la cámara |

## Mantenimiento periódico (v3)

| Cada | Qué |
|---|---|
| 3 meses | limpiar las mallas inox de las capotas y el filtro del embudo del pluviómetro; mirar que no haya avispas en las capotas |
| 6 meses | revisar el apriete de las U del mástil, la tensión de los **vientos** (tensores) y los tapones de las varillas de las discones |
| 6 meses | NanoVNA a la quad y a las discones desde la caja: un cambio brusco de ROE indica agua en un conector |
| Antes del verano | `sudo bricohams-fan --estado` con sol: la caja no debe pasar de 50 °C. Si pasa, sube `FAN_DUTY_MIN` o baja `FAN_T_CAJA_MIN` |
| Después de un temporal | antenas alineadas (quad a 205°), veleta con la marca al norte, cables y bucles de goteo |
| 1 año | cambiar la cinta autovulcanizante de los conectores N a la intemperie y las fundas TPU del MLA-30 si están cuarteadas |
