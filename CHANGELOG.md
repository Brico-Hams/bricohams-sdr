# Historial

## v5.0 · en desarrollo
**Repositorio genérico (sin datos personales), botones TAK/Monitorización y gestión de bookmarks desde /settings.**

**Usuarios y claves TAK** (manual 36)
- `tools/instalar_tak.sh` rechaza nombres de usuario TAK con guion: OpenTAKServer solo acepta letras, números, `_` y `.`; con guion el login devuelve 400 aunque la clave sea correcta.
- Los usuarios se crean con `confirmed_at` y `active=True`. «Cambiar clave» en `/settings` también los fija.
- Manual 36: procedimiento de reset completo de claves y migración de cuentas con guion.

**Importar / exportar bookmarks** (manual 32 §8)
- `files/bin/bricohams-owrx-bookmarks-io`: añade a `/settings/bookmarks` tres botones.
  - **Importar desde fichero…**: lee un `.json` local en el navegador y da de alta los bookmarks uno a uno con el propio formulario de OpenWebRX+.
  - **Exportar todos** y **Exportar editables**: bajan un `.json` con todos los bookmarks o solo los tuyos.
- La página solo existe con sesión de administrador; la web pública no cambia (regla del proyecto).
- El controlador incrusta la lista completa como JSON escapado (`<`, `>` y `&`), así un nombre de bookmark no puede romper la página.
- El parche es idempotente, escribe de forma atómica, compila el `.py` antes de escribirlo y se deshace con `--quitar`.
- Se reaplica tras cada `apt` con `/etc/apt/apt.conf.d/99bricohams-owrx-bookmarks-io`.
- Prueba: `tests/test_bookmarks_io.py`.

**Clave de la API de RepeaterBook en Ajustes generales** (manual 32 §9)
- `files/bin/bricohams-owrx-repeaterbook`: activa en `/settings/general` la sección «RepeaterBook» con un campo de contraseña `repeaterbook_api_key`, colocada antes de «Map settings».
  - OpenWebRX+ ya guarda y usa esa clave, pero el campo venía comentado.
  - Solo se ve con sesión de administrador; la clave no se publica.
- Si una versión futura de OpenWebRX+ trae el campo activo, el parche no lo duplica.
- El parche es idempotente y reversible (`--quitar`), con líneas marcadas `#@BH-RB@`.
- Se reaplica tras cada `apt` con `/etc/apt/apt.conf.d/99bricohams-owrx-repeaterbook`.
- Hace falta rellenar «Receiver admin», el e-mail de contacto que RepeaterBook exige en el User-Agent.
  - Los tokens `rbuapp_` están ligados a una aplicación aprobada: si su patrón de User-Agent no coincide, la API devuelve `403 ua_mismatch`.
- Prueba: `tests/test_repeaterbook.py`.

**Subtono CTCSS en los bookmarks** (manual 32 §10)
- `files/bin/bricohams-owrx-ctcss` + `files/share/bricohams-ctcss/` (`bricohams_ctcss.py`, `bricohams-ctcss.js`).
  - Añade el campo opcional `ctcss` (Hz) al bookmark.
  - Añade la columna «Subtono FM» en `/settings/bookmarks`, con los 50 tonos EIA y validación de 60–260 Hz.
  - Añade un silenciador por subtono en la cadena FM (`CtcssSquelch`, entre la de-énfasis y el AGC).
- El silenciador abre solo si el tono pedido es claramente el más fuerte de los 50 EIA, para no abrir con un repetidor vecino. Lleva paso-alto de 300 Hz y rampas para evitar chasquidos.
- En la web pública se activa al sintonizar un bookmark con tono. El selector «Subtono FM» del panel afecta solo a la sesión del navegador; no hay ningún ajuste persistente fuera de `/settings`.
- La etiqueta es siempre **FM**, nunca «NFM».
- `install.sh` instala `python3-numpy` y `python3-scipy`. Antes no lo hacía, y el silenciador quedaba inactivo en silencio.
- El parche es idempotente y reversible (`--quitar`), con líneas marcadas `#@BH-CTCSS@`, y tiene hook de `apt`.
- Prueba: `tests/test_ctcss_patch.py`.

**Importar repetidores de RepeaterBook** (manual 32 §11)
- `files/bin/bricohams-owrx-rbimport` + `files/share/bricohams-rbimport/bricohams_rbimport.py`.
  - Añade a `/settings/bookmarks` el botón «Importar repetidores (RepeaterBook)…».
  - Filtros: país, distrito (EA1–EA9 en España), bandas, texto y «solo activos».
  - Vista previa con selección antes de crear nada.
- Solo se proponen repetidores FM analógicos.
- Se guarda únicamente la frecuencia de **salida**, porque el SDR solo recibe. El subtono se toma de TSQ o, si no hay, de PL, y la entrada y el desplazamiento van en la descripción.
- No se pisan bookmarks existentes en la misma frecuencia.
- Acción «Asignar subtonos» (`POST /settings/bookmarks/repeaterbook/tonos`): pone el tono a bookmarks FM existentes. Desempata por el indicativo del nombre y no sobrescribe salvo que se pida.
- La descarga se cachea 6 h para respetar el límite de peticiones de RepeaterBook.
- Corrección: si la plantilla `bookmarks.html` no trae el ancla esperada, el bloque se inserta antes de `</body>` en lugar de fallar.
- Prueba: `tests/test_rbimport.py`.
- Prueba de concepto en el servidor de referencia: importado el distrito 5 en 2 m y 70 cm, con los subtonos asignados.

**Paneles TAK y Monitorización + Grafana** (manual 36)
- Accesos en `/settings/bricohams/tak` y `/settings/bricohams/monitorizacion`, siempre con sesión de administrador.
- Grafana se sirve detrás de `/settings/bricohams/grafana/`.
  - Contraseña inicial de `admin` en `GRAFANA_ADMIN_PASS` (`.env`); cámbiala en el primer acceso.
- Pasos `paso_tak` y `paso_monitorizacion` en `install.sh`, con las variables `TAK`, `MONITORIZACION` y `GRAFANA_ADMIN_PASS` en `.env.example`.

**Sincronización del repositorio personal con v5.0**
- Este repositorio (estación EA5KAO) se ha igualado con el genérico v5.0 manteniendo los datos de la estación. Copia previa: `bricohams-sdr-v4.5-backup.tgz` en la carpeta superior.
- Documentación nueva: `docs/COMPONENTES.md` (ficha por componente) y sección «Estructura» del README enlazada con `docs/ESTRUCTURA_FICHEROS.md`.

