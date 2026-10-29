#!/usr/bin/env python3
# =====================================================================
#  bricohams-api · BricoHams  (v4)
#  Pequeño servicio HTTP (127.0.0.1:8075, detrás de nginx en /bricohams/api/)
#  para los plugins de la web:
#    GET /bricohams/api/indicativo?call=N0CALL
#        -> {"call","nombre","ciudad","region","pais","foto","fuente"}
#        Fuentes: HamQTH (principal), RadioID.net y, si hay credenciales de
#        QRZ XML, QRZ como fuente complementaria. Caché de 7 días.
#    GET /bricohams/api/avion?hex=4ca123&cs=RYR12AB
#        -> {"modelo","matricula","operador","aerolinea","origen","destino",
#            "pOrigen","pDestino","foto","enlace","credito"} (map.flights
#        principal, adsbdb/Planespotters de respaldo, caché 6 h)
#    GET /bricohams/api/barcos -> {"ships": [...]} AIS local (AIS-catcher en
#        127.0.0.1:8100, solo con AIS_ENABLE=yes)
#    GET /bricohams/api/salud  -> {"ok": true}
# =====================================================================
import json
import math
import os
import re
import sqlite3
import sys
import threading
import time
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path[:0] = [os.path.dirname(os.path.realpath(globals().get('__file__', '.'))), '/usr/local/lib/bricohams']
try:
    import bricohams_telegram
except ImportError:                                    # sin el módulo: el registro funciona, sin aviso
    bricohams_telegram = None

ESTADO = os.environ.get('STATE_DIRECTORY', '/var/lib/bricohams')
UA = {'User-Agent': 'BricoHams-SDR N0CALL (+https://t.me/bricohams)'}
CALL_RE = re.compile(r'^[A-Z0-9]{1,3}[0-9][A-Z0-9]{0,4}[A-Z](/[A-Z0-9]{1,4})?$|^[A-Z0-9]{1,4}/[A-Z0-9]{3,7}$')
CACHE_VERSION = 2
ADSB_JSON = os.environ.get('ADSB_JSON', '/run/readsb/aircraft.json')
OWRX_SETTINGS_FILE = os.environ.get('OWRX_SETTINGS_FILE', '/var/lib/openwebrx/settings.json')
RETENCION_OYENTES_DIAS = 180
MAX_REGISTROS_OYENTES = 100000
NOMBRE_RE = re.compile(r"^[^\W\d_][\w .'-]{1,79}$", re.UNICODE)


def aviones(ruta=ADSB_JSON, ahora=None):
    """Solo posiciones recientes de readsb; no publica la ubicacion del receptor."""
    ahora = time.time() if ahora is None else ahora
    with open(ruta, encoding='utf-8') as f:
        datos = json.load(f)
    generado = datos['now']
    if not isinstance(generado, (float, int)) or not math.isfinite(generado) or not -5 <= ahora - generado <= 15:
        raise ValueError('readsb no ha actualizado aircraft.json en los ultimos 15 segundos')
    resultado = []
    for a in datos['aircraft']:
        lat, lon, edad = a.get('lat'), a.get('lon'), a.get('seen_pos')
        if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in (lat, lon, edad)):
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180 and 0 <= edad <= 60):
            continue
        hexid = a.get('hex', '')
        if not isinstance(hexid, str) or not re.fullmatch(r'~?[0-9a-fA-F]{6}', hexid):
            continue
        r = {'hex': hexid, 'lat': lat, 'lon': lon, 'timestamp': (generado - edad) * 1000,
             'flight': str(a.get('flight') or hexid).strip()[:32]}
        category = a.get('category')
        if isinstance(category, str) and re.fullmatch(r'[A-Z][0-9]', category.upper()):
            r['category'] = category.upper()
        for k in ('alt_baro', 'gs', 'track'):
            v = a.get(k)
            if isinstance(v, (float, int)) and math.isfinite(v):
                r[k] = v
            elif k == 'alt_baro' and v == 'ground':
                r[k] = v
        resultado.append(r)
    return {'now': generado, 'aircraft': resultado}


