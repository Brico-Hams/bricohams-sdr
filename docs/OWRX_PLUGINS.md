# Plugins del receptor y API nativa de OpenWebRX+

Desde OpenWebRX+ 1.2.124 (la estación usa 1.2.130) existe `Plugins.addButton`, `Plugins.addWindow`/`toggleWindow` y `Plugins.addSection`. Si la pila `#openwebrx-panel-plugins` no existe, cada plugin conserva su colocación anterior.

## Usan la API nativa

- `solar`: botón SOL + ventana `solar`.
- `meteo`: botón con la temperatura + ventana `meteo`.
- `camara`: botón CAM + ventana `camara`.
- `dvficha`: ventana `dvficha` (ficha automática al recibir una trama, sin botón).
- `visitas`: el resumen de oyentes es la ventana `visitas`; el contador de la cabecera no cambia.
- `bricohams`: botones TG (Telegram) y KIT (hazlo tú mismo), que se abren en pestaña nueva con `noopener` y llevan su texto completo en `title`/`aria-label`, y sección `BricoHams` con el selector de tema. Además, en pantallas de menos de 768 px coloca la pila nativa de botones como una fila encima del receptor: OWRX+ la deja fuera de pantalla en móvil, y eso también afectaba a MAP, DOP, PASES y LST.
- `filtro_audio` y `dsp_audio`: botones FILTRO y DSP + ventanas `filtro` y `dsp` (a través de la interfaz común de `audio_cadena`).

## Se dejan como están

- `consentimiento`: aviso de privacidad que debe verlo todo visitante, no es un panel que se abra.
- `identificacion`: registro/aviso obligatorio a pantalla completa, no es un lanzador.
- `marca`: marca de cabecera.
- `idioma`: traducción del chat.
- `banderas`: banderas del chat.
- `ea5hkx_puente`: puente EA5HKX, sin interfaz propia.
- `panel_visitas`: tarjetas de cabecera siempre visibles.

## Plugins del catálogo 0xAF evaluados (2026-11-19)

- `listeners`: ya está integrado. `init.js` lo carga del catálogo (`rp_url`) con nuestros añadidos (país, perfiles remotos) y solo si hay Supabase configurado. No hay nada que añadir.
- `ctcss_decoder` (MIT; código de TOLYANDR): no se añade. `tone_detector` de EA5HKX ya detecta los mismos tonos CTCSS estándar, con bloqueo y modo automático, y se instala en un commit fijo con su sha256. `ctcss_decoder` solo aportaría «AUTO SQL» y el recuerdo del último tono, a cambio de duplicar el análisis de audio en el navegador y de sumar otra dependencia externa.

## Seguridad: «restringir logins y ajustes a la red local»

La opción de OWRX+ (`allow_remote_config`, en General settings) decide qué es «local» con la IP de la conexión (`owrx/http.py`, `address_string()`). Detrás de nginx esa IP siempre es `127.0.0.1`, que cuenta como red privada, así que **la opción no surte efecto en esta estación**. Para limitar `/login`, `/pwchange` y `/settings` a la LAN hay que hacerlo en nginx (`allow` con los rangos privados y `deny all`). Es una decisión pendiente, porque dejaría al administrador sin acceso desde fuera de la LAN o la VPN.

## Notas

- Las ramas en pruebas de OWRX+ (stereo_drm_dab, SSTV nuevo) no se compilan; se adoptarán con la release 1.2.131.
- No se instala el botón PTT de RigControl: daría transmisión a los oyentes web con el indicativo EA5KAO.
