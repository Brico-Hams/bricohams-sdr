#!/usr/bin/env python3
"""v5.1 · Interfaz web del APRS: la pasarela del RAK (bricohams-rak-aprs) con su API local
(127.0.0.1, mensajes con acuse, baliza, estado completo), el digipeater automático, la lectura del
bootloader UF2, y la página /settings/bricohams/aprs de bricohams-mesh-admin que la usa
(solo con sesión de administrador, CSRF, validación y sin enseñar el passcode)."""
import http.client
import http.server
import importlib.machinery
import importlib.util
import json
import os
import re
import shutil
import tempfile
import threading
import time
from urllib.parse import urlencode

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
BIN = os.path.join(RAIZ, 'files', 'bin')


def cargar(nombre, fichero):
    ldr = importlib.machinery.SourceFileLoader(nombre, os.path.join(BIN, fichero))
    m = importlib.util.module_from_spec(importlib.util.spec_from_loader(nombre, ldr))
    ldr.exec_module(m)
    return m


tmp = tempfile.mkdtemp()
try:
    for k in [k for k in os.environ if k.startswith(('RAK_', 'IGATE_', 'STATION_', 'OWRX_', 'APRS_'))]:
        del os.environ[k]
    os.environ.update({'RAK_CALLSIGN': 'n0call-15', 'IGATE_CALLSIGN': 'N0CALL-10', 'APRS_PASSCODE': '12345',
                       'RAK_TX': 'yes', 'RAK_DIGI': 'auto', 'RAK_DIGI_AUTO_MIN': '60', 'OWRX_MAPA_LORA': 'no',
                       'RAK_OWRX_CHAT': 'no', 'RAK_RUN_DIR': tmp, 'STATION_LAT': '38.08', 'STATION_LON': '-1.26'})
    rak = cargar('rak51', 'bricohams-rak-aprs')

    # ---------------------------------------------------------------- 1. funciones sueltas
    assert rak.digi_auto(4000, 0, 0, 60, 1) == 1 and rak.digi_auto(4000, 0, 3000, 60, 1) == 0
    assert rak.digi_auto(100, 0, 0, 60, 1) == 0, 'al arrancar espera una hora antes de decidir'
    assert rak.visto_en('N0CALL-10>APLRG1,WIDE1-1:!x', 'N0CALL-10')
    assert rak.visto_en('A1BC>APRS,N0CALL-10*,WIDE2-1:>x', 'N0CALL-10')
    assert not rak.visto_en('A1BC>APRS,N0CALL-10,WIDE2-1:>x', 'N0CALL-10'), 'sin * no lo ha repetido'
    assert rak.mensaje_para(':N0CALL-15:hola{AB1}', 'N0CALL-15') == ('hola', 'AB1')
    assert rak.mensaje_para(':N0CALL-1 :hola', 'N0CALL-15') is None and rak.mensaje_para(':BLN1     :x', 'N0CALL-15') is None
    assert rak.linea_mensaje('ea1aaa', 'a|b~c{d' + 'x' * 80, '12') == ':EA1AAA   :abcd' + 'x' * 63 + '{12'
    i = rak.info_uf2('UF2 Bootloader 0.4.3 lib/nrfx (v2.0.0) lib/tinyusb (0.10.1) lib/uf2 (x)\n'
                     'Model: WisBlock RAK4631 Board\nBoard-ID: WisBlock-RAK4631-Board\nDate: Dec  1 2021\n')
    assert i['bootloader'] == '0.4.3' and i['model'] == 'WisBlock RAK4631 Board' and i['board-id'] == 'WisBlock-RAK4631-Board'
    assert rak.json_rak('{"vbat": nan, "t": 21.5}') == {'vbat': None, 't': 21.5}, 'nan del firmware 1.0.0'

    # ---------------------------------------------------------------- 2. Pasarela y API local
    class FalsoAPRSIS:
        sock, enviados = object(), 0

        def __init__(self):
            self.salida, self.entrada = [], []

        def activo(self):
            return True

        def enviar(self, l):
            self.salida.append(l)
            return True

        def lineas(self):
            l, self.entrada = self.entrada, []
            return l

    class FalsoSerie:
        port = '/dev/rak-falso'

        def __init__(self):
            self.escrito = b''

        def write(self, b):
            self.escrito += b

        def flush(self):
            pass

    p = rak.Pasarela()
    p.aprsis, p.ser = FalsoAPRSIS(), FalsoSerie()
    assert p.igate == 'N0CALL-15' and p.digi_otro == 'N0CALL-10' and p.chat is None and p.mqtt is None
    assert p.digi_deseado() == 0, 'digi auto: la primera hora no repite'
    p.inicio -= 3700
    assert p.digi_deseado() == 1, 'el LilyGO lleva una hora sin oírse: el RAK repite'
    srv = rak._Api.arrancar(p, 0)
    assert srv.server_address[0] == '127.0.0.1', 'la API solo escucha en la propia Pi'
    PUERTO = srv.server_address[1]

    def api(ruta, datos=None, metodo=None):
        c = http.client.HTTPConnection('127.0.0.1', PUERTO, timeout=5)
        c.request(metodo or ('POST' if datos is not None else 'GET'), ruta,
                  body=(json.dumps(datos) if isinstance(datos, dict) else datos))
        r = c.getresponse()
        return r.status, json.loads(r.read() or b'{}')

    # paquete oído por RF del otro iGate (posición) y un mensaje para nosotros con id
    trama = rak.tnc2_a_ax25('N0CALL-10>APLRG1,WIDE1-1:!3805.00N/00000.00W>hola')
    p.de_rak(rak.CMD_DATA, trama)
    p.de_rak(rak.CMD_DATA, rak.tnc2_a_ax25('EA5ZZZ-7>APLRT1,WIDE1-1::N0CALL-15:prueba{7'))
    assert p.otro_visto > 0 and p.digi_deseado() == 0, 'el LilyGO se oye: el RAK deja de repetir'
    st, e = api('/estado')
    assert st == 200 and e['indicativo'] == 'N0CALL-15' and 'N0CALL-10' in e['posiciones']
    assert round(e['posiciones']['N0CALL-10']['lat'], 3) == 38.083 and e['config']['callsign'] == 'N0CALL-15'
    assert any(m['de'] == 'EA5ZZZ-7' and m['texto'] == 'prueba' for m in e['mensajes']), e['mensajes']
    assert '12345' not in json.dumps(e), 'el passcode no sale por la API'
    assert 'N0CALL-15>APZBH1,TCPIP*::EA5ZZZ-7 :ack7' in p.aprsis.salida, ('acuse del mensaje recibido', p.aprsis.salida)
    # mensaje saliente y baliza desde la web: van a la cola y los manda el bucle
    assert api('/mensaje', {'a': 'ea1aaa', 'texto': 'hola desde el panel'})[0] == 200
    assert api('/mensaje', {'a': 'NO VALE', 'texto': 'x'})[0] == 400 and api('/mensaje', {'a': 'EA1AAA'})[0] == 400
    assert api('/mensaje', 'no es json')[0] == 400 and api('/nada')[0] == 404 and api('/nada', {})[0] == 404
    assert api('/baliza', {})[0] == 200
    p.ordenes()
    assert any(l.startswith('N0CALL-15>APZBH1,TCPIP*::EA1AAA   :hola desde el panel{') for l in p.aprsis.salida)
    assert b'BH:BEACON' in p.ser.escrito, 'la baliza se pide al RAK por KISS'
    assert b'hola desde el panel' in p.ser.escrito, 'con RAK_TX=yes el mensaje también sale por RF'
    mid = [m for m in p.mensajes if m['a'] == 'EA1AAA'][0]['id']
    p.aprsis.entrada.append('EA1AAA>APRS,TCPIP*,qAC,T2X::N0CALL-15:ack%s' % mid)
    p.de_aprsis(time.time())
    assert [m for m in p.mensajes if m['a'] == 'EA1AAA'][0]['ack'] is True, 'el acuse de EA1AAA marca el mensaje'
    srv.shutdown()

    # ---------------------------------------------------------------- 3. página /settings/bricohams/aprs
    SESION = 'SesionAdmin_1234567890'

    class FalsoOwrx(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            ok = self.path == '/settings' and ('owrx-session=' + SESION) in (self.headers.get('Cookie') or '')
            self.send_response(200 if ok else 403)
            self.send_header('Content-Length', '0')
            self.end_headers()
    owrx = http.server.HTTPServer(('127.0.0.1', 0), FalsoOwrx)
    threading.Thread(target=owrx.serve_forever, daemon=True).start()

    recibido = []

    class FalsaApiRak(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _r(self, cod, d):
            b = json.dumps(d).encode()
            self.send_response(cod)
            self.send_header('Content-Length', str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            self._r(200, {'actualizado': '2026-10-12T10:00:00', 'puerto': '/dev/rak-aprs', 'tx': True,
                          'rak': {'fw': '1.0.1', 'call': 'N0CALL-15', 'radio': 'ok', 'freq': 433775000, 'tx': True},
                          'aprsis': {'conectado': True, 'enviados': 3, 'activo': True},
                          'digi': {'modo': 'auto', 'actual': 0, 'otro': 'N0CALL-10', 'otro_oido': '09:58:00'},
                          'mensajes': [{'hora': '09:59:00', 'de': 'EA5ZZZ-7', 'a': 'N0CALL-15', 'texto': '<b>hola</b>',
                                        'id': '7', 'via': 'RF'}],
                          'posiciones': {'EA5ZZZ-7': {'lat': 38.1, 'lon': -1.3, 'hora': '09:59:00', 't': 1,
                                                      'comentario': 'móvil'}},
                          'oidos': []})

        def do_POST(self):
            d = json.loads(self.rfile.read(int(self.headers.get('Content-Length') or 0)) or b'{}')
            recibido.append((self.path, d))
            self._r(200, {'ok': True})
    falsa = http.server.HTTPServer(('127.0.0.1', 0), FalsaApiRak)
    threading.Thread(target=falsa.serve_forever, daemon=True).start()
    varlib = os.path.join(tmp, 'varlib')
    os.makedirs(varlib)
    json.dump({'bootloader': '0.4.3', 'board-id': 'WisBlock-RAK4631-Board'}, open(os.path.join(varlib, 'rak-bootloader.json'), 'w'))
    open(os.path.join(varlib, 'rak-puesta.txt'), 'w').write('2026-10-12 09:00:00\nOK firmware ya grabado\nFALLO fix del GPS\n')
    etc = os.path.join(tmp, 'etc.env')
    open(etc, 'w').write("APRS_PASSCODE='12345'\nOWRX_MAPA_LORA='no'\n")
    os.environ.update(MESH_ADMIN_OWRX='127.0.0.1:%d' % owrx.server_port, BRICOHAMS_ENV=etc, BRICOHAMS_KIT_ENV='',
                      RAK_API_PUERTO=str(falsa.server_port), RAK_VARLIB=varlib,
                      MESH_URL_CLI=os.path.join(BIN, 'bricohams-mesh-url'))
    M = cargar('mesh_admin51', 'bricohams-mesh-admin')
    M.TRABAJO.lanzar = lambda *a, **k: True
    M.systemctl = lambda *a: 0
    web = M.Servidor(('127.0.0.1', 0), M.Manejador)
    threading.Thread(target=web.serve_forever, daemon=True).start()
    COOKIE = {'Cookie': 'owrx-session=' + SESION, 'Host': 'sdr.ejemplo.org'}
    ORIGEN = dict(COOKIE, Origin='https://sdr.ejemplo.org')

    def pide(metodo, ruta, cuerpo=None, cab=None):
        c = http.client.HTTPConnection('127.0.0.1', web.server_address[1], timeout=10)
        h = dict(cab or {})
        if cuerpo is not None:
            h['Content-Type'] = 'application/x-www-form-urlencoded'
        c.request(metodo, ruta, body=cuerpo, headers=h)
        r = c.getresponse()
        return r.status, dict(r.getheaders()), r.read().decode('utf-8', 'replace')

    APRS = '/settings/bricohams/aprs'
    st, h, _ = pide('GET', APRS)
    assert st == 302 and h['Location'].startswith('/login'), 'sin sesión de admin: al login'
    st, _, pag = pide('GET', APRS, cab=COOKIE)
    assert st == 200 and 'Mensajes APRS' in pag and 'Enviar baliza ahora' in pag and 'EA5ZZZ-7' in pag
    assert '&lt;b&gt;hola&lt;/b&gt;' in pag and '<b>hola</b>' not in pag, 'los mensajes se escapan'
    assert 'modo auto' in pag and 'N0CALL-10 oído a las 09:58:00' in pag and '0.4.3' in pag and 'FALLO fix del GPS' in pag
    assert '38.1000, -1.3000' in pag and '12345' not in pag
    tk = re.search(r'name="csrf" value="([0-9a-f]+)"', pag).group(1)
    st, _, pag = pide('POST', APRS, urlencode({'accion': 'rakmensaje', 'a': 'ea1aaa', 'texto': '  hola   web ', 'csrf': tk}), ORIGEN)
    assert st == 200 and 'en cola' in pag and recibido[-1] == ('/mensaje', {'a': 'EA1AAA', 'texto': 'hola web'}), recibido
    st, _, pag = pide('POST', APRS, urlencode({'accion': 'rakmensaje', 'a': 'NO VALE', 'texto': 'x', 'csrf': tk}), ORIGEN)
    assert 'alert-danger' in pag and len(recibido) == 1, 'indicativo malo: no llega a la API'
    st, _, pag = pide('POST', APRS, urlencode({'accion': 'rakbaliza', 'csrf': tk}), ORIGEN)
    assert 'Baliza pedida' in pag and recibido[-1][0] == '/baliza'
    st, _, pag = pide('POST', APRS, urlencode({'accion': 'rakbaliza', 'csrf': 'malo'}), ORIGEN)
    assert st in (200, 403) and len(recibido) == 2, 'sin CSRF bueno no se hace nada'
    st, _, pag = pide('POST', APRS, urlencode({'accion': 'rakbaliza', 'csrf': tk}), {'Origin': 'https://sdr.ejemplo.org'})
    assert st in (302, 403) and len(recibido) == 2, 'sin sesión no se hace nada'
    falsa.shutdown()
    st, _, pag = pide('POST', APRS, urlencode({'accion': 'rakbaliza', 'csrf': tk}), ORIGEN)
    assert 'no contesta' in pag, 'con el servicio parado lo dice'
    web.shutdown()
    owrx.shutdown()
finally:
    shutil.rmtree(tmp, ignore_errors=True)
print('OK test_v51_aprs_web: API local del RAK (mensajes con acuse, baliza, estado sin passcode), digipeater '
      'automático, bootloader UF2 y página /settings/bricohams/aprs con sesión, CSRF y validación')
