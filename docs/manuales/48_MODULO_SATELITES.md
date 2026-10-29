# 48 · Módulo de satélites: instalar y configurar

<!-- guia-visual:inicio -->
> **Ruta visual:** [Satélites, Doppler y FT2 experimental](../GUIA_VISUAL_MODULOS.md#satelites).
> Consulta allí requisitos, ilustración, cuadro de instalación, comprobaciones y restauración.
> Los comandos de este manual se ejecutan en Bash en la Pi; revisa el backup antes de cambiarla.
<!-- guia-visual:fin -->

Guía de un solo módulo: el que muestra en OpenWebRX+ el panel **🛰️ Próximos pases (24 h)**,
la franja con el próximo pase, el botón **PASES** y el **▶** que sintoniza con Doppler. Para el
funcionamiento interno y la grabación consulta los manuales [26](26_SATELITES.md) y
[42](42_CLIMA_RED_SATELITES_GRABACION.md).

## 1. Cómo reconocerlo

| Lo que ves en la web | Pieza que lo hace | Dónde está en el kit |
|---|---|---|
| Panel «Próximos pases (24 h)» con Banda, Desde/Hasta MHz y Filtrar | plugin web `satelites` | `files/htdocs/plugins/receiver/satelites/satelites.js` |
| Columnas Hora, Satélite, Máx, Dura, Bajada, Az | datos `pases.json` | los escribe `bricohams-satpass` cada 15 min |
| Botón **▶**: cambia de perfil, sintoniza y sigue el Doppler | plugins `satelites` + `doppler` | `files/htdocs/plugins/receiver/doppler/` |
| Franja «🛰️ SO-50 en 12 min…» o «🔴 EN DIRECTO» | plugin web `satelites` | mismo fichero |
| Pases grabados en MP3 e imágenes METEOR en **Files** | `bricohams-satrec` y SatDump | `files/bin/bricohams-satrec.py` |
| Lista de satélites | catálogo del kit | `data/satelites.json` |

En el kit de una estación concreta el título puede llevar su localidad («Próximos pases (24 h) · …»);
en el kit genérico solo dice «Próximos pases (24 h)».

## 2. Requisitos

- Raspberry Pi con **OpenWebRX+ nativo** funcionando (`OWRX_BACKEND=native`; con Docker usa la
  instalación completa).
- Hora del sistema correcta (NTP): los pases se calculan con el reloj de la Pi.
- Conexión a Internet para descargar los elementos orbitales (CelesTrak y, si falla, SatNOGS).
  Sin red se usa la última copia de `/var/lib/bricohams/tle.json`; sin elementos no hay pases.
- Para escuchar: un receptor en OpenWebRX+ capaz de 137, 145, 400 y 435 MHz y una antena
  adecuada. Para imágenes METEOR, SatDump (se instala solo con `SATDUMP_ENABLE="yes"`).

## 3. Instalar

Elige una de las dos formas. Las dos se pueden repetir sin romper nada.

**a) Con la estación BricoHams completa** (perfiles `sat|…` incluidos):

```bash
sudo bash install.sh                 # instalación completa, o solo este paso:
sudo bash install.sh --solo satelites
```

**b) Solo este módulo, en otro OpenWebRX+** (no toca receptores, perfiles, otros plugins, nginx ni
el panel de administración):

```bash
cp bricohams.env.example bricohams.env   # y rellénalo (apartado 4)
sudo bash install.sh --modulo satelites
```

En `plugins/receiver/init.js` solo se añade, entre `// >>> bricohams-satelites` y
`// <<< bricohams-satelites`, la carga de `doppler` y `satelites`, con copia previa
`init.js.antes-*`. Si ese `init.js` es el completo de BricoHams, no se modifica.

## 4. Configurar

Todo se ajusta en `bricohams.env` y se aplica repitiendo la orden de instalación del apartado 3.

**Estación (obligatorio):**

| Variable | Qué hace |
|---|---|
| `STATION_LAT`, `STATION_LON` | Posición desde la que se calculan los pases. Mandan sobre el locator. |
| `STATION_LOCATOR` | Locator Maidenhead; se usa si latitud y longitud están a 0. |
| `STATION_ASL` | Altitud en metros (0 si no la sabes). |
| `CALLSIGN` | Indicativo de los informes AMSAT y de las grabaciones. |

