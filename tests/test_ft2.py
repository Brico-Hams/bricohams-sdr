#!/usr/bin/env python3
"""v4 (experimental): FT2 en OpenWebRX+.
 1. El parche se aplica sobre los ficheros reales de OpenWebRX+ 1.2.125
    (copia en tests/datos/owrx), es repetible, compila y se puede quitar.
 2. El adaptador convierte la salida de decodium-rx al formato de jt9 y el
    analizador de FT8/FT4 de OpenWebRX+ (Jt9Decoder) la entiende.
 3. Si hay un decodium-rx compilado (DECODIUM_RX o en el PATH), decodifica
    de verdad el WAV FT2 de prueba (tests/datos/ft2_261004_120015.wav)."""
import importlib.machinery
import importlib.util
import os
import py_compile
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
BIN = os.path.join(RAIZ, 'files/bin')


def cargar(nombre, ruta):
    loader = importlib.machinery.SourceFileLoader(nombre, ruta)
    spec = importlib.util.spec_from_loader(nombre, loader)
    m = importlib.util.module_from_spec(spec)
    loader.exec_module(m)
    return m


patch = cargar('ft2patch', os.path.join(BIN, 'bricohams-ft2-patch.py'))
dec = cargar('ft2dec', os.path.join(BIN, 'bricohams-ft2-decode'))

# 1. parche
d = tempfile.mkdtemp()
shutil.copytree(os.path.join(RAIZ, 'tests/datos/owrx'), os.path.join(d, 'r'))
r = os.path.join(d, 'r')
orig = {f: open(os.path.join(r, f)).read() for f in ('owrx/wsjt.py', 'owrx/modes.py', 'htdocs/lib/MessagePanel.js')}
assert patch.main(['x', '--raiz', r, '--silencioso']) == 0
once = {f: open(os.path.join(r, f)).read() for f in orig}
assert patch.main(['x', '--raiz', r, '--silencioso']) == 0
assert once == {f: open(os.path.join(r, f)).read() for f in orig}, 'el parche no es repetible'
w = once['owrx/wsjt.py']
assert 'class Ft2Profile(WsjtProfile)' in w and 'return 3.75' in w and 'elif mode == "ft2"' in w
assert 'WsjtMode("ft2", "FT2")' in once['owrx/modes.py'] and "'FT2'];" in once['htdocs/lib/MessagePanel.js']
py_compile.compile(os.path.join(r, 'owrx/wsjt.py'), doraise=True)
py_compile.compile(os.path.join(r, 'owrx/modes.py'), doraise=True)
assert patch.main(['x', '--raiz', r, '--quitar', '--silencioso']) == 0
assert orig == {f: open(os.path.join(r, f)).read() for f in orig}, 'quitar el parche no deja los ficheros como estaban'

# 2. formato jt9
lin = dec.convertir('  12:00:15.00   -9  0.1  1234  CQ EA5KAO IM98')
assert lin == '120015  -9  0.1 1234 ~  CQ EA5KAO IM98', repr(lin)
assert dec.convertir('  00:00:00.00  -18 -0.3   800  EA5KGV EA5KAO -12', '120018') == '120018 -18 -0.3  800 ~  EA5KGV EA5KAO -12'
assert dec.convertir('basura') is None
# misma lectura que Jt9Decoder.parse de OpenWebRX+ (wsjt.py): quita "HHMMSS " y corta por columnas
msg = lin[7:]
assert float(msg[0:3]) == -9 and float(msg[4:8]) == 0.1 and int(msg[9:13]) == 1234 and msg[17:53].strip() == 'CQ EA5KAO IM98'

# 3. decodificación real (si hay binario)
binario = os.environ.get('DECODIUM_RX') or shutil.which('decodium-rx')
if not binario:
    for c in (os.path.join(RAIZ, '..', '..', 'build', 'decodium-rx'),):
        if os.path.exists(c):
            binario = c
real = ''
if binario:
    wav = os.path.join(d, 'openwebrx-audiochopper-master-1-261004_120015.wav')
    shutil.copy(os.path.join(RAIZ, 'tests/datos/ft2_261004_120015.wav'), wav)
    out = subprocess.run([sys.executable, os.path.join(BIN, 'bricohams-ft2-decode'), '-d', '3', wav],
                         env=dict(os.environ, DECODIUM_RX=os.path.abspath(binario)), capture_output=True, text=True).stdout
    assert 'CQ EA5KAO IM98' in out and out.startswith('120015'), out
    real = ' y decodificación real con decodium-rx'
print('OK test_ft2: parche repetible y reversible, formato jt9%s' % real)
