# Despliegue en la estación de EA5KAO · 11/10/2026

Informe de lo que se hizo en la Pi de OpenWebRX+ (`192.168.1.50`, usuario `<usuario>`) para:
- pasar el kit de v4.3 a v4.5;
- grabar el RAK4631;
- integrar Meshtastic y LoRa APRS con OpenWebRX+.

Todo se hizo por SSH. No se escribe ninguna clave en este documento.

## 0. Requisitos del encargo
1. Revisar todo el repositorio y comprobar que no hay errores.
2. Cargar el firmware del RAK4631 en remoto.
3. Integrar Meshtastic en la web.
4. Que el RAK mande a APRS solo la información del nodo y el log.
5. **La configuración de Meshtastic nunca puede estar en la web principal**: solo en Ajustes (`/settings`, con contraseña), para el nodo 433 (LilyGO) y el HAT 868.
6. Usar el `bricohams.env` facilitado por EA5KAO.
7. Documentar todos los pasos.

## 1. Revisión del código
- Leído el repositorio entero: `install.sh`, `files/bin/*`, plugins, nginx, firmware, pruebas y docs.
- En la revisión estática no salió ningún fallo bloqueante. Los dos fallos reales del RAK salieron al probar con el hardware (apartado 5).
- Pruebas ejecutadas en la Pi: `tests/test_rak_aprs.py` (incluye la lógica del firmware compilada con g++) y `tests/test_mesh_admin.py`. **Pasan.**

## 2. Actualización del kit v4.3 → v4.5
- Copia de seguridad del kit anterior: `/home/<usuario>/bricohams-sdr.v43-backup-20261011-141629`.
- Subido el kit v4.5 a `/home/<usuario>/bricohams-sdr`, con los finales de línea CRLF quitados.
- **Env:** se fusionó el `bricohams.env` de EA5KAO con el de la Pi. Se conservan las credenciales que ya había en el servidor (APRS-IS, Telegram, DuckDNS, contraseñas). Copias del env anterior en `/home/<usuario>/bricohams-backups/`.
- `sudo bash install.sh --actualizar`. El log está en `/home/<usuario>/bricohams-backups/install-v45.log`.

## 3. Meshtastic solo en /settings (ADR-53)
- Nuevo servicio **`bricohams-mesh-admin`** (127.0.0.1:8076). nginx lo publica en `/settings/bricohams/meshtastic`:
  - forzado a HTTPS (`SSL_MODO=admin`);
  - cada petición se valida con la sesión de admin de OpenWebRX+; sin sesión → `/login`;
  - formularios con token CSRF y comprobación de origen;
  - no enseña PSK.
- Botones **«Meshtastic 433 / 868»** y **«APRS (RAK)»** en la página de Ajustes de OpenWebRX+.

### Corrección: el botón no salía en Ajustes
- Al principio el botón se metía con un `sub_filter` de nginx. EA5KAO entra **directo a `http://192.168.1.50:8073`**, que no pasa por nginx, así que no lo veía. En los logs de nginx solo había mis peticiones.
- Ahora `bricohams-owrx-botones` lo pone en la propia plantilla `/usr/lib/python3/dist-packages/htdocs/settings.html`:
  - es idempotente, con marcas `<!-- bricohams-botones -->`;
  - OpenWebRX+ lee la plantilla en cada petición, así que no hace falta reiniciarlo;
  - entrando por :8073, los enlaces pasan a `https://IP/settings/bricohams/…`.
- Gancho `/etc/apt/apt.conf.d/99bricohams-owrx-botones`: lo vuelve a aplicar después de cada apt. Se quita el `sub_filter` de nginx.
- Nueva página **«APRS (RAK)»** (`/settings/bricohams/aprs`): estado del RAK, registro de paquetes oídos y reinicio de la pasarela. Sin sesión → `/login` (comprobado: 302).
- **Seguridad:** había una IP externa conectada directa a :8073. El router parece reenviar 8073 a internet, y ahí la contraseña de admin viaja **sin cifrar**. Recomendado: cerrar ese reenvío y publicar solo 80/443 (nginx, HTTPS).

