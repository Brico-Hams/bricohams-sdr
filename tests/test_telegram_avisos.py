#!/usr/bin/env python3
"""v5.0 · avisos a Telegram: módulo común (ritmo, repetidos, HTML escapado, token oculto),
registro de oyentes (indicativo o nombre), mensajes de CANAL Meshtastic (nunca directos) y
mensajes APRS del RAK y de OpenWebRX+ (solo los dirigidos a la estación por defecto)."""
import importlib.machinery
import importlib.util
import io
import os
import sys
import tempfile
import time
from contextlib import redirect_stderr

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
BIN = os.path.join(RAIZ, 'files', 'bin')
sys.path.insert(0, BIN)


def cargar(nombre, ruta):
    ldr = importlib.machinery.SourceFileLoader(nombre, ruta)
    m = importlib.util.module_from_spec(importlib.util.spec_from_loader(nombre, ldr))
    ldr.exec_module(m)
    return m


for k in ('TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID', 'APRS_TELEGRAM', 'APRS_TELEGRAM_CALLS', 'OYENTES_TELEGRAM'):
    os.environ.pop(k, None)

tgm = cargar('bricohams_telegram', os.path.join(BIN, 'bricohams_telegram.py'))


def esperar(cond, s=3):
    fin = time.time() + s
    while time.time() < fin and not cond():
        time.sleep(0.02)
    return cond()


# ------------------------------------------------------------------ módulo común
enviados = []
reloj = [1000.0]
a = tgm.Avisador('123:SECRETO', '-100', enviar=enviados.append, ahora=lambda: reloj[0])
assert a.configurado
assert not tgm.Avisador('', '', enviar=enviados.append).avisar('x'), 'sin credenciales no se manda nada'
assert a.avisar('hola') and esperar(lambda: enviados == ['hola'])
assert not a.avisar('hola'), 'repetido en 5 min'
reloj[0] += 301
assert a.avisar('hola'), 'pasados 5 min vuelve a valer'
for i in range(tgm.MAX_MIN):
    a.avisar('m%d' % i)
assert not a.avisar('uno más'), 'límite por minuto'
reloj[0] += 61
assert a.avisar('otro minuto')
assert not a.avisar(None) and not a.avisar('')
assert tgm.esc('<b>&') == '&lt;b&gt;&amp;'
assert tgm.limpio('a\nb\x07c') == 'a b c'


def falla(_):
    raise OSError('https://api.telegram.org/bot123:SECRETO/sendMessage 401')


err = io.StringIO()
with redirect_stderr(err):
    b = tgm.Avisador('123:SECRETO', '-100', enviar=falla)
    b.avisar('x')
    esperar(lambda: 'Telegram' in err.getvalue())
assert 'SECRETO' not in err.getvalue() and '***' in err.getvalue(), err.getvalue()

# ------------------------------------------------------------------ registro de oyentes
api = cargar('api', os.path.join(BIN, 'bricohams-api.py'))
assert api.bricohams_telegram is not None
avisos = []
with tempfile.TemporaryDirectory() as d:
    r = api.RegistroOyentes(os.path.join(d, 'o.sqlite'), aviso=lambda v, t: avisos.append((v, t)))
    assert r.registrar({'identificador': 'ea5abc', 'consentimiento': True})
    assert r.registrar({'identificador': 'Ana María', 'consentimiento': True})
    assert not r.registrar({'identificador': '<script>', 'consentimiento': True})
    assert not r.registrar({'identificador': 'EA5ABC', 'consentimiento': False})

    def roto(v, t):
        raise RuntimeError('sin red')
    r2 = api.RegistroOyentes(os.path.join(d, 'o2.sqlite'), aviso=roto)
    with redirect_stderr(io.StringIO()):
        assert r2.registrar({'identificador': 'EA5ABC', 'consentimiento': True}), 'el aviso no rompe el registro'
    assert r2.listar()[0][0] == 'EA5ABC'
    r.c.close()
    r2.c.close()
assert avisos == [('EA5ABC', 'indicativo'), ('Ana María', 'nombre')], avisos
t = api.aviso_oyente_telegram('EA5ABC', 'indicativo')
assert 'EA5ABC' in t and 'https://www.qrz.com/db/EA5ABC' in t, t
t = api.aviso_oyente_telegram('Ana <b>', 'nombre')
assert '&lt;b&gt;' in t and '<b>Oyente' in t, t
assert api.avisador_oyentes() is None, 'sin credenciales no hay aviso'
os.environ.update(TELEGRAM_TOKEN='1:x', TELEGRAM_CHAT_ID='-1', OYENTES_TELEGRAM='no')
assert api.avisador_oyentes() is None, 'OYENTES_TELEGRAM=no'
os.environ['OYENTES_TELEGRAM'] = 'yes'
assert callable(api.avisador_oyentes())
for k in ('TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID', 'OYENTES_TELEGRAM'):
    os.environ.pop(k)

# ------------------------------------------------------------------ Meshtastic: canal sí, directo nunca
mesh = cargar('mesh', os.path.join(BIN, 'bricohams-mesh-owrx'))
canales = [{'indice': 0, 'nombre': 'LongFast', 'primario': True}, {'indice': 1, 'nombre': 'BricoHams', 'primario': False}]
base = {'t': 1, 'dir': 'rx', 'canal': 1, 'de': 'PEPE', 'id': '!0000abcd', 'texto': 'hola <a>', 'directo': False,
        'snr': 6.5, 'rssi': -90}