**Monitorización automatizada y adopción de instalaciones manuales** (manual 36, ADR-64)
- `paso_monitorizacion` instala Prometheus, node-exporter y Grafana si faltan y, si ya existen instalados a mano (`/usr/local/bin` + unidades propias), los **adopta** sin reinstalar.
- Drop-ins `*.service.d/bricohams.conf` fuerzan `127.0.0.1:9090` y `127.0.0.1:9100`; `openwebrx_exporter` (si existe) queda limitado a localhost con `IPAddressDeny`.
- `prometheus.yml` se regenera conservando los trabajos ajenos; `prometheus.yml` y `grafana.ini` previos se guardan una vez como `*.bak-manual`.
- Clave de `admin`: `GRAFANA_ADMIN_PASS` > `/etc/bricohams/grafana-access.txt` > aleatoria; se aplica con `grafana cli admin reset-admin-password` (`grafana.ini` repite `[paths]` para que la CLI use la misma base de datos).
- nginx: `/settings/bricohams/grafana/` pasa por `auth_request` antes de llegar a `127.0.0.1:3000`; con `MONITORIZACION=no` el bloque `#@GF@` queda comentado.
- Prueba: `tests/test_monitorizacion.py`.
- `tests/test_ssl_admin.py` remapea también `listen 8443` (cliente web Meshtastic) a un puerto libre: la prueba fallaba en una Pi con ese puerto ya ocupado.

**Credenciales del servidor TAK desde /settings** (manual 36, ADR-63)
- Las claves TAK no tienen valor por defecto: `instalar_tak.sh` las genera aleatorias y solo viven en `/etc/bricohams/tak-access.txt` (root, 600). Antes no había forma documentada de verlas ni de cambiarlas sin terminal.
- Nueva tarjeta **Credenciales TAK** en `/settings/bricohams/tak`:
  - muestra usuarios y rol con la clave enmascarada;
  - **Mostrar credenciales** (POST + CSRF, `no-store`) las enseña en claro;
  - **Cambiar clave**: manual (12–128 ASCII visibles) o aleatoria; lista blanca de usuarios del fichero; la clave va por stdin a OpenTAKServer (`runuser -u opentakserver`), nunca en argv ni en el log; el fichero se reescribe atómico solo si OpenTAKServer confirma.
- Unidad `bricohams-mesh-admin`: `ReadWritePaths=-/var/lib/bricohams-tak`. Sin ello `ProtectSystem=strict` impedía a OpenTAKServer escribir su log y el cambio fallaba (comprobado en la Pi con `systemd-run`).
- `instalar_tak.sh` reinicia `bricohams-mesh-admin` al terminar y su mensaje final indica dónde ver las credenciales.
- Pruebas en `tests/test_mesh_admin.py`.

**Pruebas y calidad**
- `tests/run_tests.sh` incluye las pruebas de BMIO, RepeaterBook, CTCSS y RBI.
- `tests/test_ft2.py` compara el indicativo con una expresión regular en lugar de uno fijo.
  - El WAV de ejemplo (`tests/datos/ft2_*.wav`) es una captura real del aire y en el audio contiene el indicativo del operador que la grabó.
- `tools/instalar_tak.sh` queda limpio en shellcheck (directiva SC1090 documentada).
- Suite completa ejecutada en una Raspberry Pi real: todo OK. Solo se omite `test_audio_navegador`, porque requiere Playwright.

**Firmware**
- iGate LoRa APRS: compiladas de nuevo las **55/55** placas, con todos los SHA256 coincidentes (`docs/manuales/` de compilación y `SHA256SUMS`).
- Meshtastic v2.7.26: compilación de todos los entornos con `build_all.py`; el resultado está en `build_report.json`.

## v4.6 · 11/10/2026
**Servidor TAK local, chat APRS en el CHAT común y mapa en vivo con aviones ADS-B y trazas APRS.** Todo lo de la v4.5 se mantiene. RadarBox y MLAT no se tocan. Justificación completa en el manual 37; manejo en el manual 36.

**TAK local** (manual 36, ADR-54)
- `tools/instalar_tak.sh`: OpenTAKServer 1.7.13 con la UI 1.7.5 (sha256 comprobado).
  - Python 3.12.15 aislado con uv en `/opt/bricohams-tak`. El Python 3.13 del sistema no se toca: el gevent de OTS falla al hacer fork con 3.13.
  - Puertos solo LAN: 8445 (UI), 8089 (CoT mTLS), 8446 (enrollment) y 8447 (Marti mTLS). 8443 sigue siendo de Meshtastic.
  - `bricohams-tak-fw` cierra 4369, 5672, 15672, 25672, 5432 y 8081 desde fuera.
  - Credenciales en `/etc/bricohams/tak-access.txt` (600).
- Capa TAK en el mapa, **solo para el admin y por HTTPS**: `/settings/bricohams/tak/posiciones` (ADR-56).

**Chat APRS** (ADR-57)
- `bricohams-rak-aprs` publica en el CHAT común de OpenWebRX+ (MQTT `aprs/CLIENT`) los mensajes APRS-IS dirigidos a la estación:
  - sin ack, rej ni telemetría;
  - sin duplicados en 5 min;
  - con un máximo de 200 caracteres.
- Solo recibe: no transmite por RF ni manda ACK automáticos.
- `RAK_OWRX_CHAT=yes` y `bricohams-mqtt-settings.py --chat`.

**Mapa en vivo** (ADR-55)
- `/bricohams/api/aviones`: aviones de readsb saneados.
  - Responde 503 si los datos tienen más de 15 s.
  - No publica la posición del receptor.
- Plugin `bricohams_live`:
  - aviones cada 2 s;
  - trazas de las estaciones APRS en movimiento (2 h, 512 estaciones, 1000 puntos);
  - etiquetas con `textContent`.
- `tools/activar_mapa_local.sh`: despliegue con copia de seguridad. Comprueba que `rbfeeder.ini` no cambia y que MLAT sigue en marcha.
- readsb pasa a `--device 00000401`: el `00001090` no existía. Cambio autorizado.

**Pruebas y documentación**
- `tests/test_live_map.py` es nuevo. Las pruebas TAK están en `tests/test_mesh_admin.py`.
- Manuales 36 y 37, ADR-54 a ADR-57 y los puertos TAK en `DATOS.md`.

