#!/usr/bin/env python3
"""v4.3 · Marcadores y meteo de zona para CUALQUIER locator de España (manual 32):
  · todas las cuadrículas de 4 caracteres con el centro en España (península, Baleares, Canarias,
    Ceuta y Melilla) dan aeropuertos, METEO_STATIONS y, en la costa, canales de puerto;
  · locator ⇄ coordenadas (ida y vuelta), dentro de la celda y detección de España;
  · datos en línea (AEMET y FM de maps.fmdx.org) con respuestas de prueba: ámbito regional /
    nacional / local, distancia, país, caché y fallos sin parar la instalación;
  · lejos de la Región de Murcia se adaptan los marcadores del kit de Murcia (los tuyos no se tocan);
  · bricohams-locator (info, meteo, marcadores) y la zona en install.sh (coordenadas que mandan,
    locator desde coordenadas, LOCATOR_METEO, avisos)."""
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
BIN = os.path.join(RAIZ, 'files', 'bin')
sys.path.insert(0, BIN)
import bricohams_locator as loc                      # noqa: E402
import bricohams_locator_bookmarks as bm             # noqa: E402
import bricohams_locator_online as online            # noqa: E402

CAT = os.path.join(RAIZ, 'data', 'locator', 'catalogo_es.json')
catalogo = bm.cargar_catalogo(CAT)
puertos = [r for r in catalogo if r['category'] == 'port']
meteo = [r for r in catalogo if r['category'] == 'weather']

# ------------------------------------------------------------------ 1. toda España
cuadros, costa = 0, 0
SUB = 'cgkosw'            # 6 × 6 subcuadrículas de cada cuadrícula (≈ cada 20 km × 10 km)
for campo in ('IL', 'IM', 'IN', 'JM', 'JN'):
    for x in range(10):
        for y in range(10):
            for a_ in SUB:
                for b_ in SUB:
                    l6 = '%s%d%d%s%s' % (campo, x, y, a_, b_)
                    lat, lon = loc.locator_to_latlon(l6)
                    if not loc.en_espana(lat, lon):
                        continue
                    # las cajas de España incluyen mar: cuenta si hay una estación AEMET a menos de 40 km
                    if min(bm.distance_km(lat, lon, m['lat'], m['lon']) for m in meteo) > 40:
                        continue
                    cuadros += 1
                    _, _, cerca = bm.seleccionar(l6, catalogo, 100, 3)
                    gen = bm.bookmarks(cerca, l6)
                    assert any(b['modulation'] == 'am' for b in gen), ('sin aeropuerto', l6)
                    assert bm.meteo_stations(cerca), ('sin estación AEMET', l6)
                    assert len({(b['frequency'], b['modulation']) for b in gen}) == len(gen), ('repetidos', l6)
                    assert all(b['frequency'] > 0 and '[AUTO-LOCATOR]' in b['description'] for b in gen)
                    if min(bm.distance_km(lat, lon, p['lat'], p['lon']) for p in puertos) < 25:
                        costa += 1
                        assert any(b['frequency'] == 156800000 for b in gen), ('costa sin canal 16', l6)
assert cuadros >= 800 and costa >= 100, (cuadros, costa)
# los tres ejemplos del manual
for l, espera in (('IM97KX', 'LELC'), ('IN80DK', 'LEMD'), ('JN11CJ', 'LEBL'), ('IL18QC', 'GC')):
    _, _, cerca = bm.seleccionar(l, catalogo, 100, 3)
    assert any(espera in r['name'] for r in cerca if r['category'] == 'airport'), (l, [r['name'] for r in cerca])

# ------------------------------------------------------------------ 2. locator
random.seed(5)
for _ in range(500):
    lat, lon = random.uniform(27, 44), random.uniform(-18.5, 4.5)
    for n in (4, 6, 8, 10):
        l = loc.latlon_to_locator(lat, lon, n)
        assert loc.dentro_de_celda(l, lat, lon), (lat, lon, l)
        c = loc.locator_to_latlon(l)
        assert loc.latlon_to_locator(c[0], c[1], n) == l, (l, c)
