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
2. Corrige el **Doppler con SGP4** cada 2 s (los mismos elementos orbitales de CelesTrak).
3. Decodifica el audio (ADPCM, igual que el navegador) a WAV de 12 kHz y, al acabar, lo pasa a **MP3** (`lame`, 32 kbps mono).
4. En NFM estima si **se oyó el satélite**: compara el ruido de los primeros segundos (antes del AOS) con el del pase; si el silenciador de FM se cierra lo bastante tiempo, lo marca como «oído».
5. Guarda la grabación en `/var/lib/bricohams/satelites/grabaciones/` (se borran las de más de `SATREC_DIAS` días o cuando pasan de `SATREC_MAX_MB`).
6. Enlaza las **10 últimas** en `/tmp` con el nombre que acepta OpenWebRX+ (`SO50-261017-082700-436795.mp3`), así salen en el menú **Files** del receptor y en la página «Clima en red» con reproductor y descarga.

> **Importante:** durante el pase el grabador ocupa el SDR de satélites con ese perfil, igual que lo haría un oyente. Los oyentes que estén en otro perfil de ese mismo SDR verán el cambio. Si no lo quieres, `SATREC_ENABLE="no"`.
> **IO-117 (435,310 MHz)** queda fuera de la banda del perfil `sat70` (centro 436,7 MHz, 2,4 MS/s): el grabador no lo intenta y lo anota como error de frecuencia. Para grabarlo, crea un perfil centrado más abajo.

### Calendario
`/static/plugins/receiver/satelites/pases.ics` (enlace «📅 Pases en tu calendario» en la página): todos los pases planificados con aviso 5 min antes. Se puede suscribir desde Google Calendar, Outlook o el móvil.

## 4. Informe a AMSAT
- AMSAT recoge el estado de los satélites en [amsat.org/status](https://www.amsat.org/status/). Cada grabación de SO-50, AO-91, RS-44 o TO-108 genera un **borrador** con los campos del formulario oficial: satélite, fecha, hora y cuarto de hora UTC, indicativo y locator de 6 caracteres.
- `AMSAT_REPORT="no"` (por defecto): en «Grabaciones e informe AMSAT» cada pase tiene un desplegable *Heard / Telemetry Only / Not Heard* (preseleccionado con el detector de FM; en SSB lo eliges tú) y el botón **Enviar a AMSAT**, que abre el formulario oficial ya relleno en otra pestaña.
- `AMSAT_REPORT="auto"`: envía solo los pases marcados como **Heard** por el detector. Los «Not Heard» nunca se envían solos (un falso negativo diría que un satélite en servicio está muerto).
- Para añadir otro satélite pon en `data/satelites.json` su nombre exacto del formulario en `"amsat"` (p. ej. `"SO-50_[FM]"`).

## 5. Configuración (`bricohams.env`)
```bash
SATREC_ENABLE="yes"      SATREC_MIN_EL="20"     SATREC_EXCLUIR=""
SATREC_METEOR="yes"      SATREC_DIAS="30"       SATREC_MAX_MB="2000"
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
