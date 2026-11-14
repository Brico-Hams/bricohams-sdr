#!/usr/bin/env python3
"""The receiver header always says who we are and survives re-rendering settings.json."""
import json, os, subprocess, sys, tempfile

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


def render(dst, extra=None):
    out = subprocess.run(['bash', '-c', 'set -a; . bricohams.env.example; set +a; env -0'],
                         cwd=RAIZ, capture_output=True, check=True).stdout
    env = dict(os.environ)
    env.update(dict(x.split('=', 1) for x in out.decode().split('\0') if '=' in x))
    env.update(extra or {})
    subprocess.run([sys.executable, 'files/bin/bricohams-render-settings.py', 'files/openwebrx/settings.json.tmpl', dst],
                   cwd=RAIZ, env=env, check=True, capture_output=True)
    return json.load(open(dst, encoding='utf-8'))


def nuevo():
    return tempfile.mktemp(suffix='.json')


def poner(dst, **kv):
    d = json.load(open(dst, encoding='utf-8'))
    d.update(kv)
    json.dump(d, open(dst, 'w', encoding='utf-8'))


# 1 · default: identity of the station and of BricoHams, with link
dst = nuevo()
d = render(dst)
assert 'BricoHams' in d['photo_desc'] and 'https://bricohams.org' in d['photo_desc'], d['photo_desc']
assert d['photo_desc'].startswith('Receptor SDR multiusuario de N0CALL')

# 2 · the generic text of older kits is upgraded, not kept
poner(dst, photo_desc='Receptor SDR multiusuario de N0CALL en Lorquí (ES).', photo_title='N0CALL · Receptor SDR')
assert 'BricoHams' in render(dst)['photo_desc']

# 3 · a text edited in the admin panel survives a new install/update
poner(dst, photo_desc='<b>Quiénes somos</b>: texto propio', photo_title='Mi estación')
d = render(dst)
assert d['photo_desc'] == '<b>Quiénes somos</b>: texto propio' and d['photo_title'] == 'Mi estación', d

# 4 · bricohams.env wins over everything
d = render(dst, {'OWRX_PHOTO_DESC': 'Desde env', 'OWRX_PHOTO_TITLE': 'Título env'})
assert (d['photo_desc'], d['photo_title']) == ('Desde env', 'Título env'), d

# 5 · callsign/QTH are escaped in the HTML default
d = render(nuevo(), {'STATION_QTH': '<script>'})
assert '<script>' not in d['photo_desc'] and '&lt;script&gt;' in d['photo_desc']

print('OK test_cabecera_receptor')
