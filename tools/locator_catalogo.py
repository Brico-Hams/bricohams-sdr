#!/usr/bin/env python3
"""v4.3 · Construye data/locator/catalogo_es.json, el catálogo nacional que usa el instalador
para elegir, según el locator de la estación (STATION_LOCATOR), los aeropuertos, estaciones
meteorológicas, puertos y otras frecuencias de interés más cercanos (manual 32).

Fuentes (todas en data/locator/fuentes, ver data/locator/LEEME.md):
  ourairports_es_aeropuertos.csv / ourairports_es_frecuencias.csv
      subconjunto de España de OurAirports (dominio público). Canales de 8,33 kHz convertidos a
      su frecuencia real (121,330 → 121,325 MHz).
  aemet_estaciones.csv   estaciones de observación de AEMET (indicativo validado con la lista de
                         estaciones convencionales); coordenadas de OurAirports o aproximadas.
  puertos_es.csv         puertos de interés general y deportivos con sus canales VHF habituales.
  otros_es.csv           otras frecuencias de interés (NAVTEX 518/490 kHz) con su alcance.

Las radios FM regionales y locales y la lista completa de AEMET se añaden en la propia Pi al
instalar (bricohams_locator_online.py), porque cambian a menudo.

Uso:
  python3 tools/locator_catalogo.py                 regenera el catálogo
  python3 tools/locator_catalogo.py --comprobar     falla si el catálogo no está al día (run_tests)
  python3 tools/locator_catalogo.py --bajar-ourairports
                                                    refresca el subconjunto de OurAirports desde GitHub
"""
import argparse
import csv
import io
import json
import os
import sys
import urllib.request

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
FUENTES = os.path.join(RAIZ, 'data', 'locator', 'fuentes')
SALIDA = os.path.join(RAIZ, 'data', 'locator', 'catalogo_es.json')
OURAIRPORTS = 'https://raw.githubusercontent.com/davidmegginson/ourairports-data/main/'

# canal marino (ITU-R M.1084, frecuencia de barco = la que se escucha en los símplex)
CANAL_MARINO = {9: 156450000, 12: 156600000, 14: 156700000, 16: 156800000}
DESC_CANAL = {
    9: 'Puertos deportivos y clubes náuticos (llamada y atraque)',
    12: 'Operaciones portuarias (control del puerto, prácticos). Cada puerto publica sus canales: 12 y 14 son los habituales',
    14: 'Operaciones portuarias (prácticos, amarradores, remolcadores). Cada puerto publica sus canales',
    16: 'Socorro, seguridad y llamada. Se anuncian aquí los boletines de Salvamento Marítimo',
}
TIPOS_AEROPUERTO = {'large_airport', 'medium_airport', 'small_airport', 'heliport', 'seaplane_base'}


def canal_833(texto):
    """Frecuencia real (Hz) de un canal aeronáutico. Los «canales» de 8,33 kHz (xxx,x05/10/15…)
    no son la frecuencia: 121,330 se transmite en 121,325 MHz. Devuelve (hz, nota)."""
    khz = round(float(texto) * 1000)
    r = khz % 25
    base = khz - r
    if r == 0:
        return khz * 1000, ''
    if r in (5, 10, 15):
        hz = round((base + {5: 0.0, 10: 25 / 3, 15: 50 / 3}[r]) * 1000)
        return hz, 'canal 8,33 kHz %s' % ('%.3f' % (khz / 1000)).replace('.', ',')
    return khz * 1000, 'frecuencia sin verificar en OurAirports (%s)' % texto


def leer(nombre):
    with open(os.path.join(FUENTES, nombre), encoding='utf-8') as f:
        return list(csv.DictReader(f))


def aeropuertos():
    aer = {a['ident']: a for a in leer('ourairports_es_aeropuertos.csv') if a['type'] in TIPOS_AEROPUERTO}
    out = []
    for f in leer('ourairports_es_frecuencias.csv'):
        a = aer.get(f['airport_ident'])
        if not a:
            continue
        hz, nota = canal_833(f['frequency_mhz'])
        if not 108e6 <= hz <= 137e6:       # solo banda aérea VHF (AM)
            continue
        tipo = f['type'].strip().upper()
        desc = ' '.join(f['description'].split())
        etiqueta = desc if tipo.lower() in desc.lower() else ('%s %s' % (tipo, desc)).strip()
        if len(etiqueta) > 28:
            etiqueta = tipo or etiqueta[:28]
        detalle = [a['name'], a['municipality']] + ([nota] if nota else [])
        out.append({'category': 'airport', 'site_id': a['ident'], 'name': '✈️ %s %s' % (a['ident'], etiqueta),
                    'lat': round(float(a['latitude_deg']), 5), 'lon': round(float(a['longitude_deg']), 5),
                    'frequency_hz': hz, 'modulation': 'am',
                    'description': ' · '.join(x for x in detalle if x), 'source': 'OurAirports (dominio público)'})
    return out


def meteo():
    out = []
    for e in leer('aemet_estaciones.csv'):
        nombre = e['nombre'].title().replace("D'", "d'").replace(' De ', ' de ').replace(' La ', ' la ').replace(' Del ', ' del ')
        out.append({'category': 'weather', 'site_id': 'AEMET-' + e['idema'], 'station_id': e['idema'], 'name': nombre,
                    'lat': float(e['lat']), 'lon': float(e['lon']),
                    'source': 'AEMET (indicativo) · coordenadas %s' % e['coordenadas']})
    return out


