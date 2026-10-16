# 09 · Mantenimiento, copias y restauración

<!-- guia-visual:inicio -->
> **Ruta visual:** [Tareas, backups, limpieza, actualización y clonado](../GUIA_VISUAL_MODULOS.md#mantenimiento).
> Consulta allí requisitos, ilustración, cuadro de instalación, comprobaciones y restauración.
> Los comandos de este manual se ejecutan en Bash en la Pi; revisa el backup antes de cambiarla.
<!-- guia-visual:fin -->

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
- **Copia diaria:** `/var/backups/bricohams/backup-openwebrx-AAAA-MM-DD.tar.gz` a las 04:30. Las copias locales de más de cinco días se eliminan automáticamente (apartado siguiente). Para hacer una al momento: `sudo /usr/local/sbin/bricohams-backup`.
- **Qué incluye:**
  - settings, usuarios, marcadores e imágenes de OpenWebRX.
  - plugins.
  - `/etc/bricohams`.
  - meshtasticd, mediamtx, gpsd y chrony.
  - `config.txt`.
  - readsb y rbfeeder.
  - regla udev de los LilyGO.
  - histórico del sensor.
- **v4.2 · Perfil de OpenWebRX+:** la copia diaria guarda además `/var/backups/bricohams/perfil-owrx-AAAA-MM-DD.owrx.tar.gz` (misma retención de cinco días), hecho con **owrx-clone**. Sirve para llevar el OpenWebRX+ tal cual a otro equipo: `sudo owrx-clone importar …` ([manual 31](31_CLONAR_OPENWEBRX.md)). Uno al momento: `sudo owrx-clone exportar --cifrar`.
- **Fuera de la Pi:** copia esas copias a otro sitio (NAS o el git interno, **sin** `bricohams.env`). Los perfiles llevan las contraseñas de administración: guárdalos cifrados. Desde v5.0 se puede hacer automáticamente (siguiente apartado).

## Limpieza automática de copias locales

`bricohams-backup-limpieza.timer` ejecuta cada día a las **06:15**, hora local de la Pi, el servicio
`bricohams-backup-limpieza.service`. Se instala con `sudo bash install.sh --solo herramientas`.
`Persistent=true` recupera una ejecución pendiente después de apagar el equipo.

- Borra solo archivos normales `backup-openwebrx-AAAA-MM-DD.tar.gz` y
  `perfil-owrx-AAAA-MM-DD.owrx.tar.gz` directamente en `/var/backups/bricohams`.
- La antigüedad se mide por la última modificación: **más de 120 horas**; exactamente cinco días todavía se conserva.
  La revisión es diaria, por lo que una copia puede permanecer hasta la siguiente ejecución tras vencer el plazo.
- No sigue enlaces ni recorre subdirectorios. No toca copias remotas, archivos ajenos, copias manuales en otras rutas
  ni carpetas de restauración de despliegues (como `mapflights-*`).
- Sustituye la retención local anterior por número de copias (14 de configuración y 7 perfiles).
  La retención remota sigue configurándose en el panel.
- No garantiza conservar una copia si todas tienen más de cinco días. Guarda fuera de la Pi las que quieras mantener.
- Los errores se registran en el journal y hacen fallar el servicio; un cerrojo evita dos limpiezas simultáneas.

```bash
sudo bricohams-backup-limpieza --dry-run  # listar sin borrar
systemctl list-timers bricohams-backup-limpieza.timer --all
sudo systemctl start bricohams-backup-limpieza.service  # limpiar ahora
journalctl -u bricohams-backup-limpieza.service --no-pager
sudo systemctl disable --now bricohams-backup-limpieza.timer  # desactivar
```

Antes de desplegar la tarea, guarda y verifica el estado previo de los scripts y unidades afectados.
Antes de la primera limpieza, revisa `--dry-run` y guarda fuera del alcance de la tarea cualquier copia que necesites conservar.
El borrado no tiene papelera; desactivar el temporizador no recupera archivos eliminados.

## Copia remota (v5.0)
En `/settings` → **Seguridad** → *Copia remota* (solo administradores) se configura un destino fuera de la Pi.

| Protocolo | Destino (ejemplo) | Credenciales |
|---|---|---|
| SMB/CIFS | `\\192.168.1.10\recurso\carpeta` | usuario (o `DOMINIO\usuario`), contraseña y versión SMB |
| NFS | `192.168.1.10:/exportado/carpeta` | ninguna: se controla en el servidor por IP |
| SFTP | servidor, puerto y carpeta | usuario y contraseña. Antes hay que confirmar la huella del servidor |
| Google Drive | carpeta | token de `rclone authorize "drive"` |
| OneDrive | carpeta | token de `rclone authorize "onedrive"` y `drive_id` |

- **Secretos:**
  - La contraseña o el token se guardan en `/etc/bricohams/backup-remoto.secret` (root, 600) y el resto de la configuración en `/etc/bricohams/backup-remoto.json`.
  - El formulario no vuelve a mostrar los secretos; si dejas el campo en blanco, se conserva el que había.
- **Borrar configuración y credenciales** elimina las dos cosas.
- **Token de Google Drive y OneDrive:**
  - En un PC con navegador, ejecuta `rclone authorize "drive"` (o `"onedrive"`) y pega en el formulario el JSON que devuelve.
  - Para OneDrive, el `drive_id` se ve con `rclone config` en ese mismo PC.
  - rclone renueva el token por su cuenta.
- **Huella SFTP:**
  1. Pulsa **Obtener huella SFTP**.
  2. Compárala con la del servidor (`ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub`).
  3. Pulsa **Confirmar huella**.
  - Sin confirmar no se conecta. Si cambias el servidor o el puerto, la huella se borra.
  - Los servidores que solo admiten SCP no sirven.
- **Órdenes:**
  - **Probar conexión**: escribe y borra un fichero de prueba.
  - **Copiar ahora**.
  - **Verificar última copia**: recalcula el SHA256 de la última copia remota.
  - Se ejecutan en segundo plano y nunca dos a la vez. El resultado aparece en la página al recargar.
- **Qué sube:**
  - `bricohams-backup-AAAAMMDD-HHMMSS.tar.gz` y su `.sha256`, hechos a partir de `bricohams-backup`.
  - Por defecto **sin** `bricohams.env`, sin `backup-remoto.*` y sin `tak-access.txt`. Solo los incluye si marcas *Incluir secretos*, y entonces el destino debe ser de confianza y estar cifrado.
  - Se conservan las N últimas (*Copias a conservar*, por defecto 14).
- **Programada:** marca *Copia diaria automática* para activar `bricohams-backup-remoto.timer` (05:15, después de la copia local de las 04:30).
- **Registro:** `journalctl -u 'bricohams-backup-remoto@*'`. Estado: `sudo bricohams-backup-remoto estado`.
- **Restaurar desde el remoto:**
  1. Descarga el `.tar.gz` y su `.sha256`.
  2. Comprueba la copia con `sha256sum -c fichero.sha256`.
  3. `sudo bash install.sh --backup /ruta/fichero.tar.gz` (apartado siguiente). Si la copia no llevaba secretos, copia antes tu `bricohams.env`.

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
