#!/usr/bin/env python3
"""BricoHams · puente de radiosondas (AEMET, 400-406 MHz) — ADR-72, manual 51.

radiosonde_auto_rx (contenedor Docker, bricohams-sondas-rx) decodifica las sondas y emite paquetes UDP JSON
«PAYLOAD_SUMMARY» a 127.0.0.1:55673. Este puente (solo biblioteca estándar):
  · valida cada paquete (tipos, rangos, tamaño) y descarta lo que no cumple,
  · quita duplicados (serie+frame), guarda la traza de cada sonda y calcula el reventón (burst),
  · pide a SondeHub la predicción de aterrizaje (como mucho 1 vez cada 5 min por sonda activa),
  · escribe de forma atómica plugins/receiver/meteo/sondas.json (mapa y pestaña Tiempo),
  · si SONDAS_MQTT=yes publica <tema>/<serie>/telemetria (retenido), <tema>/<serie>/aterrizaje y <tema>/estado.
Modos de prueba (sin red ni disco de servicio):
  bricohams-sondas --paquete '<json>'   imprime el paquete ya validado (o el motivo del rechazo)
  bricohams-sondas --station-cfg PLANTILLA   imprime el station.cfg de auto_rx: la plantilla oficial
                                        (station.cfg.example) con nuestras claves tomadas del entorno
Los datos de predicción son de SondeHub (CC BY-SA): la web los atribuye.
"""
import collections
import configparser
import io
import json
import math
import os
import re
import socket
import sys
import tempfile
import time
import urllib.parse
import urllib.request

sys.path[:0] = [os.path.dirname(os.path.realpath(__file__)), '/usr/local/lib/bricohams']

VERSION = '1'
PUERTO_UDP = 55673
MAX_PAQUETE = 8192
MAX_PUNTOS = 2000
CADUCA_S = 2 * 3600
PREDICCION_CADA_S = 300
MAX_RESPUESTA = 2 * 1024 * 1024
API_PREDICCION = 'https://api.v2.sondehub.org/predictions'
AGENTE = 'BricoHams-SDR/1 (+https://github.com/Brico-Hams/bricohams-sdr; radiosondas)'
RE_SERIE = re.compile(r'^[A-Za-z0-9-]{3,20}$')
RE_TEMA = re.compile(r'^[A-Za-z0-9_-]+(/[A-Za-z0-9_-]+)*$')
RE_HOST = re.compile(r'^[A-Za-z0-9]([A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$')
SITIO_LANZAMIENTO = {'id': '08430', 'nombre': 'AEMET Murcia', 'lat': 38.002, 'lon': -1.171}
BANDA = (400.05, 406.0)


