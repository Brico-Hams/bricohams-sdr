# Ayuda rápida · BricoHams SDR (v5.0 en desarrollo)

**Para seguir los procedimientos con imágenes y requisitos:** [guía visual de módulos](GUIA_VISUAL_MODULOS.md).

Todas las órdenes del kit en una página. El detalle de cada una está en su manual (`docs/manuales/NN_…`).

## Instalar, actualizar, clonar
| Quiero… | Orden | Manual |
|---|---|---|
| Instalar desde cero | `sudo bash install.sh` | 02 |
| Instalar y restaurar usuarios y marcadores de una copia | `sudo bash install.sh --backup copia.tar.gz` | 09 |
| Ver los pasos | `sudo bash install.sh --lista` | 02 |
| Repetir pasos sueltos | `sudo bash install.sh --solo web,plugins` | 02 |
| Ver qué haría una actualización | `sudo bash install.sh --actualizar --simular` | 29 |
| Actualizar (git + apt + pasos cambiados) | `sudo bash install.sh --actualizar` | 29 |
| Exportar mi OpenWebRX+ a un fichero | `sudo owrx-clone exportar --cifrar` (o `sudo bash install.sh --exportar`) | 31 |
| Ver qué lleva un perfil | `owrx-clone ver perfil.owrx.tar.gz` | 31 |
| Importar un perfil en otro equipo | `sudo owrx-clone importar perfil.owrx.tar.gz --simular` y luego `--todo` | 31 |
| Instalar BricoHams y aplicar un perfil | `sudo bash install.sh --importar perfil.owrx.tar.gz` | 31 |
| Deshacer la última importación | `sudo owrx-clone deshacer` | 31 |
| Compartir mi configuración sin claves | `sudo owrx-clone exportar --publico --niveles config,etc,web` | 31 |

## Comprobar y diagnosticar
| Quiero… | Orden |
|---|---|
| Revisar toda la estación | `sudo bricohams-check` |
| Revisar solo OpenWebRX+ | `sudo owrx-clone comprobar` |
| Ver servicios y direcciones | `bricohams-servicios` |
| Registro del instalador | `less /var/log/bricohams-install.log` |
| Registro de las tareas | `less /var/log/bricohams-tareas.log` |
| Registro de OpenWebRX+ | `journalctl -u openwebrx -n 100` |
| SDR conectados y series | `SoapySDRUtil --find` · `rtl_test -t` · `sudo bricohams-sdr-serials` |
| Sensores y ventiladores (Pico) | `sudo bricohams-io estado` · `sudo bricohams-fan --estado` |
| Pases de satélites | `cat /usr/lib/python3/dist-packages/htdocs/plugins/receiver/satelites/pases.json` |
| Visitas de hoy | `sudo -u openwebrx bricohams-visitas --resumen` |

## Web
| Qué | Dónde |
|---|---|
| Receptor público | `https://DOMINIO/` (también desde la LAN; sin puerto explícito) |
| Administración (siempre HTTPS) | `https://DOMINIO/settings` |
| Portal de servicios | `https://DOMINIO/bricohams/` |
| Cambiar el modo SSL | `SSL_MODO` (admin, todo o no) en `bricohams.env` + `sudo bash install.sh --solo web` (manual 23) |
| Filtro y DSP de audio | botones **FILTRO** y **DSP** de la barra superior (manual 30) |

El backend solo debe escuchar en loopback (`OWRX_SOLO_LOCAL="yes"` y
`BLINDAJE_8073="cerrado"`). No anuncies su puerto en Receiverbook ni abras una
redirección hacia él en el router. Para corregir una instalación nativa existente:
`sudo bash tools/cerrar-backend-publico.sh /ruta/bricohams.env https://DOMINIO/`.
El script exige backup verificado y deja una orden de restauración antes de cambiar
la configuración. Reinicia OpenWebRX+, por lo que interrumpe las sesiones activas.

En Receiverbook registra la URL HTTPS sin puerto. Las claves se configuran en
**Settings → General settings → Receiver keys**, una por línea; nunca en Git.
La validación usa un desafío `Authorization: ReceiverId` contra `/status.json`:
un HTTP 200 sin desafío no acredita por sí solo la verificación de propiedad.

## bricohams.env: claves con símbolos
- **Lo más claro:** comillas simples, `QRZ_PASS='abc$def!'`.
- **También valen:** las dobles con `\$` (`"abc\$def"`), y desde la v4.2 un `$` suelto entre dobles se toma literal (con aviso).
- **Comprobar el fichero:** `python3 files/bin/bricohams-env.py --comprobar bricohams.env`
- **Nunca se sube al git:** está en `.gitignore`.

