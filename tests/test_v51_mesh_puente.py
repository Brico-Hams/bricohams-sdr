#!/usr/bin/env python3
"""v5.1 · bricohams-mesh-puente: interfaz web de Meshtastic para el LilyGO 433 por USB.
Un único dueño del puerto serie que reparte la radio a la API «stream» (TCP 4404, la de
meshtasticd) y a la API HTTP del cliente web (4480), con un LilyGO de mentira."""
import http.client
import importlib.machinery
import importlib.util
import os
import queue
import socket
import threading
import time

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
ldr = importlib.machinery.SourceFileLoader('puente', os.path.join(RAIZ, 'files', 'bin', 'bricohams-mesh-puente'))
P = importlib.util.module_from_spec(importlib.util.spec_from_loader('puente', ldr))
ldr.exec_module(P)

# ---------------------------------------------------------------- 1. tramas
assert P.trama(b'\x01\x02') == b'\x94\xc3\x00\x02\x01\x02'
try:
    P.trama(b'x' * 513)
    raise AssertionError('más de 512 bytes no es una trama')
except ValueError:
    pass
L = P.Lector()
flujo = b'\xc3' * 32 + b'INFO | ??:??:?? 3 [Router] arranque\r\n' + P.trama(b'AB') + b'\x94\xc3\xff\xff' + P.trama(b'C' * 300)
partes = []
for i in range(0, len(flujo), 7):                      # llega a trozos, como por USB
    partes += L.alimentar(flujo[i:i + 7])
assert partes == [b'AB', b'C' * 300], partes
assert b'arranque' in bytes(L.texto), 'el registro de depuración del nodo no se pierde ni rompe nada'
assert L.alimentar(b'\x94') == [] and L.alimentar(b'\xc3\x00\x01Z') == [b'Z'], '0x94 al final de un trozo'

# ToRadio.want_config_id es el campo 3 (varint): el puente lo reconoce por el primer byte 0x18
try:
    from meshtastic.protobuf import mesh_pb2
    assert mesh_pb2.ToRadio(want_config_id=1234).SerializeToString()[:1] == b'\x18'
except ImportError:
    pass


# ---------------------------------------------------------------- 2. LilyGO de mentira
class Radio:
    abiertas = 0

    def __init__(self):
        Radio.abiertas += 1
        self.entrada, self.recibido, self.cerrada = queue.Queue(), bytearray(), False

    def read(self, n):
        try:
            d = self.entrada.get(timeout=0.1)
        except queue.Empty:
            return b''
        if d is None:
            raise OSError('USB desenchufado')
        return d

    def write(self, b):
        self.recibido += b

    def close(self):
        self.cerrada = True


radios = []


def abrir():
    r = Radio()
    radios.append(r)
    return r


pu = P.Puente(abrir)
parar = threading.Event()
threading.Thread(target=pu.bucle_radio, args=(parar,), daemon=True).start()
listo = []
threading.Thread(target=pu.servidor_tcp, args=(0, listo), daemon=True).start()
web = pu.servidor_http(0)
fin = time.time() + 5
while (not listo or pu.radio is None) and time.time() < fin:
    time.sleep(0.05)
assert listo and pu.radio is not None
assert radios[0].recibido.startswith(b'\xc3' * 32), 'despierta la API serie del nodo'


def esperar(cond, s=3):
    fin = time.time() + s
    while time.time() < fin:
        if cond():
            return True
        time.sleep(0.02)
    return False


# dos clientes TCP (mapa de OpenWebRX+ y panel /settings): los dos oyen la radio, los dos le hablan
c1 = socket.create_connection(('127.0.0.1', listo[0]))
c2 = socket.create_connection(('127.0.0.1', listo[0]))
assert esperar(lambda: len(pu.clientes) == 2)
c1.sendall(b'\xc3' * 32 + P.trama(b'\x18\x01'))                     # como la librería oficial
assert esperar(lambda: P.trama(b'\x18\x01') in bytes(radios[0].recibido))
radios[0].entrada.put(P.trama(b'nodo-1') + b'ruido')
for c in (c1, c2):
    c.settimeout(3)
    assert c.recv(100) == P.trama(b'nodo-1'), 'lo de la radio llega entero a cada cliente'
assert pu.cuenta['de_radio'] == 1 and pu.cuenta['a_radio'] == 1


def pide(metodo, ruta, cuerpo=None):
    c = http.client.HTTPConnection('127.0.0.1', web.server_address[1], timeout=5)
    c.request(metodo, ruta, body=cuerpo)
    r = c.getresponse()
    return r.status, r.read()


