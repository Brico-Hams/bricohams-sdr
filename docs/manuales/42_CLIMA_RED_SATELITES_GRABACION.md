# 42 · Clima en red, balizas WSPR, grabación automática de pases e informe AMSAT (v5.0)

<!-- guia-visual:inicio -->
> **Ruta visual:** [Satélites, Doppler y FT2 experimental](../GUIA_VISUAL_MODULOS.md#satelites).
> Consulta allí requisitos, ilustración, cuadro de instalación, comprobaciones y restauración.
> Los comandos de este manual se ejecutan en Bash en la Pi; revisa el backup antes de cambiarla.
<!-- guia-visual:fin -->

Página nueva del portal: **`https://TU_DOMINIO/bricohams/clima.html`** (tarjeta «🌦️ Clima en red y satélites» y enlace al pie de la ventana METEO del receptor). Tema oscuro, se refresca cada minuto y reúne:

| Bloque | De dónde sale | Servicio |
|---|---|---|
| 🏠 Nuestro sensor | `meteo/sensor.json` | `bricohams-wx` (manual 06) |
| 📡 Estaciones WX cercanas | APRS-IS, solo lectura | `bricohams-wx-red` |
| 🛰️ Paquetes APRS por satélite | APRS-IS (`RS0ISS`, `ARISS`, `NA1SS`, `PSAT`…) | `bricohams-wx-red` |
| 📶 Balizas WSPR (24 h) | [wspr.live](https://wspr.live) | `bricohams-wspr.timer` |
| 🗓️ Próximos pases que se grabarán · 🎙️ Grabaciones · AMSAT | `satelites/grabaciones.json` y `pases.ics` | `bricohams-satrec` |

## 1. Clima en red (APRS-IS)

### Administracion sencilla desde Settings

Con sesion de administrador, **Settings > Satelites y agendas** abre
`/settings/bricohams/satelites`. Permite activar la captura automatica, ajustar
la elevacion minima, habilitar METEOR y marcar los satelites que se desean
capturar. La tabla muestra los proximos pases y permite **Omitir este pase**
sin desactivar el resto de la agenda de ese satelite. **Reconsiderar** retira
esa exclusion; los filtros de elevacion, disponibilidad de perfil y solapes
siguen aplicandose. No fuerza una captura ni envia informes AMSAT.

El calendario ICS contiene las capturas planificadas, no todos los pases
visibles. Las horas de la tabla corresponden a la zona horaria del servidor.
Se muestran las ultimas capturas con sus resultados reales y enlaces a Files.
Las omisiones se guardan como `NORAD:epoch_AOS` en `SATREC_OMITIR_PASES`.
Un recalculo orbital que cambie el AOS crea un pase distinto; revisar la agenda.

**Settings > Clima en red**, `/settings/bricohams/clima`, permite ajustar el
radio APRS-IS (5-500 km), la antiguedad maxima (1-24 h) y la inclusion de
paquetes espaciales. Muestra el estado de conexion publicado y enlaza a las
estaciones y datos meteorologicos. No modifica el sensor local ni transmite RF.

Ambos paneles requieren sesion administrativa, mismo origen y token CSRF.
Antes de guardar se crea y verifica una copia de ambos entornos en
`/var/backups/bricohams/settings-agendas-*`, con permisos privados y
`RESTAURAR.sh`. El aviso indica su ubicacion y el comando de restauracion.
Si falla la copia, no se guarda ni reinicia nada. Los cambios de agenda se
bloquean durante un pase y en el minuto anterior/posterior, para no cortarlo.
Al guardar se reinicia unicamente el servicio correspondiente; si no arranca,
se muestra el error y como restaurar. El clima puede tardar un minuto en
publicar nuevas estaciones tras reconectar. No se cambian las claves ni
`AMSAT_REPORT`.

El instalador habilita la escritura del directorio de backups en la unidad
administrativa. Para actualizar una instalacion existente puede utilizarse
`tools/desplegar-agendas.sh` con el kit nuevo y el instalado como argumentos.
El despliegue crea y verifica su propia copia de los ejecutables, unidad,
plantillas, estilos y fuentes afectadas antes de modificarlos.

- `bricohams-wx-red` abre una conexión **de solo lectura** con APRS-IS (`rotate.aprs2.net:14580`, login con `pass -1`: no necesita ni envía el passcode). Filtro: `r/LAT/LON/WXRED_RADIO_KM` más los digis espaciales.
- Decodifica las tramas WX de APRS: sin posición (`_`), con posición sin comprimir o comprimida (`!`, `=`, `@`, `/`) y objetos (`;`). Pasa °F→°C, mph→km/h, centésimas de pulgada→mm y décimas de hPa→hPa. Descarta valores imposibles (p. ej. `t288`).
- **Vía** de cada estación:
  - **rf**: la oyó por radio uno de **nuestros** igates (`IGATE_CALLSIGN`, `RAK_CALLSIGN`, `WXRED_IGATES`), con `qAR`/`qAo`/`qAO`;
  - **satélite**: pasó por un digipetidor espacial (ARISS solo cuenta si lleva `*`, es decir, si realmente lo repitió); estas se muestran **a cualquier distancia**;
  - **internet**: el resto.
- Nuestra estación WX (`WX_APRS_CALLSIGN`, solo si `WX_APRS="yes"`) sale la primera y resaltada.
- Escribe `meteo/wx-red.json` cada minuto. Las estaciones caducan a las 3 h. Reconecta solo (5 s → 5 min); 2 min sin tráfico = reconexión.
- **Aviso:** si el BME280/BME680 está dentro de la caja, su temperatura es la de la caja (más alta que la del aire). La página lo indica. Presión y humedad sí valen.

## 2. Balizas WSPR
- **OpenWebRX+ ya decodifica y reporta WSPR** cuando un perfil de HF está en modo WSPR y en *Settings → Reporting* están activados «WSPRnet» y su indicativo (comprobado en la estación: los spots salen en wspr.live con nuestro indicativo).
- `bricohams-wspr` (cada 15 min) consulta en **wspr.live** las balizas oídas por ese indicativo en las últimas 24 h y escribe `meteo/wspr.json`: número de balizas y estaciones, reparto por bandas, la más lejana y las 40 últimas.
- De `settings.json` solo lee `wsprnet_enabled` y `wsprnet_callsign`; las claves y contraseñas de OpenWebRX+ no se copian a ningún sitio.
- Indicativo: `WSPR_CALLSIGN` > el de WSPRnet de OpenWebRX+ > `CALLSIGN`. Con `N0CALL` no consulta nada.

## 3. Grabación automática de los pases
`bricohams-satrec` lee `pases.json` (manual 26) y planifica:

| Pase | Acción |
|---|---|
| elevación máxima ≥ `SATREC_MIN_EL` (20°), modo NFM/USB/LSB/AM/CW | **graba el audio** |
| METEOR (perfil `meteor`) con `SATREC_METEOR="yes"` | pone el perfil `sat|meteor` y se desconecta: **SatDump** saca la imagen en Files |
| satélite en `SATREC_EXCLUIR` o solapado con otro ya planificado | no se graba |

Cómo graba:
1. 20 s antes del AOS se conecta al websocket local de OpenWebRX+ (`ws://127.0.0.1:8073/ws/`) como un oyente más, selecciona el perfil del satélite y sintoniza la bajada.
   Antes de calcular el desplazamiento, espera la respuesta al ping enviado
   despues de seleccionar el perfil. OpenWebRX+ puede anunciar el identificador
   nuevo antes de actualizar la frecuencia central; la respuesta confirma que
   termino de procesar esa seleccion. Evita usar la frecuencia del perfil
   anterior (por ejemplo, METEOR al cambiar a ISS), sin pausas arbitrarias.
   Si falta la confirmacion o el perfil no coincide, cierra la conexion y
   registra un error; no graba con una configuracion sin confirmar.
2. Corrige el **Doppler con SGP4** cada 2 s (los mismos elementos orbitales de CelesTrak).
3. Decodifica el audio (ADPCM, igual que el navegador) a WAV de 12 kHz y, al acabar, lo pasa a **MP3** (`lame`, 32 kbps mono).
4. En NFM estima si **se oyó el satélite**: compara el ruido de los primeros segundos (antes del AOS) con el del pase; si el silenciador de FM se cierra lo bastante tiempo, lo marca como «oído».
5. Guarda la grabación en `/var/lib/bricohams/satelites/grabaciones/` (se borran las de más de `SATREC_DIAS` días o cuando pasan de `SATREC_MAX_MB`; antes ya se han copiado al archivo permanente, ver 3.1).
6. Enlaza las **2 últimas** (`SATREC_EN_FILES`, igual a `ARCHIVO_FILES_ULTIMOS`) en `/tmp` con el nombre que acepta OpenWebRX+ (`SO50-261017-082700-436795.mp3`), así salen en el menú **Files** del receptor y en la página «Clima en red» con reproductor y descarga.

### 3.1 Archivo permanente de «Files»
`bricohams-archivo-files.timer` (cada minuto) copia **todo** lo que aparece en «Files» —imágenes METEOR/SatDump, SSTV, FAX, MP3 de pases y grabaciones de los oyentes— a `/var/lib/bricohams/satelites/archivo/AAAA-MM/`. Cada copia se verifica con SHA-256 y **el archivo nunca se borra automáticamente**; un nombre repetido con otro contenido se guarda como `nombre~1.ext`.

Después deja en «Files» solo los `ARCHIVO_FILES_ULTIMOS` (2) ficheros más recientes, más las 2 últimas grabaciones de `bricohams-satrec`. Solo quita de Files lo que ya está archivado y verificado; los ficheros modificados hace menos de 60 s se esperan (aún se están escribiendo). Si el disco baja de `ARCHIVO_MIN_LIBRE_MB` (500) no copia ni quita nada y lo anota en el registro. `keep_files` de OpenWebRX+ queda en 100 solo como red de seguridad: con un valor bajo, SatDump (que genera varias imágenes por pase) perdería imágenes antes de archivarlas.

```bash
sudo -u openwebrx bricohams-archivo-files --simular   # qué copiaría y qué quitaría de Files
journalctl -u bricohams-archivo-files -n 20 --no-pager
ls -lR /var/lib/bricohams/satelites/archivo | tail
```

> **Importante:** durante el pase el grabador ocupa el SDR de satélites con ese perfil, igual que lo haría un oyente. Los oyentes que estén en otro perfil de ese mismo SDR verán el cambio. Si no lo quieres, `SATREC_ENABLE="no"`.
> **IO-117 (435,310 MHz)** queda fuera de la banda del perfil `sat70` (centro 436,7 MHz, 2,4 MS/s): el grabador no lo intenta y lo anota como error de frecuencia. Para grabarlo, crea un perfil centrado más abajo.

Para actualizar solo el grabador en una instalacion existente, usar
`sudo bash tools/actualizar-satrec.sh /ruta/kit-nuevo /ruta/kit-instalado`.
Rechaza pases en curso o inminentes y verifica el backup de ambos ejecutables
antes de modificarlos. Muestra su ubicacion y `RESTAURAR.sh`; no borra
capturas anteriores ni cambia frecuencias, agendas o el modo de informes AMSAT.

### Calendario
`/static/plugins/receiver/satelites/pases.ics` (enlace «📅 Pases en tu calendario» en la página): todos los pases planificados con aviso 5 min antes. Se puede suscribir desde Google Calendar, Outlook o el móvil.

## 4. Informe a AMSAT
- **Settings > Satelites y agendas > Capturas y reportes AMSAT.org** permite
  revisar el resultado de cada grabacion y enviarlo manualmente al sitio
  oficial. Incluye satelite, fecha UTC, indicativo y locator; exige seleccionar
  el resultado observado y confirmar el envio. El boton **envia**, no abre
  una vista previa. Comprobar la respuesta de AMSAT en la nueva pestana:
  el panel no puede confirmar su aceptacion ni detectar duplicados manuales.
- Las capturas historicas grabadas sin campo `amsat` pueden usar la asociacion
  NORAD del catalogo actual para generar el formulario, sin alterar su historial.
  No hay formulario para errores de captura, satelites sin asociacion o
  indicativo no configurado. En SSB no se presupone que el satelite fue oido.
- **Files no permite borrar manualmente desde la web**, tampoco con sesion
  administrativa: no muestra botones y el servidor devuelve HTTP 403.
  Las descargas y la limpieza automatica de Files siguen activas;
  Files no es un archivo permanente: todo queda copiado en
  `/var/lib/bricohams/satelites/archivo/` (apartado 3.1).
  El parche se reaplica tras actualizar el paquete OpenWebRX+ mediante el
  gancho `99bricohams-owrx-files`; un formato incompatible produce un error.
  Actualizacion segura: `tools/desplegar-files-amsat.sh /kit/nuevo /kit/instalado`
  con sudo, fuera de los pases. Verifica backup y restauracion antes de cambiar
  controlador, panel y gancho. Reinicia OpenWebRX+ y el panel (breve desconexion
  de oyentes); no elimina ficheros ni cambia la retencion o `AMSAT_REPORT`.
- AMSAT recoge el estado de los satélites en [amsat.org/status](https://www.amsat.org/status/). Cada grabación de SO-50, AO-91, RS-44 o TO-108 genera un **borrador** con los campos del formulario oficial: satélite, fecha, hora y cuarto de hora UTC, indicativo y locator de 6 caracteres.
- `AMSAT_REPORT="no"` (por defecto): en «Grabaciones e informe AMSAT» cada pase tiene un desplegable *Heard / Telemetry Only / Not Heard* (preseleccionado con el detector de FM; en SSB lo eliges tú) y el botón **Enviar a AMSAT**, que abre el formulario oficial ya relleno en otra pestaña.
- `AMSAT_REPORT="auto"`: envía solo los pases marcados como **Heard** por el detector. Los «Not Heard» nunca se envían solos (un falso negativo diría que un satélite en servicio está muerto).
- Para añadir otro satélite pon en `data/satelites.json` su nombre exacto del formulario en `"amsat"` (p. ej. `"SO-50_[FM]"`).
- El paso `satelites` actualiza el catalogo de servicio en
  `/opt/bricohams/kit/data/satelites.json`; ambos servicios leen esa copia.
  Un catalogo antiguo sin el campo `amsat` permite grabar pero no prepara
  los borradores de informe.

## 5. Configuración (`bricohams.env`)
```bash
SATREC_ENABLE="yes"      SATREC_MIN_EL="20"     SATREC_EXCLUIR=""
SATREC_METEOR="yes"      SATREC_DIAS="30"       SATREC_MAX_MB="2000"
ARCHIVO_FILES_ULTIMOS="2" ARCHIVO_MIN_LIBRE_MB="500" ARCHIVO_DIR="/var/lib/bricohams/satelites/archivo"
AMSAT_REPORT="no"        WSPR_CALLSIGN=""
WXRED_ENABLE="yes"       WXRED_RADIO_KM="100"
```
Aplicar: `sudo bash install.sh --solo meteo,satelites,plugins,web`.

## 6. Comprobación
```bash
systemctl status bricohams-wx-red bricohams-satrec --no-pager
systemctl list-timers bricohams-wspr.timer
sudo -u openwebrx bricohams-satrec --plan          # pases que va a grabar
sudo -u openwebrx bricohams-satrec --probar 10     # 10 s del perfil sat|sat2m (cambia el perfil un momento)
sudo -u openwebrx bricohams-wspr --ver             # resumen WSPR sin escribir
journalctl -u bricohams-satrec -n 30 --no-pager
ls -l /var/lib/bricohams/satelites/grabaciones/ /tmp/*.mp3
sudo bricohams-check | grep -Ei 'grab|clima|wspr|lame'
```
Pruebas del repositorio: `tests/test_wx_red.py`, `tests/test_wspr.py`, `tests/test_satrec.py` (ADPCM, plan/ICS, AMSAT, detector FM, Doppler SGP4, websocket falso y MP3) y `tests/test_clima_web.py`.

## 7. Desactivar o restaurar
- Cada parte por separado: `SATREC_ENABLE="no"`, `WXRED_ENABLE="no"` y `sudo bash install.sh --solo meteo,satelites`.
- Parar a mano: `sudo systemctl disable --now bricohams-satrec bricohams-wx-red bricohams-wspr.timer`.
- Las grabaciones no se borran al desactivar: están en `/var/lib/bricohams/satelites/`.

## 8. Problemas detectados, diagnóstico y corrección (archivo de «Files», 2026-10-19)

Instalación en una estación existente, fuera de los pases y con copia previa verificada:
`sudo bash tools/actualizar-archivo-files.sh /ruta/kit-nuevo /ruta/kit-instalado`.
Muestra `BACKUP_VERIFICADO=` y la orden de `RESTAURAR.sh`; restaurar no borra el archivo.
Pruebas: `tests/test_archivo_files.py`.

| # | Problema detectado | Diagnóstico | Corrección |
|---|---|---|---|
| 1 | «Files» se vaciaba solo: OpenWebRX+ borra lo que pasa de `keep_files` (20) y `bricohams-satrec` borraba las grabaciones por días/espacio. No había archivo permanente. | Lectura de `owrx/storage.py` (`cleanStoredFiles`, ordena por `ctime`) y de `limpiar_archivo` en `bricohams-satrec`. | Nueva tarea `bricohams-archivo-files` (cada minuto): copia todo lo de «Files» a `satelites/archivo/AAAA-MM/`, verificado con SHA-256, sin borrado automático. |
| 2 | Se pedía que «Files» mostrara solo los 2 últimos. Bajar `keep_files` a 2 haría que OpenWebRX+ borrase imágenes de SatDump (varias por pase) antes de archivarlas. | Análisis del orden de borrado de OpenWebRX+ frente a la tarea de archivo (intervalo de 1 min). | El recorte a 2 lo hace la tarea **después** de archivar (`ARCHIVO_FILES_ULTIMOS`); `keep_files` sube a 100 como red de seguridad; `SATREC_EN_FILES` pasa de 10 a 2. |
| 3 | Riesgo de perder un fichero que aún se está escribiendo o de sobrescribir otro con el mismo nombre. | Revisión del flujo de SatDump/grabadores, que escriben durante segundos. | Espera de 60 s desde la última modificación; los nombres repetidos con otro contenido se guardan como `nombre~1.ext`. |
| 4 | En la simulación, la tarea terminaba con error cada minuto y no decía por qué. | Contenedor Debian con `systemctl`/`sudo` simulados: un fichero de otro usuario en `/tmp` (bit *sticky*) no se puede borrar (`Operation not permitted`). | Ya no es un error: se anota `AVISO no se puede quitar de Files (ya archivado)` y la tarea sigue. |
| 5 | El primer despliegue terminó con «error (1)» sin indicar en qué paso. | La salida remota no se guardaba. En la simulación, `install` fallaba cuando el kit indicado no tenía `files/bin`; el kit de servicio está en `/opt/bricohams/kit`. | El instalador solo actualiza la copia del kit si existe (si no, avisa). El script de despliegue detecta el kit, numera los pasos (pruebas, sudo, instalación) y guarda un registro en la Pi (`~/bh-archivo-deploy.log`). |
| 6 | En Windows falla la prueba de enlaces simbólicos (`WinError 1314`). | Windows exige privilegios para `os.symlink`. | La prueba se marca `SKIP` donde no se pueden crear enlaces; en Linux (Pi o contenedor) se ejecuta completa. |
| 7 | Un despliegue lanzado desde PowerShell 5.1 termina con código 2 tras `Connection ... closed`. | PowerShell 5.1 no escapa las comillas dobles internas al pasar argumentos a `ssh.exe`, así que la orden remota en línea llega con la sintaxis rota a bash. | No pasar órdenes con comillas como argumento de `ssh`: subir un script con `scp` y ejecutarlo con `ssh -t servidor 'bash ruta/script.sh'`. |
