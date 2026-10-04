# Evaluación de módulos

Para cada módulo: qué es, si se puede integrar y cómo queda en la estación.

## 1. GY-BME/BMP280 «GYBMEP» (sensor de presión y temperatura) · ✅ integrado

| Dato | Valor |
|---|---|
| Placa | GYBMEP morada de 4 pines (VIN, GND, SCL, SDA), con regulador 662K de 3,3 V y adaptación de nivel |
| Sensor | BME280 (temperatura, humedad y presión) o BMP280 (sin humedad). La serigrafía «BME/BMP280» no lo aclara |
| Bus | I2C, dirección 0x76 (SDO a GND) o 0x77 |
| Precisión (Bosch) | presión ±1 hPa, temperatura ±1 °C, humedad ±3 % HR (solo BME280) |

- **Cómo se integra:**
  - Va al I2C-1 de la Pi (pines 1, 3, 5 y 9), compartido con el RTC del HAT (0x51).
  - `bricohams-wx` detecta el chip por su ID (0x60/0x58) y aplica la compensación de Bosch, comprobada con el ejemplo del datasheet en `tests/test_wx_bme280.py`.
  - Publica en la ventana METEO de OpenWebRX y como **estación WX APRS EA5KAO-13**.
- **Condición:** debe ir **fuera**, en una garita ventilada. Dentro de la caja mediría el calor de la Pi.
- **Alternativa descartada:** conectarlo al LilyGO del iGate, cuyo firmware también lo admite. La Pi no vería el dato y no saldría en la web.

## 2. LX-LBU2C V9.3 (módulo de power bank) · ❌ no se integra en la Pi

| Dato | Valor |
|---|---|
| Qué es | Cargador y elevador para celdas de litio 18650 (1S): entrada micro-USB/USB-C y **2 salidas USB-A de 5 V, 2,4 A en total**, con indicador y NTC |
| Serigrafía | «接电池前先接充电头检测指示灯亮» (antes de conectar la batería, conecta el cargador y comprueba que se enciende el indicador) · «注意! 电池反接必烧» (¡atención! si inviertes la batería, se quema) |

- **Por qué no vale para la Pi 5:**
  1. La Pi 5 con 4 SDR pide 5 V a 3–5 A (15–18 W); este módulo da como mucho 12 W **entre las dos salidas**.
  2. Los power bank de este tipo cortan o reinician la salida al enchufar o quitar el cargador: la Pi se reiniciaría y podría dañar la tarjeta.
  3. Sin protección de inversión, la batería se quema si se conecta al revés.
- **Usos posibles:** respaldo de los LilyGO o de un equipo portátil, aunque el T3 V1.6.1 ya trae cargador para una LiPo por su conector de batería.
- **Recomendación:** para respaldo de la estación, un SAI específico para Pi 5 o una LiFePO4 de 12 V con un regulador de 5 V y 5 A.

## 3. Whadda/Velleman WPI408 (cámara con 2 luces IR) · ✅ integrado

| Dato | Valor |
|---|---|
| Sensor | OmniVision **OV5647**, 5 MP (2592×1944), 1080p30 / 720p60 |
| Óptica | 3,6 mm, F1.8, **130°**, enfoque manual |
| IR | 2 LED IR a 3,3 V; filtro IR que se puede quitar |
| Conexión | CSI de 15 pines → en la Pi 5, **cable de 15 a 22 pines** |

- **Cómo se integra:**
  - MediaMTX (`rpiCamera`) a 1280×720 y 10 fps con `softwareH264`, porque la Pi 5 no codifica H.264 por hardware.
  - Foto cada 60 s para la web por el puerto 8073.
- **Visión nocturna:** sin filtro IR la imagen sale rosada de día. Corregir con `CAM_TUNING=…/ov5647_noir.json`.
- **Montaje:** dentro de la caja, tras una ventana, porque la cámara no es estanca. El cable CSI debe ser corto (≤ 1 m).

