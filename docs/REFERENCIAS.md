# Referencias

## Hardware
- HAT HackerGadgets RTL-SDR/LoRa/GPS/RTC: https://hackergadgets.com/products/rtl-sdr-lora-gps-rtc-hat-for-raspberry-pi
- Guía de la placa AIO de HackerGadgets (origen de los pines A VERIFICAR): https://hackergadgets.com/pages/hackergadgets-uconsole-rtl-sdr-lora-gps-rtc-usb-hub-all-in-one-extension-board-setup-guide
- Mini RTL-SDR HackerGadgets: https://hackergadgets.com/products/mini-rtl-sdr-dongle
- RTL-SDR Blog V3 (muestreo directo, bias-tee): https://www.rtl-sdr.com/v4/ · driver https://github.com/rtlsdrblog/rtl-sdr-blog
- Whadda/Velleman WPI408: https://www.velleman.eu/products/view/modulo-de-camara-con-2-luces-ir-para-raspberry-pi-wpi408/?id=459182&lang=ES
- Bosch BMP280 / BME280: hojas de datos (compensación §3.12 / §4.2.3 y §8.1)
- LX-LBU2C: https://www.tastethecode.com/power-bank-from-scratch-with-18650-batteries-and-lx-lbu2c
- LilyGO T3 V1.6.1 (LoRa32 V2.1_1.6): firmware Meshtastic `tlora-v2-1-1_6`

## Software
- OpenWebRX+ (paquetes): https://luarvique.github.io/ppa/ · documentación https://fms.komkon.org/OWRX/
- Plugins 0xAF: https://0xaf.github.io/openwebrxplus-plugins/ · rig_skin: https://github.com/aganet/openwebrxplus-rig-skin
- Referencia de bandas: OpenWebRX+ de EA7CL, http://ea7cl.duckdns.org:8073/
- meshtasticd en Debian: https://meshtastic.org/docs/software/linux/installation/debian · flasher: https://flasher.meshtastic.org
- LoRa APRS iGate (CA2RXU): https://github.com/richonguzman/LoRa_APRS_iGate
- readsb y tar1090 (wiedehopf): https://github.com/wiedehopf/adsb-scripts · https://github.com/wiedehopf/tar1090
- AirNav RadarBox en Raspberry Pi: https://www.airnavradar.com/raspberry-pi/guide
  - Bookworm + MLAT: https://forum.airnavradar.com/index.php?topic=107991.0
  - **Trixie** (rbfeeder por apt y mlat-client compilado): https://forum.airnavradar.com/index.php?topic=109561.0
- MediaMTX (rpiCamera): https://github.com/bluenviron/mediamtx
- SDRplay API: https://www.sdrplay.com/api/
- AEMET OpenData: https://opendata.aemet.es · Open-Meteo: https://open-meteo.com · NOAA SWPC: https://www.swpc.noaa.gov

## Datos de la estación
- Repetidores: lista de EA5RCZ en los marcadores; Sierra Espuña ED5ZAN (BrandMeister ID 214520): https://ea5gvk-dmr.zigor.es/2019/09/10/ya-tenemos-nuevamente-repetidor-dmr-brandmeister-en-murcia-ed5zan-sierra-espuna/
- Estaciones AEMET: Archena 7158X, Molina de Segura (Los Valientes) 7237E, Alcantarilla Base Aérea 7228, Murcia 7178I
- Canales Meshtastic: QR de la red aportado por EA5KAO (04/10/2026), en `MESH_CHANNEL_URL`

## Caja y alimentación (v2.2)
- OpenSCAD (modelo de la caja): https://openscad.org/documentation.html
- Raspberry Pi 5, alimentación y límite de corriente USB (5 V 5 A frente a 3 A): https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#power-supply
- NetworkManager, `nmcli connection add` (prioridad de autoconexión): https://networkmanager.dev/docs/api/latest/nmcli.html

