#!/usr/bin/env python3
# =====================================================================
#  bricohams-satrec · BricoHams  (v5.0)
#  Graba solo los pases de satélites calculados por bricohams-satpass:
#   - lee plugins/receiver/satelites/pases.json y programa los pases que
#     superan SATREC_MIN_EL (tareas programadas, también en pases.ics);
#   - al AOS se conecta a OpenWebRX+ como un oyente más (websocket local),
#     pone el perfil del pase en el receptor de satélites, corrige el Doppler
#     con SGP4 cada 2 s y guarda el audio (MP3) hasta el LOS;
#   - las grabaciones quedan en /var/lib/bricohams/satelites/grabaciones y
#     las últimas se enlazan en «Files» de OpenWebRX+ (SATREC_FILES_DIR);
#   - los METEOR solo necesitan el perfil «meteor»: las imágenes LRPT las
#     saca el servicio de fondo de OpenWebRX+ (SatDump) y salen en «Files»;
#   - en FM mide si el satélite se ha oído (silenciamiento del ruido FM) y
#     prepara el informe para AMSAT (https://www.amsat.org/status/).
#  Salida web: satelites/grabaciones.json y satelites/pases.ics
#  Uso: bricohams-satrec              (servicio bricohams-satrec)
#       bricohams-satrec --plan       (muestra los pases que se grabarán)
#       bricohams-satrec --probar 15  (graba 15 s del perfil SATREC_PRUEBA_PERFIL)
# =====================================================================
import base64
import importlib.machinery
import importlib.util
import json
import math
import os
import re
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import wave
from datetime import datetime, timezone

HTDOCS = os.environ.get('HTDOCS', '/usr/lib/python3/dist-packages/htdocs')
C_KMS = 299792.458
OMEGA_TIERRA = 7.2921159e-5
AMSAT_URL = 'https://www.amsat.org/status/submit.php'
TASA = 12000


def _satpass():
    ruta = os.environ.get('SATPASS_PY', '/usr/local/bin/bricohams-satpass')
    loader = importlib.machinery.SourceFileLoader('bh_satpass', ruta)
    spec = importlib.util.spec_from_loader('bh_satpass', loader)
    m = importlib.util.module_from_spec(spec)
    loader.exec_module(m)
    return m


def si(v):
    return str(v).strip().lower() in ('1', 'yes', 'si', 'sí', 'true', 'on')


def cfg_desde_env(env=os.environ):
    sat = os.path.join(HTDOCS, 'plugins/receiver/satelites')
    return {
        'pases': env.get('SATREC_PASES', os.path.join(sat, 'pases.json')),
        'lista': env.get('SAT_LIST', '/opt/bricohams/kit/data/satelites.json'),
        'salida': env.get('SATREC_OUT', os.path.join(sat, 'grabaciones.json')),
        'ics': env.get('SATREC_ICS', os.path.join(sat, 'pases.ics')),
        'dir': env.get('SATREC_DIR', '/var/lib/bricohams/satelites'),
        'files': env.get('SATREC_FILES_DIR', '/tmp'),
        'en_files': int(env.get('SATREC_EN_FILES', '2')),
        'min_el': float(env.get('SATREC_MIN_EL', '20')),
        'excluir': {x.strip().upper() for x in re.split(r'[,;]+', env.get('SATREC_EXCLUIR', '')) if x.strip()},
        'omitir_pases': set(env.get('SATREC_OMITIR_PASES', '').split(',')),
        'meteor': si(env.get('SATREC_METEOR', 'yes')),
        'dias': float(env.get('SATREC_DIAS', '30')),
        'max_mb': float(env.get('SATREC_MAX_MB', '2000')),
        'owrx': env.get('SATREC_OWRX', 'ws://127.0.0.1:8073/ws/'),
        'clave_fichero': env.get('SATREC_CLAVE_FICHERO', '/etc/bricohams/satrec.clave'),
        'margen': int(env.get('SATREC_MARGEN_S', '20')),
        'lat': float(env.get('STATION_LAT') or 0), 'lon': float(env.get('STATION_LON') or 0),
        'asl': float(env.get('STATION_ASL') or 0),
        'indicativo': (env.get('CALLSIGN') or '').upper(),
        'amsat': (env.get('AMSAT_REPORT') or 'no').lower(),
        'activo': si(env.get('SATREC_ENABLE', 'yes')),
    }


