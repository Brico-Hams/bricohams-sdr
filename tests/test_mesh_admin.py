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
                      RAK_RUN_DIR=tmp, MESH_URL_CLI=os.path.join(BIN, 'bricohams-mesh-url'),
                      BACKUP_REMOTO_CONF=os.path.join(tmp, 'br', 'backup-remoto.json'),
                      BACKUP_REMOTO_SECRET=os.path.join(tmp, 'br', 'backup-remoto.secret'),
                      BACKUP_REMOTO_DIR=os.path.join(tmp, 'brdat'))
    ruta = os.path.join(BIN, 'bricohams-mesh-admin')
    cargador = importlib.machinery.SourceFileLoader('mesh_admin', ruta)
    M = importlib.util.module_from_spec(importlib.util.spec_from_loader('mesh_admin', cargador))
    cargador.exec_module(M)
    M.TRABAJO.lanzar = lambda *a, **k: True          # nada de hablar con radios de verdad
    M.TAK_ACCESO = os.path.join(tmp, 'tak-access.txt')  # nunca el /etc de verdad

    # --- funciones sueltas
    assert M.destino('433', {}) == ('serie', '/dev/lilygo-mesh')
    assert M.destino('433', {'MESH433_WEB': 'yes'}) == ('tcp', '127.0.0.1:4404')
    assert M.destino('868', {'MESH433_WEB': 'yes'}) == ('tcp', '127.0.0.1')
    html_web = M.pagina_chat(SESION, host='sdr.ejemplo.es:443')
    assert 'https://sdr.ejemplo.es:8443/' in html_web and 'https://sdr.ejemplo.es:8444/' in html_web
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
    # v5.0 · el nodo 868 también tiene rol (MESH868_ROLE)
    assert pag.count('name="rol"') == 2, 'selector de rol en los dos nodos'
    d868 = dict(datos, accion='guardar868', largo='SDR 868', corto='S86', rol='CLIENT_BASE')
    st, _, pag = pide('POST', BASE, urlencode(dict(d868, rol='JEFE')), dict(COOKIE, Origin='https://sdr.ejemplo.org'))
    assert 'alert-danger' in pag and 'MESH868_ROLE' not in open(etc, encoding='utf-8').read(), 'rol no válido'
    st, _, pag = pide('POST', BASE, urlencode(d868), dict(COOKIE, Origin='https://sdr.ejemplo.org'))
    assert st == 200 and 'Guardado' in pag and "MESH868_ROLE='CLIENT_BASE'" in open(etc, encoding='utf-8').read()
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
    for ruta in (M.TAK, M.MONITOR, M.MAPFLIGHTS):
        st, h, _ = pide('GET', ruta)
        assert st == 302 and h['Location'] == '/login?ref=' + ruta.lstrip('/'), 'sin sesión: al login'
        assert pide('POST', ruta, 'accion=tak-parar', {'Origin': 'https://sdr.ejemplo.org'})[0] == 403
    instaladas = set()
    real_registro = M.registro
    M.estado_unidad = lambda u: (u in instaladas, u in instaladas, 'active (running)' if u in instaladas else 'no instalado')
    M.registro = lambda u, lineas=40: 'arranque ok password=SuperSecreta <b>x</b>'
    st, h, pag = pide('GET', M.MAPFLIGHTS, cab=COOKIE)
    assert st == 200 and 'desactivado' in pag and 'rbfeeder' in pag
    assert h['Cache-Control'] == 'no-store' and '<form' not in pag
    assert pide('POST', M.MAPFLIGHTS, 'accion=guardar', ORIGEN)[0] == 405
    with open(etc, 'a', encoding='utf-8') as f:
        f.write('\nMAPFLIGHTS_FEED="yes"\nMAPFLIGHTS_UUID="0123abcd-4567-89ef-0123-456789abcdef"\n')
    st, _, pag = pide('GET', M.MAPFLIGHTS, cab=COOKIE)
    assert st == 200 and 'activado' in pag and 'formato válido' in pag
    assert '0123abcd' not in pag and 'ClaveSecretaPSK123456' not in pag
    assert 'no confirma' in pag and 'no reinyecta' in pag
    with open(etc, 'a', encoding='utf-8') as f:
        f.write('MAPFLIGHTS_UUID="<script>alert(1)</script>"\n')
    st, _, pag = pide('GET', M.MAPFLIGHTS, cab=COOKIE)
    assert 'formato no válido' in pag and '<script>alert' not in pag
    assert pide('HEAD', M.MAPFLIGHTS, cab=COOKIE)[0] == 200
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

    # --- mensajes Meshtastic 433 / 868: historial de bricohams-mesh-owrx y envío por su socket
    M.MESH_RUN = os.path.join(tmp, 'mesh-run')
    os.makedirs(M.MESH_RUN)
    st, _, pag = pide('GET', M.MESH_CHAT, cab=COOKIE)
    assert st == 200 and 'servicio parado' in pag and 'Sin canales todavía' in pag, 'sin servicio: lo dice, sin formulario'
    canales = [{'indice': 0, 'nombre': 'principal', 'primario': True}, {'indice': 1, 'nombre': 'Murcia', 'primario': False}]
    json.dump({'redes': {'mesh433': {'canales': canales, 'mensajes': [
        {'t': 1700000000, 'dir': 'rx', 'canal': 1, 'de': 'CT01', 'texto': '<b>hola</b>', 'directo': False, 'snr': 5, 'rssi': -90},
        {'t': 1700000060, 'dir': 'rx', 'canal': 0, 'de': 'MU02', 'texto': 'privado', 'directo': True, 'snr': 1, 'rssi': -99},
        {'t': 1700000100, 'dir': 'tx', 'canal': 1, 'de': 'yo', 'texto': 'respuesta', 'directo': False}]},
        'mesh868': {'canales': [{'indice': 0, 'nombre': 'SFNarrow', 'primario': True}, {'indice': 3, 'nombre': 'murcia', 'primario': False}],
                    'mensajes': []}}}, open(os.path.join(M.MESH_RUN, 'chat.json'), 'w', encoding='utf-8'))
    json.dump({'fuentes': {'mesh433': {'conectado': True}, 'mesh868': {'conectado': False, 'error': 'sin HAT'}}},
              open(os.path.join(M.MESH_RUN, 'mesh.json'), 'w', encoding='utf-8'))
    st, h, pag = pide('GET', M.MESH_CHAT, cab=COOKIE)
    assert st == 200 and '&lt;b&gt;hola&lt;/b&gt;' in pag and '<b>hola</b>' not in pag, 'el texto recibido se escapa'
    assert 'badge-info">directo' in pag and 'table-active' in pag and 'conectado' in pag and 'sin HAT' in pag
    assert pag.count('value="mesh-enviar"') == 2 and '<option value="1">1 · Murcia</option>' in pag
    assert 'id="bricohams-tema"' in pag and "script-src 'none'" in h['Content-Security-Policy']
    assert 'http-equiv="refresh"' not in pag and 'http-equiv="refresh"' in pide('GET', M.MESH_CHAT + '?auto=1', cab=COOKIE)[2]
    assert M.canal_equivalente(json.load(open(os.path.join(M.MESH_RUN, 'chat.json')))['redes']['mesh868']['canales'], 'Murcia') == 3
    assert M.canal_equivalente([{'indice': 2, 'nombre': 'x', 'primario': True}], 'nada') == 2
    tkc = re.search(r'name="csrf" value="([0-9a-f]+)"', pag).group(1)
    pedidos = []
    if os.name == 'posix':
        import socket
        sv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sv.bind(os.path.join(M.MESH_RUN, 'enviar.sock'))
        sv.listen(4)

        def falso_mesh():
            while True:
                c, _ = sv.accept()
                d = json.loads(c.makefile().readline())
                pedidos.append(d)
                c.sendall((json.dumps({'ok': True} if d['fuente'] == 'mesh433' else {'ok': False, 'error': 'el nodo mesh868 no está conectado'}) + '\n').encode())
                c.close()
        threading.Thread(target=falso_mesh, daemon=True).start()
    st, _, pag = pide('POST', M.MESH_CHAT, urlencode({'accion': 'mesh-enviar', 'red': '433', 'canal': '1', 'texto': 'QSO\r\nmañana',
                                                      'ambas': 'yes', 'csrf': tkc}), ORIGEN)
    if os.name == 'posix':
        assert st == 200 and 'Mensaje enviado por la red 433 (canal Murcia)' in pag and 'No ha salido por la red 868' in pag, pag[-800:]
        assert pedidos[0] == {'fuente': 'mesh433', 'canal': 1, 'texto': 'QSO  mañana'}
        assert pedidos[1] == {'fuente': 'mesh868', 'canal': 3, 'texto': 'QSO  mañana'}, 'mismo canal por nombre en la otra red'
    else:
        assert st == 200 and 'alert-danger' in pag
    n = len(pedidos)
    for malos in ({'red': '999', 'canal': '0', 'texto': 'a'}, {'red': '433', 'canal': 'x', 'texto': 'a'},
                  {'red': '433', 'canal': '0', 'texto': '   '}, {'red': '433', 'canal': '0', 'texto': 'ñ' * 101}):
        st, _, pag = pide('POST', M.MESH_CHAT, urlencode(dict(malos, accion='mesh-enviar', csrf=tkc)), ORIGEN)
        assert st == 200 and 'alert-danger' in pag, malos
    st, _, pag = pide('POST', BASE, urlencode({'accion': 'mesh-enviar', 'red': '433', 'canal': '0', 'texto': 'a', 'csrf': tkc}), ORIGEN)
    assert 'alert-danger' in pag, 'el envío solo desde la página de mensajes'
    assert pide('POST', M.MESH_CHAT, urlencode({'accion': 'mesh-enviar', 'red': '433', 'canal': '0', 'texto': 'a', 'csrf': '0' * 40}), ORIGEN)[0] == 403
    assert pide('GET', M.MESH_CHAT)[0] == 302, 'sin sesión: al login'
    assert len(pedidos) == n, 'nada no válido llega al nodo'
    assert 'href="%s"' % M.MESH_CHAT in pide('GET', BASE, cab=COOKIE)[2], 'enlace desde el panel Meshtastic'

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

    # --- página Seguridad · backup remoto (SMB/NFS/SFTP/Drive/OneDrive): secretos nunca vuelven al navegador
    st, h, _ = pide('GET', M.SEGURIDAD)
    assert st == 302 and h['Location'] == '/login?ref=' + M.SEGURIDAD.lstrip('/')
    ordenes = []
    real_run = M.subprocess.run
    # «systemctl show» (estado del temporizador al pintar la página) no cuenta como orden
    M.subprocess.run = lambda arg, **k: (None if arg[:2] == ['systemctl', 'show'] else ordenes.append(list(arg))) or type(
        'R', (), {'returncode': 0, 'stdout': 'LoadState=loaded\nActiveState=inactive\n', 'stderr': ''})()
    try:
        st, h, pag = pide('GET', M.SEGURIDAD, cab=COOKIE)
        assert st == 200 and 'Backup remoto' in pag and h['Cache-Control'] == 'no-store'
        assert 'value="seg-copiar"' in pag and 'name="password"' in pag and 'Todavía no se ha ejecutado' in pag
        tks = re.search(r'name="csrf" value="([0-9a-f]+)"', pag).group(1)

        def seg(**campos):
            return pide('POST', M.SEGURIDAD, urlencode(dict(campos, csrf=tks)), ORIGEN)
        smb = dict(accion='seg-guardar', protocolo='cifs', destino='\\\\192.168.1.10\\fw\\backup',
                   usuario='DOMINIO\\backup', smb_version='3.0', retencion='7', programado='yes')
        n = len(ordenes)
        st, _, pag = seg(accion='seg-copiar')
        assert 'alert-danger' in pag and 'primero guarda' in pag and len(ordenes) == n, 'sin configuración no se lanza'
        for malo in (dict(smb, password='ClaveSMB_123', password2='Otra_123'),            # no coinciden
                     dict(smb, password=''),                                               # SMB sin contraseña
                     dict(smb, destino='\\\\srv\\a;rm -rf', password='x', password2='x'),
                     dict(smb, protocolo='ftp', password='x', password2='x'),
                     dict(smb, retencion='0', password='x', password2='x'),
                     dict(smb, password='a\nb', password2='a\nb'),
                     dict(accion='seg-guardar', protocolo='nfs', destino='nas:/x;reboot'),
                     dict(accion='seg-guardar', protocolo='sftp', servidor='evil host', usuario='u', password='x', password2='x'),
                     dict(accion='seg-guardar', protocolo='sftp', servidor='sftp.ej.org', puerto='70000', usuario='u',
                          password='x', password2='x'),
                     dict(accion='seg-guardar', protocolo='sftp', servidor='sftp.ej.org', ruta='../etc', usuario='u',
                          password='x', password2='x'),
                     dict(accion='seg-guardar', protocolo='gdrive', token='no es json'),
                     dict(accion='seg-guardar', protocolo='gdrive', token='{"refresh_token":"r"}'),
                     dict(accion='seg-guardar', protocolo='onedrive', token='{"access_token":"a"}', drive_id=''),
                     dict(accion='seg-guardar', protocolo='onedrive', token='{"access_token":"a"}', drive_id='a b;c')):
            st, _, pag = seg(**malo)
            assert st == 200 and 'alert-danger' in pag, 'backup remoto rechaza %r' % malo
        assert not os.path.exists(M.BR_CONF) and not os.path.exists(M.BR_SECRETO), 'nada se guarda si algo falla'
        st, _, pag = seg(**dict(smb, password='ClaveSMB_Secreta_123', password2='ClaveSMB_Secreta_123'))
        assert st == 200 and 'guardada' in pag and 'ClaveSMB_Secreta_123' not in pag, 'la contraseña no vuelve'
        assert ['systemctl', 'enable', '--now', 'bricohams-backup-remoto.timer'] in ordenes
        c = json.load(open(M.BR_CONF, encoding='utf-8'))
        assert c == {'protocolo': 'cifs', 'destino': '\\\\192.168.1.10\\fw\\backup', 'usuario': 'backup',
                     'dominio': 'DOMINIO', 'smb_version': '3.0', 'retencion': 7, 'incluir_secretos': False,
                     'programado': True}, c
        assert 'ClaveSMB' not in open(M.BR_CONF, encoding='utf-8').read(), 'la configuración no lleva secretos'
        assert json.load(open(M.BR_SECRETO, encoding='utf-8')) == {'password': 'ClaveSMB_Secreta_123'}
        if os.name == 'posix':
            assert os.stat(M.BR_SECRETO).st_mode & 0o777 == 0o600 and os.stat(M.BR_CONF).st_mode & 0o777 == 0o600
        st, _, pag = pide('GET', M.SEGURIDAD, cab=COOKIE)
        assert 'ClaveSMB_Secreta_123' not in pag and 'DOMINIO\\backup' in pag and '<span class="text-success">guardada' in pag
        st, _, pag = seg(**dict(smb, password='', programado=''))
        assert 'alert-danger' not in pag, 'contraseña vacía = conservar la guardada'
        assert json.load(open(M.BR_SECRETO, encoding='utf-8')) == {'password': 'ClaveSMB_Secreta_123'}
        assert ['systemctl', 'disable', '--now', 'bricohams-backup-remoto.timer'] in ordenes
        for orden in M.BR_ORDENES:
            st, _, pag = seg(accion='seg-' + orden)
            assert 'Lanzado' in pag and ordenes[-1] == ['systemctl', 'start', '--no-block',
                                                         'bricohams-backup-remoto@%s.service' % orden]
        n = len(ordenes)
        for malo in ('seg-borrar', 'seg-estado', 'seg-copiar;id', 'seg-'):
            st, _, pag = seg(accion=malo)
            assert 'alert-danger' in pag, malo
        assert len(ordenes) == n, 'solo las órdenes de la lista llegan a systemctl'
        for ruta in (BASE, M.TAK, M.MONITOR, APRS):
            st, _, pag = pide('POST', ruta, urlencode({'accion': 'seg-copiar', 'csrf': tks}), ORIGEN)
            assert 'alert-danger' in pag, 'seg-* solo desde la página Seguridad (%s)' % ruta
        assert len(ordenes) == n
        assert pide('POST', M.SEGURIDAD, urlencode({'accion': 'seg-copiar', 'csrf': '0' * 40}), ORIGEN)[0] == 403
        assert pide('POST', M.SEGURIDAD, urlencode({'accion': 'seg-copiar', 'csrf': tks}),
                    dict(COOKIE, Origin='https://evil.example'))[0] == 403
        # cambiar de protocolo no arrastra la contraseña SMB a otro destino
        st, _, pag = seg(accion='seg-guardar', protocolo='sftp', servidor='sftp.ej.org', usuario='u', puerto='22')
        assert 'falta la contraseña' in pag
        os.makedirs(os.path.dirname(M.BR_ESTADO), exist_ok=True)
        kh = os.path.join(os.path.dirname(M.BR_ESTADO), 'known_hosts')
        open(kh, 'w').write('vieja')
        st, _, pag = seg(accion='seg-guardar', protocolo='sftp', servidor='sftp.ej.org', usuario='u', puerto='22',
                         password='ClaveSFTP_1', password2='ClaveSFTP_1')
        assert 'Obtener huella' in pag and not os.path.exists(kh), 'servidor SFTP nuevo: huella olvidada'
        assert json.load(open(M.BR_SECRETO, encoding='utf-8')) == {'password': 'ClaveSFTP_1'}
        tokj = '{"access_token":"ya29.SECRETO","refresh_token":"1//RefrescoSecreto","expiry":"2030-01-01T00:00:00Z"}'
        st, _, pag = seg(accion='seg-guardar', protocolo='onedrive', token=tokj, drive_id='b!AbC-123_x', drive_type='business')
        assert 'alert-danger' not in pag and 'SECRETO' not in pag and 'RefrescoSecreto' not in pag
        assert json.loads(json.load(open(M.BR_SECRETO, encoding='utf-8'))['token'])['refresh_token'] == '1//RefrescoSecreto'
        assert json.load(open(M.BR_CONF, encoding='utf-8'))['ruta'] == 'bricohams-backup'
        with open(M.BR_ESTADO, 'w', encoding='utf-8') as f:
            json.dump({'copiar': {'fecha': '2025-01-01 04:30', 'ok': False, 'mensaje': 'token: abc123 <b>x</b>'},
                       'ultima_copia': 'bricohams-<i>.tar.gz', 'ultimo_tamano': 3 * 1024 * 1024}, f)
        st, _, pag = pide('GET', M.SEGURIDAD, cab=COOKIE)
        assert 'abc123' not in pag and '<b>x</b>' not in pag and '<i>' not in pag and '3.0 MB' in pag
        assert 'SECRETO' not in pag and 'value="b!AbC-123_x"' in pag
        st, _, pag = seg(accion='seg-olvidar')
        assert not os.path.exists(M.BR_CONF) and not os.path.exists(M.BR_SECRETO), 'olvidar borra credenciales'
    finally:
        M.subprocess.run = real_run
    assert M.tapar('{"access_token":"ya29.abc","refresh_token":"1//xyz"}').count('ya29') == 0
    # Paneles de agendas: misma autenticacion, CSRF y aislamiento de acciones.
    for ruta in (M.SATELITES, M.CLIMA):
        assert pide('GET', ruta)[0] == 302
        st, h, pag = pide('GET', ruta, cab=COOKIE)
        assert st == 200 and 'no-store' in h['Cache-Control']
        assert ('https://www.amsat.org/status/submit.php' in h['Content-Security-Policy']) == (ruta == M.SATELITES)
        assert 'ClaveSecretaPSK123456' not in pag
        assert pide('POST', ruta, urlencode({'accion': 'wx-guardar', 'csrf': 'malo'}), ORIGEN)[0] == 403
        assert pide('POST', ruta, urlencode({'accion': 'wx-guardar', 'csrf': tks}),
                    dict(COOKIE, Origin='https://evil.example'))[0] == 403
        st, _, pag = pide('POST', ruta, urlencode({'accion': 'mesh-enviar', 'csrf': tks}), ORIGEN)
        assert st == 200 and 'alert-danger' in pag
    for ruta, otra in ((M.SATELITES, 'wx-guardar'), (M.CLIMA, 'sat-guardar'), (BASE, 'sat-guardar')):
        st, _, pag = pide('POST', ruta, urlencode({'accion': otra, 'csrf': tks}), ORIGEN)
        assert st == 200 and 'alert-danger' in pag
    srv.shutdown()
    owrx.shutdown()

    # --- instalación: solo en /settings, nada en la web pública
    R = open(os.path.join(RAIZ, 'files', 'nginx', 'bricohams-sdr-rutas.conf'), encoding='utf-8').read()
    assert 'location /settings/bricohams/ {' in R and 'proxy_pass http://127.0.0.1:8076;' in R
    assert '^~ /settings' not in R and '= /settings' not in R, 'sin ^~ ni =: en HTTP manda la redirección a HTTPS'
    subs = [l.strip() for l in R.splitlines() if l.strip().startswith('sub_filter ')]
    assert len(subs) == 1 and 'webrx-top-logo' in subs[0] and 'bh-marca-logo' in subs[0], 'nginx solo cambia el logo'
    assert 'settings/bricohams' not in ''.join(subs), 'los botones van en la plantilla de OpenWebRX+, no en nginx (también por :8073)'
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
    assert p.count('data-bricohams href="settings/bricohams/seguridad"') == 1, 'botón Seguridad (pasa a HTTPS desde :8073)'
    assert '/' + 'settings/bricohams/seguridad' == M.SEGURIDAD
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
    # tema oscuro: el mismo CSS en admin.css de OpenWebRX+ y en línea en los paneles
    assert B.TEMA_OSCURO == M.TEMA_OSCURO, 'el tema de botones y el de mesh-admin deben coincidir'
    assert 'select,textarea{background-color:#2b2b2b' in M.TEMA_OSCURO and 'select option' in M.TEMA_OSCURO
    h = M.con_tema('<html><head><title>x</title></head><body></body></html>')
    assert h.count('id="bricohams-tema"') == 1 and h.index('bricohams-tema') < h.index('</head>')
    assert M.con_tema(h) == h, 'idempotente'
    os.makedirs(os.path.join(tmp, 'css'), exist_ok=True)
    acss = os.path.join(tmp, 'css', 'admin.css')
    css_orig = '@import url("openwebrx-header.css");\nbody { margin-bottom: 5rem; }\n'
    open(acss, 'w', encoding='utf-8').write(css_orig)
    hojas = {'login.css': B.LOGIN_OSCURO, 'openwebrx-header.css': B.CABECERA}
    for nombre in hojas:
        open(os.path.join(tmp, 'css', nombre), 'w', encoding='utf-8').write(css_orig)
    open(plant, 'w', encoding='utf-8').write(orig)
    assert B.main(['-q']) == 0 and B.main(['-q']) == 0
    c = open(acss, encoding='utf-8').read()
    assert c.startswith(css_orig) and c.count(B.CSS_INI) == 1 and c.count(B.CSS_FIN) == 1 and B.TEMA_OSCURO in c
    for nombre, esperado in hojas.items():
        hoja = open(os.path.join(tmp, 'css', nombre), encoding='utf-8').read()
        assert hoja.startswith(css_orig) and hoja.count(B.CSS_INI) == 1 and esperado in hoja
    assert 'html,body{background-color:#1e1e1e!important' in B.LOGIN_OSCURO
    assert '.login{background-color:#2d2d2d!important' in B.LOGIN_OSCURO
    assert 'width:calc(100% - 32px)' in B.LOGIN_OSCURO
    assert '.webrx-top-bar{background:#242424!important}' in B.CABECERA
    assert 'background-image:none' not in B.CABECERA, 'se conserva la foto del banner expandido'
    assert B.main(['-q', '--quitar']) == 0 and open(acss, encoding='utf-8').read() == css_orig
    for nombre in hojas:
        assert open(os.path.join(tmp, 'css', nombre), encoding='utf-8').read() == css_orig
    assert open(plant, encoding='utf-8').read() == orig
    os.remove(acss)
    assert B.main(['-q']) == 0, 'sin admin.css no falla'
    B.main(['-q', '--quitar'])
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
    assert mw.count('auth_request /_bh_auth;') == 4 and 'proxy_pass https://127.0.0.1:9443;' in mw
    assert 'location /' in mw and 'location /api/' in mw and 'internal;' in mw
    assert "s/^#@MW@//" in S and "/^#@MW@/d" in S
    assert 'Port: 9443' in S and 'iifname != "lo" tcp dport 9443 drop' in S and 'bricohams-meshweb-fw' in S
    assert 'MESH_WEB=' in ej
    assert '"$FILES/bin/bricohams-mesh-admin" /usr/local/bin/bricohams-mesh-admin' in S
    assert '"$FILES/bin/bricohams-owrx-botones" /usr/local/bin/bricohams-owrx-botones' in S and '99bricohams-owrx-botones' in S
    assert 'bricohams-mesh-admin.service' in S and 'ProtectSystem=strict' in S
    assert 'ReadWritePaths=-/var/lib/bricohams-tak' in S, 'sin esto OpenTAKServer no puede escribir al cambiar claves'
    # v5.0 · copia remota: helper root, plantilla por orden, temporizador apagado hasta configurarlo
    assert 'ReadWritePaths=-/var/lib/bricohams-backup-remoto' in S, 'el panel borra known_hosts al cambiar de servidor'
    assert 'install -m 700 "$FILES/bin/bricohams-backup-remoto" /usr/local/sbin/bricohams-backup-remoto' in S
    assert 'apt_i cifs-utils nfs-common rclone openssh-client' in S
    assert 'bricohams-backup-remoto@.service' in S and 'bricohams-backup-remoto %i' in S and 'UMask=0077' in S
    assert 'Unit=bricohams-backup-remoto@copiar.service' in S and 'OnCalendar=*-*-* 05:15' in S
    assert "grep -q '\"programado\": *true' /etc/bricohams/backup-remoto.json" in S, 'el timer no se enciende sin destino'
    assert M.BR_UNIDAD == 'bricohams-backup-remoto'
    T = open(os.path.join(RAIZ, 'tools', 'instalar_tak.sh'), encoding='utf-8').read()
    assert 'try-restart bricohams-mesh-admin' in T
    assert 'confirmed_at=datetime.now(timezone.utc)' in T, 'sin confirmed_at OpenTAKServer rechaza el login (400)'
    assert 'u.confirmed_at = datetime.now' in M.SCRIPT_CLAVE_TAK and 'u.active = True' in M.SCRIPT_CLAVE_TAK
    assert '^[A-Za-z0-9_.]{1,64}$' in T, 'instalar_tak.sh debe rechazar usuarios TAK con guion'
    assert "listen[^;]*default_server' \"$s\"" in S and 'nginx-desactivados' in S, 'otro default_server no puede saltarse /settings→HTTPS'
    print('test_mesh_admin: OK')
finally:
    shutil.rmtree(tmp, ignore_errors=True)
