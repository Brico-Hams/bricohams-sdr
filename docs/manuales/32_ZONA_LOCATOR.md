# 32 · Zona de la estación por locator: aeropuertos, AEMET, puertos y FM (v4.3)

![Zona por locator](../esquemas/22_zona_locator.png)

El instalador sabe **dónde está la estación** por su locator Maidenhead (`STATION_LOCATOR`) o por sus coordenadas. Con eso elige, de un catálogo de toda España:

| Qué | De dónde | Qué sale |
|---|---|---|
| **Aeropuertos** y sus frecuencias (TWR, APP, GND, ATIS, AFIS, CTAF…) | OurAirports, dominio público. Los canales de 8,33 kHz se convierten a la frecuencia real: el canal 121,330 se escucha en 121,325 MHz | marcadores en AM |
| **Estaciones meteorológicas de AEMET** | 150 estaciones en el kit. Con `AEMET_API_KEY`, la Pi baja al instalar la lista completa (unas 800) con sus coordenadas exactas | `METEO_STATIONS` del plugin METEO |
| **Puertos** (de interés general y deportivos) | 48 puertos de la península, Baleares, Canarias, Ceuta y Melilla | canales VHF 9, 12, 14 y 16 en NFM. Un canal que se repite en varios puertos sale una sola vez: «⚓ Canal 12 · Vigo / Marín / Vilagarcía» |
| **Otras frecuencias de interés** | NAVTEX de A Coruña, Tarifa, Cabo de la Nao y Las Palmas, en 518 y 490 kHz, con 550 km de alcance | marcadores con el decodificador NAVTEX de OpenWebRX+ |
| **Emisoras de FM regionales y locales** | Se bajan en la Pi al instalar, de maps.fmdx.org (datos de FMLIST, el mismo servicio de FM-DX Webserver) | marcadores en WFM: las que mejor se oyen, una por frecuencia |

Todo lo generado lleva **`[AUTO-LOCATOR]`** en la descripción y la distancia en el nombre (`✈️ LEVX TWR · 7 km`). En cada pasada se quita y se vuelve a poner.

**Vale para cualquier locator de España:**

| Campo | Zona |
|---|---|
| `IN`, `IM`, `JN`, `JM` | península y Baleares |
| `IL` | Canarias |
| `IM75` | Ceuta |
| `IM85` | Melilla |

Fuera de España, avisa y sigue.

## 1. Configuración (bricohams.env)
```bash
STATION_LOCATOR="IM97kx"          # 4, 6, 8 o 10 caracteres
STATION_LAT="0.0"                 # si pones las coordenadas exactas, mandan sobre el locator
STATION_LON="0.0"
LOCATOR_CATALOG="data/locator/catalogo_es.json"   # vacío = desactivado
LOCATOR_RADIUS_KM="100"           # radio de búsqueda
LOCATOR_MAX_SITES="3"             # sitios más cercanos por categoría
LOCATOR_ONLINE="aemet,fmdx"       # "no" = solo el catálogo del kit
LOCATOR_RADIOS="regional,local"   # añade «nacional» si también quieres RNE, SER, COPE…
LOCATOR_RADIOS_MAX="30"
LOCATOR_METEO="yes"               # "no" = conserva tu METEO_STATIONS
LOCATOR_KIT_ZONA_KM="150"
```

**Reglas de las coordenadas:**
- Si `STATION_LAT`/`STATION_LON` están a 0, se usa el **centro** de la cuadrícula del locator. Con 6 caracteres es una celda de unos 9 × 5 km.
- Si las pones, **mandan** (son más precisas). Si no caen dentro del locator, el instalador avisa.
- Sin `STATION_LOCATOR` pero con coordenadas, el locator se calcula solo.

## 2. Procedimiento: primera instalación en cualquier sitio de España
1. Busca tu locator en un mapa de locators de QRZ o con `bricohams-locator locator LAT LON` (paso 4), o deja las coordenadas.
2. Edita `bricohams.env`: `STATION_LOCATOR="IN52pf"` (Vigo, por ejemplo) y tu `AEMET_API_KEY`.
3. Instala como siempre: `sudo bash install.sh`. En el paso **configuracion** verás el informe de la zona:
   ```
   QTH IN52PF · 42.22917, -8.70833 · península
   Aeropuertos (7)
        6.7 km  ✈️ LEVX TWR                118.4500 MHz am
   Estaciones meteorológicas (AEMET) (3)
        0.8 km  Vigo-O Castro             1496X
   …
   ```
4. En el paso **meteo**, `METEO_STATIONS` sale de las estaciones AEMET más cercanas.
5. Comprueba: `sudo bricohams-check` → «zona IN52PF: N marcadores de la zona».

## 3. Procedimiento: cambiar de sitio o de radio
```bash
nano bricohams.env                       # nuevo STATION_LOCATOR o LOCATOR_RADIUS_KM
sudo bash install.sh --solo configuracion,meteo
```
O, sin reinstalar nada, con la herramienta:
```bash
bricohams-locator info                   # qué hay cerca (sin sudo lee /etc/bricohams/zona.env, sin claves)
bricohams-locator info IL18qc            # …o de cualquier otro locator
sudo bricohams-locator refrescar         # vuelve a bajar AEMET y FM (caché de 30 días)
bricohams-locator marcadores             # enseña los que pondría
sudo bricohams-locator marcadores --aplicar   # los pone en OpenWebRX+ y lo reinicia (nativo o Docker)
bricohams-locator meteo                  # la METEO_STATIONS que saldría
bricohams-locator coordenadas IM97kx     # 38.062500 -1.291667
bricohams-locator locator 0.0 0.0   # IM97kx
```