def locator(lat, lon):
    lon, lat = lon + 180, lat + 90
    s = chr(65 + int(lon // 20)) + chr(65 + int(lat // 10))
    s += str(int(lon % 20 // 2)) + str(int(lat % 10))
    s += chr(97 + int(lon % 2 * 12)) + chr(97 + int(lat % 1 * 24))
    return s


def prefijo(nombre):
    """«IO-117 GreenCube» → «IO117GREENCUBE» (Files de OpenWebRX+ no admite guiones en el prefijo)."""
    return re.sub(r'[^A-Z0-9]', '', nombre.upper())[:16] or 'SAT'


# ---------------------------------------------------------------------
#  Plan de grabaciones
# ---------------------------------------------------------------------
def accion(p, cfg):
    if '%s:%s' % (p['norad'], int(p['aos'])) in cfg.get('omitir_pases', set()):
        return None
    if p['nombre'].upper() in cfg['excluir'] or p.get('max_el', 0) < cfg['min_el']:
        return None
    if p.get('perfil', '').endswith('|meteor'):
        return 'meteor' if cfg['meteor'] else None
    if p.get('modo') in ('nfm', 'usb', 'lsb', 'am', 'cw'):
        return 'grabar'
    return None


def plan(pases, cfg, ahora):
    """Pases futuros a grabar, sin solapes (un solo receptor de satélites)."""
    out, fin = [], 0
    for p in sorted(pases, key=lambda x: x['aos']):
        a = accion(p, cfg)
        if not a or p['los'] <= ahora or p['aos'] - cfg['margen'] < fin:
            continue
        out.append(dict(p, accion=a))
        fin = p['los']
    return out


def ics(planificados, indicativo):
    def t(x):
        return datetime.fromtimestamp(x, timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    ahora = t(time.time())
    lin = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//BricoHams SDR//satrec//ES', 'CALSCALE:GREGORIAN',
           'X-WR-CALNAME:Pases de satélites %s' % (indicativo or 'BricoHams')]
    for p in planificados:
        que = 'imágenes LRPT (SatDump)' if p['accion'] == 'meteor' else 'grabación %s' % p['modo'].upper()
        lin += ['BEGIN:VEVENT', 'UID:%s-%d@bricohams' % (p['norad'], p['aos']), 'DTSTAMP:' + ahora,
                'DTSTART:' + t(p['aos']), 'DTEND:' + t(p['los']),
                'SUMMARY:🛰 %s %.3f MHz · máx %d°' % (p['nombre'], p['hz'] / 1e6, round(p['max_el'])),
                'DESCRIPTION:%s · AOS %s° → LOS %s°' % (que, p.get('az_aos', '?'), p.get('az_los', '?')),
                'BEGIN:VALARM', 'TRIGGER:-PT5M', 'ACTION:DISPLAY', 'DESCRIPTION:Pase de %s' % p['nombre'], 'END:VALARM',
                'END:VEVENT']
    lin.append('END:VCALENDAR')
    return '\r\n'.join(lin) + '\r\n'


# ---------------------------------------------------------------------
#  Doppler
# ---------------------------------------------------------------------
class Doppler:
    def __init__(self, omm, cfg, sp=None):
        self.sp = sp or _satpass()
        self.sat = self.sp.satrec_de_omm(omm)
        self.obs = self.sp.ecef_observador(cfg['lat'], cfg['lon'], cfg['asl'])
        self.cfg = cfg

    def velocidad_radial(self, ts):
        from sgp4.api import jday
        g = time.gmtime(ts)
        jd, fr = jday(g.tm_year, g.tm_mon, g.tm_mday, g.tm_hour, g.tm_min, g.tm_sec + ts % 1)
        e, r, v = self.sat.sgp4(jd, fr)
        if e:
            return 0.0
        th = self.sp.gmst(jd + fr)
        xe, ye, ze = self.obs
        o = (xe * math.cos(th) - ye * math.sin(th), xe * math.sin(th) + ye * math.cos(th), ze)
        vo = (-OMEGA_TIERRA * o[1], OMEGA_TIERRA * o[0], 0.0)
        d = [r[i] - o[i] for i in range(3)]
        n = math.sqrt(sum(x * x for x in d))
        return sum(d[i] * (v[i] - vo[i]) for i in range(3)) / n

    def hz(self, f0, ts):
        return f0 * (1 - self.velocidad_radial(ts) / C_KMS)

    def elevacion(self, ts):
        r, jd = self.sp.posicion(self.sat, ts)
        return self.sp.az_el(r, jd, self.cfg['lat'], self.cfg['lon'], self.obs)[1] if r else -90


# ---------------------------------------------------------------------
#  Audio IMA ADPCM de OpenWebRX+ (igual que htdocs/lib/AudioEngine.js)
# ---------------------------------------------------------------------
IMA_INDICE = [-1, -1, -1, -1, 2, 4, 6, 8, -1, -1, -1, -1, 2, 4, 6, 8]
IMA_PASO = [7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31, 34, 37, 41, 45, 50, 55, 60, 66, 73, 80,
            88, 97, 107, 118, 130, 143, 157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408, 449, 494, 544, 598,
            658, 724, 796, 876, 963, 1060, 1166, 1282, 1411, 1552, 1707, 1878, 2066, 2272, 2499, 2749, 3024, 3327,
            3660, 4026, 4428, 4871, 5358, 5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899, 15289,
            16818, 18500, 20350, 22385, 24623, 27086, 29794, 32767]


class Adpcm:
    def __init__(self):
        self.indice = self.pred = self.paso = 0
        self.fase = self.sinc = self.cuenta = 0
        self.buf = bytearray()

    def nibble(self, n):
        self.indice = min(max(self.indice + IMA_INDICE[n], 0), 88)
        d = self.paso >> 3
        if n & 1:
            d += self.paso >> 2
        if n & 2:
            d += self.paso >> 1
        if n & 4:
            d += self.paso
        if n & 8:
            d = -d
        self.pred = min(max(self.pred + d, -32768), 32767)
        self.paso = IMA_PASO[self.indice]
        return self.pred

    def decodificar(self, datos):
        out = []
        for b in datos:
            if self.fase == 0:
                if b == b'SYNC'[self.sinc]:
                    self.sinc += 1
                else:
                    self.sinc = 0
                if self.sinc == 4:
                    self.buf = bytearray()
                    self.fase = 1
            elif self.fase == 1:
                self.buf.append(b)
                if len(self.buf) == 4:
                    self.indice, self.pred = struct.unpack('<hh', bytes(self.buf))
                    self.cuenta = 1000
                    self.fase = 2
            else:
                out.append(self.nibble(b & 0x0F))
                out.append(self.nibble(b >> 4))
                self.cuenta -= 1
                if self.cuenta < 0:
                    self.sinc = 0
                    self.fase = 0
        return out


# ---------------------------------------------------------------------
#  Cliente websocket mínimo (solo biblioteca estándar)
# ---------------------------------------------------------------------
class WS:
    def __init__(self, url, timeout=15):
        u = urllib.parse.urlparse(url)
        self.s = socket.create_connection((u.hostname, u.port or 80), timeout=timeout)
        clave = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall(('GET %s HTTP/1.1\r\nHost: %s:%d\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n'
                        'Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\nUser-Agent: BricoHams-satrec\r\n\r\n'
                        % (u.path or '/', u.hostname, u.port or 80, clave)).encode())
        cab = b''
        while b'\r\n\r\n' not in cab:
            d = self.s.recv(1024)
            if not d:
                raise ConnectionError('OpenWebRX+ cerró la conexión en el saludo')
            cab += d
        cab, self.resto = cab.split(b'\r\n\r\n', 1)
        if b' 101 ' not in cab.split(b'\r\n')[0]:
            raise ConnectionError('websocket rechazado: %s' % cab.split(b'\r\n')[0].decode('latin-1'))

    def _trama(self):
        """Saca una trama entera del búfer; si falta algo lee más (un timeout no pierde bytes)."""
        while True:
            r = self.resto
            if len(r) >= 2:
                n, i = r[1] & 0x7F, 2
                if n == 126:
                    n, i = (struct.unpack('>H', r[2:4])[0], 4) if len(r) >= 4 else (None, 0)
                elif n == 127:
                    n, i = (struct.unpack('>Q', r[2:10])[0], 10) if len(r) >= 10 else (None, 0)
                m = 4 if r[1] & 0x80 else 0
                if n is not None and len(r) >= i + m + n:
                    mask, d = r[i:i + m], r[i + m:i + m + n]
                    self.resto = r[i + m + n:]
                    if m:
                        d = bytes(x ^ mask[k % 4] for k, x in enumerate(d))
                    return r[0], d
            d = self.s.recv(65536)
            if not d:
                raise ConnectionError('OpenWebRX+ cerró la conexión')
            self.resto += d

    def enviar(self, datos, op=1):
        if isinstance(datos, str):
            datos = datos.encode()
        m = os.urandom(4)
        n = len(datos)
        cab = bytes([0x80 | op])
        if n < 126:
            cab += bytes([0x80 | n])
        elif n < 65536:
            cab += bytes([0x80 | 126]) + struct.pack('>H', n)
        else:
            cab += bytes([0x80 | 127]) + struct.pack('>Q', n)
        self.s.sendall(cab + m + bytes(b ^ m[i % 4] for i, b in enumerate(datos)))

    def json(self, obj):
        self.enviar(json.dumps(obj))

    def recibir(self):
        """(opcode, datos) de un mensaje completo; contesta los ping."""
        partes, op0 = b'', None
        while True:
            b0, d = self._trama()
            op, fin = b0 & 0x0F, b0 & 0x80
            if op == 9:
                self.enviar(d, 10)
                continue
            if op == 8:
                raise ConnectionError('OpenWebRX+ cerró el websocket')
            if op == 10:
                return op, d
            if op in (1, 2):
                op0, partes = op, d
            elif op == 0:
                partes += d
            else:
                continue
            if fin:
                return op0, partes

    def cerrar(self):
        try:
            self.enviar(b'', 8)
        except OSError:
            pass
        self.s.close()


def clave_magica(cfg):
    try:
        return open(cfg['clave_fichero'], encoding='utf-8').read().strip() or None
    except OSError:
        return None


ESPERA_PERFILES = 5


def conectar(cfg, perfil, timeout=20):
    """Conecta, elige el perfil y espera la configuración del receptor. Devuelve (ws, config)."""
    ws = WS(cfg['owrx'])
    sdr, prof = perfil.split('|', 1)
    conf, pedido = {}, False
    limite = time.monotonic() + timeout
    confirmado = False
    espera = None       # plazo para la lista de perfiles; servidores sin ella reciben la petición igualmente

    def pedir():
        m = {'profile': perfil}
        k = clave_magica(cfg)
        if k:
            m['key'] = k
        ws.json({'type': 'selectprofile', 'params': m})
        # OpenWebRX+ procesa el ping después de todos los cambios síncronos del perfil.
        ws.enviar(b'', 9)
    try:
        ws.s.settimeout(timeout)
        ws.enviar('SERVER DE CLIENT client=bricohams-satrec type=receiver')
        while time.monotonic() < limite:
            hasta = limite if pedido or espera is None else min(limite, espera)
            ws.s.settimeout(max(0.001, hasta - time.monotonic()))
            try:
                op, d = ws.recibir()
            except socket.timeout:
                if not pedido and espera is not None and time.monotonic() >= espera:
                    pedir()
                    pedido = True
                    continue
                break
            if op == 10 and pedido:
                confirmado = True
            elif op == 1:
                txt = d.decode('utf-8', 'replace')
                if txt.startswith('CLIENT DE SERVER'):
                    ws.json({'type': 'connectionproperties', 'params': {'output_rate': TASA, 'hd_output_rate': 48000}})
                    espera = time.monotonic() + ESPERA_PERFILES
                    continue
                try:
                    j = json.loads(txt)
                except ValueError:
                    continue
                if j.get('type') == 'profiles' and not pedido:
                    # Pedir un receptor ausente (SDR caído, sobrecorriente USB) rompe OpenWebRX+ 1.2.x
                    # (KeyError en isLocked) y deja un websocket colgado: se comprueba antes.
                    ofrecidos = {x.get('id') for x in j.get('value') or [] if isinstance(x, dict)}
                    if perfil not in ofrecidos:
                        raise ConnectionError('receptor %s no disponible en OpenWebRX+ (¿SDR desconectado o sobrecorriente USB?)'
                                              % perfil)
                    pedir()
                    pedido = True
                elif j.get('type') == 'config':
                    conf.update(j.get('value') or {})
                elif j.get('type') == 'log_message' and 'locked' in str(j.get('value', '')).lower():
                    raise PermissionError('perfil %s bloqueado: pon la clave en %s' % (perfil, cfg['clave_fichero']))
            if (confirmado and conf.get('sdr_id') == sdr and conf.get('profile_id') == prof
                    and conf.get('center_freq') is not None and conf.get('samp_rate') is not None):
                return ws, conf
        raise TimeoutError('OpenWebRX+ no ha confirmado la configuración del perfil %s' % perfil)
    except (OSError, ValueError):
        ws.cerrar()
        raise


FILTROS = {'nfm': (-7500, 7500), 'am': (-5000, 5000), 'usb': (300, 3000), 'lsb': (-3000, -300), 'cw': (-400, 400)}


def grabar_audio(cfg, p, doppler, wav, hasta, reloj=time.time):
    """Graba de OpenWebRX+ hasta «hasta» (epoch). Devuelve dict con muestras y offsets."""
    ws, conf = conectar(cfg, p['perfil'])
    try:
        centro, ancho = int(conf['center_freq']), int(conf.get('samp_rate', 0))
        comp = conf.get('audio_compression', 'adpcm')
        lo, hi = FILTROS.get(p['modo'], (-6000, 6000))

        def offset(ts):
            return int(round((doppler.hz(p['hz'], ts) if doppler else p['hz']) - centro))
        off = offset(reloj())
        if ancho and abs(off) > ancho / 2 - 20000:
            raise ValueError('%.3f MHz fuera del perfil %s (%.3f MHz ± %d kHz)' % (p['hz'] / 1e6, p['perfil'], centro / 1e6, ancho // 2000))
        ws.json({'type': 'dspcontrol', 'action': 'start'})
        ws.json({'type': 'dspcontrol', 'params': {'mod': p['modo'], 'low_cut': lo, 'high_cut': hi,
                                                  'offset_freq': off, 'squelch_level': -150}})
        dec = Adpcm() if comp == 'adpcm' else None
        n, ultimo, offs = 0, reloj(), [off]
        ws.s.settimeout(5)
        with wave.open(wav, 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(TASA)
            while reloj() < hasta:
                try:
                    op, d = ws.recibir()
                except socket.timeout:
                    continue
                if op == 2 and d[:1] == b'\x02':
                    m = dec.decodificar(d[1:]) if dec else list(struct.unpack('<%dh' % ((len(d) - 1) // 2), d[1:1 + (len(d) - 1) // 2 * 2]))
                    w.writeframes(struct.pack('<%dh' % len(m), *m))
                    n += len(m)
                if doppler and reloj() - ultimo >= 2:
                    ultimo = reloj()
                    nuevo = offset(ultimo)
                    if abs(nuevo - off) >= 50:
                        off = nuevo
                        ws.json({'type': 'dspcontrol', 'params': {'offset_freq': off}})
                        offs.append(off)
        return {'muestras': n, 'centro': centro, 'offsets': [min(offs), max(offs)]}
    finally:
        ws.cerrar()


def oido_fm(wav, ref_s=10, umbral=0.35):
    """Silenciamiento FM: con portadora el ruido de alta frecuencia cae. Compara cada segundo con
    los primeros «ref_s» segundos (antes del AOS, solo ruido). Devuelve (oido, segundos_oidos)."""
    with wave.open(wav, 'rb') as w:
        datos = w.readframes(w.getnframes())
        tasa = w.getframerate()
    x = struct.unpack('<%dh' % (len(datos) // 2), datos)
    hf = []
    for i in range(0, len(x) - tasa + 1, tasa):
        s = x[i:i + tasa]
        hf.append(math.sqrt(sum((s[j] - s[j - 1]) ** 2 for j in range(1, len(s), 2)) / (len(s) // 2)))
    if len(hf) < ref_s + 5:
        return None, 0
    ref = sorted(hf[:ref_s])[ref_s // 2]
    if ref < 50:              # sin ruido de referencia (¿silenciador o receptor parado?): no se puede decidir
        return None, 0
    n = sum(1 for v in hf[ref_s:] if v < umbral * ref)
    return n >= max(8, 0.05 * (len(hf) - ref_s)), n


# ---------------------------------------------------------------------
#  Archivo, «Files» de OpenWebRX+ y AMSAT
# ---------------------------------------------------------------------
def nombre_fichero(p, t):
    return '%s-%s-%d.mp3' % (prefijo(p['nombre']), time.strftime('%y%m%d-%H%M%S', time.gmtime(t)), round(p['hz'] / 1000))


def a_mp3(wav, mp3):
    if not shutil.which('lame'):
        return False
    r = subprocess.run(['lame', '--quiet', '-m', 'm', '-b', '32', '--resample', '16', wav, mp3 + '.tmp'], timeout=600)
    if r.returncode == 0:
        os.replace(mp3 + '.tmp', mp3)
        return True
    return False


def enlazar_files(cfg, capturas):
    """Enlaces en «Files» de las últimas capturas; borra los enlaces viejos o rotos que son nuestros."""
    arch = os.path.realpath(os.path.join(cfg['dir'], 'grabaciones'))
    orden = [c['fichero'] for c in sorted(capturas, key=lambda c: c['aos']) if c.get('fichero')]
    quiero = set(orden[-cfg['en_files']:]) if cfg['en_files'] > 0 else set()
    try:
        nombres = os.listdir(cfg['files'])
    except OSError:
        return
    for f in nombres:
        ruta = os.path.join(cfg['files'], f)
        if os.path.islink(ruta) and os.path.realpath(ruta).startswith(arch + os.sep) and (f not in quiero or not os.path.exists(ruta)):
            os.unlink(ruta)
    for f in quiero:
        ruta, dest = os.path.join(cfg['files'], f), os.path.join(arch, f)
        if os.path.exists(dest) and not os.path.lexists(ruta):
            os.symlink(dest, ruta)


def limpiar_archivo(cfg, capturas, ahora):
    arch = os.path.join(cfg['dir'], 'grabaciones')
    fich = sorted((os.path.join(arch, f) for f in os.listdir(arch) if f.endswith(('.mp3', '.wav'))), key=os.path.getmtime) if os.path.isdir(arch) else []
    total = sum(os.path.getsize(f) for f in fich)
    for f in fich:
        if os.path.getmtime(f) < ahora - cfg['dias'] * 86400 or total > cfg['max_mb'] * 1e6:
            total -= os.path.getsize(f)
            os.unlink(f)
    vivos = {os.path.basename(f) for f in fich if os.path.exists(f)}
    return [c for c in capturas if c['aos'] >= ahora - cfg['dias'] * 86400
            and (not c.get('fichero') or c['fichero'] in vivos)]


def informe_amsat(c, cfg):
    """Campos del formulario de https://www.amsat.org/status/ (o None si no aplica)."""
    if not c.get('amsat') or not str(c.get('estado', '')).startswith('grabado') \
            or not cfg['indicativo'] or cfg['indicativo'] == 'N0CALL':
        return None
    t = time.gmtime(c.get('t_max') or c['aos'])
    return {'SatName': c['amsat'], 'SatReport': {True: 'Heard', False: 'Not Heard'}.get(c.get('oido'), ''),
            'SatYear': '%04d' % t.tm_year, 'SatMonth': '%02d' % t.tm_mon, 'SatDay': '%02d' % t.tm_mday,
            'SatHour': '%02d' % t.tm_hour, 'SatPeriod': str(min(3, max(0, (t.tm_min - 1) // 15))),
            'SatCall': cfg['indicativo'], 'SatGridSquare': locator(cfg['lat'], cfg['lon'])[:6]}


def enviar_amsat(campos, url=AMSAT_URL):
    datos = urllib.parse.urlencode(dict(campos, SatSubmit='Submit Data')).encode()
    req = urllib.request.Request(url, data=datos, headers={'User-Agent': 'BricoHams-SDR satrec 1.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return 200 <= r.status < 300


def write_atomic(path, texto):
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix='.satrec-')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(texto)
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


# ---------------------------------------------------------------------
#  Servicio
# ---------------------------------------------------------------------
class Grabador:
    def __init__(self, cfg, grabar=grabar_audio, reloj=time.time, dormir=time.sleep, sp=None):
        self.cfg, self.grabar_fn, self.reloj, self.dormir, self.sp = cfg, grabar, reloj, dormir, sp
        os.makedirs(os.path.join(cfg['dir'], 'grabaciones'), exist_ok=True)
        self.estado_f = os.path.join(cfg['dir'], 'capturas.json')
        try:
            self.capturas = json.load(open(self.estado_f, encoding='utf-8'))
        except (OSError, ValueError):
            self.capturas = []
        self.amsat = {}
        try:
            for s in json.load(open(cfg['lista'], encoding='utf-8'))['satelites']:
                if s.get('amsat'):
                    self.amsat[s['norad']] = s['amsat']
        except (OSError, ValueError, KeyError):
            pass
        self.planificados = []

    def pases(self):
        try:
            return json.load(open(self.cfg['pases'], encoding='utf-8')).get('pases', [])
        except (OSError, ValueError):
            return []

    def hecho(self, p):
        return any(c['norad'] == p['norad'] and c['aos'] == p['aos'] for c in self.capturas)

    def publicar(self):
        ahora = self.reloj()
        self.capturas = limpiar_archivo(self.cfg, self.capturas, ahora)
        json.dump(self.capturas, open(self.estado_f + '.tmp', 'w', encoding='utf-8'), ensure_ascii=False)
        os.replace(self.estado_f + '.tmp', self.estado_f)
        enlazar_files(self.cfg, self.capturas)
        quitar = ('omm', 'perfil', 'nota')
        pub = {'actualizado': datetime.now(timezone.utc).isoformat(timespec='seconds'),
               'activo': self.cfg['activo'], 'min_el': self.cfg['min_el'], 'amsat_modo': self.cfg['amsat'],
               'plan': [{k: v for k, v in p.items() if k not in quitar} for p in self.planificados[:30]],
               'capturas': [dict(c, amsat_form=informe_amsat(c, self.cfg),
                                 en_files=bool(c.get('fichero')) and os.path.exists(os.path.join(self.cfg['files'], c['fichero'])))
                            for c in reversed(self.capturas[-60:])]}
        write_atomic(self.cfg['salida'], json.dumps(pub, ensure_ascii=False))
        write_atomic(self.cfg['ics'], ics(self.planificados, self.cfg['indicativo']))

    def ejecutar(self, p):
        cfg, ahora = self.cfg, self.reloj()
        c = {'nombre': p['nombre'], 'norad': p['norad'], 'aos': p['aos'], 'los': p['los'], 't_max': p.get('t_max'),
             'max_el': p['max_el'], 'hz': p['hz'], 'modo': p['modo'], 'accion': p['accion'],
             'amsat': self.amsat.get(p['norad'], '')}
        try:
            if p['accion'] == 'meteor':
                ws, _ = conectar(cfg, p['perfil'])
                ws.cerrar()
                c['estado'] = 'perfil meteor puesto: las imágenes salen en Files si SatDump decodifica'
            else:
                fich = nombre_fichero(p, p['aos'])
                arch = os.path.join(cfg['dir'], 'grabaciones')
                wav = os.path.join(arch, fich[:-4] + '.wav')
                dop = Doppler(p['omm'], cfg, self.sp) if p.get('omm') else None
                r = self.grabar_fn(cfg, p, dop, wav, p['los'], self.reloj)
                c.update(segundos=round(r['muestras'] / TASA), offsets=r['offsets'])
                if p['modo'] == 'nfm':
                    c['oido'], c['segundos_oidos'] = oido_fm(wav)
                if a_mp3(wav, os.path.join(arch, fich)):
                    os.unlink(wav)
                    c['fichero'] = fich
                    c['estado'] = 'grabado'
                else:
                    c['fichero_wav'] = os.path.basename(wav)
                    c['estado'] = 'grabado en WAV (falta lame para el MP3 de Files)'
        except Exception as e:
            c['estado'] = 'error: %s' % e
            print('satrec: %s %s' % (p['nombre'], e), file=sys.stderr, flush=True)
        if cfg['amsat'] == 'auto' and c.get('oido'):
            f = informe_amsat(c, cfg)
            try:
                c['amsat_enviado'] = bool(f) and enviar_amsat(f)
            except Exception as e:
                print('satrec: AMSAT: %s' % e, file=sys.stderr, flush=True)
                c['amsat_enviado'] = False
        c['duracion_real'] = round(self.reloj() - ahora)
        self.capturas.append(c)
        print('satrec: %s → %s' % (p['nombre'], c['estado']), flush=True)
        return c

    def vuelta(self):
        ahora = self.reloj()
        self.planificados = plan(self.pases(), self.cfg, ahora) if self.cfg['activo'] else []
        self.planificados = [p for p in self.planificados if not self.hecho(p)]
        prox = self.planificados[0] if self.planificados else None
        if prox:
            falta = prox['aos'] - self.cfg['margen'] - ahora
            if 0 < falta <= 20:                 # el ruido de antes del AOS es la referencia de «oído»
                self.dormir(falta)
                falta = 0
            if falta <= 0:
                self.ejecutar(prox)
                self.planificados.pop(0)
        self.publicar()
        return prox


def main(argv):
    cfg = cfg_desde_env()
    if '--plan' in argv:
        for p in plan(Grabador(cfg).pases(), cfg, time.time()):
            print('%s  %-18s máx %4.1f°  %3d min  %s' % (datetime.fromtimestamp(p['aos']).strftime('%d/%m %H:%M'),
                                                       p['nombre'], p['max_el'], p['duracion_s'] // 60, p['accion']))
        return 0
    if '--probar' in argv:
        seg = int(argv[argv.index('--probar') + 1]) if len(argv) > argv.index('--probar') + 1 else 15
        perfil = os.environ.get('SATREC_PRUEBA_PERFIL', 'sat|sat2m')
        p = {'nombre': 'PRUEBA', 'hz': int(os.environ.get('SATREC_PRUEBA_HZ', '145800000')), 'modo': 'nfm', 'perfil': perfil}
        wav = os.path.join(tempfile.gettempdir(), 'satrec-prueba.wav')
        r = grabar_audio(cfg, p, None, wav, time.time() + seg)
        print('satrec: prueba %d muestras (%.1f s) en %s · centro %.3f MHz · ruido FM %s'
              % (r['muestras'], r['muestras'] / TASA, wav, r['centro'] / 1e6, oido_fm(wav, ref_s=3)))
        return 0 if r['muestras'] > TASA * seg * 0.8 else 1
    g = Grabador(cfg)
    print('satrec: grabo pases con elevación ≥ %g° (%s)' % (cfg['min_el'], 'activo' if cfg['activo'] else 'SATREC_ENABLE=no'), flush=True)
    while True:
        try:
            g.vuelta()
        except Exception as e:
            print('satrec: %s' % e, file=sys.stderr, flush=True)
        time.sleep(15)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
