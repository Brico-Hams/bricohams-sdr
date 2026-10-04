#!/usr/bin/env python3
# =====================================================================
#  bricohams-wx · EA5KAO · BricoHams
#  Estación meteorológica propia con un BME280 (temperatura, humedad y
#  presión) o un BMP280 (sin humedad) en el I2C de la Raspberry Pi.
#   - Detecta solo el chip (0x60 = BME280, 0x58 = BMP280) y la dirección
#     (0x76 o 0x77).
#   - Cada minuto escribe WX_OUT (sensor.json) para la ventana METEO de
#     OpenWebRX, con la curva de las últimas 24 h.
#   - Si WX_APRS=yes, cada 10 min manda el tiempo a APRS-IS como
#     estación WX (WX_APRS_CALLSIGN) y sale en aprs.fi.
#   - v3: pluviómetro de cazoleta (interruptor reed, GPIO, 0,2794 mm por
#     vuelco) y anemómetro + veleta RS485 Modbus RTU (como los del firmware
#     LoRa_APRS_Wx_Station de CA2RXU: 4800 baudios, velocidad en la
#     dirección 1 y dirección en la 2). El paquete WX lleva entonces
#     dirección, velocidad, racha y lluvia de 1 h, 24 h y desde medianoche.
#  Variables en /etc/bricohams/wx.env. Uso de prueba: bricohams-wx --una
# =====================================================================
import json
import math
import os
import socket
import sys
import tempfile
import threading
import time
import unicodedata
from datetime import datetime, timezone

try:
    import smbus  # python3-smbus
except ImportError:
    try:
        import smbus2 as smbus  # python3-smbus2 (misma API SMBus)
    except ImportError:  # permite probar el cálculo sin el hardware
        smbus = None
try:
    import serial  # python3-serial (RS485)
except ImportError:
    serial = None
try:
    import lgpio  # python3-lgpio (pluviómetro)
except ImportError:
    lgpio = None


def env(k, d=''):
    return os.environ.get(k, d).strip()


def as_bool(v):
    return str(v).strip().lower() in ('1', 'yes', 'si', 'sí', 'true', 'on')


# ---------------------------------------------------------------------
#  Compensación de Bosch (fórmulas en coma flotante de las hojas de datos
#  del BMP280 §3.12 y del BME280 §4.2.3 / §8.1)
# ---------------------------------------------------------------------
def s16(v):
    return v - 65536 if v > 32767 else v


def s8(v):
    return v - 256 if v > 127 else v


def parse_calib(c, h=None):
    """c: 26 bytes desde 0x88; h: 7 bytes desde 0xE1 (solo BME280)."""
    u16 = lambda i: c[i] | (c[i + 1] << 8)
    cal = {'T1': u16(0), 'T2': s16(u16(2)), 'T3': s16(u16(4)),
           'P1': u16(6), 'P2': s16(u16(8)), 'P3': s16(u16(10)), 'P4': s16(u16(12)),
           'P5': s16(u16(14)), 'P6': s16(u16(16)), 'P7': s16(u16(18)), 'P8': s16(u16(20)),
           'P9': s16(u16(22))}
    if h is not None:
        cal['H1'] = c[25]
        cal['H2'] = s16(h[0] | (h[1] << 8))
        cal['H3'] = h[2]
        h4 = (h[3] << 4) | (h[4] & 0x0F)
        h5 = (h[5] << 4) | (h[4] >> 4)
        cal['H4'] = h4 - 4096 if h4 > 2047 else h4
        cal['H5'] = h5 - 4096 if h5 > 2047 else h5
        cal['H6'] = s8(h[6])
    return cal


