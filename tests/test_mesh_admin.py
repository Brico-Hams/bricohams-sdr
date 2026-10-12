#!/usr/bin/env python3
"""v4.5 · bricohams-mesh-admin: el panel Meshtastic 433/868 solo existe dentro de /settings
(sesión de administrador de OpenWebRX+ comprobada contra OpenWebRX+), con CSRF, sin enseñar
nunca claves ni URLs, y escribiendo bricohams.env sin romper comillas ni comentarios. Además:
nada de Meshtastic configurable en la web pública (ni la web de meshtasticd en 9443)."""
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
from urllib.parse import urlencode

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
BIN = os.path.join(RAIZ, 'files', 'bin')
SESION = 'SesionAdmin_1234567890'
tmp = tempfile.mkdtemp()
try:
    ej = open(os.path.join(RAIZ, 'bricohams.env.example'), encoding='utf-8').read()
    urls = dict(re.findall(r'^(MESH_CHANNEL_URL|MESH433_CHANNEL_URL)="([^"]+)"', ej, re.M))
    kit = os.path.join(tmp, 'kit.env')
    etc = os.path.join(tmp, 'etc.env')
    with open(kit, 'w', encoding='utf-8') as f:
        f.write('# kit\nMESH433_LONG_NAME="Viejo 433"        # nombre largo\nMESH433_SHORT_NAME="V43"\n'
                'MESH433_CHANNEL_URL="%s"\nMESH_CHANNEL_URL="%s"\nMESH868_PRIVATE_PSK="ClaveSecretaPSK123456"\n'
                'APRS_PASSCODE="12345"' % (urls['MESH433_CHANNEL_URL'], urls['MESH_CHANNEL_URL']))
    with open(etc, 'w', encoding='utf-8') as f:
        f.write("MESH433_LONG_NAME='Viejo 433'\nMESH433_SHORT_NAME='V43'\nMESH433_CHANNEL_URL='%s'\n"
                "MESH_CHANNEL_URL='%s'\nMESH868_PRIVATE_PSK='ClaveSecretaPSK123456'\nOWRX_MAPA_LORA='no'\n"
                % (urls['MESH433_CHANNEL_URL'], urls['MESH_CHANNEL_URL']))
    os.chmod(etc, 0o600)

    # OpenWebRX+ de mentira: /settings da 200 solo con la sesión buena (como AuthorizationMixin)
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

    os.environ.update(MESH_ADMIN_OWRX='127.0.0.1:%d' % owrx.server_port, BRICOHAMS_ENV=etc, BRICOHAMS_KIT_ENV=kit,
                      RAK_RUN_DIR=tmp, MESH_URL_CLI=os.path.join(BIN, 'bricohams-mesh-url'))
    ruta = os.path.join(BIN, 'bricohams-mesh-admin')
    cargador = importlib.machinery.SourceFileLoader('mesh_admin', ruta)
    M = importlib.util.module_from_spec(importlib.util.spec_from_loader('mesh_admin', cargador))
    cargador.exec_module(M)
    M.TRABAJO.lanzar = lambda *a, **k: True          # nada de hablar con radios de verdad
    M.TAK_ACCESO = os.path.join(tmp, 'tak-access.txt')  # nunca el /etc de verdad

    # --- funciones sueltas
    assert M.tapar('meshtastic --seturl https://meshtastic.org/e/#CgMSAQE --ch-set psk base64:QUJDREVGR0hJSktMTU5PUA==') \
        .count('…') == 2 and 'CgMSAQE' not in M.tapar('https://meshtastic.org/e/#CgMSAQE')
    for malo in ('a"b', "a'b", 'a$b', 'a`b', 'a\\b', 'a\nb'):
        try:
            M.validar_nombres(malo, 'X')
            raise AssertionError('acepta %r' % malo)
        except ValueError:
            pass
    for largo, corto in (('', 'A'), ('x' * 40, 'A'), ('Bien', ''), ('Bien', 'ABCDE')):
        try:
            M.validar_nombres(largo, corto)
            raise AssertionError('acepta %r/%r' % (largo, corto))
        except ValueError:
            pass
    assert M.validar_nombres(' Nodo Murcia ', 'MU1') == ('Nodo Murcia', 'MU1')
    assert M.validar_url(urls['MESH433_CHANNEL_URL'], 'EU_433')
    for u, reg in ((urls['MESH433_CHANNEL_URL'], 'EU_868'), ('https://example.com/#abc', 'EU_433'),
                   ('https://meshtastic.org/e/#@@@@', 'EU_433')):
        try:
            M.validar_url(u, reg)
            raise AssertionError('acepta la URL %s para %s' % (u, reg))
        except ValueError:
            pass
    assert not M.autorizado('') and not M.autorizado('corta') and not M.autorizado('a b;c=d12345')
    assert not M.autorizado('OtraSesion_1234567890') and M.autorizado(SESION)

    # --- el servicio web
    srv = M.Servidor(('127.0.0.1', 0), M.Manejador)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    def pide(metodo, ruta, cuerpo=None, cab=None):
        c = http.client.HTTPConnection('127.0.0.1', srv.server_port, timeout=10)
        h = {'Host': 'sdr.ejemplo.org'}
        h.update(cab or {})
        if cuerpo is not None:
            h['Content-Type'] = 'application/x-www-form-urlencoded'
        c.request(metodo, ruta, body=cuerpo, headers=h)
        r = c.getresponse()
        d = r.read().decode('utf-8')
        c.close()
        return r.status, dict(r.getheaders()), d

    BASE = '/settings/bricohams/meshtastic'
    COOKIE = {'Cookie': 'owrx-session=' + SESION}
    consultas_tak = []
    real_posiciones = M.posiciones_tak

    def tak_falso():
        consultas_tak.append(True)
        return {'nodes': [{'uid': 'privado', 'callsign': 'TAK', 'lat': 38, 'lon': -1}]}

    M.posiciones_tak = tak_falso
    st, _, d = pide('GET', M.TAK_POSICIONES)
    assert st == 401 and 'privado' not in d and not consultas_tak
    st, h, d = pide('GET', M.TAK_POSICIONES, cab=COOKIE)
    assert st == 200 and json.loads(d)['nodes'][0]['uid'] == 'privado'
    assert h['Cache-Control'] == 'no-store' and len(consultas_tak) == 1
    real_auth, M.autorizado = M.autorizado, lambda s: False
    st, _, _ = pide('GET', M.TAK_POSICIONES, cab=COOKIE)
    assert st == 401 and len(consultas_tak) == 1, 'TAK no usa la cache de sesiones revocadas'
    M.autorizado = real_auth

    def tak_caido():
        raise RuntimeError('TAK apagado de prueba')

    M.posiciones_tak = tak_caido
    assert pide('GET', M.TAK_POSICIONES, cab=COOKIE)[0] == 503
    M.posiciones_tak = real_posiciones
    st, h, _ = pide('GET', BASE)
    assert st == 302 and h['Location'].startswith('/login?ref=settings/bricohams/meshtastic'), 'sin sesión: al login'
    st, _, _ = pide('GET', BASE, cab={'Cookie': 'owrx-session=OtraSesion_1234567890'})
    assert st == 302, 'una sesión que OpenWebRX+ no acepta no entra'
    st, _, _ = pide('POST', BASE, 'accion=leer', {'Origin': 'https://sdr.ejemplo.org'})
    assert st == 403, 'POST sin sesión: 403'
    st, _, _ = pide('GET', '/settings/bricohams/otra', cab=COOKIE)
    assert st == 404
    # auth_request del cliente web de Meshtastic (:8443): 204 admin, 401 el resto, sin cuerpo
    st, _, d = pide('GET', '/settings/bricohams/auth')
    assert st == 401 and d == ''
    st, _, _ = pide('GET', '/settings/bricohams/auth', cab={'Cookie': 'owrx-session=OtraSesion_1234567890'})
    assert st == 401
    st, _, d = pide('GET', '/settings/bricohams/auth', cab=COOKIE)
    assert st == 204 and d == '' and M._VALIDAS.get(SESION), 'sesión buena: 204 y recordada'
    real, M.autorizado = M.autorizado, lambda s: False
    assert M.autorizado_cache(SESION), 'la caché evita preguntar a OpenWebRX+ en cada sondeo'
    M._VALIDAS.clear()
    assert not M.autorizado_cache(SESION), 'caducada la caché, se vuelve a validar'
    M.autorizado = real
    st, h, _ = pide('GET', '/settings/bricohams', cab=COOKIE)
    assert st == 302 and h['Location'] == BASE
    st, h, pag = pide('GET', BASE, cab=COOKIE)
    assert st == 200 and 'Viejo 433' in pag and 'Meshtastic' in pag
    assert 'no-store' in h['Cache-Control'] and "frame-ancestors 'self'" in h['Content-Security-Policy']
    for secreto in ('ClaveSecretaPSK123456', urls['MESH433_CHANNEL_URL'].split('#')[1][:20],
                    urls['MESH_CHANNEL_URL'].split('#')[1][:20], '12345"'):
        assert secreto not in pag, 'la página no enseña claves ni URLs'
    tk = re.search(r'name="csrf" value="([0-9a-f]+)"', pag).group(1)

    datos = {'accion': 'guardar433', 'largo': 'Nuevo 433', 'corto': 'N43', 'rol': 'ROUTER', 'url': '', 'csrf': tk}
    st, _, _ = pide('POST', BASE, urlencode(dict(datos, csrf='0' * 40)), dict(COOKIE, Origin='https://sdr.ejemplo.org'))
    assert st == 403, 'CSRF malo'
    st, _, _ = pide('POST', BASE, urlencode(datos), dict(COOKIE, Origin='https://malo.example.com'))
    assert st == 403, 'otro origen'
    st, _, _ = pide('POST', BASE, urlencode(datos), COOKIE)
    assert st == 403, 'sin Origin ni Referer'
    st, _, pag = pide('POST', BASE, urlencode(datos), dict(COOKIE, Referer='https://sdr.ejemplo.org' + BASE))
    assert st == 200 and 'Guardado' in pag, pag[-600:]
    k = open(kit, encoding='utf-8').read()
    e = open(etc, encoding='utf-8').read()
    assert 'MESH433_LONG_NAME="Nuevo 433"        # nombre largo\n' in k, 'conserva comillas y comentario'
    assert 'MESH433_SHORT_NAME="N43"' in k and 'MESH433_ROLE="ROUTER"\n' in k and 'APRS_PASSCODE="12345"\n' in k
    assert "MESH433_LONG_NAME='Nuevo 433'" in e and "MESH433_ROLE='ROUTER'" in e
    assert urls['MESH433_CHANNEL_URL'] in k and 'ClaveSecretaPSK123456' in e, 'URL vacía = no se toca'
    assert os.name != 'posix' or oct(os.stat(etc).st_mode & 0o777) == oct(0o600), 'mismo modo (lleva claves)'
    # dato malo: error en la página y el .env intacto
    st, _, pag = pide('POST', BASE, urlencode(dict(datos, largo='x"; rm -rf /')), dict(COOKIE, Origin='https://sdr.ejemplo.org'))
    assert st == 200 and 'alert-danger' in pag and open(kit, encoding='utf-8').read() == k
    st, _, pag = pide('POST', BASE, urlencode(dict(datos, accion='guardar868', url=urls['MESH433_CHANNEL_URL'])),
                      dict(COOKIE, Origin='https://sdr.ejemplo.org'))
    assert 'EU_433' in pag and 'alert-danger' in pag, 'URL de 433 en el nodo 868: no'
    st, _, pag = pide('POST', BASE, urlencode({'accion': 'mapa', 'MESH433_OWRX': 'yes', 'csrf': tk}),
                      dict(COOKIE, Origin='https://sdr.ejemplo.org'))
    assert st == 200 and "MESH868_OWRX='no'" in open(etc, encoding='utf-8').read()
    assert 'MESH433_OWRX="yes"' in open(kit, encoding='utf-8').read()

    # --- página APRS (RAK): misma sesión, solo lectura + reinicio, sin passcode
    APRS = '/settings/bricohams/aprs'
    st, h, _ = pide('GET', APRS)
    assert st == 302 and h['Location'] == '/login?ref=settings/bricohams/aprs', 'APRS sin sesión: al login'
    M.systemctl = lambda *a: 0
    st, _, pag = pide('GET', APRS, cab=COOKIE)
    assert st == 200 and 'Sin datos' in pag, 'sin JSON del RAK: lo dice'
    with open(os.path.join(tmp, 'rak-aprs.json'), 'w', encoding='utf-8') as f:
        json.dump({'actualizado': '2026-10-11T15:37:42', 'puerto': '/dev/rak-aprs',
                   'rak': {'fw': '1.0.0', 'call': 'N0CALL-15', 'radio': 'ok', 'freq': 433775000, 'tx': True, 'rx': 11,
                           'txn': 4, 'vbat': None, 'gps': {'present': True, 'fix': False}},
                   'aprsis': {'conectado': True, 'enviados': 9, 'activo': True},
                   'oidos': [{'hora': '15:37:06', 'de': 'N0CALL-10', 'rssi': -60, 'snr': 7.5, 'aprsis': True,
                              'paquete': 'N0CALL-10>APLRG1:<script>x</script>'}]}, f)
    st, _, pag = pide('GET', APRS, cab=COOKIE)
    assert st == 200 and 'N0CALL-15' in pag and '433.775 MHz' in pag and 'conectado' in pag and 'APRS (RAK)' in pag
    assert '<script>x' not in pag and '&lt;script&gt;x' in pag, 'el registro se escapa'
    assert '12345' not in pag, 'ni passcode ni claves'
    tk2 = re.search(r'name="csrf" value="([0-9a-f]+)"', pag).group(1)
    st, _, pag = pide('POST', APRS, urlencode({'accion': 'reiniciarrak', 'csrf': tk2}), dict(COOKIE, Origin='https://sdr.ejemplo.org'))
    assert st == 200 and 'Reiniciando la pasarela' in pag
    st, _, pag = pide('POST', APRS, urlencode({'accion': 'guardar433', 'largo': 'X', 'corto': 'X', 'csrf': tk2}),
                      dict(COOKIE, Origin='https://sdr.ejemplo.org'))
    assert 'alert-danger' in pag, 'desde la página APRS solo se reinicia el RAK'
    st, _, pag = pide('GET', BASE, cab=COOKIE)
    assert 'href="%s"' % APRS in pag, 'enlace Meshtastic → APRS'

    # --- v5.0: paneles TAK y Monitorización (misma sesión de /settings, lista blanca de servicios)
    ORIGEN = dict(COOKIE, Origin='https://sdr.ejemplo.org')
    for ruta in (M.TAK, M.MONITOR):
        st, h, _ = pide('GET', ruta)
        assert st == 302 and h['Location'] == '/login?ref=' + ruta.lstrip('/'), 'sin sesión: al login'
        assert pide('POST', ruta, 'accion=tak-parar', {'Origin': 'https://sdr.ejemplo.org'})[0] == 403
    instaladas = set()
    real_registro = M.registro
    M.estado_unidad = lambda u: (u in instaladas, u in instaladas, 'active (running)' if u in instaladas else 'no instalado')
    M.registro = lambda u, lineas=40: 'arranque ok password=SuperSecreta <b>x</b>'
    st, _, pag = pide('GET', M.TAK, cab=COOKIE)
    assert st == 200 and 'TAK=yes' in pag and 'no está instalado' in pag
    st, _, pag = pide('GET', M.MONITOR, cab=COOKIE)
    assert st == 200 and 'MONITORIZACION=yes' in pag and '<iframe' not in pag
    instaladas.update(M.TAK_UNIDADES + M.MON_UNIDADES)
    st, h, pag = pide('GET', M.TAK, cab=COOKIE)
    assert st == 200 and 'https://sdr.ejemplo.org:8445/' in pag and 'sdr.ejemplo.org:8089' in pag
    assert 'tak-access.txt' in pag and 'value="tak-reiniciar-bricohams-tak"' in pag and '<b>x</b>' not in pag
    assert "frame-ancestors 'self'" in h['Content-Security-Policy']
    st, _, pag = pide('GET', M.TAK, cab=dict(COOKIE, Host='evil"><script>'))
    assert '<script>' not in pag and '&lt;IP-de-la-estación&gt;' in pag, 'Host raro: no se refleja'
    st, _, pag = pide('GET', M.MONITOR, cab=COOKIE)
    assert st == 200 and '<iframe src="/settings/bricohams/grafana/d/bricohams/bricohams?orgId=1&amp;kiosk' in pag
    assert 'value="mon-reiniciar-grafana-server"' in pag
    tk3 = re.search(r'name="csrf" value="([0-9a-f]+)"', pag).group(1)
    lanzados = []
    M.TRABAJO.lanzar = lambda titulo, fn, **k: lanzados.append(titulo) or True
    st, _, pag = pide('POST', M.TAK, urlencode({'accion': 'tak-reiniciar', 'csrf': tk3}), ORIGEN)
    assert st == 200 and 'Orden enviada' in pag and 'bricohams-tak' in lanzados[-1] and 'postgresql' in lanzados[-1]
    st, _, pag = pide('POST', M.MONITOR, urlencode({'accion': 'mon-parar-prometheus-node-exporter', 'csrf': tk3}), ORIGEN)
    assert st == 200 and 'Orden enviada' in pag and lanzados[-1].endswith(': prometheus-node-exporter')
    n = len(lanzados)
    for ruta, malo in ((M.TAK, 'tak-reiniciar-ssh'), (M.TAK, 'tak-borrar'), (M.TAK, 'mon-reiniciar'),
                       (M.MONITOR, 'tak-parar'), (M.MONITOR, 'mon-parar-openwebrx'), (BASE, 'tak-parar'),
                       (BASE, 'mon-reiniciar'), (APRS, 'tak-parar')):
        st, _, pag = pide('POST', ruta, urlencode({'accion': malo, 'csrf': tk3}), ORIGEN)
        assert st == 200 and 'alert-danger' in pag, '%s no se acepta en %s' % (malo, ruta)
    assert len(lanzados) == n, 'nada fuera de la lista blanca llega a systemctl'
    assert pide('POST', M.TAK, urlencode({'accion': 'tak-parar', 'csrf': '0' * 40}), ORIGEN)[0] == 403

    # --- credenciales TAK: ocultas por defecto, visibles solo en la respuesta al POST «Mostrar»
    st, _, pag = pide('GET', M.TAK, cab=COOKIE)
    assert 'No hay credenciales' in pag, 'sin tak-access.txt: lo dice'
    with open(M.TAK_ACCESO, 'w', encoding='utf-8') as f:
        f.write('n0call: ClaveAdminTAK_aaaaaaaa\nn0call-tak: ClaveUserTAK_bbbbbbbb\n')
    st, h, pag = pide('GET', M.TAK, cab=COOKIE)
    assert 'n0call-tak' in pag and 'administrador' in pag and 'value="tak-credenciales"' in pag
    assert 'ClaveAdminTAK' not in pag and 'ClaveUserTAK' not in pag, 'GET nunca enseña claves'
    assert h['Cache-Control'] == 'no-store'
    st, _, pag = pide('POST', M.TAK, urlencode({'accion': 'tak-credenciales', 'csrf': tk3}), ORIGEN)
    assert st == 200 and 'ClaveAdminTAK_aaaaaaaa' in pag and 'ClaveUserTAK_bbbbbbbb' in pag
    assert pide('POST', M.TAK, urlencode({'accion': 'tak-credenciales', 'csrf': '0' * 40}), ORIGEN)[0] == 403
    assert pide('POST', M.TAK, urlencode({'accion': 'tak-credenciales', 'csrf': tk3}),
                dict(COOKIE, Origin='https://evil.example'))[0] == 403
    for ruta in (BASE, M.MONITOR, APRS):
        st, _, pag = pide('POST', ruta, urlencode({'accion': 'tak-credenciales', 'csrf': tk3}), ORIGEN)
        assert 'alert-danger' in pag and 'ClaveAdminTAK' not in pag, 'credenciales solo desde la página TAK'
    n = len(lanzados)
    for malos in ({'usuario': 'n0call', 'clave': 'ClaveNueva_123456', 'clave2': 'ClaveNueva_654321'},
                  {'usuario': 'n0call', 'clave': 'corta', 'clave2': 'corta'},
                  {'usuario': 'n0call', 'clave': 'Con espacio 123456', 'clave2': 'Con espacio 123456'},
                  {'usuario': 'root', 'generar': 'yes'}):
        st, _, pag = pide('POST', M.TAK, urlencode(dict(malos, accion='tak-clave', csrf=tk3)), ORIGEN)
        assert 'alert-danger' in pag, 'tak-clave rechaza %r' % malos
    st, _, pag = pide('POST', M.MONITOR, urlencode({'accion': 'tak-clave', 'usuario': 'n0call', 'generar': 'yes',
                                                     'csrf': tk3}), ORIGEN)
    assert 'alert-danger' in pag and len(lanzados) == n, 'tak-clave no se acepta fuera de la página TAK'
    st, _, pag = pide('POST', M.TAK, urlencode({'accion': 'tak-clave', 'usuario': 'n0call-tak', 'clave': 'ClaveNueva_123456',
                                                 'clave2': 'ClaveNueva_123456', 'csrf': tk3}), ORIGEN)
    assert 'Cambiando la clave de n0call-tak' in pag and 'ClaveNueva_123456' not in pag and len(lanzados) == n + 1
    vistos = []
    real_run = M.subprocess.run
    M.subprocess.run = lambda arg, **k: vistos.append((arg, k)) or type('R', (), {'returncode': 0, 'stdout': 'ok\n', 'stderr': ''})()
    notas = []

    class T2:
        def apunta(self, x):
            notas.append(x)
    try:
        M.tarea_clave_tak('n0call-tak', 'ClaveNueva_123456')(T2())
    finally:
        M.subprocess.run = real_run
    arg, k = vistos[0]
    assert arg[:4] == ['runuser', '-u', 'opentakserver', '--'] and 'ClaveNueva_123456' not in ' '.join(arg)
    assert k['input'] == 'n0call-tak\nClaveNueva_123456\n', 'la clave va por stdin, no por argv'
    assert not any('ClaveNueva' in x for x in notas), 'la clave no sale en el registro del trabajo'
    assert M.leer_acceso_tak() == [('n0call', 'ClaveAdminTAK_aaaaaaaa'), ('n0call-tak', 'ClaveNueva_123456')]
    if os.name == 'posix':
        assert os.stat(M.TAK_ACCESO).st_mode & 0o777 == 0o600
    M.subprocess.run = lambda arg, **k: type('R', (), {'returncode': 3, 'stdout': '', 'stderr': ''})()
    try:
        M.tarea_clave_tak('n0call', 'OtraClave_1234567')(T2())
        raise AssertionError('usuario inexistente en OTS: debe fallar')
    except RuntimeError:
        pass
    finally:
        M.subprocess.run = real_run
    assert M.leer_acceso_tak()[0] == ('n0call', 'ClaveAdminTAK_aaaaaaaa'), 'si OTS falla, el fichero no cambia'
    llamadas = []
    M.systemctl = lambda *a: llamadas.append(a) or 0
    real_sleep = M.time.sleep
    M.time.sleep = lambda s: None

    class T:
        def apunta(self, x):
            pass
    try:
        M.tarea_unidades('stop', M.TAK_UNIDADES)(T())
    finally:
        M.time.sleep = real_sleep
    assert [a[1] for a in llamadas] == [u + '.service' for u in reversed(M.TAK_UNIDADES)], 'parar: al revés'
    real_run = M.subprocess.run
    M.subprocess.run = lambda *a, **k: type('R', (), {'stdout': 'db password=SuperSecreta token: abc123\nok', 'stderr': ''})()
    try:
        r = real_registro('bricohams-tak')
    finally:
        M.subprocess.run = real_run
    assert 'SuperSecreta' not in r and 'abc123' not in r and 'ok' in r, 'el registro tapa claves'
    srv.shutdown()
    owrx.shutdown()

    # --- instalación: solo en /settings, nada en la web pública
    R = open(os.path.join(RAIZ, 'files', 'nginx', 'bricohams-sdr-rutas.conf'), encoding='utf-8').read()
    assert 'location /settings/bricohams/ {' in R and 'proxy_pass http://127.0.0.1:8076;' in R
    assert '^~ /settings' not in R and '= /settings' not in R, 'sin ^~ ni =: en HTTP manda la redirección a HTTPS'
    assert 'sub_filter' not in R, 'los botones van en la plantilla de OpenWebRX+, no en nginx (también por :8073)'
    # botones en settings.html de OpenWebRX+: idempotente y reversible
    orig = ('<div class="row settings-grid">\n        <div class="col-4">\n            <a class="btn btn-secondary" '
            'href="settings/wifi">WiFi setup</a>\n        </div>\n        <div class="col-4">\n'
            '            <a class="btn btn-secondary" href="features">Feature report</a>\n        </div>\n    </div>\n</body>')
    plant = os.path.join(tmp, 'settings.html')
    open(plant, 'w', encoding='utf-8').write(orig)
    os.environ['OWRX_SETTINGS_HTML'] = plant
    cb = importlib.machinery.SourceFileLoader('owrx_botones', os.path.join(BIN, 'bricohams-owrx-botones'))
    B = importlib.util.module_from_spec(importlib.util.spec_from_loader('owrx_botones', cb))
    cb.exec_module(B)
    assert B.main(['-q']) == 0 and B.main(['-q']) == 0
    p = open(plant, encoding='utf-8').read()
    assert p.count('href="settings/bricohams/meshtastic"') == 2 and p.count('href="settings/bricohams/aprs"') == 1
    assert p.count('id="bricohams-meshweb"') == 1 and ":8443/'" in p and '$' not in p
    assert p.index('settings/bricohams/aprs') < p.index('href="features"') < p.index('</body>')
    assert B.main(['-q', '--quitar']) == 0 and open(plant, encoding='utf-8').read() == orig
    with open(etc, 'a', encoding='utf-8') as f:
        f.write("MESH_WEB='no'\n")
    assert B.main(['-q']) == 0 and 'id="bricohams-meshweb"' not in open(plant, encoding='utf-8').read(), 'MESH_WEB=no: sin botón'
    assert B.main(['-q', '--quitar']) == 0 and open(plant, encoding='utf-8').read() == orig
    open(plant, 'w', encoding='utf-8').write('<html><body>\n</body>')
    B.main(['-q'])
    assert 'settings/bricohams/aprs' in open(plant, encoding='utf-8').read(), 'plantilla rara: antes de </body>'
    T = open(os.path.join(RAIZ, 'files', 'nginx', 'bricohams-sdr.conf.tmpl'), encoding='utf-8').read()
    assert T.index('#@ADMIN@') < T.index('#@HTTP@    include'), 'la regex de /settings→HTTPS va antes de las rutas'
    W = open(os.path.join(RAIZ, 'files', 'web', 'index.html.tmpl'), encoding='utf-8').read()
    assert '9443' not in W and 'settings/bricohams' not in W, 'el portal público no enlaza Meshtastic'
    S = open(os.path.join(RAIZ, 'install.sh'), encoding='utf-8').read()
    # cliente web de Meshtastic: 9443 solo para la Pi, fuera por :8443 con la sesión de /settings
    mw = [l[5:] for l in T.splitlines() if l.startswith('#@MW@')]
    assert mw and T.index('#@MW@') < T.index('#@SSL<'), 'el 8443 va dentro del bloque SSL'
    mw = '\n'.join(mw)
    assert 'listen 8443 ssl' in mw and 'proxy_pass http://127.0.0.1:8076/settings/bricohams/auth;' in mw
    assert mw.count('auth_request /_bh_auth;') == 2 and 'proxy_pass https://127.0.0.1:9443;' in mw
    assert 'location /' in mw and 'location /api/' in mw and 'internal;' in mw
    assert "s/^#@MW@//" in S and "/^#@MW@/d" in S
    assert 'Port: 9443' in S and 'iifname != "lo" tcp dport 9443 drop' in S and 'bricohams-meshweb-fw' in S
    assert 'MESH_WEB=' in ej
    assert '"$FILES/bin/bricohams-mesh-admin" /usr/local/bin/bricohams-mesh-admin' in S
    assert '"$FILES/bin/bricohams-owrx-botones" /usr/local/bin/bricohams-owrx-botones' in S and '99bricohams-owrx-botones' in S
    assert 'bricohams-mesh-admin.service' in S and 'ProtectSystem=strict' in S
    assert 'ReadWritePaths=-/var/lib/bricohams-tak' in S, 'sin esto OpenTAKServer no puede escribir al cambiar claves'
    T = open(os.path.join(RAIZ, 'tools', 'instalar_tak.sh'), encoding='utf-8').read()
    assert 'try-restart bricohams-mesh-admin' in T
    assert 'confirmed_at=datetime.now(timezone.utc)' in T, 'sin confirmed_at OpenTAKServer rechaza el login (400)'
    assert 'u.confirmed_at = datetime.now' in M.SCRIPT_CLAVE_TAK and 'u.active = True' in M.SCRIPT_CLAVE_TAK
    assert '^[A-Za-z0-9_.]{1,64}$' in T, 'instalar_tak.sh debe rechazar usuarios TAK con guion'
    assert "listen[^;]*default_server' \"$s\"" in S and 'nginx-desactivados' in S, 'otro default_server no puede saltarse /settings→HTTPS'
    print('test_mesh_admin: OK')
finally:
    shutil.rmtree(tmp, ignore_errors=True)