AIS_ENABLE = os.environ.get('AIS_ENABLE', 'no') == 'yes'
AIS_JSON_URL = os.environ.get('AIS_JSON_URL', 'http://127.0.0.1:8100/api/ships.json')
AIS_MAX_EDAD = 900


def barcos(datos, max_edad=AIS_MAX_EDAD):
    """Barcos con posicion de AIS-catcher local (api/ships.json); sin datos de la estacion."""
    lista = datos.get('ships') if isinstance(datos, dict) else datos
    if not isinstance(lista, list):
        raise ValueError('AIS-catcher no devolvio una lista de barcos')
    resultado = []
    for b in lista:
        if not isinstance(b, dict):
            continue
        mmsi, lat, lon, edad = b.get('mmsi'), b.get('lat'), b.get('lon'), b.get('last_signal')
        if not isinstance(mmsi, int) or isinstance(mmsi, bool) or not 0 < mmsi < 1000000000:
            continue
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in (lat, lon, edad)):
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180 and 0 <= edad <= max_edad) or (lat == 0 and lon == 0):
            continue
        r = {'mmsi': mmsi, 'lat': lat, 'lon': lon, 'edad': edad}
        for k, lim in (('speed', 102.2), ('cog', 359.9), ('heading', 359)):
            v = b.get(k)
            if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and 0 <= v <= lim:
                r[k] = v
        for k, n in (('shipname', 32), ('callsign', 10), ('destination', 32)):
            v = b.get(k)
            if isinstance(v, str) and v.strip():
                r[k] = re.sub(r'[\x00-\x1f<>]', '', v).strip()[:n]
        v = b.get('shiptype')
        if isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 99:
            r['shiptype'] = v
        resultado.append(r)
    return {'ships': resultado}


def barcos_locales(url=AIS_JSON_URL):
    with urllib.request.urlopen(url, timeout=4) as r:
        return barcos(json.loads(r.read(4 * 1024 * 1024).decode('utf-8')))


def _https(u):
    u = str(u or '')
    return u if u.startswith('https://') and len(u) < 500 and not any(c in u for c in '"<> \'') else ''


FUENTES_FOTO = {'wikimedia': 'Wikimedia Commons', 'planespotters': 'Planespotters.net',
                'jetphotos': 'JetPhotos', 'airport-data': 'airport-data.com'}


def _url_mapflights(u):
    """map.flights da las fotos con ruta relativa (/photos/...): se completan con su dominio."""
    u = str(u or '')
    return 'https://map.flights' + u if u.startswith('/') and not u.startswith('//') else u


def _credito_mapflights(foto):
    """«© autor · origen · licencia» de una foto de map.flights (la licencia exige citar al autor)."""
    partes = []
    autor = str(foto.get('photographer') or '').strip()[:80]
    if autor:
        partes.append('© ' + autor)
    fuente = str(foto.get('source') or '').strip().lower()
    if not fuente:
        dominio = urllib.parse.urlparse(str(foto.get('link') or foto.get('url') or '')).hostname or ''
        fuente = 'planespotters' if 'plnspttrs' in dominio or 'planespotters' in dominio else ''
    if fuente:
        partes.append(FUENTES_FOTO.get(fuente, fuente[:40]))
    licencia = str(foto.get('license') or '').strip()[:40]
    if licencia:
        partes.append(licencia)
    return ' · '.join(partes)


def _numero(v, lo, hi):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) and lo <= v <= hi else None


def _ajustes_owrx(ruta=None):
    ruta = ruta or OWRX_SETTINGS_FILE
    try:
        with open(ruta, encoding='utf-8') as f:
            ajustes = json.load(f)
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as e:
        print('api map.flights: no se pudo leer General Settings: %s' % e, file=sys.stderr, flush=True)
        return {}
    if not isinstance(ajustes, dict):
        print('api map.flights: General Settings no contiene un objeto JSON', file=sys.stderr, flush=True)
        return {}
    return ajustes


def mapflights_habilitado(ruta=None):
    return _ajustes_owrx(ruta).get('mapflights_api_enabled') is True


def _clave_mapflights_valida(clave):
    clave = clave.strip() if isinstance(clave, str) else ''
    return clave if re.fullmatch(r'[A-Za-z0-9._~+/=-]{8,256}', clave) else ''


