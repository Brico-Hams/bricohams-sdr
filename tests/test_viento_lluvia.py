#!/usr/bin/env python3
"""Viento RS485 (Modbus RTU), pluviómetro y paquete APRS WX completo."""
import importlib.util, os

AQUI = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('wx', os.path.join(AQUI, '..', 'files', 'bin', 'bricohams-wx.py'))
wx = importlib.util.module_from_spec(spec); spec.loader.exec_module(wx)

# trama Modbus de referencia: 01 03 00 00 00 01 → CRC 84 0A
assert wx.trama_lectura(1) == bytes.fromhex('010300000001840A'), wx.trama_lectura(1).hex()
assert wx.trama_lectura(2) == bytes.fromhex('020300000001840A')[:6] + bytes([wx.crc16_modbus(bytes.fromhex('020300000001')) & 0xFF, wx.crc16_modbus(bytes.fromhex('020300000001')) >> 8])
# respuesta del anemómetro: 5,4 m/s → registro 54
r = bytes([1, 3, 2, 0, 54]); c = wx.crc16_modbus(r); r += bytes([c & 0xFF, c >> 8])
assert wx.valor_respuesta(1, r) == 54
assert wx.valor_respuesta(2, r) is None                 # otra dirección
assert wx.valor_respuesta(1, r[:-1] + bytes([r[-1] ^ 1])) is None   # CRC mal

# cambio de dirección 1 → 2 (registro 0x07D0), como el firmware de CA2RXU
t = wx.trama_escritura(1, 0x07D0, 2)
assert t[:6] == bytes.fromhex('010607D00002') and wx.crc16_modbus(t[:6]) == t[6] | (t[7] << 8)

# media vectorial de la dirección
assert round(wx.media_direccion([350, 10])) in (0, 360)
assert round(wx.media_direccion([90, 90, 90])) == 90

# lluvia: 3 vuelcos en la última hora y 5 en 24 h
ahora = 1_000_000.0
v = [ahora - 100, ahora - 2000, ahora - 3500, ahora - 7200, ahora - 80000, ahora - 90000]
assert wx.lluvia_desde(v, 0.2794, ahora, ahora - 3600) == round(3 * 0.2794, 2)
assert wx.lluvia_desde(v, 0.2794, ahora, ahora - 86400) == round(5 * 0.2794, 2)

# paquete completo: dirección 225°, 5 m/s (11 mph), racha 9 m/s (20 mph), lluvia 1,1 mm/1 h (r004), 5,6 mm/24 h (p022)
pk = wx.aprs_wx_packet('N0CALL-13', 40.0, -3.0, 22.4, 55.2, 1014.27, 'Synthetic WX',
                       wind_dir=225, wind_ms=5.0, gust_ms=9.0, rain_1h=1.1, rain_24h=5.6, rain_mid=2.0)
assert pk == 'N0CALL-13>APZBHW,TCPIP*:!4000.00N/00300.00W_225/011g020t072r004p022P008h55b10143Synthetic WX', pk
# norte se escribe 360 (000 = sin dato en algunos programas)
assert '_360/' in wx.aprs_wx_packet('X', 0, 0, 10, None, 1000, '', wind_dir=0, wind_ms=1)
print('OK test_viento_lluvia: Modbus CRC, respuestas, dirección media, lluvia 1 h/24 h y paquete APRS completo')
