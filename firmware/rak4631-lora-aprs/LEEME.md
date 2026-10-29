# BricoHams RAK APRS · firmware LoRa APRS para RAK4631 (WisBlock)

Port de **LoRa APRS iGate** de Ricardo Guzmán, CA2RXU (https://github.com/richonguzman/LoRa_APRS_iGate, revisión `9314bf1` del 07/10/2026), al nRF52840 + SX1262 del RAK4631. Licencia **GPL-3.0-or-later** (`LICENSE`): el código derivado conserva el aviso de copyright del original en la cabecera de cada fichero.

- **Qué hace el RAK** (como el original):
  - LoRa APRS a 433,775 MHz (SF12, BW 125 kHz, CR 4/5);
  - digipeater WIDE1-1 / WIDE2-n;
  - baliza, estado y telemetría (temperatura y humedad de la caja, batería, paquetes);
  - TNC KISS por USB.
- **Qué hace la Pi** (`files/bin/bricohams-rak-aprs`), que en el original se hace por WiFi:
  - APRS-IS;
  - mensajes a RF;
  - configuración;
  - mapa de OpenWebRX+.

Manual completo: [docs/manuales/35_LORA_APRS_MESHTASTIC.md](../../docs/manuales/35_LORA_APRS_MESHTASTIC.md).

| Carpeta / fichero | |
|---|---|
| `bin/` | binarios: `.zip` (DFU), `.uf2`, `.hex` y `SHA256SUMS` |
| `rak4631-lora-aprs.ino` | vacío a propósito: el código va en los `.cpp` |
| `test/` | `Arduino.h` mínimo para compilar la lógica en el PC (`tests/test_rak_aprs.py`) |

**Compilar:** `bash tools/compilar_rak.sh`. Necesita arduino-cli, el BSP de RAKwireless 1.3.3, RadioLib 7.6.0, ArduinoJson 7.4.3, TinyGPSPlus 1.0.3, Adafruit BME280 2.3.0 y BME680 2.0.6.

**Firmware precompilado:** [descarga el UF2 para flasheo web](https://github.com/Brico-Hams/bricohams-sdr/releases/download/fw-v5.4.1/bricohams-rak4631-lora-aprs-v1.0.1.uf2). El [resto de formatos y sus checksums](https://github.com/Brico-Hams/bricohams-sdr/releases/tag/fw-v5.4.1) están en la release pública.

**Grabar:**
- `sudo bricohams-rak-aprs grabar` (DFU por USB);
- o doble RESET y copiar el `.uf2` a la unidad `RAK4631`.
- Un RAK de fábrica con **RUI3** (USB `1915:521f`) hay que pasarlo antes a bootloader WisBlock (manual 35, apartado 3).

Los binarios publicados corresponden a la versión 1.0.1. Verifica `SHA256SUMS` antes de grabar y usa únicamente el firmware adecuado para el RAK4631.
