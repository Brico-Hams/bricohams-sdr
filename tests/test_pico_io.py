#!/usr/bin/env python3
"""v4: puente USB con la Pico «bricohams-io».
 1. El firmware (funciones puras) calcula igual que bricohams-wx (BME280 del datasheet).
 2. PWM invertido, órdenes FAN/PING.
 3. Lluvia: contador de la Pico -> marcas de tiempo, también si la Pico se reinicia.
 4. bricohams-wx y bricohams-fan leen /run/bricohams/io.json.
 5. Prueba completa con un puerto serie virtual (pty): la Pico «simulada» manda
    JSON, bricohams-io escribe io.json y le pasa la orden FAN de bricohams-fan."""
import importlib.machinery
import importlib.util
import json
import os
import pty
import subprocess
import sys
import tempfile
import time

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


def cargar(nombre, ruta):
    loader = importlib.machinery.SourceFileLoader(nombre, ruta)
    spec = importlib.util.spec_from_loader(nombre, loader)
    m = importlib.util.module_from_spec(spec)
    loader.exec_module(m)
    return m


fw = cargar('pico_main', os.path.join(RAIZ, 'firmware/pico-io/main.py'))
wx = cargar('bwx', os.path.join(RAIZ, 'files/bin/bricohams-wx.py'))
io = cargar('bio', os.path.join(RAIZ, 'files/bin/bricohams-io.py'))
fan = cargar('bfan', os.path.join(RAIZ, 'files/bin/bricohams-fan.py'))

# 1. compensación: el mismo ejemplo del datasheet de Bosch que test_wx_bme280
cal = {'T1': 27504, 'T2': 26435, 'T3': -1000, 'P1': 36477, 'P2': -10685, 'P3': 3024, 'P4': 2855, 'P5': 140,
       'P6': -7, 'P7': 15500, 'P8': -14600, 'P9': 6000}
a = fw.compensate(cal, 519888, 415148)
b = wx.compensate(cal, 519888, 415148)
assert abs(a[0] - 25.08) < 0.01 and abs(a[1] - 100653.27) < 0.5 and a == b, (a, b)
raw = bytes(range(26))
assert fw.parse_calib(raw, bytes(range(7))) == wx.parse_calib(raw, bytes(range(7)))

# 2. PWM y órdenes
assert fw.duty_u16(0) == 65535 and fw.duty_u16(100) == 0 and fw.duty_u16(100, invert=False) == 65535
assert fw.parse_cmd('FAN 40 160') == ('FAN', [40, 100])
assert fw.parse_cmd('fan 5 -3') == ('FAN', [5, 0])
assert fw.parse_cmd('PING') == ('PING', []) and fw.parse_cmd('FAN x') == (None, []) and fw.parse_cmd('') == (None, [])
assert fw.rpm(60, 1.0) == 1800

# 3. lluvia
d = tempfile.mkdtemp()
ll = io.Lluvia(os.path.join(d, 'lluvia.json'))
t0 = 1_800_000_000
assert ll.actualizar('A', 5, t0) == 0            # primera lectura: solo fija la referencia
assert ll.actualizar('A', 8, t0 + 60) == 3
assert ll.actualizar('B', 2, t0 + 120) == 2      # reinicio de la Pico: cuenta desde 0
assert ll.actualizar('B', 1, t0 + 180) == 1      # contador hacia atrás: también reinicio
assert len(ll.marcas) == 6
ll.guardar()
pl = wx.PluviometroIO(0.2794, os.path.join(d, 'lluvia.json'))
r = pl.resumen()
assert r['24h'] == 0.0                          # las marcas de prueba son de 2027: fuera de las últimas 24 h de hoy
ll.marcas = [time.time() - 30] * 4
ll.guardar()
assert abs(pl.resumen()['1h'] - 4 * 0.2794) < 0.01

# 4. lectores de io.json
iojson = os.path.join(d, 'io.json')
json.dump({'bme': {'chip': 'BME280', 't': 21.5, 'p': 100500.0, 'h': 50.0}, 'ds': [{'id': '28aa', 't': 33.3}],
           'fan': {'rpm': [1800, 1750], 'duty': [40, 40], 'auto': False}}, open(iojson, 'w'))
s = wx.SensorPico(iojson, esperas=1)
assert s.read() == (21.5, 100500.0, 50.0) and s.chip == 'BME280 (Pico)'
assert fan.io_temp_caja(fan.io_lectura(iojson)) == 33.3
json.dump({'bme': {'error': 'sin BME280'}}, open(iojson, 'w'))
try:
    s.read()
    raise AssertionError('debía fallar sin BME280')
except RuntimeError:
    pass

# 5. puerto serie virtual
try:
    import serial  # noqa: F401
    hay_serial = True
except ImportError:
    hay_serial = False
if hay_serial:
    m, sl = pty.openpty()
    run = tempfile.mkdtemp()
    env = dict(os.environ, IO_PORT=os.ttyname(sl), IO_RUN_DIR=run, STATE_DIRECTORY=run, PYTHONDONTWRITEBYTECODE='1')
    p = subprocess.Popen([sys.executable, os.path.join(RAIZ, 'files/bin/bricohams-io.py')], env=env,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        time.sleep(1.0)
        os.write(m, (json.dumps({'v': 1, 'boot': 'X', 'rain': 0, 'bme': {'chip': 'BME280', 't': 20.0, 'p': 101000.0, 'h': 40.0},
                                 'fan': {'duty': [100, 100], 'rpm': [2000, 2000], 'auto': True}}) + '\n').encode())
        open(os.path.join(run, 'fan.cmd'), 'w').write('FAN 55 55\n')
        os.write(m, (json.dumps({'v': 1, 'boot': 'X', 'rain': 2, 'fan': {'duty': [55, 55], 'rpm': [1500, 1490]}}) + '\n').encode())
        recibido, fin = b'', time.time() + 5
        while time.time() < fin and b'FAN 55 55' not in recibido:
            os.write(m, (json.dumps({'v': 1, 'boot': 'X', 'rain': 2}) + '\n').encode())
            time.sleep(0.3)
            try:
                os.set_blocking(m, False)
                recibido += os.read(m, 1024)
            except BlockingIOError:
                pass
        assert b'PING' in recibido and b'FAN 55 55' in recibido, recibido
        dd = json.load(open(os.path.join(run, 'io.json')))
        assert dd['boot'] == 'X' and 'recibido' in dd
    finally:
        p.terminate()
        p.wait(5)
print('OK test_pico_io: firmware = datasheet, órdenes, lluvia con reinicios, io.json y puerto serie virtual%s'
      % ('' if hay_serial else ' (sin pyserial: prueba pty omitida)'))
