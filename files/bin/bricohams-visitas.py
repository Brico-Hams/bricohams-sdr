#!/usr/bin/env python3
# =====================================================================
#  bricohams-visitas · EA5KAO · BricoHams  (v4)
#  Quién se conecta al SDR y desde dónde, con aviso por Telegram.
#   - OpenWebRX+ publica por MQTT (mosquitto local, tema openwebrx/CLIENT)
#     cada conexión/desconexión con la IP del oyente (detrás de nginx, la
#     de X-Forwarded-For) y los mensajes del chat.
#   - La IP se localiza con una base GeoIP LOCAL (DB-IP City Lite, CC BY 4.0,
#     se descarga cada mes); no se manda a ningún servicio externo.
#   - Se guarda país, ciudad e IP PARCIAL (83.45.x.x). La IP completa no se
#     escribe en disco (decisión del usuario, RGPD: minimización).
#   - Telegram: aviso de cada conexión (como mucho 1 por IP cada 10 min),
#     chat opcional y resumen diario (--resumen).
#   - Web: plugins/receiver/visitas/visitas.json (solo totales y países).
#  Uso: bricohams-visitas              (servicio)
#       bricohams-visitas --resumen    (manda el resumen del día a Telegram)
#       bricohams-visitas --estado     (muestra los datos)
#       bricohams-visitas --geoip      (descarga la base GeoIP del mes)
# =====================================================================
import gzip
import ipaddress
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

try:
    import maxminddb  # python3-maxminddb
except ImportError:
    maxminddb = None

ESTADO = os.environ.get('STATE_DIRECTORY', '/var/lib/bricohams')
DB = os.path.join(ESTADO, 'visitas.sqlite')
GEO = os.path.join(ESTADO, 'dbip-city-lite.mmdb')
WEB = os.environ.get('VISITAS_OUT', '/usr/lib/python3/dist-packages/htdocs/plugins/receiver/visitas/visitas.json')
DIAS = int(os.environ.get('VISITAS_DIAS', '90'))

PAISES = {'ES': 'España', 'PT': 'Portugal', 'FR': 'Francia', 'IT': 'Italia', 'DE': 'Alemania', 'GB': 'Reino Unido',
          'US': 'Estados Unidos', 'NL': 'Países Bajos', 'BE': 'Bélgica', 'CH': 'Suiza', 'AR': 'Argentina', 'MX': 'México',
          'CU': 'Cuba', 'VE': 'Venezuela', 'CO': 'Colombia', 'CL': 'Chile', 'MA': 'Marruecos', 'AD': 'Andorra'}


def env(k, d=''):
    return os.environ.get(k, d).strip()


def si(v):
    return str(v).strip().lower() in ('1', 'yes', 'si', 'sí', 'true', 'on')


def ip_parcial(ip):
    """83.45.12.7 -> 83.45.x.x · 2a01:4f8:1:2::3 -> 2a01:4f8:…"""
    try:
        a = ipaddress.ip_address(ip)
    except ValueError:
        return '?'
    if a.version == 4:
        p = str(a).split('.')
        return '%s.%s.x.x' % (p[0], p[1])
    g = a.exploded.split(':')
    return '%s:%s:…' % (g[0].lstrip('0') or '0', g[1].lstrip('0') or '0')


def bandera(cc):
    if not cc or len(cc) != 2 or not cc.isalpha():
        return '🏳️'
    return ''.join(chr(0x1F1E6 + ord(c) - 65) for c in cc.upper())


class Geo:
    def __init__(self, ruta=GEO):
        self.r = None
        if maxminddb and os.path.exists(ruta):
            try:
                self.r = maxminddb.open_database(ruta)
            except Exception as e:
                print('visitas: GeoIP: %s' % e, file=sys.stderr)

    def buscar(self, ip):
        try:
            a = ipaddress.ip_address(ip)
        except ValueError:
            return {'cc': '', 'pais': '?', 'ciudad': ''}
        if a.is_private or a.is_loopback:
            return {'cc': 'LAN', 'pais': 'Red local', 'ciudad': ''}
        if not self.r:
            return {'cc': '', 'pais': '?', 'ciudad': ''}
        try:
            d = self.r.get(ip) or {}
        except Exception:
            d = {}
        cc = (d.get('country') or {}).get('iso_code', '') or ''
        nom = (d.get('country') or {}).get('names', {})
        ciu = (d.get('city') or {}).get('names', {})
        return {'cc': cc, 'pais': PAISES.get(cc) or nom.get('es') or nom.get('en') or cc,
                'ciudad': ciu.get('es') or ciu.get('en') or ''}


