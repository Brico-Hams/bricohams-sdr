#!/usr/bin/env python3
"""v5.0: bricohams-wx-red (tiempo de otras estaciones por APRS-IS) con un servidor APRS-IS falso."""
import importlib.machinery
import importlib.util
import json
import os
import socket
import tempfile
import threading
import time

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
loader = importlib.machinery.SourceFileLoader('wxr', os.path.join(RAIZ, 'files/bin/bricohams-wx-red.py'))
spec = importlib.util.spec_from_loader('wxr', loader)
w = importlib.util.module_from_spec(spec)
loader.exec_module(w)

# --- tramas -----------------------------------------------------------
p = w.analizar('EA1AAA-13>APRS,TCPIP*,qAC,T2SPAIN:!3800.00N/00100.00W_220/004g005t077r001p010P020h50b10132L456Test WX')
assert p['call'] == 'EA1AAA-13' and abs(p['lat'] - 38.0) < 1e-6 and abs(p['lon'] + 1.0) < 1e-6, p
x = p['wx']
assert x['temp_c'] == 25.0 and x['hum'] == 50 and x['pres_hpa'] == 1013.2 and x['dir'] == 220, x
assert x['viento_kmh'] == 6.4 and x['racha_kmh'] == 8.0 and x['lluvia_1h_mm'] == 0.3 and x['lum_wm2'] == 456, x
assert p['comentario'] == 'Test WX', p

p = w.analizar('EA1AAA-13>APRS,qAR,EA9ZZZ-10:_10090556c220s004g005t-05h00b09900')
assert p['wx']['temp_c'] == -20.6 and p['wx']['hum'] == 100 and p['wx']['pres_hpa'] == 990.0, p
assert 'lat' not in p

p = w.analizar('EA2BBB>APRS,WIDE2-1,qAR,EA9ZZZ-10:@171230z3810.00N/00110.00W_.../...g...t068h..b.....')
assert p['wx'] == {'temp_c': 20.0}, p

# comprimida (ejemplo de APRS 1.01: 49°30' N, 72°45' W) con rumbo/velocidad
p = w.analizar('EA3CCC>APRS,qAR,X:=/5L!!<*e7_7P[g005t077')
assert abs(p['lat'] - 49.5) < 0.01 and abs(p['lon'] + 72.75) < 0.01, p
assert p['wx']['temp_c'] == 25.0 and p['wx']['dir'] == 88, p

assert w.analizar('# aprsc 2.1.14') is None and w.analizar('basura') is None
assert 'wx' not in w.analizar('EA4DDD>APRS,qAR,X:!3800.00N/00100.00W-casa')

# --- distancia, rumbo y vía -------------------------------------------
assert abs(w.distancia_km(38, -1, 39, -1) - 111.2) < 0.2
assert w.rumbo(38, -1, 39, -1) == 0 and w.rumbo(38, -1, 38, 0) == 90
cfg = w.cfg_desde_env({'STATION_LAT': '38.0', 'STATION_LON': '-1.0', 'RAK_CALLSIGN': 'EA9ZZZ-10',
                       'WX_APRS_CALLSIGN': 'EA9ZZZ-13', 'WXRED_OUT': '/dev/null', 'WXRED_RADIO_KM': '50'})
assert w.filtro(cfg) == 'r/38.00/-1.00/50 ' + w.SAT_FILTRO, w.filtro(cfg)
v = lambda l: w.via(w.analizar(l), cfg)
assert v('A>APRS,WIDE2-1,qAR,EA9ZZZ-10:>x') == ('rf', 'EA9ZZZ-10')
assert v('A>APRS,TCPIP*,qAC,T2X:>x') == ('internet', 'T2X')
assert v('A>APRS,RS0ISS*,qAR,EA7XXX:>x') == ('satelite', 'EA7XXX')
assert v('A>APRS,ARISS,qAR,EA7XXX:>x') == ('internet', 'EA7XXX')        # alias sin repetir
assert v('A>APRS,ARISS*,qAo,EA9ZZZ-10:>x') == ('satelite', 'EA9ZZZ-10')

# --- red: posición + WX sin posición, radio, caducidad, propia ----------
r = w.Red(cfg)
t0 = 1_800_000_000
r.meter('EA1AAA-13>APRS,qAR,EA9ZZZ-10:!3810.00N/00100.00W_.../...t050', t0)
r.meter('EA1AAA-13>APRS,qAC,T2X:_10090556c180s010t060', t0 + 60)
r.meter('LEJOS>APRS,qAC,T2X:!4000.00N/00100.00W_.../...t050', t0)
r.meter('EA9ZZZ-13>APRS,qAC,T2X:!3800.10N/00100.00W_.../...t082b10150', t0)
r.meter('EA5SAT>APRSAT,RS0ISS*,qAR,EA7XXX:=3700.00N/00200.00W-ARISS hola', t0)
j = r.json()
calls = [e['call'] for e in j['estaciones']]
assert calls == ['EA9ZZZ-13', 'EA1AAA-13'], calls                 # la propia primero; LEJOS fuera de 50 km
e = j['estaciones'][1]
assert e['via'] == 'rf' and e['wx']['temp_c'] == 15.6 and e['wx']['dir'] == 180 and e['rumbo'] == 0, e
assert 18 < e['dist_km'] < 19, e
assert j['estaciones'][0]['propia'] and j['satelite'][0]['call'] == 'EA5SAT' and j['satelite'][0]['digi'] == 'RS0ISS'
r.caducar(t0 + 4 * 3600)
assert r.json()['estaciones'] == [] and r.json()['satelite'], r.json()

# --- servicio contra un APRS-IS falso -----------------------------------
srv = socket.socket()
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(('127.0.0.1', 0))
srv.listen(1)
login = []


def aprsis():
    c, _ = srv.accept()
    c.sendall(b'# aprsc falso\r\n')
    login.append(c.recv(512).decode())
    c.sendall(b'# logresp N0CALL unverified, server FALSO\r\n'
              b'EA1AAA-13>APRS,TCPIP*,qAC,T2X:!3810.00N/00100.00W_090/002g004t059h80b10200\r\n')
    time.sleep(1.5)
    c.close()


th = threading.Thread(target=aprsis, daemon=True)
th.start()
with tempfile.TemporaryDirectory() as d:
    cfg.update(servidor='127.0.0.1', puerto=srv.getsockname()[1], salida=os.path.join(d, 'wx-red.json'))
    fin = time.time() + 4
    red = w.servicio(cfg, parar=lambda: time.time() > fin or (os.path.exists(cfg['salida']) and not th.is_alive()), cada=0.2)
    j = json.load(open(cfg['salida']))
    assert login and login[0].startswith('user N0CALL pass -1 vers BricoHams-WX') and 'filter r/38.00/-1.00/50' in login[0], login
    assert j['estaciones'][0]['call'] == 'EA1AAA-13' and j['estaciones'][0]['wx']['pres_hpa'] == 1020.0, j
    assert j['estaciones'][0]['via'] == 'internet' and j['qth'] == {'lat': 38.0, 'lon': -1.0}, j
srv.close()
print('OK test_wx_red: tramas WX (texto, sin posición, con hora, comprimidas), vía rf/satélite/internet, radio, caducidad y APRS-IS falso')
