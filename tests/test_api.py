#!/usr/bin/env python3
"""v4: bricohams-api (ficha de indicativos) con RadioID y QRZ simulados."""
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
    if 'EA5KAO' in url:
        return {'count': 1, 'results': [{'callsign': 'EA5KAO', 'fname': 'Anatol', 'surname': '', 'city': 'Mi QTH',
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
d = api.buscar_indicativo('ea5kao', cache, sin_qrz, rid=lambda c: api.radioid(c, get=rid_falso))
assert d['nombre'] == 'Anatol' and d['ciudad'] == 'Mi QTH' and d['fuente'] == 'RadioID' and d['foto'] == '', d
n = len(llamadas)
assert api.buscar_indicativo('EA5KAO', cache, sin_qrz, rid=lambda c: api.radioid(c, get=rid_falso)) == d
assert len(llamadas) == n, 'la segunda consulta sale de la caché'

qrz = api.Qrz('usuario', 'clave', get=qrz_get)
d2 = api.buscar_indicativo('EA5KGV/P', cache, qrz, rid=lambda c: api.radioid(c, get=rid_falso))
assert d2['call'] == 'EA5KGV' and d2['nombre'] == 'Pepe García' and d2['foto'].endswith('x.jpg') and d2['fuente'] == 'QRZ', d2
assert api.buscar_indicativo('<script>', cache, qrz) is None and api.buscar_indicativo('12345', cache, qrz) is None
print('OK test_api: RadioID, QRZ XML (con foto), caché y validación del indicativo')
