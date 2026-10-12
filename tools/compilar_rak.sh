#!/bin/bash
# =====================================================================
#  tools/compilar_rak.sh · EA5KAO · BricoHams (v4.5)
#  Compila firmware/rak4631-lora-aprs para el RAK4631 y deja en bin/:
#    bricohams-rak4631-lora-aprs.zip  (DFU serie: sudo bricohams-rak-aprs grabar)
#    bricohams-rak4631-lora-aprs.uf2  (doble RESET y copiar a la unidad RAK4631)
#    bricohams-rak4631-lora-aprs.hex  (J-Link / RAKDAP1)
#  Necesita arduino-cli (https://arduino.github.io/arduino-cli) e Internet la primera vez.
#  Versiones fijas (las mismas con las que se compiló el binario del repositorio):
#    BSP RAKwireless nRF 1.3.3 · RadioLib 7.6.0 · ArduinoJson 7.4.3 · TinyGPSPlus 1.1.0
#    Adafruit BME280 2.3.0 · Adafruit BME680 2.0.6 · Adafruit Unified Sensor 1.1.15
#  Uso: bash tools/compilar_rak.sh            (en un PC o en la Pi)
# =====================================================================
set -euo pipefail
KIT=$(cd "$(dirname "$0")/.." && pwd)
FW="$KIT/firmware/rak4631-lora-aprs"
OUT="$FW/bin"
FQBN=rakwireless:nrf52:WisCoreRAK4631Board
IDX=https://raw.githubusercontent.com/RAKWireless/RAKwireless-Arduino-BSP-Index/main/package_rakwireless_index.json
CLI=${ARDUINO_CLI:-arduino-cli}
command -v "$CLI" >/dev/null || { echo "✘ Falta arduino-cli (curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh)"; exit 1; }
command -v adafruit-nrfutil >/dev/null || { echo "✘ Falta adafruit-nrfutil (pipx install adafruit-nrfutil)"; exit 1; }

"$CLI" core update-index --additional-urls "$IDX"
"$CLI" core install rakwireless:nrf52@1.3.3 --additional-urls "$IDX"
for l in "RadioLib@7.6.0" "ArduinoJson@7.4.3" "TinyGPSPlus@1.1.0" "Adafruit BME280 Library@2.3.0" \
         "Adafruit BME680 Library@2.0.6" "Adafruit Unified Sensor@1.1.15" "Adafruit BusIO"; do
    "$CLI" lib install "$l"
done
EXTRA="-DRADIOLIB_EXCLUDE_CC1101=1 -DRADIOLIB_EXCLUDE_RF69=1 -DRADIOLIB_EXCLUDE_SX1231=1 -DRADIOLIB_EXCLUDE_SI443X=1"
EXTRA+=" -DRADIOLIB_EXCLUDE_RFM2X=1 -DRADIOLIB_EXCLUDE_SX128X=1 -DRADIOLIB_EXCLUDE_SX127X=1 -DRADIOLIB_EXCLUDE_LR11X0=1"
EXTRA+=" -DRADIOLIB_EXCLUDE_NRF24=1"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
"$CLI" compile -b "$FQBN" --build-property "compiler.cpp.extra_flags=$EXTRA" --output-dir "$TMP" "$FW"
mkdir -p "$OUT"
cp "$TMP/rak4631-lora-aprs.ino.zip" "$OUT/bricohams-rak4631-lora-aprs.zip"
cp "$TMP/rak4631-lora-aprs.ino.hex" "$OUT/bricohams-rak4631-lora-aprs.hex"
UF2=$(find "${ARDUINO_DATA:-$HOME/.arduino15}" -path '*rakwireless*' -name uf2conv.py 2>/dev/null | head -1)
if [ -n "$UF2" ]; then
    python3 "$UF2" -f 0xADA52840 -c -o "$OUT/bricohams-rak4631-lora-aprs.uf2" "$OUT/bricohams-rak4631-lora-aprs.hex"
fi
# v5.1 · versión para «bricohams-rak-aprs puesta-en-marcha» (graba solo si el RAK lleva otra)
VER=$(sed -n 's/^#define FW_VERSION *"\([^"]*\)".*/\1/p' "$FW/configuration.h")
printf '{"version": "%s", "firmware": "BricoHams-RAK-APRS"}\n' "$VER" >"$OUT/VERSION.json"
(cd "$OUT" && sha256sum bricohams-rak4631-lora-aprs.* >SHA256SUMS)
echo "✔ Firmware en $OUT"
cat "$OUT/SHA256SUMS"
