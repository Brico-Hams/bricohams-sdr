#!/usr/bin/env python3
"""Select nearby radio sites from a curated JSON catalog for an OpenWebRX+ QTH.

v4.3 (BricoHams) · Elige, según el locator (o las coordenadas) de la estación, lo más cercano de
cada categoría del catálogo nacional data/locator/catalogo_es.json y lo convierte en marcadores
de OpenWebRX+ etiquetados [AUTO-LOCATOR]:

  airport  aeropuertos y sus frecuencias (TWR, APP, GND, ATIS…) · al menos el más cercano
  weather  estaciones AEMET → METEO_STATIONS (no son marcadores) · al menos la más cercana
  port     puertos y sus canales VHF (los canales repetidos se juntan en un marcador)
  radio    emisoras de FM regionales y locales (de la caché que baja bricohams_locator_online.py)
  other    otras frecuencias de interés (NAVTEX) dentro de su alcance (range_km)

Lejos de la Región de Murcia (más de --kit-zona-km), los marcadores del kit propios de la Región de Murcia (FM y
DAB+ de Murcia, aeropuertos de Murcia, repetidores EA5…) se quitan, y los canales marinos con
nombre de Cartagena vuelven a su nombre genérico. Los marcadores que añadiste tú no se tocan nunca.
"""
import argparse
import json
import math
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bricohams_locator import en_espana, latlon_to_locator, locator_to_latlon  # noqa: E402

ETIQUETA = '[AUTO-LOCATOR]'
CATEGORIAS = ('airport', 'weather', 'port', 'radio', 'other')
MINIMO_UNO = ('airport', 'weather')        # si no hay ninguno en el radio, el más cercano (hasta 2,5 × radio)
KIT_ORIGEN = locator_to_latlon('IM98')      # centro aproximado del locator regional, no un QTH preciso
LOCAL_KIT = re.compile(r'\b(E[ACD]\d\w*|Sierra Espuña|Murcia|Cartagena|Mazarrón|Lorca|Alicante|Benidorm|Granada|'
                       r'Albacete|Águilas|Carrascoy|Peña Rubia|Valencia|Radio Club|Cabo de Gata|Cabo la Nao|LE[A-Z]{2})\b')


def distance_km(lat1, lon1, lat2, lon2):
    radius = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    hav = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius * math.asin(min(1, math.sqrt(hav)))


def _validar(registro):
    categoria = str(registro.get('category', '')).strip().lower()
    if categoria not in CATEGORIAS:
        raise ValueError('category no reconocida en catálogo: %s' % categoria)
    site_id = str(registro.get('site_id') or registro.get('station_id') or registro.get('name') or '').strip()
    nombre = str(registro.get('name') or site_id).strip()
    if not site_id or not nombre:
        raise ValueError('cada registro necesita site_id y name')
    try:
        site_lat, site_lon = float(registro['lat']), float(registro['lon'])
    except (KeyError, TypeError, ValueError):
        raise ValueError('coordenadas no válidas para %s' % nombre)
    if not (-90 <= site_lat <= 90 and -180 <= site_lon <= 180):
        raise ValueError('coordenadas fuera de rango para %s' % nombre)
    return categoria, site_id, nombre, site_lat, site_lon