assert loc.latlon_to_locator(37.9838, -1.1280) == 'IM97kx' and loc.locator_to_latlon('IM98') == (38.5, -1.0)
for nombre, (lat, lon), zona in (('Murcia', (37.9922, -1.1307), 'península'), ('Badajoz', (38.878, -6.970), 'península'),
                                 ('Palma', (39.57, 2.65), 'península'), ('Las Palmas', (28.12, -15.43), 'Canarias'),
                                 ('Ceuta', (35.889, -5.32), 'Ceuta'), ('Melilla', (35.292, -2.94), 'Melilla'),
                                 ('Lisboa', (38.72, -9.14), None), ('Porto', (41.15, -8.61), None), ('Andorra', (42.51, 1.52), None),
                                 ('Perpiñán', (42.70, 2.90), None), ('Tánger', (35.77, -5.80), None)):
    assert (loc.en_espana(lat, lon) is not None) == (zona is not None), nombre
for malo in ('IM9', 'ZZ99', 'IM9AIU', '12AB'):
    try:
        loc.locator_to_latlon(malo)
        raise AssertionError(malo)
    except ValueError:
        pass
# 8,33 kHz: el canal 121,330 se transmite en 121,325 MHz
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import locator_catalogo as lc                         # noqa: E402
assert lc.canal_833('121.33') == (121325000, 'canal 8,33 kHz 121,330')
assert lc.canal_833('118.010')[0] == 118008333 and lc.canal_833('118.015')[0] == 118016667 and lc.canal_833('118.025') == (118025000, '')
assert subprocess.run([sys.executable, os.path.join(RAIZ, 'tools', 'locator_catalogo.py'), '--comprobar'], capture_output=True).returncode == 0

# ------------------------------------------------------------------ 3. datos en línea (respuestas de prueba)
QTH = (37.9838, -1.1280)
FMDX = {'locations': {
    '101': {'lat': 38.0, 'lon': -1.2, 'name': 'Murcia/Carrascoy', 'itu': 'E', 'stations': [
        {'freq': 95.6, 'station': 'Onda Regional de Murcia', 'erp': 10, 'pi': 'E2A1'},
        {'freq': '97.50', 'station': 'Wifon FM', 'erp': 1},
        {'freq': 90.9, 'station': 'RNE Radio Nacional', 'erp': 50},
        {'freq': 101.0, 'station': 'Cadena SER Murcia', 'erp': 5}]},
    '102': {'lat': 38.35, 'lon': -0.48, 'name': 'Alacant', 'itu': 'E', 'stations': [
        {'freq': 95.6, 'station': 'À Punt', 'erp': 2}, {'freq': 'x', 'station': 'roto'}]},
    '103': {'lat': 38.7, 'lon': -9.1, 'name': 'Lisboa', 'itu': 'POR', 'stations': [{'freq': 100.0, 'station': 'Antena 1', 'erp': 50}]},
    '104': {'lat': 41.4, 'lon': 2.1, 'name': 'Barcelona', 'itu': 'E', 'stations': [{'freq': 102.8, 'station': 'Catalunya Ràdio', 'erp': 50}]},
}}
radios = online.fmdx_radios(FMDX, QTH[0], QTH[1], 150)
amb = {r['name']: r['ambito'] for r in radios}
assert amb == {'📻 95.6 Onda Regional de Murcia': 'regional', '📻 97.5 Wifon FM': 'local', '📻 90.9 RNE Radio Nacional': 'nacional',
               '📻 101.0 Cadena SER Murcia': 'nacional', '📻 95.6 À Punt': 'regional'}, amb
assert all(r['frequency_hz'] % 100000 == 0 for r in radios)
for n, a in (('Radio Marca', 'nacional'), ('Los40 Classic', 'nacional'), ('Canal Sur Radio', 'regional'), ('Radio Sol de Lorca', 'local'),
             ('Radio Serena', 'local'), ('Onda Cero Cartagena', 'nacional')):
    assert online.ambito(n) == a, (n, online.ambito(n))
filas = [{'idema': '7178I', 'lat': 38.0, 'lon': -1.17, 'ubi': 'MURCIA', 'alt': 61},
         {'idema': '7178I', 'lat': 38.0, 'lon': -1.17, 'ubi': 'MURCIA', 'alt': 61},
         {'idema': '7031X', 'lat': 37.79, 'lon': -0.80, 'ubi': 'MURCIA/SAN JAVIER'}, {'idema': 'ROTA', 'lat': 'x', 'lon': 1}]
