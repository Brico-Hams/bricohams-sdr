#!/usr/bin/env python3
"""v4.5 · inventario de dispositivos con un /sys de mentira (SDR por su serie, RAK4631, LilyGO, lo que falta
y lo que está «en camino»), reglas udev, URLs de Meshtastic sin enseñar claves (y sin canales propios en el
.env.example), banner SSH (aviso legal sin pistas + estado al entrar) y su comprobación en la auditoría."""
import base64
import json
import os
import re
import shutil
import subprocess
import tempfile

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
BIN = os.path.join(RAIZ, 'files', 'bin')
T = tempfile.mkdtemp()


def poner(ruta, texto):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    open(ruta, 'w', encoding='utf-8').write(texto)


# ------------------------------------------------------------------ 1. inventario con /sys de mentira
SYS, DEV = os.path.join(T, 'sys'), os.path.join(T, 'dev')
os.makedirs(DEV)


def usb(bus, vid, pid, serie='', producto='', tty=None, clase='00'):
    d = os.path.join(SYS, 'bus', 'usb', 'devices', bus)
    for k, v in (('idVendor', vid), ('idProduct', pid), ('serial', serie), ('product', producto),
                 ('bDeviceClass', clase), ('speed', '480')):
        if v:
            poner(os.path.join(d, k), v + '\n')
    if tty:
        os.makedirs(os.path.join(d, bus + ':1.0', 'tty', tty))


usb('usb1', '1d6b', '0002')                                               # raíz: no cuenta
usb('1-1', '0bda', '2838', '00000103', 'RTL2838UHIDIR')                   # V3
usb('1-2', '0bda', '2832', '00001090', 'RadarBox FlightStick')            # ADS-B
usb('1-3', '239a', '8029', 'A1B2C3D4E5F60718', 'WisCore RAK4631 Board', 'ttyACM0')
usb('1-4', '1a86', '55d4', '5A7B012345', 'USB Single Serial', 'ttyACM1')
usb('1-5', '2109', '2817', '', 'USB2.0 Hub', clase='09')
envf = os.path.join(T, 'bricohams.env')
poner(envf, 'SERIAL_V3="00000103"\nSERIAL_ADSB="00001090"\nSERIAL_HAT="00000101"\nSERIAL_MINI="00000102"\n'
            'HARDWARE_PENDIENTE="HAT, Mini, SDRplay"\nHF_SDRPLAY="no"\n')
E = dict(os.environ, BH_SYS=SYS, BH_DEV=DEV, BRICOHAMS_ENV=envf, BH_REGLAS=os.path.join(T, 'reglas', '99-x.rules'))
D = os.path.join(BIN, 'bricohams-dispositivos')
inv = json.loads(subprocess.run(['python3', D, 'json'], env=E, capture_output=True, text=True, check=True).stdout)
roles = {x['vidpid'] + ':' + x['serie']: x.get('rol', '') for x in inv['usb']}
assert roles['0bda:2838:00000103'] == 'MULTIPERFIL + HF' and roles['0bda:2832:00001090'].startswith('ADS-B')
assert 'iGate LoRa APRS' in roles['239a:8029:A1B2C3D4E5F60718'] and 'Meshtastic 433' in roles['1a86:55d4:5A7B012345']
assert not any(x['vidpid'].startswith('1d6b') for x in inv['usb'])
faltan = {f['que']: f['pendiente'] for f in inv['faltan']}
assert faltan == {'HAT HackerGadgets (SATÉLITES)': True, 'Mini RTL-SDR (RADIOAFICIONADOS)': True}, faltan
txt = subprocess.run(['python3', D, 'inventario'], env=E, capture_output=True, text=True).stdout
assert 'en camino: no es un fallo' in txt and '[/dev/ttyACM0]' in txt
r = subprocess.run(['python3', D, 'identificar'], env=E, capture_output=True, text=True)
reglas = open(E['BH_REGLAS']).read()
assert 'ATTRS{idVendor}=="239a", ATTRS{idProduct}=="8029", ATTRS{serial}=="A1B2C3D4E5F60718", SYMLINK+="rak-aprs"' in reglas
assert 'SYMLINK+="lilygo-mesh"' in reglas and 'GROUP="dialout", MODE="0660"' in reglas, r.stdout
usb('1-6', '0bda', '2838', '12345678', 'RTL2838UHIDIR')                   # uno sin serie grabada
inv = json.loads(subprocess.run(['python3', D, 'json'], env=E, capture_output=True, text=True).stdout)
assert any('SIN ROL' in x.get('rol', '') for x in inv['usb'])

