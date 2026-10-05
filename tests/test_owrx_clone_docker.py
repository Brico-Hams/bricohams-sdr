#!/usr/bin/env python3
"""v4.3 · owrx-clone 1.1 con OpenWebRX+ en Docker, sin Docker de verdad: una orden «docker» de
mentira responde a «docker inspect» con los volúmenes del contenedor (carpetas de un árbol de
pruebas, OWRX_CLONE_RAIZ) y apunta stop/start. Comprueba:
  nativo → Docker (los ficheros caen en los volúmenes, sin apt, sin parches, sin tocar /etc/openwebrx),
  Docker → perfil (rutas lógicas, imagen apuntada, sin paquetes) → nativo,
  contenedor sin volúmenes, data_directory raro, htdocs fuera de plugins, deshacer y comprobar."""
import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
import shutil
import stat
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
DD = '/opt/owrx-docker'

# ---- docker de mentira: inspect lee el JSON de OWRX_FAKE_DOCKER; exec da la versión; el resto, 0
os.makedirs(os.path.join(T, 'bin'))
FAKE = os.path.join(T, 'bin', 'docker')
with open(FAKE, 'w') as f:
    f.write('''#!/usr/bin/env python3
import json, os, sys
a = sys.argv[1:]
cont = json.load(open(os.environ['OWRX_FAKE_DOCKER']))
if a[0] == 'inspect':
    if a[1] not in cont: sys.stderr.write('Error: No such object'); sys.exit(1)
    print(json.dumps([cont[a[1]]])); sys.exit(0)
if a[0] == 'exec':
    print('1.2.130'); sys.exit(0)
sys.exit(0)
''')
os.chmod(FAKE, os.stat(FAKE).st_mode | stat.S_IEXEC)
oc.DOCKER_BIN = FAKE
FAKE_JSON = os.path.join(T, 'contenedores.json')


def contenedores(**c):
    json.dump(c, open(FAKE_JSON, 'w'))
    os.environ['OWRX_FAKE_DOCKER'] = FAKE_JSON


def inspect(montajes, imagen='slechev/openwebrxplus-softmbe:latest', red='host', activo=True):
    return {'Image': 'sha256:abc', 'Config': {'Image': imagen}, 'State': {'Running': activo},
            'HostConfig': {'NetworkMode': red}, 'NetworkSettings': {'Ports': {'8073/tcp': [{'HostPort': '8080'}]}},
            'Mounts': [{'Type': 'bind', 'Source': s, 'Destination': d} for d, s in montajes.items()]}


VOL = {'/var/lib/openwebrx': DD + '/var', '/etc/openwebrx': DD + '/etc', HT + '/plugins': DD + '/plugins'}


def poner(raiz, ruta, texto, modo=0o644):
    p = raiz + ruta
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as f:
        f.write(texto if isinstance(texto, bytes) else texto.encode())
    os.chmod(p, modo)


def correr(raiz, *args):
    oc.RAIZ = raiz
    oc.DOCKER = ''
    oc.ORDENES.clear()
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = oc.main(list(args))
    return rc, out.getvalue() + err.getvalue()


def leer(raiz, ruta):
    return open(raiz + ruta, encoding='utf-8').read()


# ------------------------------------------------------------------ 1. estación nativa → perfil
A = os.path.join(T, 'nativa')
INDEX, MODES = '<html>owrx</html>', 'MODOS = []\n'
import hashlib  # noqa: E402
md5 = lambda t: hashlib.md5(t.encode()).hexdigest()   # noqa: E731
poner(A, '/var/lib/dpkg/status', 'Package: openwebrx\nStatus: install ok installed\nVersion: 1.2.125\nArchitecture: all\n\n'
                                 'Package: rtl-sdr\nStatus: install ok installed\nVersion: 2.0.2\nArchitecture: arm64\n')
poner(A, '/var/lib/apt/extended_states', '')
poner(A, '/var/lib/dpkg/info/openwebrx.md5sums', '%s  %s\n%s  %s\n' % (md5(INDEX), (HT + '/index.html').lstrip('/'),
                                                                    md5(MODES), 'usr/lib/python3/dist-packages/owrx/modes.py'))