pedidas = []


def falso(url, headers=None, timeout=40):
    pedidas.append((url, headers))
    if url == online.AEMET_TODAS:
        return {'estado': 200, 'datos': 'https://opendata.aemet.es/opendata/sh/abc'}
    if '/opendata/sh/' in url:
        return filas
    if url.startswith('https://maps.fmdx.org/'):
        return FMDX
    raise OSError('sin red')


online.http_json = falso
C = tempfile.mkdtemp()
os.environ.pop('AEMET_API_KEY', None)
hechos, fallos = online.refrescar(C, *QTH, avisar=lambda m: None)
assert any('sin AEMET_API_KEY' in f for f in fallos) and any('fmdx (5 emisoras' in h for h in hechos), (hechos, fallos)
os.environ['AEMET_API_KEY'] = 'clave-de-prueba'
hechos, fallos = online.refrescar(C, *QTH, avisar=lambda m: None)
assert any('aemet (2 estaciones)' in h for h in hechos) and any('fmdx (caché)' in h for h in hechos), hechos
assert pedidas[-2][1] == {'api_key': 'clave-de-prueba'} and 'clave' not in json.dumps(json.load(open(os.path.join(C, 'aemet.json'))))
assert len(online.cargar(C, *QTH)) == 7 and len(online.cargar(C, 41.4, 2.1)) == 2, 'FM solo si la estación no se ha movido'
# revisión v4.3: entradas raras en fmdx y caché rota no tumban nada
raro = {'locations': {'1': {'lat': 38.0, 'lon': -1.2, 'itu': 'E', 'name': 'X', 'stations': {'a': {'freq': 99.1, 'station': 'Radio Uno', 'erp': '1,5'}, 'b': 'basura'}},
                      '2': {'lat': 38.0, 'lon': -1.2, 'itu': 'E', 'stations': ['x', None, {'freq': None}]}}}
rr = online.fmdx_radios(raro, QTH[0], QTH[1], 150)
assert [(x['name'], x['erp_kw']) for x in rr] == [('📻 99.1 Radio Uno', 1.5)], rr
assert not online.vigente({'fecha': 'ayer', 'records': []}) and not online.vigente({'fecha': 0, 'records': [], 'qth': ['a']}, 1, 1)
online.http_json = lambda *a, **k: (_ for _ in ()).throw(OSError('sin red'))
hechos, fallos = online.refrescar(C, *QTH, forzar=True, avisar=lambda m: None)
assert len(fallos) == 2 and json.load(open(os.path.join(C, 'fmdx.json')))['records'], 'sin red se queda la caché'
cat2 = bm.cargar_catalogo(CAT, C, QTH)
assert [r['station_id'] for r in cat2 if r['category'] == 'weather'] == ['7031X', '7178I'], 'AEMET en vivo sustituye al kit'
lat, lon, cerca = bm.seleccionar('IM98', cat2, 100, 3, QTH)
assert (lat, lon) == QTH, 'las coordenadas exactas mandan sobre el centro del locator'
fm = [r['name'] for r in cerca if r['category'] == 'radio']
assert '📻 95.6 Onda Regional de Murcia' in fm and '📻 97.5 Wifon FM' in fm and not any('RNE' in x or 'SER' in x for x in fm), fm
assert '📻 95.6 À Punt' not in fm, 'una por frecuencia: la que mejor se oye'
_, _, cerca_n = bm.seleccionar('IM98', cat2, 100, 3, QTH, radios_ambitos=('regional', 'local', 'nacional'))
assert any('RNE' in r['name'] for r in cerca_n)
assert bm.meteo_stations(cerca) == '7178I:Murcia,7031X:Murcia/San Javier'

