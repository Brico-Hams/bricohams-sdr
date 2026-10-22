#!/usr/bin/env python3
"""v5.0 · Políticas y cookies, idioma ES/EN, logo BricoHams en todas las páginas y mapa con
ADS-B/AIS de recepción propia (sin webs externas), todo por 443 con el 8073 solo en local."""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import tempfile

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
PLUG = os.path.join(RAIZ, 'files/htdocs/plugins/receiver')


def leer(*ruta):
    with open(os.path.join(RAIZ, *ruta), encoding='utf-8') as f:
        return f.read()


politicas = leer('files/web/politicas.html')
privacidad = leer('files/web/privacidad.html')
portal = leer('files/web/index.html.tmpl')
instalador = leer('install.sh')
init_js = leer('files/htdocs/plugins/receiver/init.js')
env = leer('bricohams.env.example')
pruebas = leer('tests/run_tests.sh')
rutas = leer('files/nginx/bricohams-sdr-rutas.conf')
consent_js = leer('files/htdocs/plugins/receiver/consentimiento/consentimiento.js')
idioma_js = leer('files/htdocs/plugins/receiver/idioma/idioma.js')
marca_js = leer('files/htdocs/plugins/receiver/marca/marca.js')
ident_js = leer('files/htdocs/plugins/receiver/identificacion/identificacion.js')
live_js = leer('files/htdocs/plugins/map/bricohams_live/bricohams_live.js')
api_py = leer('files/bin/bricohams-api.py')
GENERICO = '__QTH__' in privacidad

# --- Sin webs externas: el módulo WEB ya no existe -------------------------------------
assert not os.path.exists(os.path.join(PLUG, 'externos')), 'el módulo WEB (externos) se retiró en v5.0'
for nombre, texto in (('politicas', politicas), ('privacidad', privacidad), ('init.js', init_js), ('env', env),
                      ('install.sh', instalador), ('consentimiento', consent_js), ('idioma', idioma_js), ('mapa', live_js)):
    for prohibido in ('astroradio', 'ea3kz', 'externos_config', 'EXTERNOS_ENABLE', 'bh-externos'):
        assert prohibido.lower() not in texto.lower(), (nombre, prohibido)

# --- Página de políticas ---------------------------------------------------------
for marca in ('__OPERADOR__', '__CONTACTO__', '__DIAS__', 'id="seguridad"', 'id="datos"', 'id="cookies"',
              'id="mapa"', 'bh_consent', 'owrx-session', 'bh_idioma', '/bricohams/privacidad.html',
              'map.flights', 'Planespotters', 'HSTS', '8073', 'esta estación con sus propias antenas'):
    assert marca in politicas, marca
assert "location.href = '/#cookies'" in politicas
assert 'fotos de los aviones' in privacidad and 'recibe la propia estación' in privacidad
assert '/bricohams/politicas.html' in privacidad and '/bricohams/politicas.html' in portal
assert ':8073' not in portal and 'href="/map"' in portal, 'el portal ya no enlaza al 8073'
if GENERICO:
    for texto in (politicas, init_js, consent_js, idioma_js, marca_js, live_js):
        assert 'EA5' + 'KAO' not in texto and 'Lorq' + 'uí' not in texto
    assert '__QTH__' in politicas
    assert re.search(r'^sed_esc\(\) \{', instalador, re.M), 'el genérico usa sed_esc: debe estar definida'

# --- Instalador y configuración ----------------------------------------------------
assert '"$FILES/web/politicas.html" >/var/www/bricohams/politicas.html' in instalador
for nombre in ('consentimiento', 'idioma', 'marca'):
    assert re.search(r'receiver/\{[^}]*\b' + nombre + r'\b[^}]*\}/\*\.js', pruebas), nombre
assert not re.search(r'receiver/\{[^}]*\bexternos\b', pruebas)
assert 'python3 tests/test_politicas_mapa_local.py' in pruebas
assert '"usage_policy_url": "/bricohams/politicas.html"' in leer('files/openwebrx/settings.json.tmpl'), 'el aviso de OpenWebRX+ debe usar la politica propia'

