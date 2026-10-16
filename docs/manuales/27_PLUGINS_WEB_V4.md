# 27 · Plugins nuevos de la web (v4)

<!-- guia-visual:inicio -->
> **Ruta visual:** [Plugins, registro de oyentes, CTCSS y RepeaterBook](../GUIA_VISUAL_MODULOS.md#plugins).
> Consulta allí requisitos, ilustración, cuadro de instalación, comprobaciones y restauración.
> Los comandos de este manual se ejecutan en Bash en la Pi; revisa el backup antes de cambiarla.
<!-- guia-visual:fin -->

## Alcance y arquitectura

Los apartados siguientes documentan las extensiones locales de BricoHams y las
adaptaciones que se cargan desde `files/htdocs/plugins/`. No describen como
desarrollo propio los plugins de terceros de OpenWebRX+ ni los de 0xAF. El
coordinador `receiver/init.js` configura y carga los plugins locales en orden;
`audio_cadena` debe preceder a `filtro_audio` y `dsp_audio`.

## Plugins propios del receptor

### `solar`

Añade el botón SOL y la presentación día/noche del QTH de la estación. El
coordinador le entrega latitud y longitud redondeadas; la configuración está en
`files/htdocs/plugins/receiver/init.js` y el cliente en
`files/htdocs/plugins/receiver/solar/solar.js`. Detalles de la ubicación en
[manual 32](32_ZONA_LOCATOR.md).

### `meteo`

Muestra estaciones meteorológicas cercanas, condiciones, curva histórica y
previsión. El navegador consume un JSON local; `bricohams-meteo.py` prepara los
datos, de modo que la clave de AEMET no se expone en JavaScript.

- **Desarrollo:** interfaz y persistencia ligera en `meteo.js`; adquisición y
  caché de datos en `files/bin/bricohams-meteo.py`.
- **Pruebas:** `tests/test_meteo.py`.
- **Referencia:** [manual 06](06_SENSOR_WX.md).

### `camara`

Integra en la barra del receptor la imagen de la cámara de la estación. El
plugin cliente `files/htdocs/plugins/receiver/camara/camara.js` usa el
intervalo definido por `CAM_SNAPSHOT_SECONDS`; el servicio que genera la captura
se documenta por separado.

- **Referencia:** [manual 07](07_CAMARA.md).

### `bricohams`

Aporta el botón/enlace de BricoHams y configura la identidad de estación en la
interfaz. Está implementado en
`files/htdocs/plugins/receiver/bricohams/bricohams.js`; la carga se declara en
`receiver/init.js`.

### `banderas`

Añade la bandera correspondiente al país que OpenWebRX+ ya asocia a cada
decodificación digital (`ccode`). No geolocaliza al operador ni realiza consultas
de país desde el navegador. Implementación:
`files/htdocs/plugins/receiver/banderas/banderas.js`.

### `dvficha`

Al seleccionar una estación digital, presenta indicativo, bandera, nombre,
localidad y, si la fuente lo permite, foto. El cliente
`files/htdocs/plugins/receiver/dvficha/dvficha.js` consulta el endpoint local de
`bricohams-api`; los proveedores y la caché se resuelven en el servidor.

HamQTH es la fuente principal; RadioID y QRZ XML completan los campos que falten
si están configurados. QRZ XML requiere suscripción para los datos completos.
Las fotos de QRZ se enlazan, no se copian. Credenciales solo en
`bricohams.env` con permisos privados, nunca en JavaScript. La ficha completa
requiere nginx; desde `http://IP:8073` solo se muestran los datos que entrega
OpenWebRX+.

### `satelites`

Presenta los próximos pases y el control PASES. El cliente
`files/htdocs/plugins/receiver/satelites/satelites.js` lee el archivo de pases
local y se integra con el seguimiento Doppler disponible en el receptor.

- **Pruebas:** `tests/test_satpass.py`.
- **Referencia:** [manual 26](26_SATELITES.md).

### `visitas`

Muestra oyentes conectados y el contador de visitas, con acceso al aviso de
privacidad. La interfaz está en
`files/htdocs/plugins/receiver/visitas/visitas.js`; los datos y el aviso se
preparan del lado del servidor. El plugin no necesita Supabase.

- **Pruebas:** `tests/test_visitas.py`.
- **Referencia:** [manual 24](24_VISITAS_TELEGRAM.md).

### `identificacion`

Presenta una bienvenida bilingüe para que el visitante pueda compartir
voluntariamente su indicativo o nombre. Exige una casilla de consentimiento; si
continúa sin identificarse, no se envía ningún dato. La API guarda el
identificador y la fecha, no la IP, en una base de datos privada de la estación.
La misma sesión del navegador no se contabiliza repetidamente al recargar.

Además bloquea la escritura en el chat hasta que el oyente indique su indicativo
o nombre (`CHAT_REGISTRO_OBLIGATORIO`, por defecto `yes`); escuchar sigue libre.

- **Desarrollo:** interfaz `files/htdocs/plugins/receiver/identificacion/identificacion.js`;
  validación, endpoint y retención en `files/bin/bricohams-api.py`.
- **Pruebas:** `tests/test_registro_oyentes.py` y `tests/test_chat_registro.py`.
- **Instalación y administración:** [manual 39](39_REGISTRO_OYENTES.md).

## Audio en el navegador

### `audio_cadena`

Base común, sin botón, que conecta las etapas DSP entre el `AudioWorklet` y el
control de volumen de OpenWebRX+. Centraliza el punto de integración para no
alterar el audio cuando ambas etapas están apagadas. Fuente:
`files/htdocs/plugins/receiver/audio_cadena/audio_cadena.js`.

### `filtro_audio`

Añade paso banda por modo, notch manual y automático y visualización del
espectro. Todo el procesado ocurre en el navegador de cada oyente; no cambia la
señal de los decodificadores ni la grabación. Fuente:
`files/htdocs/plugins/receiver/filtro_audio/filtro_audio.js`.

### `dsp_audio`

Añade ecualización, puerta de ruido, AGC, limitador, preajustes y medidores en
el navegador. Fuente:
`files/htdocs/plugins/receiver/dsp_audio/dsp_audio.js`.

Los tres plugins se desarrollaron como una cadena desacoplada de Web Audio. Las
pruebas automáticas cubren carga, reproducción y atenuación del tono de prueba:
`tests/test_audio_plugins.py` y `tests/test_audio_navegador.py`. La descripción
de controles y sus límites está en [manual 30](30_AUDIO_DSP.md).

## Mapa e integración con Rig Skin

### `bricohams_live`

Extiende el mapa con trayectorias APRS y fichas de aeronaves ADS-B. Mantiene
historial limitado en memoria, valida coordenadas y limita el número de
trayectorias y fichas; las fotos y datos opcionales se piden al abrir una ficha.
Código: `files/htdocs/plugins/map/bricohams_live/` y
`files/htdocs/plugins/map/init.js`.

- **Pruebas:** `tests/test_live_map.py` y `tests/test_avion.py`.
- **Referencia:** [manual 04](04_ADSB.md).

### `rig_skin`: integración de etiquetas DX

Rig Skin es un plugin externo. BricoHams lo integra desde `receiver/init.js` y
añade la presentación de los spots DX como etiquetas sobre la barra de
frecuencias. La adaptación mantiene el último spot por indicativo durante un
máximo de tres horas; al seleccionarlo, sintoniza su frecuencia. No se atribuye
a BricoHams el código original de Rig Skin.

<a id="instalacion-plugins-propios"></a>

## Instalación de plugins propios

Haz una copia previa verificada antes de modificar una estación. El paso
`plugins` copia los ficheros locales, instala el coordinador `init.js` y prepara
los directorios de datos; requiere que OpenWebRX+ ya esté instalado. Ejecuta
una sola vez el comando adecuado:

| Módulo | Pasos del instalador |
|---|---|
| Plugins locales del receptor, audio y mapa (`solar`, `meteo`, `camara`, `bricohams`, `banderas`, `dvficha`, `satelites`, `visitas`, `identificacion`, `audio_cadena`, `filtro_audio`, `dsp_audio`, `bricohams_live`) | `sudo bash install.sh --solo plugins` |
| `dvficha` con API local, portal/privacidad y proxy nginx | `sudo bash install.sh --solo plugins,web` |

`--solo plugins` no instala OpenWebRX+ ni configura proveedores externos. Para
la ficha DV, guarda las credenciales en la configuración privada y habilita
nginx según los manuales 23 y 24. No pongas claves en el código, en capturas ni
en registros compartidos.

**Comprobar:** recarga el receptor con `Ctrl+F5`; para el audio ejecuta
`bash tests/run_tests.sh` en el kit. Con backend nativo revisa
`systemctl status openwebrx --no-pager`; con Docker consulta el contenedor
configurado. Para volver atrás, restaura la copia previa siguiendo el manual 09
o 31.

## Plugins de terceros y ajustes, no desarrollos locales

`doppler`, `listeners`, `layer_qth_maidenhead`, el plan de bandas y otros
plugins de 0xAF/OpenWebRX+ se configuran o integran, pero su código base no se
mantiene aquí como plugin BricoHams. El plan de bandas se muestra por defecto
la primera vez y el oyente puede ocultarlo. `listeners` requiere un proyecto
Supabase propio; publica presencia anónima de frecuencia, modo y perfil, no el
indicativo ni el país individual del oyente. `LISTENERS_COUNTRY` añade el país
del receptor (ISO de dos letras; vacío usa `STATION_COUNTRY`), no geolocaliza
al visitante. Las variables `LISTENERS_SUPABASE_URL` y
`LISTENERS_SUPABASE_KEY` se entregan al cliente y deben tener permisos mínimos.
Nunca uses una clave `service_role` en el navegador ni en `bricohams.env`.

La escala de la tarjeta del logo y la imagen superior son ajustes de marca, no
plugins: se gestionan con `files/branding` y `tools/branding.py`.