def mapflights_config(ruta=None):
    """(habilitado, clave) desde General Settings; la clave nunca sale del servidor."""
    ajustes = _ajustes_owrx(ruta)
    clave = ajustes.get('mapflights_api_key')
    valida = _clave_mapflights_valida(clave)
    if clave and not valida:
        print('api map.flights: API key con formato no válido; uso acceso anónimo', file=sys.stderr, flush=True)
    return ajustes.get('mapflights_api_enabled') is True, valida


def ficha_avion(hexid, cs='', pedir=None, usar_mapflights=True, clave_mapflights=''):
    """Ficha por ICAO: map.flights primero; adsbdb y Planespotters como respaldo."""
    pedir = pedir or http_json
    clave_mapflights = _clave_mapflights_valida(clave_mapflights)
    icao = str(hexid or '').lower().lstrip('~')
    if not re.fullmatch(r'[0-9a-f]{6}', icao):
        return None
    cs = str(cs or '').upper().strip()
    cs = cs if re.fullmatch(r'[A-Z0-9]{3,8}', cs) else ''

    def leer(url, fuente, cabeceras=None):
        try:
            d = pedir(url, cabeceras) if cabeceras else pedir(url)
            return d if isinstance(d, dict) else None
        except Exception as e:
            print('api ficha avion (%s): %s' % (fuente, e), file=sys.stderr, flush=True)
            return None

    ficha = {}
    if usar_mapflights:
        url_mf = 'https://map.flights/api/v1/aircraft/' + icao
        mf = None
        if clave_mapflights:
            mf = leer(url_mf, 'map.flights con API key', {'x-api-key': clave_mapflights})
        if mf is None:
            mf = leer(url_mf, 'map.flights')
        if mf:
            tipo = str(mf.get('typeName') or mf.get('typecode') or '')[:120]
            matricula = str(mf.get('registration') or '')[:20]
            operador = mf.get('operator')
            if tipo:
                ficha['modelo'] = tipo
            if matricula:
                ficha['matricula'] = matricula
            if isinstance(operador, dict) and operador.get('name'):
                ficha['operador'] = str(operador['name'])[:120]
            ruta_vuelo = mf.get('route')
            if isinstance(ruta_vuelo, dict):
                def sitio(x):
                    if not isinstance(x, dict):
                        return ''
                    nombre = str(x.get('municipality') or x.get('name') or '')[:100]
                    codigo = x.get('iata') or x.get('icao')
                    if codigo:
                        nombre += ' (%s)' % str(codigo)[:8]
                    pais = x.get('country')
                    if pais:
                        nombre += ', %s' % str(pais)[:60]
                    return nombre

                def punto(x):
                    if not isinstance(x, dict):
                        return None
                    lat = _numero(x.get('lat'), -90, 90)
                    lon = _numero(x.get('lon'), -180, 180)
                    return [lat, lon] if lat is not None and lon is not None else None

                origen, destino = ruta_vuelo.get('origin'), ruta_vuelo.get('dest')
                if sitio(origen):
                    ficha['origen'] = sitio(origen)
                if sitio(destino):
                    ficha['destino'] = sitio(destino)
                punto_origen, punto_destino = punto(origen), punto(destino)
                if punto_origen:
                    ficha['pOrigen'] = punto_origen
                if punto_destino:
                    ficha['pDestino'] = punto_destino
                aerolinea = ruta_vuelo.get('airlineIcao')
                if aerolinea:
                    ficha['aerolinea'] = str(aerolinea)[:20]
            foto = mf.get('photo')
            if isinstance(foto, dict):
                foto_url = _https(_url_mapflights(foto.get('thumbnail') or foto.get('url')))
                if foto_url:
                    ficha['foto'] = foto_url
                    ficha['enlace'] = _https(foto.get('link')) or _https(_url_mapflights(foto.get('url')))
                    ficha['credito'] = _credito_mapflights(foto)
            if ficha:
                ficha['fuente'] = 'MAP.FLIGHTS'

    db = None
    if not ficha.get('modelo') or not ficha.get('matricula') or not ficha.get('operador') or \
            not ficha.get('origen') or not ficha.get('destino'):
        db = leer('https://api.adsbdb.com/v0/aircraft/%s%s' % (icao, '?callsign=' + cs if cs else ''),
                  'adsbdb')
    r = db.get('response') if db and isinstance(db.get('response'), dict) else {}
    av = r.get('aircraft') if isinstance(r.get('aircraft'), dict) else None
    if av:
        modelo = ' '.join(str(x) for x in (av.get('manufacturer'), av.get('type')) if x)
        if av.get('icao_type'):
            modelo += ' (%s)' % av['icao_type']
        ficha.setdefault('modelo', modelo.strip()[:120])
        ficha.setdefault('matricula', str(av.get('registration') or '')[:20])
        ficha.setdefault('operador', str(av.get('registered_owner') or '')[:120])
        if not ficha.get('foto'):
            ficha['foto'] = _https(av.get('url_photo_thumbnail'))
            if ficha['foto']:
                ficha['credito'] = 'airport-data.com'
                ficha['enlace'] = _https(av.get('url_photo'))
    fr = r.get('flightroute') if isinstance(r.get('flightroute'), dict) else None
    if (not ficha.get('origen') or not ficha.get('destino')) and cs:
        rc = leer('https://api.adsbdb.com/v0/callsign/' + cs, 'adsbdb')
        rr = rc.get('response') if rc and isinstance(rc.get('response'), dict) else {}
        fr = fr or (rr.get('flightroute') if isinstance(rr.get('flightroute'), dict) else None)
    if fr:
        def sitio(x):
            if not isinstance(x, dict):
                return ''
            s = str(x.get('municipality') or x.get('name') or '')
            cod = x.get('iata_code') or x.get('icao_code')
            if cod:
                s += ' (%s)' % cod
            if x.get('country_name'):
                s += ', %s' % x['country_name']
            return s[:120]

        def punto(x):
            if not isinstance(x, dict):
                return None
            lat, lon = _numero(x.get('latitude'), -90, 90), _numero(x.get('longitude'), -180, 180)
            return [lat, lon] if lat is not None and lon is not None else None

        al = fr.get('airline')
        if not ficha.get('aerolinea') and isinstance(al, dict):
            ficha['aerolinea'] = str(al.get('name') or '')[:120]
        if not ficha.get('origen'):
            ficha['origen'] = sitio(fr.get('origin'))
        if not ficha.get('destino'):
            ficha['destino'] = sitio(fr.get('destination'))
        if not ficha.get('pOrigen'):
            ficha['pOrigen'] = punto(fr.get('origin'))
        if not ficha.get('pDestino'):
            ficha['pDestino'] = punto(fr.get('destination'))
    ps = leer('https://api.planespotters.net/pub/photos/hex/' + icao, 'Planespotters') if not ficha.get('foto') else None
    fotos = ps.get('photos') if ps and isinstance(ps.get('photos'), list) else []
    if fotos and isinstance(fotos[0], dict):
        f = fotos[0]
        mini = f.get('thumbnail_large') or f.get('thumbnail') or {}
        src = _https(mini.get('src') if isinstance(mini, dict) else '')
        if src:
            ficha['foto'] = src
            ficha['enlace'] = _https(f.get('link'))
            ficha['credito'] = '© %s · Planespotters.net' % str(f.get('photographer') or 'autor')[:80]
    ficha = {k: v for k, v in ficha.items() if v}
    return ficha or None