# cliente web: no recibe nada hasta que mira; luego cola propia, en orden, de una en una
radios[0].entrada.put(P.trama(b'antes'))
assert esperar(lambda: pu.cuenta['de_radio'] == 2)
assert pide('GET', '/api/v1/fromradio?all=false') == (200, b''), 'sin cliente web no se acumula nada'
assert pide('PUT', '/api/v1/toradio', b'\x18\x02') == (200, b'')
assert esperar(lambda: P.trama(b'\x18\x02') in bytes(radios[0].recibido))
for x in (b'cfg-1', b'cfg-2'):
    radios[0].entrada.put(P.trama(x))
assert esperar(lambda: pu.cuenta['de_radio'] == 4)
assert pide('GET', '/api/v1/fromradio') == (200, b'cfg-1') and pide('GET', '/api/v1/fromradio') == (200, b'cfg-2')
assert pide('GET', '/api/v1/fromradio') == (200, b'')
assert pide('PUT', '/api/v1/toradio', b'x' * 600)[0] == 400 and pide('GET', '/nada')[0] == 404
assert pide('PUT', '/api/v1/otra', b'x')[0] == 404
st, cuerpo = pide('GET', '/api/v1/estado')
assert st == 200 and b'"clientes_tcp": 2' in cuerpo and b'"radio": true' in cuerpo
# want_config nuevo desde la web: se vacía la cola vieja
radios[0].entrada.put(P.trama(b'viejo'))
assert esperar(lambda: pu.cuenta['de_radio'] == 5)
pide('PUT', '/api/v1/toradio', b'\x18\x03')
assert pide('GET', '/api/v1/fromradio') == (200, b'')

# USB desenchufado: avisa (503 en la web), cierra y vuelve a abrir solo
radios[0].entrada.put(None)
assert esperar(lambda: pu.radio is None, 2) and radios[0].cerrada
assert pide('PUT', '/api/v1/toradio', b'\x18\x04')[0] == 503
assert esperar(lambda: pu.radio is not None and len(radios) == 2, 8), 'reabre a los 5 s'
c1.close()
assert esperar(lambda: len(pu.clientes) == 1)
c2.close()
parar.set()
web.shutdown()
# ---------------------------------------------------------------- 3. con la librería oficial (si está)
try:
    import meshtastic.tcp_interface
    from meshtastic.protobuf import channel_pb2, mesh_pb2
except ImportError:
    meshtastic = None
if meshtastic:
    class NodoFalso(Radio):
        """Contesta al want_config como un LilyGO: my_info, su nodo, el canal y config_complete_id."""
        def __init__(self):
            Radio.__init__(self)
            self.lector = P.Lector()

        def write(self, b):
            for crudo in self.lector.alimentar(b):
                t = mesh_pb2.ToRadio()
                t.ParseFromString(crudo)
                if t.HasField('want_config_id'):
                    for f in (mesh_pb2.FromRadio(my_info=mesh_pb2.MyNodeInfo(my_node_num=0x1234)),
                              mesh_pb2.FromRadio(node_info=mesh_pb2.NodeInfo(num=0x1234, user=mesh_pb2.User(
                                  id='!00001234', long_name='SDR BricoHams 433', short_name='SB43'))),
                              mesh_pb2.FromRadio(channel=channel_pb2.Channel(index=0, role=channel_pb2.Channel.Role.PRIMARY)),
                              mesh_pb2.FromRadio(config_complete_id=t.want_config_id)):
                        self.entrada.put(P.trama(f.SerializeToString()))
    pu2 = P.Puente(NodoFalso)
    parar2, listo2 = threading.Event(), []
    threading.Thread(target=pu2.bucle_radio, args=(parar2,), daemon=True).start()
    threading.Thread(target=pu2.servidor_tcp, args=(0, listo2), daemon=True).start()
    assert esperar(lambda: listo2 and pu2.radio is not None)
    # el mapa (bricohams-mesh-owrx) y el panel (bricohams-mesh-admin) a la vez, como en la Pi
    ifs = [meshtastic.tcp_interface.TCPInterface(hostname='127.0.0.1', portNumber=listo2[0], timeout=15) for _ in range(2)]
    assert all(i.getLongName() == 'SDR BricoHams 433' and i.myInfo.my_node_num == 0x1234 for i in ifs)
    for i in ifs:
        i.close()
    parar2.set()
s = open(os.path.join(RAIZ, 'files', 'bin', 'bricohams-mesh-puente'), encoding='utf-8').read()
assert "('127.0.0.1', puerto)" in s and s.count("'127.0.0.1'") >= 2, 'solo escucha en la propia Pi'
print('OK test_v51_mesh_puente: tramas serie de Meshtastic, dos clientes TCP y el cliente web HTTP '
      'sobre un único puerto serie, want_config, límites y reconexión del USB')
