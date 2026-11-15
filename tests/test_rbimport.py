#!/usr/bin/env python3
"""v5.0 · bricohams-owrx-rbimport: importador de repetidores de RepeaterBook.

1) El parcheador añade el import y las rutas en owrx/http.py y el bloque en
   settings/bookmarks.html; es idempotente y --quitar deja todo byte a byte.
2) El módulo (con owrx simulado) convierte repetidores en bookmarks que solo
   llevan la frecuencia de SALIDA (el SDR solo escucha), con subtono «FM»,
   filtra por distrito y asigna subtonos a bookmarks existentes."""
import importlib.machinery
import importlib.util
import os
import sys
import tempfile
import types

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
RUTA = os.path.join(RAIZ, 'files', 'bin', 'bricohams-owrx-rbimport')
MOD = os.path.join(RAIZ, 'files', 'share', 'bricohams-rbimport', 'bricohams_rbimport.py')

HTTP_PY = '''from owrx.controllers.settings.general import GeneralSettingsController
from owrx.controllers.settings.bookmarks import BookmarksController
import logging


class Router(object):
    def __init__(self):
        self.routes = [
            StaticRoute("/settings/general", GeneralSettingsController),
            StaticRoute("/settings/bookmarks", BookmarksController),
            StaticRoute("/settings/bookmarks", BookmarksController, method="POST", options={"action": "new"}),
        ]


def StaticRoute(*a, **k):
    return a
'''

HTML = '''<html>
<body>
<div class="container">
    <div class="buttons">
        <button type="button" class="btn btn-primary bookmark-add">Add</button>
    </div>
</div>
</body>
</html>
'''


def leer(r):
    with open(r, encoding='utf-8', newline='') as f:
        return f.read()


