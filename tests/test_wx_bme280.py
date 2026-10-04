#!/usr/bin/env python3
"""Compensación BME280/BMP280 contra el ejemplo de la hoja de datos de Bosch
(BMP280 §3.12: T = 25,08 °C y p = 100653,27 Pa) y formato del paquete WX APRS."""
import importlib.util, os, struct

AQUI = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('wx', os.path.join(AQUI, '..', 'files', 'bin', 'bricohams-wx.py'))
wx = importlib.util.module_from_spec(spec); spec.loader.exec_module(wx)

vals = [27504, 26435, -1000, 36477, -10685, 3024, 2855, 140, -7, 15500, -14600, 6000]
cal = wx.parse_calib(list(struct.pack('<HhhHhhhhhhhh', *vals)) + [0, 0])
t, p, _ = wx.compensate(cal, 519888, 415148)
assert abs(t - 25.08) < 0.01, t
assert abs(p - 100653.27) < 0.5, p

# calibración de humedad empaquetada como en los registros 0xE1-0xE7
h = wx.parse_calib(list(struct.pack('<HhhHhhhhhhhh', *vals)) + [0, 75], [0x62, 0x01, 0x00, 0x13, 0x2A, 0x03, 0x1E])
assert (h['H1'], h['H2'], h['H3'], h['H4'], h['H5'], h['H6']) == (75, 354, 0, 314, 50, 30)
rh = wx.compensate(h, 519888, 415148, 27000)[2]
assert 0 <= rh <= 100

assert round(wx.sea_level(990.0, 20.0, 202), 1) == 1013.5
assert wx.aprs_pos(0.0, 0.0) == ('3804.94N', '00115.21W')
pk = wx.aprs_wx_packet('EA5KAO-13', 0.0, 0.0, 22.4, 55.2, 1014.27, 'WX BricoHams Mi QTH · BME280')
assert pk == 'EA5KAO-13>APZBHW,TCPIP*:!3804.94N/00115.21W_.../...g...t072h55b10143WX BricoHams Mi QTH - BME280', pk
assert 't003' in wx.aprs_wx_packet('X', 0, 0, -16.0, None, 1000, '')   # -16 °C = 3 °F
assert 'h00' in wx.aprs_wx_packet('X', 0, 0, 10, 100, 1000, '')         # 100 % = h00
print('OK test_wx_bme280: T=%.2f °C, p=%.2f Pa (datasheet), paquete APRS WX correcto' % (t, p))
