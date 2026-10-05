# 27 · Plugins nuevos de la web (v4)

| Plugin | Qué hace | Dónde |
|---|---|---|
| **banderas** | pone la **bandera del país** delante de cada mensaje FT8, FT4, FT2, WSPR, JT65… del panel de modos digitales. El país lo calcula OpenWebRX+ (`ccode`) | `plugins/receiver/banderas/` |
| **dvficha** | ficha del operador que habla en **DMR, YSF, NXDN o D-Star**: bandera, indicativo con enlace a QRZ, nombre, ciudad y país y foto si la fuente la ofrece | `plugins/receiver/dvficha/` + `bricohams-api` |
| **satelites** | aviso de próximos pases, botón PASES y ▶ Escuchar con Doppler (manual 26) | `plugins/receiver/satelites/` |
| **visitas** | oyentes conectados con sus países y contador de visitas, con enlace al aviso de privacidad (manual 24) | `plugins/receiver/visitas/` |
| **doppler** (0xAF) | seguimiento Doppler (botón DOP). Ya estaba; ahora lo usa ▶ Escuchar | 0xAF |
| **plan de bandas** | visible por defecto la primera vez (sustituye a `show_band_plan`, que 0xAF marca como obsoleto). Cada oyente puede apagarlo | `bricohams` |
| **listeners** (0xAF) | quién escucha qué frecuencia y modo en tiempo real. **Necesita un proyecto Supabase propio**: configura `LISTENERS_SUPABASE_URL` y `LISTENERS_SUPABASE_KEY`; sin ellos no se carga. `LISTENERS_COUNTRY` añade la bandera del país del receptor (ISO de dos letras; vacío usa `STATION_COUNTRY`), no geolocaliza al visitante. Las filas locales sintonizan; las remotas abren el receptor y preseleccionan el perfil si el destino tiene esta integración. Para el recuento sin Supabase está el plugin **visitas** | 0xAF + `init.js` |
| **filtro_audio** (v4.2) | botón **FILTRO**: paso banda por modos (Voz SSB, AM, CW, Digital, FM, Libre), notch manual y **notch automático** contra pitidos, con espectro. En el navegador de cada oyente (manual 30) | `plugins/receiver/filtro_audio/` |
| **dsp_audio** (v4.2) | botón **DSP**: ecualizador de 3 bandas, puerta de ruido, AGC y limitador, con preajustes y medidores (manual 30) | `plugins/receiver/dsp_audio/` |
| **audio_cadena** (v4.2) | base común de los dos anteriores (sin botón): los mete entre el audio de OpenWebRX+ y el volumen | `plugins/receiver/audio_cadena/` |
| **imagen superior** | la tarjeta del logo de BricoHams es ahora **la mitad de pequeña** y va arriba a la derecha. La foto de cabecera abierta mide 210 px | `files/branding`, `tools/branding.py` |

**Privacidad de LST:** publica presencia anónima de frecuencia, modo y perfil; no comparte indicativo ni país individual del oyente. Usa la clave pública/publishable de Supabase, con permisos Realtime mínimos; nunca pongas una clave `service_role` en `bricohams.env`.

## Ficha DMR/YSF: de dónde salen los datos
1. **HamQTH:** fuente principal para nombre, ciudad, país y foto. Crea una cuenta gratuita en HamQTH y pon su indicativo y contraseña como `HAMQTH_USER` y `HAMQTH_PASS` en `bricohams.env`.
2. **RadioID:** fuente secundaria gratuita para completar los datos disponibles, especialmente en DMR/NXDN.
3. **QRZ XML:** fuente secundaria opcional. Pon `QRZ_USER` y `QRZ_PASS` en `bricohams.env`; el acceso completo y las fotos de QRZ requieren una suscripción XML.
4. HamQTH tiene prioridad; las fuentes secundarias completan los campos que falten cuando están configuradas. El resultado se guarda 7 días en caché. Tras cambiar credenciales, aplica la configuración con `sudo bash install.sh --solo web`.
   - **Respeta las condiciones de QRZ:** la foto solo se enlaza y no se copia al servidor.
   - Sin cuenta HamQTH, RadioID y QRZ (si está configurado) siguen como alternativas.

**Nota:** la ficha completa necesita nginx (manual 23). Fuentes de la ficha (v4.2, cambio de EA5KAO): **HamQTH** primero (API v2 con token, cuenta gratuita), después RadioID y QRZ XML para completar. Desde `http://IP:8073` solo salen los datos que trae el propio OpenWebRX+.