# ------------------------------------------------------------------ 2. URLs de Meshtastic
M = os.path.join(BIN, 'bricohams-mesh-url')
ej = open(os.path.join(RAIZ, 'bricohams.env.example'), encoding='utf-8').read()
urls = dict(re.findall(r'^(MESH_CHANNEL_URL|MESH433_CHANNEL_URL)="([^"]+)"', ej, re.M))
assert set(urls) == {'MESH_CHANNEL_URL', 'MESH433_CHANNEL_URL'}
for k, u in urls.items():
    j = json.loads(subprocess.run(['python3', M, 'json', u], capture_output=True, text=True, check=True).stdout)
    assert not any(c['propia'] for c in j['canales']), '%s del .env.example sin canales de clave propia' % k
    assert j['radio']['region'] == ('EU_868' if k == 'MESH_CHANNEL_URL' else 'EU_433')
j868 = json.loads(subprocess.run(['python3', M, 'json', urls['MESH_CHANNEL_URL']], capture_output=True, text=True).stdout)
assert j868['radio']['frecuencia_mhz'] == 869.618 and j868['radio']['sf'] == 7 and j868['radio']['bw_khz'] == 62.5
assert [c['nombre'] for c in j868['canales']][:3] == ['SFNarrow', 'Murcia', 'Cartagena']
j433 = json.loads(subprocess.run(['python3', M, 'json', urls['MESH433_CHANNEL_URL']], capture_output=True, text=True).stdout)
assert j433['radio']['modem'] == 'LONG_FAST' and j433['radio']['potencia_dbm'] == 10
# una URL con un canal de clave propia: «ver» no enseña la clave y «publica» lo quita
clave = bytes(range(32))
canal = b'\x12\x20' + clave + b'\x1a\x07Privado'
b = base64.urlsafe_b64decode(urls['MESH433_CHANNEL_URL'].split('#')[1] + '==')
priv = 'https://meshtastic.org/e/#' + base64.urlsafe_b64encode(b'\x0a' + bytes([len(canal)]) + canal + b).decode().rstrip('=')
ver = subprocess.run(['python3', M, 'ver', priv], capture_output=True, text=True).stdout
assert 'Privado' in ver and 'PROPIA AES-256' in ver
assert base64.b64encode(clave).decode() not in ver and clave.hex() not in ver, 'nunca enseña la clave'
assert subprocess.run(['python3', M, 'contar', priv], capture_output=True, text=True).stdout.strip() == '8'
pub = subprocess.run(['python3', M, 'publica', priv], capture_output=True, text=True).stdout.strip()
assert pub == urls['MESH433_CHANNEL_URL'], 'publica quita el canal propio y deja el resto igual'
assert subprocess.run(['python3', M, 'ver', 'https://meshtastic.org/e/#@@@'], capture_output=True, text=True).returncode == 1
S = open(os.path.join(RAIZ, 'install.sh'), encoding='utf-8').read()
assert 'bricohams-mesh-url" contar' in S and 'no cabe el privado' in S, 'con 8 canales no se añade el privado'
L = open(os.path.join(BIN, 'bricohams-lilygo'), encoding='utf-8').read()
assert 'meshtastic_cli --seturl "$MESH433_CHANNEL_URL"' in L and 'no de EU_433' in L
# v5.0 · SatDump encuentra sus plugins y el RTC se comprueba también sin root
assert 'ln -s /usr/lib/satdump /usr/local/lib/satdump' in S, 'enlace de plugins de SatDump'
CHK = open(os.path.join(BIN, 'bricohams-check'), encoding='utf-8').read()
assert '/sys/class/rtc/rtc0/time' in CHK and 'leída de /sys' in CHK, 'RTC leído de /sys si no hay hwclock (Trixie)'
assert 'grep -qs pcf85063 /sys/class/rtc/rtc0/name' in CHK, 'RTC detectado sin i2cdetect'
assert 'systemctl cat node_exporter' in CHK and '127.0.0.1:9100/metrics' in CHK, 'node_exporter manual adoptado'
for q, txt in (('"$CAM"', "el vídeo 'mastil' no está listo"), ('"$CAM"', 'foto de la cámara vieja'),
               ('"BME280 BMP280 sensor"', 'sensor.json viejo'), ('"Pico ventilador"', 'ventilador parado')):
    assert 'mal_hw %s "%s' % (q, txt) in CHK, txt