# --- init.js: configuración y orden de carga -----------------------------------------
assert "politicas: BH_WEB + '/bricohams/politicas.html'" in init_js
# v5.1 · por el :8073 directo las páginas /bricohams/ irían a OpenWebRX+ (404): van a https://<host>/
assert "const BH_DOM = /^[a-z0-9.-]+$/i.test('__SSL_DOMAIN__') ? '__SSL_DOMAIN__' : '';" in init_js
assert "const BH_WEB = location.port ? ('__SSL_MODO__' === 'no' ? 'http://' + location.hostname : 'https://' + (BH_DOM || location.hostname)) : '';" in init_js
assert '-e "s#__SSL_DOMAIN__#${SSL_DOMAIN:-}#g"' in instalador, 'por IP el certificado no vale: enlazar al dominio'
assert init_js.index('const BH_WEB') < init_js.index('/bricohams/privacidad.html')
assert not re.search(r"(?<!BH_WEB \+ )'/bricohams/(privacidad|politicas)\.html'", init_js), 'enlace sin BH_WEB'
assert "url: BH_WEB + '/bricohams/'" in init_js
assert "endpoint: '/bricohams/api/oyentes'" in init_js, 'la API sigue relativa (mismo origen)'
assert '-e "s#__SSL_MODO__#${SSL_MODO:-todo}#"' in instalador
carga = re.search(r"for \(const name of \[([^\]]+)\]\)", init_js).group(1)
orden = re.findall(r"'(\w+)'", carga)
for nombre in ('idioma', 'marca', 'consentimiento', 'identificacion'):
    assert nombre in orden, nombre
assert 'externos' not in orden
assert orden.index('idioma') < orden.index('consentimiento') < orden.index('identificacion')

# --- Plugins -----------------------------------------------------------------------
assert 'Plugins.consentimiento.listo' in ident_js, 'la bienvenida espera al aviso de cookies'
assert 'fotos de aviones' in consent_js and 'recepción local' in consent_js
assert "'bh_idioma'" in idioma_js and "'Settings': 'Ajustes'" in idioma_js
assert "static/plugins/receiver/marca/bricohams-logo.png" in marca_js and '.webrx-top-logo' in marca_js
assert '#openwebrx-bookmarks-container .bookmark' in marca_js and 'color:#111 !important' in marca_js, 'etiquetas legibles'
with open(os.path.join(PLUG, 'marca/bricohams-logo.png'), 'rb') as f:
    assert f.read(8) == b'\x89PNG\r\n\x1a\n'

# --- Logo BricoHams también en /map y /settings (nginx sub_filter) --------------------
sub = re.search(r"sub_filter '([^']+)' '([^']+)';", rutas)
assert sub, 'falta el sub_filter del logo'
assert sub.group(1) == '<a href="https://www.openwebrx.de/" target="_blank"><svg viewBox="0 0 591 100" class="webrx-top-logo">'
assert '/static/plugins/receiver/marca/bricohams-logo.png' in sub.group(2) and 'bh-marca-logo' in sub.group(2)
assert sub.group(2).endswith('<svg viewBox="0 0 591 100" style="display:none">'), 'el resto del SVG original queda oculto'
assert 'proxy_set_header Accept-Encoding "";' in rutas, 'sub_filter necesita HTML sin comprimir'
assert "webrx-top-logo:not(.bh-marca-logo)" in live_js, 'el mapa cambia el logo también sin nginx'

# --- ADS-B local: tar1090 servido por nginx -------------------------------------------
assert 'include /etc/nginx/snippets/bricohams-tar1090.conf;' in rutas and '8504' not in rutas.split('include /etc/nginx/snippets/bricohams-tar1090.conf;')[1]
assert 'install -m 644 /usr/local/share/tar1090/nginx-tar1090.conf /etc/nginx/snippets/bricohams-tar1090.conf' in instalador