## 4. FlightStick de AirNav RadarBox · ✅ integrado (ADS-B)

| Dato | Valor |
|---|---|
| Qué es | RTL-SDR para 1090 MHz con LNA y filtro SAW integrados |
| Uso | Dedicado a ADS-B 24 h: readsb → rbfeeder (RadarBox) + MLAT + tar1090 |
| Serie | 00001090 (`SERIAL_ADSB`) |

## 5. LilyGO T3 V1.6.1 (LoRa32 V2.1_1.6, 433 MHz) ×2 · ✅ integrados

| Dato | Valor |
|---|---|
| Chips | ESP32 + SX1278 (433 MHz), OLED de 0,96″, USB-serie CH9102F |
| Placa | 65 × 27 mm, antena **SMA**, conector de batería LiPo (Picoblade/JST 1,25) con cargador. **No lleva zócalo de 18650** (corrección v2.2) |
| Nodo 1 | Meshtastic EU_433, con los canales de la red (SFNarrow, Murcia, Cartagena, Test, Alicante) |
| Nodo 2 | iGate LoRa APRS (CA2RXU), entorno PlatformIO `ttgo-lora32-v21`, solo recepción en 433,775 |
| Conexión | USB a la Pi (hub alimentado): corriente y configuración. Nombres fijos `/dev/lilygo-mesh` y `/dev/lilygo-igate` |
| En la caja | cunas sobre la tapa interior del compartimento de potencia, coaxial a los SMA «M433» e «IG433» ([manual 10](manuales/10_CAJA_3D.md)) |

## 6. HAT HackerGadgets RTL-SDR/LoRa/GPS/RTC · ✅ integrado (pines A VERIFICAR)

| Módulo | Chip | Uso |
|---|---|---|
| RTL-SDR | RTL2832U + R860, TCXO, bias-tee | Satélites |
| LoRa | SX1262 860–960 MHz, 22 dBm, TCXO | Meshtastic 868 |
| GPS | GPS + BDS, admite antena activa | gpsd + PPS → chrony |
| RTC | PCF85063A con pila recargable | /dev/rtc0 |

En preventa (envío desde el 14/10/2026), sin pinout publicado: [HARDWARE_Y_GPIO.md](HARDWARE_Y_GPIO.md).

## 7. Mini RTL-SDR HackerGadgets · ✅ integrado

RTL2832U + R860, TCXO (1 ppm), bias-tee, USB-C, SMA, caja de aluminio, muestreo directo de 0,1 a 28,8 MHz. Se usa para RADIOAFICIONADOS.

## 8. RTL-SDR Blog V3 · ✅ integrado (corrección: no es V4)

R820T2, TCXO, bias-tee y muestreo directo por la rama Q. Hace MULTIPERFIL y, hasta que llegue el SDRplay, la HF.

## 9. SDRplay · ⏳ pendiente (meses)

Ya está en la plantilla, desactivado. Al llegar: [manual 08](manuales/08_SDRPLAY.md).

## 10. Cargador USB multitoma de 45 W · ✅ integrado (caja v2.2)

| Requisito | Por qué |
|---|---|
| USB-C PD con perfil de **5 V 3 A** | la Pi 5 no arranca bien por debajo de 3 A |
| USB-A de **2,4 A** o más | alimenta el hub: 3 SDR y 2 LilyGO (~1,2 A) |
| Clase II, marcado CE, mejor con cable en «ocho» (C7) | va dentro de una caja de plástico. Con cable C7, el 230 V se empalma sin abrir el cargador |
| 65 × 95 × 30 mm como máximo | cabe en el compartimento de potencia |

- **Límite de la Pi:** solo negocia 5 A con la fuente oficial. Con este cargador limita sus USB a 0,6 A, y por eso los SDR van al hub ([ADR-16](ARQUITECTURA.md)).

## 11. Regleta / hub USB 2.0 alimentado · ✅ integrado (caja v2.2)