poner(A, '/etc/os-release', 'ID=debian\nVERSION_CODENAME=trixie\nPRETTY_NAME="Debian GNU/Linux 13 (trixie)"\n')
poner(A, HT + '/index.html', INDEX)
poner(A, '/usr/lib/python3/dist-packages/owrx/modes.py', MODES + '# parche\n')
poner(A, HT + '/plugins/receiver/init.js', "Plugins.load('mio');\n")
poner(A, HT + '/plugins/receiver/mio/mio.js', 'Plugins.mio={}')
poner(A, HT + '/css/tema-propio.css', 'body{}')                       # fuera de plugins: no cabe en Docker
SET = {'receiver_name': 'EA5KAO · Mi QTH', 'sdrs': {'rtl': {'name': 'HAM', 'type': 'rtl_sdr', 'device': 'serial=00000102', 'profiles': {}}}}
poner(A, '/var/lib/openwebrx/settings.json', json.dumps(SET))
poner(A, '/var/lib/openwebrx/users.json', '[{"user":"admin"}]', 0o600)
poner(A, '/var/lib/openwebrx/bookmarks.json', '[]')
poner(A, '/etc/openwebrx/openwebrx.conf', '[core]\ndata_directory = /var/lib/openwebrx\n[web]\nport = 8073\n')
poner(A, '/etc/openwebrx/openwebrx.conf.d/90-mio.conf', '[core]\nlog_level = DEBUG\n')
poner(A, '/etc/udev/rules.d/99-sdr.rules', 'SUBSYSTEM=="usb"\n')
nat = os.path.join(T, 'nativa.owrx.tar.gz')
rc, out = correr(A, 'exportar', '-o', nat)
assert rc == 0, out

# ------------------------------------------------------------------ 2. perfil nativo → Docker
B = os.path.join(T, 'docker')
for d in ('/var', '/etc', '/plugins'):
    os.makedirs(B + DD + d)
poner(B, '/etc/os-release', 'ID=debian\nVERSION_CODENAME=bookworm\nPRETTY_NAME="Debian GNU/Linux 12 (bookworm)"\n')
poner(B, DD + '/var/settings.json', '{"receiver_name": "vacío", "sdrs": {}}')
poner(B, DD + '/etc/openwebrx.conf', '[core]\ndata_directory = /var/lib/openwebrx\n')
contenedores(**{'owrx-mbe': inspect(VOL)})
rc, out = correr(B, '--docker', 'owrx-mbe', 'importar', nat, '--todo', '--si')
assert rc == 0, out
assert json.loads(leer(B, DD + '/var/settings.json'))['receiver_name'] == 'EA5KAO · Mi QTH'
assert leer(B, DD + '/var/users.json').startswith('[{"user"')
assert 'log_level' in leer(B, DD + '/etc/openwebrx.conf.d/90-mio.conf')
assert leer(B, DD + '/plugins/receiver/mio/mio.js') == 'Plugins.mio={}'
assert not os.path.exists(B + '/var/lib/openwebrx') and not os.path.exists(B + '/etc/openwebrx'), 'no toca las rutas nativas'
assert not os.path.exists(B + HT), 'en Docker no hay htdocs en el equipo'
assert 'tema-propio.css' in out and 'solo está montada la carpeta htdocs/plugins' in out
assert 'código de OpenWebRX+ va dentro de la imagen' in out, 'los parches no se aplican en Docker'
assert os.path.exists(B + '/etc/udev/rules.d/99-sdr.rules'), 'sistema (udev) sí: es del equipo'
assert not any('apt-get' in o for o in oc.ORDENES), oc.ORDENES
assert any(o.endswith('docker stop owrx-mbe') for o in oc.ORDENES) and any(o.endswith('docker start owrx-mbe') for o in oc.ORDENES), oc.ORDENES
assert not any('systemctl' in o and 'openwebrx' in o for o in oc.ORDENES), oc.ORDENES

# deshacer: sabe que era un contenedor (sin --docker) y deja el settings.json de antes
rc, out = correr(B, 'deshacer', '--si')
assert rc == 0, out
assert json.loads(leer(B, DD + '/var/settings.json'))['receiver_name'] == 'vacío'
assert not os.path.exists(B + DD + '/plugins/receiver/mio/mio.js'), 'borra lo creado'
assert any(o.endswith('docker start owrx-mbe') for o in oc.ORDENES), oc.ORDENES

# ------------------------------------------------------------------ 3. Docker → perfil → nativo
rc, out = correr(B, '--docker', 'owrx-mbe', 'importar', nat, '--si')
assert rc == 0, out
dk = os.path.join(T, 'docker.owrx.tar.gz')
rc, out = correr(B, '--docker', 'owrx-mbe', 'exportar', '-o', dk)
assert rc == 0, out
m, tmp = oc.abrir_perfil(dk)
shutil.rmtree(tmp)
rutas = {e['ruta'] for e in m['ficheros']}
assert m['origen']['docker']['imagen'] == 'slechev/openwebrxplus-softmbe:latest' and m['paquetes'] == [] and m['repos'] == []
assert '{DATA}/settings.json' in rutas and '/etc/openwebrx/openwebrx.conf.d/90-mio.conf' in rutas
assert '{HTDOCS}/plugins/receiver/mio/mio.js' in rutas and not any(DD in r for r in rutas), rutas
rc, out = correr(B, 'ver', dk)
assert 'en Docker: contenedor owrx-mbe' in out, out

