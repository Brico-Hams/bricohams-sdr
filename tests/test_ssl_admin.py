#!/usr/bin/env python3
"""v4.2 · SSL_MODO (decisión de EA5KAO: «el certificado SSL es solo para la página de settings»).
Genera el sitio de nginx con nginx_sitio (la función real de install.sh) en los tres modos y,
si hay nginx en la máquina de pruebas, lo arranca de verdad delante de un OpenWebRX+ falso:
  admin → «/» por HTTP sin redirigir; /login, /settings… → 301 a HTTPS; la cookie de sesión
          que sale por HTTPS lleva «Secure» (el navegador no la manda nunca por el HTTP público)
  todo  → todo redirige a HTTPS y hay HSTS
  no    → sin bloque 443"""
import http.client
import http.server
import os
import re
import shutil
import socket
import ssl
import subprocess
import tempfile
import threading
import time

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
S = open(os.path.join(RAIZ, 'install.sh'), encoding='utf-8').read()
PLANTILLA = open(os.path.join(RAIZ, 'files/nginx/bricohams-sdr.conf.tmpl'), encoding='utf-8').read()
RUTAS = open(os.path.join(RAIZ, 'files/nginx/bricohams-sdr-rutas.conf'), encoding='utf-8').read()
FUNC = re.search(r'^nginx_sitio\(\) \{.*?^\}', S, re.S | re.M).group(0)


