#!/usr/bin/env bash
# Exporta las piezas de la caja v3 (módulos de electrónica y de potencia),
# comprueba que caben en la Kobra S1 y genera las vistas. Uso: tools/caja_v3.sh
set -euo pipefail
cd "$(dirname "$0")/../hardware/caja_v3"
SCAD=caja_v3.scad
mkdir -p stl render
COMUNES=(cuerpo tapa tejadillo placa_rejilla junta_tapa pletina_pared soporte_mastil)
SOLO_E=(bandeja poste_bandeja capota rejilla_ventilador soporte_dongle soporte_hub soporte_lilygo soporte_sdrplay soporte_wago tapon_n tapon_pg visera soporte_camara)
SOLO_P=(soporte_schuko brida_cargador tapon_pg)
for v in electronica potencia; do
    if [ "$v" = electronica ]; then lista=("${COMUNES[@]}" "${SOLO_E[@]}"); else lista=("${COMUNES[@]}" "${SOLO_P[@]}"); fi
    for p in "${lista[@]}"; do
        echo "· $v/$p"
        openscad -q -D "VARIANTE=\"$v\"" -D "PART=\"$p\"" -o "stl/${v}_$p.stl" "$SCAD"
    done
done
python3 ../../tools/stl_util.py binario stl
python3 ../../tools/stl_util.py medidas stl
if command -v xvfb-run >/dev/null; then
    R="xvfb-run -a openscad -q --colorscheme=Tomorrow --imgsize=1400,1050"
    $R -D 'VARIANTE="electronica"' -D 'PART="montaje"'  --camera=114,-40,120,72,0,30,820 -o render/electronica_montaje.png "$SCAD"
    $R -D 'VARIANTE="electronica"' -D 'PART="interior"' --camera=114,-40,120,55,0,18,720 -o render/electronica_interior.png "$SCAD"
    $R -D 'VARIANTE="electronica"' -D 'PART="montaje"'  --camera=114,-40,120,128,0,20,760 -o render/electronica_inferior.png "$SCAD"
    $R -D 'VARIANTE="potencia"'    -D 'PART="interior"' --camera=85,-40,100,55,0,18,600 -o render/potencia_interior.png "$SCAD"
    $R -D 'VARIANTE="potencia"'    -D 'PART="montaje"'  --camera=85,-40,100,72,0,30,640 -o render/potencia_montaje.png "$SCAD"
fi
echo "Listo: hardware/caja_v3/stl y render"
