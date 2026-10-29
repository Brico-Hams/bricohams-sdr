#!/usr/bin/env python3
# =====================================================================
#  bricohams-meteo · BricoHams
#  Tiempo en vivo de las estaciones cercanas para el plugin "meteo".
#
#  - Observación horaria de las estaciones AEMET de METEO_STATIONS
#    (necesita AEMET_API_KEY, gratis en opendata.aemet.es).
#  - Tiempo actual del modelo y previsión de 3 días de Open-Meteo
#    (sin clave) para el QTH.
#  Escribe METEO_OUT (JSON) de forma atómica. Lo lanza el timer
#  bricohams-meteo.timer cada 10 minutos.
#
#  Variables (en /etc/bricohams/meteo.env):
#    AEMET_API_KEY, METEO_STATIONS="7158X:Archena,7237E:Molina de Segura",
#    STATION_LAT, STATION_LON, METEO_OUT
# =====================================================================
import json
import math
import os
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

UA = 'bricohams-meteo/1.0 (+https://t.me/bricohams)'
AEMET = 'https://opendata.aemet.es/opendata/api/observacion/convencional/datos/estacion/'
OPENMETEO = 'https://api.open-meteo.com/v1/forecast'


def env(name, default=''):
    return os.environ.get(name, default).strip()


