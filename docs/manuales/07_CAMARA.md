# 07 · Cámara del mástil (Waveshare RPi Camera (F) · OV5647 con visión nocturna)

<!-- guia-visual:inicio -->
> **Ruta visual:** [Cámara y MediaMTX](../GUIA_VISUAL_MODULOS.md#camara).
> Consulta allí requisitos, ilustración, cuadro de instalación, comprobaciones y restauración.
> Los comandos de este manual se ejecutan en Bash en la Pi; revisa el backup antes de cambiarla.
<!-- guia-visual:fin -->

## 1. Cámara y conexión (v4)
- **Cámara:** **Raspberry Pi Camera Module 3 Wide** (SC0874).
  - IMX708 de 12 MP, autofoco de 5 cm a infinito, focal 2,75 mm, 120° en diagonal (102° H × 67° V).
  - **No es NoIR: no ve de noche con IR** (sin LED IR). Para la noche, usa una cámara IP o ilumina. `CAM_TUNING` se deja vacío (libcamera elige `imx708_wide` solo; si lo fijas: `/usr/share/libcamera/ipa/rpi/pisp/imx708_wide.json`).
- **Por qué «no entra»:** la Pi 5 tiene conectores CSI **mini de 22 pines y 0,5 mm**, y la cámara trae un conector **estándar de 15 pines y 1 mm**.
- **Qué cable comprar:** el **«Raspberry Pi 5 Camera Cable» Standard–Mini (15 → 22 pines)** de 200, 300 o 500 mm.
  - En la cámara va el extremo ancho de 15 pines.
  - En la Pi va el estrecho de 22 pines, en el conector **CAM/DISP 0** (o 1), con los **contactos metálicos mirando hacia el puerto Ethernet**.
- **Con el HAT puesto:** la cinta pasa por el hueco lateral entre la Pi y el HAT. Usa la de 300 mm para sacarla por el lado de la caja hasta la ventana de la tapa.
- **Montaje:** la placa (25 × 24 mm, 12,4 mm de alto, 4 × M2 a 21 × 12,5 mm: confirmar con el plano del Product Brief) no es estanca. Va dentro de la caja, con el objetivo a 3 mm de la cara exterior de un cristal de policarbonato o acrílico pegado en la ventana de 20 × 16 mm (`soporte_camara`), y la `visera` por fuera sin entrar en el campo de 67°. Con 120° la ventana no debe recortar la imagen: ≥ 2·d·tan(FOV/2) + Ø objetivo (≈ 8 mm).
- **Comprobar:**
  1. Para MediaMTX: `sudo systemctl stop mediamtx`.
  2. Lanza `rpicam-hello --list-cameras`: debe salir `imx708_wide`.
  3. Haz una prueba: `rpicam-still -o prueba.jpg`.
  4. Si no sale, revisa la orientación de la cinta y que `camera_auto_detect=1` esté en `config.txt`.
- **Enfoque:** es autofoco; comprueba la imagen en `http://<pi>:8889/mastil/`. Si el cristal desenfoca, fija el enfoque con `--lens-position` (≈ 0 para infinito).

## 2. Configuración (`/etc/mediamtx/mediamtx.yml`, la genera el paso `camara`)

| Parámetro | Valor | Por qué |
|---|---|---|
| `source` | `rpiCamera` | cámara CSI |
| Resolución | 1280×720 a 10 fps | equilibrio con la CPU |
| `rpiCameraCodec` | `softwareH264` | la Pi 5 no tiene codificador por hardware |
| `rpiCameraBitrate` | 1,5 Mb/s | |
| `rpiCameraTuningFile` | `CAM_TUNING` | `ov5647_noir.json` si la cámara no tiene filtro IR |

**Accesos:**
- Directo WebRTC: `http://<pi>:8889/mastil/`
- RTSP: `rtsp://<pi>:8554/mastil`
- HLS: `http://<pi>:8888/mastil/`
- Foto para la web: `bricohams-camsnap` cada 60 s a `htdocs/plugins/receiver/camara/snap/mastil.jpg` (tmpfs).

## 3. En OpenWebRX
El botón 📷 **CAM** de la barra abre dos vistas:
- **FOTO:** funciona desde fuera por el puerto 8073.
- **DIRECTO:** solo en la LAN, o si abres 8889/tcp y 8189/udp.

## 4. Ajustes
- **Imagen girada:** `CAM_HFLIP` / `CAM_VFLIP`.
- **Colores rosados de día:** `CAM_TUNING=/usr/share/libcamera/ipa/rpi/pisp/ov5647_noir.json`.
- **Cada vez que cambies algo:** `sudo bash install.sh --solo camara`.
