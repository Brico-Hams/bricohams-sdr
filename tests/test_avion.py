#!/usr/bin/env python3
"""v5.1: ficha de avión (/bricohams/api/avion) con adsbdb y planespotters simulados."""
import importlib.machinery
import importlib.util
import os

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
loader = importlib.machinery.SourceFileLoader('api', os.path.join(RAIZ, 'files/bin/bricohams-api.py'))
spec = importlib.util.spec_from_loader('api', loader)
api = importlib.util.module_from_spec(spec)
loader.exec_module(api)

pedidas = []


def falso(url):
    pedidas.append(url)
    if '/aircraft/' in url:
        return {'response': {'aircraft': {
            'manufacturer': 'Airbus', 'type': 'A320-214', 'icao_type': 'A320', 'registration': 'EC-ABC',
            'registered_owner': 'Vueling', 'url_photo_thumbnail': 'javascript:alert(1)'}}}
    if '/callsign/' in url:
        return {'response': {'flightroute': {
            'airline': {'name': 'Vueling'},
            'origin': {'municipality': 'Barcelona', 'iata_code': 'BCN', 'country_name': 'Spain',
                       'latitude': 41.29, 'longitude': 2.07},
            'destination': {'municipality': 'Sevilla', 'iata_code': 'SVQ', 'country_name': 'Spain',
                            'latitude': 'nan', 'longitude': -5.89}}}}
    if 'planespotters' in url:
        return {'photos': [{'thumbnail_large': {'src': 'https://t.plnspttrs.net/x.jpg'},
                            'link': 'https://www.planespotters.net/photo/1', 'photographer': 'Pepe'}]}
    raise AssertionError(url)


f = api.ficha_avion('~34510A', 'vlg12ab', pedir=falso, usar_mapflights=False)
assert f['modelo'] == 'Airbus A320-214 (A320)' and f['matricula'] == 'EC-ABC', f
assert f['foto'] == 'https://t.plnspttrs.net/x.jpg' and f['credito'].startswith('© Pepe'), f
assert f['origen'] == 'Barcelona (BCN), Spain' and f['destino'] == 'Sevilla (SVQ), Spain', f
assert f['pOrigen'] == [41.29, 2.07] and 'pDestino' not in f, 'coordenadas no válidas descartadas'
assert any('?callsign=VLG12AB' in u for u in pedidas) and any('/callsign/VLG12AB' in u for u in pedidas)

assert api.ficha_avion('zzzzzz', '', pedir=falso, usar_mapflights=False) is None
assert api.ficha_avion('34510a', 'x;rm', pedir=lambda u: (_ for _ in ()).throw(OSError('sin red')),
                       usar_mapflights=False) is None

c = api.CacheFichas()
n = []
assert c.obtener('34510a', 'VLG', buscar=lambda h, s: n.append(1) or {'modelo': 'X'}) == {'modelo': 'X'}
assert c.obtener('34510A', 'vlg', buscar=lambda h, s: n.append(1) or {}) == {'modelo': 'X'} and len(n) == 1
assert c.obtener('aaaaaa', '', buscar=lambda h, s: None) is None
assert c.d['aaaaaa|'][0] < c.d['34510a|VLG'][0] - c.ttl + 601, 'los vacíos caducan a los 10 min'
print('OK test_avion: ficha de avión saneada, ruta, foto y caché')
