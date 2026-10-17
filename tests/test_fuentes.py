#!/usr/bin/env python3
"""v5.0 · «¿Quieres una estación como esta?»: enlace a las fuentes del kit (FUENTES_URL) en el
portal y en el receptor. Vacío o no https = no se muestra; nunca rompe el HTML ni el JS."""
import os
import re
import shutil
import subprocess

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))


def leer(*ruta):
    with open(os.path.join(RAIZ, *ruta), encoding='utf-8') as f:
        return f.read()


inst = leer('install.sh')
version = leer('VERSION').strip()
assert re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', version), 'VERSION debe usar major.minor.patch'
assert ('v' + version) in leer('README.md') and ('## v' + version + ' · ') in leer('CHANGELOG.md')
env = leer('bricohams.env.example')
portal = leer('files/web/index.html.tmpl')
init_js = leer('files/htdocs/plugins/receiver/init.js')
bh_js = leer('files/htdocs/plugins/receiver/bricohams/bricohams.js')

m = re.search(r'^FUENTES_URL="([^"]*)"', env, re.M)
assert m, 'FUENTES_URL documentada en bricohams.env.example'
defecto = re.search(r'FUENTES_URL-([^}]*)\}', inst).group(1)
assert m.group(1) == defecto, 'el ejemplo y el instalador usan el mismo valor por defecto'
assert defecto == '' or defecto.startswith('https://')

# portal: una tarjeta que se borra entera si no hay enlace
lineas = [l for l in portal.splitlines() if '__FUENTES__' in l]
assert len(lineas) == 1 and 'rel="noopener"' in lineas[0] and '¿Quieres una estación como esta?' in lineas[0]
assert '-e "$fsed" "$FILES/web/index.html.tmpl"' in inst and "fsed='/__FUENTES__/d'" in inst
# receptor: init.js recibe la URL y bricohams.js crea el botón solo con https
assert "fuentes: '__FUENTES__'" in init_js and '-e "s#__FUENTES__#$(fuentes_url)#g" "$R/init.js"' in inst
assert "getElementById('bricohams-gh')" in bh_js and 'textContent' in bh_js and 'innerHTML = FU' not in bh_js
assert re.search(r"/\^https:.*\.test\(FU\)", bh_js)

# la función de bash: valores por defecto, vacío, http y caracteres peligrosos
bash = shutil.which('bash')
if bash and os.name != 'nt':
    fn = re.search(r'^fuentes_url\(\) \{.*?^\}', inst, re.M | re.S).group(0)
    casos = [(None, defecto), ('', ''), ('http://x', ''), ('https://a/b', 'https://a/b'),
             ('https://x/a?b=1&c=2#f', r'https://x/a?b=1\&c=2%23f'), ('https://x/\'a"<b>', 'https://x/ab')]
    for valor, esperado in casos:
        e = dict(os.environ)
        e.pop('FUENTES_URL', None)
        if valor is not None:
            e['FUENTES_URL'] = valor
        r = subprocess.run([bash, '-c', fn + '\nfuentes_url'], env=e, capture_output=True, text=True, check=True)
        assert r.stdout == esperado, (valor, r.stdout, esperado)

print('OK test_fuentes: «¿Quieres una estación como esta?» en portal y receptor, configurable y sin inyección')
