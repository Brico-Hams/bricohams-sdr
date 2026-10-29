#!/usr/bin/env python3
"""Rellena settings.json.tmpl con bricohams.env.example y comprueba receptores,
perfiles, cobertura de bandas y el cambio de HF al SDRplay."""
import json, os, re, subprocess, sys, tempfile

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

SERIE = dict(re.findall(r'^(SERIAL_[A-Z0-9]+)="([^"]*)"', open(os.path.join(RAIZ, 'bricohams.env.example'), encoding='utf-8').read(), re.M))
assert all(SERIE.get(k) for k in ('SERIAL_HAT', 'SERIAL_MINI', 'SERIAL_V3')), SERIE

for sdrplay in (False, True):
    d = render(sdrplay)
    assert d['sdrs']['hl2']['enabled'] is False and 'remote' not in d['sdrs']['hl2']
    s = d['sdrs']
    assert d['receiver_name'].startswith('N0CALL')
    assert d['receiver_location'] == 'Mi QTH, ES'
    assert d['receiver_country'] == 'ES'
    assert d['photo_title'] == 'N0CALL · Receptor SDR'
    assert d['aprs_callsign'] == 'N0CALL'
    assert d['aprs_igate_enabled'] is False
    assert (s['sat']['device'], s['ham']['device'], s['multi']['device']) == (SERIE['SERIAL_HAT'], SERIE['SERIAL_MINI'], SERIE['SERIAL_V3']), s
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

# v5.5 · Hermes Lite 2: perfiles de 384 kHz como máximo, sin 6 m, banda de satélites de 10 m y HF fuera del V3
h = render(False, {'HF_HERMES': 'yes', 'HERMES_IP': '10.0.0.9', 'HERMES_GAIN': '30'})['sdrs']
hl = h['hl2']
assert hl['enabled'] is True and hl['type'] == 'hpsdr' and hl['remote'] == '10.0.0.9' and hl['rf_gain'] == 30
assert not [k for k in h['multi']['profiles'] if k.startswith('hf')], 'la HF del V3 debe quitarse con el HL2'
for pid, p in hl['profiles'].items():
    assert p['samp_rate'] in (48000, 96000, 192000, 384000) and p['center_freq'] + p['samp_rate'] / 2 < 38.4e6, pid
    assert abs(p['start_freq'] - p['center_freq']) < p['samp_rate'] * 0.45, pid
for pid, banda in (('hl160', '160'), ('hl80', '80'), ('hl60', '60'), ('hl40', '40'), ('hl30', '30'), ('hl20', '20'), ('hl17', '17'), ('hl12', '12')):
    lo, hi = BANDAS[banda]; c, m = hl['profiles'][pid]['center_freq'], hl['profiles'][pid]['samp_rate'] * 0.46   # 20 m: 350 kHz en 384
    assert c - m <= lo and c + m >= hi, pid
assert abs(hl['profiles']['hl10sat']['center_freq'] - 29.41e6) < 0.1e6 and hl['scheduler']['schedule']['day'] in hl['profiles']
print('OK test_render_settings (Hermes Lite 2): %d perfiles HF de 384 kHz, satélites de 10 m' % len(hl['profiles']))
assert render(False, {'CALLSIGN': 'EA5ABC', 'APRS_PASSCODE': '12345'})['aprs_igate_enabled'] is True
locator_settings = render(False, {'STATION_LOCATOR': 'IM98'})
assert locator_settings['receiver_gps'] == {'lat': 38.5, 'lon': -1.0}
fallo = subprocess.run([sys.executable, 'files/bin/bricohams-render-settings.py',
                        'files/openwebrx/settings.json.tmpl', tempfile.mktemp(suffix='.json')],
                       cwd=RAIZ, env={**os.environ, 'CALLSIGN': '', 'APRS_PASSCODE': '12345',
                                      'APRS_IGATE_ENABLE': 'yes'}, capture_output=True, text=True)
assert fallo.returncode != 0 and 'CALLSIGN propio' in fallo.stderr
# v4.3 · si STATION_LAT/LON están puestas mandan sobre el centro del locator (son más precisas)
precisas = render(False, {'STATION_LOCATOR': 'IN52', 'STATION_LAT': '42.22917', 'STATION_LON': '-8.70833', 'OWRX_GPS_DECIMALES': 'exacta'})
assert precisas['receiver_gps'] == {'lat': 42.22917, 'lon': -8.70833}, precisas['receiver_gps']
# v4.4 · por defecto la posición pública va redondeada a 2 decimales (~1 km): no se publica la casa
publica = render(False, {'STATION_LAT': '42.229172', 'STATION_LON': '-8.708331'})
assert publica['receiver_gps'] == {'lat': 42.23, 'lon': -8.71}, publica['receiver_gps']
print('OK test_render_settings: locator solo si faltan las coordenadas')