## v4.5 · 11/10/2026
**LoRa APRS en un RAK4631 con firmware propio, Meshtastic 433/868 con las URL de la red, todo dentro del mapa de OpenWebRX+, banner SSH e inventario de dispositivos.** Se mantiene todo lo anterior (la v4.4 que subió EA5KAO como «corregido»).

**RAK4631 · iGate LoRa APRS** (manual 35, esquema 25, ADR-49)
- Firmware `firmware/rak4631-lora-aprs`: **port de LoRa_APRS_iGate (CA2RXU)** al nRF52840/SX1262. Compilado y con sus binarios `.zip`, `.uf2` y `.hex`:
  - igual que el original: radio LoRa APRS 433,775, CAD, digipeater y KISS;
  - nuevo: baliza con estado y ambigüedad, telemetría con la **temperatura y humedad de la caja** (RAK1901/RAK1906/BME280), GPS del slot A y batería;
  - configuración por USB (KISS 0x06 «BH:») guardada en la flash.
- `bricohams-rak-aprs` en la Pi:
  - sube a APRS-IS con las reglas de iGate (qAR, sin TCPIP/NOGATE/RFONLY, sin consultas ni terceros);
  - baja a RF los mensajes de APRS-IS para estaciones oídas (messagesToRF);
  - le manda al RAK su configuración desde `bricohams.env`;
  - `grabar` (DFU), `prueba`, `estado`, `baliza`;
  - servicio sin root (DynamicUser, credencial).
- Configuración **clonada del iGate actual** (192.168.1.142) con el indicativo **EA5KAO-15**.
- El control de ventiladores usa la temperatura del RAK si no hay DS18B20 (`FAN_CAJA_RAK`).

**Meshtastic** (manual 35, ADR-51)
- `MESH433_CHANNEL_URL`: la URL de la red 433 se aplica tal cual, con radio EU_433 LONG_FAST a 10 dBm. `MESH_CHANNEL_URL`: la nueva URL 868 (SFNarrow, 869,618 MHz, BW 62,5, SF7, 27 dBm).
- Las URL completas, con los canales privados, solo van en tu `bricohams.env`. El `.env.example` lleva la versión pública (`bricohams-mesh-url publica`).
- `bricohams-mesh-url`: lee una URL sin enseñar claves.
- El canal privado `MESH868_PRIVATE_*` solo se añade si queda hueco (máx. 8).
- Nombres: *SDR BricoHams 433* (SB43) y *SDR BricoHams 868* (SB86).
- `bricohams-lilygo firmware`: actualiza el Meshtastic oficial del LilyGO con esptool, conservando la configuración.

**Integración directa con OpenWebRX+** (ADR-50)
- `bricohams-mesh-owrx` y `bricohams-rak-aprs` publican en el MQTT local (`lora433/APRS`, `mesh433/Meshtastic`, `mesh868/Meshtastic`). OpenWebRX+ 1.2.126 lo pinta en su **mapa** con su propio código.
- La posición propia va redondeada. Chat de canales públicos opcional (`MESH_OWRX_CHAT`).
- Se instalan `dxlaprs-lora`, `python3-meshtastic` y `python3-pycryptodome` (modos *LoRa APRS* y *Meshtastic* de OpenWebRX+).
- Marcadores LoRa APRS 433,775, Meshtastic 433 LongFast y 868 SFNarrow.

**Banner SSH** (`bricohams-banner`, ADR-52)
- Antes de entrar: logo y aviso legal, sin sistema, versiones ni IP.
- Al entrar: estado de la estación (sistema, caja, servicios, equipos, LoRa APRS, seguridad, ayuda).
- La auditoría del blindaje lo comprueba.

**Dispositivos:** `bricohams-dispositivos` (inventario por VID:PID y serie; `/dev/rak-aprs` y `/dev/lilygo-mesh` sin enchufar de uno en uno; `HARDWARE_PENDIENTE` = «en camino»).

**Pruebas nuevas:** `test_rak_aprs`, `test_mesh_owrx`, `test_v45_dispositivos`.

**Despliegue en la estación de EA5KAO (11/10/2026)** (informe: `docs/DESPLIEGUE_EA5KAO_2026-10-11.md`, ADR-53)
- **Meshtastic solo para el admin:**
  - nuevo `bricohams-mesh-admin` en `/settings/bricohams/meshtastic` (HTTPS, sesión de OpenWebRX+, CSRF, sin PSK). Botón «Meshtastic 433 / 868» en Ajustes;
  - página `/settings/bricohams/aprs` («APRS (RAK)»): estado del RAK, registro de paquetes oídos y reinicio de la pasarela, sin enseñar el passcode;
  - los botones los pone `bricohams-owrx-botones` en la plantilla `settings.html` de OpenWebRX+ (antes era un `sub_filter` de nginx que no salía entrando por `:8073`). Un gancho de apt los vuelve a poner tras actualizar openwebrx;
  - se quita la web 9443 de meshtasticd;
  - la web pública solo enseña los nodos en el mapa.
- **nginx:** `install.sh` desactiva otros sites `default_server`. Un site antiguo `openwebrx` se saltaba el HTTPS y la protección de `/settings`.
- **RAK4631 con RUI3:**
  - `bricohams-dispositivos` lo reconoce (`1915:521f`, rol `rak-rui3`);
  - `grabar` se para y explica la conversión a WisBlock (manual 35).
- **`grabar`:** ya no da por bueno el DFU solo porque `adafruit-nrfutil` devuelva 0; exige «Device programmed».
- **Firmware:**
  - sin batería, el RAK mandaba `"vbat": nan` (JSON inválido). `prueba` se caía y el servicio tiraba todos los STATUS (sin `rak-aprs.json` ni temperatura de la caja);
  - la Pi lo tolera (`json_rak`, nan/inf → null);
  - el código usa `medidaValida()` por rangos en lugar de `isnan()`. **Hay que recompilar los binarios** (`tools/compilar_rak.sh`); los de `bin/` siguen siendo 1.0.0.
- **Pruebas:** `test_mesh_admin` (nuevo). `test_rak_aprs` amplía con nan, `json_rak`, `grabar` y RUI3.

## v4.4 · 11/10/2026
**Blindaje de seguridad de la estación y posición pública redondeada.** Se mantiene todo lo anterior, más el cambio de EA5KAO en v4.4.1 (`MESH_CHANNEL_URL` con los canales SFNarrow, Iberia, Test, Bots y Murcia).

