#!/usr/bin/env python3
"""v4.5 · RAK4631 LoRa APRS: la lógica del firmware compilada en el PC (KISS, digipeater, baliza,
telemetría) contra la pasarela de la Pi (bricohams-rak-aprs): las tramas KISS que hace el firmware
las entiende la Pi y al revés, reglas de iGate, configuración desde el env y un servicio completo
con un RAK de mentira (pty) y un servidor APRS-IS de mentira."""
import importlib.machinery
import importlib.util
import json
import os
import pty
import shutil
import socket
import subprocess
import tempfile
import threading
import time

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
FW = os.path.join(RAIZ, 'firmware', 'rak4631-lora-aprs')
B = os.path.join(RAIZ, 'files', 'bin', 'bricohams-rak-aprs')
ldr = importlib.machinery.SourceFileLoader('rak', B)
spec = importlib.util.spec_from_loader('rak', ldr)
rak = importlib.util.module_from_spec(spec)
ldr.exec_module(rak)

# ------------------------------------------------------------------ 1. firmware en el PC
T = tempfile.mkdtemp()
host = None
if shutil.which('g++'):
    host = os.path.join(T, 'host_test')
    subprocess.run(['g++', '-std=c++17', '-Wall', '-Wno-sign-compare', '-I', os.path.join(FW, 'test', 'shim'), '-o', host,
                    os.path.join(FW, 'test', 'host_test.cpp')] + [os.path.join(FW, f) for f in
                    ('kiss_utils.cpp', 'digi_utils.cpp', 'aprs_utils.cpp')], check=True)


def h(*a):
    return subprocess.run([host] + list(a), capture_output=True, text=True).stdout.splitlines()


PAQ = 'EA5ZZZ-7>APLRT1,WIDE1-1:!3759.00N/00107.00W>hola LoRa'
if host:
    kiss_fw = bytes.fromhex(h('kiss', PAQ)[0])
    lector = rak.LectorKISS()
    (cmd, datos), = lector.alimentar(kiss_fw)
    assert cmd == 0 and rak.ax25_a_tnc2(datos) == PAQ, 'la Pi entiende el KISS del firmware'
    assert rak.kiss_frame(0, rak.tnc2_a_ax25(PAQ)) == kiss_fw, 'y la Pi lo codifica igual que el firmware'
    assert h('unkiss', rak.kiss_frame(0, rak.tnc2_a_ax25('EA1AAA>APRS,EA5BBB-2*,WIDE2-1:>prueba')).hex()) == \
        ['EA1AAA>APRS,EA5BBB-2*,WIDE2-1:>prueba'], 'el firmware entiende el KISS de la Pi (con *)'
    # digipeater (lógica de digi_utils.cpp del original)
    assert h('digi', '1', PAQ) == ['EA5ZZZ-7>APLRT1,N0CALL-10*:!3759.00N/00107.00W>hola LoRa']
    assert h('digi', '2', 'EA5ZZZ-7>APLRT1,WIDE2-2:>x') == ['EA5ZZZ-7>APLRT1,N0CALL-10*,WIDE2-1:>x']
    assert h('digi', '1', 'EA5ZZZ-7>APLRT1,EA1AAA*,WIDE1-1:>x') == [''], 'WIDE1-1 tiene que ser el primer salto'
    assert h('digi', '0', PAQ) == [''] and h('digi', '1', 'EA5ZZZ-7>APLRT1,WIDE1-1,NOGATE:>x') == ['']
    assert h('digi', '1', 'N0CALL-10>APZBH1,WIDE1-1:>mío') == [''], 'lo propio no se repite'
    assert h('dup', 'EA1AAA>B,WIDE1-1:hola', 'EA1AAA>B,EA5X*:hola') == ['1', '0'], 'duplicado en 25 s, no después'
    # baliza y telemetría
    b = h('beacon', '37.983812', '-1.128011')
    assert b[0] == 'N0CALL-10>APZBH1:!3759.03NL00107.68W&/A=000755 SDR BricoHams LoRa APRS Caja 23.4C', b
    assert b[1].startswith('N0CALL-10>APZBH1,WIDE1-1:!'), 'por RF lleva la ruta'
    t = h('telem')
    assert t[0] == 'N0CALL-10>APZBH1:T#001,143,40,205,7,2,10000000', t      # 31,5 °C -> (31,5+40)*2 = 143
    assert t[1] == 'N0CALL-10>APZBH1::N0CALL-10:PARM.TempCaja,HumCaja,Bateria,RxLoRa,Digi,GPS,TX,Digi'
    assert t[3].endswith(':EQNS.0,0.5,-40,0,1,0,0,0.02,0,0,1,0,0,1,0')
    # la baliza por KISS se sube a APRS-IS como propia
    assert rak.para_aprsis(b[0], True, 'N0CALL-10') == \
        'N0CALL-10>APZBH1,TCPIP*:!3759.03NL00107.68W&/A=000755 SDR BricoHams LoRa APRS Caja 23.4C'

