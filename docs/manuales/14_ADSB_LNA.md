# 14 · Antena ADS-B 1090 MHz con el LNA en la base

<!-- guia-visual:inicio -->
> **Ruta visual:** [Caja, antenas, filtros, alimentación y anclajes](../GUIA_VISUAL_MODULOS.md#hardware).
> Consulta allí requisitos, ilustración, cuadro de instalación, comprobaciones y restauración.
> Los comandos de este manual se ejecutan en Bash en la Pi; revisa el backup antes de cambiarla.
<!-- guia-visual:fin -->

![Plano](../esquemas/10_adsb_gp.png)

**Qué es:** un plano de tierra λ/4 («araña») con radiante de 62 mm y 4 radiales de 68 mm a 45° (latón Ø2).
- **Resultados NEC2:** ROE 1,17 a 1090 MHz y 2,2 dBi en el horizonte, donde están los aviones lejanos (`hardware/antenas/sim/gp1090.py`).
- **El LNA de 1090 que ya tienes** (20,5 dB, NF 0,4 dB, «+5V MAX», «BIAS: yes») va **dentro de la base**, justo bajo el radiante. Ahí rinde más.

## 1. Por qué el LNA va en la antena (y no en la caja)
| Montaje | Lo que limita | Resultado |
|---|---|---|
| LNA en la caja, tras 7 m de RG-58 | 4 dB de pérdida antes del LNA: el ruido sube 4 dB | malo |
| LNA en la caja, tras 7 m de LMR-400 | 1,6 dB | regular |
| **LNA en la antena + 7 m de LMR-400** | el NF del LNA (0,4 dB); los 20 dB tapan la pérdida del cable | **bueno** |

- **Riesgo:** saturar el FlightStick, que ya lleva LNA y SAW, con el aeropuerto a ~25 km.
- **Solución:** readsb con `ADSB_GAIN="auto"` (o fijar 36–40 dB) y vigilar `strong_signals` en `/run/readsb/stats.json`.

## 2. Material
| Artículo | Cant. |
|---|---|
| Conector SMA hembra de panel con brida de 4 agujeros (12,7 mm) | 1 |
| Varilla de latón Ø2 | 0,4 m (62 + 4 × 68 + soldaduras) |
| LNA 1090 (el tuyo) + latiguillo SMA macho–SMA macho de 5 cm | 1 |
| Prensaestopas PG7 + pigtail SMA–N hembra de panel (o latiguillo SMA–N) | 1 |
| **Bias-tee SMA de 5 V** (en la caja) | 1 |
| LMR-400 o Hyperflex 5 con N macho en los dos extremos | 7–8 m |
| **v4:** tubo Ø25 de 300 mm + `cruceta_brazo_tubo` (cuerpo + tapa) + `adsb_tapa_tubo` + 2 prisioneros M5 (manual 21 §3.5) | 1 juego |

**Piezas impresas** (PETG blanco):
- `adsb_base`: mide tu LNA y ajusta `LNA` en el `.scad` si hace falta;
- `adsb_tapa` + junta de TPU (recórtala de una lámina de 1 mm);
- `adsb_radomo`.

## 3. Montaje paso a paso
1. **Radiante:** suelda 62 mm de latón al vivo del SMA de panel. Mide desde el plano de la brida.
2. **Radiales:**
   1. Suelda los 4 radiales de 68 mm a las orejas de la brida (o a una arandela de latón bajo los tornillos).
   2. Dóblalos 45° hacia abajo, a 90° entre sí.
3. **Base:**
   1. Monta el SMA en la torreta de la `adsb_base`: radiales fuera, por las ranuras del radomo.
   2. Dentro, conecta SMA de panel → latiguillo → **LNA IN**.
   3. Conecta **LNA OUT** → pigtail → PG7 de salida.
4. **Tapa y radomo:** cierra con la `adsb_tapa` y la junta. Pega el `adsb_radomo` sobre la torreta con silicona neutra, con los radiales saliendo por sus 4 ranuras, y sella las ranuras.
5. **Brazo (v4, manual 21 §3.5):** cierra la base con la **`adsb_tapa_tubo`** en lugar de la `adsb_tapa`. Su vaso encaja en la punta de un tubo Ø25 de 300 mm vertical y se aprieta con 2 prisioneros M5. Ese tubo va al extremo E del brazo de 1,7 m con una `cruceta_brazo_tubo` (dos M6 a tuercas cautivas + autotaladrante antigiro). El coaxial baja por fuera del tubo con bridas y un bucle de goteo.
6. **En la caja:** pasamuros N «ADSB» → **bias-tee** (puerto «RF+DC» hacia la antena, «RF» hacia el FlightStick, «DC» a 5 V de la regleta USB) → FlightStick.
7. **Comprobación:**
   - En `http://<pi>/tar1090/`: más aviones lejanos (> 250 km) y mensajes por segundo.
   - Con `bricohams-check`: readsb en marcha.
   - **Prueba de LNA alimentado:** sin el bias-tee, el número de aviones cae a la mitad o menos. Si no cae, el LNA no recibe los 5 V: revisa el bias-tee.

> ⚠ **Nunca** conectes el bias-tee de 5 V a una antena sin LNA: pondría en corto la continua a través del radiante y los radiales. Y nunca 12 V: el LNA admite 5 V como máximo.