class CacheFichas:
    """Cache en memoria (6 h, 500 entradas) para no repetir consultas externas."""

    def __init__(self, ttl=6 * 3600, maximo=500):
        self.ttl, self.maximo, self.d, self.lock = ttl, maximo, {}, threading.Lock()

    def obtener(self, hexid, cs, buscar=ficha_avion, variante=''):
        clave = '%s|%s%s' % (str(hexid).lower(), str(cs).upper(),
                             '|' + variante if variante else '')
        ahora = time.time()
        with self.lock:
            hit = self.d.get(clave)
            if hit and ahora - hit[0] < self.ttl:
                return hit[1]
        ficha = buscar(hexid, cs)
        with self.lock:
            if len(self.d) >= self.maximo:
                self.d.pop(min(self.d, key=lambda k: self.d[k][0]))
            # Sin datos (o fallo externo): se reintenta a los 10 minutos.
            self.d[clave] = (ahora if ficha else ahora - self.ttl + 600, ficha)
        return ficha


def http_json(url, headers=None, timeout=8):
    return json.load(urllib.request.urlopen(
        urllib.request.Request(url, headers={**UA, **(headers or {})}), timeout=timeout))


def http_json_con_cabeceras(url, headers, timeout=8):
    return json.load(urllib.request.urlopen(
        urllib.request.Request(url, headers={**UA, **headers}), timeout=timeout))