def abrir_db(ruta=DB):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    c = sqlite3.connect(ruta, check_same_thread=False)
    c.execute('CREATE TABLE IF NOT EXISTS visitas (ts REAL, fin REAL, ip TEXT, cc TEXT, pais TEXT, ciudad TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS diario (dia TEXT, cc TEXT, n INTEGER, PRIMARY KEY (dia, cc))')
    c.commit()
    return c


class Visitas:
    def __init__(self, db, geo, telegram=None, ahora=time.time):
        self.db, self.geo, self.tg, self.ahora = db, geo, telegram, ahora
        self.activas = {}            # clave interna (ip completa, solo en memoria) -> fila
        self.ultimo_aviso = {}
        self.clientes = 0
        self.lock = threading.Lock()

    def evento(self, m):
        estado, ip = m.get('state'), m.get('ip', '')
        if 'clients' in m:
            self.clientes = int(m.get('clients') or 0)
        if estado == 'Connected':
            return self.conectado(ip)
        if estado == 'Disconnected':
            return self.desconectado(ip)
        if estado == 'ChatMessage' and self.tg and si(env('VISITAS_CHAT', 'yes')):
            self.tg('💬 <b>%s</b>: %s' % (esc(m.get('name', '?')), esc(m.get('message', ''))))
        return None

    def conectado(self, ip):
        t = self.ahora()
        g = self.geo.buscar(ip)
        fila = {'ts': t, 'ip': ip_parcial(ip), **g}
        with self.lock:
            self.activas.setdefault(ip, []).append(fila)
            cur = self.db.execute('INSERT INTO visitas (ts, fin, ip, cc, pais, ciudad) VALUES (?,?,?,?,?,?)',
                                  (t, None, fila['ip'], g['cc'], g['pais'], g['ciudad']))
            fila['rowid'] = cur.lastrowid
            dia = datetime.fromtimestamp(t).strftime('%Y-%m-%d')
            self.db.execute('INSERT INTO diario (dia, cc, n) VALUES (?,?,1) ON CONFLICT(dia, cc) DO UPDATE SET n = n + 1',
                            (dia, g['cc'] or '??'))
            self.db.commit()
        avisar = self.tg and (g['cc'] != 'LAN' or si(env('VISITAS_AVISAR_LAN', 'no')))
        if avisar and t - self.ultimo_aviso.get(ip, 0) > 600:
            self.ultimo_aviso[ip] = t
            donde = ', '.join(x for x in (g['ciudad'], g['pais']) if x)
            self.tg('🟢 <b>Nuevo oyente</b> %s %s · <code>%s</code> · %d conectado%s' % (
                bandera(g['cc']) if g['cc'] != 'LAN' else '🏠', esc(donde or '?'), fila['ip'],
                self.clientes, '' if self.clientes == 1 else 's'))
        return fila

    def desconectado(self, ip):
        t = self.ahora()
        with self.lock:
            lst = self.activas.get(ip) or []
            if not lst:
                return None
            fila = lst.pop(0)
            if not lst:
                self.activas.pop(ip, None)
            self.db.execute('UPDATE visitas SET fin = ? WHERE rowid = ?', (t, fila['rowid']))
            self.db.commit()
        if self.tg and si(env('VISITAS_AVISAR_DESCONEXION', 'no')) and fila['cc'] != 'LAN':
            self.tg('🔴 Se va %s %s · %d min' % (bandera(fila['cc']), esc(fila['pais']), round((t - fila['ts']) / 60)))
        return fila

    def resumen(self, ahora=None):
        ahora = ahora or self.ahora()
        hoy = datetime.fromtimestamp(ahora).strftime('%Y-%m-%d')
        hace30 = (datetime.fromtimestamp(ahora) - timedelta(days=30)).strftime('%Y-%m-%d')
        q = self.db.execute
        total = q('SELECT COALESCE(SUM(n),0) FROM diario').fetchone()[0]
        n_hoy = q('SELECT COALESCE(SUM(n),0) FROM diario WHERE dia = ?', (hoy,)).fetchone()[0]
        paises = [{'cc': cc, 'pais': PAISES.get(cc, cc), 'n': n} for cc, n in
                  q('SELECT cc, SUM(n) s FROM diario WHERE dia >= ? GROUP BY cc ORDER BY s DESC', (hace30,)).fetchall()]
        with self.lock:
            ahora_cc = sorted({f['cc'] for l in self.activas.values() for f in l if f['cc'] not in ('', 'LAN')})
            activos = sum(len(l) for l in self.activas.values())
        return {'actualizado': datetime.fromtimestamp(ahora).isoformat(timespec='seconds'),
                'ahora': max(self.clientes, activos) if self.clientes else activos,
                'paises_ahora': ahora_cc, 'hoy': n_hoy, 'total': total, 'paises_30d': paises}

    def limpiar(self, dias=DIAS):
        lim = self.ahora() - dias * 86400
        self.db.execute('DELETE FROM visitas WHERE ts < ?', (lim,))
        self.db.commit()