def seleccionar(locator, catalogo, radio_km=100, max_sitios=3, qth=None, radios_max=30,
                radios_ambitos=('regional', 'local'), minimo=True):
    """(lat, lon, registros elegidos). qth=(lat, lon) manda sobre el centro del locator."""
    if radio_km <= 0 or max_sitios <= 0:
        raise ValueError('radio_km y max_sitios deben ser positivos')
    lat, lon = qth if qth else locator_to_latlon(locator)
    sitios, radios, cercanos = {}, [], {}
    for registro in catalogo:
        categoria, site_id, nombre, site_lat, site_lon = _validar(registro)
        distancia = distance_km(lat, lon, site_lat, site_lon)
        item = dict(registro, category=categoria, site_id=site_id, name=nombre, distance_km=distancia)
        alcance = max(radio_km, float(registro.get('range_km') or 0))
        if distancia > alcance:
            if minimo and categoria in MINIMO_UNO and distancia <= radio_km * 2.5:
                cercanos.setdefault(categoria, {}).setdefault(site_id, []).append(item)
            continue
        if categoria == 'radio':
            if radios_ambitos and registro.get('ambito') and registro['ambito'] not in radios_ambitos:
                continue
            radios.append(item)
            continue
        sitios.setdefault(categoria, {}).setdefault(site_id, []).append(item)

    for categoria in MINIMO_UNO:            # ninguno dentro del radio: el sitio más cercano un poco más allá
        if minimo and categoria not in sitios and categoria in cercanos:
            sid, regs = min(cercanos[categoria].items(), key=lambda par: min(x['distance_km'] for x in par[1]))
            sitios[categoria] = {sid: regs}

    elegidos = []
    for categoria, por_sitio in sitios.items():
        ranking = sorted(por_sitio.items(), key=lambda par: min(x['distance_km'] for x in par[1]))
        for _, registros in ranking[:max_sitios]:
            elegidos.extend(registros)
    # FM: las que mejor se oyen (potencia / distancia²), una por frecuencia
    por_frecuencia = {}
    for r in radios:
        puntos = max(float(r.get('erp_kw') or 0.1), 0.01) / max(r['distance_km'], 1.0) ** 2
        f = r.get('frequency_hz')
        if f not in por_frecuencia or puntos > por_frecuencia[f][0]:
            por_frecuencia[f] = (puntos, r)
    elegidos += [r for _, r in sorted(por_frecuencia.values(), key=lambda x: -x[0])[:radios_max]]
    elegidos.sort(key=lambda r: (r['category'], r['distance_km'], r['name'], r.get('frequency_hz', 0)))
    return lat, lon, elegidos


def bookmarks(registros, locator):
    """Marcadores de OpenWebRX+. Una sola entrada por (frecuencia, modo): los canales marinos de varios
    puertos se juntan («⚓ Canal 12 · Cartagena / Mazarrón»)."""
    grupos, orden = {}, []
    for registro in registros:
        if registro['category'] == 'weather' or not registro.get('frequency_hz'):
            continue
        frecuencia = int(round(float(registro['frequency_hz'])))
        modo = str(registro.get('modulation', '')).lower()
        if frecuencia <= 0 or not modo:
            raise ValueError('frecuencia_hz y modulation son necesarios para %s' % registro['name'])
        clave = (frecuencia, modo)
        if clave not in grupos:
            grupos[clave] = []
            orden.append(clave)
        grupos[clave].append(registro)
    resultado = []
    for clave in orden:
        regs = sorted(grupos[clave], key=lambda r: r['distance_km'])
        registro = regs[0]
        distancia = registro['distance_km']
        fuente = str(registro.get('source', '')).strip()
        detalle = str(registro.get('description', '')).strip()
        if registro['category'] == 'port' and registro.get('channel'):
            lugares = []
            for r in regs:
                if r.get('place') and r['place'] not in lugares:
                    lugares.append(r['place'])
            nombre = '⚓ Canal %d · %s' % (registro['channel'], ' / '.join(lugares[:3]) + (' …' if len(lugares) > 3 else ''))
        else:
            nombre = registro['name']
        parts = [ETIQUETA, 'locator %s' % locator, '%.1f km' % distancia]
        if fuente:
            parts.append('fuente: ' + fuente)
        if detalle:
            parts.append(detalle)
        if len(regs) > 1:
            otros = ['%s %.0f km' % (r.get('place') or r['name'], r['distance_km']) for r in regs[1:6]]
            parts.append('también: ' + ', '.join(otros))
        resultado.append({
            'name': '%s · %.0f km' % (nombre, distancia),
            'frequency': clave[0],
            'modulation': clave[1],
            'scannable': clave[1] in ('nfm', 'wfm', 'am', 'usb', 'lsb', 'cw'),
            'description': ' · '.join(parts),
        })
    return resultado