### LED rojo del RAK
Es el LED de carga (CHG) de la base RAK19007, que va por hardware y está fijo con USB sin batería. El firmware solo maneja el verde (RX) y el azul (TX) (`board_pinout.h`). El RAK funciona: EA5KAO-15, radio ok en 433,775, paquetes oídos y subidos a APRS-IS.
- Desde ahí se configuran los nodos 433 y 868 (nombre, rol, URL de canales, canal privado) y qué sale en el mapa. Se guarda en los dos `bricohams.env`.
- **Cliente web oficial de Meshtastic en :8443:** para el nodo 868 (HAT), solo desde Ajustes con la sesión de admin. El servidor interno mechtasticd (:9443) está protegido por nftables (firewall del host).
- **Quitada la web de meshtasticd (9443)** que no pedía contraseña; **sustituida por :8443** con autenticación de OpenWebRX+ (nginx).

### Hallazgo en nginx
- La Pi tenía un site antiguo `/etc/nginx/sites-enabled/openwebrx` marcado como `default_server`. Las peticiones por IP se lo saltaban todo: HTTPS, `/settings` protegido y cabeceras.
- `install.sh` (`escribir_nginx`) ahora desactiva cualquier otro `default_server` y guarda copia en `/etc/bricohams/nginx-desactivados/`. Log: `install-web-fix.log`.
- Comprobado tras el cambio:

| Petición | Resultado |
|---|---|
| `http://…/settings` | 301 → HTTPS |
| `/settings/bricohams/meshtastic` sin sesión | 302/303 → `/login` |
| accesos indebidos | 403 |

## 4. RAK4631: de RUI3 a WisBlock y firmware BricoHams
El RAK venía con **RUI3** de fábrica (USB `1915:521f`). Su bootloader no admite el `.zip` de Adafruit. Con autorización de EA5KAO se cambió el bootloader. Paquetes y logs en `/home/<usuario>/bricohams-backups/rak-bootloader/`.

1. Bajados de RAKwireless (`downloads.rakwireless.com/RUI/RUI3/Bootloader Upgrade/`): `rak4631_factory_bootloader.zip`, `rak4631_factory_softdevice.zip` y `rak4631_factory_application.zip`. Sus SHA256 están en `SHA256SUMS.rak`.
2. Instalado **nrfutil 6.1.7** de Nordic en `/opt/bricohams/nrfutil-venv`:
   - pide Python < 3.11 y la Pi tiene 3.13, así que se instaló con `--ignore-requires-python --no-deps` y las dependencias a mano;
   - `pc_ble_driver_py` no existe para aarch64 y solo sirve para BLE. Se puso un paquete vacío con `NordicSemiException` e `IllegalStateException`.
3. Se mandó `AT+BOOT`. Si tarda, el bootloader RUI3 vuelve solo a la aplicación y hay que repetirlo.
4. `nrfutil dfu usb-serial -pkg rak4631_factory_bootloader.zip -p /dev/ttyACM0`: «Device programmed». Ahora es `239a:0029` «WisBlock RAK4631» y aparece la unidad UF2. Log: `nrfutil-bootloader.log`.
5. `adafruit-nrfutil dfu serial` con el softdevice y luego con el firmware BricoHams (`--singlebank`): «Device programmed» las dos veces. Log: `sd-app.log`.
6. Ahora es `239a:8029`, serie `12BBD0DD66D396C9`.
7. `sudo bricohams-dispositivos identificar` crea las reglas udev:
   - `/dev/rak-aprs` → ttyACM0;
   - `/dev/lilygo-mesh` → ttyACM1 (CH9102, serie 591B033753).
8. Activado `bricohams-rak-aprs`: conectado a APRS-IS (`rotate.aprs2.net:14580`) como **EA5KAO-15**.

`sudo bricohams-rak-aprs prueba`:
- firmware BricoHams-RAK-APRS 1.0.0;
- radio ok · 433,775 MHz · TX sí;
- sensor BME680 (RAK1906): 27,5 °C, 35 %;
- GPS presente, sin fix (dentro de la caja);
- paquetes recibidos y subidos.

APRS solo recibe lo del nodo: baliza, estado, telemetría de la caja y las estaciones oídas (log) con las reglas de iGate. No se publica ninguna configuración.

## 5. Fallos encontrados y corregidos
| Fallo | Efecto | Corrección |
|---|---|---|
| El firmware manda `"vbat": nan` sin batería, aunque compruebe `isnan()` en el hardware real | JSON inválido: `prueba` se caía y el servicio tiraba **todos** los STATUS (sin `/run/bricohams-rak/rak-aprs.json` ni temperatura de la caja para los ventiladores) | Pi: `json_rak()` convierte nan/inf en `null` (CONF, STATUS, RX, `prueba`). Firmware: `medidaValida()` por rangos en `statusJson()` y en la telemetría |
| `grabar()` se fiaba del código de salida de `adafruit-nrfutil`, que devuelve 0 aunque falle | daba por grabado un RAK que no lo estaba | exige «Device programmed» en la salida |
| RAK con RUI3 no reconocido | `grabar` fallaba sin explicación | `bricohams-dispositivos` lo marca `rak-rui3` (`1915:521f`); `grabar` se para con instrucciones |
| nginx: site antiguo `default_server` | se saltaba HTTPS y la protección de /settings | apartado 3 |

