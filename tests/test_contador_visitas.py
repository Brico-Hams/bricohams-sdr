#!/usr/bin/env python3
"""Contador de visitas de la portada: agregado público, IP completa solo interna y con retención, IP propia enmascarada, proxy de confianza."""
import http.client
import importlib.machinery
import importlib.util
import json
import os
import re
import tempfile
import threading
from http.server import ThreadingHTTPServer

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
loader = importlib.machinery.SourceFileLoader('api_visitas', os.path.join(RAIZ, 'files/bin/bricohams-api.py'))
spec = importlib.util.spec_from_loader('api_visitas', loader)
api = importlib.util.module_from_spec(spec)
loader.exec_module(api)


def leer(*ruta):
    with open(os.path.join(RAIZ, *ruta), encoding='utf-8') as f:
        return f.read()


tmp = tempfile.mkdtemp()
reloj = [1_790_000_000]
cont = api.ContadorVisitas(os.path.join(tmp, 'v.sqlite'), reloj=lambda: reloj[0])
assert cont.resumen() == {'total': 0, 'hoy': 0}
cont.registrar()
assert cont.registrar() == {'total': 2, 'hoy': 2}
reloj[0] += 86400
assert cont.registrar() == {'total': 3, 'hoy': 1}, 'persiste entre días'
columnas = {r[1] for r in cont.c.execute('PRAGMA table_info(visitas_dia)')}
assert columnas == {'dia', 'n'}, 'solo agregados: %s' % columnas
cont.c.close()
cont = api.ContadorVisitas(os.path.join(tmp, 'v.sqlite'), reloj=lambda: reloj[0])
assert cont.resumen()['total'] == 3, 'persiste tras reiniciar'

cache = api.Cache(os.path.join(tmp, 'c.sqlite'))
reg = api.RegistroOyentes(os.path.join(tmp, 'o.sqlite'))
ips = api.IpVisitas(os.path.join(tmp, 'ip.sqlite'), reloj=lambda: reloj[0], dias=14)
server = ThreadingHTTPServer(('127.0.0.1', 0), api.crear_manejador(
    cache, api.HamQTH('', ''), api.Qrz('', ''), api.CacheFichas(), reg, cont, ips))
threading.Thread(target=server.serve_forever, daemon=True).start()
port = server.server_address[1]
# Segundo servidor cuyo socket NO es proxy de confianza: debe ignorar X-Forwarded-For.
server2 = ThreadingHTTPServer(('127.0.0.1', 0), api.crear_manejador(
    cache, api.HamQTH('', ''), api.Qrz('', ''), api.CacheFichas(), reg, cont, ips, proxies=frozenset({'10.255.255.1'})))
threading.Thread(target=server2.serve_forever, daemon=True).start()
port2 = server2.server_address[1]


def pedir(metodo, cabeceras=None, ruta='/bricohams/api/visitas', puerto=None):
    c = http.client.HTTPConnection('127.0.0.1', puerto or port, timeout=5)
    c.request(metodo, ruta, body='{}' if metodo == 'POST' else None,
              headers=dict({'Content-Type': 'application/json'}, **(cabeceras or {})))
    r = c.getresponse()
    out = r.status, r.read(), r.getheader('Cache-Control')
    c.close()
    return out


def ips_guardadas():
    return {f[0]: f[1] for f in ips.c.execute('SELECT ip, SUM(n) FROM visitas_ip GROUP BY ip')}


try:
    estado, cuerpo, cc = pedir('GET')
    assert estado == 200 and json.loads(cuerpo) == {'total': 3, 'hoy': 1} and cc == 'no-store'
    estado, cuerpo, _ = pedir('POST', {'Origin': 'http://127.0.0.1:%d' % port,
                                       'X-Forwarded-For': '203.0.113.9', 'User-Agent': 'Prueba/1'})
    assert estado == 201 and json.loads(cuerpo) == {'total': 4, 'hoy': 2}
    assert set(json.loads(cuerpo)) == {'total', 'hoy'}, 'no expone datos de otros visitantes'
    assert pedir('POST', {'Origin': 'https://otro.example'})[0] == 403
    assert cont.resumen()['total'] == 4, 'un POST rechazado no cuenta'

    # IP completa: solo interna, validada y desde el proxy de confianza
    assert ips_guardadas() == {'203.0.113.9': 1}
    for malo in ('203.0.113.9, 198.51.100.7', 'no-es-ip', '127.0.0.1', '0.0.0.0', '224.0.0.1', 'fe80::1%eth0', ''):
        pedir('POST', {'X-Forwarded-For': malo})
    assert ips_guardadas() == {'203.0.113.9': 1}, 'listas, basura, loopback y multicast no se guardan: %s' % ips_guardadas()
    pedir('POST', {'X-Forwarded-For': '2001:db8:85a3:8d3:1319:8a2e:370:7348'})
    assert '2001:db8:85a3:8d3:1319:8a2e:370:7348' in ips_guardadas()
    pedir('POST', {'X-Forwarded-For': '203.0.113.50', 'X-Real-IP': '198.51.100.1'}, puerto=port2)
    assert '203.0.113.50' not in ips_guardadas() and '198.51.100.1' not in ips_guardadas(), 'socket no confiable: se ignora'

    # Tarjeta: solo la propia IP, enmascarada; nunca otras ni la completa
    estado, cuerpo, cc = pedir('GET', {'X-Forwarded-For': '203.0.113.9'}, '/bricohams/api/mi-ip')
    assert estado == 200 and json.loads(cuerpo) == {'ip': '203.0.x.x'} and cc == 'private, no-store'
    assert '203.0.113.9' not in cuerpo.decode()
    estado, cuerpo, _ = pedir('GET', {'X-Forwarded-For': '2001:db8:85a3:8d3:1319:8a2e:370:7348'}, '/bricohams/api/mi-ip')
    assert json.loads(cuerpo) == {'ip': '2001:db8:85a3:x:x:x:x:x'}, cuerpo
    assert pedir('GET', {'X-Forwarded-For': '203.0.113.9, 198.51.100.7'}, '/bricohams/api/mi-ip')[0] == 404
    assert pedir('GET', {'X-Forwarded-For': '203.0.113.9'}, '/bricohams/api/mi-ip', port2)[0] == 404, 'spoof sin proxy de confianza'
    assert pedir('GET', None, '/bricohams/api/mi-ip')[0] == 404
    for ruta in ('/bricohams/api/visitas', '/bricohams/api/salud', '/bricohams/api/mi-ip'):
        _, cuerpo, _ = pedir('GET', {'X-Forwarded-For': '203.0.113.9'}, ruta)
        assert b'203.0.113.9' not in cuerpo and b'2001:db8:85a3:8d3' not in cuerpo, 'IP completa en ' + ruta
