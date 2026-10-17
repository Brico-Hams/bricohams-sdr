# 41 · Plugins de EA5HKX: callsign_gate y tone_detector

<!-- guia-visual:inicio -->
> **Ruta visual:** [Caja, antenas, filtros, alimentación y anclajes](../GUIA_VISUAL_MODULOS.md#hardware).
> Consulta allí requisitos, ilustración, cuadro de instalación, comprobaciones y restauración.
> Los comandos de este manual se ejecutan en Bash en la Pi; revisa el backup antes de cambiarla.
<!-- guia-visual:fin -->

## Qué son

EA5HKX publica dos plugins de receptor para OpenWebRX+ en
<https://gitlab.com/openwebrx-plugins>:

| Plugin | Qué hace | Variable en `bricohams.env` |
|---|---|---|
| [`callsign_gate`](https://gitlab.com/openwebrx-plugins/callsign_gate) | Ventana de bienvenida (ES/EN) que pide indicativo o nombre antes de usar el receptor. Lo guarda solo en el navegador, 14 días desde la última visita, y lo pone como nombre del chat | `PLUGIN_CALLSIGN_GATE="yes"` |
| [`tone_detector`](https://gitlab.com/openwebrx-plugins/tone_detector) | Panel «CTCSS» externo opcional, desactivado por defecto para no duplicar el control integrado | `PLUGIN_TONE_DETECTOR="no"` |

Créditos: ambos son obra de **EA5HKX** (<https://www.qrz.com/db/EA5HKX>); la
estación de referencia es <https://ea5hkx.myqnapcloud.com:8073/>.

## Por qué no van dentro del kit

Los dos repositorios **no publican licencia**, así que el kit no copia ni modifica
su código. `install.sh` (paso `plugins`) los descarga en el momento de instalar:

1. desde `https://gitlab.com/openwebrx-plugins/<plugin>/-/raw/<commit>/<plugin>.js`,
   siempre en un **commit fijo**;
2. comprueba su **sha256**; solo si coincide lo copia a
   `htdocs/plugins/receiver/<plugin>/<plugin>.js`;
3. si no hay red o la suma no coincide, avisa y deja el plugin **desactivado**
   (el resto del receptor funciona igual).

| Plugin | Commit | sha256 |
|---|---|---|
| callsign_gate | `dcd55b51e51a2a3b2e7fd2d20dd7821d686fcb0b` | `aedb2bc8e43d5da36f379f1924f00a2910e96352afeeeef9ad37dcc112e2add8` |
| tone_detector | `9d048ccb5532018349369c3a1a0cc8e9cd11ac10` | `e2acfec0b368a8c52c498f179f9376da2cf3782ed3f581b0af4ba0cfc7200c25` |

Para pasar a una versión nueva: revisa sus cambios, actualiza commit y sha256 en
`EA5HKX_PLUGINS` (`install.sh`) y en `tests/test_plugins_ea5hkx.py`, y pasa las pruebas.

## Configuración

```bash
PLUGIN_CALLSIGN_GATE="yes"        # identificación obligatoria al entrar
CALLSIGN_GATE_ANUNCIO="no"        # «Chat iniciado por …» en el chat en cada visita
PLUGIN_TONE_DETECTOR="no"         # sin boton CTCSS externo duplicado
OWRX_CTCSS_ENABLE="yes"           # conservar Subtono FM integrado
```

Aplica los cambios con `sudo bash install.sh --solo plugins` y recarga la web
con Ctrl+F5. En una instalación ya hecha también puedes cambiar a mano
`window.ea5hkx_config` en `htdocs/plugins/receiver/init.js`.

## Cómo encaja con BricoHams

El plugin local **`ea5hkx_puente`** (código propio del kit) se carga justo antes
de `callsign_gate` y, sin tocar el plugin de EA5HKX:

- cambia «SDR de EA5HKX» por el indicativo de esta estación
  (`window.ea5hkx_config.titulo`; en el kit genérico, `CALLSIGN`);
- sustituye su canal de Telegram por el de `bricohams_config.telegram` (o quita
  el párrafo si no hay canal);
- añade al pie el **aviso de privacidad** y el crédito «plugin de EA5HKX»;
- con `CALLSIGN_GATE_ANUNCIO="no"` (por defecto) **descarta** el mensaje
  automático «Chat iniciado por …» que el plugin envía en cada carga. Así no
  llena el chat y, con `VISITAS_CHAT="yes"`, tampoco el grupo de Telegram.

El plugin `identificacion` ([manual 39](39_REGISTRO_OYENTES.md)) comparte la identidad:

- el indicativo de `callsign_gate` (`openwebrx_callsign`, 14 días) desbloquea el
  chat sin volver a preguntar; si hay varias identidades guardadas, vale la más
  reciente;
- al cambiar el nombre desde el chat se actualiza también el de `callsign_gate`;
- la bienvenida del registro voluntario de oyentes espera a que el visitante
  pase la ventana de `callsign_gate` y sale ya rellena. El registro en el
  servidor sigue siendo **voluntario** y con casilla de consentimiento.

`tone_detector` usa sus propios identificadores (`#openwebrx-panel-tone-detector`,
botón «CTCSS») y no se mezcla con el detector CTCSS del servidor
(`OWRX_CTCSS_ENABLE`, línea «CTCSS» bajo el S‑meter y campo «Subtono FM» de los
marcadores). El del servidor sirve de squelch por tono; el del navegador solo
informa del tono que oye cada oyente. La configuracion recomendada conserva
el integrado y no carga el panel externo ni su boton superior. No se elimina
el detector del servidor, su JavaScript ni los subtonos de los marcadores.

## Privacidad

- `callsign_gate` guarda el indicativo o nombre **solo en el navegador**
  (`localStorage`), sin IP. Con el anuncio desactivado no envía nada al servidor.
- Con `CALLSIGN_GATE_ANUNCIO="yes"` cada visita escribe su indicativo en el
  chat público (y en Telegram si `VISITAS_CHAT="yes"`). Indícalo en las
  políticas si lo activas.
- El bloqueo se hace en el navegador: impide el uso normal sin identificarse,
  pero un cliente manipulado podría saltárselo.

## Comprobar

```bash
cd /usr/lib/python3/dist-packages/htdocs/plugins/receiver   # Docker: el htdocs del contenedor
sha256sum callsign_gate/callsign_gate.js tone_detector/tone_detector.js
grep -n "ea5hkx_config" -A4 init.js
```

En el navegador (ventana privada): aparece la ventana con el indicativo de la
estación; tras escribir un indicativo se puede usar el chat sin otra pregunta;
en un canal NFM con subtono aparece el panel «CTCSS» con el tono detectado.

## Desactivar o restaurar

- Desactivar: pon `PLUGIN_CALLSIGN_GATE="no"` o `PLUGIN_TONE_DETECTOR="no"` y
  repite `sudo bash install.sh --solo plugins`.
- El paso `plugins` guarda `init.js.antes-<fecha>` antes de cambiar `init.js`;
  para volver atrás copia esa versión sobre `init.js` y recarga con Ctrl+F5.
- Un visitante que quiera cambiar su identidad puede pulsar el nombre del chat
  o borrar los datos del sitio en su navegador.