def compensate(cal, adc_t, adc_p, adc_h=None):
    v1 = (adc_t / 16384.0 - cal['T1'] / 1024.0) * cal['T2']
    v2 = ((adc_t / 131072.0 - cal['T1'] / 8192.0) ** 2) * cal['T3']
    t_fine = v1 + v2
    temp = t_fine / 5120.0

    v1 = t_fine / 2.0 - 64000.0
    v2 = v1 * v1 * cal['P6'] / 32768.0
    v2 = v2 + v1 * cal['P5'] * 2.0
    v2 = v2 / 4.0 + cal['P4'] * 65536.0
    v1 = (cal['P3'] * v1 * v1 / 524288.0 + cal['P2'] * v1) / 524288.0
    v1 = (1.0 + v1 / 32768.0) * cal['P1']
    press = None
    if v1 != 0:
        p = 1048576.0 - adc_p
        p = (p - v2 / 4096.0) * 6250.0 / v1
        v1 = cal['P9'] * p * p / 2147483648.0
        v2 = p * cal['P8'] / 32768.0
        press = p + (v1 + v2 + cal['P7']) / 16.0  # Pa

    hum = None
    if adc_h is not None and 'H1' in cal:
        h = t_fine - 76800.0
        h = (adc_h - (cal['H4'] * 64.0 + cal['H5'] / 16384.0 * h)) * (
            cal['H2'] / 65536.0 * (1.0 + cal['H6'] / 67108864.0 * h * (1.0 + cal['H3'] / 67108864.0 * h)))
        h = h * (1.0 - cal['H1'] * h / 524288.0)
        hum = max(0.0, min(100.0, h))
    return temp, press, hum


def sea_level(p_hpa, t_c, alt_m):
    """Presión reducida al nivel del mar (fórmula hipsométrica)."""
    return p_hpa * (1.0 - 0.0065 * alt_m / (t_c + 0.0065 * alt_m + 273.15)) ** -5.257


def dew_point(t_c, rh):
    if rh is None or rh <= 0:
        return None
    a, b = 17.62, 243.12
    g = math.log(rh / 100.0) + a * t_c / (b + t_c)
    return b * g / (a - g)


# ---------------------------------------------------------------------
#  Sensor en el bus I2C
# ---------------------------------------------------------------------
class Sensor:
    CHIPS = {0x60: 'BME280', 0x58: 'BMP280', 0x57: 'BMP280', 0x56: 'BMP280'}

    def __init__(self, bus=1):
        if smbus is None:
            raise RuntimeError('falta python3-smbus (o python3-smbus2)')
        self.bus = smbus.SMBus(bus)
        self.addr = self.chip = None
        for a in (0x76, 0x77):
            try:
                cid = self.bus.read_byte_data(a, 0xD0)
            except OSError:
                continue
            if cid in self.CHIPS:
                self.addr, self.chip = a, self.CHIPS[cid]
                break
        if self.addr is None:
            raise RuntimeError('no encuentro un BME280/BMP280 en I2C-%d (0x76/0x77)' % bus)
        self.bus.write_byte_data(self.addr, 0xE0, 0xB6)  # reset
        time.sleep(0.01)
        c = self.bus.read_i2c_block_data(self.addr, 0x88, 26)
        h = self.bus.read_i2c_block_data(self.addr, 0xE1, 7) if self.chip == 'BME280' else None
        self.cal = parse_calib(c, h)
        self.bus.write_byte_data(self.addr, 0xF5, 0x00)  # sin filtro IIR, modo forzado

    def read(self):
        if self.chip == 'BME280':
            self.bus.write_byte_data(self.addr, 0xF2, 0x01)  # humedad x1 (antes de ctrl_meas)
        self.bus.write_byte_data(self.addr, 0xF4, 0x25)      # T x1, P x1, modo forzado
        for _ in range(50):
            time.sleep(0.01)
            if not self.bus.read_byte_data(self.addr, 0xF3) & 0x08:
                break
        n = 8 if self.chip == 'BME280' else 6
        d = self.bus.read_i2c_block_data(self.addr, 0xF7, n)
        adc_p = (d[0] << 12) | (d[1] << 4) | (d[2] >> 4)
        adc_t = (d[3] << 12) | (d[4] << 4) | (d[5] >> 4)
        adc_h = (d[6] << 8) | d[7] if n == 8 else None
        return compensate(self.cal, adc_t, adc_p, adc_h)


# ---------------------------------------------------------------------
#  APRS
# ---------------------------------------------------------------------
def aprs_pos(lat, lon):
    la, lo = abs(lat), abs(lon)
    return ('%02d%05.2f%s' % (int(la), (la - int(la)) * 60, 'N' if lat >= 0 else 'S'),
            '%03d%05.2f%s' % (int(lo), (lo - int(lo)) * 60, 'E' if lon >= 0 else 'W'))


def ascii_aprs(txt):
    txt = (txt or '').replace('·', '-').replace('°', '')
    return unicodedata.normalize('NFKD', txt).encode('ascii', 'ignore').decode()[:43]


