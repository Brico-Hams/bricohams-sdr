# 50 · Hermes Lite 2 en OpenWebRX+ y antenas de HF

> El Hermes Lite 2 (HL2) es un transceptor SDR de 0–38 MHz (TX hasta 30 MHz, ~5 W) por **Ethernet**
> y con su propia alimentación de 12 V: no carga el bus USB de la Pi.
> En OpenWebRX+ **solo recibe**, con perfiles de **384 kHz como máximo**. No cubre 6 m, 2 m ni 70 cm:
> para satélites de VHF/UHF sigue el RTL-SDR «sat» (manual 26).

## 1. Qué añade el kit
- Receptor **«🟠 HF · HERMES LITE 2 · 160-10 m»** (`type: hpsdr`), con perfiles de 160, 80, 60, 40, 30,
  20, 17, 15 (21,0–21,35), 12 y 10 m (28,0–28,35), y **«SAT 10m»** centrado en 29,4 MHz
  (MARMOTSat 29,410 y los satélites de 29,3–29,5 MHz).
- Planificador por luz del día: 20 m de día, 40 m en el crepúsculo y 80 m de noche.
- Con `HF_HERMES="yes"` desaparecen los perfiles de HF del RTL-SDR V3 (muestreo directo).
- `hpsdrconnector` 0.11.0: del repositorio de OpenWebRX+; en **trixie no está**, así que el instalador
  baja el paquete de bookworm (binario Go estático, sin dependencias) y **comprueba su SHA256** antes
  de instalarlo.

## 2. Puesta en marcha
1. Conecta el HL2 por cable al mismo router o switch que la Pi y dale una **IP fija** en el router.
2. En `bricohams.env`:
   ```bash
   HF_HERMES="yes"
   HERMES_IP="<ip-del-hl2>"   # vacío: el primero que conteste por difusión
   HERMES_GAIN="20"           # 0 (-12 dB) a 60 (+48 dB); súbelo con antenas cortas, bájalo si satura
   ```
3. `sudo bash install.sh --solo openwebrx,configuracion` y `sudo bricohams-check | grep -i hermes`.

## 3. Placas del pedido
| Placa | ¿Hace falta para recibir en OpenWebRX+? |
|---|---|
| HL2 | Sí |
| Caja | Recomendable (apantallamiento y disipación) |
| N2ADR (filtros) | Para **transmitir**, obligatoria (paso bajo por banda). En recepción ayuda contra la saturación |
| IO board | No (salidas de banda, PTT y amplificador para uso con PC) |

Mientras OpenWebRX+ use el HL2, ningún otro programa (SparkSDR, Thetis…) puede transmitir con él.

## 4. Antenas recomendadas
El ruido local (fuentes conmutadas, la propia Pi, LED) suele limitar más que la ganancia: prioriza
antenas **lejos de la casa** y un **choque de modo común** en el coaxial.

| Antena | Bandas | RX/TX | Por qué | Coste aprox. |
|---|---|---|---|---|
| **Lazo magnético activo** (p. ej. MLA-30+ o Wellbrook) | 0,1–30 MHz | Solo RX | Poco ruido local, compacto, ideal para una web multiusuario. Alimentar con su propio inyector | 30–250 € |
| **Hilo largo + unun 9:1** (12–25 m + contrapeso) | 160–10 m | RX (TX con acoplador) | Banda ancha, barata, buena para escuchar de todo | 20–40 € |
| **EFHW 49:1** (20 m de hilo) | 40-20-15-10 m | RX y TX (5 W) | Resonante en varias bandas sin acoplador; el HL2 puede transmitir con ella | 30–60 € |
| **OCFD / Windom 4:1** (41 m) | 80–10 m | RX y TX | Cubre casi todas las bandas con poco acoplador | 60–100 € |
| **Turnstile de 10 m** (diseño UVic CfAR) | 28–29,7 MHz | RX y TX | **Polarización circular y lóbulo alto** para satélites de 10 m (perfil SAT 10m) | 80–150 € |
| Vertical con radiales | 40–10 m | RX y TX | Ángulo bajo para DX; necesita buenos radiales | 80–300 € |

Recomendación para esta estación:
1. **Lazo activo** para el receptor web (mejor relación señal/ruido en casa).
2. **Turnstile de 10 m** si se quiere seguir MARMOTSat en HF sin rotor: dos dipolos cruzados de tubo de
   aluminio, alimentados con una **línea de fase de λ/4 de 75 Ω** (≈1,68 m de RG-11 a 29,4 MHz,
   recortada con VNA hasta que haga de corto) y un **balun choque** de 9 vueltas de RG-400 en dos
   toroides de mezcla 31 (Fair-Rite 2631803802). Planos y lista de material:
   [UVic CfAR hf-turnstile-antenna](https://gitlab.uvic-cfar.com/open-source-projects/hf-turnstile-antenna).
3. **EFHW** si se va a transmitir en HF con el HL2 desde un PC.

## 5. Instalación exterior
- **Choque de modo común** en la entrada del cuarto (el mismo balun de 9 vueltas sirve) y masa común.
- **Protector de descargas** en cada coaxial, a tierra; desconecta las antenas en tormenta.
- Estanqueidad de conectores (método de CfAR): grasa dieléctrica en la rosca → cinta Super 33+ →
  cinta semiconductora → Super 88 contra el sol.
- Si una antena se comparte con un transmisor, usa un conmutador o protección de recepción: el HL2 no
  aguanta potencia en la entrada cuando no transmite él.

## 6. Límites
- Perfiles de 384 kHz: 15 y 10 m no caben enteros (se cubre la parte de CW, digitales y SSB baja).
- No probado en una Pi con un HL2 real; `hpsdrconnector` de bookworm en trixie comprobado solo por
  dependencias (binario estático aarch64).
