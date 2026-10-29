#!/usr/bin/env bash
# Exporta las piezas impresas de antenas y soportes, comprueba que caben en
# la Kobra S1 y genera la vista. Uso: tools/antenas.sh   (necesita openscad)
set -euo pipefail
cd "$(dirname "$0")/../hardware/antenas"
SCAD=antenas_bricohams.scad
mkdir -p stl render
PIEZAS=(quad_buje_2m quad_buje_70 quad_puntera_8 quad_puntera_6 quad_clip_70 quad_alim_2m quad_alim_70 quad_abrazadera
        discone_aislador discone_plantilla_disco discone_plantilla_cono discone_adaptador_mastil discone_capuchon tapon_varilla
        adsb_base adsb_tapa adsb_radomo gps_soporte soporte_fibra brazo_mastil tapon_brazo separador_coax
        mla_caja_base mla_caja_tapa mla_junta mla_cruz mla_clip_lazo funda_sma funda_n clip_filtro)
for p in "${PIEZAS[@]}"; do
    echo "· $p"
    openscad -q -D "PART=\"$p\"" -o "stl/$p.stl" "$SCAD"
done
python3 ../../tools/stl_util.py binario stl
python3 ../../tools/stl_util.py medidas stl
if command -v xvfb-run >/dev/null; then
    xvfb-run -a openscad -q --colorscheme=Tomorrow --imgsize=1400,1000 -D 'PART="vista"' --camera=140,0,0,55,0,25,620 -o render/piezas.png "$SCAD"
fi
