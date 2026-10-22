#!/usr/bin/env python3
"""Pruebas de registro voluntario, privacidad, límites y endpoint HTTP."""
import http.client
import importlib.machinery
import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import threading
from http.server import ThreadingHTTPServer

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
loader = importlib.machinery.SourceFileLoader('api_registro', os.path.join(RAIZ, 'files/bin/bricohams-api.py'))
spec = importlib.util.spec_from_loader('api_registro', loader)
api = importlib.util.module_from_spec(spec)
loader.exec_module(api)

assert api.validar_registro_oyente({'identificador': 'ea5abc', 'consentimiento': True}) == ('EA5ABC', 'indicativo')
assert api.validar_registro_oyente({'identificador': 'José Pérez', 'consentimiento': True}) == ('José Pérez', 'nombre')
assert api.validar_registro_oyente({'identificador': 'EA5ABC', 'consentimiento': 1}) is None
assert api.validar_registro_oyente({'identificador': '<script>alert(1)</script>', 'consentimiento': True}) is None
assert api.validar_registro_oyente({'identificador': 'A' * 121, 'consentimiento': True}) is None

tmp = tempfile.mkdtemp()
reloj = [1_790_000_000]
db_path = os.path.join(tmp, 'oyentes.sqlite')
registros = api.RegistroOyentes(db_path, reloj=lambda: reloj[0])
if os.name == 'posix':
    assert stat.S_IMODE(os.stat(db_path).st_mode) == 0o600
assert registros.registrar({'identificador': 'ea5abc', 'consentimiento': True})
reloj[0] += 181 * 86400
assert registros.registrar({'identificador': 'José Pérez', 'consentimiento': True})
assert [r[0] for r in registros.listar()] == ['José Pérez'], 'la retención elimina registros vencidos'
columnas = {r[1] for r in registros.c.execute('PRAGMA table_info(registro_oyentes)')}
assert 'ip' not in columnas and 'direccion_ip' not in columnas, columnas

cache = api.Cache(os.path.join(tmp, 'cache.sqlite'))
hamqth = api.HamQTH('', '')
qrz = api.Qrz('', '')
manejador = api.crear_manejador(cache, hamqth, qrz, api.CacheFichas(), registros)
server = ThreadingHTTPServer(('127.0.0.1', 0), manejador)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
port = server.server_address[1]
origin = 'http://127.0.0.1:%d' % port


def solicitud(datos, cabeceras=None, ruta='/bricohams/api/oyentes'):
    conn = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
    body = json.dumps(datos) if datos is not None else ''
    headers = {'Content-Type': 'application/json', 'Origin': origin}
    headers.update(cabeceras or {})
    conn.request('POST', ruta, body=body, headers=headers)
    response = conn.getresponse()
    resultado = response.status, response.read()
    conn.close()
    return resultado


try:
    estado, cuerpo = solicitud({'identificador': 'EA5XYZ', 'consentimiento': True})
    assert estado == 201 and json.loads(cuerpo) == {'ok': True}, (estado, cuerpo)
    estado, _ = solicitud({'identificador': 'EA5BAD', 'consentimiento': False})
    assert estado == 400
    estado, _ = solicitud({'identificador': 'EA5BAD', 'consentimiento': True},
                          {'Origin': 'https://otro.example'})
    assert estado == 403
    estado, _ = solicitud({'identificador': 'EA5BAD', 'consentimiento': True},
                          {'Content-Type': 'text/plain'})
    assert estado == 415
    estado, _ = solicitud({'identificador': 'EA5BAD', 'consentimiento': True},
                          ruta='/bricohams/api/otro')
    assert estado == 404
finally:
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)

registros.c.close()
cache.c.close()
env = os.environ.copy()
env['STATE_DIRECTORY'] = tmp
registros = api.RegistroOyentes(db_path)
registros.registrar({'identificador': 'EA5CSV', 'consentimiento': True})
registros.c.close()
cli = os.path.join(RAIZ, 'files/bin/bricohams-oyentes')
salida = subprocess.run([sys.executable, cli, '--csv'], env=env, capture_output=True, text=True, check=True).stdout
assert 'EA5CSV,indicativo,' in salida and 'fecha_hora_local' in salida, salida
print('OK test_registro_oyentes: consentimiento, validación, endpoint mismo-origen, privacidad, retención y consulta local')