def http_json_post(url, datos, timeout=8):
    req = urllib.request.Request(url, data=json.dumps(datos).encode(),
                                 headers={**UA, 'Content-Type': 'application/json'}, method='POST')
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def http_texto(url, timeout=8):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read().decode('utf-8', 'replace')


def radioid(call, get=http_json):
    try:
        d = get('https://radioid.net/api/dmr/user/?' + urllib.parse.urlencode({'callsign': call}))
    except Exception:
        return {}
    r = (d or {}).get('results') or []
    if not r:
        return {}
    x = r[0]
    return {'nombre': ' '.join(p for p in (x.get('fname'), x.get('surname')) if p), 'ciudad': x.get('city') or '',
            'region': x.get('state') or '', 'pais': x.get('country') or '', 'dmrid': x.get('id'), 'fuente': 'RadioID'}


class HamQTH:
    LOGIN_URL = 'https://www.hamqth.com/api/v2/login'
    CALLBOOK_URL = 'https://www.hamqth.com/api/v2/callbook/'

    def __init__(self, usuario, clave, post=http_json_post, get=http_json_con_cabeceras,
                 reloj=time.monotonic):
        self.u, self.p, self.post, self.get, self.reloj = usuario, clave, post, get, reloj
        self.token, self.expira, self.lock = None, 0, threading.Lock()

    def _login(self):
        respuesta = self.post(self.LOGIN_URL, {'callsign': self.u, 'password': self.p})
        self.token = respuesta.get('token')
        self.expira = self.reloj() + max(0, int(respuesta.get('expiresIn', 3600)) - 60)
        return self.token

    def buscar(self, call):
        if not self.u or not self.p:
            return {}
        url = self.CALLBOOK_URL + urllib.parse.quote(call, safe='') + '?app=BricoHams-SDR'   # «app»: estadísticas de HamQTH
        with self.lock:
            try:
                for intento in range(2):
                    if not self.token or self.reloj() >= self.expira:
                        if not self._login():
                            return {}
                    try:
                        d = self.get(url, {'Authorization': 'Bearer ' + self.token})
                    except Exception as e:
                        if intento == 0 and getattr(e, 'code', None) == 401:
                            self.token = None
                            continue
                        return {}
                    address = d.get('address') or {}
                    region = d.get('region') or {}
                    datos = {
                        'nombre': (d.get('name') or d.get('nick') or '').strip(),
                        'ciudad': (address.get('city') or d.get('qth') or '').strip(),
                        'region': (region.get('oblast') or region.get('usState') or region.get('district') or '').strip(),
                        'pais': (d.get('country') or address.get('country') or '').strip(),
                        'foto': d.get('picture') or '',
                        'fuente': 'HamQTH',
                    }
                    return datos if any(datos[k] for k in ('nombre', 'ciudad', 'region', 'pais', 'foto')) else {}
            except Exception:
                self.token = None
        return {}


