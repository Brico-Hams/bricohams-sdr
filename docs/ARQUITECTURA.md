# Decisiones de arquitectura

Registro de decisiones (ADR) de la estación BricoHams SDR. Cada una dice **qué** se decidió, **por qué** y **qué implica**. Los datos concretos (series, perfiles, puertos) están en [DATOS.md](DATOS.md). Los pines están en [HARDWARE_Y_GPIO.md](HARDWARE_Y_GPIO.md).

![Arquitectura](esquemas/01_arquitectura.png)

---

## ADR-01 · Raspberry Pi 5 con Raspberry Pi OS Lite 64 bits: Trixie (recomendado) o Bookworm
- **Decisión:** placa Raspberry Pi 5 con Raspberry Pi OS Lite arm64, sin escritorio.
  - **Debian 13 "Trixie"**: la imagen normal actual. Es la recomendada desde la v3.1.
  - **Debian 12 "Bookworm"**: la imagen *Legacy*.
  - El instalador detecta cuál es (`DEB`, `DEB_NUM`) y elige los repositorios de cada una.
- **Por qué:**
  - En la v3.0 el kit solo admitía Bookworm, porque la página del repositorio de OpenWebRX+ solo documenta Bullseye, Bookworm y Ubuntu.
  - Al probarlo en la Pi de N0CALL (Trixie) se comprobó que el repositorio de luarvique **sí publica `ppa/trixie`**: firmado, arm64, OpenWebRX+ 1.2.125 compilado para Python 3.13.
  - Meshtastic tiene `Debian_13` y AirNav tiene el repositorio `apt.rb24.com trixie`.
  - No hace falta regrabar una Pi que ya tiene Trixie.
- **Implica:**

  | Componente | Bookworm | Trixie |
  |---|---|---|
  | OpenWebRX+ | `luarvique.github.io/ppa/bookworm` | `luarvique.github.io/ppa/trixie` |
  | meshtasticd | OBS `Debian_12` | OBS `Debian_13` |
  | rbfeeder | `inst_rbfeeder.sh` | repositorio apt `apt.rb24.com trixie` |
  | mlat-client | apt | se **compila** de `mutability/mlat-client` (necesita `python3-pyasyncore`, porque Python 3.12+ ya no trae `asyncore`) |
  | Sensor I2C | `python3-smbus` | `python3-smbus`, o `python3-smbus2` como alternativa |
  | Driver RTL-SDR | `rtl-sdr-blog` compilado y retenido (`apt-mark hold`) | **rtl-sdr 2.0.2 de Debian** (osmocom), sin compilar ni retener (v3.3) |

  - **Por qué no se usa rtl-sdr-blog en Trixie (v3.3):**
    - El fork es la versión 0.7.0~rtlsdrblog1. Debian 13 trae librtlsdr0 2.0.2, que es más nueva, y los módulos SoapySDR de Trixie la exigen.
    - Mezclar las dos versiones rompe apt («rtl-sdr: Depends librtlsdr0 (= 0.7.0~rtlsdrblog1) but 2.0.2 is to be installed»).
    - La 2.0.2 de osmocom ya incluye lo que usa la estación: bias-tee (`rtlsdr_set_bias_tee`), muestreo directo del V3 y el R820T/R860.
    - Si quedó retenido el fork de una instalación anterior, el instalador lo cambia por el de Debian.
  - **El resto es igual:** readsb/tar1090 de wiedehopf, MediaMTX (admite Trixie y Bookworm), NetworkManager y `/boot/firmware/config.txt`.
  - `install.sh` se para con cualquier otra versión.
  - La Pi 5 **no tiene codificador H.264 por hardware** (ADR-09).

## ADR-02 · Un SDR por función y cada uno identificado por su número de serie
- **Decisión:**

  | Receptor | SDR | Serie |
  |---|---|---|
  | SATÉLITES | RTL del HAT | 00000101 |
  | RADIOAFICIONADOS | Mini RTL-SDR | 00000102 |
  | MULTIPERFIL | RTL-SDR Blog V3 | 00000103 |
  | ADS-B | FlightStick de RadarBox | 00001090 |

  Las series se graban en la EEPROM con `bricohams-sdr-serials`.
- **Por qué:**
  - Los cuatro son RTL2832U con sintonizador de la familia R820T, así que el sistema no los distingue.
  - Por orden USB se cruzarían al reiniciar.
  - Con la serie, OpenWebRX y readsb abren siempre el mismo SDR.
- **Implica:** la grabación de series es interactiva (conectar de uno en uno) y solo se hace una vez.
- **Corrección v2:** el dongle MULTIPERFIL es un **V3**, no un V4. Por eso:
  - **En Bookworm** sigue haciendo falta el driver `rtl-sdr-blog` (bias-tee y muestreo directo del V3 y del R860), y queda fijado con `apt-mark hold`. **En Trixie** basta el rtl-sdr 2.0.2 de Debian (ADR-01).
  - Ya no se usa la detección del sintonizador R828D.

## ADR-03 · HF en el V3 por muestreo directo hasta que llegue el SDRplay
- **Decisión:**
  - 12 perfiles de HF con los valores de referencia de **EA7CL** (nombres, centros, modo e inicio en FT8) en el V3.
  - De 160 a 15 m, `direct_sampling: 2` (rama Q) en cada perfil. De 12 a 6 m, sintonizador normal (el R820T2 baja hasta ~24 MHz).
  - El SDRplay ya está en la plantilla con sus propios perfiles (`sp*`) y un **programador de luz solar** para la escucha automática: día 20 m, crepúsculo 40 m, noche 80 m (que cubre también 160 m).
  - El SDRplay se activa con `HF_SDRPLAY=yes`. Entonces los perfiles HF salen del V3.
- **Por qué:**
  - El SDRplay tardará meses en llegar.
  - Los 384 kS/s que usa EA7CL no son válidos en un RTL-SDR (rangos válidos 225–300 k y 900 k–3,2 M), así que en el V3 se usan 1,024–2,4 MS/s.
- **Implica:**
  - El V3 tiene un solo SMA. Para HF y VHF a la vez hace falta un **diplexor HF/VHF** (corte ~30 MHz) entre el hilo largo de HF, la discone y el V3. Ver el [esquema de RF](esquemas/04_rf_antenas_alimentacion.png).
  - El cambio al SDRplay es una línea en `bricohams.env` más `sudo bash install.sh --solo sdrplay,configuracion` ([manual 08](manuales/08_SDRPLAY.md)).

## ADR-04 · ADS-B fuera de OpenWebRX, con el FlightStick dedicado de RadarBox
- **Decisión:**
  - readsb (wiedehopf) abre el FlightStick por su serie y sirve Beast en `:30005`.
  - rbfeeder trabaja en *network mode* leyendo esa salida, con MLAT activado.
  - tar1090 da un mapa propio de aviones en `:80`.
- **Por qué:**
  - Alimentar RadarBox y hacer MLAT exige escuchar 1090 MHz las 24 h. Dentro de OpenWebRX ese SDR se movería de perfil con los visitantes.
  - El FlightStick ya trae LNA y filtro de 1090.
  - readsb permite elegir el dispositivo por serie y alimentar a otros agregadores más adelante.
- **Implica:**
  - El FlightStick no aparece en OpenWebRX.
  - La clave de compartición de RadarBox se conserva en `/etc/rbfeeder.ini` (o se fija con `RADARBOX_KEY`).
  - MLAT necesita la altura real de la antena (`ADSB_ANT_ALT`) y una hora buena (ADR-05).

## ADR-05 · El GPS lo gestiona gpsd; la hora, chrony con PPS; el RTC del HAT con pila
- **Decisión:**
  - gpsd abre `/dev/ttyAMA0` (UART0) y `/dev/pps0` (PPS en el GPIO 6).
  - chrony usa NMEA por SHM y el PPS como referencia principal.
  - El RTC PCF85063A del HAT pasa a ser `/dev/rtc0`, y el RTC de la Pi 5 se desactiva con `HAT_DISABLE_PI5_RTC`.
- **Por qué:**
  - Un puerto serie solo puede tenerlo un programa.
  - La hora exacta la necesitan MLAT, FT8/WSPR y los registros.
  - El RTC con pila evita arrancar con la hora mal si no hay Internet.
- **Implica:** meshtasticd **no** lee el GPS. Sus nodos llevan **posición fija** (la estación no se mueve).

## ADR-06 · Meshtastic: nodo 868 en el HAT y nodo 433 en un LilyGO, con los mismos canales
- **Decisión:**
  - **Nodo 868** (SX1262 del HAT, meshtasticd): se configura con el QR de la red (`MESH_CHANNEL_URL`).
    - Canales SFNarrow (principal), Murcia, Cartagena, Test y Alicante.
    - Radio EU_868 a 869,618 MHz, BW 62,5 kHz, SF7, CR 4/5.
  - **Nodo 433** (LilyGO T3 V1.6.1 por USB):
    - Mismos canales.
    - La radio se pasa después a EU_433 LONG_FAST, porque la frecuencia del QR no existe en 433.
  - **Canal privado** solo en el nodo 868: índice 5, nombre `MESH868_PRIVATE_NAME` (BricoHams) y clave AES-256 de `MESH868_PRIVATE_PSK`. La clave solo vive en `bricohams.env`, nunca en el git. Se añade después del QR, así que repetir el paso no lo duplica (`--seturl` reinicia los canales).
- **Por qué:**
  - El SX1262 del HAT solo cubre 860–960 MHz.
  - Con los mismos nombres y claves de canal, ambos nodos son compatibles si más adelante se unen por MQTT.
- **Implica:**
  - El QR pide 27 dBm; el SX1262 se queda en 22 dBm.
  - El LilyGO 433 transmite: ver la nota de RF en ADR-07.

## ADR-07 · iGate LoRa APRS solo en recepción, con su propio SSID
- **Decisión:**
  - LilyGO T3 V1.6.1 con el firmware **LoRa_APRS_iGate de CA2RXU (richonguzman)**, compilado y grabado desde la Pi con PlatformIO.
  - Escucha 433,775 MHz (SF12, BW 125, CR 4/5) y sube a APRS-IS como **N0CALL-10**, con baliza solo por APRS-IS.
  - Sin transmisión por RF ni digipeater.
- **Por qué:**
  - Va en la misma caja que los SDR: transmitir en 433 a pocos centímetros satura el receptor de 70 cm.
  - La LilyGO T3S3 de iGate actual queda libre.
  - El SSID -10 no choca con el iGate APRS de OpenWebRX (N0CALL, packet de 144,800).
- **Implica:** el iGate necesita WiFi (`LILYGO_WIFI_SSID`). Su web de administración está en su propia IP.

## ADR-08 · Sensor BME280/BMP280 en el I2C de la Pi, con la estación WX APRS hecha desde la Pi
- **Decisión:**
  - El módulo GYBMEP va a la Pi por I2C-1 (pines 1, 3, 5 y 9), en una garita en el exterior.
  - `bricohams-wx` lee cada minuto con las fórmulas de Bosch, reconoce el chip solo y escribe `sensor.json` para la ventana METEO.
  - Cada 10 min manda un paquete WX a APRS-IS como **N0CALL-13**.
- **Por qué:**
  - Una sola lectura sirve para la web y para APRS.
  - El firmware del iGate también admite el BME280, pero entonces la Pi no vería el dato.
  - Un RTC (0x51) y un BME280 (0x76/0x77) conviven en el mismo bus.
- **Implica:**
  - Cable I2C corto (unos 2 m). Más largo: extensor P82B715 ([manual 06](manuales/06_SENSOR_WX.md)).
  - Si el módulo es un BMP280, no hay humedad: el paquete APRS sale sin `h`.