**`bricohams-blindaje`** (manual 34, esquema 24, ADR-47)
- **`auditar`** (no cambia nada; nota de 0 a 100; nunca enseña una clave) revisa:
  - actualizaciones;
  - cuentas sin contraseña, usuario `pi` y sudo sin contraseña;
  - SSH;
  - puertos a la vista y cortafuegos;
  - 8073 abierto a Internet (`/login` sin cifrar);
  - permisos de `settings.json`, `users.json`, `bricohams.env`, los `.env`, las copias, `mediamtx.yml` y `rbfeeder.ini`;
  - `bricohams.env` dentro del git;
  - **valores de las claves en ficheros públicos**;
  - posición exacta publicada;
  - nginx (versión, límite de `/login`, redirección a HTTPS, certificado);
  - servicios que sobran, fail2ban y sysctl.

  Además recuerda que el HAT, el Mini RTL-SDR y el SDRplay están pendientes.
- **`aplicar`** (con copia; `deshacer` vuelve atrás):
  - cortafuegos nftables del host: público 80/443/8073; solo LAN SSH, 4403, 9443 y 8554. Se carga con **vuelta atrás automática en 3 minutos** si no se hace `confirmar`;
  - SSH sin root y con 3 intentos, solo con clave si ya hay claves;
  - fail2ban (SSH y reincidentes);
  - unattended-upgrades;
  - permisos;
  - `UMask=0027` en OpenWebRX+;
  - sysctl;
  - Bluetooth fuera;
  - `--sudo-con-clave` opcional.
- **Variables:** `BLINDAJE_8073`, `BLINDAJE_SSH`, `BLINDAJE_LAN`, `BLINDAJE_PUERTOS_LAN`.
- **Instalación:** la pone el paso `herramientas`; `bricohams-check` enseña su resumen.

**nginx:** `server_tokens off`, 12 intentos por minuto en `/login` y `/pwchange` (429), `X-Frame-Options`, `Permissions-Policy` y ficheros ocultos (`.git`, `.env`…) 404.

**Posición pública redondeada** (ADR-48): `/status.json` de `sdr.ea5kao.ampr.org` publicaba la casa con 6 decimales. Ahora:
- `OWRX_GPS_DECIMALES="2"` (~1 km) en `settings.json`;
- `meteo.json`, `pases.json` e `init.js`, siempre a 2 decimales;
- los cálculos siguen con la posición exacta.

**Pruebas:**
- `test_blindaje` (sistema de mentira, `nft -c`);
- `test_ssl_admin` con nginx real: 429, cabeceras y ocultos;
- `test_render_settings` y `test_locator_es` con la posición redondeada.

## v4.3 · 05/10/2026
**OpenWebRX+ en Docker desde `bricohams.env` y zona de la estación por locator para cualquier sitio de España.** Se mantiene todo lo anterior. Parte de la V4.3 que empezó EA5KAO (revisada y adoptada): `OWRX_BACKEND`, `owrx_control`, comprobación de volúmenes, selector por locator, plantilla genérica `N0CALL`, indicativo/QTH/país en `settings.json`, `APRS_IGATE_ENABLE`, `LISTENERS_COUNTRY` y enlace a perfiles remotos en el plugin de oyentes.

**Docker** (manual 33, esquema 23, ADR-44 y ADR-45)
- **Despliegue desde `bricohams.env`:**
  - instala Docker si falta;
  - desactiva el OpenWebRX+ nativo;
  - crea el usuario `openwebrx` para los servicios del host;
  - genera `docker-compose.yaml` (imagen `slechev/openwebrxplus-softmbe`, red `host`, volúmenes `./etc` `./var` `./plugins`, USB en caliente sin `--privileged`);
  - `compose pull` + `up -d`.
- **Variables:** `OWRX_DOCKER_IMAGE`, `_RED`, `_PORT`, `_PRIVILEGED`, `_DESPLEGAR`, `_ACTUALIZAR`.
- **Pasos:** `comprobar` sin repositorio de luarvique; `sdrplay` y `ft2` se saltan con aviso.
- **Mantenimiento:**
  - la tarea semanal actualiza la imagen;
  - la copia diaria incluye `/opt/owrx-docker`;
  - `bricohams-check`, `bricohams-servicios` y `bricohams-sdr-serials` entienden el contenedor.
- **owrx-clone 1.1 `--docker CONTENEDOR`:** exporta e importa en los volúmenes del contenedor (sin apt ni parches), pasa de nativo a Docker y al revés, `deshacer` con `docker stop/start`, y `ayuda docker`. El instalador lo usa solo en `--exportar`, `importar` y la copia diaria.
- **Rutas en `/etc`:** `instalar_env` añade a `/etc/bricohams/bricohams.env` las calculadas (`OWRX_DATA`, `OWRX_HTDOCS`, `OWRX_CLONE_DOCKER`). En Docker, `owrx_owner` cambia el dueño en la Pi.

**Zona por locator** (manual 32, esquema 22, ADR-43 y ADR-46)
- **Catálogo de España en el kit** (`data/locator`, `tools/locator_catalogo.py`):
  - 232 frecuencias de 96 aeropuertos (OurAirports, 8,33 kHz convertidos);
  - 150 estaciones AEMET (indicativos validados);
  - 48 puertos con canales 9/12/14/16;
  - NAVTEX 518/490 kHz.
- **Selección:** por categoría con mínimo garantizado de aeropuerto y AEMET. Los canales repetidos se juntan. Etiqueta `[AUTO-LOCATOR]` con distancia.
- **Las coordenadas exactas mandan sobre el locator:** sin locator, se calcula de las coordenadas; si no cuadran o se sale de España, avisa.
- **En la Pi, al instalar** (`LOCATOR_ONLINE`, caché de 30 días, nunca para la instalación): lista completa de AEMET y emisoras de FM regionales y locales de maps.fmdx.org.
- **`METEO_STATIONS`:** sale de la zona (`LOCATOR_METEO`).
- **Lejos de Mi QTH:** se quitan los marcadores del kit propios de Murcia y los canales con nombre de Cartagena vuelven al genérico. Los tuyos no se tocan.
- **`bricohams-locator`:** `info`, `refrescar`, `marcadores [--aplicar]`, `meteo`, `coordenadas`, `locator`. `bricohams-check` muestra la zona.