## 4. Qué pasa con los marcadores que ya tienes
| Marcadores | Qué se hace |
|---|---|
| **Los tuyos** (añadidos desde la web) | Nunca se tocan. Si uno tiene la misma frecuencia y modo que uno de la zona, gana el tuyo. |
| **Del kit, en la Región de Murcia** (a menos de `LOCATOR_KIT_ZONA_KM` de Mi QTH) | Se quedan tal cual. Los de la zona se añaden donde no choquen. |
| **Del kit, lejos de Mi QTH** | Se quitan los propios de Murcia: FM y DAB+ de Murcia, aeropuertos de Murcia y Alicante, repetidores y hotspots EA5, Radio Club. Los que solo llevaban el nombre de Murcia vuelven al genérico: «⛵ Canal 12 · Prácticos Cartagena» → «⛵ Canal 12», y «CB 32 · … · Radio Club» → «CB 32». El canal genérico cede su sitio al de los puertos de la zona. |
| **Genéricos** | CB, PMR446, satélites, modos digitales, 121,5, canal 16, AIS: no se tocan. |
| **`[AUTO-LOCATOR]` anteriores** | Se sustituyen. |

## 5. Datos que se bajan en la Pi (LOCATOR_ONLINE)
- **`aemet`:**
  - `GET /opendata/api/observacion/convencional/todas` con tu `AEMET_API_KEY` (la misma de la meteo, nunca va en la línea de órdenes).
  - Guarda indicativo, nombre y coordenadas de las estaciones que dan datos ahora mismo.
  - Sustituye a las 150 del kit.
- **`fmdx`:**
  - `GET https://maps.fmdx.org/api?qth=LAT,LON`: emisores de FM alrededor, de la base de FMLIST.
  - Se quedan los de España (`itu` = `E`) a menos de 150 km.
  - Se clasifican por el nombre:
    - **regional:** À Punt, Onda Regional, Canal Sur, Catalunya Ràdio, Radio Euskadi, Radio Galega, Aragón Radio, CMM, Onda Madrid, Canarias Radio, IB3, RTPA…;
    - **nacional:** RNE, SER, COPE, Onda Cero, Los40, Cadena 100…;
    - **local:** el resto.
  - De cada frecuencia queda la que mejor se oye: potencia / distancia².
- **Caché:** `/var/lib/bricohams/locator/{aemet,fmdx}.json`, 30 días.
  - **Sin red, sin clave o si el servicio cambia:** se avisa y se sigue con la caché o con el catálogo del kit. La instalación **nunca se para** por esto.
  - **Las FM de la caché solo valen si la estación no se ha movido** más de 25 km.

## 6. El catálogo del kit (data/locator)
| Fichero | Contenido |
|---|---|
| `fuentes/ourairports_es_*.csv` | aeropuertos de España con frecuencias (OurAirports) |
| `fuentes/aemet_estaciones.csv` | indicativo, nombre y coordenadas. Indicativos validados con la lista de estaciones convencionales; las coordenadas salen de OurAirports o son aproximadas (centro urbano) |
| `fuentes/puertos_es.csv` | puertos y canales |
| `fuentes/otros_es.csv` | NAVTEX con su alcance |
| `catalogo_es.json` | lo que usa el instalador. Se genera con `python3 tools/locator_catalogo.py` y `--comprobar` lo verifica en `run_tests.sh` |

- **Refrescar los aeropuertos desde OurAirports:** `python3 tools/locator_catalogo.py --bajar-ourairports`.
- **Catálogo propio** (otro país o tus frecuencias): un JSON con `records`. Cada uno lleva `category` (`airport`, `weather`, `port`, `radio`, `other`), `site_id`, `name`, `lat`, `lon` y, salvo `weather`, `frequency_hz` y `modulation`. Además:
  - `weather` lleva `station_id`;
  - `range_km` amplía el alcance de un registro.

  Ponlo en `LOCATOR_CATALOG`.

## 7. Límites (léelos)
- **Frecuencias de aeropuertos:** son las de OurAirports, que mantienen voluntarios. Alguna puede estar desactualizada (las dudosas lo dicen en la descripción). Las que valen son las del AIP de ENAIRE.
- **Canales de puerto:**
  - el 12 y el 14 son los habituales de operaciones portuarias, pero cada puerto publica los suyos;
  - el 16 es socorro y llamada;
  - los boletines de Salvamento Marítimo se anuncian en el 16.
- **FM:** la base de FMLIST la mantiene la comunidad DX. Una emisora pequeña puede faltar o haber cambiado.
- **Comunicaciones privadas:** no se añaden. El catálogo es de servicios de radiodifusión, aeronáuticos y marítimos que se pueden escuchar; escuchar no es divulgar (Ley 11/2022).

Decisiones: ADR-43 (zona por locator) y ADR-46 (datos en línea en la Pi) en [ARQUITECTURA](../ARQUITECTURA.md). Pruebas: `tests/test_locator_es.py` (895 puntos de toda España) y `tests/test_locator_bookmarks.py`.