# ------------------------------------------------------------------ 4. marcadores del kit lejos de Murcia
KIT = json.load(open(os.path.join(RAIZ, 'files', 'openwebrx', 'bookmarks.json'), encoding='utf-8'))
mio = {'name': 'Mi repetidor ED1ZZZ', 'frequency': 145650000, 'modulation': 'nfm'}       # propio: no se toca
_, _, vigo = bm.seleccionar('IN52PF', catalogo, 100, 3)
nuevos = bm.bookmarks(vigo, 'IN52PF')
lejos = bm.merge_bookmarks(KIT + [mio], nuevos, KIT, lejos=True)
nombres = [b['name'] for b in lejos]
assert 'Mi repetidor ED1ZZZ' in nombres
quedan_kit = [b for b in lejos if '[AUTO-LOCATOR]' not in b.get('description', '') and b is not mio and b['name'] != mio['name']]
assert not any(re.search(r'Murcia|Cartagena|Mazarrón|Lorca|Alicante|ED5|EA5|Sierra Espuña|LEMI|LELC', b['name']) for b in quedan_kit), \
    [b['name'] for b in quedan_kit if re.search(r'Murcia|Cartagena|ED5|EA5', b['name'])]
assert not any(b['modulation'] in ('wfm', 'dab') for b in quedan_kit), 'FM y DAB+ de Murcia fuera'
assert any(n.startswith('⚓ Canal 12 · Vigo') for n in nombres) and '⛵ Canal 12' not in nombres, 'el canal genérico del kit cede al de los puertos de la zona'
for generico in ('🆘 Canal 16 · socorro', '⛵ Canal 10', '⛵ Canal 65', '✈️ 121.500 Emergencia', '✈️ 123.450 Aire-aire', '⚓ AIS 1 (87B)', '🛰️ ISS Voz/SSTV'):
    assert generico in nombres or any(n.startswith(generico.split(' · ')[0]) for n in nombres), generico
assert sum(1 for b in lejos if 26.9e6 < b['frequency'] < 27.5e6) == sum(1 for b in KIT if 26.9e6 < b['frequency'] < 27.5e6), 'CB intacta'
assert any('Vigo' in n for n in nombres if '[AUTO' not in n) or any('LEVX' in b['name'] for b in lejos)
cerca_kit = bm.merge_bookmarks(KIT, bm.bookmarks(bm.seleccionar('IM97KX', catalogo, 100, 3)[2], 'IM97KX'), KIT, lejos=False)
assert all(b in cerca_kit for b in KIT), 'en la Región de Murcia el kit se queda entero'
assert bm.merge_bookmarks(lejos, nuevos, KIT, lejos=True) == lejos, 'idempotente'

# ------------------------------------------------------------------ 5. bricohams-locator
T = tempfile.mkdtemp()
env = os.path.join(T, 'bricohams.env')
open(env, 'w').write("STATION_LOCATOR='JN11CJ'\nSTATION_LAT='0.0'\nSTATION_LON='0.0'\nLOCATOR_CATALOG='data/locator/catalogo_es.json'\n")
e = dict(os.environ, BRICOHAMS_ENV=env, BRICOHAMS_KIT=RAIZ, BRICOHAMS_LOCATOR_CACHE=os.path.join(T, 'nada'))
cli = os.path.join(BIN, 'bricohams-locator')
r = subprocess.run([sys.executable, cli, 'info'], capture_output=True, text=True, env=e)
assert r.returncode == 0 and 'JN11CJ' in r.stdout and 'LEBL' in r.stdout and 'Barcelona' in r.stdout, r.stdout + r.stderr
zona_env = os.path.join(T, 'zona.env')           # sin sudo: la copia sin secretos (644) de instalar_env
open(zona_env, 'w').write("STATION_LOCATOR='IM75IV'\n")
r = subprocess.run([sys.executable, cli, 'info'], capture_output=True, text=True, env=dict(e, BRICOHAMS_ENV=os.path.join(T, 'no-legible.env')))
assert 'IM75IV' in r.stdout and 'Ceuta' in r.stdout, r.stdout + r.stderr
r = subprocess.run([sys.executable, cli, 'meteo'], capture_output=True, text=True, env=e)
assert r.stdout.startswith('0201D:'), r.stdout
r = subprocess.run([sys.executable, cli, 'marcadores', 'IM75IV'], capture_output=True, text=True, env=e)
assert 'GECE' in r.stdout and 'NAVTEX Tarifa' in r.stdout and '--aplicar' in r.stdout, r.stdout
assert subprocess.run([sys.executable, cli, 'locator', '37.9838', '-1.1280'], capture_output=True, text=True).stdout.strip() == 'IM97kx'
assert subprocess.run([sys.executable, cli, 'coordenadas', 'IM98'], capture_output=True, text=True).stdout.strip() == '38.500000 -1.000000'
shutil.rmtree(T)

