# 52 · Montaje de las piezas impresas en 3D
<!-- guia-visual:inicio -->
> **Ruta visual:** [Caja, antenas, filtros, alimentación y anclajes](../GUIA_VISUAL_MODULOS.md#hardware).
> Consulta allí requisitos, ilustración, cuadro de instalación, comprobaciones y restauración.
> Los comandos de este manual se ejecutan en Bash en la Pi; revisa el backup antes de cambiarla.
<!-- guia-visual:fin -->

![BricoHams](../../files/htdocs/plugins/receiver/marca/bricohams-logo.png)

**BricoHams SDR · montaje paso a paso de todas las piezas impresas de la estación**

Autores: Anatol EA5KAO · Diego EA5JEF · Pedro Roca Molina · <https://bricohams.org>

Este manual reúne, en un solo sitio, el **orden de montaje de las 110 piezas STL** del kit:
caja v2, caja v3 (electrónica, potencia y SAI), antenas y anclajes. No sustituye a los manuales
[10](10_CAJA_3D.md), [11](11_MASTIL_Y_ANTENAS.md), [12](12_QUAD_2M70.md), [13](13_DISCONES.md),
[14](14_ADSB_LNA.md), [15](15_LAZO_MLA30.md), [17](17_CAJA_V3.md), [18](18_VENTILACION.md),
[19](19_VIENTO_Y_LLUVIA.md), [20](20_PICO_IO.md) y [21](21_ANCLAJES.md): ellos explican el cableado,
la RF y la puesta en marcha; este explica **cómo se ensamblan las piezas**.

> **Regla de este manual.** Las cotas, tornillos e insertos salen de los ficheros `.scad` de
> `hardware/` y de los manuales citados. Lo que no figura en ninguno se marca como
> **PENDIENTE DE CONFIRMAR**: no lo des por bueno sin medirlo en tu pieza. Si un manual y el `.scad`
> discrepan, manda el `.scad` y la discrepancia se indica.
>
> ⚠ **Seguridad.** La caja v2 y los módulos de potencia y SAI de la v3 alojan 230 V. Trabaja siempre
> sin tensión y con diferencial de 30 mA aguas arriba. El SAI debe estar desenchufado, con la batería
> desconectada y con 5 minutos de espera. El trabajo en altura y en red eléctrica requiere personal
> cualificado y cumplir la normativa local.

## Índice

1. [Material, herramientas y consumibles](#1-material-herramientas-y-consumibles)
2. [Tabla maestra de piezas (110 STL)](#2-tabla-maestra-de-piezas-110-stl)
3. [Convenciones comunes de montaje](#3-convenciones-comunes-de-montaje)
4. [Grupo A · Caja v2](#4-grupo-a--caja-v2)
5. [Grupo B · Caja v3: electrónica](#5-grupo-b--caja-v3-electrónica)
6. [Grupo C · Caja v3: potencia y SAI](#6-grupo-c--caja-v3-potencia-y-sai)
7. [Grupo D · Antenas: quad 2 m / 70 cm](#7-grupo-d--antenas-quad-2-m--70-cm)
8. [Grupo E · Antenas: discones y ADS-B](#8-grupo-e--antenas-discones-y-ads-b)
9. [Grupo F · Antenas: MLA-30, GPS y accesorios RF](#9-grupo-f--antenas-mla-30-gps-y-accesorios-rf)
10. [Grupo G · Anclajes: crucetas](#10-grupo-g--anclajes-crucetas)
11. [Grupo H · Anclajes: sensores y Pico](#11-grupo-h--anclajes-sensores-y-pico)
12. [Mapa de piezas en el mástil y montaje final](#12-mapa-de-piezas-en-el-mástil-y-montaje-final)
13. [Lista de comprobación antes de subir al mástil](#13-lista-de-comprobación-antes-de-subir-al-mástil)
14. [Valores pendientes de confirmar](#14-valores-pendientes-de-confirmar)

| Diagrama | Grupo |
|---|---|
| [31_montaje_caja_v2.svg](../esquemas/31_montaje_caja_v2.svg) | A · Caja v2 |
| [32_montaje_caja_v3_electronica.svg](../esquemas/32_montaje_caja_v3_electronica.svg) | B · Caja v3 electrónica |
| [33_montaje_caja_v3_potencia_sai.svg](../esquemas/33_montaje_caja_v3_potencia_sai.svg) | C · Potencia y SAI |
| [34_montaje_quad.svg](../esquemas/34_montaje_quad.svg) | D · Quad 2 m / 70 cm |
| [35_montaje_discone_adsb.svg](../esquemas/35_montaje_discone_adsb.svg) | E · Discones y ADS-B |
| [36_montaje_mla_gps.svg](../esquemas/36_montaje_mla_gps.svg) | F · MLA-30, GPS y accesorios |
| [37_montaje_crucetas.svg](../esquemas/37_montaje_crucetas.svg) | G · Crucetas |
| [38_montaje_sensores_pico.svg](../esquemas/38_montaje_sensores_pico.svg) | H · Sensores y Pico |
| [39_mapa_piezas_mastil.svg](../esquemas/39_mapa_piezas_mastil.svg) | Mapa en el mástil |

Los diagramas se generan con `python3 tools/esquemas.py`. Los números de los círculos naranjas
coinciden con los números de paso agrupados de cada sección.

## 1. Material, herramientas y consumibles

**Impresión.** Anycubic Kobra S1 (250 × 250 × 250 mm) con ASA, según el
[manual 43](43_KOBRA_S1_ASA.md). El TPU 95A no es compatible con la ACE Pro: se imprime desde el
portabobinas externo. Los perfiles de ese manual **no están validados**: haz una prueba antes de imprimir
una caja completa. Importa los STL al 100 %, sin escalar ni compensar contracción.
Las piezas grandes de la v3 (cuerpo de electrónica 246 × 244,6 × 199 mm) **no caben con un borde de 5 mm**:
imprímelas sin borde o con otra orientación ([manual 43](43_KOBRA_S1_ASA.md)).

| Herramienta / consumible | Para qué |
|---|---|
| Soldador con punta para insertos | Insertos roscados de latón: 230-245 °C en la v2 y 220 °C en la v3 |
| Insertos de latón M3 (agujero 4,0 × 6 mm), M4 (5,6 × 8,5 mm) y M5 (agujero de 7,0 mm en la v3) | Roscas en el plástico |
| Tornillería M2, M2.5, M3, M4, M5, M6 y M8 | Ver tabla maestra y cada grupo |
| Tuercas hexagonales M6 (11,3 × 5,4 mm), tuercas ciegas M4 | Crucetas y garita |
| Arandelas planas y de goma | Tapas, tejadillo y crucetas |
| TPU 95A | `*_junta_*`, `pasamuros_usb`, `tapon_*`, fundas: se imprimen, no se compran |
| Pasamuros SMA con junta tórica, pasamuros N, prensaestopas PG7, PG9, M20 y M25 | Entradas de cable y RF |
| Cianoacrilato | 4 puntos por junta de tapa en la v3 |
| Cinta autoamalgamante, bridas, silicona neutra | Fundas, sujeción de coaxial, radomo y capuchón |
| Abrazaderas de tornillo sin fin de 12 mm, U de M8 y M6 | Fijación al mástil |
| Llaves Allen, llaves fijas y destornilladores | Apriete. Par de apriete: **PENDIENTE DE CONFIRMAR** |
| Calibre o pie de rey, nivel | Comprobar agujeros y la plataforma del pluviómetro |
| Multímetro y NanoVNA | Comprobaciones previas ([manual 45](45_NANOVNA.md)) |

## 2. Tabla maestra de piezas (110 STL)

Cada STL existente aparece **una sola vez**. Los STL están en `hardware/<grupo>/stl/`:
caja v2 16, caja v3 48 (25 de electrónica, 10 de potencia y 13 de SAI), antenas 30 y anclajes 16.
«Como exportada» significa que se imprime en la orientación en que está el STL.
La columna de soportes recoge los agujeros en forma de gota, que no necesitan soportes; cuando el `.scad` y los
manuales no lo dicen, se marca **PENDIENTE DE CONFIRMAR**.
Materiales de la caja v2: [manual 10](10_CAJA_3D.md); caja v3: [manual 17](17_CAJA_V3.md);
antenas: manuales [12](12_QUAD_2M70.md) y [13](13_DISCONES.md); anclajes: [manual 21](21_ANCLAJES.md).

### 2.1 Caja v2 (`hardware/caja/stl/`, 16 piezas)

PETG blanco con 8 perímetros, gyroide al 25 % y borde de 5 mm en `cuerpo` y `tapa` ([manual 10](10_CAJA_3D.md)).

| Archivo | Grupo | Cant. | Material | Orientación | Soportes | Tornillería / insertos / juntas |
|---|---|---|---|---|---|---|
| `cuerpo.stl` | A | 1 | PETG blanco | Trasera sobre la cama ([render](../../hardware/caja/render/cuerpo_impresion.png)) | No | Insertos M4 (8 orejas y 8 de soportes de mástil), M3 en bosses; 9 SMA, PG7, M20, PG9 |
| `tapa.stl` | A | 1 | PETG blanco | Cara exterior sobre la cama | No | 8 × M4×12 con arandela; ranura para `junta_tapa` |
| `tapa_potencia.stl` | A | 1 | PETG | Como exportada | No | 4 insertos M3 · 4 × M3×8 |
| `placa_electronica.stl` | A | 1 | PETG | Como exportada | No | 4 × M3×8 a bosses · Pi 5: 4 × M2.5×6 autorroscantes |
| `placa_potencia.stl` | A | 1 | PETG | Como exportada | No | 4 × M3×8 a bosses |
| `tejadillo.stl` | A | 1 | PETG blanco | Como exportada | No | 4 insertos M4 · 2 × M4×30 (traseros) + 2 × M4×25 (delanteros) con arandelas de goma |
| `visera.stl` | A | 1 | PETG blanco | Como exportada | No | 2 insertos M3 · 2 × M3×8 |
| `soporte_camara.stl` | A | 1 | PETG negro | Como exportada | No | 2 insertos M3 · 2 × M3×35; espuma de 1 mm |
| `soporte_mastil.stl` | A | 2 | PETG | Como exportada | No | 4 × M4×20 por soporte · abrazaderas de 12 mm |
| `garita_base.stl` | A | 1 | PETG blanco | Como exportada | No | 3 varillas M4×140 · tuercas ciegas · 2 × M2×8 (sensor) |
| `garita_plato.stl` | A | 6 | PETG blanco | Como exportada | No | 3 varillas M4×140 (comunes) |
| `garita_tapa.stl` | A | 1 | PETG blanco | Como exportada | No | Tuercas ciegas M4 |
| `junta_tapa.stl` | A | 1 | TPU 95A | Como exportada | No | Va en la ranura de la tapa (4,4 × 4 mm) |
| `junta_ventana.stl` | A | 1 | TPU 95A | Como exportada | No | Con policarbonato; junta de 1,5 mm |
| `separador_ir.stl` | A | 1 | TPU 95A negro | Como exportada | No | Opcional / no necesario con Camera Module 3 Wide (evita reflejos de los LED IR de la WPI408) |
| `pasamuros_usb.stl` | A | 1 | TPU 95A | Como exportada | No | Paso del tabique (hueco de 18 × 34 mm), 5 pasos de cable |

### 2.2 Caja v3 (`hardware/caja_v3/stl/`, 48 piezas)

Salvo indicación, las piezas rígidas v3 son de ASA blanco; `cuerpo` y `tapa`, con 9 perímetros y gyroide al 30 %;
`tejadillo`, con 6 perímetros; `placa_rejilla`, al 40 %; `pletina_pared` y `soporte_mastil`, al 60 %;
bandejas y postes, al 40 % con 4 perímetros; `capota`, `rejilla_ventilador`, `visera` y `soporte_camara`, al 30 %;
soportes de dongle, hub, LilyGO, RAK, SDRplay y WAGO, `soporte_schuko` y `brida_cargador`, al 40 %;
`soporte_bateria`, al 60 % con 6 perímetros; `guia_pcb`, `pletina_trafo`, `soporte_filtro` y `soporte_wago` del SAI, al 50 %;
el TPU (`junta_tapa`, `tapon_n`, `tapon_pg`), al 100 % ([manual 17](17_CAJA_V3.md)).
Orientación: cuerpo boca arriba; tapa con la cara exterior sobre la cama; el resto, como exportada.

**Electrónica (25)**

| Archivo | Grupo | Cant. | Material | Orientación | Soportes | Tornillería / insertos / juntas |
|---|---|---|---|---|---|---|
| `electronica_cuerpo.stl` | B | 1 | ASA | Boca arriba | No | Insertos M4 (orejas y pilares), M5 traseros; N 16,2 mm; M25, M20, PG7 |
| `electronica_tapa.stl` | B | 1 | ASA | Cara exterior sobre la cama | No | 8 × M4×16 (8 orejas en el `.scad`) |
| `electronica_junta_tapa.stl` | B | 1 | TPU 95A | Como exportada | No | Ranura de 5,8 mm; 4 puntos de cianoacrilato |
| `electronica_tejadillo.stl` | B | 1 | ASA | Como exportada | No | 4 insertos M4; M4 (longitud PENDIENTE DE CONFIRMAR) |
| `electronica_placa_rejilla.stl` | B | 1 | ASA, 40 % | Como exportada | No | Insertos M3 en cada nudo; 5 × M3 a bosses |
| `electronica_poste_bandeja.stl` | B | 6 | ASA | Como exportada | No | M3: longitud PENDIENTE DE CONFIRMAR |
| `electronica_bandeja_sdr.stl` | B | 1 | ASA, 40 % | Como exportada | No | Sobre 6 postes; bridas |
| `electronica_poste_medio.stl` | B | 6 | ASA | Como exportada | No | M3: PENDIENTE DE CONFIRMAR |
| `electronica_bandeja_sdr2.stl` | B | 1 | ASA, 40 % | Como exportada | No | Sobre 6 postes medios |
| `electronica_poste_superior.stl` | B | 4 | ASA | Como exportada | No | M3: PENDIENTE DE CONFIRMAR |
| `electronica_bandeja.stl` | B | 1 | ASA, 40 % | Como exportada | No | Pi 5: M2.5 autorroscante (agujero 2,4 mm) |
| `electronica_soporte_dongle.stl` | B | 3 (fila de la rejilla; más en la segunda bandeja: PENDIENTE DE CONFIRMAR) | ASA, 40 % | Como exportada | No | M3 o bridas: PENDIENTE DE CONFIRMAR |
| `electronica_soporte_hub.stl` | B | 1 | ASA, 40 % | Como exportada | No | Dos ranuras para bridas |
| `electronica_soporte_sdrplay.stl` | B | 1 | ASA, 40 % | Como exportada | No | Fijación: PENDIENTE DE CONFIRMAR |
| `electronica_soporte_lilygo.stl` | B | 1 | ASA, 40 % | Como exportada | No | M3 o bridas: PENDIENTE DE CONFIRMAR |
| `electronica_soporte_rak.stl` | B | 1 | ASA, 40 % | Como exportada | No | M3 o bridas: PENDIENTE DE CONFIRMAR |
| `electronica_soporte_wago.stl` | B | 1 | ASA, 40 % | Como exportada | No | Para 3 WAGO 221-415; fijación PENDIENTE DE CONFIRMAR |
| `electronica_rejilla_ventilador.stl` | B | 2 | ASA, 30 % | Como exportada | No | Malla inox 1 mm; tornillos del ventilador a 50 mm (3,6 mm) |
| `electronica_capota.stl` | B | 2 | ASA, 30 % | Como exportada | No | Boca hacia abajo; fijación PENDIENTE DE CONFIRMAR |
| `electronica_tapon_n.stl` | B | Los N libres | TPU 95A | Como exportada | No | A presión en agujero de 16,2 mm: PENDIENTE DE CONFIRMAR |
| `electronica_tapon_pg.stl` | B | Los PG libres (y el respiradero VENT) | TPU 95A | Como exportada | No | En PG7; con respiradero (membrana ePTFE) para VENT |
| `electronica_soporte_camara.stl` | B | 1 (opcional) | ASA, 30 % | Como exportada | No | 4 × M2 autorroscantes o insertos M2 · 2 insertos M3 de collar |
| `electronica_visera.stl` | B | 1 (opcional) | ASA, 30 % | Como exportada | No | 2 × M3 |
| `electronica_pletina_pared.stl` | B | 2 | ASA, 60 % | Como exportada | No | M5 (longitud PENDIENTE DE CONFIRMAR) + 4 tacos |
| `electronica_soporte_mastil.stl` | B | 2 (alternativa a la pletina) | ASA, 60 % | Como exportada | No | M5 + U M8 |

**Potencia (10)**

| Archivo | Grupo | Cant. | Material | Orientación | Soportes | Tornillería / insertos / juntas |
|---|---|---|---|---|---|---|
| `potencia_cuerpo.stl` | C | 1 | ASA | Boca arriba | No | Insertos M4 (orejas y pilares), M5 traseros; PG9, M25 y PG7 VENT |
| `potencia_tapa.stl` | C | 1 | ASA | Cara exterior sobre la cama | No | 6 × M4×16 (6 orejas en el `.scad`) |
| `potencia_junta_tapa.stl` | C | 1 | TPU 95A | Como exportada | No | Ranura de 5,8 mm |
| `potencia_tejadillo.stl` | C | 1 | ASA | Como exportada | No | 4 insertos M4 |
| `potencia_placa_rejilla.stl` | C | 1 | ASA, 40 % | Como exportada | No | Bosses M3 |
| `potencia_soporte_schuko.stl` | C | 1 | ASA, 40 % | Como exportada | No | M4 a ±30 mm + 4 × M3 |
| `potencia_brida_cargador.stl` | C | 1 | ASA, 40 % | Como exportada | No | 2 × M3 |
| `potencia_pletina_pared.stl` | C | 2 | ASA, 60 % | Como exportada | No | M5 + 4 tacos |
| `potencia_soporte_mastil.stl` | C | 2 (alternativa) | ASA, 60 % | Como exportada | No | M5 + U M8 |
| `potencia_tapon_pg.stl` | C | Los PG libres | TPU 95A | Como exportada | No | A presión |

**SAI (13)**

| Archivo | Grupo | Cant. | Material | Orientación | Soportes | Tornillería / insertos / juntas |
|---|---|---|---|---|---|---|
| `sai_cuerpo.stl` | C | 1 | ASA | Boca arriba | No | Insertos M4 y M5; PG9 ×2, PG7; ventilas superior e inferior |
| `sai_tapa.stl` | C | 1 | ASA | Cara exterior sobre la cama | No | 8 × M4×16 (8 orejas en el `.scad`) |
| `sai_junta_tapa.stl` | C | 1 | TPU 95A | Como exportada | No | Ranura de 5,8 mm |
| `sai_tejadillo.stl` | C | 1 | ASA | Como exportada | No | 4 insertos M4 |
| `sai_placa_rejilla.stl` | C | 1 | ASA, 40 % | Como exportada | No | Bosses M3 |
| `sai_soporte_bateria.stl` | C | 1 | ASA, 60 %, 6 perímetros | Como exportada | No | Correas por ventanas de correa (22 mm en el `.scad`; 20 mm en los manuales) |
| `sai_guia_pcb.stl` | C | 2 | ASA, 50 % | Como exportada | No | M3 prisionero (ranura 2,2 mm) |
| `sai_pletina_trafo.stl` | C | 1 | ASA, 50 % | Como exportada | No | Agujeros ranurados M5 |
| `sai_soporte_filtro.stl` | C | 2 | ASA, 50 % | Como exportada | No | Ranuras M4 |
| `sai_soporte_wago.stl` | C | 1 | ASA, 50 % | Como exportada | No | Fijación PENDIENTE DE CONFIRMAR |
| `sai_pletina_pared.stl` | C | 2 | ASA, 60 % | Como exportada | No | M5 + 4 tacos |
| `sai_soporte_mastil.stl` | C | 2 (alternativa) | ASA, 60 % | Como exportada | No | M5 + U M8 |
| `sai_tapon_pg.stl` | C | Los PG libres | TPU 95A | Como exportada | No | A presión |

### 2.3 Antenas (`hardware/antenas/stl/`, 30 piezas)

Material general: ASA o PETG blanco; fundas, junta y tapones en TPU 95A ([manuales 12](12_QUAD_2M70.md) y
[13](13_DISCONES.md)). Perímetros, relleno y orientación de impresión no figuran en el `.scad`:
se marcan **PENDIENTE DE CONFIRMAR**, salvo en las piezas con agujeros en gota.

| Archivo | Grupo | Cant. | Material | Orientación | Soportes | Tornillería / insertos / juntas |
|---|---|---|---|---|---|---|
| `quad_buje_2m.stl` | D | 2 | ASA / PETG blanco | PENDIENTE DE CONFIRMAR | No (agujeros en gota) | M3 autorroscante en varilla; 2 prisioneros M5 por buje |
| `quad_buje_70.stl` | D | 2 | ASA / PETG blanco | PENDIENTE DE CONFIRMAR | No (agujeros en gota) | M3 autorroscante; 2 prisioneros M5 por buje |
| `quad_puntera_8.stl` | D | 7 | ASA / PETG blanco | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | Sobre varilla Ø8 |
| `quad_puntera_6.stl` | D | 8 | ASA / PETG blanco | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | Sobre varilla Ø6 |
| `quad_clip_70.stl` | D | 3 | ASA / PETG blanco | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | Sin tornillería indicada |
| `quad_alim_2m.stl` | D | 1 | ASA / PETG blanco | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | 2 insertos M3 de latón (terminales a 12 mm) |
| `quad_alim_70.stl` | D | 1 | ASA / PETG blanco | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | 2 insertos M3 de latón (terminales a 12 mm) |
| `quad_abrazadera.stl` | D | 1 | ASA / PETG blanco | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | U M8 (mástil) y U M6 (boom): medidas PENDIENTE DE CONFIRMAR |
| `discone_aislador.stl` | E | 1 por discone | ASA / PETG blanco | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | 3 insertos M4 arriba y 3 abajo |
| `discone_plantilla_disco.stl` | E | 1 | ASA / PETG blanco | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | Herramienta, 12 agujeros |
| `discone_plantilla_cono.stl` | E | 1 | ASA / PETG blanco | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | Herramienta, semiángulo 30° |
| `discone_adaptador_mastil.stl` | E | 1 | ASA / PETG blanco | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | 4 × M4 al cubo; 2 × M6 pasantes |
| `discone_capuchon.stl` | E | 1 | ASA / PETG blanco | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | Sobre el cubo del disco, con silicona neutra ([manual 13](13_DISCONES.md)) |
| `tapon_varilla.stl` | E | 12 | TPU 95A | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | Agujero Ø2,5 para cordino; fijación a la varilla PENDIENTE DE CONFIRMAR |
| `adsb_base.stl` | E | 1 | ASA / PETG blanco | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | SMA de panel 6,6 mm; PG7 12,7 mm; 4 agujeros de 2,8 mm |
| `adsb_tapa.stl` | E | 1 | ASA / PETG blanco | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | 4 × M3 + junta TPU de 1 mm |
| `adsb_radomo.stl` | E | 1 | ASA / PETG blanco | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | Silicona neutra ([manual 14](14_ADSB_LNA.md)); tornillos PENDIENTE DE CONFIRMAR |
| `mla_caja_base.stl` | F | 1 | ASA / PETG blanco | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | 4 bosses M3; PG7 |
| `mla_caja_tapa.stl` | F | 1 | ASA / PETG blanco | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | 4 × M3×12 inox ([manual 15](15_LAZO_MLA30.md)) |
| `mla_junta.stl` | F | 1 | TPU 95A (1,6 mm) | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | Entre base y tapa |
| `mla_cruz.stl` | F | 1 | ASA / PETG blanco | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | U M6; varillas Ø10 |
| `mla_clip_lazo.stl` | F | 4 | ASA / PETG blanco | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | Para coaxial Ø7 |
| `gps_soporte.stl` | F | 1 | ASA / PETG blanco | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | 4 agujeros M6 (Ø6,6): tornillería PENDIENTE DE CONFIRMAR |
| `soporte_fibra.stl` | F | 3 | ASA / PETG blanco | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | M6 (longitud PENDIENTE DE CONFIRMAR) |
| `brazo_mastil.stl` | F | 4 | ASA / PETG blanco | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | M8 al mástil y M6 al brazo: medidas PENDIENTE DE CONFIRMAR |
| `tapon_brazo.stl` | F | 6 | ASA / PETG blanco | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | Fijación PENDIENTE DE CONFIRMAR |
| `separador_coax.stl` | F | 15 | ASA / PETG blanco | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | 1 brida (medida PENDIENTE DE CONFIRMAR); coaxial Ø7,5 |
| `clip_filtro.stl` | F | PENDIENTE DE CONFIRMAR | ASA / PETG blanco | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | 1 brida (medida PENDIENTE DE CONFIRMAR); filtro de unos 13 × 13 mm |
| `funda_sma.stl` | F | 6 (manual 11) | TPU 95A | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | Cinta autoamalgamante |
| `funda_n.stl` | F | 12 (manual 11) | TPU 95A | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | Cinta autoamalgamante |

### 2.4 Anclajes (`hardware/anclajes/stl/`, 16 piezas)

Material: ASA o PETG blanco ([manual 21](21_ANCLAJES.md)). Cada cruceta lleva 4 × M6×50 (lado mástil) o M6×40
(boom, fibra, tubo), 4 tuercas M6, 4 arandelas y 2 tornillos autotaladrantes de 4,8 × 19 mm.

| Archivo | Grupo | Cant. | Material | Orientación | Soportes | Tornillería / insertos / juntas |
|---|---|---|---|---|---|---|
| `cruceta_mastil_brazo_cuerpo.stl` | G | 3 | ASA / PETG blanco | Como exportada | No | 4 tuercas hex M6 (11,3 × 5,4 mm) |
| `cruceta_mastil_brazo_tapa_mastil.stl` | G | 3 | ASA / PETG blanco | Como exportada | No | 2 × M6×50 + 2 arandelas + 1 autotaladrante 4,8 × 19 |
| `cruceta_mastil_brazo_tapa_brazo.stl` | G | 3 | ASA / PETG blanco | Como exportada | No | 2 × M6×40 + 2 arandelas + 1 autotaladrante 4,8 × 19 |
| `cruceta_mastil_quad_cuerpo.stl` | G | 1 | ASA / PETG blanco | Como exportada | No | 4 tuercas hex M6 |
| `cruceta_mastil_quad_tapa_mastil.stl` | G | 1 | ASA / PETG blanco | Como exportada | No | 2 × M6×50 + autotaladrante |
| `cruceta_mastil_quad_tapa_boom.stl` | G | 1 | ASA / PETG blanco | Como exportada | No | 2 × M6×40 + autotaladrante |
| `cruceta_brazo_fibra_cuerpo.stl` | G | 1 | ASA / PETG blanco | Como exportada | No | 4 tuercas hex M6 |
| `cruceta_brazo_fibra_tapa_brazo.stl` | G | 1 | ASA / PETG blanco | Como exportada | No | 2 × M6×40 + autotaladrante |
| `cruceta_brazo_fibra_tapa_fibra.stl` | G | 1 | ASA / PETG blanco | Como exportada | No | 2 × M6×40 + autotaladrante |
| `cruceta_brazo_tubo_cuerpo.stl` | G | 5 según uso (manual 21: ADS-B, 2 Bigsignal y 2 sensores de viento) | ASA / PETG blanco | Como exportada | No | 4 tuercas hex M6 |
| `cruceta_brazo_tubo_tapa.stl` | G | 2 por cuerpo | ASA / PETG blanco | Como exportada | No | 2 × M6×40 + autotaladrante |
| `adsb_tapa_tubo.stl` | G | 1 (alternativa a `adsb_tapa`) | ASA / PETG blanco | Volteada, brida sobre la cama | No | 4 × M3×12 + 2 prisioneros M5 |
| `sensor_viento_brida.stl` | H | 2 | ASA / PETG blanco | Volteada | No | Patrón A: 4 tuercas M5 (Ø9,4); patrón B: 4 tuercas M4 (Ø8,1); 2 prisioneros M5 |
| `pluvio_vaso.stl` | H | 1 | ASA / PETG blanco | Volteado | No | 3 insertos M5; 2 prisioneros M5 |
| `pluvio_plataforma.stl` | H | 1 | ASA / PETG blanco | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | 3 × M5×40 con muelles; 3 × M3 en ranuras |
| `pico_soporte.stl` | H | 1 | ASA / PETG blanco | PENDIENTE DE CONFIRMAR | PENDIENTE DE CONFIRMAR | 4 × M3×8; 8 × M2×6 |

## 3. Convenciones comunes de montaje

**Insertos de latón.** Caliéntalos con el soldador (230-245 °C en la v2, 220 °C en la v3) y empújalos en
perpendicular, desde fuera hacia dentro, hasta que queden a ras. Agujeros de diseño: M3 4,0 mm (largo 6 mm),
M4 5,6 mm (largo 8,5 mm) y M5 7,0 mm en la v3. Enrosca un tornillo de prueba al enfriarse.

**Tuercas capturadas.** Las crucetas llevan la tuerca M6 en un alojamiento hexagonal de 11,3 × 5,4 mm: empújala
a fondo antes de cerrar la tapa. No uses tuercas autoblocantes de nailon sin comprobar que caben.

**Juntas de TPU.** La junta va en la ranura de la tapa, sin estirarla. En la v2 es de 4,4 × 4 mm en una ranura de 4,2 mm
(compresión de unos 25 %); en la v3, de 5,6 × 4 mm en una de 5,8 mm.

**Pasamuros.**

| Tipo | Agujero | Dónde |
|---|---|---|
| SMA de panel | 6,6 mm | Caja v2 (9 posiciones, paso 15 mm, z = 26) y ADS-B |
| N de panel | 16,2 mm | Caja v3 electrónica (filas z = 26, 56 y 86, paso 27 mm) |
| PG7 | 12,7 mm | WX, VIENTO, LLUVIA, VENT (membrana ePTFE), DATOS, ADS-B y MLA |
| PG9 | 15,5 mm | 230 V, RED y SALIDA |
| M20 | 20,4 mm | LAN |
| M25 | 25,4 mm | PWR y salida A ELECTRONICA |

Los pasamuros libres se cierran con `tapon_n` o `tapon_pg` (TPU).

**Estanqueidad.** Lazo de goteo en cada cable antes de entrar en una caja. Coaxial con `separador_coax` cada 50 cm
y a 30 mm del mástil. Fundas `funda_sma` y `funda_n` con cinta autoamalgamante sobre cada conector exterior.

**Apriete.** Aprieta las tapas en cruz y a mano hasta que la junta quede comprimida. No hay pares de apriete en los
`.scad` ni en los manuales: **PENDIENTE DE CONFIRMAR**.

## 4. Grupo A · Caja v2

![Diagrama de montaje de la caja v2](../esquemas/31_montaje_caja_v2.svg)

Referencias: [manual 10](10_CAJA_3D.md), [render del montaje](../../hardware/caja/render/montaje.png),
[despiece](../../hardware/caja/render/despiece.png), [interior](../../hardware/caja/render/interior.png),
[trasera](../../hardware/caja/render/montaje_trasera.png), [inferior](../../hardware/caja/render/montaje_inferior.png).
Piezas sueltas: [tapa interior](../../hardware/caja/render/tapa_interior.png),
[tapa de potencia](../../hardware/caja/render/tapa_potencia.png),
[placa electrónica](../../hardware/caja/render/placa_electronica.png),
[tejadillo](../../hardware/caja/render/tejadillo.png), [visera](../../hardware/caja/render/visera.png),
[soporte de cámara](../../hardware/caja/render/soporte_camara.png),
[soporte de mástil](../../hardware/caja/render/soporte_mastil.png),
[garita](../../hardware/caja/render/garita_base.png) y [pasamuros USB](../../hardware/caja/render/pasamuros_usb.png).

Medidas: 224 × 232 × 90 mm, pared de 3,2 mm, tapa de 4 mm.

> **Cámara.** El `.scad` y el [manual 10](10_CAJA_3D.md) de la caja v2 modelan la WPI408 (OV5647 con dos LED IR):
> ventana de 76 × 26 mm en (160, 196), policarbonato de 86 × 36 × 2 mm y espuma de 1 mm contra las placas IR.
> El kit público usa la **Raspberry Pi Camera Module 3 Wide** (IMX708, sin IR). Si se ajusta `soporte_camara`
> y la ventana a ese módulo: **PENDIENTE DE CONFIRMAR**. `separador_ir` es opcional / no necesario con Camera Module 3 Wide.

| Paso | Acción | Piezas | Tornillería / consumibles |
|---|---|---|---|
| 1a | Inserta los M4 de las 8 orejas (y = 22, 84, 148 y 210, 4 por lado) | `cuerpo` | 8 insertos M4 |
| 1b | Inserta los M4 de los 2 soportes de mástil (y = 45 e y = 187; 30 × 19 mm) | `cuerpo` | 8 insertos M4 |
| 1c | Inserta los M4 de los pilares (12,20), (212,20), (12,70), (212,70) | `tejadillo` | 4 insertos M4 |
| 1d | Inserta los M3: 8 de las placas, 4 de la tapa interior, 2 de la visera y 2 del soporte de cámara | `cuerpo`, `tapa`, `visera`, `soporte_camara` | 16 insertos M3 en total ([manual 10](10_CAJA_3D.md)) |
| 2a | Monta los 9 SMA: SAT, HAM, VHF, HF, ADSB, 868, GPS, M433, IG433 | `cuerpo` | 9 SMA + junta tórica; latiguillo RG316 de 20 cm |
| 2b | Monta los prensaestopas WX (PG7), LAN (M20) y 230 V (PG9) | `cuerpo` | PG7, M20, PG9 |
| 3 | Fija la placa de potencia a sus 4 bosses | `placa_potencia` | 4 × M3×8 (separación 10 mm, placa de 3 mm) |
| 4 | Conecta 230 V por PG9 a los 2 WAGO 221-412 (sin tensión) | — | 2 × WAGO 221-412 |
| 5 | Fija la tapa interior a 4 insertos M3 (2 en y = 30 y 2 en y = 200) a CP_Z = 56 mm | `tapa_potencia` | 4 × M3×8 |
| 6 | Pasa los cables por el hueco del tabique (18 × 34 mm) con el pasamuros | `pasamuros_usb` | — |
| 7 | Fija la placa electrónica a los bosses (30,6), (110,6), (30,204), (110,204) | `placa_electronica` | 4 × M3×8 |
| 8 | Fija la Pi 5 (58 × 49 mm) a la placa | — | 4 × M2.5×6 autorroscantes |
| 9 | Monta la LilyGO sobre la tapa interior y pasa los coaxiales por el hueco | — | — |
| 10 | Coloca `junta_ventana` y el policarbonato en la ventana de la cámara | `junta_ventana` | Policarbonato; junta de 1,5 mm |
| 11 | Monta la cámara con `soporte_camara` por dentro (`separador_ir` opcional con Camera Module 3 Wide) | `soporte_camara` | 2 × M3×35; espuma de 1 mm |
| 12 | Cierra la visera por fuera | `visera` | 2 × M3×8 |
| 13 | Encaja `junta_tapa` en la ranura de la tapa | `junta_tapa` | — |
| 14 | Cierra la tapa en cruz hasta que toque las orejas | `tapa` | 8 × M4×12 con arandela |
| 15 | Atornilla los 2 soportes de mástil a la trasera | `soporte_mastil` ×2 | 4 × M4×20 cada uno; abrazaderas de 12 mm |
| 16 | Monta el tejadillo sobre los 4 pilares | `tejadillo` | 2 × M4×30 (traseros) + 2 × M4×25 (delanteros) con arandelas de goma |
| 17 | Monta la garita: 6 platos sobre 3 varillas | `garita_base`, `garita_plato` ×6, `garita_tapa` | 3 varillas M4×140, 6 tuercas ciegas, 2 × M2×8 para el sensor |

Los pasos 1 a 17 corresponden a los 9 pasos del diagrama: 1→1; 2→2; 3-4→3; 5-6→4; 7-9→5; 10-12→6; 13-14→7; 15→8; 16-17→9.

**Comprobación.**
- Todos los insertos giran el tornillo sin holgura y quedan a ras.
- La tapa toca las orejas y la junta se ve comprimida de forma uniforme.
- La cámara ve a través de la ventana sin reflejos.
- Cada SMA tiene su etiqueta y su latiguillo; los PG no tienen holgura.

**Errores frecuentes.**
- Apretar de más los 8 × M4×12 y deformar la tapa.
- Olvidar la junta tórica de un SMA.
- Insertar los M4 de los soportes de mástil desde dentro.
- Trabajar el compartimento de 230 V con tensión.

## 5. Grupo B · Caja v3: electrónica

![Diagrama de montaje de la caja v3 electrónica](../esquemas/32_montaje_caja_v3_electronica.svg)

Referencias: [manual 17](17_CAJA_V3.md), [ventilación](18_VENTILACION.md),
[montaje](../../hardware/caja_v3/render/electronica_montaje.png),
[interior](../../hardware/caja_v3/render/electronica_interior.png),
[inferior](../../hardware/caja_v3/render/electronica_inferior.png),
[bandeja SDR](../../hardware/caja_v3/render/electronica_bandeja_sdr.png),
[bandeja SDR 2](../../hardware/caja_v3/render/electronica_bandeja_sdr2.png).

Medidas: 228 × 240 × 192 mm, pared de 4,8 mm, tapa de 5,2 mm.

| Paso | Acción | Piezas | Tornillería / consumibles |
|---|---|---|---|
| 1a | Inserta los M4 de las orejas (y = 24, 92, 148 y 216, 4 por lado) | `electronica_cuerpo` | Insertos M4 |
| 1b | Inserta los M4 de los pilares del tejadillo | `electronica_cuerpo`, `electronica_tejadillo` | 4 insertos M4 |
| 1c | Inserta los M5 de la trasera (y = 40 y 200; x al 25 % y 75 %) | `electronica_cuerpo` | Insertos M5 (agujero 7,0 mm) |
| 1d | Inserta un M3 en cada nudo de la rejilla (paso 20 mm) | `electronica_placa_rejilla` | Insertos M3 |
| 2 | Encaja `electronica_junta_tapa` en la ranura de 5,8 mm | `electronica_junta_tapa` | 4 puntos de cianoacrilato |
| 3a | Monta los N de panel en las filas z = 26, 56 y 86 | `electronica_cuerpo` | N de panel; latiguillos N-SMA RG-316 |
| 3b | Monta los prensaestopas a z = 116: M25 PWR, M20 LAN, PG7 WX, VIENTO, LLUVIA y VENT | `electronica_cuerpo` | M25, M20, PG7; VENT con membrana ePTFE |
| 3c | Cierra los libres con `electronica_tapon_n` y `electronica_tapon_pg` | tapones | — |
| 4a | Monta el ventilador de entrada (pared izquierda, y 55, z 60) soplando hacia dentro | `electronica_rejilla_ventilador` | Ventilador 60 mm, malla inox 1 mm, tornillos a 50 mm |
| 4b | Monta el ventilador de salida (pared derecha, y 190, z 68) soplando hacia fuera | `electronica_rejilla_ventilador` | Ídem |
| 4c | Pon por fuera cada `electronica_capota` con la boca hacia abajo | `electronica_capota` | Fijación PENDIENTE DE CONFIRMAR |
| 5a | Fija la rejilla a los 5 bosses (4 esquinas y centro; separación 8 mm) | `electronica_placa_rejilla` | 5 × M3 |
| 5b | Fija dongles, hub, SDRplay y WAGO a la rejilla | soportes | M3 o bridas: PENDIENTE DE CONFIRMAR |
| 6a | Monta los 6 postes de la bandeja SDR | `electronica_poste_bandeja` ×6 | M3: PENDIENTE DE CONFIRMAR |
| 6b | Fija `electronica_bandeja_sdr` (167 × 170 mm, DECK_H = 38 mm) y los SDR con bridas | `electronica_bandeja_sdr` | Bridas |
| 7 | Monta los 6 postes medios y `electronica_bandeja_sdr2` (DECK2_H = 82 mm) | `electronica_poste_medio` ×6, `electronica_bandeja_sdr2` | M3: PENDIENTE DE CONFIRMAR |
| 8a | Monta los 4 postes superiores y la bandeja (170 × 92 mm, BAND_H = 131 mm) | `electronica_poste_superior` ×4, `electronica_bandeja` | M3: PENDIENTE DE CONFIRMAR |
| 8b | Fija la Pi 5 en (8,10) a la bandeja | — | M2.5 autorroscante (agujero 2,4 mm, 58 × 49 mm) |
| 8c | Coloca LilyGO (x = 98) y RAK (129,12) en sus soportes | `electronica_soporte_lilygo`, `electronica_soporte_rak` | M3 o bridas: PENDIENTE DE CONFIRMAR |
| 8d | (Opcional) Monta la cámara Camera Module 3 Wide: ventana de 20 × 16 mm en (W/2, 210), cajeado exterior de 27 × 26 mm con cristal de policarbonato o metacrilato de 2 mm y sellador | `electronica_soporte_camara`, `electronica_visera` | 4 × M2 autorroscantes o insertos M2 (agujeros 21 × 12,5 mm: confirmar con plano), 2 insertos M3 de collar, 2 × M3 de la visera |
| 9a | Fija la caja a pared con `electronica_pletina_pared` ×2 (o al mástil con `electronica_soporte_mastil` ×2) | pletinas o soportes | M5 + 4 tacos, o M5 + 2 U M8 |
| 9b | Cierra la tapa en cruz | `electronica_tapa` | 8 × M4×16 (el [manual 17](17_CAJA_V3.md) dice 16: PENDIENTE DE CONFIRMAR) |
| 9c | Monta el tejadillo al final | `electronica_tejadillo` | M4 + arandelas de goma: longitud PENDIENTE DE CONFIRMAR |

> **Alturas.** El `.scad` usa DECK_H = 38, DECK2_H = 82 y BAND_H = 131 mm, lo que da postes de 38, 41 y 46 mm. El
> [manual 17](17_CAJA_V3.md) habla de postes de 30 mm y una bandeja a 71 mm sobre la rejilla. **PENDIENTE DE CONFIRMAR**:
> mide tus postes impresos y sigue el `.scad`, que es la fuente de verdad de este manual.
>
> **Tapa.** El `.scad` define 8 orejas en la electrónica y en el SAI y 6 en la potencia (y = 24, 100 y 176), mientras que
> el manual 17 cuenta 16 tornillos M4×16. Se sigue el `.scad`; **PENDIENTE DE CONFIRMAR**.

**Comprobación.** `sudo bricohams-check`; los dos ventiladores giran y el aire entra por la izquierda y sale por la
derecha; prueba de manguera de 2 minutos con todo cerrado ([manual 17](17_CAJA_V3.md)).

**Errores frecuentes.**
- Ventilador invertido (entra por donde debe salir).
- Capota con la boca hacia arriba: entra agua.
- Bandeja suelta por falta de tornillos en los postes.
- Cable sin lazo de goteo en un PG.

## 6. Grupo C · Caja v3: potencia y SAI

![Diagrama de montaje de potencia y SAI](../esquemas/33_montaje_caja_v3_potencia_sai.svg)

Referencias: [potencia, montaje](../../hardware/caja_v3/render/potencia_montaje.png) e
[interior](../../hardware/caja_v3/render/potencia_interior.png); [SAI, montaje](../../hardware/caja_v3/render/sai_montaje.png) e
[interior](../../hardware/caja_v3/render/sai_interior.png). Medidas: potencia 170 × 200 × 112 mm; SAI 228 × 240 × 140 mm.

⚠ SAI desenchufado, batería desconectada y 5 minutos de espera. No modifiques la placa del SAI.

| Paso | Acción | Piezas | Tornillería / consumibles |
|---|---|---|---|
| 1a | Potencia: inserta los M4 de las orejas (y = 24, 100 y 176) y los M5 traseros (y = 40 y 160) | `potencia_cuerpo` | Insertos M4 y M5 |
| 1b | SAI: inserta los M4 (y = 24, 92, 148 y 216) y los M5 traseros (y = 40 y 200) | `sai_cuerpo` | Insertos M4 y M5 |
| 1c | Inserta los M4 de los 4 pilares de cada tejadillo | `potencia_tejadillo`, `sai_tejadillo` | 4 insertos M4 por pieza |
| 1d | Encaja cada junta en su ranura de 5,8 mm | `potencia_junta_tapa`, `sai_junta_tapa` | Cianoacrilato |
| 2a | Monta el PG9 «230 V» (entrada) en potencia | `potencia_cuerpo` | PG9 |
| 2b | Monta el M25 «A ELECTRONICA» (salida) en potencia | `potencia_cuerpo` | M25; manguera 4 × 0,75 H07RN-F |
| 2c | Monta el PG7 «VENT» con membrana ePTFE y cierra los PG libres | `potencia_cuerpo`, `potencia_tapon_pg` | PG7 |
| 3a | Fija la placa rejilla de potencia a los bosses | `potencia_placa_rejilla` | M3 |
| 3b | Fija el Schuko de superficie (≈ 80 × 80 × 42 mm) | `potencia_soporte_schuko` | M4 a ±30 mm + 4 × M3 |
| 3c | Fija el cargador con su brida (110 × 16 × 40 mm) | `potencia_brida_cargador` | 2 × M3 |
| 3d | Cablea disparador PD, fusible y WAGO ([manual 17](17_CAJA_V3.md)) | — | WAGO |
| 4a | SAI: fija la placa rejilla | `sai_placa_rejilla` | M3 |
| 4b | SAI: coloca el soporte de batería en BAT (50,4) | `sai_soporte_bateria` | Correas por las ventanas de correa (22 mm en el `.scad`) |
| 4c | SAI: monta las 2 guías de PCB en y = 18 y 168 (PCB en (6,6)) | `sai_guia_pcb` ×2 | M3 prisionero (ranura 2,2 mm) |
| 5a | SAI: monta la pletina del trafo en (50,118) | `sai_pletina_trafo` | M5 ranurado |
| 5b | SAI: monta los 2 soportes de filtro EMI_OUT (138,118) y EMI_IN (176,118) | `sai_soporte_filtro` ×2 | M4 ranurado |
| 5c | SAI: monta el WAGO en DC (50,194) | `sai_soporte_wago` | Fijación PENDIENTE DE CONFIRMAR |
| 6 | SAI: pon el fusible ATO 15 A en BAT+ (a ≤ 10 cm del borne) y conecta PE a los filtros EMI | — | Fusible ATO 15 A |
| 7a | SAI: monta PG9 «RED», PG9 «SALIDA» y PG7 «DATOS» | `sai_cuerpo` | PG9, PG7 |
| 7b | Cierra los PG libres | `sai_tapon_pg` | — |
| 7c | Cierra las tapas en cruz | `potencia_tapa`, `sai_tapa` | M4×16: 6 (potencia) y 8 (SAI) según el `.scad` |
| 8a | Fija cada caja con 2 pletinas a pared (4 tacos) o 2 soportes a U M8 | `*_pletina_pared` ×2 o `*_soporte_mastil` ×2 | M5 y U: longitud PENDIENTE DE CONFIRMAR |
| 8b | Monta los tejadillos al final | `potencia_tejadillo`, `sai_tejadillo` | M4: longitud PENDIENTE DE CONFIRMAR |

**Comprobación.**
- La potencia queda más baja que la electrónica.
- Las ventilas superior e inferior del SAI siguen abiertas (hidrógeno).
- PE conectado a los filtros EMI y continuidad comprobada.
- Prueba de manguera de 2 minutos ([manual 17](17_CAJA_V3.md)).

**Errores frecuentes.**
- Tapar las ventilas del SAI.
- Poner el fusible lejos del borne de la batería.
- Confundir PG9 de red y de salida (etiqueta cada cable).

## 7. Grupo D · Antenas: quad 2 m / 70 cm

![Diagrama de montaje del quad](../esquemas/34_montaje_quad.svg)

Referencias: [manual 12](12_QUAD_2M70.md) y [piezas de antenas](../../hardware/antenas/render/piezas.png).

| Paso | Acción | Piezas | Tornillería / consumibles |
|---|---|---|---|
| 1a | Marca el boom cuadrado de 20 × 20 mm a 0, 248, 372 y 510 mm (cola de 500 mm) | — | — |
| 1b | Pon los 2 bujes de 2 m y los 2 de 70 cm en sus marcas | `quad_buje_2m` ×2, `quad_buje_70` ×2 | 2 prisioneros M5 por buje (8 en total) |
| 2a | Corta y atornilla las varillas Ø8 (378 y 345 mm; cruceta − 25 mm) a los bujes | varillas Ø8 | M3 autorroscante |
| 2b | Pon las punteras en las puntas Ø8 | `quad_puntera_8` ×7 | — |
| 3a | Monta las varillas Ø6 (108 y 95 mm) | varillas Ø6 | M3 autorroscante |
| 3b | Pon las punteras en las puntas Ø6 | `quad_puntera_6` ×8 | — |
| 3c | Coloca los clips del cuadro de 70 cm a 127 mm del centro | `quad_clip_70` ×3 | Según [manual 12](12_QUAD_2M70.md) |
| 4 | Tiende el hilo de cobre Ø2 por punteras y bujes | hilo Ø2 | — |
| 5a | Monta el alimentador de 2 m en la punta | `quad_alim_2m` | 2 insertos M3 de latón (12 mm) |
| 5b | Monta el alimentador de 70 cm en el lugar del clip +Y | `quad_alim_70` | 2 insertos M3 de latón (12 mm) |
| 5c | Suelda o atornilla la alimentación: RG-59 de λ/4 = 341 mm en 2 m; RG-58 o RG-316 en 70 cm | — | RG-59, RG-58 o RG-316 |
| 6 | Monta la abrazadera en la cola del boom (80 × 22 mm, ranura cuadrada) | `quad_abrazadera` | U M8 (mástil) y U M6 (boom): medidas PENDIENTE DE CONFIRMAR |
| 7 | Sube al mástil a 0,95 m con rumbo 205° | — | — |

Alternativa del [manual 21](21_ANCLAJES.md): `cruceta_mastil_quad` en lugar de `quad_abrazadera`.

**Comprobación.** Mide con NanoVNA antes de izar ([manual 12](12_QUAD_2M70.md), [45](45_NANOVNA.md)); el boom no gira en la abrazadera.

**Errores frecuentes.**
- Mezclar los bujes de 2 m y de 70 cm.
- Orientar el boom mal (rumbo 205°).
- Alimentador sin lazo de goteo.

## 8. Grupo E · Antenas: discones y ADS-B

![Diagrama de montaje de discone y ADS-B](../esquemas/35_montaje_discone_adsb.svg)

Referencias: [manual 13](13_DISCONES.md), [manual 14](14_ADSB_LNA.md) y [piezas de antenas](../../hardware/antenas/render/piezas.png).

| Paso | Acción | Piezas | Tornillería / consumibles |
|---|---|---|---|
| 1 | Inserta 3 M4 arriba y 3 abajo del aislador (Ø50 × 20 mm) | `discone_aislador` | 6 insertos M4 |
| 2a | Rosca las 12 varillas Ø4 del disco (327 mm) al cubo Ø70 × 12 con la plantilla | `discone_plantilla_disco` | Cubo de aluminio |
| 2b | Fija el cubo del disco al aislador | — | 3 × M4×10 ([manual 13](13_DISCONES.md)) |
| 3a | Rosca las 12 varillas del cono (1010 mm) al otro cubo con la plantilla (semiángulo 30°) | `discone_plantilla_cono` | Cubo de aluminio |
| 3b | Fija el cubo del cono al aislador (hueco de 20 mm entre disco y cono) | — | 3 × M4×10 |
| 4 | Pon los tapones en las 12 puntas de varilla | `tapon_varilla` ×12 | Agujero Ø2,5 para cordino; fijación PENDIENTE DE CONFIRMAR |
| 5 | Une el adaptador (60 mm) al cubo y al mástil (z = 12 y z = 32) | `discone_adaptador_mastil` | 4 × M4 al cubo; 2 × M6 pasantes |
| 6 | Pon el capuchón sobre el cubo del disco con silicona neutra | `discone_capuchon` | Silicona neutra |
| 7a | ADS-B: monta el SMA de panel (6,6 mm) y el PG7 (12,7 mm) en la base | `adsb_base` | SMA, PG7 |
| 7b | ADS-B: fija el LNA (72 × 34 × 20 mm) | — | 4 agujeros de 2,8 mm |
| 8a | ADS-B: monta el elemento de 62 mm y 4 radiales de 68 mm a 45° (latón Ø2) | — | Latón Ø2 |
| 8b | ADS-B: cierra con la tapa y la junta de 1 mm | `adsb_tapa` | 4 × M3 + junta TPU 1 mm |
| 8c | ADS-B: pega el radomo | `adsb_radomo` | Silicona neutra ([manual 14](14_ADSB_LNA.md)); tornillos PENDIENTE DE CONFIRMAR |

Alternativa para sujetar el ADS-B a un tubo: `adsb_tapa_tubo` ([grupo G](#10-grupo-g--anclajes-crucetas)).

**Comprobación.** Varillas con el espaciado de la plantilla; M6 del adaptador apretados sin ovalar el mástil; LNA alimentado solo tras
verificar tensión y sentido ([manual 14](14_ADSB_LNA.md)).

**Errores frecuentes.**
- Varillas desiguales en el disco.
- Faltan tapones.
- Conectar el LNA sin comprobar la polaridad del bias.

## 9. Grupo F · Antenas: MLA-30, GPS y accesorios RF

![Diagrama de montaje de MLA, GPS y accesorios](../esquemas/36_montaje_mla_gps.svg)

Referencias: [manual 15](15_LAZO_MLA30.md), [manual 11](11_MASTIL_Y_ANTENAS.md) y [piezas de antenas](../../hardware/antenas/render/piezas.png).

| Paso | Acción | Piezas | Tornillería / consumibles |
|---|---|---|---|
| 1 | Inserta los 4 M3 de las esquinas de la base (interior 90 × 60 × 36 mm) | `mla_caja_base` | 4 insertos M3 |
| 2a | Pon la junta TPU de 1,6 mm | `mla_junta` | — |
| 2b | Cierra con la tapa | `mla_caja_tapa` | 4 × M3×12 inox |
| 3 | Monta el PG7 y encaja los extremos del lazo en las medias cañas; séllalas con silicona neutra | `mla_caja_base` | PG7 |
| 4 | Monta la cruz en el poste no metálico (≥ 5 m) | `mla_cruz` | U M6; varillas Ø10 |
| 5 | Sujeta el coaxial Ø7 con los 4 clips | `mla_clip_lazo` ×4 | — |
| 6a | Cubre cada SMA con su funda | `funda_sma` | Cinta autoamalgamante |
| 6b | Cubre cada N con su funda | `funda_n` | Cinta autoamalgamante |
| 7 | GPS: monta el puck (48 × 40 × 15 mm) en el soporte | `gps_soporte` | 4 agujeros M6 (Ø6,6): tornillería PENDIENTE DE CONFIRMAR |
| 8a | Fibra 433: monta el soporte entre brazo Ø25 y fibra Ø26 | `soporte_fibra` | M6: longitud PENDIENTE DE CONFIRMAR |
| 8b | Monta cada brazo en el mástil | `brazo_mastil` | M8 al mástil y M6 al brazo: medidas PENDIENTE DE CONFIRMAR |
| 8c | Tapa los extremos de brazo | `tapon_brazo` | — |
| 8d | Sujeta el coaxial al mástil | `separador_coax` | 1 brida: medida PENDIENTE DE CONFIRMAR |
| 8e | Sujeta el filtro | `clip_filtro` | 1 brida: medida PENDIENTE DE CONFIRMAR |

**Comprobación.** Junta de la MLA asentada y sin pellizcos; fundas sin burbujas; coaxial a 30 mm del mástil.

**Errores frecuentes.**
- Usar poste metálico para la MLA.
- Funda sin cinta.
- Aplastar el coaxial con una brida.

## 10. Grupo G · Anclajes: crucetas

![Diagrama de montaje de crucetas](../esquemas/37_montaje_crucetas.svg)

Referencias: [manual 21](21_ANCLAJES.md) y [render del conjunto](../../hardware/anclajes/render/montaje.png).

Existen cuatro familias:
- `cruceta_mastil_brazo` (mástil Ø40,6 ↔ brazo Ø25,4), 3 unidades.
- `cruceta_mastil_quad` (mástil ↔ boom de 20,4 mm), 1 unidad.
- `cruceta_brazo_fibra` (brazo ↔ fibra Ø26), 1 unidad.
- `cruceta_brazo_tubo` (brazo ↔ tubo), 5 según el manual 21.

Cada cruceta se compone de un cuerpo y dos tapas. La tapa A abraza el tubo superior; la tapa B, el inferior.

| Paso | Acción | Piezas | Tornillería / consumibles |
|---|---|---|---|
| 1 | Elige el juego (cuerpo + 2 tapas) según los tubos | `cruceta_*_cuerpo` | — |
| 2 | Empuja 4 tuercas hexagonales M6 (11,3 × 5,4 mm) en sus alojamientos | cuerpo | 4 tuercas M6 |
| 3 | Apoya el tubo inferior en el semicanal | cuerpo | — |
| 4 | Monta la tapa B por abajo con 2 tornillos | tapa inferior | 2 × M6×50 (mástil) o M6×40; 2 arandelas |
| 5 | Apoya el tubo superior y monta la tapa A con 2 tornillos | tapa superior | 2 × M6×40 y arandelas |
| 6 | Atornilla el autotaladrante antigiro en cada tapa (agujero de 5,2 mm a x = L/4) | tapas | Autotaladrante Ø4,8 × 19 |
| 7 | Aprieta alternando los tornillos de cada tapa | — | Par: PENDIENTE DE CONFIRMAR |

| Cruceta | Cuerpo | Tapa inferior | Tapa superior |
|---|---|---|---|
| Mástil ↔ brazo | `cruceta_mastil_brazo_cuerpo` | `cruceta_mastil_brazo_tapa_mastil` | `cruceta_mastil_brazo_tapa_brazo` |
| Mástil ↔ quad | `cruceta_mastil_quad_cuerpo` | `cruceta_mastil_quad_tapa_mastil` | `cruceta_mastil_quad_tapa_boom` |
| Brazo ↔ fibra | `cruceta_brazo_fibra_cuerpo` | `cruceta_brazo_fibra_tapa_brazo` | `cruceta_brazo_fibra_tapa_fibra` |
| Brazo ↔ tubo | `cruceta_brazo_tubo_cuerpo` | `cruceta_brazo_tubo_tapa` | `cruceta_brazo_tubo_tapa` |

Alturas de montaje en el mástil ([manual 11](11_MASTIL_Y_ANTENAS.md)): brazos a 1,7 m, 1,5 m y 0,2 m; quad a 0,95 m (boom a 205°).
Fibra: brazo E/O. Tubos: ADS-B, 2 Bigsignal y 2 sensores de viento.

La alternativa `adsb_tapa_tubo` (impresa volteada, brida sobre la cama) sustituye a `adsb_tapa` y lleva 4 × M3×12 y 2 prisioneros M5.

**Comprobación.** El conjunto no gira ni resbala por el tubo; la separación entre tapa y cuerpo es de unos 1 mm (apriete de diseño); los autotaladrantes no atraviesan el tubo.

**Errores frecuentes.**
- Tuercas olvidadas o giradas.
- Tapas intercambiadas (la de mástil lleva M6×50).
- Apretar una sola tapa y dejar la otra floja.

## 11. Grupo H · Anclajes: sensores y Pico

![Diagrama de montaje de sensores y Pico](../esquemas/38_montaje_sensores_pico.svg)

Referencias: manuales [19](19_VIENTO_Y_LLUVIA.md), [20](20_PICO_IO.md) y [21](21_ANCLAJES.md); [esquema 16 del Pico](../esquemas/16_pico_io.png).

| Paso | Acción | Piezas | Tornillería / consumibles |
|---|---|---|---|
| 1 | Inserta las tuercas en la brida: patrón A (M5, Ø9,4) o patrón B (M4, Ø8,1) | `sensor_viento_brida` ×2 | 4 tuercas por brida |
| 2a | Coloca la brida en el tubo del brazo con la marca N hacia el norte geográfico | `sensor_viento_brida` | 2 prisioneros M5 |
| 2b | Orienta la brida de la veleta con la N al norte | `sensor_viento_brida` | — |
| 3 | Atornilla el sensor sobre la brida | — | 4 × M5 o M4 (longitud PENDIENTE DE CONFIRMAR) |
| 4a | Inserta 3 M5 en el vaso (r = 40 mm) | `pluvio_vaso` | 3 insertos M5 |
| 4b | Fija el vaso al poste Ø40 (independiente del mástil) | `pluvio_vaso` | 2 prisioneros M5 |
| 5a | Pon la plataforma (160 × 70 × 6 mm) sobre el vaso | `pluvio_plataforma` | 3 × M5×40 con muelles |
| 5b | Nivela la plataforma con los 3 M5 | `pluvio_plataforma` | 3 × M3 en ranuras |
| 6a | Atornilla el soporte a la rejilla de 20 mm de la caja v3 | `pico_soporte` | 4 × M3×8 |
| 6b | Fija el Pico y la placa perforada | — | 8 × M2×6 |
| 7 | Cablea el Pico: GP4 SDA, GP5 SCL, GP22 DS18B20, GP15 lluvia, GP16/17 PWM, GP18/19 TACH | — | 3V3 y GND |

⚠ Los pines del Pico **no toleran 5 V**. Revisa el cableado con el [esquema 16](../esquemas/16_pico_io.png) y el [manual 20](20_PICO_IO.md).

**Comprobación.** La marca N apunta al norte geográfico; la plataforma queda nivelada; `sudo bricohams-check` ve los sensores.

**Errores frecuentes.**
- Mezclar patrones A y B de la brida.
- Pluviómetro sin nivelar.
- 5 V en un pin del Pico.

## 12. Mapa de piezas en el mástil y montaje final

![Mapa de piezas impresas en el mástil](../esquemas/39_mapa_piezas_mastil.svg)

| Altura | Elemento | Piezas impresas |
|---|---|---|
| 2,9 m | Discone | Grupo E |
| 2,0 m | Collar de vientos (3 cables de acero Ø3) | Ninguna |
| 1,7 m | Brazo E/O: ADS-B (E, 0,8 m), GPS (E, 0,4 m), fibra 433 (O, 0,8 m) | `cruceta_mastil_brazo`, `brazo_mastil`, `gps_soporte`, `soporte_fibra`, `tapon_brazo` |
| 1,5 m | Brazo N/S: anemómetro (N), veleta (S) | `cruceta_mastil_brazo`, `cruceta_brazo_tubo`, `sensor_viento_brida` |
| 0,95 m | Quad a 205° | `quad_abrazadera` o `cruceta_mastil_quad` (ver [manuales 12](12_QUAD_2M70.md) y [21](21_ANCLAJES.md)) |
| 0,2 m | Brazo N/S: Bigsignal 868 (N), iGate 433 (S) | `cruceta_mastil_brazo`, `cruceta_brazo_tubo` |
| 0,05 m | Garita | `garita_*` |
| Fuera del mástil | MLA-30 (≥ 5 m, poste no metálico), pluviómetro (poste Ø40 de 1 m) | `mla_*`, `pluvio_*` |

Orden de montaje final ([manual 11](11_MASTIL_Y_ANTENAS.md)):

1. Prepara en el suelo cada brazo con su cruceta y su antena.
2. Fija la caja con sus soportes de mástil (v2: M4×20 ×4 por soporte; v3: M5 + U M8) o a pared con pletinas.
3. Monta el tejadillo y la garita.
4. Sube y fija los brazos de abajo arriba, empezando por el de 0,2 m.
5. Sube el quad, los brazos de 1,5 m y 1,7 m y, por último, el discone.
6. Coloca el collar y los 3 cables de acero Ø3 a 2,0 m.
7. Conecta cada coaxial con su funda y un lazo de goteo; añade `separador_coax` cada 50 cm.
8. Conecta el mástil a tierra con 16 mm².

## 13. Lista de comprobación antes de subir al mástil

- [ ] Todas las piezas de la tabla maestra están impresas con el material indicado.
- [ ] Insertos a ras y tornillos de prueba con rosca correcta.
- [ ] Juntas de TPU en su ranura y sin cortes.
- [ ] Pasamuros y prensaestopas apretados; los libres, con tapón.
- [ ] Lazo de goteo en cada cable.
- [ ] Tapas apretadas en cruz; prueba de manguera superada ([manual 17](17_CAJA_V3.md)).
- [ ] Ventiladores con sentido de flujo correcto; capotas con la boca hacia abajo.
- [ ] Ventilas del SAI abiertas; fusible ATO 15 A en BAT+; PE conectado.
- [ ] Antenas medidas con NanoVNA y fundas con cinta ([manual 45](45_NANOVNA.md)).
- [ ] Crucetas apretadas, sin giro, con tornillo antigiro.
- [ ] Marca N del sensor de viento al norte geográfico; pluviómetro nivelado.
- [ ] Pico sin 5 V en sus pines.
- [ ] Mástil a tierra (16 mm²) y collar de vientos montado.
- [ ] `sudo bricohams-check` sin errores con todo cerrado y alimentado.

## 14. Valores pendientes de confirmar

- Orientación, soportes, perímetros y relleno de las piezas de antenas; orientación y soportes de `pluvio_plataforma` y `pico_soporte`.
- Pares de apriete de todos los tornillos.
- Ajuste de `soporte_camara` y de la ventana de la caja v2 a la Camera Module 3 Wide; patrón de agujeros M2 (21 × 12,5 mm) de `electronica_soporte_camara`.
- Tornillería de los soportes de la v3 (`soporte_dongle`, `soporte_hub`, `soporte_sdrplay`, `soporte_lilygo`, `soporte_rak`, `soporte_wago`) y fijación de `capota`, `tapon_*`, `discone_capuchon` y `tapon_varilla`; número de `soporte_dongle` de la segunda bandeja.
- Longitud de los tornillos M4 de los tejadillos v3, M5 de pletinas y U, M3 de los postes de las bandejas y `adsb_radomo`.
- Medidas de las U de `quad_abrazadera` y `brazo_mastil`, y bridas de `separador_coax` y `clip_filtro`; cantidad de `clip_filtro`.
- Alturas de los postes de la v3 (`.scad` 38 / 41 / 46 mm frente al manual 17 con 30 mm y bandeja a 71 mm).
- Número de tornillos M4×16 de las tapas v3 (`.scad` 8 / 6 / 8 frente a 16 en el manual 17).
- Diámetro del mástil del `soporte_mastil` de la v3 (`MAST_D` 50 en el `.scad`, «PENDIENTE de medir»).
- Medida de la membrana ePTFE del respiradero VENT.
- Ventanas de correa del `sai_soporte_bateria` (22 mm en el `.scad`, 20 mm en los manuales).
