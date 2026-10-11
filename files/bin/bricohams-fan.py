#!/usr/bin/env python3
# =====================================================================
#  bricohams-fan · EA5KAO · BricoHams
#  Control de los 2 ventiladores de 60 mm (12 V, PWM de 4 hilos) de la caja.
#   - Mide la CPU de la Pi (thermal_zone0) y el interior de la caja (DS18B20
#     en 1-Wire, GPIO4). Calcula el ciclo con una curva con histéresis.
#   - PWM por hardware a 25 kHz en GPIO12 (entrada) y GPIO13 (salida) con
#     el overlay pwm-2chan; si no hay pwmchip, PWM por software con lgpio.
#   - Lee los tacómetros (GPIO22 y GPIO5, 2 pulsos por vuelta) y avisa si un
#     ventilador debería girar y no gira.
#   - Escribe el estado en /run/bricohams/caja.json y en la web (meteo/caja.json).
#  Variables en /etc/bricohams/fan.env. Prueba: sudo bricohams-fan --estado
#   Forzar 30 s (con el servicio parado): sudo bricohams-fan --forzar 80
# =====================================================================
import glob
import json
import os
import shlex
import sys
import tempfile
import time

try:
    import lgpio  # python3-lgpio
except ImportError:
    lgpio = None


def env(k, d=''):
    return os.environ.get(k, d).strip()


def as_bool(v):
    return str(v).strip().lower() in ('1', 'yes', 'si', 'sí', 'true', 'on')


def quitar_comillas(v):
    """VALOR, "VALOR" o 'VALOR' (v4.2: el instalador escribe comillas simples, como 'a'\\''b')."""
    v = v.strip()
    try:
        partes = shlex.split(v, comments=True)
        if len(partes) == 1:
            return partes[0]
    except ValueError:
        pass
    return v.strip('"\'')


def cargar_env(path='/etc/bricohams/fan.env'):
    try:
        for ln in open(path, encoding='utf-8'):
            k, sep, v = ln.strip().partition('=')
            if sep and k and not k.startswith('#'):
                os.environ.setdefault(k, quitar_comillas(v))
    except OSError:
        pass


# ---------------------------------------------------------------------
#  Curva (pura: se prueba en tests/test_fan.py)
# ---------------------------------------------------------------------
def rampa(t, t_min, t_max):
    """0 por debajo de t_min, 1 por encima de t_max, lineal en medio."""
    if t is None:
        return 0.0
    if t <= t_min:
        return 0.0
    if t >= t_max:
        return 1.0
    return (t - t_min) / (t_max - t_min)


def curva(t_cpu, t_caja, cfg, ciclo_anterior=0):
    """Ciclo en % (0 o entre DUTY_MIN y 100). Histéresis: no se apaga hasta
    bajar HIST grados por debajo del umbral de arranque."""
    f = max(rampa(t_cpu, cfg['cpu_min'], cfg['cpu_max']), rampa(t_caja, cfg['caja_min'], cfg['caja_max']))
    if t_caja is None and t_cpu is None:
        return 100                                           # sin sensores: a tope por seguridad
    if f <= 0:
        sigue = ciclo_anterior > 0 and ((t_cpu is not None and t_cpu > cfg['cpu_min'] - cfg['hist']) or
                                        (t_caja is not None and t_caja > cfg['caja_min'] - cfg['hist']))
        return cfg['duty_min'] if sigue else 0
    return int(round(cfg['duty_min'] + f * (100 - cfg['duty_min'])))


def rpm(pulsos, segundos, por_vuelta=2):
    return 0 if segundos <= 0 else int(round(pulsos / por_vuelta / segundos * 60))


# ---------------------------------------------------------------------
#  Sensores
# ---------------------------------------------------------------------
def temp_cpu():
    try:
        return int(open('/sys/class/thermal/thermal_zone0/temp').read()) / 1000.0
    except (OSError, ValueError):
        return None