**Grabación y agenda de capturas:**

| Variable | Por defecto | Qué hace |
|---|---|---|
| `SATREC_ENABLE` | `yes` | Graba los pases en MP3 (aparecen en **Files**). Ocupa el receptor de satélites durante el pase. |
| `SATREC_MIN_EL` | `20` | Elevación máxima mínima, en grados, para grabar un pase. |
| `SATREC_EXCLUIR` | vacío | Satélites que no se graban, separados por comas (p. ej. `ISS,TO-108`). |
| `SATREC_METEOR` | `yes` | En los pases METEOR pone el perfil `meteor` para que SatDump saque la imagen. |
| `SATREC_DIAS` / `SATREC_MAX_MB` | `30` / `2000` | Días y espacio máximo que se guardan las grabaciones. |
| `AMSAT_REPORT` | `no` | `no`: borrador del informe; `auto`: envía los «Heard» a amsat.org/status. |
| `SATDUMP_ENABLE` | `yes` | Instala SatDump para las imágenes METEOR LRPT. |
| `ARCHIVO_FILES_ULTIMOS` | `2` | Ficheros que quedan en **Files**; el resto se archiva en `ARCHIVO_DIR`. |

**Panel web (opcional):** en `plugins/receiver/init.js`, la línea
`window.satelites_config = { url: 'static/plugins/receiver/satelites/pases.json', min_el: 15 };`
fija la elevación mínima de la franja y de los avisos (15° por defecto). El panel **PASES**
lista todos los pases calculados de las próximas 24 h.

## 5. Añadir o quitar satélites

Edita `data/satelites.json` en el kit y repite la instalación. Cada satélite es un objeto:

```json
{ "norad": 43017, "nombre": "AO-91", "mhz": 145.96, "modo": "nfm", "perfil": "sat|sat2m",
  "nota": "subida 435,250 MHz" }
```

- `norad`: número de catálogo (CelesTrak/SatNOGS). `nombre`: texto del panel.
- `mhz` y `modo` (`nfm` o `usb`): bajada que sintoniza el **▶**.
- `perfil`: `receptor|perfil` de OpenWebRX+ al que cambia el **▶** (`sat|sat2m`, `sat|sat70`,
  `sat|sat400`, `sat|meteor`). Si ese perfil no existe en tu receptor, sintoniza en el perfil actual.
- Opcionales: `min_el` (elevación mínima para calcular sus pases, 10° por defecto) y
  `satnogs_id` (si SatNOGS usa otro identificador).

## 6. Comprobar

```bash
systemctl list-timers bricohams-satpass.timer       # cálculo cada 15 min
sudo -u openwebrx bricohams-satpass --ver           # pases de las próximas 24 h
systemctl status bricohams-satrec --no-pager        # grabación de pases
sudo -u openwebrx bricohams-satrec --plan           # qué pases se van a grabar
```

En la web: recarga el receptor, pulsa **PASES**, filtra por banda o por un rango de MHz (para una
frecuencia exacta, el mismo valor en «Desde» y «Hasta») y pulsa **▶** en un pase en curso. La
frecuencia debe moverse sola unos kHz durante el pase. El filtro solo afecta a la lista, no a las
grabaciones ni a los avisos.

## 7. Si no funciona

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| «Sin pases con estos filtros o sin datos» | Filtro demasiado estrecho o `pases.json` vacío | Quita el filtro; mira `journalctl -u bricohams-satpass.service -n 30`. |
| Horas o pases incorrectos | Reloj o QTH mal | Comprueba NTP y `STATION_LAT/LON`; repite la instalación. |
| No aparece el botón PASES | `init.js` no carga los plugins | Repite `sudo bash install.sh --modulo satelites` y recarga sin caché. |
| ▶ no cambia de perfil | No existe el perfil `sat|…` | Normal en el modo solo módulo: sintoniza en el perfil actual. |
| No hay imágenes METEOR | SatDump ausente o sin plugins | Comprueba `command -v satdump` y `ls -l /usr/local/lib/satdump`. |

Un satélite que no pasa sobre tu QTH en 24 h no es un fallo de la instalación.
