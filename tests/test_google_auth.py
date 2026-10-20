#!/usr/bin/env python3
"""Acceso de administradores con Google (bricohams-google-auth).
Sin red ni Google de verdad: un endpoint de tokens falso (comprueba PKCE y devuelve un
id_token), un OpenWebRX+ falso (/login con cookie owrx-session) y un panel falso
(/settings/bricohams/auth). Además, la transformación de nginx sobre la configuración
que genera install.sh (aplicar, idempotencia y quitar = original) y «preparar»."""
import base64
import hashlib
import http.client
import http.server
import importlib.machinery
import importlib.util
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from urllib.parse import parse_qs, urlsplit

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
TMP = tempfile.mkdtemp(prefix='bh-google-')
os.environ['BRICOHAMS_ETC'] = os.path.join(TMP, 'etc')
os.environ['GOOGLE_AUTH_UNIDAD'] = os.path.join(TMP, 'bricohams-google-auth.service')
os.makedirs(os.environ['BRICOHAMS_ETC'])
_l = importlib.machinery.SourceFileLoader('bga', os.path.join(RAIZ, 'files/bin/bricohams-google-auth'))
_s = importlib.util.spec_from_loader('bga', _l)
G = importlib.util.module_from_spec(_s)
_l.exec_module(G)

CID = '123456789012-abcdefghij0123456789.apps.googleusercontent.com'
DOM = 'sdr.ejemplo.es'
CLAVE = bytes.fromhex('11' * 32)


def b64u(d):
    return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b'=').decode()


def jwt(claims):
    return '%s.%s.firma' % (b64u({'alg': 'RS256'}), b64u(claims))


def claims(**k):
    ahora = int(time.time())
    c = {'iss': 'https://accounts.google.com', 'aud': CID, 'exp': ahora + 600, 'iat': ahora,
         'nonce': 'N1', 'email': 'admin@ejemplo.es', 'email_verified': True}
    c.update(k)
    return c


# ------------------------------------------------------------------ funciones puras
assert G.lista_admins(' A@Ejemplo.es, @empresa.es;b@x.org a@ejemplo.es ') == ['a@ejemplo.es', '@empresa.es', 'b@x.org']
for malo in ('nadie', 'a@b', '@', 'x@y.es,<script>'):
    try:
        G.lista_admins(malo)
        raise AssertionError(malo)
    except ValueError:
        pass
adm = ['a@ejemplo.es', '@empresa.es']
assert G.permitido('A@ejemplo.es', '', adm)
assert G.permitido('quien@empresa.es', 'empresa.es', adm)
assert not G.permitido('quien@empresa.es', '', adm), '@dominio exige la cuenta de Workspace (hd)'
assert not G.permitido('quien@empresa.es', 'otra.es', adm)
assert not G.permitido('b@ejemplo.es', 'ejemplo.es', adm)
assert not G.permitido('', '', adm)

for bueno in ('/settings', '/settings/general?x=1', '/_bh_google/entrar?ref=%2Fsettings'):
    assert G.ruta_segura(bueno) == bueno
for malo in ('https://malo.es/', '//malo.es/', '/\\malo.es', 'settings', '/a b', '/x\r\nSet-Cookie: a', None, ''):
    assert G.ruta_segura(malo) == '/settings', malo

f = G.firmar(CLAVE, 'ses', {'e': 'a@ejemplo.es', 'x': time.time() + 60})
assert G.verificar(CLAVE, 'ses', f)['e'] == 'a@ejemplo.es'
assert G.verificar(CLAVE, 'est', f) is None, 'una cookie de estado no vale como sesión y al revés'
assert G.verificar(bytes(32), 'ses', f) is None
cuerpo, firma = f.split('.')
otro = G.b64u(json.dumps({'e': 'intruso@x.es', 'x': time.time() + 60}).encode())
assert G.verificar(CLAVE, 'ses', otro + '.' + firma) is None
assert G.verificar(CLAVE, 'ses', G.firmar(CLAVE, 'ses', {'e': 'a', 'x': time.time() - 1})) is None
for basura in ('', 'a', 'a.b.c', None, '%%%.%%%'):
    assert G.verificar(CLAVE, 'ses', basura) is None