C = os.path.join(T, 'nativa2')
poner(C, '/var/lib/dpkg/status', 'Package: openwebrx\nStatus: install ok installed\nVersion: 1.2.130\nArchitecture: all\n')
poner(C, '/var/lib/apt/extended_states', '')
poner(C, '/var/lib/dpkg/info/openwebrx.md5sums', '%s  %s\n' % (md5(INDEX), (HT + '/index.html').lstrip('/')))
poner(C, HT + '/index.html', INDEX)
poner(C, '/etc/os-release', 'ID=debian\nVERSION_CODENAME=trixie\nPRETTY_NAME="Debian GNU/Linux 13 (trixie)"\n')
rc, out = correr(C, 'importar', dk, '--si')
assert rc == 0, out
assert json.loads(leer(C, '/var/lib/openwebrx/settings.json'))['receiver_name'] == 'EA5KAO · Mi QTH'
assert leer(C, HT + '/plugins/receiver/mio/mio.js') == 'Plugins.mio={}'
assert 'log_level' in leer(C, '/etc/openwebrx/openwebrx.conf.d/90-mio.conf')
assert any('systemctl' in o and 'start' in o for o in oc.ORDENES) and not any('docker' in o for o in oc.ORDENES), oc.ORDENES

# ------------------------------------------------------------------ 4. errores
contenedores(**{'owrx-mbe': inspect({'/var/lib/openwebrx': DD + '/var'})})
rc, out = correr(B, '--docker', 'owrx-mbe', 'exportar', '-o', os.path.join(T, 'x.tar.gz'))
assert rc == 1 and 'no tiene volumen para /etc/openwebrx' in out, out
contenedores(**{'owrx-mbe': inspect(dict(VOL, **{'/etc/openwebrx': '/etc'}))})
rc, out = correr(B, '--docker', 'owrx-mbe', 'importar', nat, '--si')
assert rc == 1 and 'una carpeta del sistema' in out, 'un volumen montado desde /etc no se usa'
rc, out = correr(B, '--docker', 'otro', 'comprobar')
assert rc == 1 and 'no existe el contenedor «otro»' in out, out
contenedores(**{'owrx-mbe': inspect(VOL)})
S = os.path.join(T, 'srv')            # perfil con data_directory=/srv/openwebrx: en Docker no vale
poner(S, '/var/lib/dpkg/status', 'Package: openwebrx\nStatus: install ok installed\nVersion: 1.2.125\nArchitecture: all\n')
poner(S, '/var/lib/apt/extended_states', '')
poner(S, '/etc/os-release', 'ID=debian\nVERSION_CODENAME=trixie\nPRETTY_NAME="Debian 13"\n')
poner(S, '/etc/openwebrx/openwebrx.conf', '[core]\ndata_directory = /srv/openwebrx\n')
poner(S, '/srv/openwebrx/settings.json', '{"sdrs": {}}')
srv = os.path.join(T, 'srv.owrx.tar.gz')
assert correr(S, 'exportar', '-o', srv)[0] == 0
rc, out = correr(B, '--docker', 'owrx-mbe', 'importar', srv, '--si')
assert rc == 1 and 'en Docker tiene que ser /var/lib/openwebrx' in out, out

# ------------------------------------------------------------------ 5. comprobar (bridge: puerto publicado)
contenedores(**{'owrx-mbe': inspect(VOL, red='bridge', activo=False)})
rc, out = correr(B, '--docker', 'owrx-mbe', 'comprobar')
assert 'imagen slechev/openwebrxplus-softmbe' in out and 'volumen /etc/openwebrx → /opt/owrx-docker/etc' in out
assert 'el contenedor está parado' in out and rc == 1, out
oc.RAIZ = B
oc.DOCKER = 'owrx-mbe'
assert oc.equipo()['puerto'] == 8080, 'en bridge, el puerto publicado'

shutil.rmtree(T)
print('OK test_owrx_clone_docker: nativo→Docker en los volúmenes (sin apt ni parches), deshacer con docker start, '
      'Docker→perfil→nativo, contenedor sin volúmenes, data_directory raro, htdocs fuera de plugins y comprobar')