def meteo_stations(registros):
    result = []
    seen = set()
    for registro in registros:
        if registro['category'] != 'weather':
            continue
        station_id = str(registro.get('station_id') or '').strip()
        if station_id and station_id not in seen:
            result.append('%s:%s' % (station_id, registro['name'].replace(',', ' ')))
            seen.add(station_id)
    return ','.join(result)


def kit_local(b):
    """¿Es un marcador del kit propio de la Región de Murcia? None (se queda), 'quitar' o el nombre genérico."""
    f, m, n = b.get('frequency', 0), b.get('modulation', ''), b.get('name', '')
    if m in ('wfm', 'dab'):
        return 'quitar'                                    # FM y DAB+ de Murcia
    if m == 'am' and 108e6 <= f <= 137e6:
        if f == 121500000:
            return None                                    # emergencia: vale en todas partes
        if f == 123450000:
            return '✈️ 123.450 Aire-aire'
        return 'quitar'                                    # aeropuertos de Murcia y Alicante
    if LOCAL_KIT.search(n):
        partes = n.split(' · ')
        if LOCAL_KIT.search(partes[0]):
            return 'quitar'                                # repetidores EA5, Radio Club, hotspots…
        generico = []
        for p in partes:                                   # «⛵ Canal 12 · Prácticos Cartagena» → «⛵ Canal 12»
            if LOCAL_KIT.search(p):
                break
            generico.append(p)
        return ' · '.join(generico)
    return None


def merge_bookmarks(existing, generated, kit=None, lejos=False):
    """Quita los [AUTO-LOCATOR] anteriores, adapta los del kit si la estación está lejos de la Región de Murcia
    y añade los nuevos que no choquen (misma frecuencia y modo) con los que quedan."""
    generated_tag = ETIQUETA
    manual = [dict(b) for b in existing if generated_tag not in b.get('description', '')]
    genericos = set()           # del kit, con el nombre de Murcia quitado: si la zona trae uno, manda el de la zona
    if kit and lejos:
        del_kit = {(b.get('name'), b.get('frequency'), b.get('modulation')) for b in kit}
        quedan = []
        for b in manual:
            if (b.get('name'), b.get('frequency'), b.get('modulation')) in del_kit:
                accion = kit_local(b)
                if accion == 'quitar':
                    continue
                if accion:
                    b['name'] = accion
                    b.pop('description', None)
                    genericos.add((b.get('frequency'), b.get('modulation')))
            quedan.append(b)
        manual = quedan
    nuevos = {(b['frequency'], b['modulation']) for b in generated}
    manual = [b for b in manual if (b.get('frequency'), b.get('modulation')) not in genericos & nuevos]
    have = {(b.get('frequency'), b.get('modulation')) for b in manual}
    return manual + [b for b in generated if (b['frequency'], b['modulation']) not in have]


def write_json(path, data):
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix='.locator-', suffix='.json', dir=directory)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def cargar_catalogo(ruta, cache=None, qth=None):
    """Catálogo del kit + caché de la Pi (AEMET en vivo sustituye a las estaciones del kit)."""
    with open(ruta, encoding='utf-8') as stream:
        catalog = json.load(stream)
    if isinstance(catalog, dict):
        catalog = catalog.get('records')
    if not isinstance(catalog, list):
        raise ValueError('el catálogo debe ser una lista JSON o un objeto con records')
    if cache:
        import bricohams_locator_online as online
        extra = online.cargar(cache, *(qth or (None, None)))
        if any(r.get('category') == 'weather' for r in extra):
            catalog = [r for r in catalog if r.get('category') != 'weather']
        catalog = catalog + extra
    return catalog


