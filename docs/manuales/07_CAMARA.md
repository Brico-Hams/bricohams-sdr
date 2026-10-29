# 07 · Cámara del mástil (Waveshare RPi Camera (F) · OV5647 con visión nocturna)

<!-- guia-visual:inicio -->
> **Ruta visual:** [Cámara y MediaMTX](../GUIA_VISUAL_MODULOS.md#camara).
> Consulta allí requisitos, ilustración, cuadro de instalación, comprobaciones y restauración.
> Los comandos de este manual se ejecutan en Bash en la Pi; revisa el backup antes de cambiarla.
<!-- guia-visual:fin -->

## 1. Cámara y conexión (v4)
- **Cámara:** **Waveshare RPi Camera (F)**.
  - OV5647 de 5 MP, enfoque manual, 50° de diagonal y dos LED IR de 850 nm.
  - **No tiene filtro IR-CUT: es NoIR permanente.** Por eso `CAM_TUNING` usa por defecto `/usr/share/libcamera/ipa/rpi/pisp/ov5647_noir.json` para que los colores de día no salgan rosados.
- **Por qué «no entra»:** la Pi 5 tiene conectores CSI **mini de 22 pines y 0,5 mm**, y la Waveshare trae un cable **estándar de 15 pines y 1 mm**.
- **Qué cable comprar:** el **«Raspberry Pi 5 Camera Cable» Standard–Mini (15 → 22 pines)** de 200, 300 o 500 mm.
  - En la cámara va el extremo ancho de 15 pines.
  - En la Pi va el estrecho de 22 pines, en el conector **CAM/DISP 0** (o 1), con los **contactos metálicos mirando hacia el puerto Ethernet**.
- **Con el HAT puesto:** la cinta pasa por el hueco lateral entre la Pi y el HAT. Usa la de 300 mm para sacarla por el lado de la caja hasta la ventana de la tapa.
- **Montaje:** la cámara no es estanca. Va dentro de la caja, detrás de la ventana de policarbonato (`soporte_camara`), con los LED IR fuera del reflejo y la `visera` por fuera.
- **Comprobar:**
  1. Para MediaMTX: `sudo systemctl stop mediamtx`.
  2. Lanza `rpicam-hello --list-cameras`: debe salir `ov5647`.
  3. Haz una prueba: `rpicam-still -o prueba.jpg --tuning-file /usr/share/libcamera/ipa/rpi/pisp/ov5647_noir.json`.
  4. Si no sale, revisa la orientación de la cinta y que `camera_auto_detect=1` esté en `config.txt`.
- **Enfoque:** gira la lente con la herramienta que trae, mirando la imagen en `http://<pi>:8889/mastil/`.

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
