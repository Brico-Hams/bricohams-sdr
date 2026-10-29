#!/usr/bin/env python3
"""Ficha de mapa desde map.flights y selector en General Settings."""
import importlib.machinery
import importlib.util
import json
import os
import tempfile

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
loader = importlib.machinery.SourceFileLoader(
    'api', os.path.join(RAIZ, 'files/bin/bricohams-api.py'))
spec = importlib.util.spec_from_loader('api', loader)
api = importlib.util.module_from_spec(spec)
loader.exec_module(api)

consultas = []


def map_flights(url):
    consultas.append(url)
    if url.endswith('/471d66'):
        return {
            'typeName': 'AIRBUS A-321neo',
            'typecode': 'A21N',
            'registration': 'HA-LDM',
            'operator': {'name': 'Wizz Air'},
            'route': {
                'origin': {'icao': 'LROP', 'iata': 'OTP', 'municipality': 'Otopeni',
                           'country': 'RO', 'lat': 44.571792, 'lon': 26.103285},
                'dest': {'icao': 'LEXJ', 'iata': 'SDR', 'municipality': 'Santander',
                         'country': 'ES', 'lat': 43.427101, 'lon': -3.82001},
                'airlineIcao': 'WMT',
            },
            'photo': {
                'thumbnail': 'https://t.plnspttrs.net/plane_t.jpg',
                'url': 'https://t.plnspttrs.net/plane.jpg',
                'link': 'https://www.planespotters.net/photo/1',
                'photographer': 'Aviador',
            },
        }
    return {}


ficha = api.ficha_avion('471d66', 'WMT5QD', pedir=map_flights)
assert consultas == ['https://map.flights/api/v1/aircraft/471d66'], consultas
assert ficha['modelo'] == 'AIRBUS A-321neo' and ficha['matricula'] == 'HA-LDM', ficha
assert ficha['operador'] == 'Wizz Air' and ficha['aerolinea'] == 'WMT', ficha
assert ficha['origen'] == 'Otopeni (OTP), RO' and ficha['destino'] == 'Santander (SDR), ES', ficha
assert ficha['pOrigen'] == [44.571792, 26.103285]
assert ficha['pDestino'] == [43.427101, -3.82001]
assert ficha['foto'] == 'https://t.plnspttrs.net/plane_t.jpg'
assert ficha['enlace'] == 'https://www.planespotters.net/photo/1'
assert ficha['fuente'] == 'MAP.FLIGHTS'
assert ficha['credito'] == '© Aviador · Planespotters.net', ficha


# map.flights entrega sus propias fotos con ruta relativa y licencia: no debe caer a Planespotters
def foto_relativa(url):
    if 'map.flights' in url:
        return {'typeName': 'BOEING 737-800', 'registration': 'EC-ABC',
                'photo': {'url': '/photos/ext_4ca703_640.webp', 'thumbnail': '/photos/ext_4ca703_320.webp',
                          'photographer': 'Autora', 'source': 'wikimedia', 'license': 'CC BY 2.0',
                          'licenseUrl': 'https://creativecommons.org/licenses/by/2.0'}}
    raise AssertionError('no debe consultar otras fuentes de foto: ' + url)


rel = api.ficha_avion('4ca703', pedir=lambda u: foto_relativa(u) if 'map.flights' in u else {})
assert rel['foto'] == 'https://map.flights/photos/ext_4ca703_320.webp', rel
assert rel['enlace'] == 'https://map.flights/photos/ext_4ca703_640.webp', rel
assert rel['credito'] == '© Autora · Wikimedia Commons · CC BY 2.0', rel
assert 'Planespotters' not in rel['credito']
assert api._url_mapflights('//evil.example/x.jpg') == '//evil.example/x.jpg'
assert api._https(api._url_mapflights('//evil.example/x.jpg')) == ''


def respuesta_parcial(url):
    if 'map.flights' in url:
        return {'photo': {'thumbnail': 'javascript:alert(1)'},
                'route': {'dest': {'lat': 'nan', 'lon': 999}}}
    return {}


parcial = api.ficha_avion('471d66', pedir=respuesta_parcial)
assert parcial is None, parcial

cabeceras_vistas = []


def con_clave(url, cabeceras=None):
    cabeceras_vistas.append((url, cabeceras))
    if cabeceras:
        raise OSError('HTTP Error 401: Unauthorized')
    return map_flights(url)


consultas.clear()
ficha_clave = api.ficha_avion('471d66', 'WMT5QD', pedir=con_clave, clave_mapflights='mf_api_ABCdef123456')
assert cabeceras_vistas[0] == ('https://map.flights/api/v1/aircraft/471d66',
                               {'x-api-key': 'mf_api_ABCdef123456'}), cabeceras_vistas
assert cabeceras_vistas[1] == ('https://map.flights/api/v1/aircraft/471d66', None), cabeceras_vistas
assert ficha_clave['fuente'] == 'MAP.FLIGHTS' and 'mf_api' not in json.dumps(ficha_clave)
cabeceras_vistas.clear()
api.ficha_avion('471d66', pedir=con_clave, clave_mapflights='mala\r\nX-Inyectada: 1')
assert all(c is None for _, c in cabeceras_vistas), cabeceras_vistas