**Arreglos sobre la V4.3 de partida**
- **El locator ya no pisa coordenadas exactas** (instalador y `settings.json`).
- **`METEO_STATIONS` de la zona llegaba solo al instalador:** ahora va también a `/etc` y a `meteo.env`, entre comillas.
- **Docker:** `owrx_owner` hacía `chown openwebrx` *dentro* del contenedor, donde OpenWebRX+ corre como root y ese usuario puede no existir. Ahora se cambia el dueño en la Pi, que es quien lo necesita.
- **`LOCATOR_CATALOG` sin locator:** paraba la instalación; ahora avisa. El resumen de la herramienta ya no se mezcla con el JSON por la salida estándar.

**Revisión independiente** (antes de entregar). Corregido:
- **Coordenadas a 0 en `/etc`:** las coordenadas sacadas del locator se perdían de `/etc/bricohams/bricohams.env` al pasar por `meteo`; el iGate y los LilyGO habrían quedado en 0,0.
- **Volver a nativo:** el contenedor seguía en marcha y se quedaba el 8073 y los SDR. Ahora se para y pierde el arranque automático.
- **`--actualizar` tras cambiar el backend:** no repetía meteo, cámara, visitas, satélites…; ahora su huella incluye `OWRX_BACKEND` y `OWRX_DOCKER_DIR`.
- **Contenedor propio sin el usuario `openwebrx` en la Pi:** `OWRX_DOCKER_DESPLEGAR="no"` paraba la instalación.
- **`--backup` con una copia de una estación Docker:** no restauraba usuarios ni marcadores.
- **`bricohams-locator` sin sudo:** no podía leer el `.env`. Ahora usa `/etc/bricohams/zona.env` (644, sin claves).
- **Entradas raras de fmdx o una caché rota:** ya no tumban la selección.
- **owrx-clone:** no usa un volumen montado desde una carpeta del sistema (`/etc`, `/var`…).

**Pruebas nuevas:**
- `test_locator_es`:
  - 895 puntos de España;
  - locator ida y vuelta;
  - datos en línea con respuestas de prueba;
  - kit lejos de Mi QTH;
  - `bricohams-locator`;
  - zona del instalador;
  - paso `configuracion` de punta a punta en Docker.
- `test_owrx_clone_docker`.
- `test_instalador_docker` ampliado: despliegue, `docker compose config`, pasos saltados y `.env` de `/etc`.
- `locator_catalogo.py --comprobar`.

## v4.2 · 05/10/2026
**Arreglos de la instalación real en la Pi de EA5KAO, plugins de audio, SSL solo en la administración y owrx-clone.** Se mantiene todo lo anterior.

**Arreglos**
- **`bricohams.env: line 182: Clave2026: unbound variable`:** una clave con `$` (`QRZ_PASS`). `bricohams.env` se lee con `bricohams-env.py` sin ejecutarlo: `$` literal, comillas dobles/simples, comentarios, errores con número de línea. La copia de `/etc` y los `.env` derivados van entre comillas simples (`sq`/`envl`). ADR-38.
- **`curl: (6) Could not resolve host: luarvique.github.io` tras el paso `red`:** `red` borraba y recreaba la conexión WiFi en uso. Ahora la modifica, `esperar_red` antes de cada paso (DNS, 2 min), `clave_apt` y `script_remoto` con reintentos y error claro (antes `bash -c "$(wget …)"` seguía con una descarga vacía). ADR-39.
- **Revisadas y adoptadas las correcciones de EA5KAO:** `paso_web` acababa en `[ … ] && aviso` (devolvía 1 con `set -e`), redirección `/tar1090`, ficha de indicativos con **HamQTH** primero (API v2) y caché versionada. Añadido `?app=BricoHams-SDR` en HamQTH. Nueva auditoría automática de funciones que acaban en `[ … ] &&`.
- **nginx:** `listen 443 ssl http2` (el `http2 on;` no existe en el nginx 1.22 de Bookworm). `nginx -t` fallido para el paso con el mensaje.
- `bricohams-fan`/`bricohams-wx` entienden valores entre comillas simples.

**SSL solo en la administración** (decisión de EA5KAO)
- `SSL_MODO="admin"` (defecto): receptor y portal por HTTP; `/login`, `/settings…` y demás rutas con usuario → 301 a HTTPS; cookie `owrx-session` `Secure; HttpOnly; SameSite=Lax`; sin HSTS. También `todo` y `no`. Rutas comunes en `bricohams-sdr-rutas.conf`. `bricohams-servicios` y `bricohams-check` lo reflejan. ADR-40, manual 23, esquema 18.

**Audio en el navegador** (los dos plugins pedidos)
- `filtro_audio` (botón FILTRO): paso banda 24 dB/oct por modos, notch manual y notch automático con seguimiento, espectro.
- `dsp_audio` (botón DSP): EQ 3 bandas, puerta de ruido, AGC (suave/medio/fuerte), limitador, preajustes y medidores.
- `audio_cadena`: base común entre `audioNode` y `gainNode` de OpenWebRX+. Manual 30, ADR-41, esquema 20.

**owrx-clone** (exportar e importar toda la configuración de un OpenWebRX+)
- Herramienta genérica para la comunidad en `owrx-clone/`: `exportar`, `ver`, `importar`, `deshacer`, `comprobar`, `ayuda` (y en inglés). Niveles `config`, `etc`, `web`, `paquetes`, `sistema`, `parches`, `extra`; `--publico`, `--cifrar`, `--mapear`, `--simular`; SHA-256, rutas vigiladas, copia previa. README es/en, `man owrx-clone`, `instalar.sh`, licencia MIT.
- **Revisión de seguridad independiente** (dos pasadas) antes de publicarlo. Corregido:
  - un `data_directory` en el perfil podía llevar los ficheros a `/etc/cron.d`, `/home/pi`…;
  - `deshacer` escribía a través de enlaces simbólicos;
  - la copia previa se hacía antes de apt;
  - una importación cortada no dejaba lista de lo creado;
  - `audio_cadena` desconectaba también el osciloscopio de rig_skin;
  - `--solo red` esperaba a una red que aún no había.

  Hay una prueba de cada caso.
- En el kit: `install.sh --exportar` (sin `bricohams.env`) y `--importar` (paso nuevo `importar`); el instalador respeta lo importado (`/etc/bricohams/perfil-importado`, `OWRX_PLANTILLA`); la copia diaria guarda un perfil. Manual 31, ADR-42, esquema 21.