def http_get(url, headers=None, timeout=25):
    req = urllib.request.Request(url, headers=dict({'User-Agent': UA, 'Accept': 'application/json'}, **(headers or {})))
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    # AEMET sirve algunos ficheros en ISO-8859-15
    for enc in ('utf-8', 'iso-8859-15'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode('utf-8', 'replace')


def haversine(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def fnum(v):
    try:
        f = float(v)
        return f if math.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def iso_aemet(fint):
    # "2026-10-04T06:00:00+0000" o "2026-10-04T06:00:00"
    s = (fint or '').replace('+0000', '+00:00')
    try:
        d = datetime.fromisoformat(s)
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


def parse_aemet(rows, sid, name, qlat, qlon):
    """Convierte la lista horaria de AEMET en el resumen que usa el plugin."""
    rows = sorted([r for r in rows if r.get('fint')], key=lambda r: r['fint'])
    if not rows:
        raise ValueError('sin observaciones')
    last = rows[-1]
    st = {
        'id': sid, 'name': name or last.get('ubi', sid).title(), 'source': 'AEMET',
        'lat': fnum(last.get('lat')), 'lon': fnum(last.get('lon')), 'alt': fnum(last.get('alt')),
        'time': iso_aemet(last.get('fint')),
        'ta': fnum(last.get('ta')), 'hr': fnum(last.get('hr')),
        'pres': fnum(last.get('pres')), 'pres_nmar': fnum(last.get('pres_nmar')),
        'dv': fnum(last.get('dv')),
        'vv_kmh': None, 'vmax_kmh': None,
        'prec_1h': fnum(last.get('prec')),
    }
    vv, vmax = fnum(last.get('vv')), fnum(last.get('vmax'))
    st['vv_kmh'] = round(vv * 3.6, 1) if vv is not None else None
    st['vmax_kmh'] = round(vmax * 3.6, 1) if vmax is not None else None
    # máx/mín y lluvia de las últimas 24 h
    tmax = [fnum(r.get('tamax')) for r in rows] + [fnum(r.get('ta')) for r in rows]
    tmin = [fnum(r.get('tamin')) for r in rows] + [fnum(r.get('ta')) for r in rows]
    tmax = [x for x in tmax if x is not None]
    tmin = [x for x in tmin if x is not None]
    st['tamax'] = max(tmax) if tmax else None
    st['tamin'] = min(tmin) if tmin else None
    precs = [fnum(r.get('prec')) for r in rows[-24:]]
    precs = [x for x in precs if x is not None]
    st['prec_24h'] = round(sum(precs), 1) if precs else None
    st['history'] = [{'t': iso_aemet(r.get('fint')), 'ta': fnum(r.get('ta')), 'hr': fnum(r.get('hr'))} for r in rows[-24:]]
    if st['lat'] is not None and st['lon'] is not None:
        st['dist_km'] = round(haversine(qlat, qlon, st['lat'], st['lon']), 1)
    return st


def fetch_aemet(sid, key):
    meta = json.loads(http_get(AEMET + urllib.parse.quote(sid), headers={'api_key': key}))
    if int(meta.get('estado', 0)) != 200 or not meta.get('datos'):
        raise RuntimeError('AEMET %s: %s' % (meta.get('estado'), meta.get('descripcion', 'sin datos')))
    return json.loads(http_get(meta['datos']))


def fetch_openmeteo(lat, lon):
    q = {
        'latitude': '%.4f' % lat, 'longitude': '%.4f' % lon, 'timezone': 'Europe/Madrid',
        'wind_speed_unit': 'kmh', 'forecast_days': 3,
        'current': ','.join(['temperature_2m', 'relative_humidity_2m', 'apparent_temperature', 'pressure_msl',
                             'wind_speed_10m', 'wind_direction_10m', 'wind_gusts_10m', 'precipitation',
                             'weather_code', 'cloud_cover', 'is_day']),
        'daily': ','.join(['weather_code', 'temperature_2m_max', 'temperature_2m_min',
                           'precipitation_probability_max', 'sunrise', 'sunset']),
    }
    d = json.loads(http_get(OPENMETEO + '?' + urllib.parse.urlencode(q)))
    daily = []
    dd = d.get('daily', {})
    for i, day in enumerate(dd.get('time', [])):
        def g(k):
            v = dd.get(k, [])
            return v[i] if i < len(v) else None
        daily.append({'date': day, 'weather_code': g('weather_code'), 'tmax': g('temperature_2m_max'),
                      'tmin': g('temperature_2m_min'), 'precip_prob': g('precipitation_probability_max'),
                      'sunrise': g('sunrise'), 'sunset': g('sunset')})
    return {'source': 'Open-Meteo', 'current': d.get('current', {}), 'daily': daily}


def parse_stations(spec):
    out = []
    for part in spec.split(','):
        part = part.strip()
        if not part:
            continue
        sid, _, name = part.partition(':')
        out.append((sid.strip(), name.strip()))
    return out


def write_atomic(path, obj):
    d = os.path.dirname(path) or '.'
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.meteo-', dir=d)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


def main():
    lat = float(env('STATION_LAT', '0'))
    lon = float(env('STATION_LON', '0'))
    out = env('METEO_OUT', '/usr/lib/python3/dist-packages/htdocs/plugins/receiver/meteo/meteo.json')
    key = env('AEMET_API_KEY')
    stations = parse_stations(env('METEO_STATIONS', '7158X:Archena,7237E:Molina de Segura,7228:Alcantarilla Base Aérea,7178I:Murcia'))
    res = {'updated': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
           'qth': {'lat': round(lat, 2), 'lon': round(lon, 2)},   # v4.4: es público (~1 km), no la casa exacta
           'stations': [], 'model': None, 'errors': []}

    # meteo.json es público: ni rutas, ni nombres de variables, ni texto de excepciones.
    # El detalle va al journal (journalctl -u bricohams-meteo).
    if not key and stations:
        print('meteo: sin AEMET_API_KEY en la configuración; solo modelo Open-Meteo', file=sys.stderr)
    for sid, name in stations:
        if not key:
            res['stations'].append({'id': sid, 'name': name or sid, 'source': 'AEMET',
                                    'error': 'Observación no disponible'})
            continue
        try:
            res['stations'].append(parse_aemet(fetch_aemet(sid, key), sid, name, lat, lon))
        except Exception as e:  # una estación caída no para las demás
            print('meteo: AEMET %s: %s' % (sid, str(e)[:200]), file=sys.stderr)
            res['stations'].append({'id': sid, 'name': name or sid, 'source': 'AEMET', 'error': 'Sin datos ahora'})
            res['errors'].append('AEMET %s sin datos' % sid)
        time.sleep(1)  # AEMET limita peticiones seguidas
    res['stations'].sort(key=lambda s: s.get('dist_km', 999))

    try:
        res['model'] = fetch_openmeteo(lat, lon)
    except Exception as e:
        print('meteo: Open-Meteo: %s' % str(e)[:200], file=sys.stderr)
        res['errors'].append('Modelo Open-Meteo sin datos')

    write_atomic(out, res)
    ok = sum(1 for s in res['stations'] if 'ta' in s)
    print('meteo: %d/%d estaciones, modelo %s -> %s' % (ok, len(stations), 'ok' if res['model'] else 'NO', out))
    if not key and stations:   # v5.0: que no pase en silencio (systemctl --failed / bricohams-check)
        print('meteo: ERROR falta la clave de AEMET; reinstala con: sudo bash install.sh --solo meteo', file=sys.stderr)
        return 2
    return 0 if (ok or res['model']) else 1


if __name__ == '__main__':
    sys.exit(main())