with tempfile.TemporaryDirectory() as directorio:
    ajustes = os.path.join(directorio, 'settings.json')
    assert api.mapflights_habilitado(ajustes) is False
    assert api.mapflights_config(ajustes) == (False, '')
    with open(ajustes, 'w', encoding='utf-8') as f:
        json.dump({'mapflights_api_enabled': True}, f)
    assert api.mapflights_habilitado(ajustes) is True
    assert api.mapflights_config(ajustes) == (True, '')
    with open(ajustes, 'w', encoding='utf-8') as f:
        json.dump({'mapflights_api_enabled': True, 'mapflights_api_key': '  mf_api_ABCdef123456 '}, f)
    assert api.mapflights_config(ajustes) == (True, 'mf_api_ABCdef123456')
    with open(ajustes, 'w', encoding='utf-8') as f:
        json.dump({'mapflights_api_enabled': True, 'mapflights_api_key': 'a b"<x>'}, f)
    assert api.mapflights_config(ajustes) == (True, '')
    with open(ajustes, 'w', encoding='utf-8') as f:
        json.dump({'mapflights_api_enabled': 'yes'}, f)
    assert api.mapflights_habilitado(ajustes) is False

cache = api.CacheFichas()
respuestas = []
assert cache.obtener('471d66', '', buscar=lambda h, cs: respuestas.append('legacy') or {'origen': 'A'},
                     variante='sin-mapflights') == {'origen': 'A'}
assert cache.obtener('471d66', '', buscar=lambda h, cs: respuestas.append('map') or {'origen': 'B'},
                     variante='mapflights') == {'origen': 'B'}
assert respuestas == ['legacy', 'map'], respuestas

parche = os.path.join(RAIZ, 'files/bin/bricohams-owrx-mapflights')
install = open(os.path.join(RAIZ, 'install.sh'), encoding='utf-8').read()
assert 'envl OWRX_SETTINGS_FILE "$OWRX_DATA/settings.json"' in install
assert '99bricohams-owrx-mapflights' in install and 'bricohams-owrx-mapflights -q' in install
assert 'test_mapflights_api.py' in open(os.path.join(RAIZ, 'tests/run_tests.sh'),
                                      encoding='utf-8').read()
PY = '''from owrx.form.input import (
    CheckboxInput,
    TextInput,
    PasswordInput,
)
from owrx.form.section import Section


class GeneralSettingsController(object):
    def getSections(self):
        return [
            Section(
                "Receiver information",
                TextInput("receiver_admin", "Receiver admin"),
            ),
            Section(
                "Map settings",
                TextInput("map_type", "Map type"),
            ),
        ]
'''

with tempfile.TemporaryDirectory() as directorio:
    archivo = os.path.join(directorio, 'general.py')
    with open(archivo, 'w', encoding='utf-8') as f:
        f.write(PY)
    original_general_py = os.environ.get('OWRX_GENERAL_PY')
    os.environ['OWRX_GENERAL_PY'] = archivo
    parche_loader = importlib.machinery.SourceFileLoader('mapflights_patch', parche)
    parche_spec = importlib.util.spec_from_loader('mapflights_patch', parche_loader)
    parche_mod = importlib.util.module_from_spec(parche_spec)
    parche_loader.exec_module(parche_mod)

    assert parche_mod.main(['-q']) == 0
    aplicado = open(archivo, encoding='utf-8').read()
    compile(aplicado, archivo, 'exec')
    assert aplicado.count('"mapflights_api_enabled"') == 1
    assert aplicado.count('"mapflights_api_key"') == 1 and 'PasswordInput(' in aplicado
    assert 'no API key is required' not in aplicado
    assert aplicado.index('"map.flights"') < aplicado.index('"Map settings"')
    assert parche_mod.main(['-q']) == 0 and open(archivo, encoding='utf-8').read() == aplicado
    assert parche_mod.main(['--quitar', '-q']) == 0 and open(archivo, encoding='utf-8').read() == PY

    nativo = PY.replace('TextInput("map_type", "Map type"),',
                        'CheckboxInput(\n                    "mapflights_api_enabled", "x"),\n'
                        '                TextInput("map_type", "Map type"),')
    with open(archivo, 'w', encoding='utf-8') as f:
        f.write(nativo)
    assert parche_mod.main(['-q']) == 0 and open(archivo, encoding='utf-8').read() == nativo
    with open(archivo, 'w', encoding='utf-8') as f:
        f.write(PY.replace('    PasswordInput,\n', ''))
    assert parche_mod.main([]) == 1
    with open(archivo, 'w', encoding='utf-8') as f:
        f.write('class X: pass\n')
    assert parche_mod.main(['-q']) == 0
    assert parche_mod.main([]) == 1 and open(archivo, encoding='utf-8').read() == 'class X: pass\n'

if original_general_py is None:
    os.environ.pop('OWRX_GENERAL_PY', None)
else:
    os.environ['OWRX_GENERAL_PY'] = original_general_py
live = open(os.path.join(RAIZ, 'files/htdocs/plugins/map/bricohams_live/bricohams_live.js'),
            encoding='utf-8').read()
assert 'Powered by MAP.FLIGHTS' in live and 'https://map.flights/favicon.svg' in live
assert "ficha.fuente === 'MAP.FLIGHTS'" in live
assert 'api.adsbdb.com' not in live and 'api.planespotters.net' not in live
print('OK test_mapflights_api: API oficial primaria, selector admin, fallback seguro y atribución')