class Qrz:
    URL = 'https://xmldata.qrz.com/xml/current/'

    def __init__(self, usuario, clave, get=http_texto):
        self.u, self.p, self.get, self.key, self.lock = usuario, clave, get, None, threading.Lock()

    def _xml(self, params):
        t = self.get(self.URL + '?' + ';'.join('%s=%s' % (k, urllib.parse.quote(str(v))) for k, v in params.items()))
        t = re.sub(r'\sxmlns="[^"]+"', '', t, count=1)
        return ET.fromstring(t)

    def _login(self):
        r = self._xml({'username': self.u, 'password': self.p, 'agent': 'bricohams-sdr'})
        self.key = r.findtext('Session/Key')
        return self.key

    def buscar(self, call):
        if not self.u or not self.p:
            return {}
        with self.lock:
            try:
                for _ in range(2):
                    if not self.key and not self._login():
                        return {}
                    r = self._xml({'s': self.key, 'callsign': call})
                    err = r.findtext('Session/Error') or ''
                    if r.find('Callsign') is not None:
                        c = r.find('Callsign')
                        g = lambda k: (c.findtext(k) or '').strip()
                        return {'nombre': ' '.join(p for p in (g('fname'), g('name')) if p), 'ciudad': g('addr2'),
                                'region': g('state'), 'pais': g('country'), 'foto': g('image'), 'fuente': 'QRZ'}
                    if 'Session Timeout' in err or 'Invalid session key' in err:
                        self.key = None
                        continue
                    return {}
            except Exception:
                self.key = None
        return {}


class Cache:
    def __init__(self, ruta, dias=7):
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        self.c = sqlite3.connect(ruta, check_same_thread=False)
        self.c.execute('CREATE TABLE IF NOT EXISTS ind (call TEXT PRIMARY KEY, t REAL, datos TEXT)')
        self.dias, self.lock = dias, threading.Lock()

    def get(self, call):
        with self.lock:
            r = self.c.execute('SELECT t, datos FROM ind WHERE call = ?', (call,)).fetchone()
        if r and time.time() - r[0] < self.dias * 86400:
            guardado = json.loads(r[1])
            if guardado.get('_cache_version') == CACHE_VERSION:
                return guardado['datos']
        return None

    def put(self, call, datos):
        with self.lock:
            guardado = {'_cache_version': CACHE_VERSION, 'datos': datos}
            self.c.execute('INSERT OR REPLACE INTO ind VALUES (?,?,?)',
                           (call, time.time(), json.dumps(guardado, ensure_ascii=False)))
            self.c.commit()


def buscar_indicativo(call, cache, qrz, rid=radioid, hamqth=None):
    call = (call or '').upper().strip()
    base = call.split('/')[0] if '/' in call and len(call.split('/')[0]) > 3 else call
    if not CALL_RE.match(call) and not CALL_RE.match(base):
        return None
    hit = cache.get(base)
    if hit is not None:
        return hit
    d = {'call': base, 'nombre': '', 'ciudad': '', 'region': '', 'pais': '', 'foto': '', 'fuente': ''}
    h = hamqth.buscar(base) if hamqth else {}
    q = qrz.buscar(base) if qrz and (not h.get('nombre') or not h.get('foto')) else {}
    r = rid(base) if any(not (h.get(k) or q.get(k)) for k in ('nombre', 'ciudad', 'pais')) else {}
    for fuente in (r, q, h):
        for k, v in fuente.items():
            if v:
                d[k] = v
    nombres = [f['fuente'] for f in (h, q, r) if f.get('fuente')]
    d['fuente'] = ' + '.join(nombres)
    cache.put(base, d)
    return d


def validar_registro_oyente(datos):
    """Valida una identificación enviada voluntariamente; nunca recibe ni guarda IP."""
    if not isinstance(datos, dict) or datos.get('consentimiento') is not True:
        return None
    valor = datos.get('identificador')
    if not isinstance(valor, str) or len(valor) > 120:
        return None
    valor = unicodedata.normalize('NFKC', valor).strip()
    if CALL_RE.fullmatch(valor.upper()):
        return valor.upper(), 'indicativo'
    if NOMBRE_RE.fullmatch(valor):
        return valor, 'nombre'
    return None