**Documentación y pruebas**
- [Ayuda rápida](docs/AYUDA_RAPIDA.md), manuales 30 y 31, manuales 02, 09, 23, 25 y 27 al día, ADR-38 a ADR-42.
- Pruebas nuevas: `test_env_red`, `test_ssl_admin` (nginx real), `test_audio_plugins`, `test_audio_navegador` (Chromium real), `test_owrx_clone`, `test_instalador_perfil`.

## v4.1 · 04/10/2026
**Nueva función: `sudo bash install.sh --actualizar`.** Se mantiene todo lo de la v4.0.
- **Qué hace, en orden:** git pull `--ff-only` del kit como su dueño (si llega un `install.sh` nuevo, se relanza con él) → añade a `bricohams.env` las variables nuevas del `.env.example` sin tocar las existentes → copia de seguridad → `apt upgrade` (respeta retenidos y `.conf`) → repite **solo los pasos que han cambiado** → `bricohams-check`, aviso por Telegram y aviso de reinicio.
- **Huellas por paso** en `/var/lib/bricohams/kit-estado` (600, sin valores): código del paso, ficheros del kit que usa y variables de `bricohams.env` que lee. Las saca solo del código de cada paso, sin tablas que mantener. También la instalación normal las guarda.
- **Opciones:** `--simular`, `--sin-git`, `--sin-apt`, `--todo`. Si se corta, se relanza y sigue.
- **Marcadores en tres vías** (paso `configuracion`): ya no se pisan los añadidos desde la web; las correcciones del kit sí llegan. `bricohams-merge-bookmarks --tres`.
- **Arreglo:** el paso `herramientas` ya no reactiva el timer de copia diaria si la copia la lleva el cron (copia doble).
- Manual 29, esquema 19, ADR-37, prueba `test_actualizar.py` (kit de juguete, git real y relanzamiento).

## v4.0 · 04/10/2026
**Correcciones y ampliación pedidas por EA5KAO tras la v3.3.** Se mantiene todo lo anterior.

**Hardware**
- **Sensores y ventiladores con el HAT puesto:** la cabecera de 40 pines queda tapada. Nueva **Pico «bricohams-io»** por USB (`firmware/pico-io/main.py`, servicio `bricohams-io`, `/dev/bricohams-io`): BME280 GP4/GP5, DS18B20 GP22, pluviómetro GP15, PWM GP16/GP17, tacómetros GP18/GP19. Failsafe al 100 % si la Pi calla 60 s. `IO_MODE="gpio"` mantiene el modo anterior sin HAT. Manual 20, esquema 16, ADR-29.
- **Cámara:** Waveshare RPi Camera (F) OV5647 NoIR + cinta Standard–Mini 15→22 pines para el conector de 22 pines de la Pi 5; ajuste `ov5647_noir.json`. Manual 07.
- **Anclajes impresos** (`hardware/anclajes`, 16 STL): crucetas de 3 piezas con M6 a tuercas cautivas y antigiro, para brazos, quad (boom 20 × 20), fibra 433, tubos cortos (Bigsignal, ADS-B, viento), `adsb_tapa_tubo`, brida de los sensores de viento, vaso y plataforma niveladora del pluviómetro y soporte de la Pico. Manual 21, ADR-30.
- Esquema 17: filtros 433/868 y preamplificadores; esquema 18: red y servicios.

**Marcadores** (374 en total, `data/marcadores_v4.json`)
- Radio Club Región de Murcia: RU-75 438,775 (−7,6 MHz, 77,0 Hz), 145,325 FM, 430,325 FM, **CB canal 32 (27,325)** y PMR canal 5.
- CB 40 canales CEPT, PMR446 16 canales, FM (Radio María y otras), DAB+ 9A/8C/9C, FT8/FT4/FT2 en todas las bandas, modos digitales, aviación (AIP de San Javier y Alicante), marina (Cartagena y Mazarrón), satélites.
- Perfiles CB de 11 m nuevos. `docs/CANALES_Y_FRECUENCIAS.md`.
- **No se incluyen** radiotaxis ni TETRA de emergencias o policía (secreto de las comunicaciones, ADR-36). El perfil TETRA sigue para explorar la banda.

**Plugins web**
- `banderas`: bandera del país en FT8/FT4/FT2.
- `dvficha`: ficha de RadioID y, con cuenta XML, foto de QRZ en DMR/YSF/NXDN/D-STAR (`bricohams-api`).
- `satelites`: banner con los próximos pases (SGP4 en la Pi, `bricohams-satpass`) y ▶ Escuchar: cambia de perfil y arranca el Doppler de 0xAF.
- Plugins de 0xAF `doppler` y `show_band_plan` (plan de bandas activado); `listeners` opcional (necesita Supabase).
- `visitas`: contador para el panel. Logo BricoHams reducido al 42 %.
- **FT2** experimental: `bricohams-ft2` compila decodium-rx y aplica un parche reversible a OpenWebRX+. Manual 28, ADR-35.

**Servicios y operación**
- **https** con nginx + Let's Encrypt (o DuckDNS), certificado propio mientras tanto; portal `/bricohams/`, privacidad, tar1090 en 127.0.0.1:8504, cámara HLS `/camara/`. Manual 23, ADR-32.
- **Visitas:** MQTT de OpenWebRX+ → `bricohams-visitas`: país, ciudad (DB-IP Lite local), IP truncada, retención de 90 días y aviso por **Telegram**. Manual 24, ADR-33.
- **Tareas automáticas:** cuenta de servicio `bricohams` (sin contraseña ni shell) + sudoers limitado a `bricohams-tarea` + `/etc/cron.d/bricohams` (copias, apt, reinicio preventivo que espera a que acabe un pase, salud, resumen). Manual 25, ADR-34.
- `bricohams-servicios` muestra y comprueba todas las URL.
- Firmware de la estación WX LoRa mejor explicado (manual 22).
- install.sh: 24 pasos (`io`, `satelites`, `ft2`, `web`, `visitas`, `tareas` nuevos). `bricohams-check` con secciones nuevas.
- Pruebas nuevas: Pico, pases, visitas, API, FT2, anclajes.

