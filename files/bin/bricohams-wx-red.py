#!/usr/bin/env python3
# =====================================================================
#  bricohams-wx-red · BricoHams  (v5.0)
#  Escucha APRS-IS (solo lectura, sin contraseña) y guarda para la web
#  «Clima en red» (/bricohams/clima.html) y la ventana del tiempo:
#   - las estaciones meteorológicas APRS cercanas (WXRED_RADIO_KM), con
#     temperatura, presión, humedad, viento y lluvia, y por dónde llegaron:
#     «rf» (las oyeron nuestros iGates), «satelite» (ISS/ARISS…) o «internet»;
#   - lo que se ha oído a través de los digipetidores de los satélites.
#  Salida: plugins/receiver/meteo/wx-red.json (atómico, cada 60 s).
#  Uso: bricohams-wx-red             (servicio systemd bricohams-wx-red)
#       bricohams-wx-red --linea 'EA1AAA>APRS,qAR,EA1BBB-10:_10090556c220s004g005t077'
# =====================================================================
import json
import math
import os
import re
import select
import socket
import sys
import tempfile
import time
from datetime import datetime, timezone

VERSION = '1.0'
SAT_DIGIS = re.compile(r'^(RS0ISS|ARISS|NA1SS|PSAT\d*|W3ADO-1|BJ1SI|LU1ESY)(-\d+)?\*?$', re.I)
SAT_FILTRO = 'd/RS0ISS*/ARISS*/NA1SS*/PSAT*'


def cfg_desde_env(env=os.environ):
    def lista(v):
        return {x.strip().upper() for x in re.split(r'[\s,]+', v or '') if x.strip()}
    lat = float(env.get('STATION_LAT') or 0)
    lon = float(env.get('STATION_LON') or 0)
    propias = lista(env.get('WXRED_IGATES', '')) | lista(env.get('IGATE_CALLSIGN', '')) | lista(env.get('RAK_CALLSIGN', ''))
    return {
        'servidor': env.get('WXRED_SERVIDOR', 'rotate.aprs2.net'),
        'puerto': int(env.get('WXRED_PUERTO', '14580')),
        'indicativo': (env.get('WXRED_CALLSIGN') or env.get('CALLSIGN') or 'N0CALL').upper(),
        'lat': lat, 'lon': lon,
        'radio_km': max(5, min(500, int(env.get('WXRED_RADIO_KM', '100')))),
        'horas': float(env.get('WXRED_HORAS', '3')),
        'satelites': env.get('WXRED_SATELITES', 'yes').lower() in ('1', 'yes', 'si', 'sí', 'true'),
        'igates': propias,
        'propia': (env.get('WX_APRS_CALLSIGN') or '').upper(),
        'salida': env.get('WXRED_OUT', '/usr/lib/python3/dist-packages/htdocs/plugins/receiver/meteo/wx-red.json'),
    }


def filtro(cfg):
    f = 'r/%.2f/%.2f/%d' % (cfg['lat'], cfg['lon'], cfg['radio_km'])
    return f + (' ' + SAT_FILTRO if cfg['satelites'] else '')