Pruebas nuevas en `tests/test_rak_aprs.py` (nan, `json_rak`, `grabar` con y sin «Device programmed», RUI3) y `tests/test_mesh_admin.py`.

**Pendiente:** recompilar el firmware con `bash tools/compilar_rak.sh` (necesita arduino-cli, BSP RAK 1.3.3 e Internet) y volver a grabar. Mientras tanto la Pi tolera el `nan` del 1.0.0.

## 6. Estado final (`sudo bricohams-check`: 72 bien · 16 avisos · 14 fallos)
**Funciona:**
- RAK: servicio activo, `/dev/rak-aprs`, radio ok, caja con BME680, APRS-IS conectado.
- LilyGO 433:
  - `/dev/lilygo-mesh`, EU_433, LONG_FAST, 10 dBm, 7 canales;
  - firmware Meshtastic 2.7.19, hw TLORA_V2_1_1P6;
  - 4 nodos, los 4 en el mapa.
- MQTT local:
  - llega `mesh433/Meshtastic`;
  - `lora433/APRS` se publica con cada paquete que oye el RAK;
  - OpenWebRX+ escucha con `mqtt_aprs` y `mqtt_meshtastic`.
- nginx, Let's Encrypt (83 días), `/settings` → HTTPS, mosquitto, visitas, Telegram, copias, plugins.

**Los 14 fallos son hardware que aún no está instalado** (`HARDWARE_PENDIENTE`):
- HAT 868 (meshtasticd no arranca sin radio; `mesh868: sin conexión` es normal);
- RTC;
- Pico de ventiladores;
- cámara/MediaMTX;
- estación WX (`bricohams-wx`, RS485);
- readsb (FlightStick).

## 7. Decisiones pendientes de EA5KAO
1. **Probar el botón «Meshtastic 433 / 868»** en Ajustes con tu usuario de admin. No tengo tus credenciales de OpenWebRX+, así que solo se comprobó la redirección sin sesión.
2. **El LilyGO no tiene exactamente la configuración del env:**
   - se llama «lorqui 433» (el env dice *EA5KAO BricoHams 433* / BH43);
   - su URL de canales tiene 7 canales y la del env 8.

   No se ha tocado para no pisar tu configuración. Si quieres la del env: panel → Nodo 433, o `sudo bricohams-lilygo meshtastic`.
3. **Números de serie de los RTL-SDR:**
   - los enchufados son `00000401` y `00000001`;
   - el kit espera `00000101` (HAT), `00000102` (Mini), `00000103` (V3) y `00001090` (ADS-B).

   Dime qué dongle es cada uno antes de `sudo bricohams-sdr-serials --grabar`, porque escribe la EEPROM.
4. **Varnish (6081)** ya no lo usa nadie: se puede desactivar.
5. **API meshtasticd 4403** sin contraseña en la LAN (lo normal en Meshtastic). No abrirla en el router.
6. **Blindaje:** `sudo bricohams-blindaje auditar` da nota 0/100 (4 altos). Revísalo aparte.

## 8. Ficheros del kit modificados
- `files/nginx/bricohams-sdr.conf.tmpl` (Meshtastic Web :8443)
- `files/bin/bricohams-rak-aprs`
- `files/bin/bricohams-rak-aprs`
- `files/bin/bricohams-dispositivos`
- `files/bin/bricohams-check`
- `files/bin/bricohams-servicios`
- `files/nginx/bricohams-sdr-rutas.conf`
- `files/web/index.html.tmpl`
- `install.sh`
- `firmware/rak4631-lora-aprs/{sensor_utils.h, bricohams_rak_aprs.cpp, aprs_utils.cpp}`
- `tests/test_rak_aprs.py`, `tests/test_mesh_admin.py` (nuevo), `tests/run_tests.sh`
- Documentación:
  - `CHANGELOG.md`;
  - manuales 23 y 35;
  - `ARQUITECTURA.md` (ADR-53);
  - `DATOS.md`;
  - `HARDWARE_Y_GPIO.md`;
  - `firmware/rak4631-lora-aprs/LEEME.md`;
  - este informe.
