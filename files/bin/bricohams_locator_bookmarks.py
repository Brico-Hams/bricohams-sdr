#!/usr/bin/env python3
"""Select nearby radio sites from a curated JSON catalog for an OpenWebRX+ QTH."""
import argparse
import json
import math
import os
import tempfile

from bricohams_locator import locator_to_latlon


def distance_km(lat1, lon1, lat2, lon2):
    radius = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    hav = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius * math.asin(min(1, math.sqrt(hav)))


def seleccionar(locator, catalogo, radio_km=100, max_sitios=3):
    if radio_km <= 0 or max_sitios <= 0:
        raise ValueError('radio_km y max_sitios deben ser positivos')
    lat, lon = locator_to_latlon(locator)
    sitios = {}
    for registro in catalogo:
        categoria = str(registro.get('category', '')).strip().lower()
        if categoria not in ('airport', 'weather', 'port', 'radio', 'other'):
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
        distancia = distance_km(lat, lon, site_lat, site_lon)
        if distancia > radio_km:
            continue
        item = dict(registro, category=categoria, site_id=site_id, name=nombre, distance_km=distancia)
        sitios.setdefault(categoria, {}).setdefault(site_id, []).append(item)

    elegidos = []
    for categoria, por_sitio in sitios.items():
        ranking = sorted(por_sitio.items(), key=lambda par: min(x['distance_km'] for x in par[1]))
        for _, registros in ranking[:max_sitios]:
            elegidos.extend(registros)
    elegidos.sort(key=lambda r: (r['category'], r['distance_km'], r['name'], r.get('frequency_hz', 0)))
    return lat, lon, elegidos


def bookmarks(registros, locator):
    resultado = []
    for registro in registros:
        if registro['category'] == 'weather' or not registro.get('frequency_hz'):
            continue
        frecuencia = int(round(float(registro['frequency_hz'])))
        modo = str(registro.get('modulation', '')).lower()
        if frecuencia <= 0 or not modo:
            raise ValueError('frecuencia_hz y modulation son necesarios para %s' % registro['name'])
        distancia = registro['distance_km']
        fuente = str(registro.get('source', '')).strip()
        detalle = str(registro.get('description', '')).strip()
        parts = ['[AUTO-LOCATOR]', 'locator %s' % locator, '%.1f km' % distancia]
        if fuente:
            parts.append('fuente: ' + fuente)
        if detalle:
            parts.append(detalle)
        resultado.append({
            'name': '%s · %.0f km' % (registro['name'], distancia),
            'frequency': frecuencia,
            'modulation': modo,
            'scannable': modo in ('nfm', 'wfm', 'am', 'usb', 'lsb', 'cw'),
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


def merge_bookmarks(existing, generated):
    generated_tag = '[AUTO-LOCATOR]'
    manual = [b for b in existing if generated_tag not in b.get('description', '')]
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--locator', required=True)
    parser.add_argument('--catalog', required=True, help='JSON con records geográficos curados')
    parser.add_argument('--radius-km', type=float, default=100)
    parser.add_argument('--max-sites', type=int, default=3, help='máximo de ubicaciones por categoría')
    parser.add_argument('--meteo-stations', action='store_true', help='imprime id:nombre para METEO_STATIONS')
    parser.add_argument('--merge-existing', help='bookmarks.json al que reemplazar los AUTO-LOCATOR anteriores')
    parser.add_argument('--output', default='-', help='JSON de salida (por defecto stdout)')
    args = parser.parse_args()

    with open(args.catalog, encoding='utf-8') as stream:
        catalog = json.load(stream)
    if isinstance(catalog, dict):
        catalog = catalog.get('records')
    if not isinstance(catalog, list):
        parser.error('el catálogo debe ser una lista JSON o un objeto con records')
    lat, lon, nearby = seleccionar(args.locator, catalog, args.radius_km, args.max_sites)
    if args.meteo_stations:
        print(meteo_stations(nearby))
        return 0

    result = bookmarks(nearby, args.locator)
    if args.merge_existing:
        with open(args.merge_existing, encoding='utf-8') as stream:
            result = merge_bookmarks(json.load(stream), result)
    if args.output == '-':
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        write_json(args.output, result)
    print('locator %s (%.6f, %.6f): %d ubicaciones próximas, %d bookmarks' % (
        args.locator.upper(), lat, lon, len(nearby), len(result)))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise SystemExit('bricohams_locator_bookmarks: %s' % error)