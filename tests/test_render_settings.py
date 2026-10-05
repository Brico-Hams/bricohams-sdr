#!/usr/bin/env python3
"""Rellena settings.json.tmpl con bricohams.env.example y comprueba receptores,
perfiles, cobertura de bandas y el cambio de HF al SDRplay."""
import json, os, subprocess, sys, tempfile

AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.join(AQUI, '..')
BANDAS = {'160': (1.81e6, 2.0e6), '80': (3.5e6, 3.8e6), '60': (5.3515e6, 5.3665e6), '40': (7.0e6, 7.2e6),
          '30': (10.1e6, 10.15e6), '20': (14.0e6, 14.35e6), '17': (18.068e6, 18.168e6), '15': (21.0e6, 21.45e6),
          '12': (24.89e6, 24.99e6), '10': (28.0e6, 29.7e6), '6': (50.0e6, 52.0e6)}

def render(sdrplay, overrides=None):
    env = dict(os.environ)
    out = subprocess.run(['bash', '-c', 'set -a; . bricohams.env.example; set +a; env -0'], cwd=RAIZ, capture_output=True, check=True).stdout
    env.update(dict(x.split('=', 1) for x in out.decode().split('\0') if '=' in x))
    env['HF_SDRPLAY'] = 'yes' if sdrplay else 'no'
    env.update(overrides or {})
    dst = tempfile.mktemp(suffix='.json')
    subprocess.run([sys.executable, 'files/bin/bricohams-render-settings.py', 'files/openwebrx/settings.json.tmpl', dst], cwd=RAIZ, env=env, check=True)
    return json.load(open(dst))

for sdrplay in (False, True):
    d = render(sdrplay)
    s = d['sdrs']
    assert d['receiver_name'].startswith('N0CALL')
    assert d['receiver_location'] == 'Mi QTH, ES'
    assert d['receiver_country'] == 'ES'
    assert d['photo_title'] == 'N0CALL · Receptor SDR'
    assert d['aprs_callsign'] == 'N0CALL'
    assert d['aprs_igate_enabled'] is False
    assert s['sat']['device'] == '00000101' and s['ham']['device'] == '00000102' and s['multi']['device'] == '00000103'
    assert s['hf']['enabled'] is sdrplay
    hfdev = s['hf'] if sdrplay else s['multi']
    hf = {k: v for k, v in hfdev['profiles'].items() if k[:2] in ('hf', 'sp')}
    assert len(hf) == 12, len(hf)
    for pid, p in hf.items():
        banda = pid[2:]
        if banda == '11':
            continue
        lo, hi = BANDAS[banda]; c, m = p['center_freq'], p['samp_rate'] * 0.45
        assert c - m <= lo and c + m >= hi, (pid, c, p['samp_rate'])
        if not sdrplay:
            assert p['direct_sampling'] == (2 if c < 24e6 else 0), pid
            sr = p['samp_rate']; assert 900001 <= sr <= 3200000, pid
    assert '_bh_hf_rtl' not in json.dumps(d) and '__' not in json.dumps(d)
    print('OK test_render_settings (HF en %s): %d perfiles' % ('SDRplay' if sdrplay else 'V3', sum(len(x['profiles']) for x in s.values())))

assert render(False, {'CALLSIGN': 'EA5ABC', 'APRS_PASSCODE': '12345'})['aprs_igate_enabled'] is True
locator_settings = render(False, {'STATION_LOCATOR': 'IM98'})
assert locator_settings['receiver_gps'] == {'lat': 38.5, 'lon': -1.0}
fallo = subprocess.run([sys.executable, 'files/bin/bricohams-render-settings.py',
                        'files/openwebrx/settings.json.tmpl', tempfile.mktemp(suffix='.json')],
                       cwd=RAIZ, env={**os.environ, 'CALLSIGN': '', 'APRS_PASSCODE': '12345',
                                      'APRS_IGATE_ENABLE': 'yes'}, capture_output=True, text=True)
assert fallo.returncode != 0 and 'CALLSIGN propio' in fallo.stderr
# v4.3 · si STATION_LAT/LON están puestas mandan sobre el centro del locator (son más precisas)
precisas = render(False, {'STATION_LOCATOR': 'IM98', 'STATION_LAT': '0.0', 'STATION_LON': '0.0'})
assert precisas['receiver_gps'] == {'lat': 0.0, 'lon': 0.0}, precisas['receiver_gps']
print('OK test_render_settings: locator solo si faltan las coordenadas')
