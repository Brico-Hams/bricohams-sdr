#!/usr/bin/env python3
"""v4.3 · Datos de zona que se bajan EN LA PI al instalar (cambian a menudo, no van en el kit):

  aemet   lista completa de estaciones de observación de AEMET con sus coordenadas exactas
          (OpenData, /observacion/convencional/todas; necesita AEMET_API_KEY, la misma de la meteo)
  fmdx    emisoras de FM (regionales, locales y nacionales) alrededor de la estación, del servicio
          público de maps.fmdx.org (datos de FMLIST), el mismo que usa FM-DX Webserver

Se guardan en una caché (/var/lib/bricohams/locator/{aemet,fmdx}.json) que se reutiliza 30 días
o si no hay red; así la instalación nunca se para por esto.

Uso:
  bricohams_locator_online.py refrescar --cache DIR --lat 37.98 --lon -1.13 [--fuentes aemet,fmdx] [--forzar]
  bricohams_locator_online.py ver --cache DIR
La clave de AEMET se lee de la variable de entorno AEMET_API_KEY (nunca de la línea de órdenes).
"""
import argparse
import json
import math
import os
import re
import sys
import tempfile
import time
import urllib.request

AEMET_TODAS = 'https://opendata.aemet.es/opendata/api/observacion/convencional/todas'
FMDX = 'https://maps.fmdx.org/api?qth=%.4f,%.4f'
AGENTE = 'BricoHams-SDR/4.3 (+https://t.me/bricohams)'
MAX_DIAS = 30
DISTANCIA_CACHE_KM = 25         # la caché de FM vale si la estación no se ha movido más que esto

# Para clasificar las emisoras de FM por su nombre (regional / nacional / local)
REGIONALES = [
    'À Punt', 'A Punt', 'Onda Regional', 'Canal Sur', 'Canal Fiesta', 'Catalunya Ràdio', 'Catalunya Radio',
    'Catalunya Informació', 'Catalunya Música', 'iCat', 'Radio Euskadi', 'Euskadi Irratia', 'Radio Vitoria',
    'Gaztea', 'EITB', 'Radio Galega', 'Aragón Radio', 'Aragon Radio', 'Radio Castilla-La Mancha',
    'Castilla-La Mancha Radio', 'CMM', 'Onda Madrid', 'Canarias Radio', 'IB3', 'RTPA', 'Radio del Principado',
    'Canal Extremadura', 'Radio Televisión Canaria', 'Ràdio Andorra', 'Radio Andorra',
]
NACIONALES = [
    'RNE', 'Radio Nacional', 'Radio Clásica', 'Radio Clasica', 'Radio 3', 'Radio 5', 'Cadena SER', 'SER ',
    'Los 40', 'LOS40', 'Cadena Dial', 'COPE', 'Cadena 100', 'Rock FM', 'Megastar', 'MegaStar', 'Onda Cero',
    'Europa FM', 'Melodía', 'Melodia', 'Kiss FM', 'Hit FM', 'Radio Marca', 'Radio María', 'Radio Maria',
    'esRadio', 'Radiolé', 'Radiole', 'Flaix', 'RAC1', 'RAC 1', 'RAC105', 'Loca FM', 'Vaughan',
    'Libertad FM', 'Cope', 'Radio Nacional de España', 'Radio Exterior', 'Ser ', 'Dial ', 'Los40',
]


def distancia_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0088 * math.asin(min(1, math.sqrt(h)))


def http_json(url, headers=None, timeout=40):
    """GET → JSON. Se sustituye en las pruebas."""
    h = {'User-Agent': AGENTE, 'Accept': 'application/json'}
    h.update(headers or {})
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
        datos = r.read()
    try:
        return json.loads(datos.decode('utf-8'))
    except UnicodeDecodeError:
        return json.loads(datos.decode('latin-1'))        # AEMET sirve los «datos» en ISO-8859-15


def ambito(nombre):
    n = ' %s ' % nombre
    if any(r.lower() in n.lower() for r in REGIONALES):
        return 'regional'
    if any(re.search(r'(^|\W)%s(\W|$)' % re.escape(x.strip()), n, re.I) for x in NACIONALES):
        return 'nacional'
    return 'local'


