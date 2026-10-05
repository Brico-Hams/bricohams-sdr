# data/locator · catálogo de zona de España (v4.3)

Lo usa el instalador con `STATION_LOCATOR` / `LOCATOR_CATALOG` para elegir los aeropuertos, estaciones AEMET, puertos y otras frecuencias más cercanos (manual 32, ADR-43).

| Fichero | Qué es | Fuente y licencia |
|---|---|---|
| `catalogo_es.json` | **Generado** con `python3 tools/locator_catalogo.py`. No lo edites a mano | — |
| `fuentes/ourairports_es_aeropuertos.csv` | aeropuertos de España con alguna frecuencia publicada | [OurAirports](https://ourairports.com/data/), dominio público. Se refresca con `tools/locator_catalogo.py --bajar-ourairports` |
| `fuentes/ourairports_es_frecuencias.csv` | sus frecuencias. Los canales de 8,33 kHz se convierten a la frecuencia real en el catálogo | OurAirports, dominio público |
| `fuentes/aemet_estaciones.csv` | 150 estaciones de observación (indicativo AEMET) | Indicativos validados con la lista de estaciones convencionales de AEMET OpenData. Coordenadas de OurAirports (estaciones de aeropuerto) o aproximadas, del centro urbano (`aprox`). En la Pi, con `AEMET_API_KEY`, se usa la lista completa con coordenadas exactas |
| `fuentes/puertos_es.csv` | puertos de interés general (Puertos del Estado) y algunos deportivos, con los canales VHF habituales | coordenadas aproximadas del puerto. Canales según ITU-R M.1084: 16 socorro, 12/14 operaciones portuarias, 9 deportivos |
| `fuentes/otros_es.csv` | NAVTEX de España (518 kHz internacional y 490 kHz nacional) con su alcance | Salvamento Marítimo; lista de estaciones NAVTEX (NAVAREA II y III) |

Las **emisoras de FM** no van en el kit: cambian a menudo. La Pi las baja al instalar de maps.fmdx.org (datos de la comunidad FMLIST), con `LOCATOR_ONLINE=fmdx`.

## Añadir o corregir
1. Edita el CSV de `fuentes/` (una fila por sitio).
2. Regenera: `python3 tools/locator_catalogo.py`.
3. Prueba: `python3 tests/test_locator_es.py`. Comprueba toda España: aeropuerto y AEMET en cada punto y canal 16 en la costa.
4. Comprueba que el catálogo está al día: `python3 tools/locator_catalogo.py --comprobar` (lo hace `run_tests.sh`).