## v4.3 · Zona por locator (manual 32)
```bash
bricohams-locator info [LOCATOR]          # aeropuertos, AEMET, puertos, FM y NAVTEX cercanos, con distancia
sudo bricohams-locator refrescar          # baja AEMET (AEMET_API_KEY) y las FM de la zona
sudo bricohams-locator marcadores --aplicar   # pone los [AUTO-LOCATOR] en OpenWebRX+ y lo reinicia
bricohams-locator meteo                   # METEO_STATIONS de la zona
bricohams-locator locator 42.22917 -8.70833 # IN52pf · bricohams-locator coordenadas IN52pf
sudo bash install.sh --solo configuracion,meteo   # tras cambiar STATION_LOCATOR o LOCATOR_*
```

## v4.3 · OpenWebRX+ en Docker (manual 33)
```bash
# bricohams.env: OWRX_BACKEND="docker" (OWRX_DOCKER_IMAGE, _RED, _PRIVILEGED…)
sudo bash install.sh --actualizar                             # tras cambiar OWRX_BACKEND: contenedor y pasos que escriben en él
sudo docker logs -f owrx-mbe                                  # registro
sudo docker exec -it owrx-mbe openwebrx admin adduser admin   # administrador
cd /opt/owrx-docker && sudo docker compose pull && sudo docker compose up -d   # imagen nueva
sudo owrx-clone --docker owrx-mbe exportar | importar | comprobar
```

## v4.4 · Seguridad (manual 34)
```bash
sudo bricohams-dispositivos              # v4.5 · qué hay enchufado, para qué es y qué falta («en camino»)
sudo bricohams-rak-aprs prueba            # v4.5 · RAK4631: firmware, radio, temperatura de la caja, GPS
sudo bricohams-rak-aprs grabar            # v4.5 · grabar el firmware del RAK por USB
sudo bricohams-lilygo firmware            # v4.5 · actualizar el Meshtastic del LilyGO (conserva la configuración)
bricohams-mesh-url ver "URL"              # v4.5 · canales y radio de una URL de Meshtastic (sin claves)
bricohams-banner ver                      # v4.5 · cómo se ve el banner SSH
sudo bricohams-blindaje auditar           # informe (no cambia nada, no enseña claves)
ssh-copy-id <usuario>@<IP-DE-LA-PI>  # desde tu PC: entrar con clave
sudo bricohams-blindaje aplicar           # cortafuegos, SSH, fail2ban, permisos… (con copia)
sudo bricohams-blindaje confirmar         # en 3 min; si no, el cortafuegos se quita solo
sudo bricohams-blindaje deshacer          # volver a como estaba
sudo fail2ban-client status sshd          # IPs bloqueadas por SSH
sudo fail2ban-client status bricohams-login # IPs bloqueadas por ataques al login web
```

## v5 · Seguridad web, ADS-B y avisos
```bash
# Ajustes → Seguridad (/settings/bricohams/seguridad): bloqueo por IP/país, cortafuegos/nginx, usuarios
sudo bricohams-bloqueo estado             # reglas nftables de bloqueo (IP/red y país)
sudo bricohams-bloqueo aplicar            # aplicar /etc/bricohams/bloqueo.json (nunca bloquea la LAN)
sudo bricohams-bloqueo geo-actualizar     # descargar zonas de país (ipdeny.com)
sudo bricohams-bloqueo desbanear         # quitar los baneos marcados en el panel
sudo bricohams-bloqueo quitar             # borrar la tabla de bloqueo
# Aviso de inicio de sesión por Telegram: TG_AVISO_LOGIN="yes" en bricohams.env (1 aviso/IP cada 10 min)
curl -s 'http://127.0.0.1:8075/bricohams/api/avion?hex=3c6444'   # ficha de avión (adsbdb + planespotters)
grep -- --device /etc/default/readsb      # dongle ADS-B; sin aviones → mira el número de serie (manual 04)
grep -o 'net-connector=[^ "]*map.flights[^,]*' /etc/default/readsb   # map.flights activo (MAPFLIGHTS_FEED, manual 04)
systemctl status bricohams-mapflights-mlat --no-pager                # MLAT de map.flights (RadarBox va aparte)
journalctl -u rbfeeder -n 20 --no-pager            # paquetes enviados a RadarBox
sudo ss -tinp dst feed.map.flights                # conexion y bytes hacia map.flights
```