class RegistroOyentes:
    def __init__(self, ruta, reloj=time.time, aviso=None):
        self.aviso = aviso
        os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
        mascara = os.umask(0o077)
        try:
            self.c = sqlite3.connect(ruta, check_same_thread=False)
        finally:
            os.umask(mascara)
        try:
            os.chmod(ruta, 0o600)
        except OSError:
            self.c.close()
            raise
        self.reloj = reloj
        self.lock = threading.Lock()
        self.c.execute('''CREATE TABLE IF NOT EXISTS registro_oyentes (
            id INTEGER PRIMARY KEY,
            identificador TEXT NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('indicativo', 'nombre')),
            creado INTEGER NOT NULL,
            consentimiento TEXT NOT NULL
        )''')
        self.c.execute('CREATE INDEX IF NOT EXISTS registro_oyentes_creado ON registro_oyentes(creado)')
        self.c.commit()
        with self.lock:
            self._limpiar()

    def _limpiar(self):
        corte = int(self.reloj()) - RETENCION_OYENTES_DIAS * 86400
        self.c.execute('DELETE FROM registro_oyentes WHERE creado < ?', (corte,))
        self.c.execute('''DELETE FROM registro_oyentes WHERE id NOT IN
            (SELECT id FROM registro_oyentes ORDER BY creado DESC, id DESC LIMIT ?)''',
                       (MAX_REGISTROS_OYENTES,))
        self.c.commit()

    def registrar(self, datos):
        identificacion = validar_registro_oyente(datos)
        if identificacion is None:
            return False
        valor, tipo = identificacion
        with self.lock:
            ahora = int(self.reloj())
            self.c.execute(
                'INSERT INTO registro_oyentes (identificador, tipo, creado, consentimiento) VALUES (?, ?, ?, ?)',
                (valor, tipo, ahora, 'v1'))
            self._limpiar()
        if self.aviso:
            try:
                self.aviso(valor, tipo)
            except Exception as e:                 # noqa: BLE001 — el aviso nunca debe romper el registro
                print('api oyentes: aviso: %s' % e, file=sys.stderr, flush=True)
        return True

    def listar(self, limite=1000):
        limite = max(1, min(int(limite), MAX_REGISTROS_OYENTES))
        with self.lock:
            return self.c.execute(
                'SELECT identificador, tipo, creado FROM registro_oyentes ORDER BY creado DESC, id DESC LIMIT ?',
                (limite,)).fetchall()


