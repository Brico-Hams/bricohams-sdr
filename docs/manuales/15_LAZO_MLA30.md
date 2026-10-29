# 15 · Lazo MLA-30 para HF: protección de intemperie y montaje

<!-- guia-visual:inicio -->
> **Ruta visual:** [Caja, antenas, filtros, alimentación y anclajes](../GUIA_VISUAL_MODULOS.md#hardware).
> Consulta allí requisitos, ilustración, cuadro de instalación, comprobaciones y restauración.
> Los comandos de este manual se ejecutan en Bash en la Pi; revisa el backup antes de cambiarla.
<!-- guia-visual:fin -->

**Qué es:** el MLA-30 es un lazo magnético **activo** de recepción (0,1–30 MHz).
- **Alimentación:** el amplificador va en la base del lazo y recibe 12 V por el coaxial, desde un inyector alimentado por USB. El kit trae 10 m de coaxial.
- **Problema:** **ni su caja ni sus conectores son estancos**. Esta guía los protege con piezas impresas y deja el lazo redondo y firme.
- **A qué va conectado:**
  - ahora, al **RTL-SDR V3** (HF por muestreo directo), a través del diplexor HF/VHF;
  - cuando llegue el SDRplay, a su **antena A**.

## 1. Piezas impresas (`hardware/antenas/stl`)
| Pieza | Material | Cant. | Notas |
|---|---|---|---|
| `mla_caja_base` + `mla_caja_tapa` | PETG blanco o ASA | 1 + 1 | caja estanca para la caja del amplificador. **Mide la tuya** y pon sus medidas interiores en `MLA_CAJA` (por defecto 90 × 60 × 36) |
| `mla_junta` | TPU | 1 | junta entre base y tapa |
| `mla_cruz` | PETG | 1 | une 2 varillas de fibra de Ø10 en «+» y se amarra al poste con una U M6 |
| `mla_clip_lazo` | PETG | 4 | en las puntas de la cruz: sujetan el coaxial del lazo (`MLA_COAX`, por defecto Ø7) |
| `funda_sma` | TPU | 2–4 | sobre cada empalme SMA (con cinta autovulcanizante encima) |

**Otro material:**
- 2 varillas de fibra de Ø10 de longitud = diámetro del lazo + 40 mm;
- poste no metálico (PVC de Ø40 o fibra) de 2–3 m;
- abrazadera en U M6;
- insertos M3 + 4 tornillos M3 × 12 inox;
- silicona neutra;
- cinta autovulcanizante.

## 2. Montaje paso a paso
1. **Cruz:** mete las dos varillas en la `mla_cruz` hasta el fondo y fíjalas con los tornillos de los brazos. La cruz va con un brazo vertical.
2. **Lazo:** pasa el coaxial del lazo por los 4 `mla_clip_lazo` de las puntas para que quede un círculo. Los dos extremos bajan por el brazo inferior hasta la caja del amplificador.
3. **Caja del amplificador:**
   1. Mete la caja del MLA-30 en la `mla_caja_base`.
   2. Los extremos del lazo entran por las dos medias cañas laterales.
   3. La bajada sale por el PG7 inferior.
   4. Pon la junta y cierra con la tapa (4 × M3).
   5. Sella las medias cañas con silicona neutra.
4. **Conectores:** cubre cada empalme con `funda_sma` y encima cinta autovulcanizante (de abajo arriba, para que escurra el agua).
5. **Poste:** la cruz va a la punta del poste con una U M6 y la caja del amplificador, abajo, sujeta al poste con bridas.
6. **Ubicación:**
   - a **≥ 5 m** del mástil, de los cables de red y de fuentes conmutadas o LED;
   - a 2–3 m de altura;
   - lejos de canalones y barandillas metálicas.
   - El lazo es direccional en las bandas bajas (nulos a los lados): gíralo para anular el ruido local mirando la cascada de OpenWebRX en 40 y 80 m.
7. **En la caja:** pasamuros N «HF» (adaptador SMA–N) → **inyector del MLA-30** (alimentado por USB de la regleta) → entrada HF del diplexor HF/VHF → RTL-SDR V3.

## 3. Comprobación
- **Con el inyector apagado:** la cascada de HF queda casi plana.
- **Con el inyector encendido:** sube el ruido de fondo 10–20 dB y aparecen las emisoras de 41 y 49 m. Si no cambia, revisa los 12 V del inyector y la continuidad del coaxial.
- **Con el SDRplay:** activa `HF_SDRPLAY="yes"` y conecta el lazo a su antena A (manual 08).