assert G.validar_id_token(jwt(claims()), CID, 'N1')['email'] == 'admin@ejemplo.es'
assert G.validar_id_token(jwt(claims(iss='accounts.google.com', email_verified='true')), CID, 'N1')
assert G.validar_id_token(jwt(claims(aud=[CID, 'otro'], azp=CID)), CID, 'N1')
for mal, msg in ((claims(iss='https://malo.es'), 'emisor'), (claims(aud='otro'), 'audiencia'),
                 (claims(aud=[CID, 'otro'], azp='otro'), 'audiencia'), (claims(exp=int(time.time()) - 600), 'caducado'),
                 (claims(iat=int(time.time()) + 3600), 'futura'), (claims(nonce='otro'), 'nonce'),
                 (claims(email_verified=False), 'verificar'), (claims(email=''), 'correo')):
    try:
        G.validar_id_token(jwt(mal), CID, 'N1')
        raise AssertionError(msg)
    except ValueError as ex:
        assert msg in str(ex), (msg, ex)
for basura in ('', 'a.b', 'a.!!!.c'):
    try:
        G.validar_id_token(basura, CID, 'N1')
        raise AssertionError(basura)
    except ValueError:
        pass
print('ok · funciones puras')


# ------------------------------------------------------------------ servicios falsos
def libre():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    p = s.getsockname()[1]
    s.close()
    return p