# ------------------------------------------------------------------ 2. reglas de iGate
I = 'N0CALL-10'
assert rak.para_aprsis(PAQ, False, I) == 'EA5ZZZ-7>APLRT1,WIDE1-1,qAR,N0CALL-10:!3759.00N/00107.00W>hola LoRa'
for malo in ('EA1A>APRS,TCPIP*:>x', 'EA1A>APRS,NOGATE:>x', 'EA1A>APRS,RFONLY:>x', 'EA1A>APRS:?APRS?',
             'EA1A>APRS:}EA2B>APRS,TCPIP,EA1A*:>x', 'N0CALL-10>APRS:>bucle', 'roto'):
    assert rak.para_aprsis(malo, False, I) is None, malo
assert rak.para_aprsis('EA1A>APRS:>x', True, I) is None, 'como propio solo vale mi indicativo'

# ------------------------------------------------------------------ 3. configuración desde el env
for k in [k for k in os.environ if k.startswith(('RAK_', 'IGATE_', 'STATION_'))]:
    del os.environ[k]
os.environ.update({'IGATE_CALLSIGN': 'n0call-10', 'STATION_LAT': '37.983812', 'STATION_LON': '-1.128011',
                   'STATION_ASL': '230', 'RAK_TX': 'no', 'RAK_DIGI': '1', 'RAK_TEMP_OFFSET': '-1.5'})
c = rak.config_deseada()
assert c['callsign'] == 'N0CALL-10' and c['tx'] is False and c['digi'] == 1 and c['freq'] == 433775000
assert c['sf'] == 12 and c['bw'] == 125000 and c['tempOffset'] == -1.5 and c['symbol'] == 'L&'
assert 'APRS_PASSCODE' not in json.dumps(c) and not any('pass' in k.lower() for k in c), 'al RAK no van claves'
assert rak.difiere(dict(c, lat=37.9838122), c) == [] and rak.difiere(dict(c, power=10), c) == ['power']
cab = open(os.path.join(FW, 'configuration.h'), encoding='utf-8').read()
for clave in c:                                            # mismas claves que entiende el firmware
    assert '"%s"' % clave in open(os.path.join(FW, 'configuration.cpp'), encoding='utf-8').read(), clave
assert 'APZBH1' in cab and 'txActive        = false' in cab, 'por defecto el RAK solo escucha'

# ------------------------------------------------------------------ 4. servicio con un RAK y un APRS-IS de mentira
srv = socket.socket()
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(('127.0.0.1', 0))
srv.listen(1)
lineas = []


def aprsis():
    con, _ = srv.accept()
    con.settimeout(15)
    buf = b''
    try:
        while True:
            d = con.recv(4096)
            if not d:
                break
            buf += d
            while b'\r\n' in buf:
                l, buf = buf.split(b'\r\n', 1)
                lineas.append(l.decode())
    except OSError:
        pass


threading.Thread(target=aprsis, daemon=True).start()
maestro, esclavo = pty.openpty()
ruta_pty = os.ttyname(esclavo)
recibido = []


def rak_falso():
    lector = rak.LectorKISS()
    conf = {}
    fin = time.time() + 20
    enviado = False
    while time.time() < fin:
        try:
            d = os.read(maestro, 1024)
        except OSError:
            return
        for cmd, datos in lector.alimentar(d):
            t = datos.decode()
            recibido.append(t)
            if t == 'BH:CONF?':
                os.write(maestro, rak.kiss_frame(6, ('BH:CONF ' + json.dumps(conf)).encode()))
            elif t.startswith('BH:CFG '):
                conf = json.loads(t[7:])
                os.write(maestro, rak.kiss_frame(6, b'BH:CFGOK 1234'))
            elif t == 'BH:GET':
                st = {'fw': '1.0.0', 'radio': 'ok', 't': 27.3, 'sensor': 'SHTC3 (RAK1901)',
                      'gps': {'present': True, 'fix': True, 'sats': 8, 'lat': 37.983812, 'lon': -1.128011}}
                # el firmware 1.0.0 real manda «"vbat": nan» (despliegue N0CALL): la Pi no puede perder el estado
                os.write(maestro, rak.kiss_frame(6, ('BH:STATUS ' + json.dumps(st)[:-1] + ',"vbat": nan}').encode()))
                if not enviado:
                    enviado = True
                    os.write(maestro, rak.kiss_frame(6, b'BH:RX {"rssi":-97,"snr":6.5,"fe":120}'))
                    os.write(maestro, rak.kiss_frame(0, rak.tnc2_a_ax25(PAQ)))
                    os.write(maestro, rak.kiss_frame(0, rak.tnc2_a_ax25('EA1AAA>APRS,TCPIP*:>no se sube')))