MS_A_MPH = 2.23694
MM_A_CENT_PULGADA = 1 / 0.254


def _campo(v, ancho=3):
    return '.' * ancho if v is None else '%0*d' % (ancho, max(0, min(10 ** ancho - 1, int(round(v)))))


def aprs_wx_packet(call, lat, lon, t_c, rh, p_sl_hpa, comment, wind_dir=None, wind_ms=None, gust_ms=None,
                   rain_1h=None, rain_24h=None, rain_mid=None):
    """Paquete WX APRS (spec 1.0.1, cap. 12). Viento en mph y lluvia en centésimas de pulgada."""
    plat, plon = aprs_pos(lat, lon)
    comment = ascii_aprs(comment)
    t_f = int(round(t_c * 9 / 5 + 32))
    t = ('t%03d' % t_f) if t_f >= 0 else ('t-%02d' % -t_f)
    h = '' if rh is None else 'h%02d' % (0 if round(rh) >= 100 else max(1, int(round(rh))))
    b = 'b%05d' % int(round(p_sl_hpa * 10))
    c = _campo(None if wind_dir is None else (wind_dir % 360 or 360))
    sp = _campo(None if wind_ms is None else wind_ms * MS_A_MPH)
    g = _campo(None if gust_ms is None else gust_ms * MS_A_MPH)
    lluvia = ''.join('%s%s' % (k, _campo(v * MM_A_CENT_PULGADA)) for k, v in (('r', rain_1h), ('p', rain_24h), ('P', rain_mid)) if v is not None)
    return '%s>APZBHW,TCPIP*:!%s/%s_%s/%sg%s%s%s%s%s%s' % (call, plat, plon, c, sp, g, t, lluvia, h, b, comment)


# ---------------------------------------------------------------------
#  Pluviómetro (cazoleta basculante con reed): cuenta vuelcos por GPIO
# ---------------------------------------------------------------------
def lluvia_desde(vuelcos, mm_vuelco, ahora, desde):
    return round(sum(1 for ts in vuelcos if desde <= ts <= ahora) * mm_vuelco, 2)


def medianoche_local(ahora):
    lt = time.localtime(ahora)
    return time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, 0, 0, 0, 0, 0, -1))


class SensorPico:
    """v4: el BME280 cuelga de la Pico «bricohams-io» (la cabecera la ocupa el HAT).
    Lee la última medida que deja bricohams-io en /run/bricohams/io.json."""

    def __init__(self, path='/run/bricohams/io.json', max_edad=30, esperas=15):
        self.path, self.max_edad = path, max_edad
        self.addr = 0
        self.chip = 'BME280 (Pico)'
        for _ in range(esperas):              # la Pico manda cada 2 s
            try:
                self.read()
                return
            except RuntimeError:
                time.sleep(2)
        self.read()

    def read(self):
        try:
            d = json.load(open(self.path))
            edad = time.time() - os.path.getmtime(self.path)
        except (OSError, ValueError):
            raise RuntimeError('sin datos de la Pico en %s (¿bricohams-io en marcha?)' % self.path)
        b = d.get('bme') or {}
        if edad > self.max_edad or b.get('t') is None or b.get('p') is None:
            raise RuntimeError('la Pico no da BME280: %s' % (b.get('error') or 'datos de hace %d s' % edad))
        self.chip = '%s (Pico)' % b.get('chip', 'BME280')
        return float(b['t']), float(b['p']), (None if b.get('h') is None else float(b['h']))


class PluviometroIO:
    """v4: los vuelcos los cuenta la Pico; bricohams-io los guarda como marcas de tiempo."""

    def __init__(self, mm_vuelco, estado):
        self.mm, self.estado = mm_vuelco, estado

    def resumen(self):
        ahora = time.time()
        try:
            v = [float(x) for x in json.load(open(self.estado))]
        except (OSError, ValueError):
            v = []
        return {'1h': lluvia_desde(v, self.mm, ahora, ahora - 3600), '24h': lluvia_desde(v, self.mm, ahora, ahora - 86400),
                'hoy': lluvia_desde(v, self.mm, ahora, medianoche_local(ahora))}


