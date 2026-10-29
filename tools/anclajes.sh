#!/usr/bin/env bash
# Exporta los anclajes impresos (v4): crucetas para unir tubos sin abrazaderas en U,
# soportes de ADS-B, anemómetro/veleta, pluviómetro y la Pico. Comprueba que caben
# en la Kobra S1 y genera las vistas. Uso: tools/anclajes.sh   (necesita openscad)
set -euo pipefail
cd "$(dirname "$0")/../hardware/anclajes"
SCAD=anclajes_bricohams.scad
mkdir -p stl render
PIEZAS=(cruceta_mastil_brazo_cuerpo cruceta_mastil_brazo_tapa_brazo cruceta_mastil_brazo_tapa_mastil
        cruceta_mastil_quad_cuerpo cruceta_mastil_quad_tapa_boom cruceta_mastil_quad_tapa_mastil
        cruceta_brazo_fibra_cuerpo cruceta_brazo_fibra_tapa_fibra cruceta_brazo_fibra_tapa_brazo
        cruceta_brazo_tubo_cuerpo cruceta_brazo_tubo_tapa
        adsb_tapa_tubo sensor_viento_brida pluvio_vaso pluvio_plataforma pico_soporte)
for p in "${PIEZAS[@]}"; do
    echo "· $p"
    openscad -q -D "PART=\"$p\"" -o "stl/$p.stl" "$SCAD"
done
python3 ../../tools/stl_util.py binario stl
python3 ../../tools/stl_util.py medidas stl
if command -v xvfb-run >/dev/null; then
    xvfb-run -a openscad -q --colorscheme=Tomorrow --imgsize=1600,1000 -D 'PART="montaje"' --camera=230,80,0,60,0,30,1100 -o render/montaje.png "$SCAD"
fi
echo "Listo: hardware/anclajes/stl y render"
