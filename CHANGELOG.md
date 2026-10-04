# Historial

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
- **WiFi de casa:** nuevo paso `red` del instalador (son 17 pasos). La Pi prefiere `BiohazardIT-5G` y pasa a `biohazard-it` si no la ve. El iGate usa `biohazard-it` (2,4 GHz). La clave solo está en `bricohams.env`.
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
