#!/usr/bin/env python3
# =====================================================================
#  bricohams-satpass · EA5KAO · BricoHams  (v4)
#  Calcula los próximos pases de los satélites de data/satelites.json sobre
#  la estación y los deja en la web (plugins/receiver/satelites/pases.json)
#  para el aviso «próximo pase» y el botón ▶ Escuchar (que cambia de perfil,
#  sintoniza y arranca el seguimiento Doppler).
#   - Elementos orbitales: CelesTrak (GP en JSON/OMM), una vez cada 12 h,
#     con copia en /var/lib/bricohams/tle.json por si no hay Internet.
#   - Propagación SGP4 (python3-sgp4) y paso TEME→tierra con GMST.
#  Uso: bricohams-satpass            (lo lanza un temporizador cada 15 min)
#       bricohams-satpass --ver      (muestra los pases de las próximas 24 h)
# =====================================================================
import json
import math
import os
import sys
import tempfile
import time
import urllib.request
from datetime import datetime, timezone

try:
    from sgp4.api import Satrec, jday
    from sgp4 import omm as sgp4_omm
except ImportError:
    Satrec = None

KIT = os.environ.get('KIT_DIR', '/opt/bricohams/kit')
LISTA = os.environ.get('SAT_LIST', os.path.join(KIT, 'data', 'satelites.json'))
SALIDA = os.environ.get('SAT_OUT', '/usr/lib/python3/dist-packages/htdocs/plugins/receiver/satelites/pases.json')
CACHE = os.path.join(os.environ.get('STATE_DIRECTORY', '/var/lib/bricohams'), 'tle.json')
CELESTRAK = 'https://celestrak.org/NORAD/elements/gp.php?CATNR={}&FORMAT=JSON'

A_WGS = 6378.137
F_WGS = 1 / 298.257223563


def gmst(jd_ut1):
    """Tiempo sidéreo medio de Greenwich (rad), IAU-82."""
    t = (jd_ut1 - 2451545.0) / 36525.0
    s = 67310.54841 + (876600.0 * 3600 + 8640184.812866) * t + 0.093104 * t * t - 6.2e-6 * t ** 3
    return math.radians((s % 86400) / 240.0) % (2 * math.pi)


def ecef_observador(lat, lon, alt_m):
    la, lo = math.radians(lat), math.radians(lon)
    e2 = F_WGS * (2 - F_WGS)
    n = A_WGS / math.sqrt(1 - e2 * math.sin(la) ** 2)
    h = alt_m / 1000.0
    return ((n + h) * math.cos(la) * math.cos(lo), (n + h) * math.cos(la) * math.sin(lo), (n * (1 - e2) + h) * math.sin(la))


def az_el(r_teme, jd, lat, lon, obs):
    """Azimut y elevación (grados) de una posición TEME (km)."""
    g = gmst(jd)
    x, y, z = r_teme
    xe = x * math.cos(g) + y * math.sin(g)
    ye = -x * math.sin(g) + y * math.cos(g)
    dx, dy, dz = xe - obs[0], ye - obs[1], z - obs[2]
    la, lo = math.radians(lat), math.radians(lon)
    e = -math.sin(lo) * dx + math.cos(lo) * dy
    n = -math.sin(la) * math.cos(lo) * dx - math.sin(la) * math.sin(lo) * dy + math.cos(la) * dz
    u = math.cos(la) * math.cos(lo) * dx + math.cos(la) * math.sin(lo) * dy + math.sin(la) * dz
    el = math.degrees(math.atan2(u, math.hypot(e, n)))
    az = (math.degrees(math.atan2(e, n)) + 360) % 360
    return az, el


def satrec_de_omm(o):
    s = Satrec()
    sgp4_omm.initialize(s, {k: str(v) for k, v in o.items()})
    return s


def posicion(sat, ts):
    jd, fr = jday(*time.gmtime(ts)[:5], time.gmtime(ts)[5] + ts % 1)
    e, r, v = sat.sgp4(jd, fr)
    return (None if e else r), jd + fr


