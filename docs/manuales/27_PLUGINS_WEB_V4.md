# 27 · Plugins nuevos de la web (v4)

| Plugin | Qué hace | Dónde |
|---|---|---|
| **banderas** | pone la **bandera del país** delante de cada mensaje FT8, FT4, FT2, WSPR, JT65… del panel de modos digitales. El país lo calcula OpenWebRX+ (`ccode`) | `plugins/receiver/banderas/` |
| **dvficha** | ficha del operador que habla en **DMR, YSF, NXDN o D-Star**: bandera, indicativo con enlace a QRZ, nombre, ciudad y país y, si hay credenciales de QRZ XML, **foto** | `plugins/receiver/dvficha/` + `bricohams-api` |
| **satelites** | aviso de próximos pases, botón PASES y ▶ Escuchar con Doppler (manual 26) | `plugins/receiver/satelites/` |
| **visitas** | oyentes conectados con sus países y contador de visitas, con enlace al aviso de privacidad (manual 24) | `plugins/receiver/visitas/` |
| **doppler** (0xAF) | seguimiento Doppler (botón DOP). Ya estaba; ahora lo usa ▶ Escuchar | 0xAF |
| **plan de bandas** | visible por defecto la primera vez (sustituye a `show_band_plan`, que 0xAF marca como obsoleto). Cada oyente puede apagarlo | `bricohams` |
| **listeners** (0xAF) | quién escucha qué frecuencia en tiempo real. **Necesita un proyecto Supabase propio**: pon `LISTENERS_SUPABASE_URL` y `LISTENERS_SUPABASE_KEY` y se carga solo. Sin ellos no se carga. Para el recuento sin Supabase está el plugin **visitas** | 0xAF |
| **imagen superior** | la tarjeta del logo de BricoHams es ahora **la mitad de pequeña** y va arriba a la derecha. La foto de cabecera abierta mide 210 px | `files/branding`, `tools/branding.py` |

## Ficha DMR/YSF: de dónde salen los datos
1. **DMR y NXDN:** OpenWebRX+ ya consulta **RadioID** con el número DMR y trae el indicativo, el nombre y la ciudad.
2. **YSF y D-Star:** solo traen el indicativo. El plugin pregunta a `bricohams-api`, que consulta RadioID por indicativo y guarda la respuesta 7 días en caché.
3. **Foto y nombre de QRZ:** solo con **suscripción XML de QRZ**. Pon `QRZ_USER` y `QRZ_PASS` en `bricohams.env` y lanza `sudo bash install.sh --solo web`.
   - **Respeta las condiciones de QRZ:** la foto solo se enlaza y no se copia al servidor.
   - **Sin suscripción:** la ficha sale sin foto, con el enlace a qrz.com.

**Nota:** la ficha completa necesita nginx (manual 23). Desde `http://IP:8073` solo salen los datos que trae el propio OpenWebRX+.
