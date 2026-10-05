#!/usr/bin/env python3
# =====================================================================
#  bricohams-api · EA5KAO · BricoHams  (v4)
#  Pequeño servicio HTTP (127.0.0.1:8075, detrás de nginx en /bricohams/api/)
#  para los plugins de la web:
#    GET /bricohams/api/indicativo?call=EA5KAO
#        -> {"call","nombre","ciudad","region","pais","foto","fuente"}
#        Fuentes: HamQTH (principal), RadioID.net y, si hay credenciales de
#        QRZ XML, QRZ como fuente complementaria. Caché de 7 días.
#    GET /bricohams/api/salud  -> {"ok": true}
# =====================================================================
import json
import os
import re
import sqlite3
import sys
import threading
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ESTADO = os.environ.get('STATE_DIRECTORY', '/var/lib/bricohams')
UA = {'User-Agent': 'BricoHams-SDR EA5KAO (+https://t.me/bricohams)'}
CALL_RE = re.compile(r'^[A-Z0-9]{1,3}[0-9][A-Z0-9]{0,4}[A-Z](/[A-Z0-9]{1,4})?$|^[A-Z0-9]{1,4}/[A-Z0-9]{3,7}$')
CACHE_VERSION = 2


def http_json(url, timeout=8):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout))


def http_json_con_cabeceras(url, headers, timeout=8):
    return json.load(urllib.request.urlopen(
        urllib.request.Request(url, headers={**UA, **headers}), timeout=timeout))


def http_json_post(url, datos, timeout=8):
    req = urllib.request.Request(url, data=json.dumps(datos).encode(),
                                 headers={**UA, 'Content-Type': 'application/json'}, method='POST')
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def http_texto(url, timeout=8):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read().decode('utf-8', 'replace')


def radioid(call, get=http_json):
    try:
        d = get('https://radioid.net/api/dmr/user/?' + urllib.parse.urlencode({'callsign': call}))
    except Exception:
        return {}
    r = (d or {}).get('results') or []
    if not r:
        return {}
    x = r[0]
    return {'nombre': ' '.join(p for p in (x.get('fname'), x.get('surname')) if p), 'ciudad': x.get('city') or '',
            'region': x.get('state') or '', 'pais': x.get('country') or '', 'dmrid': x.get('id'), 'fuente': 'RadioID'}


class HamQTH:
    LOGIN_URL = 'https://www.hamqth.com/api/v2/login'
    CALLBOOK_URL = 'https://www.hamqth.com/api/v2/callbook/'

    def __init__(self, usuario, clave, post=http_json_post, get=http_json_con_cabeceras,
                 reloj=time.monotonic):
        self.u, self.p, self.post, self.get, self.reloj = usuario, clave, post, get, reloj
        self.token, self.expira, self.lock = None, 0, threading.Lock()

    def _login(self):
        respuesta = self.post(self.LOGIN_URL, {'callsign': self.u, 'password': self.p})
        self.token = respuesta.get('token')
        self.expira = self.reloj() + max(0, int(respuesta.get('expiresIn', 3600)) - 60)
        return self.token

    def buscar(self, call):
        if not self.u or not self.p:
            return {}
        url = self.CALLBOOK_URL + urllib.parse.quote(call, safe='') + '?app=BricoHams-SDR'   # «app»: estadísticas de HamQTH
        with self.lock:
            try:
                for intento in range(2):
                    if not self.token or self.reloj() >= self.expira:
                        if not self._login():
                            return {}
                    try:
                        d = self.get(url, {'Authorization': 'Bearer ' + self.token})
                    except Exception as e:
                        if intento == 0 and getattr(e, 'code', None) == 401:
                            self.token = None
                            continue
                        return {}
                    address = d.get('address') or {}
                    region = d.get('region') or {}
                    datos = {
                        'nombre': (d.get('name') or d.get('nick') or '').strip(),
                        'ciudad': (address.get('city') or d.get('qth') or '').strip(),
                        'region': (region.get('oblast') or region.get('usState') or region.get('district') or '').strip(),
                        'pais': (d.get('country') or address.get('country') or '').strip(),
                        'foto': d.get('picture') or '',
                        'fuente': 'HamQTH',
                    }
                    return datos if any(datos[k] for k in ('nombre', 'ciudad', 'region', 'pais', 'foto')) else {}
            except Exception:
                self.token = None
        return {}


