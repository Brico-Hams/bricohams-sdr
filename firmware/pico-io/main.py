# =====================================================================
#  bricohams-io · EA5KAO · BricoHams  —  firmware MicroPython para Raspberry Pi Pico
#
#  Puente USB entre la Raspberry Pi 5 (que tiene la cabecera de 40 pines
#  ocupada por el HAT) y los sensores/actuadores de la caja:
#     BME280/BMP280 (I2C0: GP4 SDA, GP5 SCL)   · temperatura, humedad, presión
#     DS18B20 (1-Wire: GP22, 4,7 kΩ a 3V3)      · aire de la caja
#     Pluviómetro reed (GP15 a GND, 10 kΩ a 3V3 + 100 nF)
#     Ventiladores 12 V de 4 hilos:
#        PWM 25 kHz  GP16 (entrada) y GP17 (salida), por MOSFET 2N7002 (invierte)
#        Tacómetro   GP18 (entrada) y GP19 (salida), 10 kΩ a 3V3 + 1 kΩ en serie
#
#  Protocolo por USB (115200, líneas de texto):
#   Pico → Pi, cada 2 s, una línea JSON:
#     {"v":1,"up":123,"bme":{"chip":"BME280","t":21.3,"p":100512.4,"h":55.1},
#      "ds":[{"id":"28ff…","t":31.2}],"rain":17,"boot":"a1b2c3d4",
#      "fan":{"duty":[40,40],"rpm":[1810,1790],"auto":false}}
#   Pi → Pico:
#     FAN <0-100> <0-100>   ciclo de los dos ventiladores
#     PING                  responde {"pong":…}
#   Seguridad: si en 60 s no llega ninguna orden FAN, los ventiladores pasan
#   solos al 100 % («auto»: true) hasta que la Pi vuelva a mandar.
#
#  Instalar: copia el UF2 de MicroPython a la Pico (BOOTSEL) y después
#            sudo bricohams-io instalar      (copia este main.py con mpremote)
# =====================================================================
import json
import sys
import time

try:
    import machine
    import select
    import ubinascii
    PICO = True
except ImportError:          # en un PC (pruebas): solo las funciones de cálculo
    PICO = False

VERSION = 1
PIN_SDA, PIN_SCL, PIN_1W, PIN_RAIN = 4, 5, 22, 15
PIN_PWM = (16, 17)
PIN_TACH = (18, 19)
PWM_FREQ = 25000
PWM_INVERT = True            # con el 2N7002 del esquema (GPIO alto = PWM del ventilador a masa)
FAILSAFE_S = 60
PERIOD_MS = 2000
RAIN_DEBOUNCE_MS = 20


# ------------------------- BME280 / BMP280 ---------------------------
def s16(v):
    return v - 65536 if v > 32767 else v


def s8(v):
    return v - 256 if v > 127 else v


def parse_calib(c, h=None):
    def u16(i):
        return c[i] | (c[i + 1] << 8)
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
        press = p + (v1 + v2 + cal['P7']) / 16.0
    hum = None
    if adc_h is not None and 'H1' in cal:
        h = t_fine - 76800.0
        h = (adc_h - (cal['H4'] * 64.0 + cal['H5'] / 16384.0 * h)) * (
            cal['H2'] / 65536.0 * (1.0 + cal['H6'] / 67108864.0 * h * (1.0 + cal['H3'] / 67108864.0 * h)))
        h = h * (1.0 - cal['H1'] * h / 524288.0)
        hum = max(0.0, min(100.0, h))
    return temp, press, hum


def rpm(pulsos, segundos, por_vuelta=2):
    if segundos <= 0:
        return 0
    return int(round(pulsos * 60.0 / (segundos * por_vuelta)))