# --------------------------------------------------------------------- AEMET
def aemet_estaciones(clave):
    """[records weather] con todas las estaciones que dan observación ahora mismo."""
    if not clave:
        raise ValueError('falta AEMET_API_KEY')
    r = http_json(AEMET_TODAS, {'api_key': clave})
    if not isinstance(r, dict) or r.get('estado') != 200 or not r.get('datos'):
        raise ValueError('AEMET: %s' % (r.get('descripcion') if isinstance(r, dict) else r))
    filas = http_json(r['datos'])
    vistas = {}
    for f in filas if isinstance(filas, list) else []:
        try:
            idema = str(f['idema']).strip()
            lat, lon = float(f['lat']), float(f['lon'])
        except (KeyError, TypeError, ValueError):
            continue
        if not idema or not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue
        vistas[idema] = {'category': 'weather', 'site_id': 'AEMET-' + idema, 'station_id': idema,
                         'name': ' '.join(str(f.get('ubi') or idema).split()).title(),
                         'lat': round(lat, 5), 'lon': round(lon, 5), 'alt': f.get('alt'),
                         'source': 'AEMET OpenData (lista en vivo)'}
    if not vistas:
        raise ValueError('AEMET no ha devuelto estaciones')
    return [vistas[k] for k in sorted(vistas)]


# --------------------------------------------------------------------- FM (maps.fmdx.org)
def _freq_hz(v):
    f = float(str(v).replace(',', '.'))
    if 64 <= f <= 108.1:            # MHz
        return int(round(f * 1e6))
    if 64e6 <= f <= 108.1e6:         # ya en Hz
        return int(round(f))
    raise ValueError('frecuencia FM fuera de banda: %s' % v)


def fmdx_radios(datos, lat, lon, radio_km, itus=('E',)):
    """Convierte la respuesta de maps.fmdx.org en records «radio» dentro de radio_km."""
    locs = datos.get('locations') if isinstance(datos, dict) else None
    if isinstance(locs, dict):
        locs = list(locs.items())
    elif isinstance(locs, list):
        locs = [(str(l.get('id', i)), l) for i, l in enumerate(locs)]
    else:
        raise ValueError('respuesta de fmdx sin «locations»')
    out = []
    for lid, loc in locs:
        try:
            tlat, tlon = float(loc['lat']), float(loc['lon'])
        except (KeyError, TypeError, ValueError):
            continue
        itu = str(loc.get('itu', '')).upper()
        if itus and itu not in itus:
            continue
        d = distancia_km(lat, lon, tlat, tlon)
        if d > radio_km:
            continue
        estaciones = loc.get('stations') or []
        if isinstance(estaciones, dict):
            estaciones = list(estaciones.values())
        for st in estaciones if isinstance(estaciones, list) else []:
            if not isinstance(st, dict):
                continue
            try:
                hz = _freq_hz(st.get('freq'))
            except (TypeError, ValueError):
                continue
            nombre = ' '.join(str(st.get('station') or st.get('ps') or '').replace('R.', 'Radio ').split())
            if not nombre:
                continue
            try:
                erp = float(str(st.get('erp') or 0).replace(',', '.'))
            except (TypeError, ValueError):
                erp = 0.0
            ciudad = ' '.join(str(loc.get('name') or '').split())
            amb = ambito(nombre)
            out.append({'category': 'radio', 'site_id': 'FMDX-%s' % lid, 'name': '📻 %s %s' % (('%.1f' % (hz / 1e6)), nombre),
                        'lat': round(tlat, 5), 'lon': round(tlon, 5), 'frequency_hz': hz, 'modulation': 'wfm',
                        'erp_kw': erp, 'ambito': amb, 'place': ciudad, 'pi': st.get('pi') or '',
                        'description': '%s · emisor %s%s · %s' % (amb, ciudad, (' · %g kW' % erp) if erp else '', 'FMLIST/fmdx.org'),
                        'source': 'maps.fmdx.org (FMLIST)'})
    return out


# --------------------------------------------------------------------- caché
def _escribir(ruta, datos):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(ruta), prefix='.locator-')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
    os.chmod(tmp, 0o644)
    os.replace(tmp, ruta)