class Pluviometro:
    def __init__(self, gpio, mm_vuelco, estado):
        self.mm, self.estado = mm_vuelco, estado
        try:
            self.vuelcos = [float(x) for x in json.load(open(estado))]
        except (OSError, ValueError):
            self.vuelcos = []
        self.lock = threading.Lock()
        self.h = None
        for n in (0, 4):
            try:
                self.h = lgpio.gpiochip_open(n)
                break
            except Exception:
                continue
        if self.h is None:
            raise RuntimeError('no abro /dev/gpiochip para el pluviómetro')
        lgpio.gpio_claim_alert(self.h, gpio, lgpio.FALLING_EDGE, lgpio.SET_PULL_UP)
        lgpio.gpio_set_debounce_micros(self.h, gpio, 20000)      # rebote del reed
        self.cb = lgpio.callback(self.h, gpio, lgpio.FALLING_EDGE, self._vuelco)

    def _vuelco(self, chip, gpio, level, tick):
        with self.lock:
            self.vuelcos.append(time.time())

    def resumen(self):
        ahora = time.time()
        with self.lock:
            self.vuelcos = [t for t in self.vuelcos if t > ahora - 86400 - 60]
            v = list(self.vuelcos)
        try:
            json.dump(v, open(self.estado, 'w'))
        except OSError:
            pass
        return {'1h': lluvia_desde(v, self.mm, ahora, ahora - 3600), '24h': lluvia_desde(v, self.mm, ahora, ahora - 86400),
                'hoy': lluvia_desde(v, self.mm, ahora, medianoche_local(ahora))}


# ---------------------------------------------------------------------
#  Viento RS485 Modbus RTU (función 0x03, registro 0x0000, 1 registro)
# ---------------------------------------------------------------------
def crc16_modbus(datos):
    crc = 0xFFFF
    for b in datos:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


def trama_lectura(addr, reg=0, n=1):
    t = bytes([addr, 0x03, reg >> 8, reg & 0xFF, n >> 8, n & 0xFF])
    c = crc16_modbus(t)
    return t + bytes([c & 0xFF, c >> 8])


def trama_escritura(addr, reg, valor):
    """Función 0x06 (escribir un registro). Cambio de dirección: registro 0x07D0."""
    t = bytes([addr, 0x06, reg >> 8, reg & 0xFF, valor >> 8, valor & 0xFF])
    c = crc16_modbus(t)
    return t + bytes([c & 0xFF, c >> 8])


def rs485_herramienta(args):
    """bricohams-wx --rs485-buscar | --rs485-direccion VIEJA NUEVA (con un solo sensor conectado)."""
    if serial is None:
        print('falta python3-serial'); return 1
    p = serial.Serial(env('WIND_PORT', '/dev/rs485'), int(env('WIND_BAUD', '4800')), timeout=0.5)
    if '--rs485-buscar' in args:
        for a in range(1, 8):
            p.reset_input_buffer(); p.write(trama_lectura(a))
            v = valor_respuesta(a, p.read(7))
            print('dirección %d: %s' % (a, 'responde, registro 0 = %d' % v if v is not None else '—'))
        return 0
    i = args.index('--rs485-direccion')
    vieja, nueva = int(args[i + 1]), int(args[i + 2])
    t = trama_escritura(vieja, 0x07D0, nueva)
    p.reset_input_buffer(); p.write(t)
    r = p.read(8)
    print('enviado %s · respuesta %s' % (t.hex(' '), r.hex(' ') or '(ninguna)'))
    print('OK: corta la alimentación del sensor 5 s y comprueba con --rs485-buscar' if r[:6] == t[:6] else 'Sin eco: comprueba con --rs485-buscar')
    return 0


def valor_respuesta(addr, r):
    """Devuelve el registro de 16 bits o None si la trama no es válida."""
    if len(r) < 7 or r[0] != addr or r[1] != 0x03 or r[2] != 2:
        return None
    c = crc16_modbus(r[:5])
    if r[5] != (c & 0xFF) or r[6] != (c >> 8):
        return None
    return (r[3] << 8) | r[4]


def media_direccion(grados):
    """Media vectorial (evita que 350° y 10° den 180°)."""
    if not grados:
        return None
    sx = sum(math.sin(math.radians(g)) for g in grados)
    cx = sum(math.cos(math.radians(g)) for g in grados)
    if abs(sx) < 1e-9 and abs(cx) < 1e-9:
        return None
    return (math.degrees(math.atan2(sx, cx)) + 360) % 360