def duty_u16(pct, invert=PWM_INVERT):
    pct = max(0, min(100, int(pct)))
    v = int(pct * 65535 // 100)
    return 65535 - v if invert else v


def parse_cmd(line):
    """'FAN 40 60' -> ('FAN', [40, 60]); 'PING' -> ('PING', []); otro -> (None, [])."""
    p = line.strip().split()
    if not p:
        return None, []
    cmd = p[0].upper()
    if cmd == 'FAN' and len(p) == 3:
        try:
            return 'FAN', [max(0, min(100, int(p[1]))), max(0, min(100, int(p[2])))]
        except ValueError:
            return None, []
    if cmd == 'PING':
        return 'PING', []
    return None, []


# ------------------------------ hardware ------------------------------
class BME:
    CHIPS = {0x60: 'BME280', 0x58: 'BMP280', 0x57: 'BMP280', 0x56: 'BMP280'}

    def __init__(self, i2c):
        self.i2c, self.addr, self.chip = i2c, None, None
        for a in (0x76, 0x77):
            try:
                cid = i2c.readfrom_mem(a, 0xD0, 1)[0]
            except OSError:
                continue
            if cid in self.CHIPS:
                self.addr, self.chip = a, self.CHIPS[cid]
                break
        if self.addr is None:
            raise OSError('sin BME280')
        i2c.writeto_mem(self.addr, 0xE0, b'\xb6')
        time.sleep_ms(10)
        c = i2c.readfrom_mem(self.addr, 0x88, 26)
        h = i2c.readfrom_mem(self.addr, 0xE1, 7) if self.chip == 'BME280' else None
        self.cal = parse_calib(c, h)
        i2c.writeto_mem(self.addr, 0xF5, b'\x00')

    def read(self):
        if self.chip == 'BME280':
            self.i2c.writeto_mem(self.addr, 0xF2, b'\x01')
        self.i2c.writeto_mem(self.addr, 0xF4, b'\x25')
        for _ in range(50):
            time.sleep_ms(10)
            if not self.i2c.readfrom_mem(self.addr, 0xF3, 1)[0] & 0x08:
                break
        n = 8 if self.chip == 'BME280' else 6
        d = self.i2c.readfrom_mem(self.addr, 0xF7, n)
        adc_p = (d[0] << 12) | (d[1] << 4) | (d[2] >> 4)
        adc_t = (d[3] << 12) | (d[4] << 4) | (d[5] >> 4)
        adc_h = (d[6] << 8) | d[7] if n == 8 else None
        return compensate(self.cal, adc_t, adc_p, adc_h)


def main():
    from machine import Pin, PWM, I2C
    led = Pin(25, Pin.OUT)
    boot = ubinascii.hexlify(machine.unique_id()).decode()[-4:] + '%04x' % (time.ticks_ms() & 0xFFFF)

    i2c = I2C(0, sda=Pin(PIN_SDA), scl=Pin(PIN_SCL), freq=100000)
    bme = None

    ds = roms = None
    try:
        import onewire
        import ds18x20
        ds = ds18x20.DS18X20(onewire.OneWire(Pin(PIN_1W)))
        roms = ds.scan()
    except Exception:
        ds = None

    rain = {'n': 0, 'last': 0}

    def on_rain(p):
        now = time.ticks_ms()
        if time.ticks_diff(now, rain['last']) > RAIN_DEBOUNCE_MS:
            rain['n'] += 1
        rain['last'] = now
    Pin(PIN_RAIN, Pin.IN, Pin.PULL_UP).irq(trigger=Pin.IRQ_FALLING, handler=on_rain)

    pulses = [0, 0]

    def tach_cb(i):
        def cb(p):
            pulses[i] += 1
        return cb
    for i, g in enumerate(PIN_TACH):
        Pin(g, Pin.IN, Pin.PULL_UP).irq(trigger=Pin.IRQ_FALLING, handler=tach_cb(i))

    pwms = []
    for g in PIN_PWM:
        p = PWM(Pin(g))
        p.freq(PWM_FREQ)
        pwms.append(p)
    duty = [100, 100]
    for i, p in enumerate(pwms):
        p.duty_u16(duty_u16(duty[i]))

    poll = select.poll()
    poll.register(sys.stdin, select.POLLIN)
    buf = ''
    last_cmd = time.ticks_ms()
    auto = True
    t_prev = time.ticks_ms()
    rpms = [0, 0]
    next_tx = time.ticks_add(time.ticks_ms(), PERIOD_MS)
    if ds and roms:
        ds.convert_temp()

    while True:
        # órdenes de la Pi (sin bloquear)
        while poll.poll(0):
            ch = sys.stdin.read(1)
            if ch in ('\n', '\r'):
                cmd, args = parse_cmd(buf)
                buf = ''
                if cmd == 'FAN':
                    duty, auto, last_cmd = args, False, time.ticks_ms()
                    for i, p in enumerate(pwms):
                        p.duty_u16(duty_u16(duty[i]))
                elif cmd == 'PING':
                    print(json.dumps({'pong': VERSION, 'boot': boot}))
            elif len(buf) < 64:
                buf += ch
        if not auto and time.ticks_diff(time.ticks_ms(), last_cmd) > FAILSAFE_S * 1000:
            auto, duty = True, [100, 100]           # la Pi no responde: a tope por seguridad
            for p in pwms:
                p.duty_u16(duty_u16(100))
        if time.ticks_diff(time.ticks_ms(), next_tx) >= 0:
            next_tx = time.ticks_add(next_tx, PERIOD_MS)
            now = time.ticks_ms()
            dt = time.ticks_diff(now, t_prev) / 1000.0
            t_prev = now
            rpms = [rpm(pulses[0], dt), rpm(pulses[1], dt)]
            pulses[0] = pulses[1] = 0
            out = {'v': VERSION, 'up': now // 1000, 'boot': boot, 'rain': rain['n'],
                   'fan': {'duty': duty, 'rpm': rpms, 'auto': auto}}
            try:
                if bme is None:
                    bme = BME(i2c)
                t, p, h = bme.read()
                out['bme'] = {'chip': bme.chip, 't': round(t, 2), 'p': round(p, 1) if p else None,
                              'h': None if h is None else round(h, 1)}
            except Exception as e:
                bme = None
                out['bme'] = {'error': str(e)}
            if ds and roms:
                lst = []
                for r in roms:
                    try:
                        lst.append({'id': ubinascii.hexlify(r).decode(), 't': round(ds.read_temp(r), 2)})
                    except Exception:
                        pass
                out['ds'] = lst
                ds.convert_temp()                    # la siguiente lectura estará lista en 2 s
            print(json.dumps(out))
            led.toggle()
        time.sleep_ms(20)


if PICO and __name__ == '__main__':
    main()
