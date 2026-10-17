#!/usr/bin/env python3
"""v5.0: bricohams-satrec (grabación automática de pases) con un OpenWebRX+ websocket falso."""
import base64
import hashlib
import importlib.machinery
import importlib.util
import json
import math
import os
import random
import re
import socket
import struct
import tempfile
import threading
import time
import wave

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
os.environ['SATPASS_PY'] = os.path.join(RAIZ, 'files/bin/bricohams-satpass.py')
loader = importlib.machinery.SourceFileLoader('sr', os.path.join(RAIZ, 'files/bin/bricohams-satrec.py'))
spec = importlib.util.spec_from_loader('sr', loader)
sr = importlib.util.module_from_spec(spec)
loader.exec_module(sr)
random.seed(7)


def config_frame(**value):
    return 1, json.dumps({'type': 'config', 'value': value}).encode()


class PerfilWS:
    def __init__(self, frames):
        self.frames = iter(frames)
        self.s = self
        self.enviados = []
        self.cerrado = False

    def settimeout(self, timeout):
        assert timeout > 0

    def enviar(self, datos, op=1):
        self.enviados.append((op, datos))

    def json(self, datos):
        self.enviados.append((1, datos))

    def recibir(self):
        try:
            return next(self.frames)
        except StopIteration:
            raise socket.timeout()

    def cerrar(self):
        self.cerrado = True


real_ws = sr.WS
try:
    saludo = (1, b'CLIENT DE SERVER server=openwebrx')
    viejo = config_frame(sdr_id='sat', profile_id='meteor', center_freq=137500000, samp_rate=2048000)
    nuevo = config_frame(sdr_id='sat', profile_id='sat2m', samp_rate=2048000)
    frecuencia = config_frame(center_freq=145900000)
    for frames in (
        [saludo, viejo, nuevo, frecuencia, (10, b'')],
        [saludo, viejo, frecuencia, nuevo, (10, b'')],
        [saludo, config_frame(sdr_id='sat', profile_id='sat2m', center_freq=145900000,
                             samp_rate=2048000), (10, b'')],
        [saludo, viejo, config_frame(sdr_id='sat', profile_id='otro'), (10, b'')],
    ):
        falso_perfil = PerfilWS(frames)
        sr.WS = lambda url: falso_perfil
        perfil = 'sat|otro' if frames[-2] == config_frame(sdr_id='sat', profile_id='otro') else 'sat|sat2m'
        ws, conf = sr.conectar({'owrx': 'no-red', 'clave_fichero': ''}, perfil)
        esperado = 137500000 if perfil == 'sat|otro' else 145900000
        assert conf['center_freq'] == esperado and not ws.cerrado
        assert ws.enviados[-1] == (9, b'')
    falso_perfil = PerfilWS([saludo, viejo, nuevo, frecuencia])
    sr.WS = lambda url: falso_perfil
    try:
        sr.conectar({'owrx': 'no-red', 'clave_fichero': ''}, 'sat|sat2m')
        raise AssertionError('No debe aceptar sin confirmacion')
    except TimeoutError as x:
        assert 'no ha confirmado' in str(x) and falso_perfil.cerrado
finally:
    sr.WS = real_ws


# --- ADPCM: codificador de prueba que usa el mismo estado que el decodificador -----------
class Codif:
    def __init__(self):
        self.d = sr.Adpcm()

    def nib(self, x):
        mejor = None
        for n in range(16):
            i, p, s = self.d.indice, self.d.pred, self.d.paso
            v = self.d.nibble(n)
            if mejor is None or abs(v - x) < mejor[0]:
                mejor = (abs(v - x), n)
            self.d.indice, self.d.pred, self.d.paso = i, p, s
        self.d.nibble(mejor[1])
        return mejor[1]

    def bloque(self, muestras):
        """Como OpenWebRX+: «SYNC» + índice + predictor y 1001 bytes de audio."""
        out = bytearray(b'SYNC' + struct.pack('<hh', self.d.indice, self.d.pred))
        for k in range(0, len(muestras), 2):
            out.append(self.nib(muestras[k]) | (self.nib(muestras[k + 1]) << 4))
        return bytes(out)