def puertos():
    out = []
    for p in leer('puertos_es.csv'):
        for c in (int(x) for x in p['canales'].split(';')):
            out.append({'category': 'port', 'site_id': 'PUERTO-' + p['id'], 'name': '⚓ Canal %d · %s' % (c, p['nombre']),
                        'channel': c, 'place': p['nombre'],
                        'lat': float(p['lat']), 'lon': float(p['lon']), 'frequency_hz': CANAL_MARINO[c], 'modulation': 'nfm',
                        'description': '%s · %s' % (DESC_CANAL[c], p['notas']), 'source': 'Puertos del Estado / comunidades autónomas'})
    return out


def otros():
    out = []
    for o in leer('otros_es.csv'):
        out.append({'category': 'other', 'site_id': o['id'], 'name': '📟 ' + o['nombre'],
                    'lat': float(o['lat']), 'lon': float(o['lon']), 'frequency_hz': int(o['frecuencia_hz']),
                    'modulation': o['modulacion'], 'range_km': float(o['alcance_km']),
                    'description': o['descripcion'], 'source': o['fuente']})
    return out


def construir():
    recs = aeropuertos() + meteo() + puertos() + otros()
    recs.sort(key=lambda r: (r['category'], r['site_id'], r.get('frequency_hz', 0), r['name']))
    return {
        '_nota': 'Generado por tools/locator_catalogo.py desde data/locator/fuentes (no lo edites a mano). '
                 'Lo usa files/bin/bricohams_locator_bookmarks.py con STATION_LOCATOR (manual 32).',
        'pais': 'ES',
        'fuentes': {
            'airport': 'OurAirports (https://ourairports.com/data/, dominio público): aeropuertos y frecuencias de España',
            'weather': 'AEMET OpenData: indicativos de estaciones convencionales; con AEMET_API_KEY la Pi baja la lista completa',
            'port': 'Puertos de interés general (Puertos del Estado) y deportivos: canales VHF marinos ITU-R M.1084',
            'other': 'NAVTEX de España (Salvamento Marítimo, NAVAREA II/III)',
            'radio': 'Se añade en la Pi: maps.fmdx.org (datos de FMLIST) con LOCATOR_ONLINE=fmdx',
        },
        'records': recs,
    }


def bajar_ourairports():
    datos = {}
    for f in ('airports.csv', 'airport-frequencies.csv'):
        with urllib.request.urlopen(OURAIRPORTS + f, timeout=60) as r:
            datos[f] = r.read().decode('utf-8')
    aer = [a for a in csv.DictReader(io.StringIO(datos['airports.csv'])) if a['iso_country'] == 'ES' and a['type'] != 'closed']
    ids = {a['ident'] for a in aer}
    fr = [f for f in csv.DictReader(io.StringIO(datos['airport-frequencies.csv'])) if f['airport_ident'] in ids]
    con = {f['airport_ident'] for f in fr}
    ca = ['ident', 'type', 'name', 'latitude_deg', 'longitude_deg', 'elevation_ft', 'iso_region', 'municipality', 'icao_code', 'iata_code']
    with open(os.path.join(FUENTES, 'ourairports_es_aeropuertos.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, ca, extrasaction='ignore', lineterminator='\n')
        w.writeheader()
        w.writerows(sorted((a for a in aer if a['ident'] in con), key=lambda a: a['ident']))
    cf = ['airport_ident', 'type', 'description', 'frequency_mhz']
    with open(os.path.join(FUENTES, 'ourairports_es_frecuencias.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, cf, extrasaction='ignore', lineterminator='\n')
        w.writeheader()
        w.writerows(sorted(fr, key=lambda x: (x['airport_ident'], float(x['frequency_mhz']), x['type'])))
    print('OurAirports: %d aeropuertos de España con %d frecuencias' % (len(con), len(fr)))


def texto(cat):
    return json.dumps(cat, ensure_ascii=False, indent=1) + '\n'


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--comprobar', action='store_true', help='solo comprobar que el catálogo está al día')
    p.add_argument('--bajar-ourairports', action='store_true', help='refrescar el subconjunto de OurAirports')
    a = p.parse_args()
    if a.bajar_ourairports:
        bajar_ourairports()
    cat = construir()
    nuevo = texto(cat)
    viejo = open(SALIDA, encoding='utf-8').read() if os.path.exists(SALIDA) else ''
    n = {}
    for r in cat['records']:
        n[r['category']] = n.get(r['category'], 0) + 1
    resumen = ', '.join('%s %d' % kv for kv in sorted(n.items()))
    if a.comprobar:
        if nuevo != viejo:
            print('✘ data/locator/catalogo_es.json no está al día: python3 tools/locator_catalogo.py')
            return 1
        print('OK catálogo de zona al día (%s)' % resumen)
        return 0
    with open(SALIDA, 'w', encoding='utf-8') as f:
        f.write(nuevo)
    print('catálogo: %s (%s)' % (os.path.relpath(SALIDA, RAIZ), resumen))
    return 0


if __name__ == '__main__':
    sys.exit(main())