def temp_ds18b20(ident=''):
    rutas = glob.glob('/sys/bus/w1/devices/28-*/w1_slave')
    if ident:
        rutas = [r for r in rutas if ident in r] or rutas
    for r in rutas:
        try:
            ln = open(r).read().splitlines()
            if ln and ln[0].endswith('YES') and 't=' in ln[1]:
                return int(ln[1].split('t=')[1]) / 1000.0
        except (OSError, ValueError, IndexError):
            continue
    return None


# ---------------------------------------------------------------------
#  PWM
# ---------------------------------------------------------------------
class PwmHw:
    """sysfs /sys/class/pwm. En la Pi 5 los GPIO12/13 son PWM0 del RP1 (canales 0 y 1)."""

    def __init__(self, canales, freq=25000, invertir=False):
        self.chip = self._buscar()
        if self.chip is None:
            raise RuntimeError('no hay pwmchip para GPIO12/13 (¿dtoverlay=pwm-2chan,…?)')
        self.periodo = int(1e9 / freq)
        self.canales = canales
        self.inv = invertir
        for c in canales:
            base = '%s/pwm%d' % (self.chip, c)
            if not os.path.isdir(base):
                open(self.chip + '/export', 'w').write(str(c))
                time.sleep(0.2)
            self._w(c, 'period', self.periodo)
            self._w(c, 'enable', 1)

    @staticmethod
    def _buscar():
        cand = []
        for ch in sorted(glob.glob('/sys/class/pwm/pwmchip*')):
            try:
                n = int(open(ch + '/npwm').read())
                real = os.path.realpath(ch)
            except (OSError, ValueError):
                continue
            if n >= 2 and '9c000' not in real:          # 1f0009c000 = PWM1 (ventilador oficial de la Pi 5)
                cand.append((0 if '98000' in real else 1, ch))
        return sorted(cand)[0][1] if cand else None

    def _w(self, c, f, v):
        open('%s/pwm%d/%s' % (self.chip, c, f), 'w').write(str(v))

    def ciclo(self, c, pct):
        pct = 100 - pct if self.inv else pct
        self._w(c, 'duty_cycle', int(self.periodo * max(0, min(100, pct)) / 100))


class PwmSw:
    def __init__(self, h, gpios, freq=10000, invertir=False):
        self.h, self.g, self.f, self.inv = h, gpios, freq, invertir
        for g in gpios:
            lgpio.gpio_claim_output(h, g, 0)

    def ciclo(self, idx, pct):
        pct = 100 - pct if self.inv else pct
        lgpio.tx_pwm(self.h, self.g[idx], self.f, max(0, min(100, pct)))


class Tacometro:
    def __init__(self, h, gpios):
        self.h, self.g = h, gpios
        self.n = [0] * len(gpios)
        self.cb = []
        for i, g in enumerate(gpios):
            lgpio.gpio_claim_alert(h, g, lgpio.FALLING_EDGE, lgpio.SET_PULL_UP)
            self.cb.append(lgpio.callback(h, g, lgpio.FALLING_EDGE, self._mk(i)))

    def _mk(self, i):
        def f(chip, gpio, level, tick):
            self.n[i] += 1
        return f

    def leer(self):
        v = list(self.n)
        self.n = [0] * len(self.n)
        return v


def abrir_chip():
    for n in (0, 4):
        try:
            return lgpio.gpiochip_open(n)
        except Exception:
            continue
    return None


def write_atomic(path, obj):
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.caja-', dir=d)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False)
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


def io_lectura(path):
    """Última lectura de la Pico (bricohams-io) o None si es vieja (> 20 s)."""
    try:
        if time.time() - os.path.getmtime(path) > 20:
            return None
        return json.load(open(path))
    except (OSError, ValueError):
        return None


def temp_caja_rak(path=None):
    """v4.5 · temperatura de la caja medida por el RAK4631 (bricohams-rak-aprs), si es reciente (< 5 min)."""
    if not as_bool(env('FAN_CAJA_RAK', 'yes')):
        return None
    path = path or env('RAK_ESTADO', '/run/bricohams-rak/rak-aprs.json')
    try:
        if time.time() - os.path.getmtime(path) > 300:
            return None
        t = json.load(open(path)).get('t_caja')
        return float(t) if t is not None else None
    except (OSError, ValueError, TypeError, AttributeError):
        return None


