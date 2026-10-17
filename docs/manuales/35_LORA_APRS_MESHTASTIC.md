# 35 · iGate LoRa APRS en un RAK4631 y Meshtastic 433/868, dentro de OpenWebRX+ (v4.5)

<!-- guia-visual:inicio -->
> **Ruta visual:** [Meshtastic HAT y LilyGO; puente al mapa](../GUIA_VISUAL_MODULOS.md#mesh).
> Consulta allí requisitos, ilustración, cuadro de instalación, comprobaciones y restauración.
> Los comandos de este manual se ejecutan en Bash en la Pi; revisa el backup antes de cambiarla.
<!-- guia-visual:fin -->

![LoRa APRS y Meshtastic en OpenWebRX+](../esquemas/25_lora_owrx.png)

### Acceso administrativo y error 429

Si caduca la sesion, las consultas API de los clientes 8443/8444 deben
recibir **401**, no redirigir al login en cada sondeo. Solo la navegacion
al cliente redirige al acceso. El limite de login se mantiene en 12 POST
por minuto e IP; abrir el formulario mediante GET no consume ese limite.
No desactivar la autenticacion ni ampliar el limite para ocultar el problema.

Para actualizar instalaciones anteriores: con backup verificado, ejecutar
`sudo bash tools/corregir-login-429.sh /ruta/kit-instalado`.
El script verifica y registra la copia y su restauracion, valida `nginx -t`
y recarga nginx sin reiniciar OpenWebRX ni cortar la grabacion.
Usa una zona nueva `bh_login_post` para no reutilizar la memoria compartida
con una clave distinta durante la recarga. Comprueba las APIs en ambos puertos:
`nginx -t` y el exito de `systemctl reload` por si solos no prueban la activacion.
Si la sesion caduco, entrar otra vez en Settings y reconectar el cliente.

| Aparato | Qué hace | Cómo se conecta | Nombre fijo |
|---|---|---|---|
| **RAK4631 WisBlock (L, 433 MHz)** en base RAK19007, con GPS (slot A) y sensor de temperatura | iGate y digipeater **LoRa APRS 433,775 MHz** · **N0CALL-15** · mide la temperatura de la caja | USB a la Pi (KISS) | `/dev/rak-aprs` |
| **LilyGO T3 V1.6.1 433** | nodo **Meshtastic EU_433** de la red (URL 433) · *SDR BricoHams 433* (SB43) | USB a la Pi | `/dev/lilygo-mesh` |
| **HAT SX1262 868** (en camino) | nodo **Meshtastic 868** de la red (URL 868) · *SDR BricoHams 868* (SB86) | SPI (meshtasticd) | 127.0.0.1:4403 |

**Integración directa con OpenWebRX+:** todo lo que oyen los tres aparece en el **mapa** de OpenWebRX+ (`/map`) igual que lo que decodifica él mismo. Además, OpenWebRX+ decodifica LoRa APRS y Meshtastic con sus SDR (marcadores 433,775 y 433,875; manual 2.4).

### Cliente oficial para ambos nodos

**Favoritos BricoHams:** la cabecera del cliente muestra siempre **Nodo 868 MHz**
y **Nodo 433 MHz**. Al pulsarlos, conecta o selecciona la radio en el propio
cliente, sin crear duplicados. Ambas APIs pasan por el mismo origen autenticado
(`/bricohams/nodos/868/api/` y `/bricohams/nodos/433/api/`): no requieren CORS ni
guardar claves en el navegador. El 433 muestra un error si el puente o el USB
no están disponibles; un favorito no implica que el dispositivo esté conectado.

La integración usa el ámbito del módulo oficial y sus tiendas/transportes,
por lo que está limitada al SHA-256 de **Web 2.6.7 ACFA7D2**. `bricohams-meshweb`
comprueba el original y crea un módulo nuevo; nunca reemplaza el bundle original.
Una versión desconocida detiene la activación en lugar de parchear nombres internos
a ciegas. Guarda y verifica el índice anterior, imprime su restauración y cambia
la referencia del índice a un nombre con hash nuevo para evitar caché antigua.
Al actualizar Meshtastic Web, hay que adaptar y volver a probar esta integración.
Pruebas: `test_meshweb.py`, `test_meshweb_favoritos.cjs` y navegador con el cliente real.

El cliente oficial guarda sus conexiones en cada navegador y origen; no hereda
las conexiones del mapa. Inicia sesión en `/settings` **en el mismo host** que
usarás para Meshtastic (no mezcles IP y dominio).

- **868:** `https://<host>:8443/`, API de meshtasticd.
- **433:** `https://<host>:8444/`, requiere `MESH_WEB="yes"` y
  `MESH433_WEB="yes"` en la configuración real del kit y de `/etc/bricohams`.
  Sin `MESH433_WEB`, las instalaciones anteriores conservan la serie directa.
- En cada página: **New Connection → HTTP → Connect**, dejando el host y puerto
  propuestos y HTTPS activo. Los canales se descargan del nodo, no se inventan
  ni se cambian sus claves. Escribe y envía solo al canal seleccionado.
- Alternativa unificada: `/settings/bricohams/meshtastic/chat`, con una columna
  por radio y sus canales reales.

El instalador configura `bricohams-mesh-puente` como único dueño del USB 433.
Ofrece TCP `127.0.0.1:4404` al mapa/panel y HTTP `127.0.0.1:4480` al proxy
autenticado de nginx. No abras 8443/8444 en el router ni expongas 4480/4404.
Usa una sesión del cliente oficial por radio: su cola HTTP es compartida.
El historial del cliente oficial y el del panel BricoHams son independientes.

Antes de actualizar, crea y verifica una copia de los ejecutables afectados,
configuraciones reales, unidades systemd y sitio nginx; conserva un procedimiento
de restauración y los estados activo/habilitado de los servicios.
Tras instalar, comprueba `systemctl status bricohams-mesh-puente`,
`bricohams-mesh-puente estado` y `bricohams-mesh-owrx estado`: ambas fuentes
deben indicar conexión. `nginx -t` debe pasar antes de recargarlo.
La validación del desarrollo usa radio simulada y la biblioteca real;
no necesita enviar mensajes RF. No se da por desplegado hasta comprobar los
dos nodos reales y sus canales en el navegador.

## 1. Firmware del RAK4631: «BricoHams RAK APRS»
Es un **port de [LoRa_APRS_iGate](https://github.com/richonguzman/LoRa_APRS_iGate) de CA2RXU** (revisión `9314bf1`, 07/10/2026; licencia GPL-3.0) al nRF52840 del RAK4631. El original solo existe para ESP32 y hace la parte de Internet por WiFi; el RAK no tiene WiFi. Por eso (ADR-49):
- **en el RAK** se queda la radio, igual que en el original:
  - cabecera LoRa APRS `<\xff\x01`;
  - SX1262 con TCXO de 1,8 V y DIO2 como conmutador;
  - escucha antes de transmitir (CAD);
  - digipeater con la misma lógica (`digi_utils.cpp`);
  - KISS (`kiss_utils.cpp`, copiado sin cambios);
  - baliza, estado y telemetría;
- **en la Pi** va lo que el original hace por WiFi: subir a APRS-IS, bajar mensajes a RF, la configuración (en vez de su web) y el estado.

| Fichero | De dónde sale |
|---|---|
| `kiss_utils.cpp/.h`, `kiss_protocol.h` | original, sin cambios |
| `lora_utils.cpp` | adaptado: SPI propio (NRF_SPIM2) con los pines internos del RAK4630 |
| `digi_utils.cpp` | adaptado: modos 1-3 y búfer de duplicados de 25 s |
| `configuration.cpp` | nuevo: JSON en la flash interna (LittleFS), escrito por la Pi |
| `aprs_utils.cpp` | nuevo: baliza sin comprimir, estado, ambigüedad, telemetría PARM/UNIT/EQNS/BITS |
| `sensor_utils.cpp` | nuevo: GPS NMEA, RAK1901 SHTC3, RAK1906 BME680, BME280, temperatura interna del nRF52840 y batería |

**Binarios** en `firmware/rak4631-lora-aprs/bin/`, con `SHA256SUMS`:
- `.zip`: DFU por USB;
- `.uf2`: arrastrar y soltar;
- `.hex`: programador SWD.

Compilados con el BSP de RAKwireless 1.3.3 y RadioLib 7.6.0 (`tools/compilar_rak.sh` lo repite en cualquier PC). Ocupan 219 KB de 815 KB.

### Pines (RAK4631 sobre RAK19007)
| Función | Pin del nRF52840 | Nº Arduino |
|---|---|---|
| SX1262 NSS · SCK · MOSI · MISO | P1.10 · P1.11 · P1.12 · P1.13 | 42 · 43 · 44 · 45 |
| SX1262 RESET · BUSY · DIO1 | P1.06 · P1.14 · P1.15 | 38 · 46 · 47 |
| Alimentación del conmutador de antena | P1.05 | 37 |
| 3V3_S (GPS y sensores de los slots) = WB_IO2 | P1.02 | 34 |
| GPS slot A (RAK1910 / RAK12500), NMEA 9600 | P0.15 RX · P0.16 TX (Serial1) | 15 · 16 |
| I2C de los slots | P0.13 SDA · P0.14 SCL | 13 · 14 |
| LED verde (RX) · LED azul (TX) | P1.03 · P1.04 | 35 · 36 |
| Batería (divisor ×1,73) | P0.05 / AIN3 | 5 |

### Protocolo por el USB
| Dirección | Trama | Contenido |
|---|---|---|
| RAK → Pi | KISS 0x00 | cada paquete oído por RF y los propios (baliza, estado, telemetría) |
| Pi → RAK | KISS 0x00 | lo que hay que transmitir (mensajes de APRS-IS), solo con `RAK_TX="yes"` |
| Pi → RAK | KISS 0x06 `BH:…` | `PING`, `GET`, `CONF?`, `CFG {json}`, `BEACON`, `REBOOT`, `DFU`, `UF2` |
| RAK → Pi | KISS 0x06 `BH:…` | `PONG`, `STATUS {json}` (cada 60 s), `CONF {json}`, `CFGOK`, `CFGERR`, `RX {rssi,snr}`, `LOG` |

Cualquier programa KISS (Direwolf, APRX, Xastir) puede usar el RAK: las tramas 0x06 las ignora.

## 2. Configuración clonada del iGate actual (192.168.1.142)
Leída de su `/configuration.json` el 11/10/2026; en `bricohams.env` (personal):

| iGate LilyGO (N0CALL-10) | RAK4631 | Variable |
|---|---|---|
| callsign N0CALL-10 | **N0CALL-15**. «N0CALL-SDR» no vale: en RF el SSID es un número de 0 a 15 y en APRS-IS caben 9 caracteres | `RAK_CALLSIGN` |
| 433,775 · SF12 · BW 125 · CR 4/5 · 20 dBm · TX y CAD activos | igual | `RAK_TX="yes"`, `RAK_POWER="20"` |
| baliza cada 15 min por RF y APRS-IS, «LoRa APRS igate», símbolo `L` + `a`, ruta WIDE1-1,WIDE2-1, ambigüedad 1 | igual, + `Caja 23.4C` al final del comentario | `RAK_BEACON_MIN`, `RAK_BEACON_RF`, `RAK_COMMENT`, `RAK_SYMBOL="La"`, `RAK_PATH`, `RAK_AMBIGUEDAD="1"` |
| estado «N0CALL-tu QTH-IGate» | «N0CALL-SDR BricoHams iGate» | `RAK_STATUS` |
| digipeater WIDE1-1 automático | **`auto`** (v5.0): el RAK repite solo cuando el iGate LilyGO (`RAK_DIGI_VIGILA`, por defecto `IGATE_CALLSIGN`) lleva `RAK_DIGI_AUTO_MIN` (30) minutos sin oírse, ni como origen ni repitiendo (`N0CALL-10*`); cuando vuelve, el RAK deja de repetir. Dos digis de relleno en el mismo sitio repetirían dos veces cada paquete. Fijos: `0` apagado, `1` WIDE1-1, `2` + WIDE2-n, `3` solo vía nuestro indicativo | `RAK_DIGI` |
| APRS-IS rotate.aprs2.net · filtro m/10 · mensajes a RF | igual (objetos a RF: no) | `RAK_APRSIS_SERVER`, `RAK_APRSIS_FILTRO`, `RAK_MENSAJES_RF` |
| recordar estaciones 30 min | igual | `RAK_RECORDAR_MIN` |
| syslog y MQTT a link9.net | no: el RAK publica en el MQTT **local** para OpenWebRX+ | — |

> **Aviso de seguridad del iGate viejo:** su web no tiene usuario (`webadmin.active=false`). Cualquiera en tu red puede leer en `/configuration.json` la **contraseña de la WiFi** y el passcode APRS. Activa `webadmin` con una contraseña en su web, o apágalo cuando el RAK funcione.

## 3. Procedimiento en la Pi (paso a paso)
**Antes:** por SSH desde casa (`ssh pi@192.168.1.50`); el RAK y el LilyGO enchufados al hub USB; sus antenas puestas. **Nunca transmitas sin antena.**

1. Kit y servicios al día:
   ```bash
   cd ~/bricohams-sdr && git pull
   sudo cp /ruta/a/tu/bricohams.env ./bricohams.env      # el personal (no va en el git)
   sudo bash install.sh --actualizar
   ```
   Esto instala `bricohams-rak-aprs`, `bricohams-mesh-owrx`, `bricohams-dispositivos`, `bricohams-mesh-url`, `bricohams-banner`, mosquitto local, `adafruit-nrfutil`, `esptool` y los decodificadores LoRa de OpenWebRX+. También activa `mqtt_aprs` y `mqtt_meshtastic`.
2. **Qué hay enchufado:**
   ```bash
   sudo bricohams-dispositivos
   ```
   El HAT, el Mini y el SDRplay salen «en camino» (`HARDWARE_PENDIENTE`), no como fallo.
3. **Grabar el RAK4631:**
   ```bash
   sudo bricohams-rak-aprs grabar
   ```
   - Usa DFU por USB y tarda unos 40 s. Solo vale si el RAK tiene el **bootloader WisBlock/Adafruit** (USB `239a:xxxx`, como los que traen Meshtastic o Arduino).
   - `grabar` solo da el trabajo por bueno si `adafruit-nrfutil` dice «Device programmed». Ese programa devuelve 0 aunque falle.
   - **Si falla:** pulsa RESET dos veces; aparece la unidad `RAK4631`. Copia en ella `firmware/rak4631-lora-aprs/bin/bricohams-rak4631-lora-aprs.uf2` (desde la Pi: `sudo mount /dev/sdX /mnt && sudo cp …uf2 /mnt/`).
   - **RAK con RUI3 de fábrica** (USB `1915:521f`, contesta a comandos `AT`). Su bootloader no admite este firmware. `grabar` lo detecta y se para; `bricohams-dispositivos` lo marca como `rak-rui3`. Antes hay que pasarlo a WisBlock **una sola vez** (es lo que se hizo con el de N0CALL, ver `docs/DESPLIEGUE_N0CALL_2026-10-11.md`):
     1. Baja de RAK los paquetes `rak4631_factory_bootloader.zip`, `rak4631_factory_softdevice.zip` y `rak4631_factory_application.zip` (downloads.rakwireless.com → RUI/RUI3/Bootloader Upgrade) y guarda su SHA256.
     2. Instala `nrfutil` 6.1.7 de Nordic en un venv. En la Pi (Python 3.13, aarch64) necesita esto:
        - `pip install --ignore-requires-python --no-deps nrfutil==6.1.7`, con sus dependencias a mano;
        - un paquete vacío `pc_ble_driver_py` (`__init__.py` y `exceptions.py` con `NordicSemiException` e `IllegalStateException`). Solo hace falta para BLE y no existe para ARM.
     3. Manda `AT+BOOT` por el puerto (115200). El RAK entra en «DFU». Si tarda, vuelve solo a RUI3 y hay que repetirlo.
     4. `nrfutil dfu usb-serial -pkg rak4631_factory_bootloader.zip -p /dev/ttyACM0`. Pasa a `239a:0029` y aparece la unidad `RAK4631`.
     5. `adafruit-nrfutil --verbose dfu serial --package rak4631_factory_softdevice.zip -p /dev/ttyACM0 -b 115200`.
     6. `sudo bricohams-rak-aprs grabar`, o el `.zip` de la aplicación con `--singlebank`. Queda en `239a:8029`.
4. **Nombres fijos y prueba:**
   ```bash
   sudo bricohams-dispositivos identificar      # /dev/rak-aprs y /dev/lilygo-mesh por VID:PID y serie
   sudo systemctl restart bricohams-rak-aprs
   sudo bricohams-rak-aprs prueba
   ```
   Debe salir:
   - `firmware: BricoHams-RAK-APRS 1.0.0`;
   - `configuración: actualizada (…)` la primera vez y `al día` después;
   - `radio: ok · 433.775 MHz`;
   - la temperatura de la caja y el sensor (`SHTC3 (RAK1901)` o `BME680 (RAK1906)`);
   - el GPS.
5. **LilyGO Meshtastic 433.** Ya tiene Meshtastic (pantalla con el nombre del nodo). Para ponerlo al último estable conservando la configuración:
   ```bash
   sudo bricohams-lilygo firmware      # baja el oficial (tlora-v2-1-1_6), lo graba con esptool y lo configura
   ```
   O solo la configuración:
   ```bash
   sudo bricohams-lilygo meshtastic
   ```
   Aplica la URL de la red 433 (canales Murcia, Cartagena, Iberia, Alicante, Almería, SOS y el privado) y el nombre *SDR BricoHams 433* / SB43. El servicio del mapa suelta el puerto mientras tanto.
6. **HAT 868 (cuando llegue):**
   ```bash
   sudo bash install.sh --solo hat,meshtastic
   ```
   Aplica la URL 868: SFNarrow, 869,618 MHz, BW 62,5 kHz, SF7, 27 dBm, más el canal EA5RCZ. El nombre es *SDR BricoHams 868* / SB86. Hasta entonces, `bricohams-mesh-owrx` reintenta solo.
7. **Comprobar:**
   - `sudo bricohams-check`: apartados RAK4631, Mapa de OpenWebRX+ y Dispositivos;
   - el mapa en `https://sdr.example.org/map`;
   - en APRS: https://aprs.fi/#!call=N0CALL-15.

### Panel de administración Meshtastic (solo admin)
La configuración de Meshtastic **no está en la web pública**. Para verla:
1. Entra en `https://DOMINIO/settings` con la contraseña de administrador de OpenWebRX+.
2. Pulsa el botón **«Meshtastic 433 / 868»**, que lleva a `/settings/bricohams/meshtastic`, o **«APRS (RAK)»**, que lleva a `/settings/bricohams/aprs`.

Los botones los añade `bricohams-owrx-botones` a la plantilla `settings.html` de OpenWebRX+. Entra por `https://DOMINIO/settings`: tanto el receptor como los paneles pasan por nginx; el backend no se publica directamente. Tras un `apt upgrade` de openwebrx, el gancho `/etc/apt/apt.conf.d/99bricohams-owrx-botones` los vuelve a poner. Para quitarlos: `sudo bricohams-owrx-botones --quitar`.

**APRS (RAK)** enseña, en solo lectura:
- el estado del RAK4631: firmware, indicativo, radio y frecuencia, contadores, sensor, batería, GPS, APRS-IS y mapa;
- los últimos paquetes oídos.

Desde ahí solo se puede reiniciar `bricohams-rak-aprs`. El passcode y la baliza siguen en `bricohams.env`.

Qué se puede hacer:
- **Nodo 433 (LilyGO):** leer su estado real y cambiar nombre largo y corto, rol y URL de canales. El panel para y arranca solo `bricohams-mesh-owrx` para liberar el puerto.
- **Nodo 868 (HAT):** lo mismo por la API 127.0.0.1:4403, además del canal privado de `bricohams.env`. El rol se guarda en `MESH868_ROLE` (por defecto `CLIENT`; v5.0, antes este nodo no tenía selector de rol) y `install.sh --solo meshtastic` también lo aplica con `meshtastic --set device.role`.
  Para un nodo fijo en casa, Meshtastic recomienda `CLIENT` o `CLIENT_BASE`. `ROUTER` y `ROUTER_LATE` son solo para emplazamientos altos con buena cobertura, y se deben coordinar con la red local.
- **Mapa:** elegir qué se publica (`MESH433_OWRX`, `MESH868_OWRX`, `MESH_OWRX_CHAT`).

Los cambios se guardan en `bricohams.env` (el del kit y `/etc/bricohams/`), así que `install.sh --actualizar` no los deshace. Las claves (PSK) nunca se enseñan. Sin sesión de admin te lleva a `/login`. El servicio es `bricohams-mesh-admin` (127.0.0.1:8076).

La web antigua de meshtasticd (`https://IP:9443`) se ha quitado porque no pedía contraseña.

## Mensajes 433 / 868 desde el panel (v5.0)
`/settings/bricohams/meshtastic/chat` (botón **Mensajes** en el panel Meshtastic). Hay dos columnas, una por red:
- **433 (LilyGO)** y **868 (HAT)**: cada una con su estado (conectado, sin conexión o servicio parado), un formulario de envío y los últimos 80 mensajes (recibidos, directos a nosotros con la marca «directo», y los nuestros resaltados con «yo ↑»).
- **Envío:** eliges el canal (la lista sale de los canales reales del nodo) y escribes hasta 200 bytes; los caracteres de control se quitan. Si marcas «enviar también por la otra red», el mensaje sale por el canal **del mismo nombre** en la otra red o, si no lo hay, por su canal principal. Así sirve de pasarela manual entre las redes de nuestros nodos.
- **Sin JavaScript** (la CSP lo prohíbe): «Actualizar» recarga a mano y `?auto=1` recarga cada 20 s.

Funcionamiento:
- `bricohams-mesh-owrx` es el único que habla con cada nodo (el puerto USB y el 4403 solo admiten un cliente). Guarda el historial en `/run/bricohams-mesh/chat.json` (0600, en RAM, máximo 200 por red) y abre el socket `/run/bricohams-mesh/enviar.sock` (0600), al que solo llega `bricohams-mesh-admin` (root).
- El panel valida la red, el canal, la longitud, la sesión de admin, el origen y el CSRF antes de pedir nada al nodo.
- Mientras el panel lee o cambia la configuración de un nodo, `bricohams-mesh-owrx` está parado y el envío dice «el servicio no está en marcha».
- Requiere el mapa LoRa activo (`OWRX_MAPA_LORA="yes"`, que arranca `bricohams-mesh-owrx`). `MESH_CHAT="no"` lo desactiva.
- Los directos entre otros nodos no se ven (van cifrados para ellos); los que nos mandan a nosotros sí, solo en el panel y nunca en el chat público de OpenWebRX+.


## Cliente web oficial de Meshtastic (:8443, solo admin)
Si se instala con `MESH_WEB="yes"` (por defecto en v4.5):
- `https://IP:8443/` es el cliente web oficial de Meshtastic.
- Solo accesible desde la sesión de `/settings` de OpenWebRX+ (la cookie `owrx-session`).
- meshtasticd sirve su Webserver en `127.0.0.1:9443` sin contraseña, pero un cortafuegos (`bricohams-meshweb-fw`, nftables) lo bloquea desde fuera; nginx lo revierte a `:8443` con autenticación.
- El botón «Meshtastic Web (868)» sale en los **Ajustes** de OpenWebRX+.
- El nodo 868 (HAT) solo funciona una vez que meshtasticd detecta el SX1262; mientras tanto da "No sx1262 radio".
- **No abrir el 8443 en el router,** porque sería internet sin cifrar. Ni el 9443. El 8073 tampoco (manual 34).
- Sin sesión de admin: redirige a `/login?ref=settings`.

## 4. Integración con OpenWebRX+ (ADR-50)
OpenWebRX+ 1.2.122 y posteriores escuchan en su broker MQTT los temas `+/APRS`, `+/Meshtastic` y `+/CLIENT` (`owrx/mqtt.py`, `MqttSubscriber`). Pintan lo recibido en el mapa con su propio código: `AprsParser.updateMap` y `MeshtasticParser.updateMap`. Comprobado contra el código de OpenWebRX+ 1.2.126.

| Tema | Lo publica | Contenido |
|---|---|---|
| `lora433/APRS` | `bricohams-rak-aprs` | estación oída por el RAK: posición (normal, comprimida, objetos, con ambigüedad), símbolo, comentario + «LoRa 433,775 · RSSI · SNR» |
| `mesh433/Meshtastic` · `mesh868/Meshtastic` | `bricohams-mesh-owrx` | nodos con posición: nombre corto y largo, modelo, rol, batería, uso del canal, tiempo. Se republican cada 10 min para que no caduquen |
| `mesh433/CLIENT` | `bricohams-mesh-owrx` | solo con `MESH_OWRX_CHAT="yes"`: mensajes de canales **públicos** al chat de la web. Los directos nunca |

**Privacidad:**
- la posición de **nuestros** nodos va redondeada a `OWRX_GPS_DECIMALES` (manual 34);
- la de los demás va como la emiten ellos (con la precisión de su canal).

**Decodificación por SDR (además):**
- marcadores `📡 LoRa APRS 433,775` (modo *LoRa APRS*), `📶 Meshtastic 433 LongFast` y `📶 Meshtastic 868 SFNarrow`;
- *Meshtastic bandwidth* es un único ajuste global: 62,5 kHz para 868 SFNarrow (el del kit) o 250 kHz para 433/868 LongFast;
- el LoRa APRS siempre se decodifica (BW 125 fijo).

## 5. Problemas
| Síntoma | Qué hacer |
|---|---|
| `prueba`: «El RAK no contesta» | no tiene el firmware BricoHams: `sudo bricohams-rak-aprs grabar` |
| `grabar`: «tiene RUI3» / USB `1915:521f` | conversión a WisBlock (apartado 3, paso 3) |
| `prueba`: «estado ilegible» o `vbat: null` | firmware 1.0.0 sin batería: manda `nan` y la Pi lo convierte en `null`. Se corrige en el código fuente; hay que recompilar con `tools/compilar_rak.sh` |
| `grabar` no encuentra el puerto | enchufa solo el RAK (un `/dev/ttyACM*`) o usa el `.uf2` |
| `radio: error -2` | el SX1262 no responde: ¿es un RAK4631(**L**) de 433? ¿antena puesta? |
| `CFGERR frecuencia fuera de 410-525 MHz` | el RAK4631 normal es de 868-915: hace falta el (L) |
| Sensor «nRF52840 interno» | no hay RAK1901/RAK1906 en un slot: mide el módulo, no el aire (súmale `RAK_TEMP_OFFSET`) |
| GPS «sin fix» | dentro de la caja puede no ver el cielo: antena GPS activa fuera o `RAK_GPS_BALIZA="no"` (por defecto `yes`: con fix usa el GPS, sin fix `STATION_LAT/LON`) |
| LED **rojo** fijo en el RAK | es el LED de carga (CHG) de la base RAK19007, por hardware; el firmware no lo controla. Fijo con USB sin batería o cargando: normal. El firmware solo usa el verde (P1.03, parpadea al recibir) y el azul (P1.04, al transmitir). Compruébalo en Ajustes → «APRS (RAK)» o con `sudo bricohams-rak-aprs prueba` |
| No sale el botón Meshtastic/APRS en Ajustes | `sudo bricohams-owrx-botones` y Ctrl+F5 |
| Nada en el mapa | `systemctl status mosquitto bricohams-rak-aprs bricohams-mesh-owrx` · `sudo bricohams-check` · `mqtt_aprs`/`mqtt_meshtastic` en Ajustes → Integración |
| `mesh868: sin conexión` | normal sin HAT |
| `meshtastic --port /dev/lilygo-mesh` dice «ocupado» | `sudo systemctl stop bricohams-mesh-owrx` (lo hace solo `bricohams-lilygo`) |
| Duplicados en aprs.fi | dos digis: `RAK_DIGI="auto"` (o `"0"`) mientras funcione el LilyGO iGate. Estado en `/run/bricohams-rak/rak-aprs.json` → `digi_auto` y en el registro («digi auto: …») |
| No sale el tiempo (N0CALL-13) en aprs.fi | `systemctl is-active bricohams-wx`. Hasta la v5.0 `bricohams-io` y `bricohams-fan` llevaban `After=multi-user.target` y systemd quitaba `bricohams-wx` al arrancar («ordering cycle»); `sudo bash install.sh --solo io,sensor,ventilacion` lo corrige |
| El nodo 868 no tiene rol o aparece con uno equivocado | hasta v5.0 el kit no lo fijaba en el nodo 868. Elige el rol en Ajustes → Meshtastic → Nodo 868 y pulsa *Aplicar* (con `meshtasticd` activo). También puedes ponerlo en `MESH868_ROLE` y ejecutar `sudo bash install.sh --solo meshtastic` |
| El nodo sale con un nombre viejo (p. ej. «mi-qth») | el nombre se guarda en el propio nodo, no basta con cambiar `bricohams.env`. Ajusta `MESH_LONG_NAME`/`MESH_SHORT_NAME` (868) y `MESH433_LONG_NAME`/`MESH433_SHORT_NAME` (433) y pulsa *Aplicar* en Ajustes → Meshtastic (`bricohams-mesh-admin`, que llama a `meshtastic --set-owner`). El nodo 433 también se renombra con `sudo bricohams-lilygo`. Los vecinos tardan unos minutos en ver el nombre nuevo |

Decisiones: ADR-49 a ADR-52 en [ARQUITECTURA](../ARQUITECTURA.md). Pruebas: `tests/test_rak_aprs.py` (firmware compilado en el PC + pasarela + RAK y APRS-IS de mentira), `tests/test_mesh_owrx.py` y `tests/test_v45_dispositivos.py`.