class Viento(threading.Thread):
    def __init__(self, puerto, baudios, a_vel, a_dir, modo_dir):
        super().__init__(daemon=True)
        self.p = serial.Serial(puerto, baudios, timeout=0.5)
        self.a_vel, self.a_dir, self.modo = a_vel, a_dir, modo_dir
        self.muestras = []          # (ts, m/s, grados)
        self.lock = threading.Lock()
        self.errores = 0

    def _leer(self, addr):
        self.p.reset_input_buffer()
        self.p.write(trama_lectura(addr))
        return valor_respuesta(addr, self.p.read(7))

    def run(self):
        while True:
            try:
                v = self._leer(self.a_vel)
                time.sleep(0.2)
                d = self._leer(self.a_dir)
                if v is not None and d is not None:
                    grados = d * 45 if self.modo == 'sector8' else d
                    with self.lock:
                        self.muestras.append((time.time(), v / 10.0, grados % 360))
                        self.muestras = [m for m in self.muestras if m[0] > time.time() - 600]
                else:
                    self.errores += 1
            except Exception:
                self.errores += 1
            time.sleep(3)

    def resumen(self):
        ahora = time.time()
        with self.lock:
            m1 = [m for m in self.muestras if m[0] > ahora - 60]
            m2 = [m for m in self.muestras if m[0] > ahora - 120]
            m5 = [m for m in self.muestras if m[0] > ahora - 300]
        if not m1:
            return None
        return {'vel_ms': round(sum(m[1] for m in m1) / len(m1), 1),
                'dir': None if not m2 else round(media_direccion([m[2] for m in m2 if m[1] > 0.2] or [m[2] for m in m2])),
                'racha_ms': round(max(m[1] for m in m5), 1), 'muestras': len(m5), 'errores': self.errores}


def aprs_send(server, call, passcode, packet):
    host, _, port = server.partition(':')
    with socket.create_connection((host, int(port or 14580)), timeout=20) as s:
        s.recv(512)
        s.sendall(('user %s pass %s vers BricoHamsWX 1.0\r\n' % (call, passcode)).encode())
        resp = s.recv(512).decode('ascii', 'replace')
        if 'verified' not in resp or 'unverified' in resp:
            raise RuntimeError('APRS-IS no verificó el indicativo: %s' % resp.strip())
        s.sendall((packet + '\r\n').encode('ascii', 'replace'))
        time.sleep(1)


# ---------------------------------------------------------------------
def write_atomic(path, obj):
    d = os.path.dirname(path) or '.'
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.wx-', dir=d)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


def cargar_env(path='/etc/bricohams/wx.env'):
    """Para probar a mano (sudo bricohams-wx --una) sin el EnvironmentFile de systemd."""
    try:
        for ln in open(path, encoding='utf-8'):
            k, sep, v = ln.strip().partition('=')
            if sep and k and not k.startswith('#'):
                os.environ.setdefault(k, v.strip().strip('"'))
    except OSError:
        pass


def paquete(call, lat, lon, t, h, p_sl, vi, ll):
    return aprs_wx_packet(call, lat, lon, t, h, p_sl, env('WX_APRS_COMMENT'),
                          wind_dir=vi['dir'] if vi else None, wind_ms=vi['vel_ms'] if vi else None,
                          gust_ms=vi['racha_ms'] if vi else None, rain_1h=ll['1h'] if ll else None,
                          rain_24h=ll['24h'] if ll else None, rain_mid=ll['hoy'] if ll else None)


