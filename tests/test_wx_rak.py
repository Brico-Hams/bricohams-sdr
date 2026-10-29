#!/usr/bin/env python3
"""v5: la estación meteo toma T/HR/P y la posición del RAK4631 (rak-aprs.json)."""
import importlib.util, json, os, tempfile, time

AQUI = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('wx', os.path.join(AQUI, '..', 'files', 'bin', 'bricohams-wx.py'))
wx = importlib.util.module_from_spec(spec); spec.loader.exec_module(wx)

tmp = tempfile.mkdtemp()
ruta = os.path.join(tmp, 'rak-aprs.json')


def escribe(rak, edad=0):
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump({'actualizado': 0, 'rak': rak}, f)
    if edad:
        t = time.time() - edad
        os.utime(ruta, (t, t))


# BME680: T, HR y P (hPa -> Pa)
escribe({'t': 21.5, 'h': 48.2, 'p': 1009.3, 'sensor': 'BME680',
         'gps': {'present': True, 'fix': True, 'sats': 7, 'lat': 42.22917, 'lon': -8.70833, 'alt': 210}})
s = wx.SensorRak(ruta, esperas=1)
t, p, h = s.read()
assert (t, round(p), h) == (21.5, 100930, 48.2), (t, p, h)
assert s.chip == 'BME680 (RAK)'
assert wx.posicion_gps(wx.leer_rak(ruta)) == (42.22917, -8.70833, 210.0)

# SHTC3: sin presión y sin respaldo -> p None; paquete APRS sin campo b
escribe({'t': 19.0, 'h': 60, 'sensor': 'SHTC3', 'gps': {'present': True, 'fix': False, 'lat': 0, 'lon': 0}})
t, p, h = wx.SensorRak(ruta, esperas=1).read()
assert p is None and t == 19.0 and h == 60.0
assert wx.posicion_gps(wx.leer_rak(ruta)) is None          # sin fix
pk = wx.aprs_wx_packet('N0CALL-13', 42.23, -8.71, t, h, None, 'COM')
assert pk.endswith('t066h60COM'), pk
assert wx.aprs_wx_packet('N0CALL-13', 42.23, -8.71, t, h, 1013.2, 'COM').endswith('h60b10132COM')


# SHTC3 + respaldo con presión (Pico/I2C)
class Resp:
    chip = 'BME280'

    def read(self):
        return 20.0, 101000.0, 50.0


s = wx.SensorRak(ruta, respaldo=Resp(), esperas=1)
assert s.read()[1] == 101000.0 and 'presión BME280' in s.chip

# fichero viejo -> sin datos
escribe({'t': 19.0, 'h': 60}, edad=600)
assert wx.leer_rak(ruta) is None
try:
    wx.SensorRak(ruta, esperas=1)
    raise AssertionError('debía fallar con datos viejos')
except RuntimeError:
    pass

# GPS fuera de rango o 0,0 -> se ignora
assert wx.posicion_gps({'gps': {'fix': True, 'lat': 0, 'lon': 0}}) is None
assert wx.posicion_gps({'gps': {'fix': True, 'lat': 95, 'lon': 1}}) is None
assert wx.posicion_gps(None) is None

print('test_wx_rak OK')
