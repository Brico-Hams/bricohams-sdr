# 22 · Estación meteorológica APRS con firmware LoRa (CA2RXU) en un LilyGO

<!-- guia-visual:inicio -->
> **Ruta visual:** [Meteorología, BME280, viento/lluvia y Pico IO](../GUIA_VISUAL_MODULOS.md#wx).
> Consulta allí requisitos, ilustración, cuadro de instalación, comprobaciones y restauración.
> Los comandos de este manual se ejecutan en Bash en la Pi; revisa el backup antes de cambiarla.
<!-- guia-visual:fin -->

**Qué es:** la estación **N0CALL-14** es un tercer LilyGO T3 V1.6.1 (433 MHz) con el firmware **LoRa_APRS_Wx_Station** de CA2RXU. Lee BME280, viento RS485 y pluviómetro, y **emite el paquete WX por LoRa a 433,775 MHz**. Lo recoge el iGate (N0CALL-10) y lo sube a APRS-IS.

**Para qué sirve:** como estación aislada (solo con batería o panel solar, lejos de la caja) o como respaldo si la Pi se para.
- Con la Pi en marcha, la estación principal sigue siendo **N0CALL-13** (manuales 06, 19 y 20).
- ⚠ **El bus RS485 solo admite un maestro:** los sensores de viento van a la Pi **o** al LilyGO, nunca a los dos.

Fuente de los datos: el repositorio y el código del firmware (`platformio.ini` y `src/boards_pinout.h`), revisados en octubre de 2026 ([enlace](https://github.com/richonguzman/LoRa_APRS_Wx_Station)).

## 1. Material
| Artículo | Cant. | Nota |
|---|---|---|
| LilyGO T3 V1.6.1 433 MHz (SX1278) | 1 | entorno PlatformIO `ttgo-lora32-v21` |
| Antena 433 con SMA | 1 | — |
| BME280 (I2C, 3,3 V) | 1 | en una garita |
| Módulo **TTL↔RS485 con control de dirección automático** | 1 | el firmware **no maneja DE/RE**: un MAX485 «pelado» no sirve |
| Anemómetro y veleta RS485 Modbus (10–30 V) + fuente de 12 V | 1 + 1 | los mismos del manual 19 |
| Pluviómetro de reed | 1 | — |
| Cable de puente (jumper) | 1 | solo para cambiar la dirección de la veleta |

## 2. Pines del T3 V1.6.1 con este firmware
| Función | GPIO del LilyGO | Conexión |
|---|---|---|
| I2C SDA | **21** | BME280 SDA (compartido con la pantalla OLED) |
| I2C SCL | **22** | BME280 SCL |
| 3,3 V / GND | 3V3 / GND | BME280 VIN / GND |
| RS485 RX (UART1) | **34** | RO/TXD del módulo RS485 |
| RS485 TX (UART1) | **4** | DI/RXD del módulo RS485 |
| Pluviómetro | **15** | un hilo del reed (el otro a GND). Pull-up interno; antirrebote de 50 ms por programa |
| Buscar la dirección del sensor | **13** | puente a 3,3 V **al arrancar** |
| Cambiar la dirección a 0x02 | **14** | puente a 3,3 V al arrancar |
| LED | 25 | — |
| Bus RS485 | — | A+ amarillo, B− azul, +12 V marrón, GND negro (sensores) |

**Avisos:**
- **GPIO 13, 14 y 15 son los de la tarjeta SD** del T3: no uses la SD.
- **GPIO 15 decide el arranque:** si el pluviómetro está cerrado al encender, desconéctalo y vuelve a probar.
- El firmware declara el reset de la radio en el GPIO 14, pero en el T3 V1.6 es el 23. Normalmente arranca igual. Si el LoRa no responde, quita el puente de GPIO 14.

## 3. Grabar el firmware (desde la Pi, el camino corto)
1. Rellena en `bricohams.env`:
   ```
   WXLORA_CALLSIGN="N0CALL-14"   WXLORA_POWER="17"   WXLORA_BME280="yes"
   WXLORA_WIND="yes"             WXLORA_RAIN="yes"   WXLORA_COMMENT="WX LoRa BricoHams"
   ```
2. **Si este LilyGO hace de estación:** pon `WIND_ENABLE="no"` y `RAIN_ENABLE="no"` (el bus RS485 tiene un solo maestro) y lanza `sudo bash install.sh --solo sensor`.
3. Conecta **solo** ese LilyGO por USB y ejecuta:
   ```bash
   ls /dev/ttyUSB* /dev/ttyACM*
   sudo bricohams-lilygo wxstation /dev/ttyUSB0
   ```
   - **Qué hace el script:**
     - descarga el firmware;
     - escribe `data/wxStation_conf.json` con tus datos;
     - compila con PlatformIO (`pio run -e ttgo-lora32-v21 -t upload`);
     - **sube el sistema de ficheros** (`-t uploadfs`). Sin ese paso el LilyGO se reinicia en bucle.
   - **Tiempo:** la primera vez tarda 10–15 min.

## 4. Grabarlo desde un PC (alternativa)
1. Instala VS Code con la extensión PlatformIO y clona `https://github.com/richonguzman/LoRa_APRS_Wx_Station`.
2. Edita `data/wxStation_conf.json`:
   - `callsign`
   - `beacon.latitude` y `beacon.longitude` (grados decimales)
   - `beacon.comment`, `interval: 10`, `path: "WIDE1-1"`
   - `lora.txFreq: 433775000`, `spreadingFactor: 12`, `signalBandwidth: 125000`, `codingRate4: 5`, `power: 17`
   - `sensors.bme280Active`, `windSpeedActive`, `windDirectionActive`, `rainActive` y `bme280HeightCorrection` (altitud en m)
3. En PlatformIO, con el entorno `ttgo-lora32-v21`: **Upload** y después **Upload Filesystem Image**.

## 5. Dirección Modbus de la veleta (una vez)
Los dos sensores salen de fábrica con la dirección **0x01**. El firmware lee el **anemómetro en 0x01** y la **veleta en 0x02**.
1. Conecta **solo la veleta** al bus RS485.
2. Pon el puente de **GPIO 14 a 3,3 V** y enciende. El firmware escribe la dirección 0x02 (función 06, registro 0x07D0).
3. Apaga, quita el puente y comprueba la dirección con el puente en **GPIO 13**: la pantalla muestra la dirección encontrada.
4. Conecta también el anemómetro y arranca sin puentes.

(Desde la Pi se hace lo mismo con `sudo bricohams-wx --rs485-direccion 1 2`, manual 19.)

## 6. Comprobación
- **Pantalla del LilyGO:** temperatura, presión, viento y lluvia.
- **Unidades:** el firmware manda la temperatura en °F, como pide el formato APRS.
- **Que llegan los paquetes:**
  - en la web del iGate (`http://<IP del iGate>/`) deben aparecer los de N0CALL-14 cada 10 min;
  - en **aprs.fi → N0CALL-14 → Weather**, las gráficas.
- **Alcance:** con 17 dBm y SF12 sobran varios km hasta el iGate. Si no llega, sube a 20 dBm (`WXLORA_POWER`).
