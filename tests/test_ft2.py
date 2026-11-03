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
import re
import shutil
import subprocess
import sys
import tempfile
import time

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

# 2. formato jt9 (líneas sintéticas, sin indicativos reales)
lin = dec.convertir('  12:00:15.00   -9  0.1  1234  CQ N0CALL IM98')
assert lin == '120015  -9  0.1 1234 ~  CQ N0CALL IM98', repr(lin)
assert dec.convertir('  00:00:00.00  -18 -0.3   800  K1ABC N0CALL -12', '120018') == '120018 -18 -0.3  800 ~  K1ABC N0CALL -12'
assert dec.convertir('basura') is None and dec.convertir('') is None and dec.convertir('  12:00:15.00 x y z') is None
# formatos de hora alternativos: HHMMSS, HH:MM:SS, HH:MM:SS.cc, coma decimal, sin sangría, con color ANSI
esperado = '120015  -9  0.1 1234 ~  CQ N0CALL IM98'
for crudo in ('120015  -9  0.1  1234  CQ N0CALL IM98',
              '  12:00:15   -9  0.1  1234  CQ N0CALL IM98',
              '12:00:15.00 -9 0.1 1234 CQ N0CALL IM98',
              '  12:00:15,25   -9  0.1  1234  CQ N0CALL IM98',
              '\x1b[32m  12:00:15.00   -9  0.1  1234.0  CQ N0CALL IM98\x1b[0m'):
    assert dec.convertir(crudo) == esperado, (crudo, dec.convertir(crudo))
assert dec.convertir('  12:00:15.00  +3  -0.4  250  N0CALL K1ABC RR73') == '120015   3 -0.4  250 ~  N0CALL K1ABC RR73'
# misma lectura que Jt9Decoder.parse de OpenWebRX+ (wsjt.py): quita "HHMMSS " y corta por columnas
msg = lin[7:]
assert float(msg[0:3]) == -9 and float(msg[4:8]) == 0.1 and int(msg[9:13]) == 1234 and msg[17:53].strip() == 'CQ N0CALL IM98'

# 2b. ajustes: indicativo (AP), banda de audio y plazo menor que el ciclo
cf = os.path.join(d, 'ft2.conf')
with open(cf, 'w') as f:
    f.write('# prueba\nFT2_CALL="K1ABC"   # comentario\nFT2_HIGH_HZ=4500\n')
conf = dec.leer_conf(cf)
assert conf == {'FT2_CALL': 'K1ABC', 'FT2_HIGH_HZ': '4500'}, conf
for k in ('FT2_CALL', 'FT2_LOW_HZ', 'FT2_HIGH_HZ'):
    os.environ.pop(k, None)
cmd = dec.comando('x.wav', 3, conf)
assert cmd[-1] == 'x.wav' and cmd[cmd.index('--call') + 1] == 'K1ABC'
assert cmd[cmd.index('--low') + 1] == '200' and cmd[cmd.index('--high') + 1] == '4500'
assert '--call' not in dec.comando('x.wav', 3, {'FT2_CALL': 'N0CALL'}) and '--call' not in dec.comando('x.wav', 3, {})
assert '--call' not in dec.comando('x.wav', 3, {'FT2_CALL': 'a b;rm'})
assert dec.comando('x.wav', 3, {})[dec.comando('x.wav', 3, {}).index('--high') + 1] == '5000'
assert dec.numero('99', 3.5, 0.5, dec.PERIODO - 0.05) < dec.PERIODO and dec.numero('zz', 3.5, 0, 9) == 3.5

# 2c. plazo y no apilar procesos (solo con shell POSIX): un «decodium-rx» falso que tarda mucho
if os.name == 'posix' and dec.fcntl:
    falso = os.path.join(d, 'decodium-rx-falso')
    with open(falso, 'w') as f:
        f.write('#!/bin/sh\nsleep 30\n')
    os.chmod(falso, 0o755)
    registro = os.path.join(d, 'ft2.log')
    env = dict(os.environ, DECODIUM_RX=falso, FT2_CONF=os.path.join(d, 'no-existe'), FT2_LOG=registro, FT2_TIMEOUT='1')
    wav0 = os.path.join(d, 'openwebrx-audiochopper-master-1-261004_120015.wav')
    open(wav0, 'wb').close()
    t0 = time.time()
    p = subprocess.run([sys.executable, os.path.join(BIN, 'bricohams-ft2-decode'), wav0], env=env, capture_output=True, text=True)
    assert p.returncode == 0 and p.stdout == '' and time.time() - t0 < 10, (p.returncode, p.stdout, p.stderr)
    assert 'saltado' in open(registro).read() and '120015' in open(registro).read()
    # con el cerrojo ocupado, el trozo siguiente se salta sin lanzar nada
    cerrojo = open(dec.CERROJO, 'a')
    dec.fcntl.flock(cerrojo, dec.fcntl.LOCK_EX | dec.fcntl.LOCK_NB)
    t0 = time.time()
    p = subprocess.run([sys.executable, os.path.join(BIN, 'bricohams-ft2-decode'), wav0], env=env, capture_output=True, text=True)
    cerrojo.close()
    assert p.returncode == 0 and time.time() - t0 < 5 and 'sigue decodificándose' in open(registro).read(), p.stderr

# 2d. aviso del troceador si convierte el intervalo a entero
os.makedirs(os.path.join(r, 'owrx/audio'))
assert patch.revisar_chopper(r).startswith('no se pudo')
with open(os.path.join(r, 'owrx/audio/chopper.py'), 'w') as f:
    f.write('delta = int(self.profile.getInterval()) - 1\n')
assert 'entero' in patch.revisar_chopper(r)
with open(os.path.join(r, 'owrx/audio/chopper.py'), 'w') as f:
    f.write('delta = self.profile.getInterval() - (time.time() % self.profile.getInterval())\n')
assert patch.revisar_chopper(r) is None

# 3. decodificación real (si hay binario): solo la estructura, sin fijar el indicativo de un tercero
binario = os.environ.get('DECODIUM_RX') or shutil.which('decodium-rx')
if not binario:
    for c in (os.path.join(RAIZ, '..', '..', 'build', 'decodium-rx'),):
        if os.path.exists(c):
            binario = c
real = ''
if binario:
    wav = os.path.join(d, 'openwebrx-audiochopper-master-1-261004_120015.wav')
    shutil.copy(os.path.join(RAIZ, 'tests/datos/ft2_261004_120015.wav'), wav)
    out = subprocess.run([sys.executable, os.path.join(BIN, 'bricohams-ft2-decode'), '-d', '3', '-t', '60', wav],
                         env=dict(os.environ, DECODIUM_RX=os.path.abspath(binario), FT2_CONF=os.path.join(d, 'no-existe')),
                         capture_output=True, text=True).stdout
    # la muestra es una emisión FT2 real grabada en el aire (no hay simulador FT2 para regenerarla)
    assert re.match(r'^120015 +-?\d+ +-?\d+\.\d +\d+ ~  CQ \S+', out), out
    real = ' y decodificación real con decodium-rx'
print('OK test_ft2: parche repetible y reversible, formato jt9, ajustes y plazo%s' % real)