finally:
    server.shutdown()
    server.server_close()
    server2.shutdown()
    server2.server_close()

assert api.enmascarar_ip('82.160.12.200') == '82.160.x.x'
assert api.enmascarar_ip('2001:db8::1') == '2001:db8:0:x:x:x:x:x'
assert api.ip_valida('::ffff:203.0.113.9') == '203.0.113.9'

# Retención corta: se borra pasado el plazo y el fichero es 0600
reloj[0] += 15 * 86400
ips.purgar()
assert ips_guardadas() == {}, 'IP completa conservada más allá de la retención'
assert api._dias_ip('9999') == 30 and api._dias_ip('0') == 1 and api._dias_ip('x') == 14
if os.name == 'posix':
    assert os.stat(os.path.join(tmp, 'ip.sqlite')).st_mode & 0o777 == 0o600
columnas_ip = {r[1] for r in ips.c.execute('PRAGMA table_info(visitas_ip)')}
assert columnas_ip == {'dia', 'ip', 'n'}, 'sin agente de usuario ni identificadores: %s' % columnas_ip

volcado = ''.join(str(f) for f in cont.c.execute('SELECT * FROM visitas_dia'))
assert '203.0.113.9' not in volcado and 'Prueba' not in volcado

web = leer('files', 'web', 'index.html.tmpl')
for i in ('bh-v-total', 'bh-v-hoy', 'bh-c-nav', 'bh-c-so', 'bh-c-idi', 'bh-c-ip', 'bh-c-id'):
    assert 'id="%s"' % i in web, i
assert 'aria-labelledby' in web and 'aria-live' in web and 'focus-visible' in web
assert 'minmax(250px' in web and 'prefers-reduced-motion' in web
# every inline script of the portal (theme switch first, visitors counter after it)
script = '\n'.join(re.findall(r'<script>(.*?)</script>', web, re.S))
assert re.search(r"https?://", script) is None, 'sin servicios de terceros'
assert 'userAgentData' in script and '/bricohams/api/visitas' in script
assert '__' not in script.replace('__proto__', ''), 'el sed del instalador no debe tocar el script'

rutas = leer('files', 'nginx', 'bricohams-sdr-rutas.conf')
bloque = re.search(r'location = /bricohams/api/visitas \{(.*?)\n\}', rutas, re.S).group(1)
assert 'limit_req zone=bh_visitas' in bloque and 'limit_except GET POST' in bloque
assert 'proxy_set_header X-Forwarded-For $remote_addr;' in bloque, 'nginx sobrescribe X-Forwarded-For'
assert 'X-Real-IP ""' in bloque
bloque_ip = re.search(r'location = /bricohams/api/mi-ip \{(.*?)\n\}', rutas, re.S).group(1)
assert 'proxy_set_header X-Forwarded-For $remote_addr;' in bloque_ip and 'limit_req zone=bh_visitas' in bloque_ip
assert 'limit_except GET {' in bloque_ip and '$proxy_add_x_forwarded_for' not in rutas
assert 'zone=bh_visitas' in leer('files', 'nginx', 'bricohams-sdr.conf.tmpl')
privacidad = leer('files', 'web', 'privacidad.html')
assert 'contador de visitas' in privacidad.lower()
assert '__IP_DIAS__' in privacidad and 'enmascarada' in privacidad and 'IP completa' in privacidad
assert 'ip_dias' in leer('install.sh') and 'VISITAS_IP_DIAS' in leer('bricohams.env.example')
assert "/bricohams/api/mi-ip" in script and 'bh-c-ip' in script

print('OK test_contador_visitas: agregado, IP completa interna con retención, máscara propia, proxy de confianza, plantilla y nginx')
