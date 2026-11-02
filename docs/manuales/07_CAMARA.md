# 07 · Cámara pública del mástil (Camera Module 3 · IMX708 Wide)

<!-- guia-visual:inicio -->
> **Ruta visual:** [Cámara y MediaMTX](../GUIA_VISUAL_MODULOS.md#camara).
> Consulta allí requisitos, ilustración, cuadro de instalación, comprobaciones y restauración.
> Los comandos de este manual se ejecutan en Bash en la Pi; crea y verifica el backup antes de cambiarla.
<!-- guia-visual:fin -->

## 1. Cámara y conexión

- **Cámara instalada:** Raspberry Pi Camera Module 3 gran angular, sensor `imx708_wide`, 4608 × 2592 píxeles y autofoco.
- **Cable:** Raspberry Pi 5 Camera Cable Standard–Mini (15 → 22 pines). Conecta y desconecta únicamente con la Raspberry apagada; el índice `0` de libcamera no identifica el número del conector físico.
- **Montaje:** protección de intemperie y ventana limpia delante de la lente. El encuadre definitivo es el mástil; las imágenes de pruebas interiores también son públicas mientras la transmisión esté activa.
- **Perfil del sensor:** `CAM_TUNING=""` permite que libcamera seleccione automáticamente el perfil de la cámara detectada. No fuerces `ov5647_noir.json` en una IMX708.
- **Cámara anterior:** Waveshare RPi Camera (F), OV5647 NoIR de 5 MP y enfoque manual. Solo para ese sensor conserva la opción explícita `CAM_TUNING=/usr/share/libcamera/ipa/rpi/pisp/ov5647_noir.json`.

## 2. Configuración

`/etc/mediamtx/mediamtx.yml` se genera en el paso `camara`.

| Parámetro | Valor | Motivo |
|---|---|---|
| `source` | `rpiCamera` | Cámara CSI |
| Resolución | 1280 × 720 a 10 fps | Limitar carga en la Pi |
| `rpiCameraCodec` | `softwareH264` | La Pi 5 no tiene codificador H.264 por hardware |
| `rpiCameraBitrate` | 1,5 Mb/s | Caudal por espectador aproximado |
| `rpiCameraTuningFile` | `CAM_TUNING` vacío por defecto | Selección automática del perfil |
| RTSP | TCP en `127.0.0.1:8554` | Solo consumidores internos, incluida la foto periódica |
| HLS | `127.0.0.1:8888` | Solo accesible mediante el proxy Nginx |
| WebRTC | Desactivado | Evitar puertos adicionales para vídeo |

Nginx sirve `/camara/` desde el HLS interno. El vídeo y las fotos son públicos para todos los usuarios del SDR; los ajustes y la administración conservan su autenticación. No reenvíes los puertos de MediaMTX en el router. El navegador utiliza únicamente HTTPS por el **443**, sin conexiones a 8889 ni a UDP 8189.

## 3. En OpenWebRX+

El botón 📷 **CAM** ofrece:

- **FOTO:** imagen pública en `static/plugins/receiver/camara/snap/mastil.jpg`, por el mismo HTTPS del SDR. `bricohams-camsnap` la actualiza cada 60 s y la guarda en tmpfs.
- **DIRECTO:** HLS público en `https://DOMINIO/camara/mastil/`. `live: 'auto'` utiliza esa ruta en el mismo origen. HLS tiene cierto retardo respecto a la escena.

Cerrar el panel retira la imagen o el reproductor. No hay detección automática de disponibilidad ni cambio automático de DIRECTO a FOTO.

## 4. Comprobación y ajustes

Sin detener MediaMTX, comprueba una captura del flujo interno:

```bash
ffmpeg -hide_banner -loglevel error -rtsp_transport tcp \
  -i rtsp://127.0.0.1:8554/mastil \
  -frames:v 1 -y /tmp/mastil-test.jpg
```

Abre la imagen para verificar nitidez y color. Revisa FOTO y DIRECTO desde el SDR mediante HTTPS, también desde una conexión exterior; comprueba en las herramientas de red del navegador que la cámara solo utiliza el 443.

`rpicam-hello --list-cameras` permite identificar el sensor. Una captura independiente con `rpicam-still` requiere liberar la cámara: MediaMTX mantiene acceso exclusivo. Pararlo interrumpe el vídeo público; vuelve a iniciarlo al terminar.

- **Imagen girada:** ajusta `CAM_HFLIP` / `CAM_VFLIP`.
- **Color incorrecto:** comprueba el sensor detectado y elimina un perfil forzado de otra cámara antes de ajustar el balance de blancos.
- **Aplicar configuración:** después del backup verificado, `sudo bash install.sh --solo camara`. Comprueba el reinicio del servicio y la reproducción; un servicio activo no demuestra por sí solo que la imagen sea correcta.
