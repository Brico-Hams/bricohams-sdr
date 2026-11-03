#!/usr/bin/env python3
"""Banner raíz de OpenWebRX+: visitas, IP propia enmascarada, país local opcional, identidad y paleta oficial."""
import http.client
import importlib.machinery
import importlib.util
import json
import os
import re
import subprocess
import tempfile
import threading
from http.server import ThreadingHTTPServer

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
loader = importlib.machinery.SourceFileLoader('api_banner', os.path.join(RAIZ, 'files/bin/bricohams-api.py'))
spec = importlib.util.spec_from_loader('api_banner', loader)
api = importlib.util.module_from_spec(spec)
loader.exec_module(api)


def leer(*ruta):
    with open(os.path.join(RAIZ, *ruta), encoding='utf-8') as f:
        return f.read()


class GeoFalso:
    def __init__(self, tabla):
        self.tabla = tabla

    def pais(self, ip):
        return self.tabla.get(ip)


tmp = tempfile.mkdtemp()
cache = api.Cache(os.path.join(tmp, 'c.sqlite'))
reg = api.RegistroOyentes(os.path.join(tmp, 'o.sqlite'))
cont = api.ContadorVisitas(os.path.join(tmp, 'v.sqlite'))


def servidor(geo):
    srv = ThreadingHTTPServer(('127.0.0.1', 0), api.crear_manejador(
        cache, api.HamQTH('', ''), api.Qrz('', ''), api.CacheFichas(), reg, cont, geo=geo))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def mi_ip(srv, ip):
    c = http.client.HTTPConnection('127.0.0.1', srv.server_address[1], timeout=5)
    c.request('GET', '/bricohams/api/mi-ip', headers={'X-Forwarded-For': ip})
    r = c.getresponse()
    out = r.status, json.loads(r.read())
    c.close()
    return out


con_pais = servidor(GeoFalso({'203.0.113.9': 'ES'}))
sin_pais = servidor(GeoFalso({}))
try:
    assert mi_ip(con_pais, '203.0.113.9') == (200, {'ip': '203.0.x.x', 'pais': 'ES'})
    assert mi_ip(sin_pais, '203.0.113.9') == (200, {'ip': '203.0.x.x'}), 'sin base GeoIP el país se omite'
finally:
    for s in (con_pais, sin_pais):
        s.shutdown()
        s.server_close()

# Búsqueda local real: sin módulo/base o IP no pública -> None, sin excepciones ni red
geo = api.PaisLocal(os.path.join(tmp, 'no-existe.mmdb'))
assert geo.pais('203.0.113.9') is None and geo.pais('192.168.1.5') is None and geo.pais('basura') is None


class Lector:
    def __init__(self, d):
        self.d = d

    def get(self, ip):
        return self.d


for dato, esperado in (({'country': {'iso_code': 'FR'}}, 'FR'), ({'country': {'iso_code': '<x>'}}, None), ({}, None), (None, None)):
    g = api.PaisLocal(os.path.join(tmp, 'x.mmdb'))
    g.lector = Lector(dato)
    assert g.pais('8.8.8.8') == esperado, dato
    assert g.pais('10.0.0.1') is None, 'IP privada: sin país'

js = leer('files', 'htdocs', 'plugins', 'receiver', 'visitas', 'visitas.js')
assert subprocess.run(['node', '--check', os.path.join(RAIZ, 'files/htdocs/plugins/receiver/visitas/visitas.js')]).returncode == 0
assert '/bricohams/api/mi-ip' in js and '/bricohams/api/visitas' in js, 'reutiliza los endpoints existentes'
assert "'bh_visita'" in js and "'bh_visita'" in leer('files', 'web', 'index.html.tmpl').replace('"', "'"), 'misma clave anti-duplicado que la portada'
assert 'webrx-rx-desc' in js and 'webrx-rx-title' in js and 'bh:identidad' in js
assert 'no disponible' in js and 'identidad' in js and 'aria-live' in js
assert 'role="button"' in js and 'id="bh-visitas-pop"' in js and 'id="bh-banner-info"' in js
assert 'propia.identidad' not in js, 'la identidad no viene de la API por IP (IP compartida)'
assert "datos && typeof datos.total === 'number' ? datos.total : total" in js, 'API en 0 no pisa el histórico de visitas.json'
assert "_version = '1.2.0'" in js
assert 'bh:identidad' in leer('files', 'htdocs', 'plugins', 'receiver', 'identificacion', 'identificacion.js')
assert re.search(r'https?://', js) is None, 'sin servicios de terceros'

# Paleta oficial: sin el naranja antiguo; enlaces accesibles; instalador despliega lo cambiado
for ruta in ('files/web/index.html.tmpl', 'files/web/privacidad.html', 'files/web/politicas.html', 'files/web/clima.html',
             'files/htdocs/plugins/receiver/visitas/visitas.js', 'files/htdocs/plugins/receiver/bricohams/bricohams.js',
             'files/htdocs/plugins/receiver/dvficha/dvficha.js', 'files/htdocs/plugins/receiver/audio_cadena/audio_cadena.js',
             'files/htdocs/plugins/receiver/meteo/meteo.js', 'files/htdocs/plugins/map/init.js',
             'files/bin/bricohams-owrx-botones', 'files/bin/bricohams-mesh-admin'):
    t = leer(*ruta.split('/'))
    assert not re.search(r'(?i)#f26b21|242,\s*107,\s*33', t), 'naranja antiguo en ' + ruta
assert '#F26B1D' in leer('files', 'web', 'index.html.tmpl') and '--link:#AA410B' in leer('files', 'web', 'index.html.tmpl')
assert '#FFA06A' in leer('files', 'web', 'index.html.tmpl') and '#111518' in leer('files', 'web', 'privacidad.html')
# brand manual v1.1: headings in graphite text with the orange accent border
assert 'h2{color:var(--text)' in leer('files', 'web', 'politicas.html') and 'var(--brand-orange)' in leer('files', 'web', 'politicas.html')

inst = leer('install.sh')
assert re.search(r'paso_web\(\) \{\r?\n\s+apt_i nginx certbot openssl python3-maxminddb', inst), 'la API necesita maxminddb'
for destino in ('files/web/index.html.tmpl', 'files/web/privacidad.html', 'files/web/politicas.html', 'files/web/clima.html',
                'files/bin/bricohams-api.py', 'files/bin/bricohams-owrx-botones', 'files/bin/bricohams-mesh-admin'):
    assert destino.replace('files/', '$FILES/') in inst, 'el instalador no despliega ' + destino
assert 'visitas' in inst.split('PASOS=(')[1].split(')')[0].split()

print('OK test_banner_visitas: banner raíz, país local opcional, identidad, sin doble conteo, paleta y despliegue')
