#!/usr/bin/env python3
"""v4: bricohams-api (ficha de indicativos) con HamQTH, RadioID y QRZ simulados."""
import importlib.machinery
import importlib.util
import os
import tempfile

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
loader = importlib.machinery.SourceFileLoader('api', os.path.join(RAIZ, 'files/bin/bricohams-api.py'))
spec = importlib.util.spec_from_loader('api', loader)
api = importlib.util.module_from_spec(spec)
loader.exec_module(api)

llamadas = []


def rid_falso(url):
    llamadas.append(url)
    if 'N0CALL' in url:
        return {'count': 1, 'results': [{'callsign': 'N0CALL', 'fname': 'Operador', 'surname': '', 'city': 'Murcia',
                                         'state': 'Murcia', 'country': 'Spain', 'id': 2145999}]}
    return {'count': 0, 'results': []}


QRZ_LOGIN = '<?xml version="1.0"?><QRZDatabase xmlns="http://xmldata.qrz.com"><Session><Key>abc</Key></Session></QRZDatabase>'
QRZ_OK = ('<?xml version="1.0"?><QRZDatabase xmlns="http://xmldata.qrz.com"><Callsign><call>EA5KGV</call><fname>Pepe</fname>'
          '<name>García</name><addr2>Cartagena</addr2><country>Spain</country><image>https://cdn.qrz.com/x.jpg</image></Callsign>'
          '<Session><Key>abc</Key></Session></QRZDatabase>')


def qrz_get(url):
    llamadas.append(url)
    return QRZ_LOGIN if 'username=' in url else QRZ_OK


cache = api.Cache(os.path.join(tempfile.mkdtemp(), 'c.sqlite'))
sin_qrz = api.Qrz('', '')
d = api.buscar_indicativo('n0call', cache, sin_qrz, rid=lambda c: api.radioid(c, get=rid_falso))
assert d['nombre'] == 'Operador' and d['ciudad'] == 'Murcia' and d['fuente'] == 'RadioID' and d['foto'] == '', d
n = len(llamadas)
assert api.buscar_indicativo('N0CALL', cache, sin_qrz, rid=lambda c: api.radioid(c, get=rid_falso)) == d
assert len(llamadas) == n, 'la segunda consulta sale de la caché'
cache.c.execute('INSERT INTO ind VALUES (?,?,?)', ('EA5OLD', api.time.time(), '{"call":"EA5OLD","fuente":"RadioID"}'))
assert cache.get('EA5OLD') is None, 'invalida entradas antiguas para aplicar la nueva prioridad HamQTH'

qrz = api.Qrz('usuario', 'clave', get=qrz_get)
d2 = api.buscar_indicativo('EA5KGV/P', cache, qrz, rid=lambda c: api.radioid(c, get=rid_falso))
assert d2['call'] == 'EA5KGV' and d2['nombre'] == 'Pepe García' and d2['foto'].endswith('x.jpg') and d2['fuente'] == 'QRZ', d2
assert api.buscar_indicativo('<script>', cache, qrz) is None and api.buscar_indicativo('12345', cache, qrz) is None

hamqth_llamadas = []


def hamqth_post(url, payload):
    hamqth_llamadas.append(('POST', url, payload))
    return {'token': 'ham-token', 'expiresIn': 3600}


def hamqth_get(url, headers):
    hamqth_llamadas.append(('GET', url, headers))
    return {'callsign': 'EA5HAM', 'name': 'Ana Operadora', 'qth': 'Murcia', 'country': 'Spain',
            'region': {'oblast': 'Murcia'}, 'picture': 'https://www.hamqth.com/foto.jpg'}


hamqth = api.HamQTH('EA5HAM', 'secreto', post=hamqth_post, get=hamqth_get)
ham_cache = api.Cache(os.path.join(tempfile.mkdtemp(), 'c.sqlite'))
sin_llamada = len(llamadas)
d3 = api.buscar_indicativo('EA5HAM', ham_cache, qrz, rid=lambda c: api.radioid(c, get=rid_falso), hamqth=hamqth)
assert d3['nombre'] == 'Ana Operadora' and d3['ciudad'] == 'Murcia' and d3['region'] == 'Murcia', d3
assert d3['foto'].endswith('foto.jpg') and d3['fuente'] == 'HamQTH', d3
assert len(hamqth_llamadas) == 2 and hamqth_llamadas[0][0] == 'POST', hamqth_llamadas
assert hamqth_llamadas[0][2] == {'callsign': 'EA5HAM', 'password': 'secreto'}
assert hamqth_llamadas[1][2] == {'Authorization': 'Bearer ham-token'}
assert len(llamadas) == sin_llamada, 'no consulta las fuentes secundarias cuando HamQTH tiene los datos'


def hamqth_incompleto(url, headers):
    return {'name': 'Nombre HamQTH'}


hamqth_parcial = api.HamQTH('EA5HAM', 'secreto', post=hamqth_post, get=hamqth_incompleto)
d4 = api.buscar_indicativo('EA5KGV', ham_cache, qrz, rid=lambda c: api.radioid(c, get=rid_falso),
                           hamqth=hamqth_parcial)
assert d4['nombre'] == 'Nombre HamQTH' and d4['ciudad'] == 'Cartagena', d4
assert d4['foto'].endswith('x.jpg') and d4['fuente'] == 'HamQTH + QRZ', d4
print('OK test_api: HamQTH prioritario, RadioID/QRZ de respaldo, caché y validación del indicativo')
