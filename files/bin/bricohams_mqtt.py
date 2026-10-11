"""BricoHams v4.5 · publicador MQTT 3.1.1 mínimo (QoS 0, sin dependencias) para el broker local.

Lo usan bricohams-rak-aprs y bricohams-mesh-owrx para pintar en el MAPA de OpenWebRX+ lo que oyen el
RAK4631 (LoRa APRS) y los nodos Meshtastic: OpenWebRX+ (1.2.122+) se suscribe a «+/APRS», «+/Meshtastic»
y «+/CLIENT» de su broker (owrx/mqtt.py, MqttSubscriber) y lo pone en el mapa como si lo hubiera
decodificado él (ADR-50). Se instala en /usr/local/lib/bricohams.
"""
import json
import os
import socket
import struct
import time


def _cadena(s):
    b = s.encode('utf-8')
    return struct.pack('!H', len(b)) + b


def _longitud(n):
    out = bytearray()
    while True:
        d, n = n % 128, n // 128
        out.append(d | (0x80 if n else 0))
        if not n:
            return bytes(out)


class Publicador:
    def __init__(self, host='127.0.0.1', puerto=1883, cliente=None, usuario='', clave=''):
        self.host, self.puerto = host, int(puerto)
        self.cliente = cliente or 'bricohams-%d' % os.getpid()
        self.usuario, self.clave = usuario, clave
        self.sock, self.reintento, self.enviados = None, 0.0, 0

    def conectar(self):
        if self.sock or time.time() < self.reintento:
            return self.sock is not None
        try:
            s = socket.create_connection((self.host, self.puerto), timeout=5)
            flags = 0x02 | (0x80 if self.usuario else 0) | (0x40 if self.clave else 0)
            var = _cadena('MQTT') + bytes([4, flags]) + struct.pack('!H', 60)
            pay = _cadena(self.cliente) + (_cadena(self.usuario) if self.usuario else b'') + \
                (_cadena(self.clave) if self.clave else b'')
            s.sendall(bytes([0x10]) + _longitud(len(var) + len(pay)) + var + pay)
            r = s.recv(4)
            if len(r) < 4 or r[0] != 0x20 or r[3] != 0:
                raise OSError('el broker rechaza la conexión (%s)' % r.hex())
            s.settimeout(5)
            self.sock = s
            return True
        except OSError:
            self.sock, self.reintento = None, time.time() + 30
            return False

    def publicar(self, tema, datos):
        """Publica JSON (QoS 0). Devuelve False si no hay broker (no bloquea más de 5 s)."""
        if not self.conectar():
            return False
        carga = json.dumps(datos, ensure_ascii=False, separators=(',', ':')).encode('utf-8') \
            if not isinstance(datos, (bytes, str)) else (datos.encode('utf-8') if isinstance(datos, str) else datos)
        var = _cadena(tema)
        try:
            self.sock.sendall(bytes([0x30]) + _longitud(len(var) + len(carga)) + var + carga)
            self.enviados += 1
            return True
        except OSError:
            self.cerrar()
            return False

    def latido(self):
        if self.sock:
            try:
                self.sock.sendall(b'\xc0\x00')          # PINGREQ
            except OSError:
                self.cerrar()

    def cerrar(self):
        try:
            if self.sock:
                self.sock.close()
        except OSError:
            pass
        self.sock, self.reintento = None, time.time() + 10


def simbolo(sym, tabla):
    """Igual que owrx.aprs.getSymbolData: el mapa de OpenWebRX+ dibuja el icono con esto."""
    return {'symbol': sym, 'table': tabla, 'index': ord(sym) - 33, 'tableindex': ord(tabla) - 33}


def redondear(v, decimales):
    try:
        return round(float(v), decimales) if decimales is not None else float(v)
    except (TypeError, ValueError):
        return None