- **Requisitos:** 4 puertos o más, alimentado por USB o 5 V (desde el cargador, no con otro transformador de 230 V), y 40 × 100 × 22 mm como máximo.
- **Conexiones:** su «upstream» va a un USB 2.0 de la Pi. Las salidas van a Mini, V3, FlightStick y los 2 LilyGO.



---

# v3.0 · Evaluaciones nuevas

## 12. ¿Hay algo mejor que el SDRplay para la HF? · ✅ RSPdx-R2 (presupuesto: RSP1B)

El 4.º receptor es la HF multiusuario de la web: varias personas escuchando a la vez bandas distintas, en una Pi 5 que ya mueve tres RTL-SDR.

| Equipo | HF | Ancho visible | ADC | En OpenWebRX+ | ¿Vale en la Pi 5? | Precio aprox. |
|---|---|---|---|---|---|---|
| **SDRplay RSPdx-R2** | 1 kHz–2 GHz, 12 filtros, modo HDR < 2 MHz, 3 antenas (SMA B con bias-T) | hasta 10 MHz | 14 bits | sí (SoapySDRplay3) | **sí**: 2–6 MHz por perfil | ≈ 265 € + IVA |
| SDRplay RSP1B | 1 kHz–2 GHz, 1 antena | hasta 10 MHz | 14 bits | sí | sí | ≈ 140 € |
| Airspy HF+ Discovery | 0,5 kHz–31 MHz y 60–260 MHz | **≈ 0,66–0,77 MHz** | 18 bits | sí | sí, pero cada perfil ve **una sola banda** | ≈ 170–200 € |
| RX888 MkII | 0–64 MHz de una vez (muestreo directo) | 30+ MHz | 16 bits | sí (sddc, 64/128 MHz en 1.2.110) | **no**: necesita USB 3 continuo y un mini-PC; la Pi 5 se ahoga | ≈ 150 € |
| HydraSDR RFOne | **24–1800 MHz, sin HF** | 10 MHz | 12 bits | sí (desde 1.2.90) | sí | — |

- **Recomendación: SDRplay RSPdx-R2.** Es el único que junta HF de calidad, 10 MHz de ancho (varias bandas por perfil y muchos usuarios a la vez), filtros de preselección y tres entradas:
  - antena A al **lazo MLA-30**;
  - antena B a una antena de HF exterior futura;
  - el puerto C libre para VHF.
  - El plan ya está hecho: `HF_SDRPLAY=yes` y los perfiles `sp*` con programación día/crepúsculo/noche ([manual 08](manuales/08_SDRPLAY.md)).
- **Si el presupuesto manda:** RSP1B con los mismos perfiles.
- **No recomendado aquí:**
  - **Airspy HF+ Discovery:** el mejor receptor de HF «para una persona», pero sus ~0,7 MHz obligan a un perfil por banda y limitan a los oyentes simultáneos.
  - **RX888 MkII:** solo con un mini-PC x86 aparte.
- **HydraSDR RFOne:** no sirve para HF, pero es una mejora clara del MULTIPERFIL de VHF/UHF (12 bits, 10 MHz). Cabe en la bahía de expansión de la caja v3 si algún día se quiere sustituir el V3.

## 13. Cámara · ✅ dos opciones mejores que la WPI408

La Pi 5 **no tiene codificador H.264 por hardware**: la WPI408 se codifica por CPU y le quita potencia a los SDR. Con la caja a 5 m del mástil, una cámara CSI (cable ≤ 1 m) solo puede ver el mástil desde abajo.