## v3.3 · 04/10/2026
**Arreglo (Trixie):** apt no podía resolver las dependencias.
- **Error:** «rtl-sdr : Depends: librtlsdr0 (= 0.7.0~rtlsdrblog1) but 2.0.2-2+b1 is to be installed».
- **Causa:** en la Pi quedaba retenido el fork rtl-sdr-blog de una instalación anterior. En Debian 13 la librtlsdr0 es la 2.0.2, más nueva, y los paquetes de Trixie la piden.
- **Solución:**
  - En Trixie se usa el **rtl-sdr 2.0.2 de Debian** (osmocom), que ya trae bias-tee, muestreo directo del V3 y el R820T/R860.
  - `rtlsdr_debian` quita la retención y pasa las tres piezas (`librtlsdr0`, `librtlsdr-dev` y `rtl-sdr`) a la versión de Debian a la vez. Se ejecuta al principio del paso `base` y en el paso `rtlsdr`.
  - En Bookworm todo sigue igual: rtl-sdr-blog compilado y retenido.
- `bricohams-check` comprueba en Trixie que las tres piezas son la misma versión de Debian.
- Prueba ampliada en `test_instalador_os.py`; ADR-01 y ADR-02 y los manuales 02 y 09 actualizados.

## v3.2 · 04/10/2026
**Arreglo:** el paso `base` se paraba en la Pi de EA5KAO.
- **Error:** `archive.raspberrypi.com … Network is unreachable` y `no longer has a Release file`.
- **Causa:** la Pi tiene dirección IPv6, pero el router no la deja salir a Internet. apt intentaba conectar por IPv6 y fallaba.
- **Solución:** nueva función `apt_update`. Si `apt-get update` falla, crea `/etc/apt/apt.conf.d/99bricohams-ipv4` (`Acquire::ForceIPv4 "true"`) y reintenta hasta 3 veces. Si aun así falla, se para con los comandos para diagnosticar la red.
- Todas las llamadas a `apt-get update` del instalador usan ahora `apt_update`.
- Manual 02: problema y solución documentados. Prueba en `test_instalador_os.py`.

## v3.1 · 04/10/2026
**El instalador funciona en Raspberry Pi OS Trixie (Debian 13) y en Bookworm (Debian 12)**
- La Pi de EA5KAO tiene Trixie y la v3.0 se paraba en el paso `comprobar`.
- El repositorio de OpenWebRX+ sí publica `ppa/trixie`: firmado, arm64, OpenWebRX+ 1.2.125 para Python 3.13.
- `install.sh` detecta la versión (`DEB` y `DEB_NUM`) y elige:
  - el repositorio de OpenWebRX+ (`ppa/$DEB`);
  - Meshtastic `Debian_12` o `Debian_13`;
  - rbfeeder: con `inst_rbfeeder.sh` en Bookworm y con el repositorio apt `apt.rb24.com trixie` en Trixie;
  - mlat-client: de apt o **compilado** de `mutability/mlat-client` con `python3-pyasyncore`.
- El sensor I2C admite `python3-smbus` o `python3-smbus2`.
- `bricohams-check` acepta las dos versiones y avisa si el repositorio de OpenWebRX+ no corresponde a la del sistema.
- **Docs:** ADR-01 reescrita, manuales 01 y 02, REFERENCIAS.
- **Prueba nueva:** `test_instalador_os.py`.
- **Todo lo de la v3.0 se mantiene igual.**

## v3.0 · 04/10/2026
**Corrección urgente**
- **`sudo: ./install.sh: command not found`:** el kit se había copiado sin el bit de ejecución.
  - Toda la documentación usa ahora `sudo bash install.sh`.
  - El instalador repara solo los permisos y los finales de línea CRLF de sus scripts.
  - `.gitattributes` fuerza LF.

**Nuevo: antenas** (`hardware/antenas/`, manuales 11–16)
- **Modelos NEC2** (`sim/`) de la **quad de doble resonancia 2 m/70 cm**, dos **discones** de 12 + 12 varillas y el **plano de tierra de 1090 MHz**. Generan resultados JSON y diagramas.
- **30 piezas impresas paramétricas** (OpenSCAD + STL):
  - bujes, punteras y alimentadores de la quad;
  - aislador, plantillas de taladro y adaptador de las discones;
  - base, radomo y tapa de la ADS-B con el **LNA dentro**;
  - **caja estanca y cruz del lazo MLA-30**;
  - fundas SMA/N;
  - brazos, soportes de fibra, GPS y clip de filtro.
- **Plan de mástil con cálculo de viento** (`tools/mastil.py`, esquema 11). Conclusión: el mástil **necesita vientos a 2 m**.
- **Planos** 08–10 y la **cadena de RF completa** (esquema 12).
- **Evaluación** de los filtros NMRF (433 en el iGate; 868 en reserva), del LNA de 1090, del MLA-30, de las Bigsignal y de la caja de aluminio de cabecera.

**Nuevo: caja v3** (`hardware/caja_v3/`, manual 17)
- **Dos módulos al pie del mástil:** electrónica (228 × 240 × 112) y potencia (170 × 200 × 112). 30 STL.
- Rejilla universal de M3 cada 20 mm para futuros SDR, 14 pasamuros N, bahía para el SDRplay o el HydraSDR.
- Alimentación con cargador de **120 W** + gatillo USB-C PD a **12 V** + bus WAGO (esquema 15). Regleta **Vansuny USB 3.0** a 12 V.

**Nuevo: ventilación** (`bricohams-fan`, paso `ventilacion`, manual 18, esquema 13)
- 2 ventiladores de 60 mm PWM con **PWM por hardware** en GPIO12/13, tacómetros en GPIO22/5 y DS18B20 en GPIO4.
- Curva con histéresis, alarma de ventilador parado y estado en la web y en `bricohams-check`.

**Nuevo: viento y lluvia** (manual 19, esquema 14)
- `bricohams-wx` lee anemómetro y veleta **RS485 Modbus** (`/dev/rs485`) y un **pluviómetro** en GPIO17.
- Medias APRS: viento de 1 min, dirección vectorial de 2 min, racha de 5 min, lluvia de 1 h, 24 h y desde medianoche.
- Herramientas `--rs485-buscar` y `--rs485-direccion`.
- **Alternativa:** `bricohams-lilygo wxstation` graba la estación LoRa de CA2RXU (**EA5KAO-14**). Variables `WXLORA_*`.

**Nuevo: marcadores y FM**
- `tools/marcadores.py` (idempotente) crea o anota **27 repetidores 🔁** con su **subtono en la descripción**. OpenWebRX no tiene campo CTCSS (ADR-26).
- **Wifon FM 97,5** es el primer marcador y el primer perfil FM («⭐»).