def distancia_km(la1, lo1, la2, lo2):
    p1, p2 = math.radians(la1), math.radians(la2)
    dp, dl = p2 - p1, math.radians(lo2 - lo1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371.0 * 2 * math.asin(min(1, math.sqrt(a)))


def rumbo(la1, lo1, la2, lo2):
    p1, p2, dl = math.radians(la1), math.radians(la2), math.radians(lo2 - lo1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return round((math.degrees(math.atan2(y, x)) + 360) % 360)


def _latlon_texto(s):
    """'4025.00N' + '00342.00W' → grados (admite ambigüedad con espacios)."""
    la, lo = s[:8].replace(' ', '0'), s[9:18].replace(' ', '0')
    if not re.match(r'^\d{4}\.\d{2}[NS]$', la) or not re.match(r'^\d{5}\.\d{2}[EW]$', lo):
        return None
    lat = int(la[:2]) + float(la[2:7]) / 60
    lon = int(lo[:3]) + float(lo[3:8]) / 60
    if la[7] == 'S':
        lat = -lat
    if lo[8] == 'W':
        lon = -lon
    if abs(lat) > 90 or abs(lon) > 180:
        return None
    return lat, lon


def _b91(s):
    n = 0
    for c in s:
        n = n * 91 + ord(c) - 33
    return n


def posicion(cuerpo):
    """Devuelve (lat, lon, símbolo, resto) de una posición APRS sin cabecera de tipo."""
    if len(cuerpo) >= 19 and cuerpo[0].isdigit():
        ll = _latlon_texto(cuerpo[:18])
        if ll:
            return ll[0], ll[1], cuerpo[8] + cuerpo[18], cuerpo[19:]
        return None
    if len(cuerpo) >= 13 and cuerpo[0] in '/\\ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij':
        c = cuerpo[1:13]
        if all(33 <= ord(x) <= 124 for x in c[:8]):
            lat = 90 - _b91(c[0:4]) / 380926.0
            lon = -180 + _b91(c[4:8]) / 190463.0
            resto = cuerpo[13:]
            sym = cuerpo[0] + c[8]
            cs, tipo = c[9:11], c[11:12]
            if cs[:1] not in ('', ' ', '{') and len(cs) == 2 and tipo and (ord(tipo) - 33) & 0x18 != 0x10 \
                    and 0 <= ord(cs[0]) - 33 <= 89:
                # en las WX comprimidas el rumbo/velocidad del viento va en «cs»
                resto = '%03d/%03d' % ((ord(cs[0]) - 33) * 4, round((1.08 ** (ord(cs[1]) - 33) - 1) * 1.15078)) + resto
            return lat, lon, sym, resto
    return None


CAMPOS = {'c': 3, 's': 3, 'g': 3, 't': 3, 'r': 3, 'p': 3, 'P': 3, 'h': 2, 'b': 5, 'L': 3, 'l': 3}


def datos_wx(texto):
    """Campos WX (formato APRS 1.01) → dict en unidades métricas. Devuelve (wx, comentario)."""
    raw = {}
    i = 0
    m = re.match(r'^(\d{3}|\.{3}| {3})/(\d{3}|\.{3}| {3})', texto)
    if m:
        raw['c'], raw['s'] = m.group(1), m.group(2)
        i = 7
    while i < len(texto) and texto[i] in CAMPOS:
        k = texto[i]
        n = CAMPOS[k]
        v = texto[i + 1:i + 1 + n]
        if len(v) < n or not re.match(r'^(-?\d+|\.+| +)$', v):
            break
        raw.setdefault(k, v)
        i += 1 + n
    wx = {}

    def num(k):
        v = raw.get(k, '')
        return int(v) if re.match(r'^-?\d+$', v) else None
    t = num('t')
    if t is not None and -80 <= t <= 160:
        wx['temp_c'] = round((t - 32) * 5 / 9, 1)
    if num('h') is not None:
        wx['hum'] = 100 if num('h') == 0 else num('h')
    if num('b') is not None and 8000 <= num('b') <= 11000:
        wx['pres_hpa'] = round(num('b') / 10, 1)
    if num('s') is not None:
        wx['viento_kmh'] = round(num('s') * 1.609344, 1)
    if num('g') is not None:
        wx['racha_kmh'] = round(num('g') * 1.609344, 1)
    if num('c') is not None and 0 <= num('c') <= 360:
        wx['dir'] = num('c') % 360
    for k, nombre in (('r', 'lluvia_1h_mm'), ('p', 'lluvia_24h_mm'), ('P', 'lluvia_hoy_mm')):
        if num(k) is not None:
            wx[nombre] = round(num(k) * 0.254, 1)
    if num('L') is not None:
        wx['lum_wm2'] = num('L')
    elif num('l') is not None:
        wx['lum_wm2'] = num('l') + 1000
    return wx, texto[i:].strip()


def analizar(linea):
    """Línea TNC2 de APRS-IS → dict o None (comentarios del servidor, basura)."""
    if not linea or linea.startswith('#') or '>' not in linea or ':' not in linea:
        return None
    cab, carga = linea.split(':', 1)
    src, resto = cab.split('>', 1)
    camino = resto.split(',')[1:]
    pkt = {'call': src.strip().upper()[:9], 'camino': camino, 'carga': carga}
    if not carga:
        return pkt
    tipo = carga[0]
    cuerpo = None
    if tipo in '!=':
        cuerpo = carga[1:]
    elif tipo in '/@':
        cuerpo = carga[8:]
    elif tipo == ';' and len(carga) > 18 and carga[10] == '*':
        pkt['call'] = carga[1:10].strip()[:9]
        pkt['objeto'] = True
        cuerpo = carga[18:]
    elif tipo == '_' and len(carga) >= 9:
        wx, com = datos_wx(carga[9:])
        if wx:
            pkt['wx'] = wx
        return pkt
    if cuerpo:
        p = posicion(cuerpo)
        if p:
            pkt['lat'], pkt['lon'] = round(p[0], 4), round(p[1], 4)
            if p[2][1:] == '_':
                wx, com = datos_wx(p[3])
                if wx:
                    pkt['wx'] = wx
                pkt['comentario'] = com[:60]
    return pkt


def via(pkt, cfg):
    """('rf'|'satelite'|'internet', igate)."""
    camino = pkt['camino']
    igate, q = '', None
    for j, e in enumerate(camino):
        if e.startswith('qA'):
            q = e
            igate = camino[j + 1].upper() if j + 1 < len(camino) else ''
            camino = camino[:j]
            break
    # ARISS sin «*» es solo el alias pedido: cuenta si el satélite lo ha repetido
    if any(SAT_DIGIS.match(e) and (e.endswith('*') or not e.upper().startswith('ARISS')) for e in camino):
        return 'satelite', igate
    if igate and igate in cfg['igates'] and q in ('qAR', 'qAo', 'qAO'):
        return 'rf', igate
    return 'internet', igate


class Red:
    def __init__(self, cfg):
        self.cfg = cfg
        self.est = {}
        self.pos = {}
        self.sat = []

    def meter(self, linea, ahora=None):
        ahora = ahora or time.time()
        pkt = analizar(linea)
        if not pkt:
            return None
        v, igate = via(pkt, self.cfg)
        if 'lat' in pkt:
            self.pos[pkt['call']] = (pkt['lat'], pkt['lon'], ahora)
        if v == 'satelite':
            self.sat.insert(0, {'call': pkt['call'], 't': int(ahora), 'igate': igate,
                                'digi': next((e.rstrip('*') for e in pkt['camino'] if SAT_DIGIS.match(e)), ''),
                                'texto': re.sub(r'[\x00-\x1f]', '', pkt['carga'])[:80],
                                **({'lat': pkt['lat'], 'lon': pkt['lon']} if 'lat' in pkt else {})})
            del self.sat[50:]
        if 'wx' not in pkt:
            return pkt
        p = self.pos.get(pkt['call'])
        if not p:
            return pkt
        cfg = self.cfg
        dist = distancia_km(cfg['lat'], cfg['lon'], p[0], p[1])
        if dist > cfg['radio_km'] and v != 'satelite':
            return pkt
        prev = self.est.get(pkt['call'], {})
        wx = dict(prev.get('wx', {}))
        wx.update(pkt['wx'])
        self.est[pkt['call']] = {
            'call': pkt['call'], 'lat': round(p[0], 3), 'lon': round(p[1], 3),
            'dist_km': round(dist, 1), 'rumbo': rumbo(cfg['lat'], cfg['lon'], p[0], p[1]),
            't': int(ahora), 'via': 'rf' if v == 'internet' and prev.get('via') == 'rf' else v,
            'igate': igate, 'wx': wx, 'propia': pkt['call'] == cfg['propia'],
            'comentario': pkt.get('comentario', prev.get('comentario', '')),
        }
        return pkt

    def caducar(self, ahora=None):
        ahora = ahora or time.time()
        lim = ahora - self.cfg['horas'] * 3600
        for k in [k for k, e in self.est.items() if e['t'] < lim]:
            del self.est[k]
        for k in [k for k, e in self.pos.items() if e[2] < ahora - 86400]:
            del self.pos[k]
        self.sat = [s for s in self.sat if s['t'] >= ahora - 86400]

    def json(self, conectado=True):
        est = sorted(self.est.values(), key=lambda e: (not e['propia'], e['dist_km']))
        return {'actualizado': datetime.now(timezone.utc).isoformat(timespec='seconds'),
                'conectado': conectado, 'servidor': self.cfg['servidor'],
                'qth': {'lat': round(self.cfg['lat'], 2), 'lon': round(self.cfg['lon'], 2)},
                'radio_km': self.cfg['radio_km'], 'horas': self.cfg['horas'],
                'estaciones': est[:80], 'satelite': self.sat[:50]}


def write_atomic(path, obj):
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix='.wxred-')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False)
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