def _num(v, lo, hi):
    """Número finito dentro de [lo, hi]; None si no vale (los bool no cuentan como número)."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    v = float(v)
    if not math.isfinite(v) or v < lo or v > hi:
        return None
    return v


def _texto(v, largo):
    """Cadena imprimible acotada (sin controles) o None."""
    if not isinstance(v, str):
        return None
    v = ''.join(c for c in v if c.isprintable())[:largo].strip()
    return v or None


def _freq_mhz(v):
    """Frecuencia de auto_rx en MHz: número (MHz o Hz) o cadena tipo «403.400 MHz». None si no se entiende."""
    if isinstance(v, bool):
        return None
    if isinstance(v, str):
        m = re.match(r'^\s*([0-9]+(?:\.[0-9]+)?)\s*(?:MHz)?\s*$', v, re.I)
        if not m:
            return None
        v = float(m.group(1))
    if not isinstance(v, (int, float)) or not math.isfinite(v):
        return None
    v = float(v)
    return v / 1e6 if v > 1e6 else v


def validar_paquete(crudo):
    """Devuelve (paquete_limpio, None) o (None, motivo). Acepta bytes o str."""
    if isinstance(crudo, (bytes, bytearray)):
        if len(crudo) > MAX_PAQUETE:
            return None, 'paquete demasiado grande'
        try:
            crudo = bytes(crudo).decode('utf-8')
        except UnicodeDecodeError:
            return None, 'no es UTF-8'
    elif len(crudo) > MAX_PAQUETE:
        return None, 'paquete demasiado grande'
    try:
        d = json.loads(crudo)
    except (ValueError, RecursionError):
        return None, 'JSON inválido'
    if not isinstance(d, dict):
        return None, 'no es un objeto JSON'
    if d.get('type') not in (None, 'PAYLOAD_SUMMARY'):
        return None, 'tipo de paquete no soportado'
    serie = d.get('callsign')
    if not isinstance(serie, str) or not RE_SERIE.match(serie):
        return None, 'serie inválida'
    lat, lon, alt = _num(d.get('latitude'), -90, 90), _num(d.get('longitude'), -180, 180), \
        _num(d.get('altitude'), -500, 50000)
    if lat is None or lon is None or alt is None:
        return None, 'posición fuera de rango'
    frame = d.get('frame')
    if frame is not None:
        if isinstance(frame, bool) or not isinstance(frame, int) or not 0 <= frame <= 10 ** 9:
            return None, 'frame inválido'
    p = {
        'serie': serie, 'lat': round(lat, 5), 'lon': round(lon, 5), 'alt': round(alt, 1), 'frame': frame,
        'modelo': _texto(d.get('model'), 24), 'datetime': _texto(d.get('datetime'), 40),
    }
    for clave, orig, lo, hi, dec in (
            ('vel', 'speed', 0, 1000, 1), ('rumbo', 'heading', 0, 360, 0), ('vel_v', 'vel_v', -300, 300, 1),
            ('temp', 'temp', -150, 80, 1), ('humedad', 'humidity', 0, 100, 1), ('presion', 'pressure', 0, 1500, 1),
            ('freq', 'freq', 300, 500, 3), ('sats', 'sats', 0, 64, 0), ('bateria', 'batt', 0, 30, 2),
            ('snr', 'snr', -50, 100, 1)):
        if d.get(orig) is None:
            p[clave] = None
            continue
        v = _num(_freq_mhz(d.get(orig)) if orig == 'freq' else d.get(orig), lo, hi)
        if v is None:                       # un campo opcional absurdo se ignora, no tumba el paquete
            p[clave] = None
        else:
            p[clave] = int(v) if dec == 0 else round(v, dec)
    return p, None


def siguiente_lanzamiento(ahora):
    """Próximo lanzamiento de las 00 o 12 UTC (epoch)."""
    base = ahora - ahora % 43200
    return int(base + 43200)


def validar_prediccion(respuesta, serie):
    """Extrae el punto de aterrizaje de la respuesta de SondeHub. Devuelve dict o None."""
    if isinstance(respuesta, dict):
        respuesta = [respuesta]
    if not isinstance(respuesta, list):
        return None
    for it in respuesta[:50]:
        if not isinstance(it, dict) or it.get('vehicle') != serie:
            continue
        datos = it.get('data')
        if isinstance(datos, str):
            try:
                datos = json.loads(datos)
            except (ValueError, RecursionError):
                return None
        if isinstance(datos, dict):
            datos = list(datos.values())
        if not isinstance(datos, list) or not datos:
            return None
        ruta = []
        for pt in datos[:5000]:
            if not isinstance(pt, dict):
                continue
            la = _num(pt.get('lat', pt.get('latitude')), -90, 90)
            lo = _num(pt.get('lon', pt.get('longitude')), -180, 180)
            al = _num(pt.get('alt', pt.get('altitude')), -500, 50000)
            if la is not None and lo is not None and al is not None:
                ruta.append([round(la, 5), round(lo, 5), round(al, 1)])
        if not ruta:
            return None
        paso = max(1, len(ruta) // 60)
        reducida = ruta[::paso]
        if reducida[-1] != ruta[-1]:
            reducida.append(ruta[-1])
        t = _num(it.get('time'), 0, 4e9) if not isinstance(it.get('time'), str) else None
        return {'lat': ruta[-1][0], 'lon': ruta[-1][1], 'alt': ruta[-1][2], 'ruta': reducida,
                'hora': int(t) if t is not None else None}
    return None


def pedir_prediccion(serie):
    """Fetcher real: HTTPS con tiempo límite, tamaño acotado y User-Agent propio."""
    if not RE_SERIE.match(serie):
        return None
    url = API_PREDICCION + '?' + urllib.parse.urlencode({'vehicles': serie})
    req = urllib.request.Request(url, headers={'User-Agent': AGENTE, 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=15) as r:
        cuerpo = r.read(MAX_RESPUESTA + 1)
    if len(cuerpo) > MAX_RESPUESTA:
        return None
    return json.loads(cuerpo.decode('utf-8'))


def escribir_atomico(ruta, datos, modo=0o644):
    d = os.path.dirname(ruta) or '.'
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix='.sondas-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, separators=(',', ':'))
        os.chmod(tmp, modo)
        os.replace(tmp, ruta)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


class Seguimiento:
    """Estado de todas las sondas: trazas, duplicados, reventón, predicción y caducidad."""

    def __init__(self, ruta_estado=None, prediccion=True, fetcher=None, publicador=None, tema='bricohams/sondas'):
        self.sondas = {}
        self.ruta_estado = ruta_estado
        self.prediccion = prediccion
        self.fetcher = fetcher or pedir_prediccion
        self.pub = publicador
        self.tema = tema
        self.recibidos = self.descartados = 0

    def temas(self, serie):
        return {'telemetria': '%s/%s/telemetria' % (self.tema, serie),
                'aterrizaje': '%s/%s/aterrizaje' % (self.tema, serie),
                'estado': '%s/estado' % self.tema}

    def procesar(self, crudo, ahora=None):
        """Valida y aplica un paquete. Devuelve la sonda actualizada o None (duplicado/rechazo)."""
        ahora = time.time() if ahora is None else ahora
        p, motivo = validar_paquete(crudo)
        if p is None:
            self.descartados += 1
            return None
        s = self.sondas.setdefault(p['serie'], {
            'serie': p['serie'], 'traza': [], 'burst': None, 'prediccion': None, 'ultima_pred': 0,
            'primera': ahora, 'recientes': collections.deque(maxlen=512)})
        clave = p['frame'] if p['frame'] is not None else p['datetime']
        if clave is not None and clave in s['recientes']:
            self.descartados += 1
            return None
        s['recientes'].append(clave)
        self.recibidos += 1
        for k in ('modelo', 'freq', 'vel', 'rumbo', 'vel_v', 'temp', 'humedad', 'presion', 'sats', 'bateria',
                  'snr', 'datetime', 'frame'):
            if p[k] is not None:
                s[k] = p[k]
        s.update(lat=p['lat'], lon=p['lon'], alt=p['alt'], visto=ahora)
        s['traza'].append([p['lat'], p['lon'], p['alt'], int(ahora)])
        if len(s['traza']) > MAX_PUNTOS:
            del s['traza'][:len(s['traza']) - MAX_PUNTOS]
        self._reventon(s)
        return s

    @staticmethod
    def _reventon(s):
        """Reventón = punto más alto de la traza, fijado cuando la sonda empieza a descender (vel_v < -1)."""
        if s['burst'] is not None:
            return
        vv = s.get('vel_v')
        if vv is None or vv >= -1:
            return
        mejor = max(s['traza'], key=lambda t: t[2])
        if mejor[2] - s['alt'] > 50:
            s['burst'] = {'lat': mejor[0], 'lon': mejor[1], 'alt': mejor[2], 'hora': mejor[3]}

    def expirar(self, ahora=None):
        ahora = time.time() if ahora is None else ahora
        for serie in [k for k, s in self.sondas.items() if ahora - s['visto'] > CADUCA_S]:
            del self.sondas[serie]

    def activa(self, s, ahora):
        return ahora - s['visto'] <= CADUCA_S

    def actualizar_predicciones(self, ahora=None):
        """Como mucho una consulta cada 5 min por sonda, solo mientras está activa (descendiendo no hace falta
        reintentar si ya aterrizó: sin frames nuevos en 5 min se deja de consultar)."""
        ahora = time.time() if ahora is None else ahora
        if not self.prediccion:
            return 0
        n = 0
        for serie, s in self.sondas.items():
            if ahora - s['visto'] > PREDICCION_CADA_S or ahora - s['ultima_pred'] < PREDICCION_CADA_S:
                continue
            s['ultima_pred'] = ahora                    # también si falla: nunca más de 1 cada 5 min
            n += 1
            try:
                pred = validar_prediccion(self.fetcher(serie), serie)
            except Exception:                           # red, HTTP, JSON: la telemetría sigue sin predicción
                pred = None
            if pred is not None:
                s['prediccion'] = pred
                self.publicar_aterrizaje(serie, pred)
        return n

    def publicar_telemetria(self, s):
        if self.pub is None:
            return
        t = self.temas(s['serie'])['telemetria']
        self.pub.publicar(t, self.vista(s), True)

    def publicar_aterrizaje(self, serie, pred):
        if self.pub is not None:
            self.pub.publicar(self.temas(serie)['aterrizaje'], pred, True)

    @staticmethod
    def vista(s):
        """Sonda sin campos internos y sin traza (para MQTT: último estado)."""
        omit = {'traza', 'recientes', 'ultima_pred', 'primera', 'prediccion'}
        return {k: v for k, v in s.items() if k not in omit}

    def documento(self, mqtt_estado, ahora=None):
        ahora = time.time() if ahora is None else ahora
        lista = []
        for s in sorted(self.sondas.values(), key=lambda x: -x['visto']):
            d = {k: v for k, v in s.items() if k not in ('recientes', 'ultima_pred', 'primera')}
            d['activa'] = ahora - s['visto'] <= PREDICCION_CADA_S
            lista.append(d)
        return {'version': VERSION, 'actualizado': int(ahora), 'sitio': SITIO_LANZAMIENTO,
                'proximo_lanzamiento': siguiente_lanzamiento(ahora), 'prediccion': bool(self.prediccion),
                'mqtt': mqtt_estado, 'sondas': lista}

    def guardar(self):
        if not self.ruta_estado:
            return
        datos = {k: {kk: vv for kk, vv in s.items() if kk != 'recientes'} for k, s in self.sondas.items()}
        escribir_atomico(self.ruta_estado, datos, 0o600)

    def cargar(self, ahora=None):
        ahora = time.time() if ahora is None else ahora
        if not self.ruta_estado or not os.path.exists(self.ruta_estado):
            return
        try:
            with open(self.ruta_estado, encoding='utf-8') as f:
                datos = json.load(f)
        except (OSError, ValueError):
            return
        if not isinstance(datos, dict):
            return
        for serie, s in datos.items():
            if not isinstance(s, dict) or not RE_SERIE.match(str(serie)):
                continue
            visto = _num(s.get('visto'), 0, 4e9)
            traza = s.get('traza')
            if visto is None or ahora - visto > CADUCA_S or not isinstance(traza, list):
                continue
            ok = [t for t in traza[-MAX_PUNTOS:] if isinstance(t, list) and len(t) == 4 and
                  _num(t[0], -90, 90) is not None and _num(t[1], -180, 180) is not None and
                  _num(t[2], -500, 50000) is not None and _num(t[3], 0, 4e9) is not None]
            if not ok or _num(s.get('lat'), -90, 90) is None or _num(s.get('lon'), -180, 180) is None \
                    or _num(s.get('alt'), -500, 50000) is None:
                continue
            s['traza'] = ok
            s['serie'] = serie
            s['recientes'] = collections.deque(maxlen=512)
            s.setdefault('burst', None)
            s.setdefault('prediccion', None)
            s['ultima_pred'] = 0
            s.setdefault('primera', visto)
            self.sondas[serie] = s


def leer_credenciales(ruta):
    """Lee KEY='valor' (comillas de shell) de sondas.env; devuelve dict. Nunca falla."""
    out = {}
    try:
        with open(ruta, encoding='utf-8') as f:
            for linea in f:
                m = re.match(r"^([A-Z_]+)='((?:[^']|'\\'')*)'\s*$", linea.rstrip('\n'))
                if m:
                    out[m.group(1)] = m.group(2).replace("'\\''", "'")
    except OSError:
        pass
    return out


def cfg_desde_env(env=None):
    e = os.environ if env is None else env
    def si(k, defecto='no'):
        return str(e.get(k, defecto)).strip().lower() in ('yes', 'si', 'sí', 'true', '1')
    cred = e.get('SONDAS_ENV_FILE') or os.path.join(e.get('CREDENTIALS_DIRECTORY', ''), 'sondas.env')
    c = leer_credenciales(cred) if (e.get('SONDAS_ENV_FILE') or e.get('CREDENTIALS_DIRECTORY')) else {}
    try:
        puerto = int(e.get('SONDAS_MQTT_PORT', '1883'))
    except ValueError:
        puerto = 1883
    return {
        'salida': e.get('SONDAS_OUT', '/usr/share/openwebrx/htdocs/plugins/receiver/meteo/sondas.json'),
        'estado': os.path.join(e.get('STATE_DIRECTORY', e.get('SONDAS_STATE_DIR', '/var/lib/bricohams/sondas')),
                               'estado.json'),
        'udp_puerto': int(e.get('SONDAS_UDP_PORT', PUERTO_UDP)),
        'prediccion': si('SONDAS_PREDICCION', 'yes'),
        'mqtt': si('SONDAS_MQTT'),
        'mqtt_host': e.get('SONDAS_MQTT_HOST', '127.0.0.1'),
        'mqtt_puerto': puerto,
        'mqtt_tema': e.get('SONDAS_MQTT_TOPIC', 'bricohams/sondas').strip('/'),
        'mqtt_user': c.get('SONDAS_MQTT_USER', ''),
        'mqtt_pass': c.get('SONDAS_MQTT_PASS', ''),
    }


def mqtt_publico(cfg, conectado=False):
    """Estado MQTT para la web: SOLO activo, host, puerto y tema (nunca usuario ni clave)."""
    return {'activo': bool(cfg['mqtt']), 'host': cfg['mqtt_host'] if cfg['mqtt'] else None,
            'puerto': cfg['mqtt_puerto'] if cfg['mqtt'] else None,
            'tema': cfg['mqtt_tema'] if cfg['mqtt'] else None, 'conectado': bool(conectado)}


def _ini(v):
    """Valor de station.cfg en una línea, sin saltos ni caracteres que rompan el INI."""
    return re.sub(r'[\r\n=;#%]', '', str(v)).strip()


def generar_station_cfg(plantilla, e=None):
    """station.cfg de radiosonde_auto_rx: la plantilla oficial (station.cfg.example) con solo nuestras claves
    sustituidas desde el entorno (bricohams.env). Valida y lanza ValueError."""
    e = os.environ if e is None else e
    cp = configparser.ConfigParser(interpolation=None, strict=False)
    cp.optionxform = str
    try:
        with open(plantilla, encoding='utf-8') as f:
            cp.read_file(f)
    except OSError as exc:
        raise ValueError('no puedo leer la plantilla %s: %s' % (plantilla, exc.strerror or exc))
    except configparser.Error as exc:
        raise ValueError('plantilla %s inválida: %s' % (plantilla, str(exc).splitlines()[0]))
    for sec in ('sdr', 'search_params', 'web'):
        if not cp.has_section(sec):
            raise ValueError('la plantilla %s no tiene la sección [%s]' % (plantilla, sec))
    def get(k, d=''):
        return str(e.get(k, d)).strip()
    def flt(k, lo, hi, d):
        try:
            v = float(get(k, d))
        except ValueError:
            raise ValueError('%s no es numérico' % k)
        if not math.isfinite(v) or not lo <= v <= hi:
            raise ValueError('%s fuera de rango (%s..%s)' % (k, lo, hi))
        return v
    serie = get('SONDAS_SDR_SERIAL')
    if not re.match(r'^[A-Za-z0-9._-]{1,32}$', serie):
        raise ValueError('SONDAS_SDR_SERIAL vacío o inválido')
    fmin, fmax = flt('SONDAS_MIN_FREQ', *BANDA, '400.05'), flt('SONDAS_MAX_FREQ', *BANDA, '406.0')
    if fmin >= fmax:
        raise ValueError('SONDAS_MIN_FREQ debe ser menor que SONDAS_MAX_FREQ')
    fijas = []
    for f in [x for x in get('SONDAS_ALWAYS_SCAN', '403.4').split(',') if x.strip()]:
        try:
            v = float(f)
        except ValueError:
            raise ValueError('SONDAS_ALWAYS_SCAN: «%s» no es numérico' % f.strip())
        if not BANDA[0] <= v <= BANDA[1]:
            raise ValueError('SONDAS_ALWAYS_SCAN: %s fuera de la banda' % f.strip())
        fijas.append('%.3f' % v)
    ppm = int(flt('SONDAS_PPM', -200, 200, '0'))
    ganancia = flt('SONDAS_GAIN', -1, 50, '-1')
    lat, lon = flt('STATION_LAT', -90, 90, '0'), flt('STATION_LON', -180, 180, '0')
    alt = flt('STATION_ASL', -500, 9000, '0')
    indicativo = re.sub(r'[^A-Za-z0-9-]', '', get('CALLSIGN', 'BRICOHAMS'))[:20] or 'BRICOHAMS'
    subir = 'True' if get('SONDAS_SONDEHUB', 'no').lower() in ('yes', 'si', 'true', '1') else 'False'
    cambios = (
        ('sdr', {'sdr_type': 'RTLSDR', 'sdr_quantity': '1'}, True),
        ('sdr_1', {'device_idx': _ini(serie), 'ppm': '%d' % ppm, 'gain': '%g' % ganancia, 'bias': 'False'}, True),
        ('search_params', {'min_freq': '%.3f' % fmin, 'max_freq': '%.3f' % fmax,
                           'always_scan': '[%s]' % ', '.join(fijas), 'never_scan': '[]', 'only_scan': '[]',
                           'rx_timeout': '180'}, True),
        ('location', {'station_lat': '%.5f' % lat, 'station_lon': '%.5f' % lon, 'station_alt': '%.0f' % alt}, True),
        ('habitat', {'uploader_callsign': indicativo}, True),
        ('sondehub', {'sondehub_enabled': subir}, True),
        ('aprs', {'aprs_enabled': 'False'}, False),
        ('email', {'email_enabled': 'False'}, False),
        ('oziplotter', {'payload_summary_enabled': 'True', 'payload_summary_host': '127.0.0.1',
                        'payload_summary_port': '%d' % PUERTO_UDP}, True),
        ('web', {'web_host': '127.0.0.1', 'web_port': '5000', 'web_control': 'False'}, True))
    for sec, claves, crear in cambios:
        if not cp.has_section(sec):
            if not crear:
                continue
            cp.add_section(sec)
        for k, v in claves.items():
            cp.set(sec, k, v)
    salida = io.StringIO()
    salida.write('# Generado por bricohams-sondas --station-cfg (install.sh, paso sondas) a partir de la plantilla '
                 'oficial.\n# No editar a mano: se sobrescribe.\n')
    cp.write(salida)
    return salida.getvalue()


def servicio(cfg):
    from bricohams_mqtt import Publicador
    pub = None
    if cfg['mqtt']:
        pub = Publicador(cfg['mqtt_host'], cfg['mqtt_puerto'], 'bricohams-sondas', cfg['mqtt_user'], cfg['mqtt_pass'],
                         testamento=('%s/estado' % cfg['mqtt_tema'], 'offline', True))
    seg = Seguimiento(cfg['estado'], cfg['prediccion'], publicador=pub, tema=cfg['mqtt_tema'])
    seg.cargar()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('127.0.0.1', cfg['udp_puerto']))
    sock.settimeout(2)
    ultimo_doc = ultimo_pub = 0.0
    en_linea = False
    while True:
        ahora = time.time()
        try:
            crudo, _ = sock.recvfrom(MAX_PAQUETE + 1)
            s = seg.procesar(crudo)
            if s is not None and pub is not None:
                try:
                    seg.publicar_telemetria(s)
                except Exception as exc:
                    print('MQTT: %s' % exc, file=sys.stderr)
        except socket.timeout:
            pass
        except OSError as exc:
            print('UDP: %s' % exc, file=sys.stderr)
            time.sleep(1)
        ahora = time.time()
        if ahora - ultimo_doc >= 2:
            ultimo_doc = ahora
            try:
                seg.expirar(ahora)
                seg.actualizar_predicciones(ahora)
                if pub is not None:
                    if not en_linea and pub.conectar():
                        pub.publicar('%s/estado' % cfg['mqtt_tema'], 'online', True)
                        en_linea = True
                    elif en_linea and pub.sock is None:
                        en_linea = False
                    if ahora - ultimo_pub >= 30:
                        ultimo_pub = ahora
                        pub.latido()
                escribir_atomico(cfg['salida'], seg.documento(mqtt_publico(cfg, en_linea), ahora))
                seg.guardar()
            except Exception as exc:                    # nunca caer por disco/broker: se reintenta en 2 s
                print('ciclo: %s' % exc, file=sys.stderr)


def main(argv):
    if len(argv) >= 2 and argv[1] == '--paquete':
        crudo = argv[2] if len(argv) > 2 else sys.stdin.read()
        p, motivo = validar_paquete(crudo)
        print(json.dumps(p if p is not None else {'rechazado': motivo}, ensure_ascii=False))
        return 0 if p is not None else 1
    if len(argv) >= 2 and argv[1] == '--station-cfg':
        if len(argv) < 3:
            print('ERROR: uso: bricohams-sondas --station-cfg PLANTILLA (station.cfg.example de auto_rx)',
                  file=sys.stderr)
            return 2
        try:
            sys.stdout.write(generar_station_cfg(argv[2]))
        except ValueError as exc:
            print('ERROR: %s' % exc, file=sys.stderr)
            return 2
        return 0
    servicio(cfg_desde_env())
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
