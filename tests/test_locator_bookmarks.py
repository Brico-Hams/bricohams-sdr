#!/usr/bin/env python3
"""Locator conversion and geographic bookmark selection from a curated catalog."""
import os
import sys

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(RAIZ, 'files', 'bin'))
from bricohams_locator import locator_to_latlon
from bricohams_locator_bookmarks import bookmarks, merge_bookmarks, meteo_stations, seleccionar


assert locator_to_latlon('IM98') == (38.5, -1.0)
assert locator_to_latlon('IM98iu') == (38.854167, -1.291667)
for invalid in ('IM9', 'ZZ99', 'IM9AIU'):
    try:
        locator_to_latlon(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError('locator inválido aceptado: %s' % invalid)

catalog = [
    {'category': 'airport', 'site_id': 'AIR1', 'name': 'Aeropuerto prueba', 'lat': 38.5, 'lon': -1.0,
     'frequency_hz': 121330000, 'modulation': 'am', 'source': 'CATÁLOGO DE PRUEBA'},
    {'category': 'airport', 'site_id': 'AIR1', 'name': 'Aeropuerto prueba TWR', 'lat': 38.5, 'lon': -1.0,
     'frequency_hz': 121700000, 'modulation': 'am'},
    {'category': 'weather', 'site_id': 'MET1', 'station_id': 'MET1', 'name': 'Meteo prueba', 'lat': 38.6, 'lon': -1.0},
    {'category': 'port', 'site_id': 'PORT1', 'name': 'Puerto prueba', 'lat': 37.8, 'lon': -1.0,
     'frequency_hz': 156800000, 'modulation': 'nfm'},
    {'category': 'radio', 'site_id': 'FM1', 'name': 'Radio prueba', 'lat': 38.5, 'lon': -1.0,
     'frequency_hz': 97500000, 'modulation': 'wfm'},
    {'category': 'radio', 'site_id': 'FAR', 'name': 'Emisora lejana', 'lat': 41.0, 'lon': 2.0,
     'frequency_hz': 100000000, 'modulation': 'wfm'},
]
lat, lon, nearby = seleccionar('IM98', catalog, radio_km=100, max_sitios=1)
assert (lat, lon) == (38.5, -1.0)
assert len(nearby) == 5, nearby
assert meteo_stations(nearby) == 'MET1:Meteo prueba'
generated = bookmarks(nearby, 'IM98')
assert {b['frequency'] for b in generated} == {121330000, 121700000, 156800000, 97500000}
assert all('[AUTO-LOCATOR]' in b['description'] for b in generated)
existing = [{'name': 'Mío', 'frequency': 123000000, 'modulation': 'am'},
            {'name': 'Viejo automático', 'frequency': 97500000, 'modulation': 'wfm',
             'description': '[AUTO-LOCATOR] antiguo'}]
merged = merge_bookmarks(existing, generated)
assert [b['name'] for b in merged if b['frequency'] == 123000000] == ['Mío']
assert len([b for b in merged if b['frequency'] == 97500000]) == 1
assert len(merge_bookmarks(merged, generated)) == len(merged)
print('OK test_locator_bookmarks: Maidenhead, radio de búsqueda, sitios más cercanos, meteo y merge idempotente')