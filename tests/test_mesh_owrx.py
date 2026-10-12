#!/usr/bin/env python3
"""v4.5 · integración directa con OpenWebRX+ por su MQTT: el publicador MQTT mínimo contra un broker de
mentira, los nodos Meshtastic al formato de owrx/meshtastic.py (posición propia redondeada, la de los demás
tal cual), el chat opcional y el servicio completo con una librería «meshtastic» de mentira; y lo oído por
el RAK4631 al formato de owrx/aprs (AprsParser.updateMap), con mensajes de APRS-IS a RF."""
import importlib.machinery
import importlib.util
import json
import os
import shutil
import socket
import struct
import subprocess
import tempfile
import threading
import time

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
BIN = os.path.join(RAIZ, 'files', 'bin')


def cargar(nombre, ruta):
    ldr = importlib.machinery.SourceFileLoader(nombre, ruta)
    m = importlib.util.module_from_spec(importlib.util.spec_from_loader(nombre, ldr))
    ldr.exec_module(m)
    return m


# ------------------------------------------------------------------ broker MQTT de mentira
class Broker:
    def __init__(self):
        self.srv = socket.socket()
        self.srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv.bind(('127.0.0.1', 0))
        self.srv.listen(5)
        self.puerto = self.srv.getsockname()[1]
        self.msgs, self.clientes = [], []
        threading.Thread(target=self._aceptar, daemon=True).start()

    def _aceptar(self):
        while True:
            c, _ = self.srv.accept()
            threading.Thread(target=self._cliente, args=(c,), daemon=True).start()

    def _cliente(self, c):
        buf = b''
        while True:
            try:
                d = c.recv(4096)
            except OSError:
                return
            if not d:
                return
            buf += d
            while len(buf) >= 2:
                tipo, i, n, mult = buf[0] >> 4, 1, 0, 1
                while True:
                    if i >= len(buf):
                        break
                    b = buf[i]
                    n += (b & 127) * mult
                    mult *= 128
                    i += 1
                    if not b & 128:
                        break
                if len(buf) < i + n:
                    break
                cuerpo, buf = buf[i:i + n], buf[i + n:]
                if tipo == 1:
                    self.clientes.append(cuerpo[12:].decode(errors='replace'))
                    c.sendall(b'\x20\x02\x00\x00')
                elif tipo == 3:
                    lt = struct.unpack('!H', cuerpo[:2])[0]
                    self.msgs.append((cuerpo[2:2 + lt].decode(), json.loads(cuerpo[2 + lt:].decode())))
                elif tipo == 12:
                    c.sendall(b'\xd0\x00')


br = Broker()
mq = cargar('bricohams_mqtt', os.path.join(BIN, 'bricohams_mqtt.py'))
p = mq.Publicador('127.0.0.1', br.puerto, 'prueba')
assert p.publicar('x/APRS', {'a': 'ñ' * 200})                    # cuerpo > 127 bytes: longitud de 2 bytes
p.latido()
time.sleep(0.3)
assert br.msgs[-1] == ('x/APRS', {'a': 'ñ' * 200}), br.msgs
assert mq.Publicador('127.0.0.1', 1, 'nadie').publicar('x', {}) is False, 'sin broker no bloquea ni falla'
assert mq.simbolo(',', 'M') == {'symbol': ',', 'table': 'M', 'index': 11, 'tableindex': 44}

# ------------------------------------------------------------------ Meshtastic -> formato de OpenWebRX+
M = cargar('mesh', os.path.join(BIN, 'bricohams-mesh-owrx'))
nodo = {'num': 0x1234abcd, 'user': {'longName': 'SDR BricoHams 433', 'shortName': 'SB43', 'hwModel': 'TLORA_V2_1_1P6',
                                    'role': 'CLIENT'},
        'position': {'latitude': 38.08, 'longitude': -1.25, 'altitude': 230},
        'deviceMetrics': {'voltage': 4.1, 'channelUtilization': 3.2, 'airUtilTx': 0.5, 'uptimeSeconds': 600}}
d = M.nodo_a_owrx(nodo['num'], nodo, 'mesh433', 433875000, decimales=2)
assert d['mode'] == 'Meshtastic' and d['src'] == 0x1234abcd and (d['lat'], d['lon']) == (38.08, -1.25), d
assert d['nickName'] == 'SB43' and d['longName'] == 'SDR BricoHams 433' and d['device'] == 'TLORA_V2_1_1P6'
assert d['battery'] == 4.1 and d['symbol']['table'] == 'M' and d['freq'] == 433875000 and d['timestamp'] > 1.7e12
assert M.nodo_a_owrx(1, {'user': {}}, 'mesh433', 1) is None, 'sin posición no va al mapa'
assert M.nodo_a_owrx(1, {'position': {'latitudeI': 380800000, 'longitudeI': -12500000}}, 'm', 1)['lat'] == 38.08
nodos = {}
n, t, extra = M.paquete(nodos, {'from': 7, 'to': M.BROADCAST, 'rxSnr': 6.25, 'rxRssi': -95, 'hopStart': 3, 'hopLimit': 1,
                                'decoded': {'portnum': 'TEXT_MESSAGE_APP', 'text': 'hola Murcia'}}, 'mesh433')
