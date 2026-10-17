#!/usr/bin/env python3
"""v5.0 · «Clima en red»: instalador, unidades systemd, página del portal y formulario AMSAT encajan entre sí."""
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def leer(*r):
    return open(os.path.join(RAIZ, *r), encoding='utf-8').read()


def funcion(src, nombre):
    m = re.search(r'^%s\(\) \{\n(.*?)^\}\n' % nombre, src, re.S | re.M)
    assert m, nombre
    return m.group(1)


def main():
    ins = leer('install.sh')
    meteo, sat, web, plug = (funcion(ins, 'paso_' + p) for p in ('meteo', 'satelites', 'web', 'plugins'))

    # servicios: instalados desde el kit, como openwebrx, sin PrivateTmp (enlaces de «Files» en /tmp)
    for paso, bins in ((meteo, ('bricohams-wx-red', 'bricohams-wspr')), (sat, ('bricohams-satrec',))):
        for b in bins:
            assert 'install -m 755 "$FILES/bin/%s.py" /usr/local/bin/%s' % (b, b) in paso, b
    for u in ('bricohams-wx-red.service', 'bricohams-wspr.service', 'bricohams-wspr.timer', 'bricohams-satrec.service'):
        bloque = re.search(r'/etc/systemd/system/%s <<.?EOF.?\n(.*?)\nEOF' % re.escape(u), ins, re.S)
        assert bloque, u
        cuerpo = bloque.group(1)
        assert 'PrivateTmp' not in cuerpo and 'DynamicUser' not in cuerpo, u
        # passcode y claves nunca en las unidades (systemctl show las enseña a cualquiera)
        assert not re.search(r'PASSCODE|_KEY|TOKEN|PASS=', cuerpo), 'secretos en ' + u
        if u.endswith('.service'):
            assert 'User=openwebrx' in cuerpo, u
    assert 'StateDirectory=bricohams/satelites' in sat and 'apt_i lame' in sat
    assert 'AMSAT_REPORT=${AMSAT_REPORT:-no}' in sat, 'AMSAT automático debe ir apagado por defecto'
    assert 'WXRED_OUT=${HTDOCS}/plugins/receiver/meteo/wx-red.json' in meteo
    assert 'WSPR_OUT=${HTDOCS}/plugins/receiver/meteo/wspr.json' in meteo
    assert 'OWRX_SETTINGS_FILE=${OWRX_DATA}/settings.json' in meteo
    assert re.search(r'si "\$\{WX_APRS:-no\}" \|\| wxcall=""', meteo), 'sin WX_APRS no hay estación propia que destacar'

    # una reinstalación no borra los datos que generan los servicios
    for f in ('meteo/wx-red.json', 'meteo/wspr.json', 'satelites/grabaciones.json', 'satelites/pases.ics'):
        assert "--exclude '%s'" % f in plug, f

    # portal: página copiada con sus sustituciones y tarjeta en el índice
    assert '"$FILES/web/clima.html" >/var/www/bricohams/clima.html' in web
    assert 'href="/bricohams/clima.html"' in leer('files', 'web', 'index.html.tmpl')
    assert '/bricohams/clima.html' in leer('files', 'htdocs', 'plugins', 'receiver', 'meteo', 'meteo.js')

    html = leer('files', 'web', 'clima.html')
    for j in ('meteo/sensor.json', 'meteo/wx-red.json', 'meteo/wspr.json', 'satelites/grabaciones.json'):
        assert "json('%s')" % j in html, j
    assert "var B = '/static/plugins/receiver/'" in html
    assert 'href="/static/plugins/receiver/satelites/pases.ics"' in html
    assert '__OPERADOR__' in html and '__FUENTES__' in html
    assert 'background:#fff' not in html.replace(' ', '') and '--bg:#141518' in html, 'tema oscuro: nada de fondo blanco'
    assert html.count('esc(') > 30, 'todo lo que llega de APRS/WSPR debe escaparse'

    # el formulario de la página manda exactamente los campos que prepara el grabador
    sp = importlib.util.spec_from_file_location('satrec', os.path.join(RAIZ, 'files', 'bin', 'bricohams-satrec.py'))
    sr = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(sr)
    cfg = sr.cfg_desde_env({'CALLSIGN': 'DL0XYZ', 'STATION_LAT': '48.14', 'STATION_LON': '11.58'})
    f = sr.informe_amsat({'amsat': 'SO-50_[FM]', 'estado': 'grabado', 'oido': True, 'aos': 1700000000}, cfg)
    enviados = set(re.findall(r"'(Sat[A-Za-z]+)'", re.search(r"function amsat\(f\).*?\n    \}", html, re.S).group(0)))
    enviados |= {'SatReport', 'SatSubmit'}
    assert set(f) | {'SatSubmit'} == enviados, (sorted(f), sorted(enviados))
    assert 'action="https://www.amsat.org/status/submit.php"' in html and sr.AMSAT_URL == 'https://www.amsat.org/status/submit.php'
    assert "'Heard', 'Telemetry Only', 'Not Heard'" in html

    # .env.example documenta las claves nuevas
    ej = leer('bricohams.env.example')
    for k in ('SATREC_ENABLE', 'SATREC_MIN_EL', 'SATREC_EXCLUIR', 'SATREC_METEOR', 'SATREC_DIAS', 'SATREC_MAX_MB',
              'AMSAT_REPORT', 'WSPR_CALLSIGN', 'WXRED_ENABLE', 'WXRED_RADIO_KM'):
        assert re.search(r'^%s=' % k, ej, re.M), k
    assert re.search(r'^AMSAT_REPORT="no"', ej, re.M)

    # JavaScript de la página sin errores de sintaxis (si hay node)
    if shutil.which('node'):
        js = re.search(r'<script>\n(.*?)</script>', html, re.S).group(1)
        with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as t:
            t.write(js)
        try:
            r = subprocess.run(['node', '--check', t.name], capture_output=True, text=True)
            assert r.returncode == 0, r.stderr
        finally:
            os.unlink(t.name)
    print('OK test_clima_web: servicios WX-red/WSPR/satrec, exclusiones, portal oscuro, formulario AMSAT = grabador, .env.example')


if __name__ == '__main__':
    sys.exit(main())