def _leer(ruta):
    try:
        with open(ruta, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def vigente(c, lat=None, lon=None, max_dias=MAX_DIAS):
    if not isinstance(c, dict) or not isinstance(c.get('records'), list):
        return False
    try:                    # una caché rota (a mano, disco lleno…) es como no tenerla
        if time.time() - float(c.get('fecha', 0)) > max_dias * 86400:
            return False
        if lat is not None and c.get('qth') and distancia_km(lat, lon, float(c['qth'][0]), float(c['qth'][1])) > DISTANCIA_CACHE_KM:
            return False
    except (TypeError, ValueError, IndexError):
        return False
    return True


def refrescar(cache, lat, lon, fuentes=('aemet', 'fmdx'), forzar=False, radio_fm_km=150, avisar=print):
    """Baja lo que falte o haya caducado. Nunca lanza: devuelve (hechos, fallos)."""
    hechos, fallos = [], []
    if 'aemet' in fuentes:
        ruta = os.path.join(cache, 'aemet.json')
        if not forzar and vigente(_leer(ruta)):
            hechos.append('aemet (caché)')
        elif not os.environ.get('AEMET_API_KEY'):
            fallos.append('aemet: sin AEMET_API_KEY (uso las estaciones del kit)')
        else:
            try:
                recs = aemet_estaciones(os.environ['AEMET_API_KEY'])
                _escribir(ruta, {'fecha': time.time(), 'fuente': 'aemet', 'records': recs})
                hechos.append('aemet (%d estaciones)' % len(recs))
            except Exception as e:      # red, clave, JSON… : la caché o el kit siguen valiendo
                fallos.append('aemet: %s' % e)
    if 'fmdx' in fuentes:
        ruta = os.path.join(cache, 'fmdx.json')
        if not forzar and vigente(_leer(ruta), lat, lon):
            hechos.append('fmdx (caché)')
        else:
            try:
                recs = fmdx_radios(http_json(FMDX % (lat, lon), timeout=90), lat, lon, radio_fm_km)
                _escribir(ruta, {'fecha': time.time(), 'fuente': 'fmdx', 'qth': [lat, lon], 'records': recs})
                hechos.append('fmdx (%d emisoras de FM)' % len(recs))
            except Exception as e:
                fallos.append('fmdx: %s' % e)
    for f in fallos:
        avisar('  ! datos de zona: %s' % f)
    return hechos, fallos


def cargar(cache, lat=None, lon=None):
    """records de la caché que valgan para esta estación (sin mirar la fecha: mejor viejos que nada)."""
    out = []
    if not cache:
        return out
    a = _leer(os.path.join(cache, 'aemet.json'))
    if isinstance(a, dict) and isinstance(a.get('records'), list):
        out += a['records']
    f = _leer(os.path.join(cache, 'fmdx.json'))
    if vigente(f, lat, lon, max_dias=10 ** 6):
        out += f['records']
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest='orden')
    r = sp.add_parser('refrescar')
    r.add_argument('--cache', required=True)
    r.add_argument('--lat', type=float, required=True)
    r.add_argument('--lon', type=float, required=True)
    r.add_argument('--fuentes', default='aemet,fmdx')
    r.add_argument('--radio-fm-km', type=float, default=150)
    r.add_argument('--forzar', action='store_true')
    v = sp.add_parser('ver')
    v.add_argument('--cache', required=True)
    a = p.parse_args(argv)
    if a.orden == 'refrescar':
        fuentes = [x.strip() for x in a.fuentes.split(',') if x.strip()]
        malas = [x for x in fuentes if x not in ('aemet', 'fmdx')]
        if malas:
            p.error('fuentes desconocidas: %s (valen aemet, fmdx)' % ', '.join(malas))
        hechos, fallos = refrescar(a.cache, a.lat, a.lon, fuentes, a.forzar, a.radio_fm_km)
        print('datos de zona: %s' % (', '.join(hechos) or 'nada nuevo'))
        return 0
    if a.orden == 'ver':
        for n in ('aemet', 'fmdx'):
            c = _leer(os.path.join(a.cache, n + '.json'))
            if c:
                print('%-6s %4d registros · %s%s' % (n, len(c.get('records', [])), time.strftime('%F %H:%M', time.localtime(c.get('fecha', 0))),
                                                     ' · QTH %.3f, %.3f' % tuple(c['qth']) if c.get('qth') else ''))
            else:
                print('%-6s sin datos' % n)
        return 0
    p.print_help()
    return 2


if __name__ == '__main__':
    sys.exit(main())