def main():
    cargar_env()
    if any(a.startswith('--rs485') for a in sys.argv):
        return rs485_herramienta(sys.argv)
    out = env('WX_OUT', '/usr/lib/python3/dist-packages/htdocs/plugins/receiver/meteo/sensor.json')
    hist_file = os.path.join(env('STATE_DIRECTORY', '/var/lib/bricohams'), 'wx-history.json')
    lat, lon = float(env('STATION_LAT', '0.0')), float(env('STATION_LON', '0.0'))
    alt = float(env('STATION_ASL', '200')) + float(env('WX_SENSOR_HEIGHT', '2'))
    toff = float(env('WX_TEMP_OFFSET', '0') or 0)
    do_aprs = as_bool(env('WX_APRS', 'no'))
    call = env('WX_APRS_CALLSIGN', 'EA5KAO-13')
    once = '--una' in sys.argv

    pico = env('IO_MODE', 'pico') == 'pico'
    sensor = SensorPico(os.path.join(env('IO_RUN_DIR', '/run/bricohams'), 'io.json')) if pico \
        else Sensor(int(env('WX_I2C_BUS', '1')))
    print('wx: %s en 0x%02x' % (sensor.chip, sensor.addr), flush=True)
    viento = pluvio = None
    if as_bool(env('WIND_ENABLE', 'no')):
        try:
            viento = Viento(env('WIND_PORT', '/dev/rs485'), int(env('WIND_BAUD', '4800')), int(env('WIND_ADDR_SPEED', '1')),
                            int(env('WIND_ADDR_DIR', '2')), env('WIND_DIR_MODE', 'sector8'))
            viento.start()
            print('wx: viento RS485 en %s' % env('WIND_PORT', '/dev/rs485'), flush=True)
        except Exception as e:
            print('wx: sin viento (%s)' % e, file=sys.stderr, flush=True)
    if as_bool(env('RAIN_ENABLE', 'no')):
        try:
            estado = os.path.join(env('STATE_DIRECTORY', '/var/lib/bricohams'), 'lluvia.json')
            if pico:
                pluvio = PluviometroIO(float(env('RAIN_MM', '0.2794')), estado)
                print('wx: pluviómetro en la Pico (GP15)', flush=True)
            else:
                pluvio = Pluviometro(int(env('RAIN_GPIO', '17')), float(env('RAIN_MM', '0.2794')), estado)
                print('wx: pluviómetro en GPIO%s' % env('RAIN_GPIO', '17'), flush=True)
        except Exception as e:
            print('wx: sin pluviómetro (%s)' % e, file=sys.stderr, flush=True)
    if once and viento:
        time.sleep(8)
    try:
        history = json.load(open(hist_file))
    except (OSError, ValueError):
        history = []
    last_hist = last_aprs = 0.0

    while True:
        t, p, h = sensor.read()
        t += toff
        p_hpa = p / 100.0
        p_sl = sea_level(p_hpa, t, alt)
        now = time.time()
        iso = datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
        vi = viento.resumen() if viento else None
        ll = pluvio.resumen() if pluvio else None
        if now - last_hist >= 300:
            history.append({'t': iso, 'ta': round(t, 1), 'hr': None if h is None else round(h),
                            'p': round(p_sl, 1), 'vv': vi['vel_ms'] if vi else None, 'dv': vi['dir'] if vi else None,
                            'll': ll['1h'] if ll else None})
            history = [x for x in history if x['t'] >= datetime.fromtimestamp(now - 86400, timezone.utc).isoformat()[:19]]
            try:
                os.makedirs(os.path.dirname(hist_file), exist_ok=True)
                json.dump(history, open(hist_file, 'w'))
            except OSError:
                pass
            last_hist = now
        data = {'updated': iso, 'chip': sensor.chip, 'addr': '0x%02x' % sensor.addr,
                'name': env('WX_NAME', 'EA5KAO · Mi QTH'),
                'ta': round(t, 1), 'hr': None if h is None else round(h, 1),
                'pres': round(p_hpa, 1), 'pres_nmar': round(p_sl, 1),
                'dew': None if h is None else round(dew_point(t, h), 1),
                'aprs': call if do_aprs else None, 'viento': vi, 'lluvia': ll, 'history': history}
        write_atomic(out, data)
        if once:
            print(json.dumps({k: v for k, v in data.items() if k != 'history'}, ensure_ascii=False))
            if do_aprs:
                print(paquete(call, lat, lon, t, h, p_sl, vi, ll))
            return 0
        if do_aprs and now - last_aprs >= 600:
            try:
                aprs_send(env('WX_APRS_SERVER', 'euro.aprs2.net:14580'), call, env('APRS_PASSCODE'),
                          paquete(call, lat, lon, t, h, p_sl, vi, ll))
                last_aprs = now
            except Exception as e:
                print('wx: APRS-IS: %s' % e, file=sys.stderr, flush=True)
                last_aprs = now - 480  # reintenta en 2 min
        time.sleep(60)


if __name__ == '__main__':
    sys.exit(main())