**Nuevo: cámara**
- `CAM_SOURCE="rtsp"`: cámara IP PoE (recomendada: Reolink RLC-510A), reenviada sin recodificar.
- Para CSI, la recomendada es la Camera Module 3 Wide NoIR.

**Documentación**
- `docs/MEMORIA_TECNICA.md`: inventario de componentes, **cables C1–C18**, secuencia de instalación y BOM consolidada.
- **Manuales** 11–19.
- **ADR-18 a ADR-28.**
- Apartados 12–20 de la evaluación, incluida la alternativa al SDRplay: **RSPdx-R2**; con presupuesto ajustado, RSP1B.
- HARDWARE_Y_GPIO con los pines v3.

**Pruebas**
- Nuevas: `test_viento_lluvia.py`, `test_fan.py` y `test_v3_hardware.py` (STL ≤ 250 mm, NEC2, mástil).
- `marcadores.py --comprobar`.
- shellcheck de `tools/*.sh`.

## v2.2 · 04/10/2026
**Nuevo**
- **Caja de intemperie impresa en 3D** para el mástil Televés (`hardware/caja/`). Modelo paramétrico OpenSCAD con 16 piezas, STL listos para imprimir sin soportes en la Kobra S1 y vistas de montaje.
  - **Compartimento de potencia aparte** (tabique + tapa interior) con el cargador USB de 45 W, la regleta/hub USB alimentado y la entrada de 230 V por PG9.
  - Los 2 LilyGO van sobre la tapa interior. Pi 5 + HAT, 3 dongles, diplexor y cámara van en la zona de electrónica.
  - 9 SMA pasamuros rotulados, prensaestopas WX y LAN y rejillas en la cara inferior. Tejadillo inclinado sobre las rejillas de salida.
  - Junta de TPU en ranura con tope de compresión, ventana de la cámara con policarbonato, aro anti-reflejos IR y visera.
  - Sillas en V con abrazadera para el mástil y garita de 6 platos para el BME280.
  - `tools/caja.sh`: exporta los STL, comprueba que caben en 250 × 250 × 250 mm y genera las vistas.
- **WiFi configurable:** nuevo paso `red` del instalador (son 17 pasos). La Pi prioriza `WIFI_SSID_1` y usa `WIFI_SSID_2` como respaldo; el iGate usa `LILYGO_WIFI_SSID` (2,4 GHz). Los SSID y claves se configuran localmente en `bricohams.env`.
- `bricohams-check` muestra la red activa y la señal WiFi.
- Esquemas 06 (alimentación en la caja) y 07 (distribución y conectores). Manual 10 (caja paso a paso). ADR-15 (caja), ADR-16 (cargador de 45 W) y ADR-17 (WiFi).

**Cambios**
- `PI5_USB_MAX_CURRENT="no"` por defecto: con el cargador de 45 W, la Pi limita sus USB a 0,6 A y los SDR van al hub alimentado.

**Correcciones**
- El LilyGO T3 V1.6.1 **no** lleva zócalo de 18650. Lleva un conector de batería LiPo (Picoblade), USB-serie CH9102F y antena SMA, y mide 65 × 27 mm.

## v2.1 · 04/10/2026
- **Canal privado en el nodo Meshtastic 868** (HAT): se añade un 6.º canal «BricoHams» (índice 5) con clave AES-256 detrás de SFNarrow, Murcia, Cartagena, Test y Alicante. La clave va en `MESH868_PRIVATE_PSK` (bricohams.env, fuera del git). El nodo 433 no cambia.

## v2.0 · 04/10/2026
**Correcciones**
- El dongle MULTIPERFIL es un **RTL-SDR Blog V3**, no un V4: la detección del R828D desaparece y el driver rtl-sdr-blog se mantiene.
- El SDRplay tardará meses: la **HF va en el V3** (muestreo directo por la rama Q de 160 a 15 m, sintonizador normal de 12 a 6 m), con los mismos valores de EA7CL. El SDRplay queda preparado con `HF_SDRPLAY`.

**Nuevo**
- **ADS-B** con el FlightStick de RadarBox: readsb (serie 00001090) → rbfeeder en modo red + **MLAT** + mapa tar1090.
- **Sensor BME280/BMP280** en I2C: tarjeta «🏠 EA5KAO · Mi QTH» en METEO y **estación WX APRS EA5KAO-13**.
- **Cámara WPI408** (OV5647 + IR): MediaMTX con H.264 por CPU a 720p y 10 fps, y fichero de ajuste NoIR opcional.
- **LilyGO T3 V1.6.1 de 433** por USB: nodo **Meshtastic EU_433** e **iGate LoRa APRS de CA2RXU** (EA5KAO-10, solo RX), con la herramienta `bricohams-lilygo`.
- **Canales Meshtastic de la red** (QR): SFNarrow, Murcia, Cartagena, Test y Alicante (869,618 MHz, BW 62,5, SF7) en el nodo 868 del HAT. Los mismos canales en el nodo 433.
- **Marcadores:** hotspot DMR 439,450/431,850, hotspot YSF 439,375/431,775 y Sierra Espuña digital 438,950/431,350.
- `bricohams-sdr-serials` para 4 RTL-SDR, `bricohams-check` ampliado y copia diaria con ADS-B, udev y sensor.
- **Repositorio documentado:** decisiones de arquitectura, conjuntos de datos, GPIO, esquemas, manuales, evaluación de módulos y pruebas.
- **Claves fuera del git:** `bricohams.env.example` y `.gitignore`.

## v1.0 · 04/10/2026
- Instalador desde cero para Pi 5 + Bookworm: OpenWebRX+ con 4 receptores, perfiles HF de EA7CL y marcadores.
- HAT HackerGadgets: RTC, GPS con PPS (gpsd + chrony) y Meshtastic 868 (meshtasticd).
- Cámara CSI con MediaMTX y foto para la web.
- Plugins solar (NOAA), meteo (AEMET + Open-Meteo), cámara e imagen BricoHams con Murcia (cabecera, avatar, bandera).
- `bricohams-check`, `bricohams-sdr-serials` y copias diarias.

## v0 · 03/10/2026
- Perfiles HF de 160 a 6 m añadidos a OpenWebRX siguiendo a EA7CL.
- Plugin `solar` (botón SOL junto al DX cluster).
