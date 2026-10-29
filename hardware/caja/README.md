# Caja de intemperie BricoHams SDR

Caja para el mástil Televés con toda la estación dentro. Va impresa en **PETG** (estructura) y **TPU 95A** (juntas) en una Anycubic Kobra S1.

![Montaje](render/montaje.png)

| Fichero | Qué es |
|---|---|
| `caja_bricohams.scad` | modelo paramétrico (OpenSCAD 2021 o posterior). Las medidas son variables al principio del fichero |
| `stl/` | 16 piezas en STL binario, ya orientadas para imprimir **sin soportes** |
| `render/` | vistas: montaje, interior, cara inferior, despiece y piezas en posición de impresión |

- **Montaje, material e impresión:** [docs/manuales/10_CAJA_3D.md](../../docs/manuales/10_CAJA_3D.md).
- **Decisiones:** ADR-15 y ADR-16 en [docs/ARQUITECTURA.md](../../docs/ARQUITECTURA.md).
- **Esquemas:** [06 alimentación](../../docs/esquemas/06_alimentacion_caja.png) y [07 distribución](../../docs/esquemas/07_caja_distribucion.png).

Regenerar tras cambiar una medida:

```bash
tools/caja.sh                                                  # todas las piezas, medidas y vistas
openscad -D 'PART="tapa"' -o tapa.stl hardware/caja/caja_bricohams.scad   # una sola pieza
python3 tests/test_caja.py                                     # comprobaciones
```

| Pieza | Material | Cant. |
|---|---|---|
| cuerpo, tapa, tejadillo, visera | PETG blanco | 1 de cada |
| tapa_potencia, placa_electronica, placa_potencia, soporte_camara | PETG | 1 de cada |
| soporte_mastil | PETG | 2 |
| garita_base, garita_tapa | PETG blanco | 1 de cada |
| garita_plato | PETG blanco | 6 |
| junta_tapa, junta_ventana, separador_ir, pasamuros_usb | TPU 95A | 1 de cada |
