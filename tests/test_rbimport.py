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
            h = leer(html)
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


if __name__ == '__main__':
    probar_parche()
    probar_modulo()
    print('OK test_rbimport')
