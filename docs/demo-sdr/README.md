# Demostración SDR narrada y anonimizada

- [Vídeo MP4](SDR_Demo_ES_anonimizada.mp4): 8 min 43 s, narración femenina en español de España, capítulos y subtítulos integrados en la imagen.
- [Subtítulos SRT](SDR_Demo_ES.srt): transcripción sincronizada de la narración.

La voz es sintética: **Microsoft Helena Desktop**, generada localmente con Windows.
El audio original se ha excluido por completo para evitar reproducir conversaciones,
identificadores hablados o audio de terceros. El vídeo fuente permanece sin modificar
y **no se incluye en Git**.

## Recorrido

| Inicio | Opción |
|---|---|
| 00:00 | Inicio, sintonía, espectro y cascada |
| 00:18 | Modos, volumen, silenciador y subtonos |
| 00:36 | Chat del receptor |
| 00:48 | Acceso, identificación y privacidad |
| 01:37 | Selección de receptor y perfil |
| 01:58 | Radiodifusión FM y RDS |
| 02:19 | DX Cluster |
| 02:42 | Actividad solar y propagación |
| 02:57 | Meteorología en red |
| 03:08 | Filtro de audio |
| 03:22 | Procesamiento digital de audio |
| 03:42 | Seguimiento de satélites |
| 04:16 | Archivos recibidos |
| 04:27 | Mapa de recepción y capas |
| 05:00 | Ajustes generales |
| 05:29 | Dispositivos SDR |
| 05:37 | Marcadores de frecuencia |
| 05:52 | Demodulación y decodificación |
| 06:18 | Informes y redes externas |
| 06:26 | Integración ADS-B |
| 06:31 | Administración Meshtastic |
| 06:48 | Pasarela LoRa APRS |
| 06:58 | Acceso web no completado |
| 07:17 | Menú de administración |
| 07:22 | Servidor TAK local |
| 07:37 | Monitorización |
| 07:57 | Otras opciones del menú |
| 08:02 | Cliente web Meshtastic |
| 08:28 | Avisos y cierre |

## Tratamiento de privacidad

- Se recortan las pestañas, la barra de direcciones y los marcadores del navegador.
- Se cubren con máscaras opacas la identificación y ubicación de la cabecera,
  los registros del chat, las notificaciones y la franja inferior de enlaces.
- Las escenas con formularios de identificación, indicativos de terceros, estaciones
  meteorológicas, ubicación del receptor, fichas del mapa, ajustes personales,
  nodos, credenciales, registros o conversaciones se sustituyen por tarjetas
  explicativas. Las tarjetas están identificadas como escenas sustituidas;
  no son capturas de una instalación anonimizada.
- Solo se incluye la pista de narración; no se conserva el audio original como
  pista alternativa. Los metadatos de salida se crean de nuevo.

Se mantiene la duración y el orden del recorrido. La narración distingue entre
**opciones visitadas** y **funciones efectivamente demostradas**: el error de
conexión visible en el original se explica como tal, no como un acceso correcto.
Las opciones de WiFi, seguridad y decodificación en segundo plano solo aparecen
en el menú; no se dan por probadas. Esta edición no despliega ni modifica la estación.

## Comprobación

La revisión comprende el recorrido original, la duración real de cada fragmento
de voz, la sincronización de subtítulos y capítulos, la decodificación del MP4
y una revisión visual/OCR por muestreo de la edición. El OCR es un control
complementario, no una garantía absoluta de anonimato.

Resultado de la comprobación de esta edición:

- MP4 H.264/AAC de **1600 × 900**, **523,267 segundos** y **15.052.705 bytes**.
- Una sola pista de audio, identificada como español; **29 capítulos** y **58 entradas SRT**.
- Decodificación completa sin errores y tiempos de subtítulos válidos y sin solapamientos.
- **677 fotogramas examinados con OCR local**: uno por segundo más muestras
  alrededor de los cambios de escena sensibles. No se detectaron los
  identificadores, direcciones ni datos personales buscados.
- Revisión visual de muestras para comprobar las máscaras y la legibilidad.
- SHA-256 del MP4:
  `88e70f7ab76a514f74d4acf7a2b6b29d60bed2844b1a3adab0442331bcb4873c`.

El resultado no debe sustituirse por otra grabación aplicando las mismas máscaras:
las posiciones y los intervalos están ajustados exclusivamente al vídeo revisado.