assert 'servicio_hw "BME280 BMP280 sensor" bricohams-wx' in CHK
# pendiente(): comportamiento real con bash (si lo hay)
import re as _re
import shutil as _sh
import subprocess as _sp
_bash = _sh.which('bash')
if _bash:
    _fn = _re.search(r'^pendiente\(\) \{.*?^\}\n', CHK, _re.S | _re.M).group(0)
    for env, nombre, esperado in (('BME280, Cámara, Pico', 'cámara camara CSI', 0), ('bme280', 'BME280 BMP280 sensor', 0),
                                  ('HAT, Mini', 'Pico ventilador', 1), ('', 'cámara camara CSI', 1),
                                  ('camara', 'cámara camara CSI', 0)):
        r = _sp.run([_bash, '-c', _fn + 'HARDWARE_PENDIENTE="%s"; pendiente "%s"' % (env, nombre)])
        assert r.returncode == esperado, (env, nombre, r.returncode)
assert 'sudo ln -s /usr/lib/satdump /usr/local/lib/satdump' in CHK, 'el check avisa del enlace de SatDump'

# ------------------------------------------------------------------ 3. banner SSH
R = os.path.join(T, 'raiz')
poner(R + '/etc/bricohams/bricohams.env', 'CALLSIGN="EA5ZZZ"\nSSL_DOMAIN="sdr.ejemplo.org"\n')
poner(R + '/etc/issue.net', 'Debian GNU/Linux 13\n')
poner(R + '/etc/motd', 'The programs included with the Debian GNU/Linux system are free software\n')
poner(R + '/run/bricohams-rak/rak-aprs.json', json.dumps({'rak': {'rx': 5, 'h': '41'}, 't_caja': 29.5,
                                                        'aprsis': {'conectado': True}, 'oidos': []}))
os.makedirs(R + '/proc')
for f in ('uptime', 'loadavg', 'meminfo'):
    shutil.copy('/proc/' + f, R + '/proc/' + f)
Eb = dict(os.environ, BH_RAIZ=R, BH_SIN_SYSTEMD='1', BH_SIN_COLOR='1', BH_DISP_JSON=json.dumps(inv))
BB = os.path.join(BIN, 'bricohams-banner')
r = subprocess.run(['bash', BB, 'instalar'], env=Eb, capture_output=True, text=True)
assert r.returncode == 0, r.stdout + r.stderr
issue = open(R + '/etc/issue.net', encoding='utf-8').read()
assert 'EA5ZZZ' in issue and 'AUTORIZADAS' in issue and '197 bis' in issue and 'RGPD' in issue
assert not re.search(r'debian|raspbian|kernel|\\[rvsnm]|\d+\.\d+\.\d+\.\d+|sdr\.ejemplo', issue, re.I), 'sin pistas antes de entrar'
assert open(R + '/etc/issue.net.bricohams-orig').read().startswith('Debian'), 'copia del original'
assert open(R + '/etc/motd').read() == '' and os.path.exists(R + '/etc/motd.bricohams-orig')
assert 'Banner /etc/issue.net' in open(R + '/etc/ssh/sshd_config.d/80-bricohams-banner.conf').read()
motd = subprocess.run(['bash', R + '/etc/update-motd.d/20-bricohams'], env=Eb, capture_output=True, text=True).stdout
for t in ('EA5ZZZ · sdr.ejemplo.org', 'Caja      interior 29.5 °C · humedad 41 %', 'LoRa APRS 5 paquetes', 'APRS-IS conectado',
          'MULTIPERFIL + HF', 'HAT HackerGadgets (SATÉLITES) · en camino', 'sudo bricohams-check'):
    assert t in motd, (t, motd)
poner(R + '/var/backups/bricohams-blindaje/pendiente', '')
motd = subprocess.run(['bash', R + '/etc/update-motd.d/20-bricohams'], env=Eb, capture_output=True, text=True).stdout
assert 'blindaje SIN CONFIRMAR' in motd
r = subprocess.run(['bash', BB, 'quitar'], env=Eb, capture_output=True, text=True)
assert open(R + '/etc/issue.net').read().startswith('Debian') and not os.path.exists(R + '/etc/ssh/sshd_config.d/80-bricohams-banner.conf')
# la auditoría avisa del issue.net que da pistas
poner(R + '/etc/bricohams/bricohams.env', 'CALLSIGN="EA5ZZZ"\n')
a = subprocess.run(['bash', os.path.join(BIN, 'bricohams-blindaje'), 'auditar'], env=dict(os.environ, BH_RAIZ=R),
                   capture_output=True, text=True).stdout
assert 'issue.net enseña el sistema' in a, a[-800:]
assert open(R + '/var/lib/bricohams/blindaje-nota').read().strip().endswith(')'), 'nota para el banner'
assert 'paso_banner' in S and ' banner importar ' in S and ' lilygo rak satelites ' in S
shutil.rmtree(T)
print('OK test_v45_dispositivos: inventario (SDR por serie, RAK, LilyGO, «en camino»), udev, URLs de Meshtastic '
      'sin claves, banner SSH (aviso sin pistas y estado al entrar) y su auditoría')