## v5 · Meteorología y mantenimiento

Limpieza local automática: diariamente a las **06:15**, copias de configuración y perfiles de más de cinco días.
No toca remotos ni carpetas de despliegues ([manual 09](manuales/09_MANTENIMIENTO.md#limpieza-automática-de-copias-locales)).
```bash
sudo bricohams-backup-limpieza --dry-run
systemctl list-timers bricohams-backup-limpieza.timer --all
journalctl -u bricohams-backup-limpieza.service --no-pager
```

| Quiero… | Orden o ajuste | Manual |
|---|---|---|
| Elegir el sensor meteorológico | `WX_FUENTE=auto` prioriza el RAK y usa Pico/I2C de respaldo; también admite `rak`, `pico` e `i2c` | [06](manuales/06_SENSOR_WX.md) |
| Usar el GPS del RAK para APRS WX | `WX_POS_GPS=auto`; sin fix usa `STATION_LAT/LON` | [06](manuales/06_SENSOR_WX.md) |
| Diagnosticar el sensor | `journalctl -u bricohams-wx -n 50 --no-pager` | [06](manuales/06_SENSOR_WX.md) |
| Diagnosticar la meteo pública | `journalctl -u bricohams-meteo -n 50 --no-pager`; los errores internos no se publican en `meteo.json` | [06](manuales/06_SENSOR_WX.md) |
| Ver la última actividad del moderador | `sudo -u openwebrx bricohams-visitas --moderador` | [24](manuales/24_VISITAS_TELEGRAM.md) |
| Configurar una copia remota | `/settings` → Seguridad → Copia remota | [09](manuales/09_MANTENIMIENTO.md#copia-remota-v50) |
| Consultar la copia remota | `sudo bricohams-backup-remoto estado` | [09](manuales/09_MANTENIMIENTO.md#copia-remota-v50) |
| Comprobar la rotación sin modificar registros | `sudo logrotate --debug /etc/logrotate.conf` | [04](manuales/04_ADSB.md) |

## Errores conocidos y arreglo
| Mensaje | Arreglo |
|---|---|
| `sudo: ./install.sh: command not found` | `sudo bash install.sh` |
| `…bricohams.env: line N: X: unbound variable` | resuelto en v4.2 (clave con `$`); usa comillas simples |
| `Could not resolve host: luarvique.github.io` | resuelto en v4.2 (el paso `red` cortaba la WiFi); relanza el instalador |
| `Network is unreachable` con `2a00:…` | IPv6 sin salida: lo arregla el instalador (v3.2) |
| `rtl-sdr : Depends: librtlsdr0 (= 0.7.0~rtlsdrblog1)` | resuelto en v3.3 |
| `nginx no acepta la configuración` | mira el mensaje de `nginx -t` encima; `sudo nginx -t` |
| `git pull no puede avanzar el kit` | `git stash`, actualiza y `git stash pop` (manual 29) |
| No entro por SSH tras `bricohams-blindaje aplicar` | espera 3 min (vuelta atrás) o en la Pi: `sudo bricohams-blindaje deshacer` |
| `STATION_LOCATOR=… no es un locator Maidenhead válido` | 4, 6, 8 o 10 caracteres: `IN52pf` (manual 32) |
| `Sin datos de zona en línea (AEMET/FM)` | sin red o sin `AEMET_API_KEY`: sigue con el catálogo del kit; luego `sudo bricohams-locator refrescar` |
| `Falta el volumen Docker persistente …` | el contenedor no monta etc/var/plugins: deja que lo cree el kit (`OWRX_DOCKER_DESPLEGAR="yes"`, manual 33) |
| lgpio: `can not open … .lgd-nfy` | la unidad WX necesita `WorkingDirectory=/var/lib/bricohams`; ver manual 06 |
| logrotate: no existe `/var/log/mlat-client.log` | el paso `adsb` añade `missingok` y `notifempty` a la regla del paquete; ver manual 04 |

## Ayuda integrada
```bash
sudo bash install.sh --help
owrx-clone --help ; owrx-clone ayuda {niveles,seguridad,dispositivos,migrar,docker,problemas} ; man owrx-clone
bricohams-locator --help ; python3 files/bin/bricohams-docker-compose.py --help
bricohams-io --help ; bricohams-fan --help ; bricohams-ft2 ; sudo bricohams-tarea
python3 files/bin/bricohams-env.py
```