# ------------------------------------------------------------------ 6. zona en install.sh
S = open(os.path.join(RAIZ, 'install.sh'), encoding='utf-8').read()
fn = lambda n: re.search(r'^%s\(\) \{.*?^\}' % n, S, re.S | re.M).group(0)      # noqa: E731
base = 'set -Eeuo pipefail\nKIT="%s"; FILES="$KIT/files"; LOCATOR_CACHE=/nonexistent\n' % RAIZ + \
       'fallo() { echo "FALLO $*"; exit 1; }; aviso() { echo "AVISO $*"; }\n' + '\n'.join(fn(x) for x in ('coords_ok', 'zona_locator', 'zona_selector'))
fin = '\nzona_locator\necho "LAT=$STATION_LAT LON=$STATION_LON LOC=$STATION_QTH_LOCATOR MET=${METEO_STATIONS:-} DER=${LOCATOR_DERIVADAS[*]:-}"'


def zona(vars_):
    r = subprocess.run(['bash', '-c', base + '\n' + vars_ + fin], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


rc, o = zona('STATION_LOCATOR=im97kx; STATION_LAT=0.0; STATION_LON=0.0; LOCATOR_CATALOG=data/locator/catalogo_es.json')
assert rc == 0 and 'LAT=37.979167 LON=-1.125000' in o, o
assert 'LOC=IM97KX' in o and 'DER=STATION_LAT STATION_LON METEO_STATIONS' in o and 'MET=7178I:Murcia' in o, o
rc, o = zona('STATION_LOCATOR=IM97kx; STATION_LAT=40.4; STATION_LON=-3.7; LOCATOR_CATALOG=""')
assert rc == 0 and 'LAT=40.4 LON=-3.7' in o and 'no caen en STATION_LOCATOR' in o and 'DER= ' not in o.split('DER=')[0], o
rc, o = zona('STATION_LOCATOR=""; STATION_LAT=41.39; STATION_LON=2.17; LOCATOR_CATALOG=data/locator/catalogo_es.json; METEO_STATIONS="X:manual"')
assert rc == 0 and 'LOC=JN11cj' in o and 'MET=0201D' in o, o
rc, o = zona('STATION_LOCATOR=""; STATION_LAT=41.39; STATION_LON=2.17; LOCATOR_CATALOG=data/locator/catalogo_es.json; METEO_STATIONS="X:manual"; LOCATOR_METEO=no')
assert rc == 0 and 'MET=X:manual' in o, o
rc, o = zona('STATION_LOCATOR=IM58kr; STATION_LAT=0; STATION_LON=0; LOCATOR_CATALOG=""')
assert rc == 0 and 'fuera de España' in o, o
# revisión v4.3: paso_meteo vuelve a llamar a zona_locator sin releer el env: las coordenadas siguen siendo «del locator»
r = subprocess.run(['bash', '-c', base + '\nSTATION_LOCATOR=IM97kx; STATION_LAT=0.0; STATION_LON=0.0; LOCATOR_CATALOG=data/locator/catalogo_es.json'
                    + '\nzona_locator\nzona_locator\necho "DER=${LOCATOR_DERIVADAS[*]} LAT=$STATION_LAT"'], capture_output=True, text=True)
assert 'DER=STATION_LAT STATION_LON METEO_STATIONS LAT=37.979167' in r.stdout, r.stdout + r.stderr
rc, o = zona('STATION_LOCATOR=XX99; LOCATOR_CATALOG=""')
assert rc != 0 and 'no es un locator Maidenhead' in o, o
rc, o = zona('STATION_LOCATOR=""; STATION_LAT=0.0; STATION_LON=0.0; LOCATOR_CATALOG=data/locator/catalogo_es.json')
assert rc == 0 and 'sin marcadores de zona' in o and 'LOC= ' in o, o
assert 'zona_selector --merge-existing "$OWRX_DATA/bookmarks.json" --kit "$FILES/openwebrx/bookmarks.json"' in S
assert 'METEO_STATIONS=$(sq "${METEO_STATIONS:-}")' in S, 'meteo.env entre comillas (nombres con espacios)'

# ------------------------------------------------------------------ 7. paso «configuracion» de punta a punta (Docker, Vigo)
T = tempfile.mkdtemp()
kit = os.path.join(T, 'kit')
os.makedirs(kit)
for d in ('files', 'data'):
    os.symlink(os.path.join(os.path.abspath(RAIZ), d), os.path.join(kit, d))
open(os.path.join(kit, 'bricohams.env'), 'w').write(open(os.path.join(RAIZ, 'bricohams.env.example'), encoding='utf-8').read()
                                                     + '\nSTATION_LOCATOR="IN52pf"\nLOCATOR_ONLINE="no"\nOWRX_BACKEND="docker"\nOWRX_DOCKER_DIR="%s/owrx-docker"\n' % T)
dd = os.path.join(T, 'owrx-docker')
os.makedirs(dd + '/var')
json.dump(KIT + [dict(mio, frequency=144612500)], open(dd + '/var/bookmarks.json', 'w'))   # (a la misma frecuencia que uno del kit, gana el kit: v4.1)
open(dd + '/var/users.json', 'w').write('[{"user": "admin"}]')
script = 'set -Eeuo pipefail\nKIT="%s"; FILES="$KIT/files"; ETC_BH="%s/etc"; LOCATOR_CACHE="%s/cache"; VARBH="%s/varbh"\n' % (kit, T, T, T) + \
    'PERFIL_IMPORTADO=/nonexistent; BACKUP=""; IMPORTAR=""; LOCATOR_CATALOG_PATH=""; STATION_QTH_LOCATOR=""; LOCATOR_DERIVADAS=()\n' + \
    'bien() { echo "BIEN $*"; }; aviso() { echo "AVISO $*"; }; fallo() { echo "FALLO $*"; exit 1; }; info() { echo "INFO $*"; }\n' + \
    'chown() { :; }; usuario_openwebrx() { :; }; owrx_owner() { :; }; owrx_control() { echo "CONTROL $*"; }; systemctl() { echo "systemctl $*"; }\n' + \
    r'install() { local a=("$@"); command install "${a[@]//\/var\/lib\/bricohams/$VARBH}"; }' + '\n' + \
    '\n'.join(fn(x) for x in ('si', 'sq', 'envl', 'coords_ok', 'zona_locator', 'zona_selector', 'cargar_env', 'instalar_env', 'paso_configuracion')) + \
    '\ncargar_env "$KIT/bricohams.env"\npaso_configuracion\n'
r = subprocess.run(['bash', '-c', script], capture_output=True, text=True)
assert r.returncode == 0, (r.stdout[-3000:], r.stderr[-3000:])
final = json.load(open(dd + '/var/bookmarks.json'))
auto = [b for b in final if '[AUTO-LOCATOR]' in b.get('description', '')]
assert any('LEVX' in b['name'] for b in auto) and any('Vigo' in b['name'] for b in auto), [b['name'] for b in auto]
assert 'Mi repetidor ED1ZZZ' in [b['name'] for b in final], 'lo tuyo se queda'
assert not any('Cartagena' in b['name'] or b['modulation'] == 'wfm' for b in final if b not in auto), 'kit de Murcia adaptado'
assert json.load(open(dd + '/var/settings.json'))['receiver_gps']['lat'] == 42.23     # v4.4: posición pública redondeada
etc = open(T + '/etc/bricohams.env', encoding='utf-8').read()
assert "STATION_QTH_LOCATOR='IN52PF'" in etc and "OWRX_HTDOCS='%s'" % dd in etc and "METEO_STATIONS='1496X:Vigo-O Castro" in etc, etc[-600:]
assert 'CONTROL restart' in r.stdout and 'Aeropuertos' in r.stdout and 'marcadores de la zona IN52PF' in r.stdout
shutil.rmtree(T)

print('OK test_locator_es: %d puntos de España (%d en la costa) con aeropuertos, AEMET y puertos; locator ida y vuelta; '
      'FM regional/local y AEMET en vivo con caché; kit de Murcia adaptado lejos de la Región de Murcia; bricohams-locator, zona del instalador y paso configuracion en Docker'
      % (cuadros, costa))