seno = [int(8000 * math.sin(2 * math.pi * 1000 * i / 12000)) for i in range(2002 * 3)]
cod = Codif()
flujo = b''.join(cod.bloque(seno[k:k + 2002]) for k in range(0, len(seno), 2002))
dec = sr.Adpcm()
salida = dec.decodificar(b'\x00basura')
for k in range(0, len(flujo), 333):                   # troceado arbitrario, como llegan las tramas
    salida += dec.decodificar(flujo[k:k + 333])
assert salida == sr.Adpcm().decodificar(b'xx' + flujo)
assert len(salida) == len(seno), (len(salida), len(seno))
err = math.sqrt(sum((a - b) ** 2 for a, b in zip(salida[50:], seno[50:])) / (len(seno) - 50))
assert err < 400, err

# --- utilidades ----------------------------------------------------------------------
assert sr.locator(48.1467, 11.6081) == 'JN58td', sr.locator(48.1467, 11.6081)
assert sr.prefijo('IO-117 GreenCube') == 'IO117GREENCUBE' and sr.prefijo('TO-108') == 'TO108'
OWRX_FILES = re.compile(r'^[A-Z0-9]+-[0-9]+-[0-9]+(-[0-9]+)?(-[0-9]+)?\.(bmp|png|txt|mp3)$')
f = sr.nombre_fichero({'nombre': 'TO-108', 'hz': 145925000}, 1_800_000_000)
assert OWRX_FILES.match(f) and f == 'TO108-270115-080000-145925.mp3', f

cfg = sr.cfg_desde_env({'STATION_LAT': '48.1467', 'STATION_LON': '11.6081', 'STATION_ASL': '500', 'CALLSIGN': 'DL0XYZ',
                        'SATREC_MIN_EL': '20', 'SATREC_EXCLUIR': 'AO-91'})
T = 1_800_000_000


def pase(nombre, aos, el, modo='nfm', perfil='sat|sat2m', norad=1, hz=145800000):
    return {'nombre': nombre, 'norad': norad, 'aos': aos, 'los': aos + 600, 't_max': aos + 300, 'max_el': el,
            'hz': hz, 'modo': modo, 'perfil': perfil, 'duracion_s': 600, 'az_aos': 10, 'az_los': 200}


ps = [pase('ISS', T + 100, 45), pase('SO-50', T + 300, 60, norad=2),   # solapa con la ISS: fuera
      pase('BAJO', T + 2000, 12, norad=3), pase('AO-91', T + 3000, 50, norad=4),
      pase('METEOR-M2-4', T + 4000, 40, perfil='sat|meteor', norad=5), pase('X', T + 5000, 40, modo='bpsk', norad=6),
      pase('VIEJO', T - 1000, 80, norad=7)]
pl = sr.plan(ps, cfg, T)
assert [(p['nombre'], p['accion']) for p in pl] == [('ISS', 'grabar'), ('METEOR-M2-4', 'meteor')], pl
omitida = dict(cfg, omitir_pases={'1:%s' % (T + 100)})
assert [p['nombre'] for p in sr.plan(ps, omitida, T)] == ['SO-50', 'METEOR-M2-4']
assert '1:1234' in sr.cfg_desde_env({'SATREC_OMITIR_PASES': '1:1234'})['omitir_pases']
cal = sr.ics(pl, 'DL0XYZ')
assert cal.count('BEGIN:VEVENT') == 2 and 'DTSTART:20270115T080140Z' in cal and cal.endswith('END:VCALENDAR\r\n'), cal

for minuto, periodo in ((0, '0'), (15, '0'), (16, '1'), (30, '1'), (31, '2'), (45, '2'), (46, '3'), (59, '3')):
    c = {'amsat': 'SO-50_[FM]', 'estado': 'grabado', 'oido': True, 'aos': 0, 't_max': 1_800_000_000 - 1_800_000_000 % 3600 + minuto * 60}
    assert sr.informe_amsat(c, cfg)['SatPeriod'] == periodo, (minuto, sr.informe_amsat(c, cfg))
