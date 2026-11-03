#!/usr/bin/env python3
"""Vínculo interno IP completa -> identidad elegida: máscara, proxy de confianza, retención 0600, aviso de Telegram
con identidad (también si llega después, sin aviso de llegada duplicado), tarjeta propia y nada en lo público."""
import http.client
import importlib.machinery
import importlib.util
import json
import os
import sys
import tempfile
import threading
from http.server import ThreadingHTTPServer

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(RAIZ, 'files', 'bin'))
import bricohams_conexiones as cx


def cargar(nombre, fichero):
    loader = importlib.machinery.SourceFileLoader(nombre, os.path.join(RAIZ, 'files/bin', fichero))
    spec = importlib.util.spec_from_loader(nombre, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


vis = cargar('vis_cx', 'bricohams-visitas.py')
api = cargar('api_cx', 'bricohams-api.py')

# Máscaras: IPv4 con exactamente los dos primeros octetos, IPv6 con los tres primeros grupos
assert cx.enmascarar('82.160.12.7') == '82.160.x.x' == api.enmascarar_ip('82.160.12.7') == vis.ip_parcial('82.160.12.7')
assert cx.enmascarar('2a01:4f8:1:2::3') == '2a01:4f8:1:x:x:x:x:x' == api.enmascarar_ip('2a01:4f8:1:2::3')
assert vis.ip_parcial('2a01:4f8:1:2::3') == '2a01:4f8:1:x:x:x:x:x'
assert cx.enmascarar('::ffff:82.160.1.1') == '82.160.x.x' and cx.enmascarar('basura') == '?'

# Proxy de confianza: solo un socket local y un único valor válido en X-Forwarded-For
redes = cx.redes_confiables('127.0.0.1,::1')
assert cx.ip_de_proxy('127.0.0.1', ['82.160.12.7'], redes) == '82.160.12.7'
assert cx.ip_de_proxy('198.51.100.5', ['82.160.12.7'], redes) is None, 'spoof desde un socket no confiable'
assert cx.ip_de_proxy('127.0.0.1', ['1.1.1.1, 82.160.12.7'], redes) is None
assert cx.ip_de_proxy('127.0.0.1', ['1.1.1.1', '82.160.12.7'], redes) is None
assert cx.ip_de_proxy('127.0.0.1', ['no-es-ip'], redes) is None and cx.ip_de_proxy('127.0.0.1', None, redes) is None

# Texto de identidad: sin controles ni formato bidi, acotado; Telegram escapado
assert cx.limpiar_identidad('Ana\x00\n\u202e<b>') == 'Ana <b>'
assert len(cx.limpiar_identidad('x' * 500)) == cx.MAX_IDENTIDAD
frag = cx.fragmento('Ana <b>&</b>')
assert '&lt;b&gt;&amp;&lt;/b&gt;' in frag and '<b>Ana' not in frag.replace('<b>Ana &lt;', '')
assert cx.fragmento('') == '' and cx.fragmento('\x1f\x00') == ''

# Almacén: 0600, retención, tope de filas, IP inválida rechazada
tmp = tempfile.mkdtemp()
t = [1_790_000_000]
ruta = os.path.join(tmp, 'c.sqlite')
con = cx.Conexiones(ruta, reloj=lambda: t[0], dias=14, maximo=3)
if os.name == 'posix':
    assert os.stat(ruta).st_mode & 0o777 == 0o600
assert not con.visto('no-es-ip') and not con.identificar('0.0.0.0', 'Ana', 'nombre')
assert con.identificar('203.0.113.9', 'EA5ABC', 'indicativo') and con.identidad('203.0.113.9') == ('EA5ABC', 'indicativo')
t[0] += 15 * 86400
assert con.identidad('203.0.113.9') is None, 'retención corta'
con.visto('203.0.113.10')
assert not con.c.execute('SELECT 1 FROM conexion WHERE ip = ?', ('203.0.113.9',)).fetchone(), 'purgada'
for i in range(10):
    t[0] += 1
    con.visto('203.0.113.%d' % (20 + i))
assert con.c.execute('SELECT COUNT(*) FROM conexion').fetchone()[0] == 3, 'tope de filas'
assert cx.retencion_dias('9999') == 30 and cx.retencion_dias('0') == 1 and cx.retencion_dias('x') == 14

# Daemon: aviso de llegada con identidad conocida, o completado después con una sola edición
enviados, ediciones, ids = [], [], iter(range(100, 200))


class GeoFalsa:
    def buscar(self, ip):
        return {'cc': 'ES', 'pais': 'España', 'ciudad': 'Murcia'}


def enviar_id(texto, callback):
    enviados.append(texto)
    callback(next(ids))


def editar(mensaje_id, texto):
    ediciones.append((mensaje_id, texto))


reloj = [1_790_000_000.0]
db = vis.abrir_db(os.path.join(tmp, 'v.sqlite'))
c2 = cx.Conexiones(os.path.join(tmp, 'c2.sqlite'), reloj=lambda: reloj[0])
v = vis.Visitas(db, GeoFalsa(), lambda x: enviados.append(x), ahora=lambda: reloj[0],
                conexiones=c2, enviar_id=enviar_id, editar=editar)

# 1) identificación posterior a la conexión: un aviso de llegada y una edición, nunca otro aviso
v.evento({'state': 'Connected', 'ip': '82.160.12.7', 'clients': 1})
assert len(enviados) == 1 and '82.160.x.x' in enviados[0] and '👤' not in enviados[0] and '\x1f' not in enviados[0]
assert '82.160.12.7' not in enviados[0]
assert cx.reflejar(c2, '82.160.12.7', 'EA5ABC', 'indicativo', editar)
assert len(enviados) == 1 and len(ediciones) == 1 and ediciones[0][0] == 100
assert '👤 <b>EA5ABC</b>' in ediciones[0][1] and 'Nuevo oyente' in ediciones[0][1] and '82.160.12.7' not in ediciones[0][1]
v.evento({'state': 'Disconnected', 'ip': '82.160.12.7', 'clients': 0})
reloj[0] += 60
v.evento({'state': 'Connected', 'ip': '82.160.12.7', 'clients': 1})
assert len(enviados) == 1, 'reconexión < 10 min: sin otro aviso de llegada'

# 2) identidad previa a la conexión: el aviso ya la lleva, escapada, sin edición
reloj[0] += 3600
cx.reflejar(c2, '151.20.1.1', 'Ana <i>&', 'nombre', editar)
v.evento({'state': 'Connected', 'ip': '151.20.1.1', 'clients': 2})
assert len(enviados) == 2 and '👤 <b>Ana &lt;i&gt;&amp;</b>' in enviados[1] and len(ediciones) == 1

# 3) el nombre del chat identifica si no hay identidad; no pisa una ya elegida
v.evento({'state': 'Connected', 'ip': '90.1.2.3', 'clients': 3})
v.evento({'state': 'ChatMessage', 'ip': '90.1.2.3', 'name': 'Pepe\u202e<b>', 'message': 'hola'})
assert c2.identidad('90.1.2.3') == ('Pepe<b>', 'nombre') and len(ediciones) == 2
assert '👤 <b>Pepe&lt;b&gt;</b>' in ediciones[1][1]
assert sum('Nuevo oyente' in x for x in enviados) == 3, 'solo un aviso de llegada por conexión'
v.evento({'state': 'ChatMessage', 'ip': '82.160.12.7', 'name': 'Otro', 'message': 'hola'})
assert c2.identidad('82.160.12.7')[0] == 'EA5ABC'

# 4) carrera: la identidad llega entre el envío y el id del mensaje -> se completa al guardar el id
pendiente = []
v2 = vis.Visitas(db, GeoFalsa(), lambda x: None, ahora=lambda: reloj[0] + 5000, conexiones=c2,
                 enviar_id=lambda texto, cb: pendiente.append(cb), editar=editar)
v2.evento({'state': 'Connected', 'ip': '95.5.5.5', 'clients': 1})
cx.reflejar(c2, '95.5.5.5', 'N0CALL', 'indicativo', editar)
n = len(ediciones)
pendiente[0](555)
assert len(ediciones) == n + 1 and ediciones[-1][0] == 555 and 'N0CALL' in ediciones[-1][1]

# API: registro con identidad y tarjeta propia (solo enmascarada), nada en lo público
reg = api.RegistroOyentes(os.path.join(tmp, 'o.sqlite'), conexiones=c2, editar=editar)
cont = api.ContadorVisitas(os.path.join(tmp, 'cv.sqlite'))
H = api.crear_manejador(api.Cache(os.path.join(tmp, 'ca.sqlite')), api.HamQTH('', ''), api.Qrz('', ''),
                        api.CacheFichas(), reg, cont)
srv = ThreadingHTTPServer(('127.0.0.1', 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
srv2 = ThreadingHTTPServer(('127.0.0.1', 0), api.crear_manejador(
    api.Cache(os.path.join(tmp, 'cb.sqlite')), api.HamQTH('', ''), api.Qrz('', ''), api.CacheFichas(), reg, cont,
    proxies=frozenset({'10.255.255.1'})))
threading.Thread(target=srv2.serve_forever, daemon=True).start()


def pedir(servidor, metodo, ruta, xff=None, cuerpo=None):
    c = http.client.HTTPConnection('127.0.0.1', servidor.server_address[1], timeout=5)
    cab = {'Content-Type': 'application/json'}
    if xff:
        cab['X-Forwarded-For'] = xff
    c.request(metodo, ruta, body=json.dumps(cuerpo) if cuerpo is not None else None, headers=cab)
    r = c.getresponse()
    out = r.status, r.read().decode()
    c.close()
    return out


try:
    assert pedir(srv, 'GET', '/bricohams/api/mi-ip', '203.0.113.77') == (200, '{"ip": "203.0.x.x"}')
    assert pedir(srv, 'POST', '/bricohams/api/oyentes', '203.0.113.77',
                 {'identificador': 'ea5xyz', 'consentimiento': True})[0] == 201
    estado, cuerpo = pedir(srv, 'GET', '/bricohams/api/mi-ip', '203.0.113.77')
    assert estado == 200 and json.loads(cuerpo) == {'ip': '203.0.x.x'}, 'mi-ip nunca devuelve identidad (IP compartida)'
    assert '203.0.113.77' not in cuerpo and 'EA5XYZ' not in cuerpo
    assert json.loads(pedir(srv, 'GET', '/bricohams/api/mi-ip', '203.0.113.78')[1]) == {'ip': '203.0.x.x'}, 'otra IP no ve la identidad'
    assert c2.identidad('203.0.113.77')[0] == 'EA5XYZ', 'el vínculo interno para Telegram se conserva'
    # Socket no confiable: la IP afirmada se ignora (no se vincula ni se muestra)
    assert pedir(srv2, 'POST', '/bricohams/api/oyentes', '203.0.113.99',
                 {'identificador': 'EA5ZZZ', 'consentimiento': True})[0] == 201
    assert c2.identidad('203.0.113.99') is None and pedir(srv2, 'GET', '/bricohams/api/mi-ip', '203.0.113.99')[0] == 404
    # Registro sin proxy válido o sin consentimiento: sin vínculo
    assert pedir(srv, 'POST', '/bricohams/api/oyentes', '1.1.1.1, 203.0.113.55',
                 {'identificador': 'EA5QQQ', 'consentimiento': True})[0] == 201
    assert c2.identidad('203.0.113.55') is None and c2.identidad('1.1.1.1') is None
    assert pedir(srv, 'POST', '/bricohams/api/oyentes', '203.0.113.56',
                 {'identificador': 'EA5QQQ', 'consentimiento': False})[0] == 400 and c2.identidad('203.0.113.56') is None
    # Nada de IP ni identidad en lo público
    for ruta in ('/bricohams/api/visitas', '/bricohams/api/salud'):
        publico = pedir(srv, 'GET', ruta, '203.0.113.77')[1]
        assert '203.0.113.77' not in publico and 'EA5XYZ' not in publico, ruta
finally:
    srv.shutdown()
    srv2.shutdown()
    srv.server_close()
    srv2.server_close()

assert 'EA5XYZ' not in json.dumps(v.resumen()), 'visitas.json sin identidades'
assert '203.0.113.77' not in open(os.path.join(tmp, 'cv.sqlite'), 'rb').read().decode('latin-1')

print('OK test_conexiones_ip: máscara, proxy de confianza, retención 0600, identidad en el aviso sin duplicados, tarjeta propia')