def io_temp_caja(d, ident=''):
    lst = (d or {}).get('ds') or []
    if ident:
        lst = [x for x in lst if ident in x.get('id', '')] or lst
    return lst[0]['t'] if lst and lst[0].get('t') is not None else None


def main_pico(cfg, forzado, salida_web):
    """v4: los ventiladores, el tacómetro y el DS18B20 cuelgan de la Pico «bricohams-io»."""
    run = env('IO_RUN_DIR', '/run/bricohams')
    io_json, orden = os.path.join(run, 'io.json'), os.path.join(run, 'fan.cmd')
    fin = time.time() + 30 if forzado is not None else None
    print('fan: ventiladores en la Pico (GP16/GP17 PWM, GP18/GP19 tacómetro, DS18B20 en GP22)', flush=True)
    ciclo = 0
    while True:
        d = io_lectura(io_json)
        tc, tb = temp_cpu(), io_temp_caja(d, env('FAN_DS18B20_ID'))
        if tb is None:
            tb = temp_caja_rak()                          # v4.5: sin DS18B20, la del RAK4631
        nuevo = forzado if forzado is not None else curva(tc, tb, cfg, ciclo)
        if ciclo == 0 and 0 < nuevo < 60 and forzado is None:
            nuevo_envio = 100                                 # arranque desde parado: golpe al 100 %
        else:
            nuevo_envio = nuevo
        try:
            os.makedirs(run, exist_ok=True)
            with open(orden, 'w') as f:
                f.write('FAN %d %d\n' % (nuevo_envio, nuevo_envio))
        except OSError as e:
            print('fan: no puedo dejar la orden (%s)' % e, file=sys.stderr, flush=True)
        if nuevo_envio != nuevo:
            time.sleep(2)
            with open(orden, 'w') as f:
                f.write('FAN %d %d\n' % (nuevo, nuevo))
        ciclo = nuevo
        time.sleep(10)
        d = io_lectura(io_json)
        vueltas = list(((d or {}).get('fan') or {}).get('rpm') or [])
        auto = bool(((d or {}).get('fan') or {}).get('auto'))
        alarma = [i for i, r in enumerate(vueltas) if ciclo >= 40 and r < 300]
        estado = {'actualizado': time.strftime('%Y-%m-%dT%H:%M:%S'), 't_cpu': tc, 't_caja': tb, 'ciclo': ciclo,
                  'rpm': vueltas, 'alarma': ['entrada', 'salida'][alarma[0]] if alarma else None,
                  'modo': 'Pico bricohams-io' + (' (sin órdenes: a tope por seguridad)' if auto else ''),
                  'pico': d is not None}
        if d is None:
            estado['alarma'] = 'sin Pico'
        for ruta in (os.path.join(run, 'caja.json'), salida_web):
            try:
                write_atomic(ruta, estado)
            except OSError:
                pass
        if forzado is not None:
            print('fan: ciclo %d %% · CPU %s °C · caja %s °C · rpm %s' % (ciclo, tc, tb, vueltas), flush=True)
            if time.time() >= fin:
                return 0
        if estado['alarma']:
            print('fan: AVISO %s (rpm %s, ciclo %d %%)' % (estado['alarma'], vueltas, ciclo), file=sys.stderr, flush=True)


