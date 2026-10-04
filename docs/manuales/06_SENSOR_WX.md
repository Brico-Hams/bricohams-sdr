# 06 · Sensor BME280/BMP280 y estación WX APRS

![Cableado](../esquemas/03_cableado_bme280.png)

## 1. Cableado (con la Pi apagada)

| Módulo GYBMEP | Cable | Raspberry Pi 5 (o pines pasantes del HAT) |
|---|---|---|
| VIN | rojo | pin 1 · 3V3 |
| GND | negro | pin 9 · GND |
| SCL | amarillo | pin 5 · GPIO3 SCL1 |
| SDA | azul | pin 3 · GPIO2 SDA1 |

- **Alimentación:** a **3,3 V**. El módulo admite 5 V, pero el bus de la Pi es de 3,3 V.
- **Cable:** apantallado de 4 hilos, de unos 2 m como máximo. Para más distancia, usa un extensor P82B715 en cada punta.
- **Ubicación:** en una **garita de radiación** a la sombra, a 1,5–2 m del suelo y lejos de la caja de la Pi.

## 2. Comprobar
```bash
sudo i2cdetect -y 1          # deben salir 51 (o UU: RTC) y 76 o 77 (sensor)
sudo bricohams-wx --una      # una lectura y el paquete APRS que mandaría
sudo systemctl restart bricohams-wx
sudo bricohams-check         # sección "Sensor BME280/BMP280"
```
El chip se reconoce solo: **BME280** (ID 0x60) mide humedad y **BMP280** (ID 0x58) no.

## 3. Qué publica
- **Web:** ventana 🌡️ METEO de OpenWebRX. Arriba sale la tarjeta «🏠 EA5KAO · Mi QTH» con temperatura, humedad, punto de rocío, presión a nivel del mar y en el QTH, y la curva de 24 h. El botón de la barra muestra la temperatura.
- **APRS-IS:** cada 10 min, como **EA5KAO-13**:
  ```
  EA5KAO-13>APZBHW,TCPIP*:!3804.94N/00115.21W_.../...g...t072h55b10143WX BricoHams Mi QTH - BME280
  ```
  Se ve en https://aprs.fi/#!call=EA5KAO-13

## 4. Ajustes (`bricohams.env`, después `sudo bash install.sh --solo sensor`)

| Variable | Para qué |
|---|---|
| `WX_SENSOR_HEIGHT` | altura del sensor sobre el suelo, para reducir la presión al nivel del mar |
| `WX_TEMP_OFFSET` | corrección de temperatura si la garita calienta o enfría |
| `WX_APRS` | `no` para no publicar en APRS |
| `WX_APRS_CALLSIGN` | indicativo de la estación WX |
