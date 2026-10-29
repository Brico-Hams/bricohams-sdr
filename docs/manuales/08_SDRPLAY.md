# 08 · Cuando llegue el SDRplay

<!-- guia-visual:inicio -->
> **Ruta visual:** [OpenWebRX+, RTL-SDR y SDRplay](../GUIA_VISUAL_MODULOS.md#receptor).
> Consulta allí requisitos, ilustración, cuadro de instalación, comprobaciones y restauración.
> Los comandos de este manual se ejecutan en Bash en la Pi; revisa el backup antes de cambiarla.
<!-- guia-visual:fin -->

La plantilla ya trae el receptor `hf` (SDRplay) **desactivado**, con 12 perfiles `sp*` de los valores de EA7CL y escucha automática según el Sol (día 20 m, crepúsculo 40 m, noche 80 m).

## Paso a paso
1. Conecta el SDRplay a un **USB 3.0** de la Pi, con la antena de HF.
2. En `bricohams.env`:
   ```bash
   INSTALL_SDRPLAY_API="yes"
   HF_SDRPLAY="yes"
   SDRPLAY_ANTENNA=""            # RSP1A/RSP1B: vacío. RSPdx: "Antenna A", "Antenna B" o "Antenna C"
   ```
3. `sudo bash install.sh --solo sdrplay,configuracion`
   - Descarga la API oficial (3.15.2) y te pide **aceptar la licencia**.
   - Activa el receptor `hf` y **quita los perfiles de HF del V3**, que vuelve a ser solo MULTIPERFIL.
4. `sudo bricohams-check`: en la sección SDR debe salir «SDRplay detectado (HF)».

## Muestreos del SDRplay (SoapySDRPlay3)
- **384 kS/s:** 160, 60, 40, 30, 17 y 12 m.
- **500 kS/s:** 20 m.
- **1 MS/s:** 15 m y 11 m.
- **2 MS/s:** 10 m.
- **3 MS/s:** 80 m (centro 2,8 MHz, cubre también 160 m) y 6 m.

El detalle está en [DATOS.md](../DATOS.md).

## Si la API no se descarga
Baja la versión para Linux de https://www.sdrplay.com/downloads/, cambia `SDRPLAY_API_URL` y repite el paso 3.