def sitio(modo, cert='/c.pem', key='/k.pem'):
    r = subprocess.run(['bash', '-c', FUNC + '\nnginx_sitio "$@"', '_', modo, 'sdr.ejemplo.es', cert, key],
                       input=PLANTILLA, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout


ADMIN = ('login', 'logout', 'pwchange', 'settings', 'imageupload', 'clients', 'services', 'ban', 'unban', 'broadcast')
for m in ('admin', 'todo', 'no'):
    c = sitio(m)
    assert not re.search(r'^#@', c, re.M), 'quedan marcas #@ en el modo %s' % m
    assert '__' not in c.replace('__DOMINIO__', ''), m
    assert 'sdr.ejemplo.es' in c and '/.well-known/acme-challenge/' in c
    assert ('listen 443' in c) == (m != 'no'), m
    assert ('Strict-Transport-Security' in c) == (m == 'todo'), 'HSTS solo en «todo» (con HSTS el navegador ya no volvería a HTTP)'
    assert ('location / { return 301 https' in c) == (m == 'todo')
    assert ('location ~ ^/(login' in c) == (m == 'admin')
    assert 'http2 on;' not in c, '«http2 on» no existe en el nginx 1.22 de Bookworm'
assert 'proxy_cookie_flags owrx-session secure' in sitio('admin')
assert subprocess.run(['bash', '-c', FUNC + '\nnginx_sitio raro a b c'], input='', capture_output=True).returncode == 1
rx = re.search(r'location ~ \^/\(([^)]*)\)', sitio('admin')).group(1).split('|')
for r in ADMIN:
    assert r in rx, r
assert 'X-Forwarded-Proto $scheme' in RUTAS and 'X-Forwarded-For $remote_addr' in RUTAS
assert 'case "$modo" in admin|todo|no)' in S and 'SSL_MODO="admin"' in open(os.path.join(RAIZ, 'bricohams.env.example'), encoding='utf-8').read()
assert 'nginx -t || fallo' in S


# ------------------------------------------------------------------ prueba real con nginx (si lo hay)
def libre():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p


nginx = shutil.which('nginx')
real = False
if nginx and os.geteuid() == 0:
    d = tempfile.mkdtemp()
    subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1', '-subj', '/CN=t',
                    '-keyout', d + '/k.pem', '-out', d + '/c.pem'], capture_output=True, check=True)
    p_owrx, p_http, p_https = libre(), libre(), libre()

    class Owrx(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Set-Cookie', 'owrx-session=abc123; Path=/')
            self.send_header('X-Proto', self.headers.get('X-Forwarded-Proto', ''))
            self.end_headers()
            self.wfile.write(b'owrx ' + self.path.encode())

        def log_message(self, *a):
            pass

    srv = http.server.ThreadingHTTPServer(('127.0.0.1', p_owrx), Owrx)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    rutas = RUTAS.replace('127.0.0.1:8073', '127.0.0.1:%d' % p_owrx).replace('/var/log/nginx/bricohams-sdr.access.log', d + '/a.log')
    open(d + '/rutas.conf', 'w').write(rutas)
    c = sitio('admin', d + '/c.pem', d + '/k.pem').replace('/etc/nginx/snippets/bricohams-sdr-rutas.conf', d + '/rutas.conf')
    c = '\n'.join(l for l in c.splitlines() if '[::]' not in l)
    c = c.replace('listen 80;', 'listen 127.0.0.1:%d;' % p_http).replace('listen 443 ssl http2;', 'listen 127.0.0.1:%d ssl http2;' % p_https)
    # el resto de bloques (p. ej. cliente web de Meshtastic en :8443) a puertos libres: en un servidor real ya están ocupados
    c = re.sub(r'listen (\d+)(?=[ ;])', lambda mm: 'listen 127.0.0.1:%d' % libre(), c)
    open(d + '/site.conf', 'w').write(c)
    open(d + '/nginx.conf', 'w').write('daemon off; pid %s/n.pid; error_log %s/e.log;\nevents{}\nhttp{ access_log off; include %s/site.conf; }\n' % (d, d, d))
    t = subprocess.run([nginx, '-t', '-c', d + '/nginx.conf', '-p', d], capture_output=True, text=True)
    assert t.returncode == 0, t.stderr
    proc = subprocess.Popen([nginx, '-c', d + '/nginx.conf', '-p', d], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1.0)

        def get(path, https=False):
            if https:
                cx = http.client.HTTPSConnection('127.0.0.1', p_https, context=ssl._create_unverified_context(), timeout=5)
            else:
                cx = http.client.HTTPConnection('127.0.0.1', p_http, timeout=5)
            cx.request('GET', path, headers={'Host': 'sdr.ejemplo.es'})
            r = cx.getresponse(); r.read()
            return r

        r = get('/')
        assert r.status == 200 and r.getheader('X-Proto') == 'http', 'el receptor público va por HTTP'
        assert 'secure' not in (r.getheader('Set-Cookie') or '').lower()
        for path in ('/login', '/settings', '/settings/sdr/rtl', '/logout', '/clients', '/pwchange'):
            r = get(path)
            assert r.status == 301 and r.getheader('Location') == 'https://sdr.ejemplo.es' + path, (path, r.status, r.getheader('Location'))
        for path in ('/map', '/features', '/static/x.js', '/status.json', '/settingsx'):
            assert get(path).status == 200, path
        r = get('/login', https=True)
        ck = (r.getheader('Set-Cookie') or '').lower()
        assert r.status == 200 and 'secure' in ck and 'httponly' in ck and r.getheader('X-Proto') == 'https', ck
        # v4.4 · blindaje: límite de intentos de /login, sin versión de nginx, cabeceras y ficheros ocultos
        estados = [get('/login', https=True).status for _ in range(12)]
        assert 429 in estados and estados[0] == 200, estados
        assert get('/', https=True).status == 200, 'el límite es solo para /login'
        r = get('/')
        assert r.getheader('Server') == 'nginx' and r.getheader('X-Frame-Options') == 'SAMEORIGIN', (r.getheader('Server'), r.getheader('X-Frame-Options'))
        assert 'geolocation=()' in (r.getheader('Permissions-Policy') or '')
        for oculto in ('/.git/config', '/bricohams/.env', '/.htpasswd'):
            assert get(oculto).status == 404, oculto
        real = True
    finally:
        proc.terminate(); proc.wait(5); srv.shutdown()
        shutil.rmtree(d, ignore_errors=True)

print('OK test_ssl_admin: modos admin/todo/no%s; /login y /settings forzados a HTTPS, receptor por HTTP, cookie Secure; v4.4: /login limitado (429), sin versión, X-Frame-Options y ocultos 404' %
      (' probados con nginx real' if real else ' (sin nginx: solo la plantilla)'))
