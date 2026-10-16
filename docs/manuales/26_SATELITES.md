# 26 · Satélites: aviso de próximos pases, ▶ Escuchar con Doppler e imágenes METEOR

<!-- guia-visual:inicio -->
> **Ruta visual:** [Satélites, Doppler y FT2 experimental](../GUIA_VISUAL_MODULOS.md#satelites).
> Consulta allí requisitos, ilustración, cuadro de instalación, comprobaciones y restauración.
> Los comandos de este manual se ejecutan en Bash en la Pi; revisa el backup antes de cambiarla.
<!-- guia-visual:fin -->

## 1. Qué ve el oyente
- **Franja en lo alto de la web:**
  - antes del pase: «🛰️ **SO-50** en 12 min (18:42) · máx 54° · 11 min · 436,795 NFM **[▶ Escuchar]**»;
  - durante el pase: «🔴 EN DIRECTO: ISS · hasta las 19:03».
  - Solo avisa de los pases de más de 15° de elevación.
- **Botón «PASES»** en la barra superior: tabla de los próximos pases (hora, máxima elevación, duración, frecuencia y azimut de entrada→salida), cada uno con su ▶.
- **▶ Escuchar:**
  1. cambia al receptor y perfil de satélites que toca (`sat|sat2m`, `sat|sat70` o `sat|meteor`);
  2. sintoniza la bajada en su modo;
  3. **arranca el seguimiento Doppler** del plugin `doppler` con los mismos elementos orbitales. La frecuencia se corrige cada segundo.
- **Imágenes METEOR-M2-3/M2-4 (LRPT 137,9 MHz):**
  - las decodifica **SatDump** como servicio de fondo de OpenWebRX+ cuando el receptor de satélites está libre;
  - aparecen en el menú **Files** de la web;
  - el instalador baja SatDump de GitHub si `SATDUMP_ENABLE="yes"`.
  - en el waterfall la señal LRPT solo se oye como ruido digital: la imagen no se ve en directo, sale en **Files** al acabar el pase;
  - algunas compilaciones de SatDump 2.x buscan sus plugins solo en `/usr/local/lib/satdump`. Si faltan, el pase se salta sin imagen; el instalador crea el enlace `/usr/local/lib/satdump → /usr/lib/satdump` y `bricohams-check` avisa si no está.

## 2. Cómo se calcula (ADR-31)
- **`bricohams-satpass`**, cada 15 min (temporizador systemd):
  1. descarga los elementos orbitales de **CelesTrak** (formato OMM/JSON) cada 12 h, con copia en `/var/lib/bricohams/tle.json` por si no hay Internet;
  2. propaga con **SGP4** (`python3-sgp4`) las próximas 24 h desde el QTH (`STATION_LAT/LON/ASL`);
  3. escribe `plugins/receiver/satelites/pases.json`.
- **Precisión:** la prueba `tests/test_satpass.py` compara con Skyfield: entrada en horizonte a ±10 s y elevación máxima a ±1°.
- **Lista de satélites:** `data/satelites.json`.

  | Satélite | NORAD | Bajada | Modo | Perfil |
  |---|---|---|---|---|
  | ISS | 25544 | 145,800 | NFM | sat2m |
  | SO-50 | 27607 | 436,795 | NFM | sat70 |
  | AO-91 | 43017 | 145,960 | NFM | sat2m |
  | RS-44 | 44909 | 435,640 | USB | sat70 |
  | TO-108 | 44881 | 145,925 | USB | sat2m |
  | IO-117 GreenCube | 53106 | 435,310 | USB | sat70 |
  | METEOR-M2-3 | 57166 | 137,900 | NFM / LRPT | meteor |
  | METEOR-M2-4 | 59051 | 137,900 | NFM / LRPT | meteor |

  Para añadir uno, pon una línea con su número NORAD, la bajada, el modo y el perfil, y lanza `sudo systemctl start bricohams-satpass`.

## 3. Duplex y transmisión
La estación **solo recibe**. «Autoconfigurar el duplex» aquí significa sintonizar la **bajada** con su Doppler. La subida y el tono de cada satélite van en la nota del marcador y en la tabla del manual 27, para quien vaya a transmitir con su equipo.

## 4. Comprobación
```bash
sudo -u openwebrx bricohams-satpass --ver    # pases de las próximas 24 h
systemctl list-timers bricohams-satpass.timer
command -v satdump && satdump --help | head -3
ls -l /usr/local/lib/satdump                 # enlace a /usr/lib/satdump
```
- **En la web:** pulsa **PASES** y después ▶ en un pase en curso. La frecuencia del receptor debe moverse sola unos pocos kHz durante el pase.