class Falso(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass


GOOGLE = {'correo': 'admin@ejemplo.es', 'hd': '', 'retos': {}, 'peticiones': []}
OWRX = {'logins': []}
SESION_OWRX = 'b1946ac9-2a3f-4d1e-9c55-8d1a0f6a7e21'


class Google(Falso):
    def do_POST(self):
        d = {k: v[0] for k, v in parse_qs(self.rfile.read(int(self.headers['Content-Length'])).decode()).items()}
        GOOGLE['peticiones'].append(d)
        reto = GOOGLE['retos'].get(d.get('code'))
        bueno = (d.get('client_id') == CID and d.get('client_secret') == 'secreto-de-prueba-123' and
                 d.get('grant_type') == 'authorization_code' and d.get('redirect_uri') == 'https://%s/_bh_google/callback' % DOM and
                 reto and G.b64u(hashlib.sha256(d.get('code_verifier', '').encode()).digest()) == reto[0])
        if not bueno:
            self.send_response(400)
            self.end_headers()
            return
        c = claims(nonce=reto[1], email=GOOGLE['correo'])
        if GOOGLE['hd']:
            c['hd'] = GOOGLE['hd']
        cuerpo = json.dumps({'id_token': jwt(c), 'access_token': 'x'}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)


class Owrx(Falso):
    def do_POST(self):
        d = {k: v[0] for k, v in parse_qs(self.rfile.read(int(self.headers['Content-Length'])).decode()).items()}
        ref = parse_qs(urlsplit(self.path).query).get('ref', ['/settings'])[0]
        OWRX['logins'].append(d)
        self.send_response(302)
        if d == {'user': 'bricohams-google', 'password': 'clave-servicio'}:
            self.send_header('Set-Cookie', 'owrx-session=' + SESION_OWRX)
            self.send_header('Location', ref)
        else:
            self.send_header('Location', '/login?ref=' + ref)
        self.end_headers()

    def do_GET(self):
        ok = self.path == '/settings/bricohams/auth' and ('owrx-session=' + SESION_OWRX) in (self.headers.get('Cookie') or '')
        self.send_response(200 if ok else 401)
        self.end_headers()


def arrancar(manejador):
    p = libre()
    s = http.server.ThreadingHTTPServer(('127.0.0.1', p), manejador)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, p


_, P_GOOGLE = arrancar(Google)
_, P_OWRX = arrancar(Owrx)
CRED = os.path.join(TMP, 'cred')
os.makedirs(CRED)
for n, v in (('client_secret', 'secreto-de-prueba-123'), ('cookie_key', CLAVE.hex()), ('owrx_password', 'clave-servicio')):
    with open(os.path.join(CRED, n), 'w') as fh:
        fh.write(v + '\n')


def servicio(modo, admins='admin@ejemplo.es,@empresa.es'):
    env = {'GOOGLE_AUTH_MODO': modo, 'GOOGLE_CLIENT_ID': CID, 'GOOGLE_ADMINS': admins, 'GOOGLE_DOMINIO': DOM,
           'GOOGLE_CRED_DIR': CRED, 'GOOGLE_PERMITIR_HTTP_PRUEBAS': '1', 'GOOGLE_AUTH_PORT': str(libre()),
           'GOOGLE_TOKEN_ENDPOINT': 'http://127.0.0.1:%d/token' % P_GOOGLE,
           'GOOGLE_OWRX_URL': 'http://127.0.0.1:%d' % P_OWRX,
           'GOOGLE_MESH_AUTH_URL': 'http://127.0.0.1:%d/settings/bricohams/auth' % P_OWRX}
    cfg = G.Config(env)
    assert cfg.errores() == [], cfg.errores()
    s = G.Servidor(('127.0.0.1', cfg.puerto), G.Manejador)
    s.cfg, s.limite = cfg, G.Limite()
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, cfg.puerto


def pide(puerto, ruta, cab=None, metodo='GET'):
    c = http.client.HTTPConnection('127.0.0.1', puerto, timeout=10)
    c.request(metodo, ruta, headers=dict({'Host': DOM}, **(cab or {})))
    r = c.getresponse()
    cuerpo = r.read().decode('utf-8', 'replace')
    c.close()
    return r.status, r, cuerpo


def galletas(r):
    return {g.split('=', 1)[0]: g for g in r.msg.get_all('Set-Cookie') or []}


def valor(g):
    return g.split(';', 1)[0].split('=', 1)[1]


def entrar_google(puerto, rd_cab='/settings/general', correo='admin@ejemplo.es', hd=''):
    """Recorre login → (Google) → callback; devuelve (estado, respuesta, cuerpo) del callback."""
    st, r, _ = pide(puerto, '/_bh_google/login', {'X-BH-Rd': rd_cab, 'X-Forwarded-For': '203.0.113.7'})
    assert st == 302, st
    loc = urlsplit(r.getheader('Location'))
    q = {k: v[0] for k, v in parse_qs(loc.query).items()}
    assert loc.netloc == 'accounts.google.com' and loc.path == '/o/oauth2/v2/auth'
    assert q['client_id'] == CID and q['response_type'] == 'code' and q['scope'] == 'openid email'
    assert q['code_challenge_method'] == 'S256' and q['redirect_uri'] == 'https://%s/_bh_google/callback' % DOM
    assert 'client_secret' not in loc.query
    g = galletas(r)['bh-google-est']
    assert 'Secure' in g and 'HttpOnly' in g and 'SameSite=Lax' in g and 'Path=/_bh_google/' in g
    codigo = 'codigo-%d' % len(GOOGLE['retos'])
    GOOGLE['retos'][codigo] = (q['code_challenge'], q['nonce'])
    GOOGLE['correo'], GOOGLE['hd'] = correo, hd
    return pide(puerto, '/_bh_google/callback?code=%s&state=%s' % (codigo, q['state']),
                {'Cookie': 'bh-google-est=' + valor(g), 'X-Forwarded-For': '203.0.113.7'})


# ------------------------------------------------------------------ modo doble
srv, P = servicio('doble')
assert pide(P, '/_bh_google/auth')[0] == 401
assert pide(P, '/_bh_google/auth', {'Cookie': 'bh-google=basura.firma'})[0] == 401
assert pide(P, '/_bh_google/entrar?ref=/settings')[0] == 404, 'en doble no hay entrar (hace falta además la contraseña local)'
assert pide(P, '/otra')[0] == 404

st, r, _ = pide(P, '/_bh_google/login?rd=/settings', {'Host': '192.168.1.10'})
assert st == 302 and r.getheader('Location') == 'https://%s/_bh_google/login?rd=%%2Fsettings' % DOM, 'por IP se pasa antes al dominio'
st, r, _ = pide(P, '/_bh_google/login', {'X-BH-Rd': 'https://malo.es/'})
assert st == 302

st, r, cuerpo = entrar_google(P)
assert st == 302 and r.getheader('Location') == '/settings/general', (st, cuerpo)
g = galletas(r)
ses = g['bh-google']
assert 'Secure' in ses and 'HttpOnly' in ses and 'Max-Age=28800' in ses
assert 'Max-Age=0' in g['bh-google-est']
assert r.getheader('Referrer-Policy') == 'no-referrer' and r.getheader('Cache-Control') == 'no-store'
COOKIE = {'Cookie': 'bh-google=' + valor(ses)}
assert pide(P, '/_bh_google/auth', COOKIE)[0] == 204
assert pide(P, '/_bh_google/auth-owrx', COOKIE)[0] == 401, 'Grafana/Meshtastic: además hace falta la sesión de OpenWebRX+'
assert pide(P, '/_bh_google/auth-owrx', {'Cookie': 'owrx-session=' + SESION_OWRX})[0] == 401
assert pide(P, '/_bh_google/auth-owrx', {'Cookie': 'bh-google=%s; owrx-session=%s' % (valor(ses), SESION_OWRX)})[0] == 204

# cuenta fuera de la lista, dominio de Workspace y estado manipulado
st, r, cuerpo = entrar_google(P, correo='intruso@gmail.com')
assert st == 403 and 'intruso@gmail.com' in cuerpo and 'bh-google' not in {k for k in galletas(r) if 'Max-Age=0' not in galletas(r)[k]}
st, r, cuerpo = entrar_google(P, correo='<b>x</b>@empresa.es')
assert st == 403 and '<b>x</b>' not in cuerpo
st, r, _ = entrar_google(P, correo='pepa@empresa.es', hd='empresa.es')
assert st == 302 and 'bh-google' in galletas(r)
st, r, _ = entrar_google(P, correo='pepa@empresa.es', hd='')
assert st == 403
st, _, _ = pide(P, '/_bh_google/callback?code=x&state=otro', {'Cookie': 'bh-google-est=' + G.firmar(CLAVE, 'est', {'s': 's1', 'n': 'n', 'v': 'v', 'r': '/', 'x': time.time() + 60})})
assert st == 400
assert pide(P, '/_bh_google/callback?code=x&state=s1')[0] == 400, 'sin cookie de estado no hay canje'
st, _, _ = pide(P, '/_bh_google/callback?error=access_denied&state=s1', {'Cookie': 'bh-google-est=' + G.firmar(CLAVE, 'est', {'s': 's1', 'n': 'n', 'v': 'v', 'r': '/', 'x': time.time() + 60})})
assert st == 403
st, _, _ = pide(P, '/_bh_google/callback?code=desconocido&state=s1', {'Cookie': 'bh-google-est=' + G.firmar(CLAVE, 'est', {'s': 's1', 'n': 'n', 'v': 'v', 'r': '/', 'x': time.time() + 60})})
assert st == 403, 'Google rechaza el código (PKCE o código falso)'
st, r, _ = pide(P, '/_bh_google/salir', COOKIE)
assert st == 302 and all('Max-Age=0' in v for v in galletas(r).values())
# quitar a alguien de GOOGLE_ADMINS invalida su cookie en el siguiente reinicio
srv.cfg.admins = ['otra@ejemplo.es']
assert pide(P, '/_bh_google/auth', COOKIE)[0] == 401
srv.shutdown()
# límite de intentos por IP
lim = G.Limite(3, 60)
assert [lim.permite('1.2.3.4') for _ in range(4)] == [True, True, True, False] and lim.permite('5.6.7.8')
print('ok · modo doble')

# ------------------------------------------------------------------ modo solo_google
srv, P = servicio('solo_google')
st, r, _ = pide(P, '/_bh_google/entrar?ref=/settings/general')
assert st == 302 and r.getheader('Location') == '/_bh_google/login?rd=%2F_bh_google%2Fentrar%3Fref%3D%252Fsettings%252Fgeneral'
st, r, _ = entrar_google(P, rd_cab='/_bh_google/entrar?ref=%2Fsettings%2Fgeneral')
assert st == 302 and r.getheader('Location') == '/_bh_google/entrar?ref=%2Fsettings%2Fgeneral'
COOKIE = {'Cookie': 'bh-google=' + valor(galletas(r)['bh-google'])}
st, r, _ = pide(P, '/_bh_google/entrar?ref=%2Fsettings%2Fgeneral', COOKIE)
assert st == 302 and r.getheader('Location') == '/settings/general'
o = galletas(r)['owrx-session']
assert valor(o) == SESION_OWRX and 'Secure' in o and 'HttpOnly' in o
assert OWRX['logins'][-1] == {'user': 'bricohams-google', 'password': 'clave-servicio'}
st, r, _ = pide(P, '/_bh_google/entrar?ref=https://malo.es/', COOKIE)
assert st == 302 and r.getheader('Location') == '/settings'
srv.cfg.owrx_clave = 'mala'
st, _, _ = pide(P, '/_bh_google/entrar', COOKIE)
assert st == 502, 'clave de servicio rechazada: no se inventa sesión'
srv.shutdown()
print('ok · modo solo_google')

# ------------------------------------------------------------------ modo alternativa (usuario local o Google)
srv, P = servicio('alternativa')
st, r, _ = pide(P, '/_bh_google/entrar?ref=settings')
assert st == 302 and r.getheader('Location').startswith('/_bh_google/login?rd='), 'sin Google: primero a Google'
st, r, _ = entrar_google(P, rd_cab='/_bh_google/entrar?ref=%2Fsettings')
COOKIE = {'Cookie': 'bh-google=' + valor(galletas(r)['bh-google'])}
st, r, _ = pide(P, '/_bh_google/entrar?ref=settings', COOKIE)
assert st == 302 and r.getheader('Location') == '/settings', 'ref de OpenWebRX+ sin barra inicial'
assert valor(galletas(r)['owrx-session']) == SESION_OWRX
st, r, _ = pide(P, '/_bh_google/entrar', COOKIE)
assert st == 302 and r.getheader('Location') == '/settings', 'el botón del login no lleva ref'
srv.shutdown()
print('ok · modo alternativa')

# ------------------------------------------------------------------ configuración incompleta
cfg = G.Config({'GOOGLE_AUTH_MODO': 'raro', 'GOOGLE_CLIENT_ID': 'x', 'GOOGLE_ADMINS': 'nadie', 'GOOGLE_CRED_DIR': TMP,
                'GOOGLE_SESION_HORAS': 'mucho'})
e = ' | '.join(cfg.errores())
for t in ('GOOGLE_AUTH_MODO', 'GOOGLE_CLIENT_ID', 'GOOGLE_ADMINS', 'client_secret', 'cookie_key', 'dominio', 'GOOGLE_SESION_HORAS'):
    assert t in e, t
assert G.servicio(cfg) == 2
cfg = G.Config({'GOOGLE_CLIENT_ID': CID, 'GOOGLE_ADMINS': 'a@b.es', 'GOOGLE_DOMINIO': DOM, 'GOOGLE_CRED_DIR': CRED})
assert any('https' in x for x in G.Config(dict(GOOGLE_TOKEN_ENDPOINT='http://x/', GOOGLE_CLIENT_ID=CID, GOOGLE_ADMINS='a@b.es',
                                               GOOGLE_DOMINIO=DOM, GOOGLE_CRED_DIR=CRED)).errores())
assert cfg.errores() == [] and cfg.modo == 'alternativa' and cfg.horas == 8, 'por defecto: usuario local o Google'
print('ok · configuración')

# ------------------------------------------------------------------ nginx
S = open(os.path.join(RAIZ, 'install.sh'), encoding='utf-8').read()
FUNC = re.search(r'^nginx_sitio\(\) \{.*?^\}', S, re.S | re.M).group(0)
PLANTILLA = open(os.path.join(RAIZ, 'files/nginx/bricohams-sdr.conf.tmpl'), encoding='utf-8').read()
RUTAS_TXT = open(os.path.join(RAIZ, 'files/nginx/bricohams-sdr-rutas.conf'), encoding='utf-8').read()
RUTAS = re.sub(r'(?m)^#@GF@', '', RUTAS_TXT)
bash = shutil.which('bash')
SITIO = None
if bash:
    r = subprocess.run([bash, '-c', FUNC + '\nnginx_sitio "$@"', '_', 'admin', DOM, '/c.pem', '/k.pem'],
                       input=PLANTILLA, capture_output=True, text=True, env=dict(os.environ, MESH_WEB='yes', MESH433_WEB='yes'))
    if r.returncode == 0 and r.stdout.strip():
        SITIO = r.stdout
for modo in ('doble', 'solo_google'):
    a = G.nginx_rutas(RUTAS, modo)
    assert a == G.nginx_rutas(a, modo), 'aplicar dos veces da lo mismo'
    assert G.nginx_quitar(a) == RUTAS, 'quitar deja el fichero como estaba'
    assert a.count('# bricohams-google:inicio') == 1 and a.count('auth_request /_bh_google_auth;') == 3
    assert 'proxy_pass http://127.0.0.1:8077/_bh_google/auth-owrx;' in a and G.AUTH_MESH not in a, 'Grafana pasa por Google'
    assert ('return 302 /_bh_google/entrar?$args;' in a) == (modo == 'solo_google')
    assert a.index('location ~ /\\.(?!well-known/)') < a.index(G.PAGINAS_OWRX) < a.index('\nlocation / {'), 'orden de las regex'
    bloque = a[a.index(G.PAGINAS_OWRX):]
    bloque = bloque[:bloque.index('\n}\n')]
    assert 'sub_filter_once on;' in bloque and 'proxy_set_header Accept-Encoding "";' in bloque, 'el logo sigue en /settings'
    assert 'add_header' not in a[a.index(G.INICIO):a.index(G.FIN)], 'add_header en la location borraría las cabeceras heredadas'
a = G.nginx_rutas(RUTAS, 'alternativa')
assert a == G.nginx_rutas(a, 'alternativa') and G.nginx_quitar(a) == RUTAS
assert 'auth_request /_bh_google_auth' not in a and a.count(G.AUTH_MESH) == RUTAS.count(G.AUTH_MESH) and 'auth-owrx' not in a, 'alternativa: decide la sesión de OpenWebRX+'
assert 'location /_bh_google/ {' in a and '_bh_google_auth' not in a
login = a[a.index('location ~ ^/(login|pwchange)$ {'):]
login = login[:login.index('\n}\n')]
assert "sub_filter '</form>' '</form>" in login and 'href="/_bh_google/entrar"' in login and '$' not in [x for x in login.splitlines() if "sub_filter '</form>'" in x][0], 'nada de la petición en el HTML'
assert 'proxy_set_header Accept-Encoding "";' in login
for modo in ('doble', 'solo_google'):
    assert G.nginx_rutas(a, modo) == G.nginx_rutas(RUTAS, modo), 'cambiar de modo sobre un fichero ya transformado'
rx = re.compile(G.PAGINAS_OWRX.split(' ', 2)[2].rsplit(' ', 1)[0])
for ruta, debe in (('/settings', True), ('/settings/general', True), ('/logout', True), ('/files/delete', True),
                   ('/settings/bricohams/', False), ('/settings/bricohams/grafana/x', False), ('/', False),
                   ('/settingsx', False), ('/static/css/admin.css', False), ('/login', False)):
    assert bool(rx.search(ruta)) == debe, ruta
try:
    G.nginx_rutas('server {}\n', 'doble')
    raise AssertionError('sin anclajes debe fallar')
except ValueError:
    pass
if SITIO:
    s3 = G.nginx_sitio(SITIO, 'alternativa')
    assert G.nginx_quitar(s3) == SITIO and 'auth-owrx' not in s3 and 'files/delete|_bh_google)(/|$) {' in s3
    s2 = G.nginx_sitio(SITIO, 'doble')
    assert s2 == G.nginx_sitio(s2, 'doble') and G.nginx_quitar(s2) == SITIO
    assert s2.count('proxy_pass http://127.0.0.1:8077/_bh_google/auth-owrx;') == 2, 'Meshtastic 8443 y 8444'
    assert 'files/delete|_bh_google)(/|$) {' in s2, 'por HTTP /_bh_google/ también se manda a HTTPS'
    print('ok · nginx (rutas y sitio)')
else:
    print('ok · nginx (rutas; sitio omitido: sin bash)')

# fichero real: aplicar y quitar con la orden «nginx»
fr, fs = os.path.join(TMP, 'rutas.conf'), os.path.join(TMP, 'sitio')
open(fr, 'w').write(RUTAS)
open(fs, 'w').write(SITIO or 'server {\n}\n')
os.chmod(fr, 0o644)
assert G.main(['nginx', '--aplicar', '--modo', 'doble', '--rutas', fr, '--sitio', fs]) == 0
assert '# bricohams-google:inicio' in open(fr).read() and (os.stat(fr).st_mode & 0o777) == 0o644
assert G.main(['nginx', '--quitar', '--rutas', fr, '--sitio', fs]) == 0
assert open(fr).read() == RUTAS and open(fs).read() == (SITIO or 'server {\n}\n')

# ------------------------------------------------------------------ preparar
kit = os.path.join(TMP, 'bricohams.env')
open(kit, 'w').write('SSL_DOMAIN="%s"\nSSL_MODO="admin"\nGOOGLE_AUTH="no"\n' % DOM)
assert G.preparar(kit) == 3
G.escribir_env(kit, {'GOOGLE_AUTH': 'yes', 'GOOGLE_CLIENT_ID': CID, 'GOOGLE_ADMINS': 'a@ejemplo.es', 'GOOGLE_AUTH_MODO': 'doble'})
assert G.preparar(kit) == 4, 'sin client_secret no se activa'
assert os.path.isfile(os.path.join(G.CRED_DIR_ETC, 'cookie_key'))
open(os.path.join(G.CRED_DIR_ETC, 'client_secret'), 'w').write('secreto\n')
assert G.preparar(kit) == 0
env = G.leer_env(G.ENV_SERVICIO)
assert env['GOOGLE_DOMINIO'] == DOM and env['GOOGLE_CLIENT_ID'] == CID and 'secreto' not in open(G.ENV_SERVICIO).read()
u = open(G.UNIDAD).read()
assert 'DynamicUser=yes' in u and 'LoadCredential=client_secret:' in u and 'owrx_password' not in u
creadas = []
G.escribir_env(kit, {'GOOGLE_AUTH_MODO': 'solo_google'})
assert G.preparar(kit, crear_cuenta=lambda k, us, cl: creadas.append((us, cl)) or 'adduser') == 0
assert creadas and creadas[0][0] == 'bricohams-google' and len(creadas[0][1]) >= 40
assert open(os.path.join(G.CRED_DIR_ETC, 'owrx_password')).read().strip() == creadas[0][1]
assert 'LoadCredential=owrx_password:' in open(G.UNIDAD).read()
assert G.preparar(kit, crear_cuenta=lambda *a: creadas.append('otra') or 'adduser') == 0 and len(creadas) == 1, 'la cuenta se crea una vez'
if os.name == 'posix':
    assert (os.stat(G.CRED_DIR_ETC).st_mode & 0o777) == 0o700
    assert (os.stat(os.path.join(G.CRED_DIR_ETC, 'cookie_key')).st_mode & 0o777) == 0o600
G.escribir_env(kit, {'SSL_MODO': 'no'})
assert G.preparar(kit) == 4, 'sin HTTPS no se activa'
G.escribir_env(kit, {'SSL_MODO': 'admin'})
print('ok · preparar')

# ------------------------------------------------------------------ aplicar (lo lanza el panel Seguridad)
import argparse
ordenes = []


def falsa(fallan=()):
    def orden(cli):
        ordenes.append(cli)
        return (1, 'nginx: [emerg] prueba') if tuple(cli[:2]) in fallan or tuple(cli[:3]) in fallan else (0, '')
    return orden


AP = argparse.Namespace(kit_env=kit, rutas=fr, sitio=fs)
assert G.aplicar(AP, falsa()) == 0
assert 'auth_request /_bh_google_auth;' in open(fr).read(), 'solo_google aplicado'
assert ['systemctl', 'reload', 'nginx'] in ordenes and ['systemctl', 'enable', 'bricohams-google-auth.service'] in ordenes
est = json.load(open(G.ESTADO_JSON))
assert est['ok'] and est['modo'] == 'solo_google'
G.escribir_env(kit, {'GOOGLE_AUTH_MODO': 'alternativa'})
antes = open(fr).read()
assert G.aplicar(AP, falsa({('nginx', '-t')})) == 4
assert open(fr).read() == antes, 'nginx -t falla: los ficheros vuelven a como estaban'
assert not json.load(open(G.ESTADO_JSON))['ok']
assert G.aplicar(AP, falsa()) == 0 and 'Entrar con Google' in open(fr).read() and 'auth_request /_bh_google_auth' not in open(fr).read()
del ordenes[:]
assert G.aplicar(AP, falsa({('systemctl', 'is-active', '--quiet')})) == 4, 'sin pasarela no se exige Google'
assert open(fr).read() == RUTAS and ['systemctl', 'disable', '--now', 'bricohams-google-auth.service'] in ordenes
G.escribir_env(kit, {'GOOGLE_AUTH': 'no'})
assert G.aplicar(AP, falsa()) == 0 and open(fr).read() == RUTAS
assert json.load(open(G.ESTADO_JSON))['modo'] == 'local'
G.escribir_env(kit, {'GOOGLE_AUTH': 'yes', 'GOOGLE_ADMINS': ''})
assert G.aplicar(AP, falsa()) == 4 and open(fr).read() == RUTAS, 'configuración incompleta: nginx sin tocar'
assert G.aplicar(argparse.Namespace(kit_env=kit, rutas=fr + '.no', sitio=fs), falsa()) == 4
assert G.main(['instalar-aplicar', '--kit-env', '/opt/bricohams/kit/bricohams.env']) == 0
u = open(G.UNIDAD_APLICAR).read()
assert 'Type=oneshot' in u and 'aplicar --kit-env /opt/bricohams/kit/bricohams.env' in u
assert G.main(['instalar-aplicar', '--kit-env', '/x; rm -rf /']) == 4 and G.main(['instalar-aplicar', '--kit-env', 'rel.env']) == 4
print('ok · aplicar')

shutil.rmtree(TMP, ignore_errors=True)
# --- dónde se configura: --help, páginas de la pasarela y botón de /login
assert '/settings/bricohams/seguridad' in G.AYUDA_CONFIG and '_bh_google/callback' in G.AYUDA_CONFIG and '--desactivar' in G.AYUDA_CONFIG
assert 'Métodos de acceso de administradores' in G.PAGINA and 'href="/login"' in G.PAGINA
assert 'Métodos de acceso de administradores' in G.BOTON_GOOGLE and "'" not in G.BOTON_GOOGLE and '$' not in G.BOTON_GOOGLE
print('ok · referencias de configuración')
print('test_google_auth: TODO OK')
