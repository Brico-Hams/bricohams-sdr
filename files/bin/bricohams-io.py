#!/usr/bin/env python3
# =====================================================================
#  bricohams-io · EA5KAO · BricoHams
#  Servicio que habla con la Raspberry Pi Pico «bricohams-io» por USB
#  (/dev/bricohams-io). La Pico lee el BME280, el DS18B20 y el pluviómetro
#  y mueve los ventiladores, porque la cabecera de 40 pines de la Pi la
#  ocupa el HAT.
#   - Escribe lo último que manda la Pico en /run/bricohams/io.json
#     (lo leen bricohams-wx y bricohams-fan).
#   - Pasa a la Pico las órdenes de ventilador que deja bricohams-fan en
#     /run/bricohams/fan.cmd ("FAN 40 60").
#   - Convierte el contador de vuelcos del pluviómetro en marcas de tiempo
#     en /var/lib/bricohams/lluvia.json (las mismas que usaba el GPIO).
#  Uso:  bricohams-io                 (servicio)
#        bricohams-io estado          (última lectura)
#        bricohams-io ping            (¿responde la Pico?)
#        bricohams-io instalar [puerto]   copia el firmware con mpremote
# =====================================================================
import json
import os
import subprocess
import sys
import tempfile
import time

try:
    import serial  # python3-serial
except ImportError:
    serial = None

RUN = os.environ.get('IO_RUN_DIR', '/run/bricohams')
STATE = os.environ.get('STATE_DIRECTORY', '/var/lib/bricohams')
PORT = os.environ.get('IO_PORT', '/dev/bricohams-io')
FW = os.environ.get('IO_FIRMWARE', '/opt/bricohams/kit/firmware/pico-io/main.py')


def write_atomic(path, obj):
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix='.io-')
    with os.fdopen(fd, 'w') as f:
        json.dump(obj, f, ensure_ascii=False)
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


class Lluvia:
    """Pasa el contador acumulado de la Pico (que vuelve a 0 si se reinicia) a marcas de tiempo."""

    def __init__(self, fichero):
        self.fichero = fichero
        try:
            self.marcas = [float(x) for x in json.load(open(fichero))]
        except (OSError, ValueError):
            self.marcas = []
        self.boot = self.n = None

    def actualizar(self, boot, n, ahora=None):
        ahora = ahora or time.time()
        nuevos = 0
        if self.boot == boot and self.n is not None and n >= self.n:
            nuevos = n - self.n
        elif self.boot is not None and (boot != self.boot or (self.n is not None and n < self.n)):
            nuevos = n                     # la Pico se reinició: cuenta desde 0
        self.boot, self.n = boot, n
        if nuevos:
            nuevos = min(nuevos, 500)      # protección ante ruido
            self.marcas += [ahora] * nuevos
        self.marcas = [t for t in self.marcas if t > ahora - 86400 - 120]
        return nuevos

    def guardar(self):
        try:
            write_atomic(self.fichero, self.marcas)
        except OSError:
            pass


def leer_orden(path):
    try:
        with open(path) as f:
            s = f.read().strip()
        os.unlink(path)
        return s if s.startswith('FAN ') else None
    except OSError:
        return None


def servicio():
    if serial is None:
        print('io: falta python3-serial', file=sys.stderr)
        return 1
    lluvia = Lluvia(os.path.join(STATE, 'lluvia.json'))
    ultimo_guardado = 0
    while True:
        try:
            with serial.Serial(PORT, 115200, timeout=1) as s:
                print('io: Pico en %s' % PORT, flush=True)
                s.write(b'PING\n')
                ultimo = time.time()
                while True:
                    orden = leer_orden(os.path.join(RUN, 'fan.cmd'))
                    if orden:
                        s.write((orden + '\n').encode())
                    linea = s.readline().decode(errors='replace').strip()
                    if not linea.startswith('{'):
                        if time.time() - ultimo > 15:
                            raise OSError('la Pico no manda datos desde hace 15 s')
                        continue
                    try:
                        d = json.loads(linea)
                    except ValueError:
                        continue
                    if 'pong' in d:
                        continue
                    ultimo = time.time()
                    d['recibido'] = time.strftime('%Y-%m-%dT%H:%M:%S')
                    if 'rain' in d:
                        lluvia.actualizar(d.get('boot'), int(d['rain']))
                        if time.time() - ultimo_guardado > 30:
                            lluvia.guardar()
                            ultimo_guardado = time.time()
                    write_atomic(os.path.join(RUN, 'io.json'), d)
        except Exception as e:
            print('io: %s; reintento en 5 s' % e, file=sys.stderr, flush=True)
            time.sleep(5)


def estado():
    try:
        d = json.load(open(os.path.join(RUN, 'io.json')))
    except (OSError, ValueError):
        print('Sin datos de la Pico. ¿Está en marcha? systemctl status bricohams-io · ls -l %s' % PORT)
        return 1
    print(json.dumps(d, indent=1, ensure_ascii=False))
    return 0


def ping():
    if serial is None:
        print('falta python3-serial')
        return 1
    subprocess.run(['systemctl', 'stop', 'bricohams-io'], check=False)
    try:
        with serial.Serial(PORT, 115200, timeout=3) as s:
            s.write(b'PING\n')
            fin = time.time() + 5
            while time.time() < fin:
                linea = s.readline().decode(errors='replace').strip()
                if '"pong"' in linea:
                    print('✔ la Pico responde: %s' % linea)
                    return 0
                if linea.startswith('{'):
                    print('  datos: %s' % linea[:160])
        print('✘ la Pico no responde al PING')
        return 1
    finally:
        subprocess.run(['systemctl', 'start', 'bricohams-io'], check=False)


def instalar(puerto=None):
    puerto = puerto or PORT
    if not os.path.exists(FW):
        print('✘ No encuentro el firmware %s' % FW)
        return 1
    subprocess.run(['systemctl', 'stop', 'bricohams-io'], check=False)
    r = subprocess.run(['mpremote', 'connect', puerto, 'fs', 'cp', FW, ':main.py', '+', 'reset'])
    subprocess.run(['systemctl', 'start', 'bricohams-io'], check=False)
    if r.returncode == 0:
        print('✔ firmware copiado; en 5 s: sudo bricohams-io estado')
    else:
        print('✘ mpremote falló. ¿Tiene MicroPython la Pico? (manual 20: BOOTSEL + UF2)')
    return r.returncode


def main(argv):
    if len(argv) > 1:
        c = argv[1]
        if c == 'estado':
            return estado()
        if c == 'ping':
            return ping()
        if c == 'instalar':
            return instalar(argv[2] if len(argv) > 2 else None)
        print(__doc__ or 'uso: bricohams-io [estado|ping|instalar [puerto]]')
        return 1
    return servicio()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