# --- Solo 443: SSL_MODO=todo y OpenWebRX+ en 127.0.0.1 ----------------------------------
assert re.search(r'^SSL_MODO="todo"', env, re.M) and re.search(r'^OWRX_SOLO_LOCAL="yes"', env, re.M)
assert re.search(r'^BLINDAJE_8073="cerrado"', env, re.M)
assert "printf '[web]\\nbind_address = 127.0.0.1\\n' >\"$OWRX_ETC/openwebrx.conf.d/22-solo-local.conf\"" in instalador
assert 'modo=${SSL_MODO:-todo}' in instalador
blindaje = leer('files/bin/bricohams-blindaje')
assert 'cerrado) ;;' in blindaje

# --- AIS local: instalador, API y capa del mapa ----------------------------------------
assert re.search(r'^AIS_ENABLE="no"', env, re.M) and re.search(r'^AIS_SDR_SERIAL=""', env, re.M)
assert re.search(r'^PASOS=\(.*\badsb ais\b', instalador, re.M)
assert re.search(r'^paso_ais\(\) \{', instalador, re.M)
assert '-N 8100 IP_BIND 127.0.0.1' in instalador and 'aiscatcher-install -p --no-systemd' in instalador
assert 'envl AIS_ENABLE "${AIS_ENABLE:-no}"' in instalador
assert "fetch('bricohams/api/barcos'" in live_js and "'AIS local (AIS-catcher)'" in live_js
assert 'if (response.status === 404) return false;' in live_js, 'sin AIS instalado el mapa deja de preguntar'
assert 'function tercerosAceptados()' in live_js, 'las fotos de aviones esperan al consentimiento'
assert "'/bricohams/api/barcos'" in api_py

spec = importlib.util.spec_from_loader('bh_api', loader=None)
api = importlib.util.module_from_spec(spec)
exec(compile(api_py, 'bricohams-api.py', 'exec'), api.__dict__)
r = api.barcos({'ships': [
    {'mmsi': 224123456, 'lat': 37.6, 'lon': -0.98, 'last_signal': 12, 'speed': 11.2, 'cog': 87.5, 'heading': 88,
     'shipname': 'PUERTO <b>CARTAGENA</b>\x07', 'callsign': 'EA1234', 'destination': 'VALENCIA', 'shiptype': 70},
    {'mmsi': 224000001, 'lat': None, 'lon': None, 'last_signal': 3},
    {'mmsi': 224000002, 'lat': 0, 'lon': 0, 'last_signal': 3},
    {'mmsi': 224000003, 'lat': 37.0, 'lon': -1.0, 'last_signal': 5000},
    {'mmsi': '224000004', 'lat': 37.0, 'lon': -1.0, 'last_signal': 1},
    {'mmsi': True, 'lat': 37.0, 'lon': -1.0, 'last_signal': 1},
    {'mmsi': 224000005, 'lat': 95, 'lon': -1.0, 'last_signal': 1},
    {'mmsi': 224000006, 'lat': 37.1, 'lon': -1.1, 'last_signal': 2, 'speed': 999, 'cog': float('nan'), 'shiptype': 300},
    'basura']})
assert [b['mmsi'] for b in r['ships']] == [224123456, 224000006], r
b0 = r['ships'][0]
assert b0['shipname'] == 'PUERTO bCARTAGENA/b' and b0['destination'] == 'VALENCIA' and b0['speed'] == 11.2, b0
assert set(r['ships'][1]) == {'mmsi', 'lat', 'lon', 'edad'}, r['ships'][1]
assert api.barcos([{'mmsi': 224123456, 'lat': 1, 'lon': 1, 'last_signal': 0}])['ships'][0]['mmsi'] == 224123456
for malo in ({'ships': 'x'}, None, 3):
    try:
        api.barcos(malo)
        raise AssertionError('debía fallar: %r' % (malo,))
    except ValueError:
        pass