## ADR-09 · Cámara: MediaMTX con H.264 por CPU y foto servida por el puerto de OpenWebRX
- **Decisión:**
  - **WPI408** (OV5647, 130°, IR) por CSI, con el cable de 15 a 22 pines de la Pi 5.
  - MediaMTX `rpiCamera` a 1280×720 y 10 fps con `softwareH264`.
  - `bricohams-camsnap` saca una foto cada 60 s a una carpeta tmpfs dentro de los plugins.
- **Por qué:**
  - La Pi 5 no tiene codificador por hardware: 720p a 10 fps deja CPU para cuatro SDR.
  - La foto por el puerto 8073 funciona para cualquier visitante sin abrir más puertos.
  - El tmpfs no gasta la tarjeta SD.
- **Implica:**
  - El directo por WebRTC (8889) solo funciona en la LAN o si abres ese puerto.
  - Si la cámara no tiene filtro IR, se usa el fichero de ajuste `ov5647_noir.json` (`CAM_TUNING`).

## ADR-10 · Meteo de estaciones en el servidor, no en el navegador
- **Decisión:** `bricohams-meteo` (temporizador de 10 min) junta en `meteo.json` dos fuentes:
  - Observación horaria de **AEMET OpenData** de Archena 7158X, Molina 7237E, Alcantarilla 7228 y Murcia 7178I.
  - Previsión de **Open-Meteo**.
- **Por qué:**
  - La clave de AEMET no sale al navegador y no hay problemas de CORS.
  - Una sola consulta sirve a todos los visitantes.
  - Meteoclimatic se descartó porque su robots.txt prohíbe el acceso automático.
- **Implica:** sin `AEMET_API_KEY` (es gratuita) solo se ve el modelo.

## ADR-11 · Plugins web locales e imagen BricoHams con Murcia
- **Decisión:**
  - Plugins propios en `htdocs/plugins/receiver/`: `solar` (NOAA), `meteo`, `camara` y `bricohams`.
  - Orden de botones: DX (rig_skin) → SOL → temperatura → CAM.
  - Cabecera con el skyline de Murcia: torre de la catedral, Puente de los Peligros, palmeras, el Segura y el mástil con la cámara.
  - Avatar con franja carmesí "MURCIA" y bandera de la Región junto al nombre del receptor.
- **Por qué:**
  - Todo lo de la marca queda versionado.
  - Los plugins de terceros (0xAF y rig_skin) se cargan desde su CDN y no hay que mantenerlos aquí.
- **Implica:** si rig_skin no carga, los botones propios se colocan detrás de "Estado".

## ADR-12 · Claves fuera del git
- **Decisión:**
  - El repositorio lleva `bricohams.env.example` sin claves. `bricohams.env` está en `.gitignore`.
  - El instalador lo copia a `/etc/bricohams/` con permisos 600 y reparte a cada servicio solo lo que necesita (`meteo.env` y `wx.env` con permisos 640).
- **Por qué:** el repositorio se comparte en BricoHams. Las claves de APRS, receiverbook, RadarBox, AEMET y WiFi son personales.

## ADR-13 · Instalador por pasos, repetible, con copia diaria
- **Decisión:**
  - `install.sh` está dividido en 18 pasos (v3.0: + `ventilacion`). Se pueden lanzar sueltos con `--solo`, y cada uno se puede repetir sin efectos raros.
  - Los ficheros del sistema se tocan en bloques marcados (`# >>> BricoHams`).
  - Con `--backup` se restauran usuarios y marcadores, añadiendo los nuevos del kit.
  - `bricohams-backup` guarda cada día la configuración (retención local de cinco días mediante `bricohams-backup-limpieza.timer`).
- **Por qué:** restaurar la estación tras un fallo de tarjeta tiene que ser un solo comando.

