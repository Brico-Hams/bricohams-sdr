# 07 · Cámara del mástil (WPI408, OV5647 con IR)

## 1. Conexión
- **Cable:** de **15 a 22 pines** (la Pi 5 usa conectores CSI de 22 pines). Va al conector **CAM/DISP 0**.
- **Montaje:** la cámara no es estanca. Ponla dentro de la caja, detrás de una ventana de policarbonato, con los LED IR fuera del reflejo.
- **Comprobar:** `rpicam-hello --list-cameras` debe mostrar `ov5647`. Para esta prueba, para antes MediaMTX con `sudo systemctl stop mediamtx`.

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