| Opción | Ventajas | Cómo se instala |
|---|---|---|
| **A. Cámara IP PoE de exterior** (p. ej. Reolink RLC-510A: 5 MP, IP66, IR de 30 m, H.264, RTSP) **← recomendada** | En el mástil mismo, estanca, visión nocturna de verdad, **0 % de CPU en la Pi**: MediaMTX reenvía su H.264 tal cual | Inyector PoE (o switch PoE) en la caja · `CAM_SOURCE="rtsp"` y `CAM_RTSP_URL="rtsp://usuario:clave@IP:554/h264Preview_01_main"` (la clave, solo en bricohams.env) |
| **B. Raspberry Pi Camera Module 3 Wide NoIR** (IMX708, 12 MP, 120°, HDR, enfoque automático) | Mucho mejor que la OV5647: HDR para el contraluz del cielo, autofoco, 120° | Mismo cable de 22 pines y ventana de la tapa: `CAM_SOURCE="rpi"`. Sigue codificándose por CPU |

- La WPI408 queda como cámara de la caja (sirve para ver el interior o el pie del mástil) o de repuesto.

## 14. Filtros NMRF FBP-433s y FBP-868s · ✅ 433 en el iGate · ⚠️ 868 solo en recepción

| Filtro | Paso | Pérdida | Potencia máx. | Dónde |
|---|---|---|---|---|
| **FBP-433s** | 430–438 MHz (centro 433,92) | < 2,5 dB | **1 W (30 dBm)** | **iGate (433,775, solo RX)**: quita los repetidores de 70 cm de 438,6+ MHz, TETRA, la FM y la TDT, que saturan el SX1278 |
| **FBP-868s** | 866–870 MHz (SAW) | ~2,5–2,8 dB | **SAW: ~18 dBm** (comprobar la tuya) | No en el nodo 868 del HAT, que transmite a 22 dBm y quemaría el filtro. Solo si se mide bloqueo por LTE800 (791–821 MHz), y entonces con `lora.tx_power=17` |

- **El Meshtastic 433 (LilyGO con la antena de fibra)** puede llevar también un FBP-433s, porque aguanta 1 W y el LilyGO da 20 dBm. Pero se pierden 2,5 dB a la ida y a la vuelta. Pruébalo sin filtro y solo ponlo si hay interferencias.
- **Ningún filtro separa el Meshtastic 433 del iGate:** están a 100 kHz uno del otro. Eso solo se arregla con **separación vertical** (1,5 m en el plan del mástil, unos 40 dB de aislamiento).
- **Montaje:** dentro de la caja, entre el pasamuros N y el receptor, sujeto con `clip_filtro`, para que su peso no cuelgue del SMA del LilyGO.

## 15. LNA 1090 MHz (20,5 dB, NF 0,4 dB, «BIAS: yes») · ✅ en la antena, con bias-tee

- **Conviene, por el coaxial:** 7 m de bajada a 1090 MHz pierden 1,6 dB en LMR-400 y 4 dB en RG-58. Con el LNA en la antena, esa pérdida ya no suma ruido: lo fija el NF de 0,4 dB.
- **Cuidado con la saturación:**
  - El FlightStick ya lleva LNA y filtro SAW. 20 dB más, con el aeropuerto de Corvera a unos 25 km y el radar de Sierra Espuña, pueden saturar.
  - readsb con `--gain auto` (o bajar a 36–40 dB) lo compensa. Si en las estadísticas de readsb (`/run/readsb/stats.json`, campo `strong_signals`) más del 5 % de los mensajes son «fuertes», baja la ganancia.
- **Alimentación:**
  - Por el coaxial con un **bias-tee de 5 V** dentro de la caja, entre el pasamuros «ADSB» y el FlightStick. El bias-tee se alimenta del USB de la regleta.
  - El LNA pone «+5V MAX»: nunca le metas los 12 V del bus.
- **Montaje:** dentro de la base impresa `adsb_base`, justo bajo el radiante (manual 14).

## 16. Cargador USB de 120 W (foto) · ✅ sustituye al de 45 W

