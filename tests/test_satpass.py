#!/usr/bin/env python3
"""v4: pases de satélites (bricohams-satpass) comparados con Skyfield cuando está
instalado (en el PC de pruebas); si no, comprobaciones de coherencia."""
import importlib.machinery
import importlib.util
import json
import os

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
loader = importlib.machinery.SourceFileLoader('sp', os.path.join(RAIZ, 'files/bin/bricohams-satpass.py'))
spec = importlib.util.spec_from_loader('sp', loader)
sp = importlib.util.module_from_spec(spec)
loader.exec_module(sp)
if sp.Satrec is None:
    print('SKIP test_satpass: falta sgp4')
    raise SystemExit(0)

d = json.load(open(os.path.join(RAIZ, 'tests/datos/iss_omm.json')))
LAT, LON, ALT = 42.22917, -8.70833, 200
import calendar
t0 = calendar.timegm((2026, 10, 3, 12, 0, 0))
sat = sp.satrec_de_omm(d['omm'])
ps = sp.pases(sat, LAT, LON, ALT, t0, horas=24, min_el=0)
assert ps, 'sin pases de la ISS en 24 h'
for p in ps:
    assert 0 < p['duracion_s'] < 900 and 0 <= p['max_el'] <= 90 and p['aos'] < p['t_max'] < p['los']

try:
    from skyfield.api import EarthSatellite, load, wgs84
except ImportError:
    print('OK test_satpass: %d pases de la ISS en 24 h (sin Skyfield para comparar)' % len(ps))
    raise SystemExit(0)
ts = load.timescale()
es = EarthSatellite(d['tle'][0], d['tle'][1], 'ISS', ts)
obs = wgs84.latlon(LAT, LON, ALT)
t, ev = es.find_events(obs, ts.from_datetime(__import__('datetime').datetime.fromtimestamp(t0, __import__('datetime').timezone.utc)),
                       ts.from_datetime(__import__('datetime').datetime.fromtimestamp(t0 + 86400, __import__('datetime').timezone.utc)),
                       altitude_degrees=0.0)
aos_sky = [ti.utc_datetime().timestamp() for ti, e in zip(t, ev) if e == 0]
max_sky = [(ti.utc_datetime().timestamp(), (es - obs).at(ti).altaz()[0].degrees) for ti, e in zip(t, ev) if e == 1]
assert len(aos_sky) == len([p for p in ps]), (len(aos_sky), len(ps))
for p, a, (tm, mx) in zip(ps, aos_sky, max_sky):
    assert abs(p['aos'] - a) < 10, (p['aos'], a)                 # AOS a menos de 10 s
    assert abs(p['max_el'] - mx) < 1.0, (p['max_el'], mx)        # elevación máxima a menos de 1°
print('OK test_satpass: %d pases de la ISS iguales a Skyfield (AOS ±10 s, elevación ±1°)' % len(ps))