def sesion(red, cfg, parar, cada=60.0, espera=120.0):
    """Una conexión a APRS-IS hasta que se cae o parar() devuelve True."""
    s = socket.create_connection((cfg['servidor'], cfg['puerto']), timeout=30)
    try:
        s.sendall(('user %s pass -1 vers BricoHams-WX %s filter %s\r\n' % (cfg['indicativo'], VERSION, filtro(cfg))).encode())
        buf = b''
        ultimo = time.time()
        escrito = 0.0
        while not parar():
            r, _, _ = select.select([s], [], [], 1.0)
            ahora = time.time()
            if r:
                d = s.recv(8192)
                if not d:
                    raise ConnectionError('APRS-IS cerró la conexión')
                ultimo = ahora
                buf += d
                *lineas, buf = buf.split(b'\n')
                for ln in lineas:
                    red.meter(ln.decode('utf-8', 'replace').rstrip('\r'), ahora)
            elif ahora - ultimo > espera:
                raise ConnectionError('APRS-IS mudo %d s' % espera)
            if ahora - escrito >= cada:
                red.caducar(ahora)
                write_atomic(cfg['salida'], red.json(True))
                escrito = ahora
    finally:
        s.close()


def servicio(cfg, parar=lambda: False, cada=60.0):
    red = Red(cfg)
    pausa = 5
    print('wx-red: %s:%d filtro «%s»' % (cfg['servidor'], cfg['puerto'], filtro(cfg)), flush=True)
    while not parar():
        try:
            sesion(red, cfg, parar, cada)
            pausa = 5
        except (OSError, ConnectionError) as e:
            print('wx-red: %s; reintento en %d s' % (e, pausa), file=sys.stderr, flush=True)
            red.caducar()
            try:
                write_atomic(cfg['salida'], red.json(False))
            except OSError:
                pass
            t = time.time() + pausa
            while time.time() < t and not parar():
                time.sleep(0.5)
            pausa = min(300, pausa * 2)
    return red


def main(argv):
    cfg = cfg_desde_env()
    if '--linea' in argv:
        print(json.dumps(analizar(argv[argv.index('--linea') + 1]), ensure_ascii=False, indent=1))
        return 0
    if '--filtro' in argv:
        print(filtro(cfg))
        return 0
    if not (cfg['lat'] or cfg['lon']):
        print('wx-red: faltan STATION_LAT/STATION_LON', file=sys.stderr)
        return 1
    servicio(cfg)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