t = mesh.aviso_telegram('mesh868', base, canales)
assert t and 'Meshtastic 868' in t and '#BricoHams' in t and 'PEPE' in t and '&lt;a&gt;' in t and 'SNR 6.5' in t, t
assert mesh.aviso_telegram('mesh433', dict(base, directo=True), canales) is None, 'los directos son privados'
assert mesh.aviso_telegram('mesh433', dict(base, dir='tx'), canales) is None, 'lo enviado no se reenvía'
assert 'canal 5' in mesh.aviso_telegram('mesh433', dict(base, canal=5), canales)


class Tg:
    def __init__(self):
        self.l = []

    def avisar(self, x):
        self.l.append(x)


class Mq:
    enviados = 0

    def publicar(self, *a):
        return True


tg = Tg()
f = mesh.Fuente('mesh433', 'serie', '/dev/null', 433875000, Mq(), 2, False, None, tg)
f.mio, f.estado['canales'] = 0x1234, canales
f.nodos[0xabcd] = {'num': 0xabcd, 'user': {'shortName': 'PEPE'}}
f.recibido({'from': 0xabcd, 'to': mesh.BROADCAST, 'channel': 0, 'decoded': {'portnum': 'TEXT_MESSAGE_APP', 'text': 'cq'}})
f.recibido({'from': 0xabcd, 'to': 0x1234, 'channel': 0, 'decoded': {'portnum': 'TEXT_MESSAGE_APP', 'text': 'secreto'}})
assert len(tg.l) == 1 and '#LongFast' in tg.l[0] and 'cq' in tg.l[0] and 'secreto' not in tg.l[0], tg.l

# ------------------------------------------------------------------ APRS por el RAK (RF y APRS-IS)
os.environ.update(CALLSIGN='EA0TST', IGATE_CALLSIGN='EA0TST-10', RAK_CALLSIGN='')
rak = cargar('rak', os.path.join(BIN, 'bricohams-rak-aprs'))
propios = rak.indicativos_propios()
assert propios == {'EA0TST'}, propios
para_mi = 'EA1XYZ-7>APRS,WIDE1-1::EA0TST-10:hola <amigo>{12'
t = rak.aviso_aprs(para_mi, propios, 'propios', 'RF 433')
assert t and 'EA1XYZ-7' in t and 'EA0TST-10' in t and '&lt;amigo&gt;' in t and '{12' not in t, t
otro = 'EA1XYZ-7>APRS::EA9OTR   :hola'
assert rak.aviso_aprs(otro, propios, 'propios') is None
assert rak.aviso_aprs(otro, propios, 'todos')
assert rak.aviso_aprs(para_mi, propios, 'no') is None
assert rak.aviso_aprs('EA1XYZ>APRS::EA0TST   :ack12', propios) is None, 'acuses no'
assert rak.aviso_aprs('EA0TST-5>APRS::EA0TST-10:eco', propios, 'todos') is None, 'lo nuestro no'
assert rak.aviso_aprs('EA1XYZ>APRS:!3800.00N/00100.00W-', propios, 'todos') is None, 'posiciones no'
for k in ('CALLSIGN', 'IGATE_CALLSIGN', 'RAK_CALLSIGN'):
    os.environ.pop(k)

# ------------------------------------------------------------------ APRS que decodifica OpenWebRX+ (MQTT openwebrx/APRS)
vis = cargar('visitas', os.path.join(BIN, 'bricohams-visitas.py'))
os.environ.update(APRS_TELEGRAM='propios', APRS_TELEGRAM_CALLS='EA0TST,EA0TST-10,')
avisos = []
with tempfile.TemporaryDirectory() as d:
    v = vis.Visitas(vis.abrir_db(os.path.join(d, 'v.sqlite')), vis.Geo(os.path.join(d, 'no.mmdb')), avisos.append,
                    ahora=lambda: 5000.0)
    msg = {'mode': 'APRS', 'type': 'message', 'source': 'EA1XYZ-7', 'addressee': 'EA0TST', 'message': 'qsl? <x>',
           'freq': 144800000}
    v.evento(msg)
    v.evento(msg)
    v.evento(dict(msg, addressee='EA9OTR'))
    v.evento(dict(msg, source='EA0TST-9'))
    v.evento({'mode': 'APRS', 'type': 'regular', 'source': 'EA1XYZ'})
    assert len(avisos) == 1 and '144.800 MHz' in avisos[0] and '&lt;x&gt;' in avisos[0], avisos
    os.environ['APRS_TELEGRAM'] = 'todos'
    v.evento(dict(msg, addressee='EA9OTR'))
    assert len(avisos) == 2, avisos
    os.environ['APRS_TELEGRAM'] = 'no'
    v.evento(dict(msg, message='otro'))
    assert len(avisos) == 2, avisos
    v.db.close()

print('OK test_telegram_avisos: módulo común, oyentes, Meshtastic de canal y mensajes APRS a Telegram')