def pases(sat, lat, lon, alt_m, desde, horas=24, paso=30, min_el=10):
    obs = ecef_observador(lat, lon, alt_m)

    def elev(t):
        r, jd = posicion(sat, t)
        return az_el(r, jd, lat, lon, obs) if r else (0, -90)

    def cruce(t0, t1, subiendo):
        for _ in range(20):                       # bisección: ~0,03 s
            m = (t0 + t1) / 2
            if (elev(m)[1] > 0) == subiendo:
                t1 = m
            else:
                t0 = m
        return (t0 + t1) / 2

    out = []
    t, fin = desde, desde + horas * 3600
    prev = elev(t)[1]
    aos = None if prev <= 0 else desde
    maxel, tmax = (prev, t) if prev > 0 else (-90, None)
    while t < fin:
        t2 = t + paso
        az2, el2 = elev(t2)
        if prev <= 0 < el2:
            aos, maxel, tmax = cruce(t, t2, True), el2, t2
        elif aos is not None and el2 > maxel:
            maxel, tmax = el2, t2
        if aos is not None and prev > 0 >= el2:
            los = cruce(t, t2, False)
            if maxel >= min_el:
                out.append({'aos': round(aos), 'los': round(los), 'max_el': round(maxel, 1), 't_max': round(tmax),
                            'az_aos': round(elev(aos + 1)[0]), 'az_los': round(elev(los - 1)[0]),
                            'duracion_s': round(los - aos)})
            aos = None
        prev, t = el2, t2
    if aos is not None and maxel >= min_el:          # pase en curso al final de la ventana
        out.append({'aos': round(aos), 'los': round(fin), 'max_el': round(maxel, 1), 't_max': round(tmax),
                    'az_aos': round(elev(aos + 1)[0]), 'az_los': None, 'duracion_s': round(fin - aos)})
    return out


def descargar_omm(noradas, cache=CACHE, max_edad=12 * 3600):
    try:
        datos = json.load(open(cache))
    except (OSError, ValueError):
        datos = {}
    ahora = time.time()
    for n in noradas:
        e = datos.get(str(n))
        if e and ahora - e.get('t', 0) < max_edad:
            continue
        try:
            req = urllib.request.Request(CELESTRAK.format(n), headers={'User-Agent': 'BricoHams-SDR EA5KAO'})
            j = json.load(urllib.request.urlopen(req, timeout=20))
            if j:
                datos[str(n)] = {'t': ahora, 'omm': j[0]}
        except Exception as ex:
            print('satpass: CelesTrak %s: %s (uso la copia)' % (n, ex), file=sys.stderr)
    try:
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        json.dump(datos, open(cache, 'w'))
    except OSError:
        pass
    return {int(k): v['omm'] for k, v in datos.items()}


def calcular(lista, omms, lat, lon, alt, ahora=None, horas=24):
    ahora = ahora or time.time()
    todos = []
    for s in lista:
        o = omms.get(s['norad'])
        if not o:
            continue
        try:
            sat = satrec_de_omm(o)
        except Exception as e:
            print('satpass: %s: %s' % (s['nombre'], e), file=sys.stderr)
            continue
        for p in pases(sat, lat, lon, alt, ahora - 900, horas=horas, min_el=s.get('min_el', 10)):
            if p['los'] < ahora:
                continue
            p.update({'nombre': s['nombre'], 'norad': s['norad'], 'hz': int(round(s['mhz'] * 1e6)),
                      'modo': s['modo'], 'perfil': s['perfil'], 'nota': s.get('nota', ''), 'omm': o})
            todos.append(p)
    todos.sort(key=lambda p: p['aos'])
    return todos


def write_atomic(path, obj):
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix='.pases-')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False)
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


def main():
    if Satrec is None:
        print('satpass: falta python3-sgp4', file=sys.stderr)
        return 1
    lat = float(os.environ.get('STATION_LAT', '0.0'))
    lon = float(os.environ.get('STATION_LON', '0.0'))
    alt = float(os.environ.get('STATION_ASL', '200'))
    lista = json.load(open(LISTA, encoding='utf-8'))['satelites']
    omms = descargar_omm([s['norad'] for s in lista])
    p = calcular(lista, omms, lat, lon, alt)
    if '--ver' in sys.argv:
        for x in p:
            print('%s  %-18s máx %4.1f°  %3d min  AOS %3s° → LOS %3s°  %.3f MHz %s' % (
                datetime.fromtimestamp(x['aos']).strftime('%d/%m %H:%M'), x['nombre'], x['max_el'],
                x['duracion_s'] // 60, x['az_aos'], x['az_los'], x['hz'] / 1e6, x['modo']))
        return 0
    write_atomic(SALIDA, {'actualizado': datetime.now(timezone.utc).isoformat(timespec='seconds'),
                          'qth': {'lat': round(lat, 2), 'lon': round(lon, 2), 'asl': alt},   # v4.4: público, ~1 km
                          'pases': p[:40]})
    print('satpass: %d pases en las próximas 24 h' % len(p))
    return 0


if __name__ == '__main__':
    sys.exit(main())
