#!/usr/bin/env python3
"""bricohams-rotor: sigue los pases que graba satrec, aparca fuera de pase y con viento, y no filtra la clave."""
import calendar
import importlib.machinery
import importlib.util
import json
import os
import tempfile
from datetime import datetime, timezone

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
os.environ['SATPASS_PY'] = os.path.join(RAIZ, 'files/bin/bricohams-satpass.py')


def cargar(nombre, rel):
    loader = importlib.machinery.SourceFileLoader(nombre, os.path.join(RAIZ, rel))
    spec = importlib.util.spec_from_loader(nombre, loader)
    m = importlib.util.module_from_spec(spec)
    loader.exec_module(m)
    return m


sr = cargar('sr', 'files/bin/bricohams-satrec.py')
ro = cargar('ro', 'files/bin/bricohams-rotor.py')
if not importlib.util.find_spec('sgp4'):
    print('SKIP test_rotor: falta python3-sgp4')
    raise SystemExit(0)
sp = sr._satpass()

omm = json.load(open(os.path.join(RAIZ, 'tests/datos/iss_omm.json')))['omm']
pp = sp.pases(sp.satrec_de_omm(omm), 38.0, -1.0, 200, calendar.timegm((2026, 10, 3, 12, 0, 0)), min_el=30)
assert pp, 'sin pase alto de la ISS'
p0 = pp[0]
iso = lambda t: datetime.fromtimestamp(t, timezone.utc).isoformat()

with tempfile.TemporaryDirectory() as d:
    pases = os.path.join(d, 'pases.json')
    json.dump({'pases': [dict(p0, nombre='ISS', norad=25544, hz=145800000, modo='nfm', perfil='sat|sat2m', omm=omm),
                         dict(p0, nombre='METEOR-M2-4', norad=59051, aos=p0['los'] + 900, los=p0['los'] + 1500,
                              hz=137900000, modo='nfm', perfil='sat|meteor', omm=omm)]}, open(pases, 'w'))
    clave = os.path.join(d, 'rotor.clave')
    open(clave, 'w').write('clave-de-prueba-123456\n')
    meteo = os.path.join(d, 'meteo.json')
    env = {'STATION_LAT': '38.0', 'STATION_LON': '-1.0', 'STATION_ASL': '200', 'SATREC_PASES': pases,
           'SATREC_MIN_EL': '20', 'ROTOR_URL': 'http://rotor.test/', 'ROTOR_CLAVE_FICHERO': clave, 'METEO_JSON': meteo}
    cfg = ro.cfg_desde_env(sr, env)
    assert cfg['url'] == 'http://rotor.test' and cfg['parque'] == (0.0, 90.0) and cfg['viento_max'] == 36

    enviados, t = [], [0]

    def post(url, campos):
        enviados.append((url, dict(campos)))
        return 200, '{"ok":1}'
    r = ro.Rotor(cfg, sr, sp, post=post, reloj=lambda: t[0])

    def mueve():
        n = len(enviados)
        r.paso()
        return None if len(enviados) == n else (float(enviados[-1][1]['az']), float(enviados[-1][1]['el']))

    # sin meteo.json: lejos del pase aparca una sola vez
    t[0] = p0['aos'] - 3600
    assert mueve() == (0.0, 90.0) and mueve() is None and 'sin pase' in r.estado
    assert enviados[0][0] == 'http://rotor.test/api/goto_true' and enviados[0][1]['key'] == 'clave-de-prueba-123456'

    # 2 min antes del AOS: azimut de entrada, elevación 0
    t[0] = p0['aos'] - 100
    az, el = mueve()
    assert abs(az - p0['az_aos']) < 3 and el == 0.0, (az, el, p0['az_aos'])
    assert 'esperando' in r.estado

    # en el máximo: la elevación del pase
    t[0] = p0['t_max']
    az, el = mueve()
    assert abs(el - p0['max_el']) < 0.5 and r.estado == 'siguiendo ISS', (el, p0['max_el'])

    # racha fuerte: aparca; al bajar de 0,8 × máximo vuelve a seguir
    json.dump({'updated': iso(t[0] - 600), 'model': {'current': {'wind_speed_10m': 20, 'wind_gusts_10m': 40}}}, open(meteo, 'w'))
    t[0] += 10
    assert mueve() == (0.0, 90.0) and 'racha 40' in r.estado, r.estado
    json.dump({'updated': iso(t[0] - 600), 'model': {'current': {'wind_gusts_10m': 32}}}, open(meteo, 'w'))
    assert mueve() is None and 'aparcado' in r.estado                       # 32 ≥ 0,8 × 36: sigue aparcado
    json.dump({'updated': iso(t[0] - 600), 'model': {'current': {'wind_gusts_10m': 20}}}, open(meteo, 'w'))
    assert mueve()[1] > 20 and r.estado == 'siguiendo ISS'

    # dato meteorológico viejo: aparca (no se sigue a ciegas)
    json.dump({'updated': iso(t[0] - 4 * 3600), 'model': {'current': {'wind_gusts_10m': 5}}}, open(meteo, 'w'))
    assert mueve() == (0.0, 90.0) and 'más de 3 h' in r.estado
    os.remove(meteo)

    # METEOR: no se sigue con la yagi (va por la QFH fija)
    t[0] = p0['los'] + 1200
    mueve()
    assert r.ultimo == (0.0, 90.0) and 'sin pase' in r.estado

    # rotor que rechaza la clave: error, y la clave no sale en el mensaje
    r.ultimo = None
    r.post = lambda url, campos: (403, 'API key required')
    try:
        r.paso()
        raise AssertionError('debía fallar')
    except OSError as e:
        assert '403' in str(e) and 'clave-de-prueba' not in str(e)

print('OK test_rotor: preposición al AOS, seguimiento SGP4, METEOR fuera, aparcado por viento con histéresis y dato viejo, clave fuera del registro')