threading.Thread(target=rak_falso, daemon=True).start()
run = os.path.join(T, 'run')
envf = os.path.join(T, 'bricohams.env')
assert rak.quitar_comillas('"N0CALL-15"      # vacío = IGATE_CALLSIGN') == 'N0CALL-15'
assert rak.quitar_comillas("'a # b'   # c") == 'a # b' and rak.quitar_comillas('yes  # x') == 'yes'
open(envf, 'w').write('IGATE_CALLSIGN="N0CALL-10"     # comentario\nAPRS_PASSCODE="12345"\nSTATION_LAT="37.983812"   # «¿y esto?»\n'
                      'STATION_LON="-1.128011"\nOWRX_GPS_DECIMALES="2"\n')
p = subprocess.Popen(['python3', B, 'servicio'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                     env=dict(os.environ, BRICOHAMS_ENV=envf, RAK_PUERTO=ruta_pty, RAK_RUN_DIR=run,
                              RAK_APRSIS_SERVER='127.0.0.1', RAK_APRSIS_PORT=str(srv.getsockname()[1])))
fin = time.time() + 15
estado = None
while time.time() < fin:
    try:
        estado = json.load(open(os.path.join(run, 'rak-aprs.json')))
        if estado.get('oidos') and any('qAR' in l for l in lineas):
            break
    except (OSError, ValueError):
        pass
    time.sleep(0.3)
p.terminate()
salida = p.communicate(timeout=5)[0]
assert recibido[:2] == ['BH:CONF?', recibido[1]] and recibido[1].startswith('BH:CFG '), recibido
assert json.loads(recibido[1][7:])['callsign'] == 'N0CALL-10'
assert lineas and lineas[0].startswith('user N0CALL-10 pass 12345 vers BricoHams-RAK'), lineas
assert 'EA5ZZZ-7>APLRT1,WIDE1-1,qAR,N0CALL-10:!3759.00N/00107.00W>hola LoRa' in lineas, (lineas, salida)
assert not any('no se sube' in l for l in lineas), 'TCPIP no se sube'
assert estado['t_caja'] == 27.3 and estado['rak']['gps']['lat'] == 37.98, 'posición pública redondeada'
o = [x for x in estado['oidos'] if x['de'] == 'EA5ZZZ-7'][0]
assert o['rssi'] == -97 and o['aprsis'] is True, estado['oidos']
assert [x for x in estado['oidos'] if x['de'] == 'EA1AAA'][0]['aprsis'] is False
assert '12345' not in json.dumps(estado) and '12345' not in salida, 'el passcode no sale en el estado ni el registro'

# ------------------------------------------------------------------ 5. JSON del RAK con nan y grabar() honesto
assert rak.json_rak('{"t":26.0,"vbat": nan,"x":-inf,"l":[nan],"s":"nan"}') == \
    {'t': 26.0, 'vbat': None, 'x': None, 'l': [None], 's': 'nan'}, 'nan/inf sueltos -> null; dentro de texto, no'
for f in ('sensor_utils.h', 'bricohams_rak_aprs.cpp', 'aprs_utils.cpp'):
    assert 'isnan(s.vbat)' not in open(os.path.join(FW, f), encoding='utf-8').read(), f
fb = os.path.join(T, 'fakebin')
os.makedirs(fb)
falso = os.path.join(T, 'ttyACM9')
open(falso, 'w').close()
for nombre, texto in (('systemctl', ''), ('adafruit-nrfutil', 'Failed to upgrade target. Error is: No data received on serial port.')):
    with open(os.path.join(fb, nombre), 'w') as fh:
        fh.write('#!/bin/sh\necho "%s"\nexit 0\n' % texto)
    os.chmod(os.path.join(fb, nombre), 0o755)
camino = os.environ['PATH']
os.environ.update({'PATH': fb + os.pathsep + camino, 'RAK_PUERTO': falso})
zip_falso = os.path.join(T, 'fw.zip')
open(zip_falso, 'w').close()
assert rak.grabar(zip_falso) != 0, 'adafruit-nrfutil sale con 0 aunque falle: no se puede dar por grabado'
with open(os.path.join(fb, 'adafruit-nrfutil'), 'w') as fh:
    fh.write('#!/bin/sh\necho "Activating new firmware"\necho "Device programmed."\nexit 0\n')
rak.time.sleep, dormir = (lambda s: None), rak.time.sleep
assert rak.grabar(zip_falso) == 0
rak.time.sleep = dormir
os.environ['PATH'] = camino
assert '1915:521f' in open(os.path.join(RAIZ, 'files', 'bin', 'bricohams-dispositivos'), encoding='utf-8').read()
shutil.rmtree(T)
print('OK test_rak_aprs: firmware (KISS, digipeater, baliza, telemetría) %s, reglas de iGate, configuración '
      'sin claves y servicio completo con RAK y APRS-IS de mentira' % ('compilado en el PC' if host else 'sin g++'))