assert (n, t) == (7, 'hola Murcia') and 'saltos 2/3' in extra and 'SNR 6.25 dB' in extra
n, t, _ = M.paquete(nodos, {'from': 7, 'to': 9, 'decoded': {'portnum': 'TEXT_MESSAGE_APP', 'text': 'privado'}}, 'm')
assert t is None, 'los mensajes directos no salen nunca'
M.paquete(nodos, {'from': 7, 'decoded': {'portnum': 'POSITION_APP', 'position': {'latitude': 37.6, 'longitude': -0.98}}}, 'm')
M.paquete(nodos, {'from': 7, 'decoded': {'portnum': 'NODEINFO_APP', 'user': {'shortName': 'CT01'}}}, 'm')
assert M.nombre(nodos, 7) == 'CT01' and M.nodo_a_owrx(7, nodos[7], 'm', 1)['lat'] == 37.6

# ------------------------------------------------------------------ servicio con «meshtastic» de mentira
T = tempfile.mkdtemp()
falso = os.path.join(T, 'falso')
os.makedirs(os.path.join(falso, 'meshtastic'))
os.makedirs(os.path.join(falso, 'pubsub'))
open(os.path.join(falso, 'pubsub', '__init__.py'), 'w').write('''
class _Pub:
    def __init__(self): self.s = {}
    def subscribe(self, f, tema): self.s.setdefault(tema, []).append(f)
    def sendMessage(self, tema, **kw):
        for f in self.s.get(tema, []): f(**kw)
pub = _Pub()
''')
open(os.path.join(falso, 'meshtastic', '__init__.py'), 'w').write('')
open(os.path.join(falso, 'meshtastic', 'tcp_interface.py'), 'w').write('''
class TCPInterface:
    def __init__(self, hostname): raise OSError('meshtasticd no responde (sin HAT)')
''')
open(os.path.join(falso, 'meshtastic', 'serial_interface.py'), 'w').write('''
import threading, time
from pubsub import pub
class _Info: my_node_num = 0x1234abcd
class SerialInterface:
    def __init__(self, devPath):
        self.myInfo = _Info()
        self.nodes = {'!1234abcd': %r,
                      '!00000007': {'num': 7, 'user': {'shortName': 'CT01', 'longName': 'Cartagena 1'},
                                    'position': {'latitude': 37.605, 'longitude': -0.986}},
                      '!00000008': {'num': 8, 'user': {'shortName': 'SINP'}}}
        threading.Thread(target=self._rx, daemon=True).start()
    def _rx(self):
        time.sleep(1)
        pub.sendMessage('meshtastic.receive', packet={'from': 7, 'to': 0xFFFFFFFF, 'rxSnr': 5.0,
                        'decoded': {'portnum': 'TEXT_MESSAGE_APP', 'text': 'QSO de prueba'}}, interface=self)
        pub.sendMessage('meshtastic.receive', packet={'from': 9, 'decoded': {'portnum': 'POSITION_APP',
                        'position': {'latitude': 38.0, 'longitude': -1.1}}}, interface=self)
    def close(self): pass
''' % nodo)
puerto_lily = os.path.join(T, 'lilygo-mesh')
open(puerto_lily, 'w').close()
envf = os.path.join(T, 'bricohams.env')
open(envf, 'w').write('OWRX_GPS_DECIMALES="2"\nMESH_OWRX_CHAT="yes"\n')
run = os.path.join(T, 'run')
pr = subprocess.Popen(['python3', os.path.join(BIN, 'bricohams-mesh-owrx'), 'servicio'], stdout=subprocess.PIPE,
                      stderr=subprocess.STDOUT, text=True,
                      env=dict(os.environ, PYTHONPATH=falso, BRICOHAMS_ENV=envf, MESH_RUN_DIR=run,
                               MESH433_PUERTO=puerto_lily, BRICOHAMS_MQTT='127.0.0.1:%d' % br.puerto))
fin = time.time() + 15
while time.time() < fin and not (any(t.endswith('/CLIENT') for t, _ in br.msgs) and
                                  any(m.get('src') == 9 for t, m in br.msgs if t == 'mesh433/Meshtastic')):
    time.sleep(0.3)
