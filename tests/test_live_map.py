#!/usr/bin/env python3
"""ADS-B reciente, APRS-IS y mensajes de chat sin transmitir por RF."""
import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name, filename):
    loader = importlib.machinery.SourceFileLoader(name, os.path.join(ROOT, 'files', 'bin', filename))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


api = load('api', 'bricohams-api.py')
rak = load('rak', 'bricohams-rak-aprs')
with tempfile.TemporaryDirectory() as t:
    p = os.path.join(t, 'aircraft.json')
    records = [
        {'hex': 'abcdef', 'flight': '<script>', 'lat': 38, 'lon': -1, 'seen_pos': 1, 'alt_baro': 12000},
        {'hex': '123456', 'lat': 38, 'lon': -1, 'seen_pos': 61},
        {'hex': '123457', 'lat': float('nan'), 'lon': -1, 'seen_pos': 1},
        {'hex': '123458', 'lat': 91, 'lon': -1, 'seen_pos': 1},
        {'hex': '123459'},
        {'hex': 'bad-id', 'lat': 38, 'lon': -1, 'seen_pos': 1},
    ]
    with open(p, 'w') as f:
        json.dump({'now': 1000, 'aircraft': records}, f)
    d = api.aviones(p, ahora=1005)
    assert len(d['aircraft']) == 1 and d['aircraft'][0]['timestamp'] == 999000
    assert 'alt_baro' in d['aircraft'][0] and 'receiver' not in d
    for now in (1016, 990):
        try:
            api.aviones(p, ahora=now)
        except ValueError:
            pass
        else:
            raise AssertionError('acepta una instantanea caducada o futura')
    settings = os.path.join(t, 'settings.json')
    with open(settings, 'w') as f:
        json.dump({'receiver_name': 'keep', 'mqtt_enabled': True, 'mqtt_host': 'localhost'}, f)
    subprocess.run([sys.executable, os.path.join(ROOT, 'files', 'bin', 'bricohams-mqtt-settings.py'),
                    settings, '--lora', '--chat'], check=True)
    with open(settings) as f:
        s = json.load(f)
    assert s['receiver_name'] == 'keep' and s['mqtt_chat'] and s['mqtt_aprs']

packet = 'EA1AAA>APRS,TCPIP*::N0CALL   :hola{123'
m = rak.mensaje_chat(packet)
assert m == {'state': 'ChatMessage', 'name': 'EA1AAA -> N0CALL', 'message': 'hola'}, m
assert rak.mensaje_chat('EA2BBB>APRS:}' + packet) == m
for body in ('ack123', 'rej12', 'PARM.x', 'UNIT.x', 'EQNS.x', 'BITS.x', ''):
    assert rak.mensaje_chat('EA1AAA>APRS::N0CALL   :' + body) is None
assert rak.mensaje_chat('EA1AAA>APRS::N0CALL   :<img onerror=x>')['message'] == '<img onerror=x>'
assert rak.mensaje_chat('broken') is None


class MQTT:
    def __init__(self):
        self.sent = []

    def publicar(self, topic, data):
        self.sent.append((topic, data))
        return True


mqtt = MQTT()
chat = rak.ChatAPRS(mqtt)
assert chat.recibir(packet, 1000)
assert not chat.recibir(packet.replace('TCPIP*', 'WIDE1-1'), 1001)
assert chat.recibir(packet, 1301)
assert all(topic == 'aprs/CLIENT' for topic, _ in mqtt.sent)
pos = rak.aprs_mapa('EA1AAA>APRS,TCPIP*:!3805.00N/00000.00W>moving', origen='APRS-IS')
assert pos['source'] == 'EA1AAA' and 'freq' not in pos and 'APRS-IS' in pos['comment']
assert 'LoRa' not in pos['comment']
assert rak.aprs_mapa('EA1AAA>APRS:') is None
print('OK: ADS-B, APRS-IS, deduplicacion de chat y flags MQTT')
