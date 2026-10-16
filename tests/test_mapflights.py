#!/usr/bin/env python3
"""v5.1: map.flights como destino adicional a RadarBox (conector Beast + MLAT con el UUID)."""
import importlib.machinery
import importlib.util
import os
import re
import subprocess
import sys
import tempfile

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
HELPER = os.path.join(RAIZ, 'files/bin/bricohams-mapflights.py')
loader = importlib.machinery.SourceFileLoader('mf', HELPER)
spec = importlib.util.spec_from_loader('mf', loader)
mf = importlib.util.module_from_spec(spec)
loader.exec_module(mf)

UUID = '0123abcd-4567-89ef-0123-456789abcdef'
NET = ('NET_OPTIONS="--net --net-heartbeat 60 --net-ro-size 1250 --net-ro-interval 0.05 --net-ri-port 0 '
       '--net-ro-port 30002 --net-sbs-port 30003 --net-bi-port 30004,30104 --net-bo-port 30005"')
BASE = 'RECEIVER_OPTIONS="--device-type rtlsdr --device 00001090 --gain auto --ppm 0"\n' + NET + '\nJSON_OPTIONS="--json-location-accuracy 2"\n'
CONECTOR = '--net-connector=feed.map.flights,30004,beast_reduce_plus_out,uuid=' + UUID


def leer(r):
    with open(os.path.join(RAIZ, r), encoding='utf-8') as fh:
        return fh.read()


# validación y normalización del UUID
assert mf.uuid_valido(UUID) == UUID
assert mf.uuid_valido(UUID.upper()) == UUID
assert mf.uuid_valido(UUID.replace('-', '')) == UUID
for malo in ('', 'mf_feed_' + 'a' * 32, '1234', UUID + '0', 'g' * 32, UUID.replace('a', 'z')):
    assert mf.uuid_valido(malo) is None, malo

# añadir, idempotente, sin tocar el resto de readsb
uno = mf.aplicar(BASE, UUID)
assert uno.count(CONECTOR) == 1, uno
assert '--net-bo-port 30005' in uno and 'RECEIVER_OPTIONS="--device-type rtlsdr' in uno and 'JSON_OPTIONS=' in uno
assert mf.aplicar(uno, UUID) == uno
# otros conectores (p. ej. de otra red) se conservan; el de map.flights se sustituye
otro = '--net-connector=feed.adsb.example,30004,beast_reduce_plus_out'
con_otro = BASE.replace('--net-bo-port 30005"', '--net-bo-port 30005 %s --net-connector feed.map.flights,30004,beast_out"' % otro)
dos = mf.aplicar(con_otro, UUID)
assert otro in dos and dos.count('feed.map.flights') == 1 and CONECTOR in dos, dos
# quitar
assert 'map.flights' not in mf.aplicar(uno, None)
assert '--net-bo-port 30005' in mf.aplicar(uno, None)
# sin NET_OPTIONS: lo crea con los puertos estándar de readsb
assert CONECTOR in mf.aplicar('RECEIVER_OPTIONS=""\n', UUID)

# línea de órdenes: escribe el fichero y no imprime el UUID entero
with tempfile.TemporaryDirectory() as d:
    f = os.path.join(d, 'readsb')
    with open(f, 'w') as fh:
        fh.write(BASE)
    r = subprocess.run([sys.executable, HELPER, f, UUID.upper()], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert UUID not in r.stdout
    assert CONECTOR in open(f).read()
    r = subprocess.run([sys.executable, HELPER, f, 'mf_feed_' + '0' * 32], capture_output=True, text=True)
    assert r.returncode == 1 and CONECTOR in open(f).read()
    r = subprocess.run([sys.executable, HELPER, f, UUID, 'x;rm -rf /', '30004'], capture_output=True, text=True)
    assert r.returncode == 1
    r = subprocess.run([sys.executable, HELPER, f, ''], capture_output=True, text=True)
    assert r.returncode == 0 and 'map.flights' not in open(f).read()
    r = subprocess.run([sys.executable, HELPER, '--uuid', UUID.replace('-', '')], capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.strip() == UUID

# instalador: conector, MLAT propio, RadarBox intacto, copia de seguridad
ins = leer('install.sh')
assert re.search(r'\n    mapflights\n    systemctl daemon-reload\n    systemctl enable readsb rbfeeder', ins)
fn = ins[ins.index('\nmapflights() {'):]
fn = fn[:fn.index('\n}\n')]
assert 'bricohams-mapflights.py' in fn and 'rbfeeder' not in fn.replace('RadarBox', '')
assert '--server \\${MAPFLIGHTS_MLAT_HOST}:\\${MAPFLIGHTS_MLAT_PORT} --user \\${MAPFLIGHTS_UUID}' in fn
assert '--results' not in fn and 'DynamicUser=yes' in fn   # ADR-55: sin reinyectar MLAT en readsb
assert 'chmod 600 "$ETC_BH/mapflights.env"' in fn and 'umask 077' in fn
assert 'systemctl disable --now bricohams-mapflights-mlat' in fn
assert 'etc/systemd/system/bricohams-mapflights-mlat.service' in ins

# bricohams.env.example: variables sin secretos
env = leer('bricohams.env.example')
for v in ('MAPFLIGHTS_FEED="no"', 'MAPFLIGHTS_UUID=""', 'MAPFLIGHTS_MLAT="yes"', 'MAPFLIGHTS_HOST="feed.map.flights"',
          'MAPFLIGHTS_PORT="30004"', 'MAPFLIGHTS_MLAT_HOST="mlat.map.flights"', 'MAPFLIGHTS_MLAT_PORT="31090"'):
    assert v in env, v

# comprobación y manual
chk = leer('files/bin/bricohams-check')
assert 'net-connector=feed.map.flights' in chk and 'bricohams-mapflights-mlat' in chk
man = leer('docs/manuales/04_ADSB.md')
assert 'map.flights' in man and 'MAPFLIGHTS_UUID' in man and 'bricohams-backup' in man

# ninguna clave mf_feed_ real en el kit
for base, _, ficheros in os.walk(RAIZ):
    if '.git' in base or '__pycache__' in base:
        continue
    for n in ficheros:
        if not os.path.isfile(os.path.join(base, n)):   # FIFO de lgpio (.lgd-nfy*) en la Pi: open() se bloquea
            continue
        try:
            t = open(os.path.join(base, n), encoding='utf-8').read()
        except (UnicodeDecodeError, OSError):
            continue
        assert not re.search(r'mf_feed_[0-9a-f]{8,}', t), os.path.join(base, n)

print('test_mapflights OK')
