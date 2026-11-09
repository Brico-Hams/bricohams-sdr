#!/usr/bin/env bash
# Renders every printed part (PNG per part) and every exploded/assembled view used by
# docs/manuales/52_MONTAJE_PIEZAS_IMPRESAS.md. No xvfb-run: run it on a machine with a display
# or with an OpenSCAD build that supports headless PNG export.
# Usage: tools/render_montaje.sh [group ...]   (groups: caja caja_v3 antenas anclajes; default: all)
set -euo pipefail

OPENSCAD=${OPENSCAD:-openscad}
cd "$(dirname "$0")/../hardware"

GROUPS_SEL=("$@")
[ ${#GROUPS_SEL[@]} -eq 0 ] && GROUPS_SEL=(caja caja_v3 antenas anclajes)

scad_of() {
  case "$1" in
    caja) echo "caja/caja_bricohams.scad" ;;
    caja_v3) echo "caja_v3/caja_v3.scad" ;;
    antenas) echo "antenas/antenas_bricohams.scad" ;;
    anclajes) echo "anclajes/anclajes_bricohams.scad" ;;
  esac
}

# render_part <group> <part> <png-name> [extra openscad args...]
render_part() {
  local g=$1 part=$2 name=$3; shift 3
  echo "[piezas] $g/$name"
  "$OPENSCAD" -o "$g/render/piezas/$name.png" -D "PART=\"$part\"" "$@" \
    --imgsize=800,600 --colorscheme=Tomorrow --viewall --autocenter \
    --camera=0,0,0,55,0,25,500 "$(scad_of "$g")"
}

# render_view <group> <view> <rx,ry,rz> [extra openscad args...]
render_view() {
  local g=$1 view=$2 rot=$3; shift 3
  echo "[montaje] $g/$view"
  "$OPENSCAD" -o "$g/render/montaje/$view.png" -D "PART=\"$view\"" "$@" \
    --imgsize=1600,1000 --colorscheme=Tomorrow --viewall --autocenter \
    --camera="0,0,0,$rot,500" "$(scad_of "$g")"
}

# render_pair <group> <suffix> <rx,ry,rz> [extra args...]: exploded + assembled
render_pair() {
  local g=$1 s=$2 rot=$3; shift 3
  render_view "$g" "vista_despiece_$s" "$rot" "$@"
  render_view "$g" "vista_montado_$s" "$rot" "$@"
}

want() { local x; for x in "${GROUPS_SEL[@]}"; do [ "$x" = "$1" ] && return 0; done; return 1; }

if want caja; then
  mkdir -p caja/render/piezas caja/render/montaje
  for p in cuerpo tapa tapa_potencia placa_electronica placa_potencia tejadillo visera soporte_camara \
           soporte_mastil junta_tapa junta_ventana separador_ir pasamuros_usb garita_base garita_plato garita_tapa; do
    render_part caja "$p" "$p"
  done
  render_pair caja caja_v2 60,0,25
  render_pair caja caja_v2_camara 60,0,25
  render_pair caja garita 60,0,25
fi

if want caja_v3; then
  mkdir -p caja_v3/render/piezas caja_v3/render/montaje
  COMUNES="cuerpo tapa tejadillo placa_rejilla junta_tapa pletina_pared soporte_mastil"
  ELECTRONICA="bandeja poste_bandeja bandeja_sdr poste_medio bandeja_sdr2 poste_superior capota rejilla_ventilador soporte_dongle soporte_hub soporte_lilygo soporte_rak soporte_sdrplay soporte_wago tapon_n tapon_pg visera soporte_camara"
  POTENCIA="soporte_schuko brida_cargador tapon_pg"
  SAI="soporte_bateria guia_pcb pletina_trafo soporte_filtro soporte_wago tapon_pg"
  for v in electronica potencia sai; do
    case "$v" in electronica) extra=$ELECTRONICA ;; potencia) extra=$POTENCIA ;; sai) extra=$SAI ;; esac
    for p in $COMUNES $extra; do
      render_part caja_v3 "$p" "${v}_$p" -D "VARIANTE=\"$v\""
    done
  done
  render_pair caja_v3 v3_electronica 60,0,25 -D 'VARIANTE="electronica"'
  render_pair caja_v3 v3_potencia 60,0,25 -D 'VARIANTE="potencia"'
  render_pair caja_v3 v3_sai 60,0,25 -D 'VARIANTE="sai"'
  render_pair caja_v3 v3_postes_bandejas 60,0,25 -D 'VARIANTE="electronica"'
  render_pair caja_v3 v3_soportes 60,0,25 -D 'VARIANTE="electronica"'
  render_pair caja_v3 v3_ventilacion 60,0,60 -D 'VARIANTE="electronica"'
  render_pair caja_v3 v3_camara 60,0,25 -D 'VARIANTE="electronica"'
  render_pair caja_v3 v3_tapones 70,0,35 -D 'VARIANTE="electronica"'
fi

if want antenas; then
  mkdir -p antenas/render/piezas antenas/render/montaje
  for p in quad_buje_2m quad_buje_70 quad_puntera_8 quad_puntera_6 quad_clip_70 quad_alim_2m quad_alim_70 \
           quad_abrazadera discone_aislador discone_plantilla_disco discone_plantilla_cono \
           discone_adaptador_mastil discone_capuchon tapon_varilla adsb_base adsb_tapa adsb_radomo gps_soporte \
           soporte_fibra brazo_mastil tapon_brazo separador_coax mla_caja_base mla_caja_tapa mla_junta mla_cruz \
           mla_clip_lazo funda_sma funda_n clip_filtro; do
    render_part antenas "$p" "$p"
  done
  render_pair antenas quad_buje 60,0,25
  render_pair antenas quad_alimentacion 60,0,25
  render_pair antenas quad_abrazadera 60,0,35
  render_pair antenas brazo_mastil 60,0,35
  render_pair antenas soporte_fibra 60,0,35
  render_pair antenas discone 70,0,25
  render_pair antenas discone_plantillas 60,0,25
  render_pair antenas adsb 60,0,25
  render_pair antenas mla 60,0,25
  render_pair antenas mla_cruz 60,0,25
  render_pair antenas gps 60,0,35
  render_pair antenas fundas_tapones 70,0,20
fi

if want anclajes; then
  mkdir -p anclajes/render/piezas anclajes/render/montaje
  for p in cruceta_mastil_brazo_cuerpo cruceta_mastil_brazo_tapa_brazo cruceta_mastil_brazo_tapa_mastil \
           cruceta_mastil_quad_cuerpo cruceta_mastil_quad_tapa_boom cruceta_mastil_quad_tapa_mastil \
           cruceta_brazo_fibra_cuerpo cruceta_brazo_fibra_tapa_fibra cruceta_brazo_fibra_tapa_brazo \
           cruceta_brazo_tubo_cuerpo cruceta_brazo_tubo_tapa adsb_tapa_tubo sensor_viento_brida \
           pluvio_vaso pluvio_plataforma pico_soporte; do
    render_part anclajes "$p" "$p"
  done
  for s in cruceta_mastil_brazo cruceta_mastil_quad cruceta_brazo_fibra cruceta_brazo_tubo pluviometro viento pico adsb_tubo; do
    render_pair anclajes "$s" 60,0,25
  done
fi

echo "Listo."
