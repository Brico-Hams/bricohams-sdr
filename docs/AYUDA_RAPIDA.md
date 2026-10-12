# Ayuda rápida · BricoHams SDR (v4.2)

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
| v5.1 · RAK de una vez (grabar si hace falta, prueba, bootloader, GPS) | `sudo bricohams-rak-aprs puesta-en-marcha` |
| v5.1 · Versión del bootloader del RAK | `sudo bricohams-rak-aprs bootloader` |
| v5.1 · ¿Tiene fix el GPS en la caja? | `sudo bricohams-rak-aprs gps 15` |
| v5.1 · Puente del LilyGO 433 (web Meshtastic) | `bricohams-mesh-puente estado` |
| v5.1 · ¿Por qué no sincroniza con GitHub? (en el PC) | `bash tools/git_sanear.sh` · `--reparar` |
| v5.1 · ¿Hay datos personales o claves en lo que subo? | `python3 tools/datos_personales.py` · `--historial` |

## Web
| Qué | Dónde |
|---|---|
| Receptor público | `http://DOMINIO/` (o `http://IP:8073/` en casa) |
| Administración (siempre HTTPS) | `https://DOMINIO/settings` |
| v5.1 · Panel APRS: mensajes, baliza, digipeater (admin) | `https://DOMINIO/settings/bricohams/aprs` |
| v5.1 · Cliente web de Meshtastic del LilyGO 433 (admin, solo LAN) | `https://IP:8444/` (botón «Meshtastic Web (433)» en Ajustes) |
| Portal de servicios | `http://DOMINIO/bricohams/` |
| Cambiar el modo SSL | `SSL_MODO` (admin, todo o no) en `bricohams.env` + `sudo bash install.sh --solo web` (manual 23) |
| Filtro y DSP de audio | botones **FILTRO** y **DSP** de la barra superior (manual 30) |

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
bricohams-locator locator 38.08 -1.26 # IM97kx · bricohams-locator coordenadas IM97kx
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
ssh-copy-id <usuario>@192.168.1.50          # desde tu PC: entrar con clave
sudo bricohams-blindaje aplicar           # cortafuegos, SSH, fail2ban, permisos… (con copia)
sudo bricohams-blindaje confirmar         # en 3 min; si no, el cortafuegos se quita solo
sudo bricohams-blindaje deshacer          # volver a como estaba
sudo fail2ban-client status sshd          # IPs bloqueadas
```

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
| `STATION_LOCATOR=… no es un locator Maidenhead válido` | 4, 6, 8 o 10 caracteres: `IM97kx` (manual 32) |
| `Sin datos de zona en línea (AEMET/FM)` | sin red o sin `AEMET_API_KEY`: sigue con el catálogo del kit; luego `sudo bricohams-locator refrescar` |
| `Falta el volumen Docker persistente …` | el contenedor no monta etc/var/plugins: deja que lo cree el kit (`OWRX_DOCKER_DESPLEGAR="yes"`, manual 33) |

## Ayuda integrada
```bash
sudo bash install.sh --help
owrx-clone --help ; owrx-clone ayuda {niveles,seguridad,dispositivos,migrar,docker,problemas} ; man owrx-clone
bricohams-locator --help ; python3 files/bin/bricohams-docker-compose.py --help
bricohams-io --help ; bricohams-fan --help ; bricohams-ft2 ; sudo bricohams-tarea
python3 files/bin/bricohams-env.py
```