def informe(lat, lon, locator, nearby):
    zona = en_espana(lat, lon)
    print('QTH %s · %.5f, %.5f · %s' % (locator.upper() if locator else latlon_to_locator(lat, lon),
                                        lat, lon, zona or 'FUERA DE ESPAÑA (el catálogo es de España)'))
    titulos = {'airport': 'Aeropuertos', 'weather': 'Estaciones meteorológicas (AEMET)', 'port': 'Puertos (VHF marina)',
               'radio': 'Emisoras de FM', 'other': 'Otras frecuencias de interés'}
    for cat in ('airport', 'weather', 'port', 'radio', 'other'):
        regs = [r for r in nearby if r['category'] == cat]
        print('\n%s (%d)' % (titulos[cat], len(regs)))
        for r in regs:
            f = r.get('frequency_hz')
            print('  %6.1f km  %-44s %s' % (r['distance_km'], r['name'][:44],
                                           ('%.4f MHz %s' % (f / 1e6, r.get('modulation', ''))) if f else r.get('station_id', '')))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--locator', help='locator Maidenhead (4-10 caracteres)')
    parser.add_argument('--lat', type=float, help='latitud exacta (manda sobre el centro del locator)')
    parser.add_argument('--lon', type=float, help='longitud exacta')
    parser.add_argument('--catalog', required=True, help='JSON con records geográficos curados')
    parser.add_argument('--online-cache', help='carpeta de la caché de bricohams_locator_online.py')
    parser.add_argument('--radius-km', type=float, default=100)
    parser.add_argument('--max-sites', type=int, default=3, help='máximo de ubicaciones por categoría')
    parser.add_argument('--radios-max', type=int, default=30, help='máximo de emisoras de FM')
    parser.add_argument('--radios', default='regional,local', help='ámbitos de FM: regional,local,nacional')
    parser.add_argument('--meteo-stations', action='store_true', help='imprime id:nombre para METEO_STATIONS')
    parser.add_argument('--informe', action='store_true', help='tabla de lo más cercano por categoría')
    parser.add_argument('--merge-existing', help='bookmarks.json al que reemplazar los AUTO-LOCATOR anteriores')
    parser.add_argument('--kit', help='bookmarks.json del kit (para adaptar los de Murcia lejos de la Región de Murcia)')
    parser.add_argument('--kit-zona-km', type=float, default=150, help='distancia a Murcia capital a partir de la que se adaptan')
    parser.add_argument('--output', default='-', help='JSON de salida (por defecto stdout)')
    args = parser.parse_args()
    if not args.locator and (args.lat is None or args.lon is None):
        parser.error('hace falta --locator o --lat y --lon')
    qth = (args.lat, args.lon) if args.lat is not None and args.lon is not None and (args.lat or args.lon) else None
    locator = args.locator or latlon_to_locator(*qth)
    catalog = cargar_catalogo(args.catalog, args.online_cache, qth or locator_to_latlon(locator))
    ambitos = tuple(x.strip() for x in args.radios.split(',') if x.strip())
    lat, lon, nearby = seleccionar(locator, catalog, args.radius_km, args.max_sites, qth, args.radios_max, ambitos)
    if args.meteo_stations:
        print(meteo_stations(nearby))
        return 0
    if args.informe:
        informe(lat, lon, locator, nearby)
        return 0

    result = bookmarks(nearby, locator.upper())
    if args.merge_existing:
        with open(args.merge_existing, encoding='utf-8') as stream:
            existing = json.load(stream)
        kit = None
        if args.kit:
            with open(args.kit, encoding='utf-8') as stream:
                kit = json.load(stream)
        lejos = distance_km(lat, lon, *KIT_ORIGEN) > args.kit_zona_km
        result = merge_bookmarks(existing, result, kit, lejos)
    if args.output == '-':
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        write_json(args.output, result)
        print('locator %s (%.6f, %.6f): %d ubicaciones próximas, %d bookmarks' % (
            locator.upper(), lat, lon, len(nearby), len(result)))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise SystemExit('bricohams_locator_bookmarks: %s' % error)
