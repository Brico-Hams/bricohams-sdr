# 37 · Justificación de los cambios de la v4.6

Este documento explica **qué se ha añadido sobre la v4.5, por qué y cómo se ha comprobado**. Sirve de auditoría del código entregado en el ZIP `bricohams-sdr-v4.6-codigo.zip`. El manejo diario está en el [manual 36](36_TAK_MAPA_LOCAL.md). Las decisiones de arquitectura están en [ARQUITECTURA.md](../ARQUITECTURA.md) (ADR-54 a ADR-57).

## 1. Cambio de versión: de v4.5 a v4.6

La v4.5 cerraba el RAK4631 (iGate LoRa APRS), Meshtastic 433/868 y su configuración solo desde `/settings`. Sobre esa base se ha añadido:

- un servidor TAK local;
- el chat APRS;
- el mapa en vivo (ADS-B y trazas APRS);
- la capa TAK privada.

Son funciones nuevas que no rompen nada de lo anterior. Por eso suben la versión menor del kit: **v4.5 → v4.6**. OpenWebRX+ no cambia de versión.

| Componente | v4.5 | v4.6 | Motivo |
|---|---|---|---|
| Kit BricoHams SDR | 4.5 | **4.6** | Funciones nuevas compatibles hacia atrás |
| OpenWebRX+ | 1.2.126 | 1.2.126 (sin cambios) | Solo se añade un plugin de mapa; no se toca su código |
| OpenTAKServer | — | **1.7.13** | Servidor TAK libre (Python), con CoT, enrollment y Marti |
| OpenTAKServer UI | — | **1.7.5** | Interfaz web oficial, comprobada con sha256 |
| Python para TAK | — | **3.12.15** (uv 0.13.0, entorno aislado en `/opt/bricohams-tak`) | El gevent fijado por OTS falla con `AssertionError` al hacer fork en Python 3.13 |
| Python del sistema | 3.13 | 3.13 (sin tocar) | El resto del kit sigue igual |
| readsb `--device` | `00001090` | **`00000401`** | El serie `00001090` no existe en la Pi y readsb no recibía. Cambio autorizado por el usuario. OpenWebRX+ sigue en `00000001` |
| RadarBox / MLAT | activo | activo (sin cambios) | `/etc/rbfeeder.ini` tiene el mismo hash que antes |

## 2. Requisitos del usuario y cómo se cumplen

| Petición | Solución | Dónde |
|---|---|---|
| La configuración nunca en la web pública, solo en Ajustes (con contraseña) | Todo lo que configura o muestra datos privados cuelga de `/settings/bricohams/…` y valida la sesión de OpenWebRX+ | `bricohams-mesh-admin`, ADR-53 y ADR-56 |
| Servidor TAK local | OpenTAKServer aislado, solo LAN y con TLS | `tools/instalar_tak.sh`, ADR-54 |
| TAK dentro de «Mapas» | Capa TAK en el mapa, solo para el admin y solo por HTTPS | `bricohams_live.js`, `TAK_POSICIONES`, ADR-56 |
| Los mensajes APRS en el CHAT común | Mensajes APRS-IS dirigidos a nosotros, publicados en MQTT `aprs/CLIENT`, que OpenWebRX+ ya pinta en su chat | `mensaje_chat`, `ChatAPRS`, ADR-57 |
| Aviones de ADS-B en tiempo real | API pública saneada `/bricohams/api/aviones` sobre `aircraft.json` de readsb | `bricohams-api.py`, ADR-55 |
| Estaciones APRS en movimiento y sus trazas | Posiciones APRS-IS en el mapa y trazas guardadas en el navegador | `aprs_mapa`, `bricohams_live.js` |
| No romper RadarBox con MLAT | No se toca rbfeeder ni mlat-client; solo se lee `aircraft.json` | ADR-55 |

## 3. Cambios fichero a fichero

### 3.1 `files/bin/bricohams-api.py`: aviones ADS-B

- **Qué hace:** [`aviones()`](../../files/bin/bricohams-api.py) (línea 32) lee `/run/readsb/aircraft.json`. Se publica en la ruta `/bricohams/api/aviones` (línea 245).
- **Diseño:**
  - Si la instantánea tiene más de 15 s, o viene del futuro, devuelve **503**: se ve enseguida que readsb ha parado.
  - Descarta las posiciones con más de 60 s (`seen_pos`), las coordenadas no finitas o fuera de rango y los hex que no son 6 cifras hexadecimales.
  - Solo publica `hex`, `flight`, `lat`, `lon`, `timestamp`, `alt_baro`, `gs` y `track`.