## v3.0 · Antenas, caja v3, ventilación, viento y lluvia
- **NEC2 (`nec2c`)**, motor de simulación de los modelos de `hardware/antenas/sim/`: paquete `nec2c` de Debian. Las reglas de la cúbica parten de `claude/cubica_cx1ddr.md`, y el diplexor de `claude/diplexor_2m70cm_v1.md`, ambos del proyecto.
- **SDRplay RSPdx-R2:**
  - datasheet: https://sdrplay.com/wp-content/uploads/2026/06/RSPdxR2_Datasheet.pdf
  - ficha y precio: https://www.passion-radio.com/sdr-receivers/rsp-dx-935.html
- **HydraSDR RFOne** (24–1800 MHz, sin HF), datasheet: https://hydrasdr.com/downloads/HydraSDR_RFOne_Datasheet.pdf
- **OpenWebRX+:**
  - changelog (dispositivos admitidos: SDRplay, HydraSDR, RX888/sddc): https://github.com/luarvique/openwebrx/releases/
  - PPA: https://luarvique.github.io/ppa/
- **Raspberry Pi 5:**
  - PWM por hardware (overlay `pwm-2chan`, PWM0 del RP1 en GPIO12/13): https://gist.github.com/Gadgetoid/b92ad3db06ff8c264eef2abf0e09d569
  - foro: https://forums.raspberrypi.com/viewtopic.php?t=362319
- **Camera Module 3 (Wide NoIR, IMX708):** https://datasheets.raspberrypi.com/camera/camera-module-3-product-brief.pdf
- **Reolink RLC-510A** (cámara IP PoE con RTSP): https://reolink.com/product/rlc-510a/
- **MLA-30, manual de usuario:** https://www.tecsunradios.com.au/store/wp-content/uploads/2021/09/MLA-30-User-Instructions.pdf · https://www.passion-radio.com/hf/megaloop-968.html
- **Filtros NMRF FBP-433s:** https://www.amazon.co.uk/FBP-433s-433MHz-bandpass-filter-bandwidth/dp/B0FQ2KYRJG
- **Regleta Vansuny USB 3.0 con alimentador de 12 V 2 A (ASIN B09Q2YC87C):** https://www.amazon.es/Vansuny-Alimentacion-Externa-Ladron-Velocidad/dp/B09Q2YC87C
- **Estación WX LoRa de CA2RXU** (antes «APRS_WX_REPORT_STATION»): https://github.com/richonguzman/LoRa_APRS_Wx_Station
- **Sensores de viento RS485 Modbus** (registro de datos 0x0000, dirección en 0x07D0):
  - https://wiki.dfrobot.com/RS485_Wind_Direction_Transmitter_SKU_SEN0482
  - https://wiki.dfrobot.com/RS485_Wind_Speed_Transmitter_SKU_SEN0483
  - https://devices.esphome.io/devices/renke-rs-fxjt-n01-wind-direction/
- **Formato APRS WX** (`_CCC/SSSgGGGtTTTrRRRpPPPPPPPhHHbBBBBB`): APRS Protocol Reference 1.0.1, cap. 12.
- **Wifon FM** (97,5 MHz, Murcia): https://wifonfm.es/
- **Repetidores EA5:** lista EA5KGV del proyecto (`claude/canales_repetidores_EA.md`) → `data/repetidores_EA5KGV_zonaEA5.csv`.

## v3.1 · Trixie
- **Repositorio de OpenWebRX+ por versión:** `bookworm/` y `trixie/`, Release firmado. Página: https://luarvique.github.io/ppa/ · Repositorio: https://github.com/luarvique/ppa
- **meshtasticd en Debian 13:** https://meshtastic.org/docs/meshtasticd/installation/debian/
- **MediaMTX rpiCamera** (admite Trixie y Bookworm): https://mediamtx.org/docs/publish/raspberry-pi-cameras
