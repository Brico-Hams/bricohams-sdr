# 01 · Preparación del hardware y de la tarjeta

## Material
- **Placa y alimentación:**
  - Raspberry Pi 5 (4 u 8 GB).
  - Fuente: cargador USB multitoma de 45 W (en la caja) o la fuente oficial de 27 W (en el banco de pruebas).
  - Tarjeta microSD de 32 GB o más (A2), o un SSD NVMe.
- **Receptores y radios:**
  - HAT HackerGadgets RTL-SDR/LoRa/GPS/RTC con antenas de 868 MHz y GPS activa.
  - Mini RTL-SDR HackerGadgets, RTL-SDR Blog V3 y FlightStick de RadarBox.
  - 2 LilyGO T3 V1.6.1 de 433 MHz con sus antenas.
- **Sensor y cámara:**
  - Sensor GY-BME/BMP280, cable apantallado de 4 hilos y garita.
  - Cámara WPI408 con cable de 15 a 22 pines para Pi 5.
- **Conexiones:** hub USB 2.0 alimentado y diplexor HF/VHF para el V3.
- **Caja del mástil:** piezas impresas, tornillería, SMA pasamuros y prensaestopas ([manual 10](10_CAJA_3D.md)).
- **v3.0:** caja de dos módulos, antenas, ventiladores, sensores de viento y lluvia, filtros, LNA, coaxiales y vientos del mástil. La lista completa está en la [memoria técnica](../MEMORIA_TECNICA.md) (BOM consolidada) y en cada manual del 11 al 19.

## 1. Grabar la tarjeta
1. Abre **Raspberry Pi Imager**: Dispositivo **Raspberry Pi 5** → Sistema **Raspberry Pi OS (other) → Raspberry Pi OS Lite (64-bit)**.
   - Esa imagen es **Trixie** (Debian 13), la recomendada desde la v3.1.
   - También vale **Raspberry Pi OS (Legacy) Lite (64-bit)**, que es Bookworm (Debian 12).
   - **Si tu Pi ya tiene Trixie o Bookworm, no hace falta regrabar.** Compruébalo con `grep VERSION_CODENAME /etc/os-release`.
2. En la configuración avanzada (⚙️):
   - Nombre de equipo `bricohams-sdr` y usuario `pi`.
   - WiFi `BiohazardIT-5G` (país ES) o cable. El instalador añade después las dos redes de casa (paso `red`).
   - **Activar SSH.**
   - Zona horaria Europe/Madrid.
3. Graba y arranca la Pi **sin el HAT** la primera vez. Comprueba que entras por SSH: `ssh pi@bricohams-sdr.local`.

## 2. Montar el hardware (con la Pi apagada)
1. **HAT:**
   - Pínchalo en la cabecera de 40 pines con separadores.
   - Conecta las antenas de 868 MHz y GPS antes de encender: el SX1262 no debe transmitir sin antena.
   - Si su RTL-SDR va por USB, conéctalo a un USB 2.0 de la Pi.
2. **Cámara:**
   - Cable de 15 a 22 pines: lado de 22 pines en **CAM/DISP 0** de la Pi 5, con los contactos hacia el conector Ethernet. Lado de 15 pines en la cámara, con los contactos hacia la placa.
   - Monta los LED IR con sus tornillos.
3. **Sensor:** según el [esquema 03](../esquemas/03_cableado_bme280.png) y el [manual 06](06_SENSOR_WX.md).
4. **SDR y LilyGO:** sigue el [esquema de RF](../esquemas/04_rf_antenas_alimentacion.png).
   - Mini y V3 a los USB de la Pi.
   - FlightStick y los dos LilyGO al hub alimentado.
   - No los enchufes todavía si vas a grabar las series ([manual 03](03_SDR_Y_SERIES.md)): basta con dejarlos a mano.

## 3. Copiar el repositorio
```bash
sudo apt install -y git
git clone <git-interno-bricohams>/bricohams-sdr.git
cd bricohams-sdr
cp bricohams.env.example bricohams.env
nano bricohams.env
```
Siguiente: [02 · Instalación](02_INSTALACION.md).
