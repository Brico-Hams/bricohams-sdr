# 39 · Registro voluntario de oyentes y registro obligatorio del chat

<!-- guia-visual:inicio -->
> **Ruta visual:** [Plugins, registro de oyentes, CTCSS y RepeaterBook](../GUIA_VISUAL_MODULOS.md#plugins).
> Consulta allí requisitos, ilustración, cuadro de instalación, comprobaciones y restauración.
> Los comandos de este manual se ejecutan en Bash en la Pi; revisa el backup antes de cambiarla.
<!-- guia-visual:fin -->

## Qué hace

Al entrar por primera vez desde un navegador, muestra una bienvenida en español
o inglés inspirada en la tarjeta de acceso de la estación. El oyente puede:

- introducir un indicativo válido o un nombre/apodo;
- aceptar explícitamente que se guarde el identificador y la fecha; o
- continuar sin identificarse, sin enviar esos datos.

Al aceptar, se registra una entrada por sesión del navegador. La preferencia se
recuerda localmente para que el visitante no tenga que aceptar en cada carga; al
abrir otra sesión se registra de nuevo mientras su consentimiento local siga
vigente. La decisión de no identificarse también queda en el almacenamiento
local. Borrar los datos del sitio permite volver a escoger.

## Registro obligatorio para el chat

Desde la v5.0 el chat del receptor exige identificarse, como en otras estaciones
públicas (p. ej. EA5HKX). **Escuchar sigue siendo libre**; solo se bloquea escribir:

- Sin identidad, el campo de mensaje del chat queda de solo lectura con el aviso
  «🔒 Identifícate para usar el chat (clic aquí)». Al pulsarlo, o al intentar
  enviar, se abre la tarjeta «💬 Identifícate para el chat».
- Se pide el indicativo de radioaficionado o, si no se tiene, el nombre (mismas
  reglas de validación que el registro voluntario). Los indicativos se pasan a
  mayúsculas.
- La identidad se guarda **solo en el navegador** (`bh_chat_identidad`) durante
  `chat_dias` (14 días por defecto) y rellena el campo «Name» del chat, que ya no
  se edita a mano: un clic en él abre la tarjeta para cambiarla. Todos los
  mensajes salen con esa identidad (no se puede suplantar escribiendo otro nombre).
- Quien ya aceptó el registro voluntario de oyentes queda identificado también
  en el chat.
- La casilla para guardar además el identificador en el registro de oyentes del
  servidor (180 días) es **opcional** en esta tarjeta y solo aparece si la API
  responde; sin marcarla no se envía nada al servidor.
- Funciona aunque `VISITAS_ENABLE="no"` (entonces no aparece la casilla).

Se activa por defecto. Para desactivarlo:

```bash
CHAT_REGISTRO_OBLIGATORIO="no"     # en bricohams.env
sudo bash install.sh --solo web
```

En una instalación ya hecha se puede cambiar a mano en
`htdocs/plugins/receiver/init.js` (`chat_obligatorio` y `chat_dias` dentro de
`window.identificacion_config`) y recargar la web con Ctrl+F5.

> El bloqueo se hace en el navegador (igual que la referencia EA5HKX): impide el
> uso normal sin identificarse, pero un cliente manipulado podría saltárselo.
> Para expulsar a alguien usa el moderador de chat ([manual 24](24_VISITAS_TELEGRAM.md)).

> **v5.1 · callsign_gate de EA5HKX.** Con `PLUGIN_CALLSIGN_GATE="yes"` (por
> defecto) la identificación se pide ya al entrar, también para escuchar, y ese
> indicativo vale para el chat (14 días). Detalles en el
> [manual 41](41_PLUGINS_EA5HKX.md).

## Datos, privacidad y retención

- Base local: `/var/lib/bricohams/oyentes.sqlite`, con permisos `0600`, propiedad
  del usuario de servicio `openwebrx`.
- Campos: identificador, tipo (indicativo/nombre), fecha Unix y versión del
  consentimiento. **No se guarda IP, geolocalización, frecuencia, audio ni chat**
  en esta base de datos.
- El identificador se conserva hasta 180 días. La API purga vencidos al iniciar
  y al recibir nuevas entradas; además limita el archivo a 100.000 registros.
- **v5.0 · Aviso por Telegram.** Cada registro se avisa al grupo privado de los
  operadores («📝 Oyente registrado: indicativo EA… · QRZ» o el nombre), con las
  mismas credenciales `TELEGRAM_TOKEN`/`TELEGRAM_CHAT_ID` (en `api.env`, 0640).
  Máximo 20 avisos por minuto y sin repetidos en 5 minutos. Se desactiva con
  `OYENTES_TELEGRAM="no"` y `sudo bash install.sh --solo web`. El texto del
  consentimiento lo indica.
- No existe endpoint público para leer la lista. El acceso se hace localmente
  desde la Pi. Para solicitar acceso o supresión de entradas previas, usa el
  contacto publicado en el [aviso de privacidad](../../files/web/privacidad.html).
- Desactivar la preferencia en el navegador detiene las próximas entradas, pero
  no borra automáticamente registros ya guardados; el operador tramita la
  supresión solicitada.

El tratamiento del contador de visitas existente (IP truncada y país aproximado)
es independiente y se explica en [manual 24](24_VISITAS_TELEGRAM.md). El
consentimiento para el nuevo registro no cambia el procesamiento separado de
visitas ni de chat. Configurar `VISITAS_ENABLE="no"` deshabilita ambos servicios
de visitas y la bienvenida de identificación.

## Instalación y configuración

El registro necesita el paso `web`, que instala el plugin, la API local y la
ruta limitada de nginx. Configura el mismo valor en el `bricohams.env` usado por
el instalador:

```bash
VISITAS_ENABLE="yes"
```

Tras crear y comprobar un backup:

```bash
sudo bash install.sh --solo web
```

El plugin verifica `/bricohams/api/salud` antes de mostrar la bienvenida. Así no
solicita datos si falta el proxy o la API. El envío se limita a JSON del mismo
origen, requiere consentimiento explícito, valida el identificador y limita las
peticiones en nginx.

## Consultar el registro

Ejecuta en la Raspberry:

```bash
sudo -u openwebrx bricohams-oyentes
sudo -u openwebrx bricohams-oyentes --limite 500
sudo -u openwebrx bricohams-oyentes --csv > oyentes.csv
```

La salida predeterminada es CSV de las 1.000 entradas más recientes;
`--limite` la acota entre 1 y 100.000, y `--csv` exporta todas las entradas
vigentes. Guarda y comparte el CSV como dato personal; contiene indicativos o
nombres y fechas.

## Desarrollo

1. `files/htdocs/plugins/receiver/identificacion/identificacion.js` crea la
   tarjeta modal, valida localmente indicativos/nombres, exige la casilla y
   conserva la decisión del navegador. El DOM usa texto para los datos del
   usuario y no incluye un identificador en la URL.
2. `files/htdocs/plugins/receiver/init.js` carga el módulo y lo desactiva cuando
   `VISITAS_ENABLE=no`. El plugin consulta salud antes de renderizar o enviar.
3. `files/bin/bricohams-api.py` expone `POST /bricohams/api/oyentes`, acepta
   solo same-origin `application/json` de hasta 1 KiB y valida/normaliza el
   contenido antes de guardarlo. No persiste la IP recibida por el transporte.
4. `files/nginx/bricohams-sdr-rutas.conf` limita el endpoint a POST y aplica un
   límite por dirección de red; el acceso de lectura no está expuesto.
5. `files/bin/bricohams-oyentes` es una consulta SQLite de solo lectura para el
   operador local.

Las pruebas `tests/test_registro_oyentes.py` ejercitan consentimiento,
normalización, formato inválido, origen, tipos de contenido, retención y export
CSV; `tests/run_tests.sh` comprueba además la sintaxis del plugin.

El registro del chat vive en el mismo plugin: `chatInstalar()` espera a que exista
el objeto `Chat` de OpenWebRX+ (reintenta cada 500 ms), envuelve `Chat.send` y
`Chat.sendMessage` (este último fuerza el nombre guardado), y deja el nombre de
solo lectura. Se expone como `Plugins.identificacion.chat` (`identidad`,
`guardar`, `valido`, `abrir`, `aplicar`). `install.sh` sustituye
`__CHAT_REGISTRO__` en `init.js` según `CHAT_REGISTRO_OBLIGATORIO`.
`tests/test_chat_registro.py` lo prueba con un arnés de Node que imita el `Chat`
de OWRX 1.2.126: bloqueo, desbloqueo, suplantación, caducidad, registro previo,
`VISITAS_ENABLE=no`, desactivación y `Chat` que aparece tarde.