- **Seguridad:** nunca publica la posición del receptor (`receiver`) ni otros campos de readsb. El nombre de vuelo se manda como texto; el navegador lo pinta con `textContent`.
- **Alternativa descartada:** abrir tar1090 o el JSON de readsb directamente. Expondría la posición de la estación y todos los campos internos.
- **Pruebas:** `tests/test_live_map.py` cubre la caducidad, el futuro, el NaN, la latitud 91, el hex inválido, el `<script>` en el vuelo y la ausencia de `receiver`.

### 3.2 `files/bin/bricohams-rak-aprs`: chat APRS y posiciones APRS-IS

- [`aprs_mapa`](../../files/bin/bricohams-rak-aprs) (línea 273) convierte los paquetes de posición de APRS-IS en el formato del mapa de OpenWebRX+. Los marca con el origen «APRS-IS» y sin frecuencia, para no confundirlos con lo oído por RF.
- [`mensaje_chat`](../../files/bin/bricohams-rak-aprs) (línea 306) trata los mensajes APRS:
  - desempaqueta los de terceros (`}`);
  - descarta `ack`, `rej`, `PARM.`, `UNIT.`, `EQNS.` y `BITS.` (son protocolo, no conversación);
  - quita el `{msgid`, los caracteres de control y corta a 200 caracteres;
  - el nombre queda «ORIGEN -> DESTINO».
- [`ChatAPRS`](../../files/bin/bricohams-rak-aprs) (línea 329) evita duplicados: el mismo mensaje por varias rutas en 5 min sale una sola vez. Publica en MQTT `aprs/CLIENT`.
- Se activa con `RAK_OWRX_CHAT=yes` (lectura en la línea 536).
- **Seguridad:**
  - **Solo recibe:** el chat no transmite por RF ni manda ACK automáticos. Así no hay emisiones sin control del operador y se cumplen las reglas de iGate de la v4.5.
  - El HTML llega como texto; lo comprueba la prueba `<img onerror=x>`.
- **Pruebas:** `tests/test_live_map.py` (formato, terceros, filtros, deduplicación, tema MQTT y posiciones) y `tests/test_rak_aprs.py`.

### 3.3 `files/bin/bricohams-mqtt-settings.py` e `install.sh`

- La opción `--chat` (línea 14) activa `mqtt_chat` y `mqtt_aprs` en `settings.json` de OpenWebRX+, sin tocar el resto de ajustes.
- `install.sh` la pasa cuando `RAK_OWRX_CHAT=yes`.
- `bricohams.env.example` documenta `RAK_OWRX_CHAT=yes`.
- **Por qué:** OpenWebRX+ ya tiene un chat que escucha MQTT. Reutilizarlo evita parchear su código y sobrevive a sus actualizaciones.

### 3.4 `files/bin/bricohams-mesh-admin`: posiciones TAK privadas

- [`TAK_POSICIONES`](../../files/bin/bricohams-mesh-admin) (línea 52) es `/settings/bricohams/tak/posiciones`.
- [`posiciones_tak()`](../../files/bin/bricohams-mesh-admin) (línea 676) hace una consulta de **solo lectura** a PostgreSQL como `opentakserver`:
  - `statement_timeout` de 3000 ms y `timeout=5` en el proceso;
  - `LIMIT 1000`;
  - solo CoT que no han caducado (`stale`).
- El manejador (línea 737):
  - devuelve **401** sin sesión de admin y **503** si TAK falla;
  - responde con `Cache-Control: no-store`;
  - no usa la caché de sesiones, para que una sesión cerrada no siga viendo posiciones.
- **Seguridad:**
  - Las posiciones TAK son de personas y equipos. Nunca van a MQTT ni a la web pública.
  - No se expone `/etc/bricohams/tak-access.txt`.
- **Alternativa descartada:** la API Marti de OTS desde el navegador. Necesita un certificado de cliente en cada navegador y mezclaría la sesión de OpenWebRX+ con la de TAK.
- **Pruebas:** `tests/test_mesh_admin.py` cubre el 401 sin consultar la base de datos, el 200 con sesión, `no-store`, la sesión revocada y el 503.

### 3.5 Plugin de mapa `files/htdocs/plugins/map/bricohams_live/`

`init.js` carga `bricohams_live.js` y `bricohams_live.css` en el mapa de OpenWebRX+.

| Capa | Fuente | Refresco | Límites |
|---|---|---|---|
| Aviones | `/bricohams/api/aviones` (público) | 2 s | Se quitan a los 75 s sin posición |
| Trazas APRS | Mensajes del mapa de OpenWebRX+ | Al llegar | TTL 2 h, 512 estaciones, 1000 puntos por estación |
| TAK | `/settings/bricohams/tak/posiciones` (admin) | 10 s | Solo por HTTPS; se borra con 401, 403 o error |

**Seguridad y robustez:**
- Las etiquetas se pintan con `textContent` (sin inyección de HTML).
- Los límites de memoria evitan que una pestaña abierta días acabe colgada.
- Si no hay sesión, la capa TAK no hace nada visible.