def main():
    if '-h' in sys.argv or '--help' in sys.argv:          # v4.2: la ayuda no arranca el servicio
        print('uso: bricohams-fan [--estado | --forzar 0-100 (30 s, con el servicio parado)]\n'
              '     sin argumentos: servicio (lo lanza systemd: bricohams-fan.service)')
        return 0
    cargar_env()
    if '--estado' in sys.argv:
        try:
            print(open('/run/bricohams/caja.json').read())
        except OSError:
            print('sin estado: ¿está en marcha bricohams-fan?')
        return 0
    cfg = {'cpu_min': float(env('FAN_T_CPU_MIN', '55')), 'cpu_max': float(env('FAN_T_CPU_MAX', '75')),
           'caja_min': float(env('FAN_T_CAJA_MIN', '35')), 'caja_max': float(env('FAN_T_CAJA_MAX', '45')),
           'duty_min': int(env('FAN_DUTY_MIN', '30')), 'hist': float(env('FAN_HIST', '3'))}
    pwm_gpios = [int(x) for x in env('FAN_PWM_GPIOS', '12,13').split(',') if x]
    tach_gpios = [int(x) for x in env('FAN_TACH_GPIOS', '22,5').split(',') if x]
    invertir = as_bool(env('FAN_PWM_INVERT', 'yes'))
    forzado = None
    if '--forzar' in sys.argv:
        forzado = max(0, min(100, int(sys.argv[sys.argv.index('--forzar') + 1])))
        if os.system('systemctl is-active --quiet bricohams-fan 2>/dev/null') == 0:
            print('fan: para antes el servicio: sudo systemctl stop bricohams-fan (y luego start)', file=sys.stderr)
            return 1
    fin = time.time() + 30 if forzado is not None else None   # --forzar dura 30 s y termina
    salida_web = env('FAN_OUT', '/usr/lib/python3/dist-packages/htdocs/plugins/receiver/meteo/caja.json')
    if env('IO_MODE', 'pico') == 'pico':
        return main_pico(cfg, forzado, salida_web)

    h = abrir_chip() if lgpio else None
    try:
        pwm = PwmHw([0, 1][:len(pwm_gpios)], invertir=invertir)
        modo = 'hardware 25 kHz (%s)' % os.path.basename(pwm.chip)
        canal = lambda i: [0, 1][i]
    except Exception as e:
        if h is None:
            print('fan: sin PWM por hardware (%s) ni lgpio' % e, file=sys.stderr)
            return 1
        pwm = PwmSw(h, pwm_gpios, invertir=invertir)
        modo = 'software 10 kHz (lgpio)'
        canal = lambda i: i
    tach = Tacometro(h, tach_gpios) if h is not None and tach_gpios else None
    print('fan: PWM %s en GPIO %s, tacómetros %s' % (modo, pwm_gpios, tach_gpios), flush=True)

    ciclo = 0
    while True:
        tc, tb = temp_cpu(), temp_ds18b20(env('FAN_DS18B20_ID'))
        if tb is None:
            tb = temp_caja_rak()                          # v4.5: sin DS18B20, la del RAK4631
        nuevo = forzado if forzado is not None else curva(tc, tb, cfg, ciclo)
        if ciclo == 0 and 0 < nuevo < 60:                # arranque desde parado: golpe al 100 % 1,5 s
            for i in range(len(pwm_gpios)):
                pwm.ciclo(canal(i), 100)
            time.sleep(1.5)
        for i in range(len(pwm_gpios)):
            pwm.ciclo(canal(i), nuevo)
        ciclo = nuevo
        if tach:
            tach.leer()
        t0 = time.time()
        time.sleep(10)
        dt = time.time() - t0
        pulsos = tach.leer() if tach else []
        vueltas = [rpm(p, dt) for p in pulsos]
        alarma = [i for i, r in enumerate(vueltas) if ciclo >= 40 and r < 300]
        estado = {'actualizado': time.strftime('%Y-%m-%dT%H:%M:%S'), 't_cpu': tc, 't_caja': tb, 'ciclo': ciclo,
                  'rpm': vueltas, 'alarma': ['entrada', 'salida'][alarma[0]] if alarma else None, 'modo': modo}
        for ruta in ('/run/bricohams/caja.json', salida_web):
            try:
                write_atomic(ruta, estado)
            except OSError:
                pass
        if forzado is not None:
            print('fan: ciclo %d %% · CPU %s °C · caja %s °C · rpm %s' % (ciclo, tc, tb, vueltas), flush=True)
            if time.time() >= fin:
                return 0
        if alarma:
            print('fan: AVISO ventilador %s parado (%s rpm con ciclo %d %%)' % (alarma, vueltas, ciclo), file=sys.stderr, flush=True)


if __name__ == '__main__':
    sys.exit(main())