- **Margen:** la estación v3 consume 16–24 W, así que el cargador va al ~20 %: se calienta poco y tiene sitio para el SDRplay, otro SDR y los ventiladores.
- **Gatillo de 12 V:** con dos USB-C PD, uno va a la Pi y el otro, con un **gatillo PD de 12 V** (cable USB-C → 5,5 × 2,1 mm o bornes), da el bus de 12 V. Así hay un solo transformador de 230 V.
- **Comprobar** en su etiqueta que el USB-C ofrece **12 V**. Muchos cargadores GaN dan 5/9/12/15/20 V, pero algunos se saltan los 12 V. Si no los da: gatillo a 15 V + reductor DC-DC a 12 V, o el alimentador de la regleta (apartado 17).
- **Montaje:** es de enchufe directo, así que va en una **base Schuko de superficie** dentro del módulo de potencia, sujeto con `brida_cargador`.

## 17. Regleta USB Vansuny USB 3.0 + alimentador FX24E-120200C · ✅ integrada

- **El producto (ASIN B09Q2YC87C):** es un **hub USB 3.0 alimentado** de 12 × 3,4 × 1,8 cm (55 g). El FX24E-120200C es su **alimentador de 12 V 2 A** (24 W, clavija 5,5 × 2,5).
- **En la v3:** el hub se alimenta del **bus de 12 V** (fusible de 2 A) y el FX24E queda de repuesto. Su «upstream» USB 3.0 va al puerto azul de la Pi.
- **Cuelgan de él:** Mini, V3, FlightStick, los 2 LilyGO, el adaptador RS485, el inyector del MLA-30 y el bias-tee del LNA. Hacen falta 8 puertos: cuenta los de tu modelo y, si se queda corto, añade un segundo hub en cascada (el inyector y el bias-tee solo toman corriente: valen también en un cargador USB).

## 18. Lazo MLA-30 · ✅ antena de HF con carcasa estanca impresa

- **Datos del lazo:** activo de 0,1–30 MHz. El amplificador se alimenta por el coaxial (inyector de 12 V que sale del USB) y el kit trae 10 m de coaxial.
- **Problema:** su caja **no es estanca**, ni sus conectores.
- **Lo que se imprime:**
  - `mla_caja_base`/`mla_caja_tapa` con junta TPU (`mla_junta`): las medidas interiores son variables; mide la tuya.
  - `mla_cruz` + 4 `mla_clip_lazo`: cruz de fibra de vidrio que mantiene el lazo redondo.
  - `funda_sma`/`funda_n` de TPU para los empalmes.
- **Colocación:** a ≥ 5 m del mástil y de cables de red, en un poste **no metálico** a 2–3 m de altura. Es un receptor de campo magnético y capta el ruido de fuentes y LED cercanos.
- **Conexión:** al V3 por el diplexor HF/VHF (HF del lazo + VHF de la discone) y, cuando llegue, a la antena A del SDRplay.

## 19. Antenas Bigsignal 868 / 433 y fibra 433 · ✅ en brazos separados

- **Montaje:** van en los brazos de Ø25 con `soporte_fibra` + abrazaderas en U inox (el plástico solo reparte el apriete).
- **Separaciones:**
  - TX 868 ↔ iGate 433: 1,6 m.
  - TX 433 (fibra) ↔ iGate 433: 1,5 m en vertical.
  - Resto de receptores: ≥ 1,6 λ ([plan del mástil](esquemas/11_plan_mastil.png)).
- **Coaxial:** H155 o LMR-240 con N macho. Bucle de goteo antes de cada conector y `funda_n` con cinta autovulcanizante.

## 20. Caja de aluminio inyectado (foto) · ✅ caja de cabecera de la quad

- La caja de aluminio con pasamuros N y prensaestopas de la foto es ideal para el **diplexor 2 m/70 cm de la quad** (las dos alimentaciones entran y sale un solo coaxial), junto al mástil.
- **A tierra:** la caja va unida al mástil, que está conectado a tierra.
- **Si se usa para el LNA de 1090:** el LNA ya queda protegido en la base impresa de la antena, así que basta con la caja impresa.
