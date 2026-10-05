#!/usr/bin/env python3
"""bricohams-meteo con respuestas simuladas de AEMET (una estación con 404) y Open-Meteo."""
import importlib.util, json, os, tempfile
from datetime import datetime, timedelta, timezone

AQUI = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('m', os.path.join(AQUI, '..', 'files', 'bin', 'bricohams-meteo.py'))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
now = datetime(2026, 10, 4, 6, 0, tzinfo=timezone.utc)
rows = [{"idema": "TEST1", "lon": -3.04, "lat": 40.04, "alt": 95.0, "ubi": "SAMPLE",
         "fint": (now - timedelta(hours=23 - h)).strftime('%Y-%m-%dT%H:%M:%S+0000'),
         "prec": 0.2 if h == 5 else 0.0, "vmax": 6.1, "vv": 2.3, "dv": 120.0, "pres": 1003.4, "hr": 60 + h,
         "pres_nmar": 1014.2, "tamin": 15 + h * 0.3, "ta": 15.5 + h * 0.3, "tamax": 16 + h * 0.3} for h in range(24)]

def fake(url, headers=None, timeout=25):
    if '/opendata/api/' in url:
        if url.endswith('TEST2'):
            return json.dumps({"descripcion": "No hay datos", "estado": 404})
        return json.dumps({"estado": 200, "datos": "https://opendata.aemet.es/opendata/sh/x"})
    if '/opendata/sh/' in url:
        return json.dumps(rows)
    return json.dumps({"current": {"temperature_2m": 21.3, "weather_code": 2},
                       "daily": {"time": ["2026-10-04"], "weather_code": [2], "temperature_2m_max": [27],
                                 "temperature_2m_min": [15], "precipitation_probability_max": [5], "sunrise": ["x"], "sunset": ["y"]}})

m.http_get = fake; m.time.sleep = lambda s: None
out = tempfile.mktemp(suffix='.json')
os.environ.update({'AEMET_API_KEY': 'x', 'METEO_STATIONS': 'TEST1:Sample,TEST2:Offline', 'METEO_OUT': out,
                   'STATION_LAT': '40.0', 'STATION_LON': '-3.0'})
assert m.main() == 0
d = json.load(open(out)); a = d['stations'][0]
assert a['name'] == 'Sample' and a['dist_km'] == 5.6 and a['vv_kmh'] == 8.3 and a['prec_24h'] == 0.2 and len(a['history']) == 24
assert 'error' in d['stations'][1] and d['model']['current']['temperature_2m'] == 21.3
print('OK test_meteo: Sample %.1f °C a %.1f km, Offline con error controlado, modelo Open-Meteo' % (a['ta'], a['dist_km']))