## ADR-14 · Alimentación: fuente oficial de 27 W y hub USB alimentado; el LX-LBU2C no alimenta la Pi
> **v2.2:** en la caja del mástil, la fuente pasa a ser el cargador USB de 45 W ([ADR-16](#adr-16--alimentación-en-la-caja-un-cargador-usb-multitoma-de-45-w)). El hub alimentado y lo dicho del LX-LBU2C siguen valiendo.

- **Decisión:**
  - Fuente oficial de la Pi 5 (5 V, 5 A) con `usb_max_current_enable=1`.
  - Hub USB 2.0 **alimentado** para los LilyGO y uno o dos SDR.
  - El módulo de power bank LX-LBU2C no se usa para la Pi.
- **Por qué:**
  - Hay 6 dispositivos USB para 4 puertos, y unos 1,5 A de USB contra un límite de 1,6 A.
  - El LX-LBU2C da 5 V a 2,4 A como máximo y corta la salida durante la carga ([evaluación](EVALUACION_MODULOS.md)).
- **Implica:** si hace falta un SAI, usar un SAI específico de Pi 5 o una LiFePO4 de 12 V con un regulador de 5 V y 5 A.

## ADR-15 · Caja de intemperie impresa en PETG, con compartimento de potencia aparte
- **Decisión:**
  - Caja paramétrica en OpenSCAD (`hardware/caja/caja_bricohams.scad`) de 224 × 232 × 90 mm, impresa en PETG blanco con juntas de TPU 95A en la Anycubic Kobra S1. Cada pieza cabe en 250 × 250 mm y se imprime sin soportes.
  - **Tabique y tapa interior:** separan el compartimento de potencia (230 V, cargador y hub) de la electrónica.
  - **LilyGO:** los dos van sobre la tapa interior.
  - **Cara inferior:** todos los conectores (9 SMA pasamuros, PG7, M20) y las rejillas de entrada. Las de salida van arriba, bajo un tejadillo inclinado.
  - **Cierre:** la pared entra en una ranura de la tapa con una junta de TPU. Las orejetas hacen de tope y fijan la compresión en el 25 %.
  - **Mástil Televés:** 2 sillas en V con abrazadera de 12 mm (`MAST_D`).
  - **Cámara:** detrás de una ventana de policarbonato con junta, aro anti-reflejos IR y visera.
  - **BME280:** en una garita de platos aparte, a 1 m o más de la caja.
- **Por qué:**
  - Un solo punto en el mástil: coaxiales cortos (menos pérdidas, sobre todo en 1090 MHz y satélites) y un único cable de 230 V.
  - Con los conectores abajo y el tejadillo arriba, el agua no entra aunque haya rejillas, y las rejillas sacan el calor por efecto chimenea.
  - Separar los 230 V es una cuestión de seguridad: quien abra la caja para tocar un SDR no tiene nada con tensión a la vista.
  - PETG: aguanta la intemperie y unos 75 °C. El PLA se deforma al sol de Murcia y el ABS/ASA pide cámara caliente. La Kobra S1 imprime PETG y TPU sin cambios.
  - Todo paramétrico: si cambian el mástil, el cargador o los conectores, se ajusta una variable y se regeneran los STL (`tools/caja.sh`).
- **Implica:**
  - Hay que comprobar la temperatura en verano (`vcgencmd measure_temp`). Si pasa de 75 °C sostenidos, se añade un ventilador de 40 mm.
  - Los coaxiales internos son latiguillos RG316 de 20 cm.
  - Montaje paso a paso en el [manual 10](manuales/10_CAJA_3D.md).

## ADR-16 · Alimentación en la caja: un cargador USB multitoma de 45 W
- **Decisión:**
  - Una sola entrada de 230 V a un cargador USB de 45 W, dentro del compartimento de potencia.
    - **USB-C PD (5 V 3 A)** → Raspberry Pi 5.
    - **USB-A (2,4 A)** → hub USB 2.0 alimentado, del que cuelgan Mini, V3, FlightStick y los 2 LilyGO.
  - `PI5_USB_MAX_CURRENT="no"`.
  - Sustituye en la caja a la fuente oficial de 27 W de la ADR-14.
- **Por qué:**
  - Un solo transformador y un solo cable de red en el mástil.
  - Consumo total de 13 a 19 W: un 40 % de los 45 W, con margen para el calor y para el SDRplay.
  - La Pi 5 solo negocia 5 A con su fuente oficial. Con cualquier otro cargador arranca a 3 A y limita sus USB a 0,6 A en total, así que los SDR **tienen** que ir al hub alimentado.
- **Implica:**
  - **Cable USB-C de 3 A** y corto. Si `bricohams-check` avisa de `get_throttled`, la causa es el cable o el puerto.
  - Conexión de 230 V con diferencial de 30 mA, prensaestopas PG9 y anclaje del cable. La hace o la revisa alguien cualificado.

## ADR-17 · WiFi configurable con NetworkManager: la Pi prioriza 5 GHz y el iGate usa 2,4 GHz
- **Decisión:**
  - El paso `red` del instalador crea dos conexiones de NetworkManager:
    - `WIFI_SSID_1`, con prioridad 20.
    - `WIFI_SSID_2`, con prioridad 10.
  - País de WiFi `WIFI_COUNTRY`.
  - El iGate LilyGO usa `LILYGO_WIFI_SSID` (2,4 GHz).
  - La clave solo está en `bricohams.env`.
- **Por qué:**
  - La Pi 5 tiene WiFi de 5 GHz: menos interferencias en 2,4 GHz y más caudal para el vídeo y los usuarios web. Si la de 5 GHz no llega al mástil, la Pi pasa sola a la de 2,4 GHz.
  - El ESP32 del LilyGO solo funciona en 2,4 GHz.
  - El prensaestopas M20 deja pasar un cable de red, que siempre tiene prioridad sobre el WiFi.
- **Implica:**
  - Con la caja cerrada en el mástil, comprueba la cobertura: `nmcli -f IN-USE,SSID,SIGNAL dev wifi` (lo muestra `bricohams-check`).
  - La caja de PETG apenas atenúa, pero el mástil y los coaxiales sí: orienta la cara de la tapa hacia el punto de acceso si se puede.

## ADR-18 · Antenas propias diseñadas con NEC2 y piezas impresas paramétricas
- **Decisión:**
  - Cada antena que se construye (quad 2 m/70 cm, dos discones y ADS-B) tiene un modelo NEC2 en `hardware/antenas/sim/` (Python + `nec2c`) que genera sus medidas, sus diagramas y un JSON de resultados.
  - Las piezas de plástico salen de un solo fichero OpenSCAD paramétrico (`hardware/antenas/antenas_bricohams.scad`, 30 piezas). `tools/antenas.sh` las exporta y comprueba que caben en la Kobra S1.
- **Por qué:**
  - Las medidas «de calculadora» no tienen en cuenta el acoplo entre bandas de la quad ni la influencia del mástil. Con el modelo se ven y se corrigen antes de cortar aluminio.
  - Si cambia un diámetro de varilla o de mástil, se cambia una variable y se reimprime.
- **Implica:**
  - Las cotas de los manuales 12–14 salen de `resultados/*.json`. Si se toca un modelo, hay que volver a ejecutar `--final` y los planos (`tools/planos_antenas.py`).
  - **Comprobación final con NanoVNA siempre:** el modelo no conoce tu hilo ni tus soldaduras.

## ADR-19 · HAM con una quad de doble resonancia 2 m/70 cm y un diplexor
- **Decisión:**
  - El receptor RADIOAFICIONADOS (Mini 00000102) va a una **cúbica de rombos, vertical**: 2 elementos en 2 m y 3 en 70 cm sobre un solo boom, fija a **205°**.
  - Dos alimentaciones, unidas por el **diplexor 2 m/70 cm del proyecto** en la caja de aluminio de cabecera.
  - En 2 m, adaptación con un λ/4 de RG-59.
- **Por qué:**
  - Es lo que pidió el usuario («RADIOAFICIONADOS fija»).
  - 8,5 dBi en 2 m y 9,8 dBi en 70 cm, con F/B > 30 dB, es decir 6–8 dB más que la colineal. Un ancho de 75–100° a 205° cubre los repetidores de Sierra Espuña (229°), Peña Rubia (222°), Águilas (201°) y Carrascoy (176°).
  - La polarización vertical es la de los repetidores FM.
  - Con alimentaciones separadas, cada banda se ajusta sin tocar la otra.
- **Implica:**
  - Lo que queda detrás de la antena (≈ 25° al NE) se oye peor.
  - El diplexor tiene ~0,3 dB de pérdida por rama.

## ADR-20 · Plan de mástil: alturas, separaciones y vientos obligatorios
- **Decisión:** reparto vertical en el mástil Ø40 (`tools/mastil.py`, esquema 11).

  | Altura | Antenas |
  |---|---|
  | 2,9 m | discone grande |
  | 1,7 m | brazo con ADS-B, GPS y Meshtastic 433 |
  | 1,5 m | viento |
  | 0,95 m | quad |
  | 0,2 m | brazo con 868 e iGate 433 |

  Lleva **3 vientos a 2 m** con tensores.
- **Por qué:**
  - **Separación entre transmisores y receptores:**
    - TX 433 ↔ iGate: 1,5 m en vertical, unos 40 dB.
    - TX 868 ↔ iGate: 1,6 m.
    - Resto: ≥ 1,6 λ.
  - **Viento:** el cálculo da **530 MPa** en el empotramiento a 130 km/h sin vientos, más que el límite del S235: el mástil **se dobla**. Con vientos, 92 MPa a 150 km/h.
- **Implica:**
  - Sin vientos no se monta la discone grande arriba.
  - Si no se pueden poner vientos: mástil de Ø50 × 3 o bajar la discone.

## ADR-21 · Caja v3 en dos módulos al pie del mástil (≈ 5 m)
- **Decisión:**
  - **Módulo de electrónica** (228 × 240 × 140) con rejilla universal de M3 cada 20 mm, 18 pasamuros N, bahía de expansión, bandeja de SDR (HackRF One, Airspy HF+, RTL-SDR V4) y ventilación forzada.
  - **Módulo de potencia** (170 × 200 × 112) aparte.
  - **Módulo SAI** opcional (228 × 240 × 140) debajo del de potencia: reaprovecha la placa, el transformador y la batería de plomo de un SAI de 600 VA, con filtro EMI de red a la entrada y a la salida (manual 17 §1.2, `tools/sai_calculo.py`). Se elige el SAI completo a 230 V (≈ 1,1 h con 7 Ah usada) frente a llevar su batería al bus de 12 V (≈ 1,9 h) para no tocar el resto de la alimentación.
  - Los dos, a ~5 m del mástil, en pared o poste.
- **Por qué:**
  - Decisión del usuario («A 5 m, al pie»). No suma peso ni carga de viento al mástil (ADR-20).
  - Se abre sin escalera y caben más SDR sin reimprimir.
  - Los 230 V quedan en otra caja.
- **Implica:**
  - Bajadas de 7–8 m: LMR-400 o Hyperflex 5 en VHF/UHF/1090 y H155 en el resto.
  - El LNA de ADS-B va en la antena.
  - La caja v2 (ADR-15) queda como alternativa en el mástil.

## ADR-22 · Alimentación v3: cargador de 120 W + bus de 12 V
- **Decisión:**
  - Cargador USB de 120 W en una base Schuko dentro del módulo de potencia:
    - **USB-C 1 (PD 5 V 3 A)** → Pi 5;
    - **USB-C 2 + gatillo PD a 12 V** → portafusibles → bus WAGO de 12 V.
  - Del bus cuelgan la regleta Vansuny (2 A), los ventiladores (1 A) y los sensores RS485 (1 A).
- **Por qué:**
  - Un único transformador de 230 V.
  - La estación consume 16–24 W, el ~20 % del cargador.
  - Los ventiladores y los sensores de viento piden 12 V. La regleta Vansuny es de 12 V (su FX24E queda de repuesto).
- **Implica:**
  - **Comprobar que el cargador da 12 V por PD.** Si no, gatillo a 15 V + reductor.
  - Con los módulos a más de 1,5 m, la Pi se alimenta con un reductor 12 → 5,1 V 5 A en el módulo de electrónica.

## ADR-23 · Ventilación forzada con PWM por hardware y tacómetro
- **Decisión:**
  - 2 ventiladores de 60 mm de 4 hilos (entrada abajo a la izquierda, salida arriba a la derecha, con capotas).
  - PWM0 del RP1 en GPIO12/13 a 25 kHz, invertido por 2N7002.
  - Tacómetros en GPIO22/5 y DS18B20 en GPIO4.
  - Servicio `bricohams-fan` con curva CPU/caja e histéresis.
- **Por qué:**
  - En verano el interior pasaría de 60 °C.
  - Un ventilador de 4 hilos regula sin conmutar los 12 V, así que no mete ruido en los SDR.
  - El PWM por hardware no gasta CPU.
  - Los tacómetros detectan un ventilador parado antes de que se cuelgue un SDR.
- **Implica:**
  - Los pines 12/13/22/5/17/4 quedan reservados (HARDWARE_Y_GPIO).
  - Hacen falta los overlays `pwm-2chan` y `w1-gpio` y un reinicio.

## ADR-24 · Cámara: IP por RTSP en el mástil (recomendada) o Camera Module 3
- **Decisión:**
  - `CAM_SOURCE="rtsp"` hace que MediaMTX **reenvíe** el H.264 de una cámara IP PoE de exterior (p. ej. Reolink RLC-510A), sin recodificar.
  - `CAM_SOURCE="rpi"` mantiene la cámara CSI. Si se compra una nueva, que sea la Camera Module 3 Wide NoIR.
- **Por qué:**
  - Con la caja al pie, una CSI solo vería el mástil desde abajo.
  - La Pi 5 no tiene codificador H.264, y la IP le quita esa carga (0 % de CPU).
  - Una cámara IP es estanca y tiene IR de verdad.
- **Implica:**
  - `CAM_RTSP_URL` lleva usuario y clave: **solo en `bricohams.env`**.
  - `mediamtx.yml` pasa a ser `root:mediamtx 640`.

## ADR-25 · Viento y lluvia: en la Pi (N0CALL-13) y, como alternativa, en un LilyGO (N0CALL-14)
- **Decisión:**
  - Anemómetro y veleta RS485 Modbus (4800 8N1, direcciones 1 y 2), por un adaptador USB que el sistema llama `/dev/rs485`.
  - Pluviómetro de reed en GPIO17.
  - `bricohams-wx` hace las medias APRS: viento de 1 min, dirección vectorial de 2 min, racha de 5 min y lluvia en 1 h, 24 h y desde medianoche.
  - Alternativa: `bricohams-lilygo wxstation` graba el firmware de CA2RXU.
- **Por qué:**
  - El usuario pidió **las dos**.
  - En la Pi aprovecha el BME280 y la conexión que ya hay.
  - El LilyGO sirve para una estación aislada o de respaldo, y usa los mismos sensores que el proyecto de CA2RXU.
- **Implica:**
  - **Un solo maestro en el bus RS485:** o la Pi o el LilyGO.
  - El pluviómetro va en un poste aparte, no en el mástil.

## ADR-26 · Repetidores en marcadores con el subtono en la descripción; Wifon FM la primera
- **Decisión:**
  - `tools/marcadores.py` lee la lista de repetidores EA5 (`data/repetidores_EA5KGV_zonaEA5.csv`) y crea marcadores 🔁 nuevos o anota los que ya existen. En la descripción va «Entrada 145,05 MHz (−0,6 MHz) · Subtono 88,5 Hz para abrirlo (para escuchar no hace falta)». Es idempotente.
  - **Wifon FM 97,5** es la primera emisora («⭐») y el primer perfil FM del MULTIPERFIL.
- **Por qué:**
  - Los marcadores de OpenWebRX **no tienen campo de CTCSS**: solo nombre, frecuencia, modulación, descripción y «scannable».
  - Un receptor SDR no necesita el tono para oír el repetidor (no tiene silenciador por tono). El tono solo es útil para quien quiera transmitir, y lo lee en la descripción.
  - El perfil va primero porque OpenWebRX ordena los perfiles por su orden en `settings.json`.
- **Implica:** al actualizar la lista de repetidores, se vuelve a ejecutar `marcadores.py`. No duplica.

## ADR-27 · HF: SDRplay RSPdx-R2 (presupuesto: RSP1B)
- **Decisión:** el 4.º receptor de HF será un **RSPdx-R2**: antena A al MLA-30, antena B a una HF exterior futura y la C libre.
- **Por qué:**
  - Es el único que junta HF de calidad, 10 MHz por perfil para muchos oyentes, preselección y tres entradas, y funciona en la Pi 5.
  - **Airspy HF+:** solo ve ~0,7 MHz.
  - **RX888:** necesita un mini-PC.
  - **HydraSDR:** no tiene HF.
- **Implica:** los perfiles `sp*` y `HF_SDRPLAY` del manual 08 no cambian.

## ADR-28 · Filtros y LNA: solo donde se ha medido o calculado que ayudan
- **Decisión:**
  - FBP-433s en el iGate (solo RX).
  - FBP-868s en reserva, nunca en la TX de 22 dBm.
  - LNA 1090 en la base de la antena ADS-B con bias-tee de 5 V.
- **Por qué:**
  - Un filtro quita 2,5 dB. Solo compensa si hay bloqueo, así que se prueba una semana con y sin filtro.
  - El LNA solo sirve **antes** del cable.
- **Implica:** quedan en la documentación los avisos de los errores que rompen equipos (manual 16).

## ADR-29 · Con el HAT no hay GPIO: sensores y ventiladores en una Raspberry Pi Pico por USB
- **Decisión:**
  - BME280, DS18B20, pluviómetro y los 2 ventiladores (PWM + tacómetro) van a una **Raspberry Pi Pico** con MicroPython (`firmware/pico-io/main.py`), enchufada por USB a la regleta (`/dev/bricohams-io`).
  - El servicio `bricohams-io` deja los datos en `/run/bricohams/io.json` y pasa a la Pico las órdenes de `bricohams-fan`.
  - `IO_MODE="gpio"` conserva el montaje de la v3 para una Pi sin HAT.
- **Por qué:** el usuario lo comprobó: con el HAT puesto no se puede llegar a la cabecera. Así se evitan una cabecera apiladora y los pines que el HAT pueda usar.
- **Alternativas descartadas:**
  - **Cabecera apiladora:** depende de que el HAT deje pasar los pines.
  - **ESP32/LilyGO:** más caro y gasta más.
- **Implica:**
  - Una pieza más (~5 €) y una placa perforada con 2 MOSFET.
  - Si la Pi deja de mandar órdenes 60 s, la Pico pone los ventiladores al 100 % ella sola.
  - El viento sigue por USB-RS485 y la cámara por CSI.

## ADR-30 · Anclajes impresos sin abrazaderas en U: crucetas de tres piezas con tuercas cautivas
- **Decisión:**
  - Toda unión de dos tubos perpendiculares usa la **cruceta**: cuerpo + 2 tapas, 2 × M6 por tubo, media caña 1 mm menos profunda que el radio y un tornillo autotaladrante como antigiro.
  - Piezas propias para la base de la ADS-B, la brida de anemómetro y veleta (vale para los dos patrones de brida), el pluviómetro nivelable y la Pico.
- **Por qué:**
  - El usuario no encontraba cómo anclar la fibra, la quad y la ADS-B.
  - Un solo diseño paramétrico cubre todos los casos y se imprime sin soportes.
- **Implica:**
  - ASA para exterior y revisión del apriete cada 6 meses.
  - Los vientos del mástil siguen siendo de cable de acero: no se imprimen.

## ADR-31 · Satélites: pases calculados en la Pi y ▶ Escuchar con el Doppler del plugin de 0xAF
- **Decisión:**
  - `bricohams-satpass` (SGP4 + CelesTrak, cada 15 min) genera `pases.json`.
  - El plugin `satelites` muestra la franja del próximo pase y el botón PASES.
  - ▶ Escuchar cambia de perfil, sintoniza y llama a `Plugins.doppler.start_tracker()` con los mismos elementos orbitales.
  - SatDump decodifica en segundo plano las imágenes METEOR.
- **Por qué:**
  - OpenWebRX+ no trae predicción de pases.
  - El plugin `doppler` ya corrige la frecuencia, pero obliga a buscar el satélite a mano.
- **Implica:**
  - La precisión se comprueba con Skyfield en las pruebas.
  - Solo recepción: el «duplex» es la bajada con Doppler; la subida queda documentada.

## ADR-32 · Web pública por nginx con SSL y portal de servicios
- **Decisión:**
  - nginx en 80/443 delante de OpenWebRX+ (websockets y `X-Forwarded-For`), tar1090 (lighttpd movido a 127.0.0.1:8504), HLS de la cámara, portal `/bricohams/` y API.
  - Let's Encrypt con dominio propio o DuckDNS; si falla, certificado autofirmado.
  - En el router solo se abren 80 y 443.
- **Por qué:** lo pidió el usuario (servicio sin SSL). Además da una sola entrada, las IP reales para los baneos y las estadísticas, y nada más expuesto.
- **Implica:**
  - RTSP y MQTT quedan solo en la LAN. La web de meshtasticd (9443) se quita en v4.5 (ADR-52).
  - `bricohams-check` vigila la caducidad del certificado.
  - **v4.2:** por decisión de N0CALL, el HTTPS se usa solo para la administración (ADR-40).

## ADR-33 · Visitas: MQTT de OpenWebRX+ + GeoIP local + Telegram, con IP truncada
- **Decisión:**
  - `mqtt_enabled` en OpenWebRX+ (mosquitto solo en 127.0.0.1).
  - `bricohams-visitas` escucha `openwebrx/CLIENT`, localiza con DB-IP Lite **local** y guarda **solo la IP truncada**.
  - Avisa por Telegram (1 por IP cada 10 min), reenvía el chat y publica totales y países en la web, con aviso de privacidad.
- **Por qué:**
  - Es la fuente oficial de conexiones de OpenWebRX+: no hay log de IPs.
  - El usuario eligió «país, ciudad e IP parcial»: minimización del RGPD.
  - La GeoIP local no filtra IPs a terceros.
- **Implica:**
  - Hace falta el texto de privacidad con contacto (`ADMIN_EMAIL`).
  - Se conservan 90 días, configurable.

## ADR-34 · Mantenimiento con una cuenta de servicio y cron, sin credenciales guardadas
- **Decisión:**
  - Cuenta de sistema `bricohams` sin contraseña ni shell.
  - `/etc/sudoers.d/bricohams` solo permite `/usr/local/sbin/bricohams-tarea`, con verbos fijos.
  - `/etc/cron.d/bricohams` lanza copia diaria, actualización semanal, reinicio preventivo (aplazado si hay un pase), salud cada 30 min con aviso por Telegram, resumen y GeoIP.
- **Por qué:** el usuario quería tareas «sin sudo» y una cuenta de servicio. Guardar una contraseña en un script la expondría en las copias y en el git; con sudoers restringido no hace falta ninguna.
- **Implica:**
  - La copia diaria pasa del temporizador systemd al cron, para tenerlo todo en un sitio.
  - El calendario se cambia en `bricohams.env` (`CRON_*`).

## ADR-35 · FT2 (experimental): decodium-rx + adaptador con formato jt9 + parche reversible
- **Decisión:**
  - Se compila solo el decodificador de terminal de Decodium (GPLv3).
  - `bricohams-ft2-decode` traduce su salida al formato de `jt9`.
  - `bricohams-ft2-patch` añade `Ft2Profile` (3,75 s) y el modo FT2 a OpenWebRX+, con marcas y un hook de apt que lo vuelve a aplicar.
- **Por qué:**
  - OpenWebRX+ y WSJT-X no traen FT2.
  - Reutilizar el analizador de FT8 da mapa, PSK Reporter y banderas sin más cambios.
- **Implica:**
  - Depende de los ficheros internos de OpenWebRX+. Si cambian, el parche no se aplica y lo avisa, sin romper nada.
  - Hay que compilar Qt6 (unos 700 MB y 20–40 min).

## ADR-36 · Marcadores: canales abiertos sí, comunicaciones privadas no
- **Decisión:**
  - Se añaden CB (40 canales CEPT), PMR446 (16), Radio Club Región de Murcia (RU-75 ED5YBF, 145,325, 430,325, CB 32 = 27,325, PMR 5), aviación (AIP de ENAIRE), marítimo de Cartagena y Mazarrón, FM (Radio María 91,0…), DAB+, FT8/FT4/WSPR/JS8/FT2 y satélites (`data/marcadores_v4.json`).
  - **No** se publican radiotaxis ni TETRA de emergencias o policía.
- **Por qué:** es un receptor público en Internet. Escuchar y difundir comunicaciones privadas puede vulnerar el secreto de las comunicaciones (Ley 11/2022).
- **Implica:**
  - El perfil TETRA queda solo como exploración de banda.
  - Los marcadores PMR 9–16 vuelven a ser FM analógico. Antes estaban mal como DMR; DMR446 usa las mismas portadoras.

## ADR-37 · Actualizar con huellas por paso, a mano y sin perder nada
- **Decisión:** `install.sh --actualizar` = git pull `--ff-only` + variables nuevas en `bricohams.env` + copia + `apt upgrade` + **solo los pasos con huella cambiada**. La huella de cada paso son tres SHA-256 cortados: su código (`declare -f`), los ficheros del kit que nombra (`$FILES/…`, `$KIT/…`) y las variables de `bricohams.env` que lee (`configuracion`: todas). Se guardan en `/var/lib/bricohams/kit-estado` al terminar bien cada paso.
- **Por qué:**
  - Los pasos ya eran idempotentes, pero repetirlos todos tarda 30–60 min, para OpenWebRX y reinicia servicios sin necesidad.
  - Una tabla «fichero → paso» escrita a mano se queda vieja; la huella sale del propio código.
  - `git pull --ff-only` como el dueño del kit: nunca fusiona ni pisa cambios locales, y git no protesta por un repositorio ajeno.
  - Si llega un `install.sh` nuevo, se relanza con él (`--continuar`): el plan lo hace siempre el código nuevo.
  - **No va en el cron:** bajar código de un git y ejecutarlo como root sin nadie delante es un riesgo (un commit roto o un git comprometido). El cron sigue solo con `apt`.
  - Marcadores en tres vías: el kit anterior (`bookmarks.kit.json`) dice qué marcadores son «propios», así se conservan los añadidos desde la web y llegan las correcciones del kit.
- **Implica:**
  - La primera actualización de una estación anterior a la v4.1 aplica todos los pasos.
  - Un cambio de hardware sin cambio de código (p. ej. conectar la Pico después) no cambia la huella: `--solo io`.
  - Si cambia la versión de bash, `declare -f` puede formatear distinto y repetir todos los pasos una vez (inofensivo).
  - `settings.json` sigue saliendo de la plantilla: los cambios hechos en `/settings` se pierden (queda copia `.antes-FECHA`).

## ADR-38 · bricohams.env se LEE, no se ejecuta
- **Decisión:**
  - `install.sh` ya no hace `. bricohams.env`.
  - `files/bin/bricohams-env.py` lo interpreta sin ejecutar nada:
    - comillas dobles con escapes ``\" \\ \$ \` ``;
    - comillas simples literales;
    - comentarios;
    - un `$` suelto es **literal** y da un aviso.
  - La copia de `/etc/bricohams/bricohams.env` y los `.env` derivados (api, telegram, duckdns, web, meteo, wx) se escriben con **comillas simples** (`sq`/`envl`). Así los leen igual bash, systemd `EnvironmentFile` y los lectores de Python.
- **Por qué:** en la Pi de N0CALL, `QRZ_PASS="…$Clave2026"` paró el instalador con «unbound variable». Sin `set -u` habría sido peor: la clave se habría guardado recortada sin avisar. Una contraseña no tiene por qué saber de sintaxis de bash.
- **Implica:**
  - Hace falta python3 desde el primer paso (viene en Raspberry Pi OS).
  - Las sustituciones `${VAR}` dentro de `bricohams.env` ya no se expanden. El `.example` no las usa: `test_env_red` comprueba que da lo mismo que bash.
  - Los errores de sintaxis se paran con el número de línea.

## ADR-39 · La red no se corta a sí misma y nada se baja sin reintento
- **Decisión:**
  - **Paso `red`:** si la conexión `bricohams-wifi-N` ya existe, se modifica (`nmcli connection modify`); antes se borraba y se volvía a crear.
  - **`esperar_red`:** antes de cada paso espera DNS (hasta 2 min) y, si no llega, se para con el estado de la red.
  - **Claves de repositorios (`clave_apt`) e instaladores de terceros (`script_remoto`):** se bajan con `curl --retry 5 --retry-all-errors` y fallan con un mensaje claro.
  - **`nginx -t`:** si falla, para el paso y enseña el error.
- **Por qué:** en la segunda ejecución en la Pi de N0CALL, `red` tumbó la WiFi por la que estaba conectada. El paso `openwebrx` falló con «Could not resolve host» y `gpg: no valid OpenPGP data` (había llegado una clave vacía por la tubería). Con `bash -c "$(wget …)"`, una descarga fallida ejecutaba un texto vacío y el paso seguía sin readsb.
- **Implica:** relanzar el instalador sigue donde se quedó. La auditoría de `test_env_red` impide funciones que acaben en `[ … ] && …`, que devuelven 1 con `set -e` (el fallo de `paso_web` que corrigió N0CALL).

## ADR-40 · HTTPS solo para la administración (SSL_MODO)
- **Decisión (de N0CALL: «el certificado SSL es solo para la página de settings»):** `SSL_MODO="admin"` por defecto.
  - **En el 80:** nginx sirve el receptor y el portal por HTTP.
  - **Rutas de OpenWebRX+ con usuario:** `/login`, `/logout`, `/pwchange`, `/settings…`, `/imageupload`, `/clients`, `/services`, `/ban`, `/unban`, `/broadcast` y `/files/delete` reciben un 301 a HTTPS.
  - **En el 443:** sirve todo, con la cookie `owrx-session` marcada `Secure; HttpOnly; SameSite=Lax` y sin HSTS.
  - **Otros modos:** `todo` (todo HTTPS + HSTS) y `no` (sin certificado, solo LAN).
  - Las rutas se separan en `/etc/nginx/snippets/bricohams-sdr-rutas.conf`, y la plantilla se monta con marcas `#@ADMIN@ #@TODO@ #@HTTP@ #@SSL>…<`.
- **Por qué:** lo que hay que proteger es la contraseña y la sesión del administrador. El receptor público por HTTP funciona en cualquier navegador y dispositivo, y en directorios de receptores que esperan `http://`.
  - **Por qué `Secure`:** sin él, la sesión abierta en HTTPS viajaría en claro al volver al receptor por HTTP.
  - **Por qué sin HSTS:** con HSTS, el navegador ya no volvería nunca a HTTP.
- **Implica:**
  - En el receptor por HTTP no se ve la sesión de admin; quien la necesite allí entra por `https://`.
  - `bricohams-check` prueba que `http://127.0.0.1/settings` redirige.
  - `test_ssl_admin` arranca un nginx real con los tres modos.
  - `listen 443 ssl http2` en vez de `http2 on;`, que no existe en el nginx 1.22 de Bookworm.

## ADR-41 · Filtro y DSP de audio en el navegador del oyente
- **Decisión:** el plugin base `audio_cadena` inserta etapas Web Audio entre `audioNode` y `gainNode` del `AudioEngine` de OpenWebRX+, por orden.
  - `filtro_audio` (orden 10): paso banda de 24 dB/oct con modos, notch manual y notch automático con seguimiento.
  - `dsp_audio` (orden 20): EQ de 3 bandas, puerta de ruido, AGC y limitador.
  - Apagados por defecto; los ajustes de cada oyente se guardan en su navegador.
- **Por qué:**
  - En la Pi, un DSP por oyente multiplicaría la CPU y cambiaría lo que oyen todos.
  - En el navegador cuesta cero al servidor y cada uno lo ajusta a su oído.
  - No hay plugins de audio en el repositorio de 0xAF (los enlaces que mencionó N0CALL no llegaron; eligió que se hicieran).
- **Implica:**
  - Los decodificadores y la grabación (REC) usan la señal original.
  - El notch automático exige dos detecciones seguidas y un pico estrecho (<120 Hz a −6 dB) para no tomar la voz por un pitido.
  - Probado en Chromium real con `tests/test_audio_navegador.py`: el 1 kHz baja más de 20 dB (en la práctica, unos 40) y la voz no cambia.

## ADR-42 · owrx-clone: perfiles portables de OpenWebRX+, por niveles y con copia previa
- **Decisión:** herramienta genérica e independiente (`owrx-clone/`, Python 3 sin dependencias, MIT, README es/en, `man`), que el kit también usa.
  - **Niveles:** `config`, `etc`, `web`, `paquetes`, `sistema`, `parches`, `extra`.
  - **Rutas lógicas:** `{DATA}`/`{HTDOCS}`.
  - **Integridad:** SHA-256 por fichero.
  - **Cifrado y publicación:** cifrado opcional con openssl (AES-256 + PBKDF2) y modo `--publico`.
  - **Importar:** repositorio luarvique según el sistema y paquetes por apt.
  - **Copia previa:** lo sobrescrito y lista de lo creado, para `deshacer`.
- **Por qué:**
  - Que cualquiera pueda llevar su OpenWebRX+ a otro equipo con todas sus personalizaciones, y la comunidad pueda compartir configuraciones.
  - **Qué es «personalización»:** sale de dpkg. Lo que no es del paquete (`web`) o lo que difiere de sus MD5 (`parches`), sin listas a mano.
  - **Archivos fuera de su sitio:** un perfil de terceros no puede escribir fuera de las carpetas de su nivel.
  - **Niveles con código como root:** `sistema` y `parches` ejecutan código como root y no entran sin pedirlos; `extra` solo con `--niveles extra`.
  - **Revisión de seguridad independiente (v4.2):** la revisión encontró que un `data_directory` del perfil podía llevar los ficheros a `/etc/cron.d`, y que `deshacer` seguía enlaces simbólicos. Arreglos:
    - `data_directory` del perfil: solo el del equipo o uno nuevo `/var/lib/openwebrx…`/`/srv/openwebrx…` del usuario openwebrx (una segunda revisión descartó `/home`, `/opt` y `/var/lib` en general);
    - lista de rutas prohibidas para todos los niveles;
    - escritura por temporal + `os.replace` sin enlaces en el camino;
    - copia previa tras apt;
    - `try/finally` con OpenWebRX+ rearrancado y la lista de lo creado.
    Hay una prueba de cada ataque en `test_owrx_clone`.
  - **`parches`:** solo con la misma versión del paquete.
- **Implica:**
  - **En el kit:** `install.sh --exportar` (sin `bricohams.env`) y `--importar` (paso `importar`).
  - **Marca:** `/etc/bricohams/perfil-importado` hace que `configuracion` y `plugins` respeten lo importado (`OWRX_PLANTILLA="yes"` vuelve a la plantilla).
  - **Copia diaria:** guarda además un perfil (retención local de cinco días mediante `bricohams-backup-limpieza.timer`).
  - **No se deshacen:** los paquetes instalados.
  - **Sistemas:** solo los que tienen repositorio de OpenWebRX+.

## ADR-43 · Zona de la estación por locator con un catálogo nacional en el kit (v4.3)
- **Decisión:** `STATION_LOCATOR` (o `STATION_LAT/LON`) + `LOCATOR_CATALOG` (por defecto `data/locator/catalogo_es.json`) eligen lo más cercano de cada categoría y lo convierten en marcadores `[AUTO-LOCATOR]` y en `METEO_STATIONS`.
  - **Categorías:** `airport`, `weather`, `port`, `radio`, `other`.
  - **Catálogo:** generado por `tools/locator_catalogo.py` desde CSV con fuente (`data/locator/fuentes`).
  - **Selección:** `files/bin/bricohams_locator_bookmarks.py`, el selector que empezó N0CALL en su V4.3, conservado y ampliado.
  - **Paso `configuracion`:** lo usa, y `bricohams-locator` lo deja a mano.
- **Por qué:**
  - **Cualquier estación de España**, no solo tu QTH. Los marcadores y la meteo dependen del sitio; el kit traía los de Murcia.
  - **Catálogo en el kit, no consultas en vivo:**
    - la instalación funciona sin Internet y es reproducible;
    - se prueba (`test_locator_es`: 895 puntos de toda España con aeropuerto, AEMET y, en la costa, canal 16);
    - cada dato tiene su fuente y su licencia (OurAirports es de dominio público).
  - **Las coordenadas exactas mandan sobre el centro del locator:** con 6 caracteres el centro puede estar a 4 km, y `STATION_LAT/LON` también alimentan el mapa y el APRS.
  - **8,33 kHz:** el «canal» no es la frecuencia (121,330 → 121,325 MHz). Se convierte, porque OpenWebRX+ sintoniza la frecuencia.
  - **Mínimo garantizado:** aeropuerto y AEMET, al menos el más cercano (hasta 2,5 × radio). Así ningún sitio de interior queda sin meteo.
  - **Una entrada por frecuencia:** los canales 12/14/16 son iguales en todos los puertos; se juntan con los nombres de los puertos.
  - **Los marcadores de Murcia del kit lejos de tu QTH** (más de `LOCATOR_KIT_ZONA_KM`):
    - se quitan los locales: FM y DAB de Murcia, aeropuertos, repetidores EA5;
    - se dejan genéricos los que solo llevaban el nombre de Murcia, y el genérico cede ante el de la zona;
    - lo tuyo no se toca: solo se adapta lo que es idéntico a un marcador del kit (nombre, frecuencia y modo).
- **Implica:**
  - **Variables nuevas:** `LOCATOR_ONLINE`, `LOCATOR_RADIOS(_MAX)`, `LOCATOR_METEO`, `LOCATOR_KIT_ZONA_KM`.
  - **En `/etc/bricohams/bricohams.env`:** van las calculadas (`STATION_LAT/LON` si salen del locator, `METEO_STATIONS`, `STATION_QTH_LOCATOR`).
  - **`meteo.env`:** lleva `METEO_STATIONS` entre comillas (los nombres llevan espacios).
  - **`--actualizar`:** repite `configuracion` si cambia el catálogo.

## ADR-44 · OpenWebRX+ en Docker desde bricohams.env, con red host y volúmenes en carpetas de la Pi (v4.3)
- **Decisión:** `OWRX_BACKEND="docker"` (lo introdujo N0CALL en su V4.3: rutas, `owrx_control`, comprobación de volúmenes). El kit lo completa así:
  - **Despliegue (`docker_preparar`):**
    - `docker.io` y `docker-compose` de Debian si faltan;
    - para el OpenWebRX+ nativo;
    - crea el usuario de sistema `openwebrx` para los servicios del host;
    - `docker-compose.yaml` generado (`bricohams-docker-compose.py`): imagen `slechev/openwebrxplus-softmbe`, `network_mode: host`, `./etc` `./var` `./plugins` como bind mounts, `/dev/bus/usb` con `device_cgroup_rules: c 189:* rmw`, `tmpfs /tmp`, `restart: unless-stopped`;
    - `compose pull` + `up -d`.
  - **Pasos adaptados:**
    - `comprobar` sin luarvique;
    - `sdrplay` y `ft2` se saltan con aviso;
    - tarea semanal con `compose pull`;
    - copia diaria con `/opt/owrx-docker`;
    - `bricohams-check`, `bricohams-servicios` y `bricohams-sdr-serials` entienden el contenedor.
- **Por qué:**
  - **Red `host`:** el resto del kit habla con OpenWebRX+ por 127.0.0.1 (nginx, MQTT de visitas, rtl_tcp). En `bridge` 127.0.0.1 sería el propio contenedor. `bridge` queda como opción con `OWRX_DOCKER_PORT`.
  - **Bind mounts en una carpeta de la Pi, no volúmenes con nombre:** los servicios del host (meteo, cámara, visitas, satélites, ventiladores) escriben en `plugins/`. Además se copian, se inspeccionan y owrx-clone los encuentra.
  - **Seed:** el `run.sh` de la imagen siembra `/etc/openwebrx` y `/var/lib/openwebrx` vacíos con `cp -n`, así que el bind mount vacío arranca.
  - **USB sin `--privileged`:** con `/dev/bus/usb` montado y la regla del grupo 189 se ven los SDR enchufados después. `OWRX_DOCKER_PRIVILEGED="yes"` queda para SDRplay o casos raros.
  - **Formato 2.4:** lo entienden `docker-compose` 1.29 (Bookworm) y `docker compose` 2.x (Trixie); `docker compose config` lo valida en las pruebas.
  - **Sin contraseñas en el compose:** `OPENWEBRX_ADMIN_PASSWORD` dejaría la clave en un fichero 644. El administrador se crea con `docker exec -it … openwebrx admin adduser`.
  - **OpenWebRX+ corre como root dentro:** el dueño en la Pi es el usuario `openwebrx` de la Pi (para los servicios), no el del contenedor (`owrx_owner` hace el `chown` en el host).
- **Implica:**
  - **FT2 no está disponible en Docker:** parchea el código del paquete.
  - **La instalación nativa queda desactivada, no borrada:** se pasa con owrx-clone (manual 33).
  - **`instalar_env`:** guarda en `/etc` `OWRX_DATA/OWRX_ETC/OWRX_HTDOCS` y `OWRX_CLONE_DOCKER`, para `bricohams-tarea` y los scripts.

## ADR-45 · owrx-clone 1.1: el mismo perfil para nativo y Docker (v4.3)
- **Decisión:**
  - **`--docker CONTENEDOR` (o `OWRX_CLONE_DOCKER`):** `docker inspect` da las carpetas montadas en `/var/lib/openwebrx`, `/etc/openwebrx` y `htdocs/plugins`, y los niveles leen y escriben ahí.
  - **Formato:** sin cambios (`FORMATO 1`): rutas lógicas `{DATA}`, `/etc/openwebrx/…` y `{HTDOCS}/plugins/…`.
  - **En Docker:** sin apt ni parches; `docker stop/start` en vez de systemctl; la copia previa apunta el contenedor para `deshacer`.
- **Por qué:**
  - **Pasar de nativo a Docker y al revés** sin perder receptores, usuarios, marcadores ni plugins, y que la copia diaria funcione igual.
  - **Sin volumen de config o etc, se para:** escribir dentro del contenedor se perdería al recrearlo.
  - **Directorio de datos:** tiene que ser el del volumen. Si no, el contenedor no vería los datos.
  - **Fuera de plugins:** lo de `htdocs` que no está en `plugins` no tiene sitio en Docker; se avisa y se salta.
- **Implica:**
  - **El instalador pasa `--docker` solo:** en `--exportar`, en el paso `importar` y en la copia diaria.
  - **Pruebas:** `test_owrx_clone_docker`, con una orden `docker` de mentira.

## ADR-46 · Datos de zona que cambian se bajan en la Pi, con caché, y nunca paran la instalación (v4.3)
- **Decisión:**
  - **`bricohams_locator_online.py`:**
    - baja la lista completa de estaciones AEMET con coordenadas (`/observacion/convencional/todas`, con `AEMET_API_KEY`);
    - baja las emisoras de FM alrededor del QTH de maps.fmdx.org (datos de FMLIST).
  - **Caché:** `/var/lib/bricohams/locator`, 30 días. Las FM valen mientras la estación no se mueva más de 25 km.
  - **Cualquier fallo es un aviso:** se usa la caché o el catálogo del kit.
- **Por qué:**
  - **La FM cambia demasiado para un catálogo en el git**, y no hay un listado oficial descargable con coordenadas. fmdx.org es lo que usa FM-DX Webserver con el mismo fin: identificar emisoras desde un QTH.
  - **AEMET publica la lista con coordenadas exactas** pero pide clave. La clave ya está para la meteo y se pasa por entorno, nunca por la línea de órdenes ni a la caché.
  - **Clasificación por el nombre** (regional / nacional / local) para cumplir «radios regionales y locales». Las nacionales se añaden con `LOCATOR_RADIOS`. De cada frecuencia, la que mejor se oye: potencia/distancia².
- **Implica:**
  - **Si fmdx cambia su formato:** el parser es tolerante. Si falla, no hay FM nuevas y se avisa.
  - **Verificación:** con la Pi real (aquí no hay salida a esos servicios).
  - **`LOCATOR_ONLINE="no"`:** desactiva las dos fuentes.

## ADR-47 · Blindaje: auditar sin tocar, aplicar con copia y cortafuegos con vuelta atrás (v4.4)
- **Decisión:** `bricohams-blindaje` (bash, `/usr/local/sbin`).
  - **`auditar`:** solo lee, da una nota y **no enseña nunca un valor de clave**.
  - **`aplicar`:**
    - cortafuegos nftables propio (`table inet bricohams`, solo la cadena `input`): público 80/443/8073, SSH y servicios auxiliares solo para la LAN;
    - SSH sin root y con 3 intentos; **solo con clave únicamente si ya hay claves**;
    - fail2ban, unattended-upgrades, sysctl, permisos de todo lo que lleva claves, `UMask=0027` para OpenWebRX+ y Bluetooth apagado.
  - **Copia y vuelta atrás:** cada cambio guarda copia en `/var/backups/bricohams-blindaje/FECHA` y `deshacer` la restaura.
  - **El cortafuegos** se carga con un temporizador de vuelta atrás de 3 minutos (`systemd-run`) y solo se hace permanente con `confirmar`.
  - **nginx (kit):** `server_tokens off`, `limit_req` de 12/min en `/login` y `/pwchange` (regex, para que en `SSL_MODO=admin` gane la redirección a HTTPS), `X-Frame-Options`, `Permissions-Policy` y ficheros ocultos 404. Fail2ban bloquea una IP tras 5 POST fallidos al login (HTTP 303 de vuelta al formulario) en 10 min.
- **Por qué:**
  - **Sin acceso remoto a la Pi:** N0CALL pidió revisar y blindar el servidor (192.168.1.50, `sdr.example.org`), pero desde la sesión no se llega a su red (la salida va por una lista de dominios permitidos). Iniciar sesión con una contraseña escrita en el chat tampoco es aceptable.
  - **Herramienta para la Pi:** él la ejecuta en la Pi, se puede repetir y queda en el kit para cualquier estación.
  - **Lo visto desde fuera** (`/status.json`) confirmó una fuga real: la posición exacta de la casa (ADR-48).
  - **Contraseña solo con claves:** quitar la contraseña de SSH sin una clave instalada deja a la gente fuera.
  - **Cortafuegos con vuelta atrás:** uno mal calculado (otra subred, VPN) también. Por eso la red de casa se detecta de la interfaz (`BLINDAJE_LAN` la cambia) y hay vuelta atrás automática.
  - **Tabla propia en `input`:** no choca con las cadenas de Docker (`forward`, `nat`) ni con un ufw que ya hubiera; borrarla deja la Pi como estaba.
  - **El 8073 queda abierto, con aviso ALTO:** el usuario lo abre en el router. Por ahí la administración no pasa por nginx (sin HTTPS ni límite de intentos), así que se recomienda cerrarlo (`BLINDAJE_8073="lan"`), pero sin imponerlo.
  - **Búsqueda de fugas:** recorre los valores de las variables secretas de `bricohams.env` en la web, el kit y `/etc`, y solo cuenta los ficheros legibles por todos o servidos. La clave «anon» de Supabase es pública por diseño.
- **Implica:**
  - `bricohams-check` muestra el resumen (aviso, no fallo: no satura Telegram).
  - Los paquetes que instala `aplicar` (nftables, fail2ban, unattended-upgrades) no se desinstalan al deshacer, y los permisos endurecidos se quedan.
  - Pruebas sin tocar la máquina (`BH_RAIZ`), `nft -c` del cortafuegos generado y nginx real para el 429.

## ADR-48 · La posición pública va redondeada; la exacta se queda en la Pi (v4.4)
- **Decisión:**
  - `OWRX_GPS_DECIMALES="2"` (por defecto) redondea `receiver_gps` en `settings.json` (mapa, `/status.json`, directorios de receptores).
  - `meteo.json`, `pases.json` e `init.js` (todos públicos) llevan siempre 2 decimales.
  - `STATION_LAT/LON` siguen exactas para los cálculos (distancias AEMET, pases, Open-Meteo) y el APRS.
- **Por qué:** `https://sdr.example.org/status.json` publicaba 37.983812, -1.128011, la casa con unos 10 cm de precisión. Dos decimales (unos 1 km) bastan para el mapa, la meteo y el día/noche.
- **Implica:**
  - **El APRS WX sigue publicando su posición:** el protocolo lo exige; queda a elección del operador.
  - **Volver a publicar la posición exacta:** `"exacta"`.

## Pendiente / a verificar
1. **Pinout del HAT HackerGadgets**: en preventa, sin documentación publicada a 04/10/2026. Se han tomado los valores de la guía AIO.
2. **Repetidor digital de Sierra Espuña**: hay dos marcadores, 438,950 (dato de N0CALL) y 438,250 (ED5ZAN, de la lista anterior). Confirmar cuál está activo.
3. **WPI408**: comprobar si el filtro IR es fijo o se puede quitar, para elegir `CAM_TUNING`.
4. **SDRplay**: modelo (RSP1A/1B/dx) para `SDRPLAY_ANTENNA`.
5. **Cargador de 120 W**: comprobar que su USB-C PD ofrece **12 V** (ADR-22). **Regleta Vansuny**: contar los puertos (hacen falta 8; 11 con la bandeja de SDR, o un segundo hub USB 3.0 alimentado).
6. **Conectores de antena del HAT y de los LilyGO** (SMA o u.FL): según cuáles sean, los latiguillos a los SMA pasamuros cambian.
7. **Diámetro del mástil Televés**: el modelo trae `MAST_D = 40`.
8. **Pines del HAT AIO frente a GPIO 4, 5, 12, 13, 17 y 22** (ADR-23 y 25): confirmarlos cuando se publique el esquema del HAT. Se han evitado 7, 16, 23 y 27, que la guía AIO puede usar.
9. **FBP-868s**: potencia máxima real de tu unidad (SAW, ~18 dBm).
10. **Antenas**: ajuste final con NanoVNA (manuales 12–14).
11. **Temperatura de la caja en verano**: medir con `bricohams-fan --estado` y ajustar la curva.
12. **v4.3 · Docker en la Pi real**: primer `docker compose up` con `slechev/openwebrxplus-softmbe` en Trixie y Bookworm, SDR enchufados en caliente con `c 189:* rmw`, y RSP de SDRplay (¿hace falta `OWRX_DOCKER_PRIVILEGED`?).
13. **v4.3 · Datos en línea**: respuesta real de `maps.fmdx.org/api?qth=` (formato y clasificación de emisoras) y de `observacion/convencional/todas` de AEMET desde la Pi. Las pruebas usan respuestas de muestra.
14. **v4.3 · Coordenadas «aprox» del catálogo AEMET**: se afinan solas con `AEMET_API_KEY`. Las frecuencias de OurAirports marcadas «sin verificar» conviene contrastarlas con el AIP de ENAIRE.
15. **v4.4 · Primer «bricohams-blindaje aplicar» en la Pi real** (192.168.1.50): comprobar SSH desde la LAN, web desde Internet, que el 8073 se decida (cerrar en el router + `BLINDAJE_8073="lan"`) y `confirmar`. Cambiar la contraseña de `pi` (salió en un chat).
16. **v4:**
    - **Dominio para el SSL** (`SSL_DOMAIN`) y reenvío de los puertos 80/443 en el router.
    - **Token y chat de Telegram.**
    - **Medir** el Ø del tubo de la antena de fibra (`FIBRA_D`) y la brida de los sensores de viento.
    - **Cable de cámara de Pi 5:** comprar el Standard–Mini (15 → 22 pines).
    - **Primera compilación de FT2 en la Pi**, todavía sin probar en arm64.
17. **v4.2:**
    - **Probar en la Pi** los plugins FILTRO y DSP con audio real (los navegadores móviles pueden limitar Web Audio).
    - **Primera migración real con owrx-clone** (Pi → Pi o Pi → PC) y revisar la lista de paquetes que propone.
    - **SSL_MODO=admin:** comprobar que el directorio de receptores (receiverbook) acepta la URL `http://`.


## ADR-49 · iGate LoRa APRS en un RAK4631: radio en el RAK, Internet en la Pi (v4.5)
**Contexto:** N0CALL quiere el iGate en el RAK4631(L) que ya tiene (433 MHz, GPS y sensor de temperatura), partiendo de LoRa_APRS_iGate de CA2RXU. Ese firmware solo existe para ESP32 y depende de la WiFi: web de configuración, APRS-IS, OTA, NTP, MQTT y syslog. El nRF52840 no tiene WiFi.
**Decisión:** port parcial al nRF52840:
- **en el RAK**, lo que no depende de la red, reutilizando el código del original donde se puede:
  - KISS sin cambios;
  - radio y CAD adaptados;
  - lógica del digipeater;
- **en la Pi**, lo de Internet: `bricohams-rak-aprs` (APRS-IS con reglas de iGate, mensajes a RF y configuración);
- **entre los dos**, KISS por USB, con la orden estándar 0x06 (SetHardware) para configuración y estado. Así cualquier cliente KISS sigue valiendo.

Indicativo N0CALL-15: «N0CALL-SDR» no es válido en AX.25 ni en APRS-IS. Destino APZBH1 (experimental) hasta registrar uno.
**Consecuencias:**
- Sin la Pi el RAK sigue escuchando, digipeateando y balizando por RF, pero no sube a APRS-IS.
- Configurar el RAK es editar `bricohams.env`: el servicio compara y reenvía.
- Binarios en el repositorio, reproducibles con `tools/compilar_rak.sh`.

## ADR-50 · Integración con OpenWebRX+ por su propio suscriptor MQTT (v4.5)
**Contexto:** se pide ver el APRS y el Meshtastic «dentro» de OpenWebRX+. OpenWebRX+ no admite plugins de servidor, pero desde la 1.2.122 escucha `+/APRS`, `+/Meshtastic` y `+/CLIENT` en su broker (`mqtt_aprs`, `mqtt_meshtastic`, `mqtt_chat`) y los pasa por su código de mapa.
**Decisión:**
- Broker mosquitto **solo en 127.0.0.1**. Los dos servicios publican con el **mismo formato** que generan los decodificadores de OpenWebRX+, comprobado pasándolo por `AprsParser.updateMap` y `MeshtasticParser.updateMap` de la 1.2.126.
- Publicador MQTT mínimo propio (`bricohams_mqtt.py`) para no depender de paho en el entorno de pipx.
- Nuestra posición redondeada (ADR-48). Mensajes directos nunca; chat de canales públicos solo si se pide.

**Consecuencias:** sin parches en OpenWebRX+ (vale nativo y Docker con red host). Si OpenWebRX+ cambia el formato, lo detecta la prueba de compatibilidad del manual 35.

## ADR-51 · URLs de Meshtastic: completas solo en el env personal (v4.5)
**Contexto:** las URL de la red 433 y 868 llevan canales con clave AES propia (EspeleoSOS, EA5RCZ).
**Decisión:**
- Las URL completas van **solo** en `bricohams.env`.
- El `.env.example` (git) lleva la versión sin esos canales, generada con `bricohams-mesh-url publica`.
- Nunca se enseña una clave: `bricohams-mesh-url ver` dice «PROPIA AES-256».
- La URL 433 se aplica tal cual (trae EU_433 LONG_FAST y 10 dBm), sin forzar la radio.

## ADR-52 · Banner SSH: aviso sin pistas antes, estado después (v4.5)
**Decisión:**
- **Antes de autenticarse:** solo logo y aviso legal. Cualquiera lo ve, así que no se dice sistema, versión, IP ni dominio.
- **Después:** el estado útil, generado en cada entrada sin red (lee `/run` y `/proc`) para no retrasar el login.

Y `bricohams-dispositivos` identifica por VID:PID y serie (RAK 239a:8029, LilyGO CH9102 1a86:55d4). `HARDWARE_PENDIENTE` separa «no aparece» de «en camino». `bricohams-check` lo aplica también al BME280, la cámara del mástil y la Pico de los ventiladores: si están declarados, sus fallos son avisos y no llegan al informe de Telegram.

## ADR-53 · Configuración de Meshtastic solo dentro de /settings (v4.5, despliegue N0CALL)
**Contexto:** N0CALL exige que la configuración de Meshtastic no sea accesible desde la web pública de OpenWebRX+. Solo se puede tocar en Ajustes, que pide contraseña.
**Decisión:**
- `bricohams-mesh-admin` (127.0.0.1:8076) se publica en `/settings/bricohams/meshtastic`:
  - nginx lo fuerza a HTTPS (`SSL_MODO=admin`);
  - cada petición valida la cookie de sesión de OpenWebRX+ contra `127.0.0.1:8073/settings` (sin sesión, redirige a `/login`);
  - los POST llevan token CSRF;
  - nunca enseña PSK.
- Desde ahí se configuran el nodo 433 (LilyGO USB) y el 868 (HAT, API 4403), y qué sale en el mapa (`MESH433_OWRX`, `MESH868_OWRX`, `MESH_OWRX_CHAT`). Se guarda en los dos `bricohams.env`.
- Se quita la web propia de meshtasticd (9443), que no tenía contraseña.
- La web pública solo muestra los nodos en el mapa (ADR-50). El RAK solo envía información del nodo (baliza, estado, telemetría) y el log de estaciones oídas a APRS-IS/aprs.fi.
- `escribir_nginx` desactiva cualquier otro site `default_server` (copia en `/etc/bricohams/nginx-desactivados/`). En la Pi de N0CALL, un site antiguo `openwebrx` se saltaba HTTPS y las protecciones de /settings.

## ADR-54 · TAK local aislado con Python 3.12 (v4.6)
**Contexto:** N0CALL quiere un servidor TAK local. El instalador oficial de OpenTAKServer borra los sites de nginx y ocupa 443/8443, donde ya están OpenWebRX+ HTTPS y Meshtastic. Además, el gevent que fija OTS 1.7.13 falla al hacer fork con el Python 3.13 del sistema.
**Decisión:**
- `tools/instalar_tak.sh` instala OTS 1.7.13 y la UI 1.7.5 (sha256 fijo) en `/opt/bricohams-tak`:
  - Python 3.12.15 de uv, con dependencias fijadas;
  - usuario de sistema propio, PostgreSQL `bricohams_tak` y RabbitMQ en loopback.
- Puertos solo LAN (`BLINDAJE_PUERTOS_LAN`):
  - 8445: UI;
  - 8089: CoT mTLS;
  - 8446: enrollment;
  - 8447: Marti mTLS.
- `bricohams-tak-fw` (tabla nft `bricohams_tak`) cierra desde fuera 4369, 5672, 15672, 25672, 5432 y 8081.
- Las credenciales van solo en `/etc/bricohams/tak-access.txt` (root, 600).
**Consecuencias:**
- El resto del kit y el Python del sistema no cambian.
- TAK se puede quitar desactivando sus cuatro servicios y su site.
- Hay un segundo intérprete de Python que mantener.

## ADR-55 · Aviones ADS-B públicos y saneados, sin tocar RadarBox/MLAT (v4.6)
**Contexto:** el mapa debe mostrar los aviones en tiempo real. La Pi alimenta RadarBox con MLAT (readsb:30005 → rbfeeder → mlat-client → mlat1.rb24.com:40900). Exponer el JSON de readsb publicaría la posición del receptor y campos internos.
**Decisión:**
- `bricohams-api` sirve `/bricohams/api/aviones` a partir de `aircraft.json`:
  - 503 si los datos tienen más de 15 s o vienen del futuro;
  - descarta las posiciones con más de 60 s, las coordenadas inválidas y los hex mal formados;
  - solo publica hex, vuelo, lat/lon, hora, altitud, velocidad y rumbo.
- Los resultados MLAT (127.0.0.1:32004) no se reinyectan en readsb, para evitar bucles y no alterar el feed de RadarBox.
- `activar_mapa_local.sh` comprueba el sha256 de `rbfeeder.ini` y que mlat-client sigue en marcha.
- readsb pasa a `--device 00000401`, con autorización del usuario: `00001090` no existía.
**Consecuencias:**
- El mapa público enseña aviones, pero no dónde está la estación.
- Los aviones que solo tienen MLAT no salen en el mapa.

## ADR-56 · Capa TAK privada en el mapa (v4.6)
**Contexto:** TAK debe verse en «Mapas». Sus posiciones son de personas y equipos y no pueden ser públicas (ADR-53).
**Decisión:**
- `bricohams-mesh-admin` sirve `/settings/bricohams/tak/posiciones`:
  - valida la sesión de OpenWebRX+ en cada petición, sin caché;
  - 401 sin sesión y 503 si TAK falla;
  - `Cache-Control: no-store`.
- Lee PostgreSQL en solo lectura: timeout de 3 s, 1000 filas como máximo y solo CoT no caducados.
- El plugin solo la pide por HTTPS y la borra con 401, 403 o error.
- Nunca va a MQTT.
**Consecuencias:**
- Solo el admin con sesión ve TAK.
- El público sigue viendo el mapa sin TAK.
- No hacen falta certificados de cliente en el navegador.

## ADR-57 · Chat APRS en el CHAT común, solo recepción (v4.6)
**Contexto:** los mensajes APRS deben verse en el CHAT común de OpenWebRX+. Transmitir o mandar ACK automáticos desde una web pública sería emitir sin control del operador.
**Decisión:**
- `bricohams-rak-aprs` publica en MQTT `aprs/CLIENT` los mensajes APRS-IS dirigidos a la estación:
  - desempaqueta los de terceros;
  - descarta ack, rej y telemetría;
  - quita los caracteres de control y el `{msgid`, y corta a 200 caracteres;
  - no repite el mismo mensaje en 5 min.
- OpenWebRX+ los pinta con su chat MQTT (`bricohams-mqtt-settings.py --chat`), sin parchear su código.
- Se controla con `RAK_OWRX_CHAT`.
**Consecuencias:**
- Los mensajes se ven en vivo.
- No hay respuesta ni ACK: se contesta desde un cliente APRS.
- Los mensajes no se guardan en el servidor.

## ADR-58 · Importar/exportar bookmarks con el propio formulario de OpenWebRX+ (v5.0)
**Contexto:** hay que poder volcar y cargar todos los bookmarks desde un fichero. Escribir directamente `bookmarks.json` saltaría la validación de OpenWebRX+ y se rompería al actualizar.
**Decisión:**
- `bricohams-owrx-bookmarks-io` parchea solo la página `/settings/bookmarks` (marcadores `<!-- bricohams-bmio -->` y `#@BH-BMIO@`).
- Importar: el navegador lee el `.json` y da de alta cada bookmark con el formulario nativo, uno a uno.
- Exportar: «todos» o «editables», a partir de la lista incrustada como JSON escapado.
- Parche idempotente, atómico, compilado antes de escribir, reversible (`--quitar`) y con hook de `apt`.
**Consecuencias:**
- Sin sesión de administrador no existe nada nuevo; la web pública no cambia.
- Si OpenWebRX+ cambia la página, el parche no se aplica y lo avisa, en vez de romperla.

## ADR-59 · Clave de RepeaterBook en Ajustes generales (v5.0)
**Contexto:** OpenWebRX+ ya sabe usar `repeaterbook_api_key`, pero el campo viene comentado. El operador quiere ponerla desde la web protegida.
**Decisión:**
- `bricohams-owrx-repeaterbook` activa la sección «RepeaterBook» en `/settings/general` con un campo de contraseña (marcador `#@BH-RB@`).
- No la duplica si una versión futura trae el campo.
**Consecuencias:**
- La clave se guarda en la configuración de OpenWebRX+ y no se publica.
- RepeaterBook exige el e-mail de «Receiver admin» en el User-Agent; un token `rbuapp_` con otro patrón devuelve `403 ua_mismatch`.

## ADR-60 · Subtono CTCSS en el bookmark y silenciador por tono (v5.0)
**Contexto:** muchos repetidores solo son útiles si se escucha su subtono; el bookmark de OpenWebRX+ no tiene campo para él. Al ser un SDR (solo recepción) el bookmark guarda únicamente la frecuencia de salida del repetidor.
**Decisión:**
- `bricohams-owrx-ctcss` añade el campo opcional `ctcss` (Hz), la columna «Subtono FM» en `/settings/bookmarks` (50 tonos EIA, 60–260 Hz) y el módulo `CtcssSquelch` entre la de-énfasis FM y el AGC (marcador `#@BH-CTCSS@`).
- El silenciador abre solo si el tono pedido es el más fuerte de los 50 con margen claro; paso-alto de 300 Hz y rampas anti-chasquido.
- Etiqueta siempre **FM**, nunca «NFM».
- En la web pública solo se activa al sintonizar un bookmark con tono; el selector del panel afecta a la sesión del navegador, sin ajustes persistentes fuera de `/settings`.
**Consecuencias:**
- Requiere `python3-numpy` y `python3-scipy` (los instala `install.sh`).
- Sin numpy/scipy el silenciador queda inactivo y el audio pasa sin filtrar.

## ADR-61 · Importador de repetidores de RepeaterBook por zona (v5.0)
**Contexto:** cargar a mano los repetidores de la zona es lento y propenso a errores de subtono.
**Decisión:**
- `bricohams-owrx-rbimport` añade `/settings/bookmarks/repeaterbook` (marcador `#@BH-RBI@`): consulta la API con la clave de ADR-59, filtra por región/provincia/banda, previsualiza y crea bookmarks con su frecuencia de salida y su subtono (ADR-60).
- Modos analógicos a FM; los digitales se marcan y no se inventa subtono.
- No duplica bookmarks ya existentes en la misma frecuencia.
**Consecuencias:**
- Prueba de concepto en la estación del autor con la región 5 (Valencia/Murcia).
- Los datos de RepeaterBook pueden estar desactualizados: el operador revisa la previsualización.

## ADR-62 · Paneles TAK y Monitorización con Grafana tras /settings (v5.0)
**Contexto:** el operador necesita llegar a TAK y a la monitorización sin abrir puertos ni enlaces en la web pública.
**Decisión:**
- Accesos `/settings/bricohams/tak` y `/settings/bricohams/monitorizacion`, servidos por `bricohams-mesh-admin` con la sesión de OpenWebRX+.
- Grafana escucha solo en loopback y se publica por nginx en `/settings/bricohams/grafana/`; contraseña inicial `GRAFANA_ADMIN_PASS`.
**Consecuencias:**
- Nada nuevo en la página principal.
- La contraseña inicial de Grafana debe cambiarse en el primer acceso.

## ADR-63 · Credenciales TAK aleatorias, visibles y cambiables solo desde /settings (v5.0)
**Contexto:** las claves TAK se generan aleatorias al instalar y solo existían en `/etc/bricohams/tak-access.txt` (root, 600): no había forma documentada de verlas ni de cambiarlas sin terminal, y el manual citaba usuarios que no eran los reales.
**Decisión:**
- Sin claves por defecto: `instalar_tak.sh` las genera con `secrets.token_urlsafe(24)`. Los nombres salen de `TAK_ADMIN_USER` (rol administrator) y `TAK_USER` (rol user).
- Tarjeta «Credenciales TAK» en `/settings/bricohams/tak`: claves enmascaradas por defecto; «Mostrar credenciales» por POST con CSRF y `no-store`.
- Cambio de clave (manual o aleatoria) solo para usuarios del fichero; la clave va por stdin a OpenTAKServer bajo `runuser -u opentakserver`, nunca en argv ni en logs. El fichero se reescribe atómico (0600) solo si OpenTAKServer confirma; código 3 = usuario inexistente.
- La unidad `bricohams-mesh-admin` añade `ReadWritePaths=-/var/lib/bricohams-tak` (opcional con `-`), porque `ProtectSystem=strict` impedía a OpenTAKServer escribir su log. `instalar_tak.sh` hace `try-restart` del panel.
**Consecuencias:**
- El administrador ve y rota las claves sin SSH.
- El panel puede escribir en el directorio de TAK; se acepta porque ya es root y se limita a esa ruta.
- OpenTAKServer solo admite usuarios con letras, números, `_` y `.` (`UsernameValidator`): un guion da HTTP 400 en `/api/login`. `instalar_tak.sh` valida `TAK_ADMIN_USER` y `TAK_USER` con `^[A-Za-z0-9_.]{1,64}$`. Los usuarios nuevos llevan `active=True` y `confirmed_at`. No se renombra un usuario existente porque la tabla `certificates` referencia el nombre: se crea uno nuevo y se desactiva el antiguo.

## ADR-64 · Monitorización «adoptiva»: Prometheus/Grafana manuales se integran, no se reinstalan (v5.0)
**Contexto:** hay estaciones donde el operador ya instaló a mano Prometheus y node_exporter (binarios oficiales en `/usr/local/bin`) y Grafana por apt, con trabajos de scraping propios y escuchando en `0.0.0.0`. Reinstalar desde Debian duplicaría unidades y perdería datos y configuración.
**Decisión:**
- `paso_monitorizacion` detecta la instalación manual y solo añade drop-ins `*.service.d/bricohams.conf` que reescriben `ExecStart=` para escuchar en loopback, conservando la ruta TSDB existente.
- `prometheus.yml` se regenera con los trabajos `prometheus` y `node` y se conservan los demás; la primera vez se guarda `*.bak-manual`.
- Clave de Grafana estable y rotable sin terminal web: `GRAFANA_ADMIN_PASS` > fichero guardado > aleatoria, aplicada con `grafana cli`.
- Grafana solo es accesible por `/settings/bricohams/grafana/` tras `auth_request`.
**Consecuencias:**
- Reejecutar el paso es idempotente y no destruye nada del operador.
- Los exportadores ajenos que escuchen en `0.0.0.0` se limitan a localhost con `IPAddressDeny`/`IPAddressAllow` en lugar de tocar su código.
- Si el operador cambia la clave dentro de Grafana, la próxima ejecución la vuelve a fijar a la del `.env`/fichero: hay que rotarla por `GRAFANA_ADMIN_PASS`.

## ADR-65 · Bloqueo por IP y por país con nftables, gestionado desde /settings (v5.0)
**Contexto:** fail2ban solo reacciona a intentos fallidos; faltaba vetar a mano IPs, redes o países enteros sin abrir una terminal.
**Decisión:**
- `bricohams-bloqueo` (`/usr/local/sbin`) mantiene su propia tabla `inet bricohams_bloqueo` con conjuntos de IPs y redes, separada del cortafuegos de `bricohams-blindaje`.
- Configuración en `/etc/bricohams/bloqueo.json` y estado en `/var/lib/bricohams-bloqueo`. Las zonas de país se bajan de ipdeny.com (`geo-actualizar`), con caché.
- Órdenes: `estado`, `aplicar`, `geo-actualizar`, `desbanear` (lee `desbanear.json`) y `quitar` (borra la tabla).
- Nunca se bloquean la LAN, el loopback ni CGNAT, aunque se pidan.
- La tarjeta «Bloqueo por IP y país» del panel Seguridad (`/settings/bricohams/seguridad`) edita la lista y muestra las IPs baneadas por fail2ban con botón para desbanear.
**Consecuencias:**
- `quitar` deja la máquina como antes sin tocar el resto del cortafuegos.
- Los baneos automáticos (fail2ban y moderador) solo surten efecto con nftables activo y fail2ban instalado: hace falta `bricohams-blindaje aplicar`.

## ADR-66 · Usuarios de OpenWebRX y cortafuegos desde el panel Seguridad (v5.0)
**Decisión:**
- Tarjeta «Usuarios de la web»: alta, cambio de clave, activar/desactivar y borrar mediante `openwebrx admin --noninteractive` (nativo o `docker exec`). La clave va por la variable `OWRX_PASSWORD`, nunca en argv; los hashes de `users.json` no se leen ni se muestran.
- No se puede borrar ni desactivar el último usuario activo, y borrar exige escribir el nombre en «confirmar».
- Tarjeta «Cortafuegos y nginx»: estado de las unidades, últimas líneas del registro y botón «Recargar» (reinicia nftables y fail2ban, recarga nginx sin cortar sesiones y vuelve a aplicar el bloqueo).
- Todas las acciones van por POST con CSRF y la sesión de OpenWebRX+.
**Consecuencias:** el administrador gestiona accesos sin SSH; un error no puede dejar la web sin usuarios.

## ADR-67 · Aviso por Telegram de los inicios de sesión (v5.0)
**Decisión:** `bricohams-login-aviso` lee `/var/log/nginx/bricohams-sdr-login.access.log` y envía al bot solo la IP y la hora de cada login correcto, con una pausa de 600 s por IP. Se activa con `TG_AVISO_LOGIN="yes"`.
**Consecuencias:** no viaja ningún usuario ni clave; un acceso inesperado se ve en el móvil al momento.

## ADR-68 · Moderador del chat dentro de bricohams-visitas (v5.0)
**Decisión:** el mismo servicio que lee el MQTT de OpenWebRX+ vigila el chat: límite de mensajes por ventana, longitud, enlaces y palabras vetadas (`CHATBOT_ENABLE`, `CHATBOT_MAX_MSG`, `CHATBOT_VENTANA`, `CHATBOT_MAX_LEN`, `CHATBOT_LINKS`, `CHATBOT_PALABRAS`, `CHATBOT_UMBRAL`, `CHATBOT_AVISAR`, `CHATBOT_LOG`). Al superar el umbral avisa y escribe en su registro para que fail2ban banee.
**Consecuencias:** sin proceso nuevo; el baneo real depende de fail2ban (ver ADR-65).

## ADR-69 · Ficha del avión (foto, modelo y ruta) por un proxy con caché (v5.0)
**Contexto:** el navegador del oyente no debe llamar a servicios externos ni revelar su IP a terceros.
**Decisión:**
- `bricohams-api` (127.0.0.1:8075) sirve `/bricohams/api/avion?hex=ICAO&cs=INDICATIVO`: modelo, matrícula y operador de api.adsbdb.com, ruta origen/destino por indicativo y foto de api.planespotters.net (solo URLs https validadas).
- Caché en memoria de 6 h y 500 entradas; las respuestas vacías se reintentan a los 10 minutos.
- `bricohams_live.js` añade la ficha al globo del avión en el mapa.
**Consecuencias:** si un servicio externo cae, el globo sale sin foto pero el mapa sigue. Que no aparezcan aviones no es culpa de la ficha: depende de que readsb use el dongle de 1090 MHz correcto (`--device` en `/etc/default/readsb`).

## ADR-70 · map.flights como segundo destino ADS-B, sin tocar RadarBox (v5.1)
**Contexto:** se quiere compartir los aviones también con map.flights. RadarBox (rbfeeder + su MLAT) debe seguir igual.
**Decisión:**
- Conector Beast nativo de readsb (`--net-connector=feed.map.flights,30004,beast_reduce_plus_out,uuid=<UUID>`), sin cliente nuevo para posiciones. Solo `beast_reduce_plus_out` lleva la etiqueta `uuid`.
- MLAT con un `mlat-client` aparte (`bricohams-mapflights-mlat`, `DynamicUser`) contra `mlat.map.flights:31090`; sus resultados no se reinyectan en readsb (ADR-55).
- El UUID va en `bricohams.env` y en `/etc/bricohams/mapflights.env` (600), nunca en el repositorio. No se usa la clave `mf_feed_` del cliente JSON alternativo.
- Opcional (`MAPFLIGHTS_FEED="no"` por defecto); desactivarlo quita el conector y la unidad.
**Consecuencias:** sin proceso nuevo para posiciones; un segundo mlat-client lee 30005. El UUID viaja en claro por TCP: si se filtra, se cambia en map.flights.

## ADR-71 · Acceso de administradores con usuarios locales y/o Google (v5.5)
**Contexto:** los administradores entran con los usuarios de OpenWebRX+ (`users.json`). Se quiere poder entrar también con una cuenta de Google, sin perder el acceso local y configurándolo desde el panel Seguridad.
**Decisión:**
- Pasarela propia `bricohams-google-auth` (Python estándar, `DynamicUser`, 127.0.0.1:8077) con OpenID Connect (código + PKCE, `state`, `nonce`) y una cookie `bh-google` firmada con HMAC. No usa bibliotecas externas ni guarda tokens de Google.
- Cuatro modos: solo locales (`GOOGLE_AUTH=no`), `alternativa` (local O Google; botón «Entrar con Google» en `/login` con `sub_filter`), `doble` (`auth_request` de Google y además el usuario local) y `solo_google`. En `alternativa` y `solo_google`, la sesión de OpenWebRX+ se abre con la cuenta de servicio `bricohams-google` (clave aleatoria en `/etc/bricohams/google`, 0600).
- Los cambios en nginx se marcan (`# bricohams-google`) y son reversibles e idempotentes (`nginx --quitar`).
- El panel (`ProtectSystem=strict`) solo valida y guarda (`bricohams.env`, secreto 0600) y lanza la unidad *oneshot* `bricohams-google-auth-aplicar.service`, que ejecuta `aplicar`: preparar, servicio, nginx, `nginx -t` (restaura si falla) y `estado.json`.
- Antibloqueo: siempre queda un usuario local activo en los modos que lo usan, y solo se puede exigir Google si la petición ya trae una sesión de Google válida.
**Consecuencias:** el secreto del cliente no vuelve al navegador ni entra en Git. Si Google cae, en `alternativa` se sigue entrando con el usuario local; en los demás modos, el acceso de emergencia es `configurar --desactivar` + `aplicar` por SSH. Manual 46.
