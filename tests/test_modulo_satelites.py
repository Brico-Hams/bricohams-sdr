#!/usr/bin/env python3
"""install.sh --modulo satelites: solo satélites y agenda sobre un OpenWebRX+ existente.

Ejecuta de verdad en bash la función que registra los plugins en init.js:
  - sin init.js crea uno que carga utils, doppler y satelites;
  - con el init.js de serie añade un bloque marcado sin tocar el resto y es idempotente;
  - con el init.js completo de BricoHams no cambia nada (ya carga los dos plugins);
y comprueba que la opción rechaza combinaciones y nombres desconocidos antes de tocar el sistema."""
import os
import re
import shutil
import subprocess
import tempfile

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
INSTALL = os.path.join(RAIZ, 'install.sh')
S = open(INSTALL, encoding='utf-8').read()


def funcion(nombre):
    m = re.search(r'^%s\(\) \{.*?^\}$' % re.escape(nombre), S, re.S | re.M)   # «})();» del JS no cierra
    assert m, nombre
    return m.group(0)


# ------------------------------------------------------------------ estático
assert '--modulo)' in S and 'MODULO=""' in S
assert 'if [ "$MODULO" = satelites ]; then modulo_satelites; exit 0; fi' in S
modulo = funcion('modulo_satelites')
assert 'paso_satelites' in modulo and 'init_js_satelites' in modulo
assert 'OWRX_BACKEND:-native}" = native' in modulo and 'coords_ok' in modulo
for ajeno in ('paso_plugins', 'paso_configuracion', 'paso_web', 'paso_openwebrx'):
    assert ajeno not in modulo, 'el módulo no debe tocar ' + ajeno
assert S.index('if [ "$MODULO" = satelites ]') < S.index('for PASO_ACTUAL in "${PASOS[@]}"'), \
    'el módulo debe terminar antes del bucle de pasos'

# ------------------------------------------------------------------ init.js en una carpeta temporal
tmp = tempfile.mkdtemp()
htdocs = os.path.join(tmp, 'htdocs')
receiver = os.path.join(htdocs, 'plugins', 'receiver')
os.makedirs(receiver)
init = os.path.join(receiver, 'init.js')


def registrar():
    script = 'HTDOCS=%s\nbien() { echo "OK $*"; }\n%s\ninit_js_satelites\n' % (htdocs.replace('\\', '/'), funcion('init_js_satelites'))
    r = subprocess.run(['bash', '-c', script], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    return r.stdout


def leer():
    with open(init, encoding='utf-8') as f:
        return f.read()


registrar()
creado = leer()
assert creado.count('// >>> bricohams-satelites') == 1 and creado.count('// <<< bricohams-satelites') == 1
assert "['doppler', 'satelites']" in creado and "/utils/utils.js" in creado

serie = "// init.js de serie\nPlugins.load(rp_url + '/utils/utils.js').then(async function () {\n});\n"
with open(init, 'w', encoding='utf-8') as f:
    f.write(serie)
registrar()
primera = leer()
assert primera.startswith(serie), 'el init.js existente debe quedar intacto'
registrar()
assert leer() == primera, 'repetir el módulo no debe duplicar el bloque'
assert primera.count('// >>> bricohams-satelites') == 1
assert any(n.startswith('init.js.antes-') for n in os.listdir(receiver)), 'debe guardar copia previa'
if shutil.which('node'):
    r = subprocess.run(['node', '--check', init], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr

completo = "const PluginsToLoad = [];\nfor (const name of ['meteo', 'satelites']) {}\n"
with open(init, 'w', encoding='utf-8') as f:
    f.write(completo)
assert 'ya carga' in registrar()
assert leer() == completo, 'el init.js completo de BricoHams no se toca'
shutil.rmtree(tmp)

# ------------------------------------------------------------------ opciones, antes de tocar el sistema
for argumentos, mensaje in (
        (['--modulo'], 'necesita el nombre'),
        (['--modulo', 'meteo'], 'Módulo desconocido'),
        (['--modulo', 'satelites', '--solo', 'web'], 'no se combina'),
        (['--modulo', 'satelites', '--actualizar'], 'no se combina')):
    r = subprocess.run(['bash', INSTALL] + argumentos, capture_output=True, text=True, timeout=30)
    assert r.returncode != 0 and mensaje in r.stderr, (argumentos, r.stderr)

print('OK: --modulo satelites registra doppler y satelites en init.js sin tocar el resto, es idempotente y valida sus opciones')
