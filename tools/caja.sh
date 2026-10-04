#!/usr/bin/env bash
# Exporta todas las piezas de la caja a STL, comprueba que caben en la
# Anycubic Kobra S1 (250 × 250 × 250 mm) y genera las vistas PNG.
#   uso: tools/caja.sh            (necesita openscad; las PNG, también xvfb-run)
set -euo pipefail
cd "$(dirname "$0")/../hardware/caja"
SCAD=caja_bricohams.scad
mkdir -p stl render

PIEZAS=(cuerpo tapa tapa_potencia placa_electronica placa_potencia tejadillo visera
        soporte_camara soporte_mastil junta_tapa junta_ventana separador_ir pasamuros_usb
        garita_base garita_plato garita_tapa)

for p in "${PIEZAS[@]}"; do
    echo "· $p"
    openscad -q -D "PART=\"$p\"" -o "stl/$p.stl" "$SCAD"
done

python3 ../../tools/stl_util.py binario stl
python3 ../../tools/stl_util.py medidas stl

if command -v xvfb-run >/dev/null; then
    R="xvfb-run -a openscad -q --colorscheme=Tomorrow --imgsize=1400,1050"
    $R -D 'PART="montaje"'  --camera=112,-40,116,75,0,30,800  -o render/montaje.png "$SCAD"
    $R -D 'PART="montaje"'  --camera=112,-40,116,75,0,215,800 -o render/montaje_trasera.png "$SCAD"
    $R -D 'PART="montaje"'  --camera=112,-40,116,128,0,20,760 -o render/montaje_inferior.png "$SCAD"
    $R -D 'PART="interior"' --camera=112,-40,116,60,0,20,700  -o render/interior.png "$SCAD"
    $R -D 'PART="despiece"' --camera=112,-80,116,72,0,40,1150 -o render/despiece.png "$SCAD"
    $R -D 'PART="cuerpo"'   --camera=112,116,45,35,0,20,700   -o render/cuerpo_impresion.png "$SCAD"
    $R -D 'PART="tapa"'     --camera=112,116,0,40,0,200,700   -o render/tapa_interior.png "$SCAD"
    for p in tapa_potencia placa_electronica tejadillo soporte_mastil garita_base visera soporte_camara pasamuros_usb; do
        $R -D "PART=\"$p\"" --autocenter --viewall -o "render/$p.png" "$SCAD"
    done
fi
echo "Listo: hardware/caja/stl y hardware/caja/render"