def crear_manejador(cache, hamqth, qrz, fichas, oyentes):
    class H(BaseHTTPRequestHandler):
        def _json(self, code, obj, cache_control='public, max-age=3600'):
            b = json.dumps(obj, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', cache_control)
            self.send_header('Content-Length', str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            u = urllib.parse.urlparse(self.path)
            if u.path == '/bricohams/api/aviones':
                try:
                    d = aviones()
                except (OSError, ValueError, KeyError, TypeError) as e:
                    print('api ADS-B: %s' % e, file=sys.stderr, flush=True)
                    return self._json(503, {'error': 'ADS-B local no disponible o sin datos recientes'}, 'no-store')
                return self._json(200, d, 'no-store')
            if u.path == '/bricohams/api/barcos':
                if not AIS_ENABLE:
                    return self._json(404, {'error': 'AIS local no instalado'}, 'no-store')
                try:
                    d = barcos_locales()
                except (OSError, ValueError, KeyError, TypeError, UnicodeDecodeError) as e:
                    print('api AIS: %s' % e, file=sys.stderr, flush=True)
                    return self._json(503, {'error': 'AIS local no disponible'}, 'no-store')
                return self._json(200, d, 'no-store')
            if u.path == '/bricohams/api/avion':
                q = urllib.parse.parse_qs(u.query)
                hexid = q.get('hex', [''])[0][:8]
                if not re.fullmatch(r'~?[0-9a-fA-F]{6}', hexid):
                    return self._json(400, {'error': 'hex no válido'}, 'no-store')
                usar_mapflights, clave_mapflights = mapflights_config()
                variante = ('mapflights+clave' if clave_mapflights else 'mapflights') \
                    if usar_mapflights else 'sin-mapflights'
                ficha = fichas.obtener(
                    hexid, q.get('cs', [''])[0][:10],
                    buscar=lambda h, cs: ficha_avion(h, cs, usar_mapflights=usar_mapflights,
                                                     clave_mapflights=clave_mapflights),
                    variante=variante)
                return self._json(200, ficha or {}, 'public, max-age=21600')
            if u.path.endswith('/salud'):
                return self._json(200, {'ok': True, 'hamqth': bool(hamqth.u), 'qrz': bool(qrz.u)})
            if u.path.endswith('/indicativo'):
                call = urllib.parse.parse_qs(u.query).get('call', [''])[0]
                d = buscar_indicativo(call, cache, qrz, hamqth=hamqth)
                return self._json(200 if d else 400, d or {'error': 'indicativo no válido'})
            self._json(404, {'error': 'no existe'})

        def do_POST(self):
            u = urllib.parse.urlparse(self.path)
            if u.path != '/bricohams/api/oyentes':
                return self._json(404, {'error': 'no existe'}, 'no-store')
            origen = self.headers.get('Origin')
            host_header = self.headers.get('Host', '')
            if origen:
                try:
                    if urllib.parse.urlsplit(origen).netloc.lower() != host_header.lower():
                        return self._json(403, {'error': 'origen no permitido'}, 'no-store')
                except ValueError:
                    return self._json(403, {'error': 'origen no permitido'}, 'no-store')
            if self.headers.get_content_type() != 'application/json':
                return self._json(415, {'error': 'se requiere application/json'}, 'no-store')
            try:
                longitud = int(self.headers.get('Content-Length', '0'))
            except ValueError:
                return self._json(400, {'error': 'longitud no válida'}, 'no-store')
            if not 0 < longitud <= 1024:
                return self._json(413 if longitud > 1024 else 400, {'error': 'tamaño no válido'}, 'no-store')
            try:
                datos = json.loads(self.rfile.read(longitud))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return self._json(400, {'error': 'JSON no válido'}, 'no-store')
            if not oyentes.registrar(datos):
                return self._json(400, {'error': 'identificación o consentimiento no válido'}, 'no-store')
            self._json(201, {'ok': True}, 'no-store')

        def log_message(self, *a):
            pass

    return H


def aviso_oyente_telegram(valor, tipo):
    """Texto HTML del aviso de un oyente registrado (indicativo o nombre ya validados)."""
    tg = bricohams_telegram
    if tipo == 'indicativo':
        return '📝 <b>Oyente registrado</b>: indicativo <b>%s</b> · <a href="https://www.qrz.com/db/%s">QRZ</a>' % (
            tg.esc(valor), urllib.parse.quote(valor))
    return '📝 <b>Oyente registrado</b>: %s' % tg.esc(valor)


def avisador_oyentes():
    """Función (valor, tipo) que avisa por Telegram, o None si no hay Telegram u OYENTES_TELEGRAM=no."""
    if not bricohams_telegram or not bricohams_telegram.activo(os.environ.get('OYENTES_TELEGRAM'), 'yes'):
        return None
    tg = bricohams_telegram.Avisador(nombre='api oyentes')
    if not tg.configurado:
        return None
    return lambda valor, tipo: tg.avisar(aviso_oyente_telegram(valor, tipo))


def servidor(host='127.0.0.1', puerto=8075):
    cache = Cache(os.path.join(ESTADO, 'indicativos.sqlite'))
    aviso = avisador_oyentes()
    oyentes = RegistroOyentes(os.path.join(ESTADO, 'oyentes.sqlite'), aviso=aviso)
    hamqth = HamQTH(os.environ.get('HAMQTH_USER', ''), os.environ.get('HAMQTH_PASS', ''))
    qrz = Qrz(os.environ.get('QRZ_USER', ''), os.environ.get('QRZ_PASS', ''))
    fichas = CacheFichas()
    httpd = ThreadingHTTPServer((host, puerto), crear_manejador(cache, hamqth, qrz, fichas, oyentes))
    print('api: http://%s:%d/bricohams/api/ (HamQTH %s, QRZ %s, registro->Telegram %s)' %
          (host, puerto, 'sí' if hamqth.u else 'no', 'sí' if qrz.u else 'no', 'sí' if aviso else 'no'), flush=True)
    httpd.serve_forever()


if __name__ == '__main__':
    sys.exit(servidor(os.environ.get('API_HOST', '127.0.0.1'), int(os.environ.get('API_PORT', '8075'))))