class Qrz:
    URL = 'https://xmldata.qrz.com/xml/current/'

    def __init__(self, usuario, clave, get=http_texto):
        self.u, self.p, self.get, self.key, self.lock = usuario, clave, get, None, threading.Lock()

    def _xml(self, params):
        t = self.get(self.URL + '?' + ';'.join('%s=%s' % (k, urllib.parse.quote(str(v))) for k, v in params.items()))
        t = re.sub(r'\sxmlns="[^"]+"', '', t, count=1)
        return ET.fromstring(t)

    def _login(self):
        r = self._xml({'username': self.u, 'password': self.p, 'agent': 'bricohams-sdr'})
        self.key = r.findtext('Session/Key')
        return self.key

    def buscar(self, call):
        if not self.u or not self.p:
            return {}
        with self.lock:
            try:
                for _ in range(2):
                    if not self.key and not self._login():
                        return {}
                    r = self._xml({'s': self.key, 'callsign': call})
                    err = r.findtext('Session/Error') or ''
                    if r.find('Callsign') is not None:
                        c = r.find('Callsign')
                        g = lambda k: (c.findtext(k) or '').strip()
                        return {'nombre': ' '.join(p for p in (g('fname'), g('name')) if p), 'ciudad': g('addr2'),
                                'region': g('state'), 'pais': g('country'), 'foto': g('image'), 'fuente': 'QRZ'}
                    if 'Session Timeout' in err or 'Invalid session key' in err:
                        self.key = None
                        continue
                    return {}
            except Exception:
                self.key = None
        return {}


class Cache:
    def __init__(self, ruta, dias=7):
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        self.c = sqlite3.connect(ruta, check_same_thread=False)
        self.c.execute('CREATE TABLE IF NOT EXISTS ind (call TEXT PRIMARY KEY, t REAL, datos TEXT)')
        self.dias, self.lock = dias, threading.Lock()

    def get(self, call):
        with self.lock:
            r = self.c.execute('SELECT t, datos FROM ind WHERE call = ?', (call,)).fetchone()
        if r and time.time() - r[0] < self.dias * 86400:
            guardado = json.loads(r[1])
            if guardado.get('_cache_version') == CACHE_VERSION:
                return guardado['datos']
        return None

    def put(self, call, datos):
        with self.lock:
            guardado = {'_cache_version': CACHE_VERSION, 'datos': datos}
            self.c.execute('INSERT OR REPLACE INTO ind VALUES (?,?,?)',
                           (call, time.time(), json.dumps(guardado, ensure_ascii=False)))
            self.c.commit()


def buscar_indicativo(call, cache, qrz, rid=radioid, hamqth=None):
    call = (call or '').upper().strip()
    base = call.split('/')[0] if '/' in call and len(call.split('/')[0]) > 3 else call
    if not CALL_RE.match(call) and not CALL_RE.match(base):
        return None
    hit = cache.get(base)
    if hit is not None:
        return hit
    d = {'call': base, 'nombre': '', 'ciudad': '', 'region': '', 'pais': '', 'foto': '', 'fuente': ''}
    h = hamqth.buscar(base) if hamqth else {}
    q = qrz.buscar(base) if qrz and (not h.get('nombre') or not h.get('foto')) else {}
    r = rid(base) if any(not (h.get(k) or q.get(k)) for k in ('nombre', 'ciudad', 'pais')) else {}
    for fuente in (r, q, h):
        for k, v in fuente.items():
            if v:
                d[k] = v
    nombres = [f['fuente'] for f in (h, q, r) if f.get('fuente')]
    d['fuente'] = ' + '.join(nombres)
    cache.put(base, d)
    return d


def servidor(host='127.0.0.1', puerto=8075):
    cache = Cache(os.path.join(ESTADO, 'indicativos.sqlite'))
    hamqth = HamQTH(os.environ.get('HAMQTH_USER', ''), os.environ.get('HAMQTH_PASS', ''))
    qrz = Qrz(os.environ.get('QRZ_USER', ''), os.environ.get('QRZ_PASS', ''))

    class H(BaseHTTPRequestHandler):
        def _json(self, code, obj):
            b = json.dumps(obj, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'public, max-age=3600')
            self.send_header('Content-Length', str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            u = urllib.parse.urlparse(self.path)
            if u.path.endswith('/salud'):
                return self._json(200, {'ok': True, 'hamqth': bool(hamqth.u), 'qrz': bool(qrz.u)})
            if u.path.endswith('/indicativo'):
                call = urllib.parse.parse_qs(u.query).get('call', [''])[0]
                d = buscar_indicativo(call, cache, qrz, hamqth=hamqth)
                return self._json(200 if d else 400, d or {'error': 'indicativo no válido'})
            self._json(404, {'error': 'no existe'})

        def log_message(self, *a):
            pass

    print('api: http://%s:%d/bricohams/api/ (HamQTH %s, QRZ %s)' %
          (host, puerto, 'sí' if hamqth.u else 'no', 'sí' if qrz.u else 'no'), flush=True)
    ThreadingHTTPServer((host, puerto), H).serve_forever()


if __name__ == '__main__':
    sys.exit(servidor(os.environ.get('API_HOST', '127.0.0.1'), int(os.environ.get('API_PORT', '8075'))))