# --- Prueba funcional del consentimiento en Node (DOM mínimo) ------------------------
ARNES = r"""
const fs = require('fs');
function elemento() {
    const e = { attrs: {}, hijos: [], textContent: '', innerHTML: '', href: '', id: '',
        setAttribute(k, v) { this.attrs[k] = v; }, addEventListener(t, f) { this['on' + t] = f; },
        querySelector() { return this._sub || (this._sub = elemento()); },
        querySelectorAll() { return this._subs || (this._subs = [elemento(), elemento()]); },
        remove() { global.quitados++; }, focus() {} };
    return e;
}
function probar(cookieInicial, protocolo, hash) {
    const escrituras = [];
    let jar = cookieInicial;
    global.quitados = 0;
    global.Plugins = { consentimiento: {} };
    global.navigator = { language: 'es-ES' };
    global.location = { protocol: protocolo, hash: hash || '' };
    global.localStorage = { d: {}, getItem(k) { return this.d[k] || null; }, setItem(k, v) { this.d[k] = v; }, removeItem(k) { delete this.d[k]; } };
    const eventos = [];
    global.CustomEvent = function (n, o) { this.type = n; this.detail = o.detail; };
    global.window = { consentimiento_config: {}, addEventListener() {}, dispatchEvent(e) { eventos.push(e.detail.estado); } };
    const anadidos = [];
    global.document = { createElement: elemento, body: { appendChild(e) { anadidos.push(e); } } };
    Object.defineProperty(global.document, 'cookie', { get() { return jar; }, set(v) { escrituras.push(v); jar = v.split(';')[0]; }, configurable: true });
    eval(fs.readFileSync(process.argv[2], 'utf8'));
    const ok = Plugins.consentimiento.init();
    return { ok, P: Plugins.consentimiento, escrituras, anadidos, eventos, ls: localStorage.d };
}
(async () => {
    const r = {};
    const a = probar('', 'https:');
    r.sin = { ok: a.ok, estado: a.P.estado(), banner: a.anadidos.length };
    a.P.guardar('terceros');
    r.sin.tras = { estado: a.P.estado(), terceros: a.P.terceros(), cookie: a.escrituras[0], ls: a.ls.bh_consent,
                   eventos: a.eventos, listo: await a.P.listo, quitados: global.quitados };
    const b = probar('otra=1; bh_consent=v1.necesarias', 'http:');
    r.con = { estado: b.P.estado(), terceros: b.P.terceros(), banner: b.anadidos.length, escrituras: b.escrituras.length, listo: await b.P.listo };
    b.P.guardar('malo');
    r.con.malo = b.escrituras.length;
    b.P.guardar('terceros');
    r.con.http = b.escrituras[0];
    const c = probar('bh_consent=v1.hack', 'https:');
    r.trucada = { estado: c.P.estado(), banner: c.anadidos.length };
    const d = probar('bh_consent=v1.terceros', 'https:', '#cookies');
    r.reabrir = { estado: d.P.estado(), banner: d.anadidos.length };
    console.log(JSON.stringify(r));
})();
"""

node = shutil.which('node')
if node:
    with tempfile.TemporaryDirectory() as tmp:
        arnes = os.path.join(tmp, 'arnes.js')
        with open(arnes, 'w', encoding='utf-8') as f:
            f.write(ARNES)
        salida = subprocess.run([node, arnes, os.path.join(PLUG, 'consentimiento/consentimiento.js')],
                                capture_output=True, text=True, check=True).stdout
    r = json.loads(salida)
    assert r['sin']['ok'] is True and r['sin']['estado'] is None and r['sin']['banner'] == 1, r
    tras = r['sin']['tras']
    assert tras['estado'] == 'terceros' and tras['terceros'] is True and tras['listo'] == 'terceros', r
    assert tras['cookie'] == 'bh_consent=v1.terceros; Path=/; Max-Age=15552000; SameSite=Lax; Secure', tras['cookie']
    assert tras['ls'] == 'v1.terceros' and tras['eventos'] == ['terceros'] and tras['quitados'] == 1, r
    assert r['con'] == {'estado': 'necesarias', 'terceros': False, 'banner': 0, 'escrituras': 0, 'listo': 'necesarias',
                        'malo': 0, 'http': 'bh_consent=v1.terceros; Path=/; Max-Age=15552000; SameSite=Lax'}, r
    assert r['trucada'] == {'estado': None, 'banner': 1}, r
    assert r['reabrir'] == {'estado': 'terceros', 'banner': 1}, r
else:
    print('AVISO: sin node; se omite la prueba funcional del consentimiento')

print('OK test_politicas_mapa_local: sin webs externas, ADS-B/AIS locales en el mapa, 443 y logo en todas las páginas')