time.sleep(1)
pr.terminate()
salida = pr.communicate(timeout=5)[0]
mesh = {m['src']: m for t, m in br.msgs if t == 'mesh433/Meshtastic'}
assert (mesh[0x1234abcd]['lat'], mesh[0x1234abcd]['lon']) == (38.08, -1.25), 'nuestro nodo, redondeado (manual 34)'
assert mesh[7]['lat'] == 37.605 and mesh[7]['nickName'] == 'CT01' and mesh[9]['lat'] == 38.0
assert 8 not in mesh, 'nodo sin posición: no va al mapa'
assert ('mesh433/CLIENT', {'state': 'ChatMessage', 'name': 'CT01', 'message': 'QSO de prueba'}) in br.msgs
est = json.load(open(os.path.join(run, 'mesh.json')))
assert est['fuentes']['mesh433']['conectado'] and est['fuentes']['mesh433']['nodos'] == 3
assert not est['fuentes']['mesh868']['conectado'] and 'sin HAT' in est['fuentes']['mesh868']['error']
assert 'bricohams-mesh-owrx' in br.clientes

# ------------------------------------------------------------------ LoRa APRS (RAK) -> formato de OpenWebRX+
R = cargar('rak', os.path.join(BIN, 'bricohams-rak-aprs'))
a = R.aprs_mapa('EA5ZZZ-7>APLRT1,WIDE1-1:!3805.00N/00000.00W>hola LoRa', {'rssi': -97, 'snr': 6.5})
assert a['mode'] == 'APRS' and a['source'] == 'EA5ZZZ-7' and a['path'] == ['WIDE1-1'] and a['freq'] == 433775000
assert (round(a['lat'], 4), round(a['lon'], 4)) == (0.0, -1.25) and a['symbol'] == mq.simbolo('>', '/')
assert a['comment'] == 'hola LoRa · LoRa 433,775 · -97 dBm · SNR 6.5 dB'
c = R.aprs_mapa('EA5YYY-9>APLRT1:=/5L!!<*e7>{?!test')          # comprimida (ejemplo de la especificación APRS)
assert abs(c['lat'] - 49.5) < 0.01 and abs(c['lon'] + 72.75) < 0.01 and c['symbol']['symbol'] == '>'
o = R.aprs_mapa('EA5KAO-10>APZBH1:;REPE70   *111111z3804.94N/00115.21Wr438.775')
assert o['type'] == 'object' and o['object'] == 'REPE70' and round(o['lat'], 2) == 38.08
assert R.aprs_mapa('EA5ZZZ>APRS:>solo estado') is None and R.aprs_mapa('roto') is None
assert R.aprs_mapa('EA5ZZZ>APRS:@111111z3804.9 N/00115.2 W-')['lat'] > 38, 'con ambigüedad'
# mensajes de APRS-IS a RF (messagesToRF): solo para estaciones oídas por RF y no si el remitente está en RF
oidas = {'EA5ZZZ-7': time.time() - 60, 'EA5LOC': time.time() - 30}
m = R.mensaje_a_rf('EA1AAA>APRS,TCPIP*,qAC,T2::EA5ZZZ-7 :hola{12', 'EA5KAO-10', oidas, time.time())
assert m == 'EA5KAO-10>APZBH1,WIDE1-1:}EA1AAA>APRS,TCPIP,EA5KAO-10*::EA5ZZZ-7 :hola{12', m
assert R.mensaje_a_rf('EA1AAA>APRS,TCPIP*::EA9XXX   :hola', 'EA5KAO-10', oidas, time.time()) is None
assert R.mensaje_a_rf('EA5LOC>APRS,TCPIP*::EA5ZZZ-7 :hola', 'EA5KAO-10', oidas, time.time()) is None
assert R.mensaje_a_rf('EA1AAA>APRS,TCPXX*::EA5ZZZ-7 :hola', 'EA5KAO-10', oidas, time.time()) is None
assert R.mensaje_a_rf('# aprsc 2.1', 'EA5KAO-10', oidas, time.time()) is None
assert R.mensaje_a_rf('EA1AAA>APRS,TCPIP*::EA5ZZZ-7 :viejo', 'EA5KAO-10', {'EA5ZZZ-7': 0}, time.time()) is None
shutil.rmtree(T)
print('OK test_mesh_owrx: MQTT mínimo, Meshtastic y LoRa APRS al formato de OpenWebRX+ (posición propia '
      'redondeada, objetos, comprimidas, ambigüedad), chat opcional, servicio sin HAT y mensajes APRS-IS → RF')