**Limitaciones:**
- Las trazas APRS viven solo en el navegador: al recargar empiezan de cero.
- Los aviones solo tienen posiciones de readsb (ver ADR-55).

### 3.6 `tools/instalar_tak.sh` y `tools/tak-requirements.txt`

El instalador es idempotente y se puede volver a lanzar.

1. **Python:** instala uv 0.13.0 y Python 3.12.15 en `/opt/bricohams-tak`, con dependencias fijadas en `tak-requirements.txt`.
2. **Interfaz:** descarga la UI 1.7.5 y comprueba su sha256.
3. **Base de datos y colas:** crea la base `bricohams_tak` en PostgreSQL y RabbitMQ en loopback.
4. **Usuario:** crea el usuario TAK con `hash_password()`. La contraseña se guarda solo en `/etc/bricohams/tak-access.txt`, con permisos 600.
5. **Servicios:** crea `bricohams-tak`, `bricohams-tak-cot`, `bricohams-tak-ssl` y `bricohams-tak-fw`.
6. **Red:**
   - nginx publica 8445 (UI), 8446 (enrollment) y 8447 (Marti mTLS); 8089 es CoT mTLS. 8443 sigue siendo de Meshtastic.
   - La tabla nft `bricohams_tak` bloquea desde fuera 4369, 5672, 15672, 25672, 5432 y 8081.
   - Los puertos TAK se añaden a `BLINDAJE_PUERTOS_LAN`: solo la red local.

**Alternativa descartada:** el instalador oficial de OTS. Borra los sites de nginx, ocupa 443/8443 (rompería OpenWebRX+ HTTPS y Meshtastic) y usaría Python 3.13 (fallo de gevent).

### 3.7 `tools/activar_mapa_local.sh`

Despliega el plugin, la API y el chat en una instalación existente sin reinstalar todo:

1. **Copia de seguridad:** guarda antes una copia en `/var/backups/bricohams-mapa-FECHA/` (readsb, `.env`, binarios, `init.js` y `settings.json`).
2. **readsb:** cambia el `--device` de readsb a `SERIAL_ADSB`, o al serie que se le pase:
   - valida el formato;
   - si no hay exactamente un `--device`, se niega a modificar nada.
3. **Ficheros:** instala la API, `bricohams-rak-aprs`, `bricohams-mesh-admin` y el plugin.
4. **Chat:** aplica `--lora --chat` a `settings.json`.
5. **Reinicio:** reinicia solo readsb, la API, rak-aprs, mesh-admin y openwebrx.
6. **Verificación de RadarBox:**
   - `/etc/rbfeeder.ini` tiene el mismo sha256 que antes;
   - `mlat-client` sigue en marcha;
   - la API de aviones responde.

   Si algo falla, termina con error.

### 3.8 `tools/datos.py` y `docs/DATOS.md`

Añaden los puertos 8445, 8089, 8446 y 8447 (LAN) y 8081, 5432 y 5672 (loopback) a la tabla de puertos, para que el inventario refleje la realidad.

## 4. Pruebas

Las pruebas se ejecutan en la Pi (`tests/run_tests.sh`), con el Python real del sistema. Todas pasan:

- `tests/test_live_map.py`: ADS-B, APRS-IS, chat y flags MQTT;
- `tests/test_mesh_admin.py`: incluye el endpoint TAK;
- el resto de la batería de la v4.5, sin regresiones.

Además se verificó en vivo:

- `/bricohams/api/aviones` devuelve aviones reales;
- el endpoint TAK da 401 sin sesión;
- los mensajes APRS aparecen en el chat;
- rbfeeder y mlat-client siguen enviando a RadarBox (`mlat1.rb24.com:40900`).

## 5. Marcha atrás

| Qué | Cómo |
|---|---|
| Chat APRS | `RAK_OWRX_CHAT=no` en `bricohams.env` y reiniciar `bricohams-rak-aprs` |
| Mapa en vivo | Quitar `Plugins.load('bricohams_live');` de `plugins/map/init.js`, o restaurar la copia de `/var/backups/bricohams-mapa-*` |
| TAK | `systemctl disable --now bricohams-tak bricohams-tak-cot bricohams-tak-ssl bricohams-tak-fw` y borrar `/etc/nginx/sites-enabled/bricohams-tak.conf` (luego `nginx -t` y recargar nginx) |
| readsb | Volver a `--device 00001090` (no se recomienda: ese dongle no existe) |

## 6. Ficheros excluidos del ZIP

- `bricohams.env`: tiene el passcode APRS-IS, las PSK y las URL privadas de Meshtastic. Se incluye `bricohams.env.example`.
- Carpetas `.vscode`, `__pycache__` y ficheros `*.pyc`.
- Credenciales de servidor y herramientas de sesión: nunca forman parte del repositorio.