fa = sr.informe_amsat({'amsat': 'SO-50_[FM]', 'estado': 'grabado', 'oido': False, 'aos': T, 't_max': T}, cfg)
assert fa == {'SatName': 'SO-50_[FM]', 'SatReport': 'Not Heard', 'SatYear': '2027', 'SatMonth': '01', 'SatDay': '15',
              'SatHour': '08', 'SatPeriod': '0', 'SatCall': 'DL0XYZ', 'SatGridSquare': 'JN58td'}, fa
assert sr.informe_amsat({'amsat': 'SO-50_[FM]', 'estado': 'error: x', 'oido': None, 'aos': T}, cfg) is None
assert sr.informe_amsat({'amsat': 'RS-44_[V/u]', 'estado': 'grabado', 'aos': T}, cfg)['SatReport'] == ''


# --- «oído» por silenciamiento del ruido FM ----------------------------------------------
def wav_fm(ruta, segundos_ruido_antes, segundos_senal, segundos_ruido_despues):
    m = []
    for s, r in ((segundos_ruido_antes, True), (segundos_senal, False), (segundos_ruido_despues, True)):
        for i in range(s * 12000):
            m.append(int(random.gauss(0, 6000)) if r else int(3000 * math.sin(2 * math.pi * 800 * i / 12000) + random.gauss(0, 150)))
    with wave.open(ruta, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(12000)
        w.writeframes(struct.pack('<%dh' % len(m), *[max(-32768, min(32767, x)) for x in m]))


with tempfile.TemporaryDirectory() as d:
    a = os.path.join(d, 'a.wav')
    wav_fm(a, 12, 20, 15)
    oido, n = sr.oido_fm(a)
    assert oido is True and 18 <= n <= 21, (oido, n)
    wav_fm(a, 12, 0, 40)
    assert sr.oido_fm(a) == (False, 0), sr.oido_fm(a)

# --- Doppler de la ISS: sube al AOS, baja al LOS (±3,5 kHz en 2 m) -------------------------
if sr.importlib.util.find_spec('sgp4'):
    sp = sr._satpass()
    d = json.load(open(os.path.join(RAIZ, 'tests/datos/iss_omm.json')))
    import calendar
    c2 = dict(cfg, lat=38.0, lon=-1.0, asl=200)
    pp = sp.pases(sp.satrec_de_omm(d['omm']), 38.0, -1.0, 200, calendar.timegm((2026, 10, 3, 12, 0, 0)), min_el=30)
    assert pp, 'sin pase alto de la ISS'
    dop = sr.Doppler(d['omm'], c2, sp)
    p0 = pp[0]
    da, dm, dl = (dop.hz(145.8e6, t) - 145.8e6 for t in (p0['aos'] + 5, p0['t_max'], p0['los'] - 5))
    assert 2500 < da < 3700 and abs(dm) < 600 and -3700 < dl < -2500, (da, dm, dl)
    assert abs(dop.elevacion(p0['t_max']) - p0['max_el']) < 0.5
    doppler_ok = True
else:
    doppler_ok = False


# --- OpenWebRX+ websocket falso -----------------------------------------------------------
class FalsoOWRX(threading.Thread):
    def __init__(self, bloqueado=False):
        super().__init__(daemon=True)
        self.srv = socket.socket()
        self.srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv.bind(('127.0.0.1', 0))
        self.srv.listen(4)
        self.puerto = self.srv.getsockname()[1]
        self.recibido = []
        self.bloqueado = bloqueado
        self.parar = False

    def enviar(self, c, datos, op):
        n = len(datos)
        cab = bytes([0x80 | op]) + (bytes([n]) if n < 126 else bytes([126]) + struct.pack('>H', n))
        c.sendall(cab + datos)

    def leer(self, c, buf):
        while True:
            if len(buf) >= 6:
                n, i = buf[1] & 0x7F, 2
                if n == 126:
                    n, i = struct.unpack('>H', buf[2:4])[0], 4
                if len(buf) >= i + 4 + n:
                    m, d = buf[i:i + 4], buf[i + 4:i + 4 + n]
                    return buf[0] & 0x0F, bytes(x ^ m[k % 4] for k, x in enumerate(d)), buf[i + 4 + n:]
            x = c.recv(4096)
            if not x:
                return None, b'', b''
            buf += x

    def atender(self, c):
        cab = b''
        while b'\r\n\r\n' not in cab:
            cab += c.recv(1024)
        clave = re.search(rb'Sec-WebSocket-Key: (\S+)', cab).group(1)
        acc = base64.b64encode(hashlib.sha1(clave + b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest())
        c.sendall(b'HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: ' + acc + b'\r\n\r\n')
        buf, cod, audio = b'', Codif(), False
        c.settimeout(0.05)
        i = 0
        while not self.parar:
            try:
                op, d, buf = self.leer(c, buf)
            except socket.timeout:
                op = -1
            except OSError:
                break
            if op is None or op == 8:
                break
            if op == 9:
                self.enviar(c, b'', 10)
                continue
            if op == 1:
                t = d.decode()
                self.recibido.append(t)
                if t.startswith('SERVER DE CLIENT'):
                    self.enviar(c, b'CLIENT DE SERVER server=openwebrx version=falso', 1)
                    self.enviar(c, json.dumps({'type': 'config', 'value': {'sdr_id': 'ham', 'profile_id': '2m', 'center_freq': 145e6}}).encode(), 1)
                    self.enviar(c, b'\x01' + bytes(100), 2)                   # FFT: se ignora
                    continue
                j = json.loads(t)
                if j['type'] == 'selectprofile':
                    if self.bloqueado:
                        self.enviar(c, json.dumps({'type': 'log_message', 'value': 'This profile is locked, keeping current profile.'}).encode(), 1)
                    else:
                        sdr, prof = j['params']['profile'].split('|')
                        self.enviar(c, json.dumps({'type': 'config', 'value': {'sdr_id': sdr, 'profile_id': prof,
                                                                                'samp_rate': 2048000, 'audio_compression': 'adpcm'}}).encode(), 1)
                        self.enviar(c, json.dumps({'type': 'config', 'value': {'center_freq': 145900000}}).encode(), 1)
                if j['type'] == 'dspcontrol' and j.get('action') == 'start':
                    audio = True
            if audio:
                m = [int(random.gauss(0, 5000)) for _ in range(2002)]
                try:
                    self.enviar(c, b'\x02' + cod.bloque(m), 2)
                    c.sendall(b'\x89\x00')                               # ping del servidor
                except OSError:
                    break
                i += 1
                time.sleep(0.02)
        c.close()

    def run(self):
        self.srv.settimeout(0.2)
        while not self.parar:
            try:
                c, _ = self.srv.accept()
            except socket.timeout:
                continue
            threading.Thread(target=self.atender, args=(c,), daemon=True).start()


class DopplerFalso:
    def __init__(self):
        self.t0 = time.time()

    def hz(self, f0, ts):
        return f0 + 1000 * (ts - self.t0)


falso = FalsoOWRX()
falso.start()
with tempfile.TemporaryDirectory() as d:
    c3 = dict(cfg, owrx='ws://127.0.0.1:%d/ws/' % falso.puerto, clave_fichero=os.path.join(d, 'no-existe'))
    wav = os.path.join(d, 'g.wav')
    r = sr.grabar_audio(c3, pase('ISS', 0, 50), DopplerFalso(), wav, time.time() + 3.2)
    assert r['centro'] == 145900000 and -100000 <= r['offsets'][0] < -99800 and r['offsets'][1] > -98500, r
    with wave.open(wav) as w:
        assert w.getframerate() == 12000 and w.getnframes() == r['muestras'] > 12000, (w.getnframes(), r)
    msgs = [json.loads(x) for x in falso.recibido if x.startswith('{')]
    assert msgs[0] == {'type': 'connectionproperties', 'params': {'output_rate': 12000, 'hd_output_rate': 48000}}, msgs
    assert msgs[1] == {'type': 'selectprofile', 'params': {'profile': 'sat|sat2m'}}, msgs[1]
    dsp = [m['params'] for m in msgs if m['type'] == 'dspcontrol' and 'params' in m]
    assert dsp[0] == {'mod': 'nfm', 'low_cut': -7500, 'high_cut': 7500, 'offset_freq': r['offsets'][0], 'squelch_level': -150}, dsp
    assert len(dsp) >= 2 and dsp[1]['offset_freq'] >= r['offsets'][0] + 1500, dsp                # Doppler corregido

    # clave mágica opcional (nunca en el registro) y frecuencia fuera del perfil
    open(c3['clave_fichero'], 'w').write('secreto\n')
    falso.recibido.clear()
    ws, conf = sr.conectar(c3, 'sat|sat70')
    ws.cerrar()
    assert json.loads(falso.recibido[2])['params'] == {'profile': 'sat|sat70', 'key': 'secreto'}, falso.recibido
    try:
        sr.grabar_audio(c3, pase('IO-117', 0, 50, hz=435310000), None, wav, time.time() + 2)
        raise AssertionError('debía fallar fuera de banda')
    except ValueError as e:
        assert 'fuera del perfil' in str(e), e

    # servicio completo: un pase de SO-50 que empieza ya, informe AMSAT automático simulado
    sat = os.path.join(d, 'web')
    os.makedirs(sat)
    json.dump({'pases': [pase('SO-50', int(time.time()) + 5, 60, norad=27607)]}, open(os.path.join(sat, 'pases.json'), 'w'))
    json.dump({'satelites': [{'norad': 27607, 'nombre': 'SO-50', 'amsat': 'SO-50_[FM]'}]}, open(os.path.join(sat, 'lista.json'), 'w'))
    filesdir = os.path.join(d, 'tmp')
    os.makedirs(filesdir)
    c4 = dict(c3, pases=os.path.join(sat, 'pases.json'), lista=os.path.join(sat, 'lista.json'), salida=os.path.join(sat, 'grabaciones.json'),
              ics=os.path.join(sat, 'pases.ics'), dir=os.path.join(d, 'var'), files=filesdir, amsat='auto')
    enviados = []
    sr.enviar_amsat = lambda campos, url=None: enviados.append(campos) or True

    def grabar_falso(cfg, p, dop, wav, hasta, reloj):
        assert p['nombre'] == 'SO-50' and dop is None
        wav_fm(wav, 12, 25, 10)
        return {'muestras': 47 * 12000, 'centro': 436700000, 'offsets': [95000, 95000]}
    g = sr.Grabador(c4, grabar=grabar_falso)
    prox = g.vuelta()
    assert prox['nombre'] == 'SO-50'
    j = json.load(open(c4['salida']))
    cap = j['capturas'][0]
    assert cap['estado'].startswith('grabado') and cap['oido'] is True and cap['amsat_enviado'] is True, cap
    assert cap['amsat_form']['SatReport'] == 'Heard' and enviados[0]['SatName'] == 'SO-50_[FM]', (cap, enviados)
    assert j['plan'] == [] and 'BEGIN:VCALENDAR' in open(c4['ics'], encoding='utf-8').read()
    assert cap['en_files'] is bool(cap.get('fichero')), cap
    if cap.get('fichero'):                                  # con lame (Raspberry): MP3 y enlace en «Files»
        assert os.path.islink(os.path.join(filesdir, cap['fichero'])) and OWRX_FILES.match(cap['fichero']), os.listdir(filesdir)
        assert cap['en_files'] is True, cap
        c4['en_files'] = 0
        sr.enlazar_files(c4, g.capturas)
        assert os.listdir(filesdir) == []
    g.vuelta()                                              # no se repite el mismo pase
    assert len(g.capturas) == 1

    falso.bloqueado = True
    try:
        sr.conectar(c3, 'sat|sat2m', timeout=3)
        raise AssertionError('debía avisar del perfil bloqueado')
    except PermissionError as e:
        assert 'bloqueado' in str(e) and 'secreto' not in str(e)
falso.parar = True
print('OK test_satrec: ADPCM como el navegador, plan/ICS, AMSAT, «oído» FM, %swebsocket falso con Doppler, clave y servicio%s'
      % ('Doppler SGP4 de la ISS, ' if doppler_ok else '', ' con MP3 en Files' if cap.get('fichero') else ''))
