#!/usr/bin/env python3
"""v5.0: bricohams-wspr (escuchas WSPR reportadas, vía wspr.live) con un servidor HTTP falso."""
import http.server
import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import threading
import urllib.parse

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
PROG = os.path.join(RAIZ, 'files/bin/bricohams-wspr.py')
loader = importlib.machinery.SourceFileLoader('ws', PROG)
spec = importlib.util.spec_from_loader('ws', loader)
w = importlib.util.module_from_spec(spec)
loader.exec_module(w)

assert w.banda(14097100) == '20m' and w.banda(7040100) == '40m' and w.banda(474200) == '630m' and w.banda(1) == '0.000 MHz'
q = w.consulta('DL0XYZ')
assert "rx_sign = 'DL0XYZ'" in q and 'INTERVAL 24 HOUR' in q and q.endswith('FORMAT JSON'), q
for malo in ("X' OR 1=1 --", 'dl0xyz', ''):
    try:
        w.consulta(malo)
        raise AssertionError('consulta aceptó %r' % malo)
    except ValueError:
        pass

FILAS = [{'time': '2026-10-15 13:44:00', 'frequency': 18106100, 'tx_sign': 'G4AAA', 'tx_loc': 'IO90gu', 'distance': 1500, 'azimuth': 10, 'snr': -20, 'power': 23},
         {'time': '2026-10-15 13:40:00', 'frequency': 14097050, 'tx_sign': 'VK2BBB', 'tx_loc': 'QF56', 'distance': 17000, 'azimuth': 80, 'snr': -27, 'power': 37},
         {'time': '2026-10-15 13:30:00', 'frequency': 14097080, 'tx_sign': 'G4AAA', 'tx_loc': 'IO90gu', 'distance': 1500, 'azimuth': 10, 'snr': -18, 'power': 23}]
r = w.resumen(FILAS, 'DL0XYZ', {'reporta': True})
assert r['spots_24h'] == 3 and r['estaciones'] == 2 and r['bandas'] == {'20m': 2, '17m': 1}, r
assert r['mas_lejano']['call'] == 'VK2BBB' and r['ultimos'][0]['t'] == '2026-10-15 13:44:00Z' and r['enlace'].endswith('rx=DL0XYZ'), r
assert w.resumen([], 'DL0XYZ', {})['mas_lejano'] is None

with tempfile.TemporaryDirectory() as d:
    ajustes = os.path.join(d, 'settings.json')
    json.dump({'wsprnet_enabled': False, 'wsprnet_callsign': 'dl0xyz', 'aprs_igate_password': 'NO-SALE'}, open(ajustes, 'w'))
    assert w.ajustes_owrx(ajustes) == {'reporta': False, 'indicativo': 'DL0XYZ'}
    pedidas = []

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            pedidas.append(urllib.parse.unquote(self.path))
            b = json.dumps({'meta': [], 'data': FILAS}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b)

        def log_message(self, *a):
            pass
    srv = http.server.HTTPServer(('127.0.0.1', 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    salida = os.path.join(d, 'meteo', 'wspr.json')
    env = dict(os.environ, OWRX_SETTINGS_FILE=ajustes, WSPR_OUT=salida, CALLSIGN='N0CALL', PYTHONIOENCODING='utf-8',
               WSPR_LIVE_URL='http://127.0.0.1:%d/?query=' % srv.server_address[1])
    p = subprocess.run([sys.executable, PROG], env=env, capture_output=True, text=True, encoding='utf-8', timeout=60)
    assert p.returncode == 0, p.stderr
    assert 'DL0XYZ · 3 escuchas' in p.stdout and 'no tiene activado el reporte' in p.stdout, p.stdout
    j = json.load(open(salida, encoding='utf-8'))
    assert j['reporta'] is False and j['indicativo'] == 'DL0XYZ' and 'NO-SALE' not in open(salida, encoding='utf-8').read(), j
    assert "rx_sign = 'DL0XYZ'" in pedidas[0], pedidas
    os.unlink(ajustes)
    p = subprocess.run([sys.executable, PROG], env=env, capture_output=True, text=True, encoding='utf-8', timeout=60)
    assert p.returncode == 1 and 'sin indicativo' in p.stderr, (p.returncode, p.stderr)
    srv.shutdown()
print('OK test_wspr: bandas, consulta blindada, resumen, solo claves WSPRnet de settings.json y wspr.live falso')