def escribir(r, t):
    with open(r, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def cargar(nombre, ruta):
    cargador = importlib.machinery.SourceFileLoader(nombre, ruta)
    spec = importlib.util.spec_from_loader(nombre, cargador)
    m = importlib.util.module_from_spec(spec)
    cargador.exec_module(m)
    return m


def probar_parche():
    p = cargar('bh_rbi_patch', RUTA)
    with tempfile.TemporaryDirectory() as d:
        http = os.path.join(d, 'http.py')
        html = os.path.join(d, 'bookmarks.html')
        dst = os.path.join(d, 'bricohams_rbimport.py')
        escribir(http, HTTP_PY)
        escribir(html, HTML)
        os.environ.update({'OWRX_HTTP_PY': http, 'OWRX_BOOKMARKS_HTML': html,
                           'OWRX_RBI_DST': dst, 'BH_RBI_SRC': MOD})
        try:
            assert p.main(['-q']) == 0
            t = leer(http)
            compile(t, http, 'exec')
            assert p.IMPORT_PY in t, 'falta el import'
            assert t.count(p.MARCA_PY) == 1 + len(p.RUTAS_PY), 'líneas marcadas inesperadas'
            # las rutas nuevas van antes de la de /settings/bookmarks
            assert t.index(p.MARCA_PY + '\n            StaticRoute("/settings/bookmarks"') > 0
            assert 'aeropuertos' in t and t.count('"action": "aeropuertos"') == 1, 'falta la ruta de aeropuertos'
            h = leer(html)
            assert 'bh-rbi-fuente' in h and 'Aeropuertos de España (OurAirports)' in h and 'bh-rbi-sintonizables' in h
            assert h.count(p.MARCA_INI) == 1 and p.MARCA_FIN in h
            assert h.index('bookmark-add') < h.index(p.MARCA_INI), 'bloque fuera del ancla'
            assert 'NFM' not in h.split(p.MARCA_INI)[1].split(p.MARCA_FIN)[0], 'debe decir FM, no NFM'
            assert leer(dst) == leer(MOD), 'módulo no copiado'
            # idempotente
            t1, h1 = leer(http), leer(html)
            assert p.main(['-q']) == 0
            assert leer(http) == t1 and leer(html) == h1, 'no idempotente'
            # quitar
            assert p.main(['-q', '--quitar']) == 0
            assert leer(http) == HTTP_PY, 'http.py no restaurado'
            assert leer(html) == HTML, 'bookmarks.html no restaurado'
            assert not os.path.exists(dst), 'módulo no eliminado'
            # sin módulo fuente no se toca http.py
            os.environ['BH_RBI_SRC'] = os.path.join(d, 'no-existe.py')
            p.main(['-q'])
            assert leer(http) == HTTP_PY, 'http.py parcheado sin módulo'
            # http.py sin anclas: error controlado, sin cambios
            os.environ['BH_RBI_SRC'] = MOD
            escribir(http, 'x = 1\n')
            assert p.main([]) == 1
            assert leer(http) == 'x = 1\n'
            # html sin ancla: se inserta antes de </body>
            escribir(html, '<html><body></body></html>\n')
            escribir(http, HTTP_PY)
            p.main(['-q'])
            h = leer(html)
            assert h.index(p.MARCA_INI) < h.index('</body>')
            p.main(['-q', '--quitar'])
            assert leer(html) == '<html><body></body></html>\n'
        finally:
            for k in ('OWRX_HTTP_PY', 'OWRX_BOOKMARKS_HTML', 'OWRX_RBI_DST', 'BH_RBI_SRC'):
                os.environ.pop(k, None)


def stub_owrx():
    owrx = types.ModuleType('owrx')
    ctrls = types.ModuleType('owrx.controllers')
    admin = types.ModuleType('owrx.controllers.admin')

    class Controller(object):
        pass

    class AuthorizationMixin(object):
        pass

    ctrls.Controller = Controller
    admin.AuthorizationMixin = AuthorizationMixin
    owrx.controllers = ctrls
    ctrls.admin = admin
    sys.modules.setdefault('owrx', owrx)
    sys.modules.setdefault('owrx.controllers', ctrls)
    sys.modules.setdefault('owrx.controllers.admin', admin)


class BM(object):
    def __init__(self, nombre, f, mod='nfm', ctcss=0):
        self.n, self.f, self.m, self.ctcss = nombre, f, mod, ctcss

    def getName(self):
        return self.n

    def getFrequency(self):
        return self.f

    def getModulation(self):
        return self.m


def probar_modulo():
    stub_owrx()
    m = cargar('bh_rbi_mod', MOD)
    assert m.tono('77') == 77.0 and m.tono('88.50') == 88.5
    assert m.tono('') is None and m.tono('CSQ') is None and m.tono('500') is None

    rb = [
        {'Callsign': 'ED5YAA', 'Frequency': '145.7000', 'Input Freq': '145.1000', 'PL': '88.5', 'TSQ': '',
         'FM Analog': 'Yes', 'Operational Status': 'On-air', 'Region': 'Comunidad Valenciana',
         'Nearest City': 'Alicante'},
        {'Callsign': 'ED5YAU', 'Frequency': '438.7000', 'Input Freq': '431.1000', 'PL': '', 'TSQ': '79.7',
         'FM Analog': 'Yes', 'Operational Status': 'On-air', 'Region': 'Comunidad Valenciana',
         'Nearest City': 'Valencia'},
        {'Callsign': 'ED5ZAB', 'Frequency': '438.4250', 'Input Freq': '430.8250', 'PL': '',
         'FM Analog': 'No', 'Operational Status': 'On-air', 'Region': 'Comunidad Valenciana'},
        {'Callsign': 'ED1ZZZ', 'Frequency': '145.6000', 'Input Freq': '145.0000', 'PL': '123',
         'FM Analog': 'Yes', 'Operational Status': 'On-air', 'Region': 'Galicia'},
        {'Callsign': 'ED5OFF', 'Frequency': '145.6500', 'Input Freq': '145.0500', 'PL': '71.9',
         'FM Analog': 'Yes', 'Operational Status': 'Off-air', 'Region': 'Murcia'},
        {'Callsign': 'ED5HF', 'Frequency': '29.6500', 'PL': '', 'FM Analog': 'Yes',
         'Operational Status': 'On-air', 'Region': 'Murcia'},
    ]

    sel = m.filtrar(rb, distrito='5')
    assert [r['Callsign'] for r in sel] == ['ED5YAA', 'ED5YAU'], sel
    assert [r['Callsign'] for r in m.filtrar(rb, distrito='5', solo_activos=False)] == ['ED5YAA', 'ED5YAU', 'ED5OFF']
    assert [r['Callsign'] for r in m.filtrar(rb, distrito='1')] == ['ED1ZZZ']
    assert [r['Callsign'] for r in m.filtrar(rb, distrito='5', texto='valencia')] == ['ED5YAA', 'ED5YAU']
    assert [r['Callsign'] for r in m.filtrar(rb, distrito='5', bandas=('10m',))] == ['ED5HF']
    assert m.filtrar(rb, distrito='5', bandas=('23cm',)) == []

    b, info = m.a_bookmark(rb[0])
    assert b['frequency'] == 145700000, 'debe ser la frecuencia de SALIDA'
    assert b['modulation'] == 'nfm' and b['ctcss'] == 88.5
    assert 'subtono FM 88.5 Hz' in b['description'] and 'NFM' not in b['description']
    assert '145.1000' in b['description'] and info['entrada'] == 145.1
    assert not any(v == 145100000 for v in b.values()), 'la entrada no puede ser una frecuencia del bookmark'
    b2, _ = m.a_bookmark(rb[1])
    assert b2['frequency'] == 438700000 and b2['ctcss'] == 79.7, 'TSQ tiene prioridad'
    b3, _ = m.a_bookmark(dict(rb[0], PL=''))
    assert 'ctcss' not in b3 and 'sin subtono' in b3['description']

    prop = m.proponer(sel + [dict(rb[0])], {145700000: 'existente'})
    assert [p['frequency'] for p in prop] == [145700000, 438700000], 'sin duplicados y ordenado'
    assert prop[0]['existe'] == 'existente' and prop[1]['existe'] is None

    bms = [BM('ED5YAA Alicante', 145700000), BM('Rep 70cm', 438700000), BM('FM radio', 100000000, 'wfm'),
           BM('Ya tiene', 145600000, ctcss=67.0)]
    cambios = m.asignar_tonos(bms, rb, distrito='5')
    assert {c['name']: c['ctcss'] for c in cambios} == {'ED5YAA Alicante': 88.5, 'Rep 70cm': 79.7}, cambios
    assert bms[0].ctcss == 88.5 and bms[2].ctcss == 0 and bms[3].ctcss == 67.0
    cambios = m.asignar_tonos([BM('Ya tiene', 145600000, ctcss=67.0)], rb, sobrescribir=True)
    assert cambios and cambios[0]['ctcss'] == 123.0 and cambios[0]['antes'] == 67.0

    # sin coincidencia de indicativo y con subtonos distintos -> no se asigna
    dup = [dict(rb[0], Callsign='ED5AAA', PL='88.5'), dict(rb[0], Callsign='ED5BBB', PL='100')]
    assert m.elegir_tono('Otro', dup, '5') == (None, None)
    assert m.elegir_tono('ED5BBB', dup, '5')[0] == 100.0

    probar_rangos_aeropuertos(m, rb)


class Req(object):
    def __init__(self, **q):
        self.query = {k: [str(v)] for k, v in q.items()}


def llamar(m, accion, **q):
    ctl = m.RepeaterBookImportController()
    ctl.request = Req(**q)
    salida = []
    ctl.send_response = lambda cuerpo, code=200, **k: salida.append((code, __import__('json').loads(cuerpo)))
    getattr(ctl, accion)()
    return salida[0]


def probar_rangos_aeropuertos(m, rb):
    sdrs = {
        'a': {'profiles': {'p1': {'center_freq': 145000000, 'samp_rate': 4000000},
                           'p2': {'center_freq': 146000000, 'samp_rate': 4000000},
                           'p3': {'center_freq': 100000000, 'samp_rate': 2000000}}},
        'b': {'enabled': False, 'profiles': {'p': {'center_freq': 1200000000, 'samp_rate': 2000000}}},
        'c': {'enabled': True, 'profiles': {'p': {'center_freq': 125000000, 'samp_rate': 2000000}}},
    }
    rg = m.rangos_sintonizables(sdrs)
    assert rg == [(99000000, 101000000), (124000000, 126000000), (143000000, 148000000)], rg
    assert m.sintonizable(145700000, rg) and m.sintonizable(126000000, rg)
    assert not m.sintonizable(1200000000, rg) and not m.sintonizable(130000000, rg)
    assert m.rangos_sintonizables({}) == [] and m.rangos_sintonizables(None) == []

    class Capa:
        """Like owrx PropertyLayer: «in», [] and values(), but no .get()."""
        def __init__(self, **kw):
            self.p = kw
        def __contains__(self, k):
            return k in self.p
        def __getitem__(self, k):
            return self.p[k]
        def values(self):
            return self.p.values()
    capa = Capa(a=Capa(profiles=Capa(x=Capa(center_freq=145000000, samp_rate=2000000))),
                b=Capa(enabled=False, profiles=Capa(y=Capa(center_freq=7000000, samp_rate=1000000))))
    assert m.rangos_sintonizables(capa) == [(144000000, 146000000)], m.rangos_sintonizables(capa)

    aero = [
        {'ident': 'LELC', 'name': 'San Javier', 'municipality': 'Murcia', 'iso_region': 'ES-MC'},
        {'ident': 'LEMD', 'name': 'Madrid Barajas', 'municipality': 'Madrid', 'iso_region': 'ES-MD'},
    ]
    fr = [
        {'airport_ident': 'LEMD', 'type': 'TWR', 'description': 'Madrid Torre', 'frequency_mhz': '118.15'},
        {'airport_ident': 'LELC', 'type': 'TWR', 'description': 'San Javier Torre', 'frequency_mhz': '118.7'},
        {'airport_ident': 'LELC', 'type': 'TWR', 'description': 'repetida', 'frequency_mhz': '118.700'},
        {'airport_ident': 'LELC', 'type': 'ATIS', 'description': '', 'frequency_mhz': '127.3'},
        {'airport_ident': 'LELC', 'type': 'GND', 'description': 'sin frecuencia', 'frequency_mhz': ''},
        {'airport_ident': 'LELC', 'type': 'APP', 'description': 'cero', 'frequency_mhz': '0'},
        {'airport_ident': 'XXXX', 'type': 'TWR', 'description': 'huérfano', 'frequency_mhz': '120.0'},
    ]
    todos = m.aeropuertos_bookmarks(aero, fr)
    assert [(b['frequency'], b['name']) for b in todos] == [
        (118150000, '✈️ LEMD TWR'), (118700000, '✈️ LELC TWR'), (127300000, '✈️ LELC ATIS')], todos
    b = todos[1]
    assert b['modulation'] == 'am' and b['scannable'] is True
    assert b['description'] == 'OurAirports · San Javier · Murcia · TWR San Javier Torre'
    assert todos[2]['description'] == 'OurAirports · San Javier · Murcia · ATIS'
    assert (b['aeropuerto'], b['municipio'], b['region'], b['tipo']) == ('San Javier', 'Murcia', 'ES-MC', 'TWR')
    assert [x['name'] for x in m.aeropuertos_bookmarks(aero, fr, region='ES-MC')] == ['✈️ LELC TWR', '✈️ LELC ATIS']
    assert [x['name'] for x in m.aeropuertos_bookmarks(aero, fr, texto='BARAJAS')] == ['✈️ LEMD TWR']
    assert m.aeropuertos_bookmarks(aero, fr, region='ES-GA') == []
    assert len(m.REGIONES_ES) == 19 and m.REGIONES_ES['ES-MC'] == 'Región de Murcia'

    # acciones: oculta lo no sintonizable e informa de «ocultos»
    m._ocupadas = lambda: {118700000: 'Ya está'}
    m.descargar = lambda *a, **k: rb
    m._config = lambda: 'clave'
    m.descargar_aeropuertos = lambda refrescar=False: (aero, fr)
    m._rangos = lambda: [(118000000, 119000000), (145000000, 146000000)]
    code, d = llamar(m, 'aeropuertosAction', region='ES-MC', solo_sintonizables='1')
    assert code == 200 and d['ok'] and [x['frequency'] for x in d['aeropuertos']] == [118700000]
    assert d['ocultos'] == 1 and d['total'] == 1 and d['rangos'] == [[118000000, 119000000], [145000000, 146000000]]
    assert d['aeropuertos'][0]['sintonizable'] is True and d['aeropuertos'][0]['existe'] == 'Ya está'
    assert d['regiones']['ES-MD'] == 'Comunidad de Madrid'
    code, d = llamar(m, 'aeropuertosAction', region='ES-MC', solo_sintonizables='0')
    assert d['total'] == 2 and d['ocultos'] == 0
    assert [x['sintonizable'] for x in d['aeropuertos']] == [True, False]
    assert llamar(m, 'aeropuertosAction', region='es-mc')[0] == 400
    assert llamar(m, 'aeropuertosAction', texto='x' * 61)[0] == 400

    code, d = llamar(m, 'indexAction', distrito='5', solo_sintonizables='1')
    assert [r['frequency'] for r in d['repetidores']] == [145700000] and d['ocultos'] == 1
    assert d['rangos'] == [[118000000, 119000000], [145000000, 146000000]]
    code, d = llamar(m, 'indexAction', distrito='5', solo_sintonizables='0')
    assert d['total'] == 2 and d['ocultos'] == 0
    m._rangos = lambda: []
    for acc in ('indexAction', 'aeropuertosAction'):
        code, d = llamar(m, acc, distrito='5', solo_sintonizables='1')
        assert d['ocultos'] == 0 and d['total'] >= 2 and d['rangos'] == []

    def falla(refrescar=False):
        raise m.AeropuertosError('sin red')
    m.descargar_aeropuertos = falla
    assert llamar(m, 'aeropuertosAction')[0] == 502


if __name__ == '__main__':
    probar_parche()
    probar_modulo()
    print('OK test_rbimport')