def esc(t):
    return str(t).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def telegram_envio():
    tok, chat = env('TELEGRAM_TOKEN'), env('TELEGRAM_CHAT_ID')
    if not tok or not chat:
        return None

    def enviar(texto):
        def _t():
            try:
                datos = urllib.parse.urlencode({'chat_id': chat, 'text': texto, 'parse_mode': 'HTML',
                                                'disable_web_page_preview': 'true'}).encode()
                urllib.request.urlopen('https://api.telegram.org/bot%s/sendMessage' % tok, datos, timeout=15).read()
            except Exception as e:
                print('visitas: Telegram: %s' % e, file=sys.stderr)
        threading.Thread(target=_t, daemon=True).start()
    return enviar


def write_atomic(path, obj):
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix='.visitas-')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False)
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


def descargar_geoip(destino=GEO):
    mes = datetime.now().strftime('%Y-%m')
    url = 'https://download.db-ip.com/free/dbip-city-lite-%s.mmdb.gz' % mes
    tmp = destino + '.gz.tmp'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'BricoHams-SDR EA5KAO'})
        with urllib.request.urlopen(req, timeout=120) as r, open(tmp, 'wb') as f:
            shutil.copyfileobj(r, f)
        with gzip.open(tmp) as g, open(destino + '.tmp', 'wb') as f:
            shutil.copyfileobj(g, f)
        os.replace(destino + '.tmp', destino)
        print('visitas: GeoIP %s descargada (DB-IP City Lite, CC BY 4.0)' % mes)
        return 0
    except Exception as e:
        print('visitas: no pude descargar %s: %s' % (url, e), file=sys.stderr)
        return 1
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def servicio():
    try:
        import paho.mqtt.client as mqtt  # python3-paho-mqtt
    except ImportError:
        print('visitas: falta python3-paho-mqtt', file=sys.stderr)
        return 1
    v = Visitas(abrir_db(), Geo(), telegram_envio())
    tema = env('MQTT_TOPIC', 'openwebrx') + '/CLIENT'

    def on_connect(c, u, f, rc, *a):
        c.subscribe(tema)
        print('visitas: escuchando %s' % tema, flush=True)

    def on_message(c, u, msg):
        try:
            v.evento(json.loads(msg.payload.decode('utf-8', 'replace')))
            write_atomic(WEB, v.resumen())
        except Exception as e:
            print('visitas: %s' % e, file=sys.stderr, flush=True)

    try:
        c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id='bricohams-visitas')
    except AttributeError:                         # paho-mqtt 1.x
        c = mqtt.Client(client_id='bricohams-visitas')
    c.on_connect, c.on_message = on_connect, on_message
    c.connect_async(env('MQTT_HOST', 'localhost'), int(env('MQTT_PORT', '1883')))
    c.loop_start()
    while True:
        write_atomic(WEB, v.resumen())
        v.limpiar()
        time.sleep(300)


def main(argv):
    if '--geoip' in argv:
        return descargar_geoip()
    if '--resumen' in argv or '--estado' in argv:
        v = Visitas(abrir_db(), Geo())
        r = v.resumen()
        if '--estado' in argv:
            print(json.dumps(r, indent=1, ensure_ascii=False))
            return 0
        tg = telegram_envio()
        top = ' '.join('%s%d' % (bandera(p['cc']), p['n']) for p in r['paises_30d'][:10])
        if tg:
            tg('📊 <b>BricoHams SDR · resumen</b>\nHoy: <b>%d</b> visitas · total %d\n30 días: %s' % (r['hoy'], r['total'], top))
            time.sleep(5)
        return 0
    return servicio()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
