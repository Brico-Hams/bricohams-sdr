#!/usr/bin/env python3
"""Verifica backend Docker de OpenWebRX+ sin requerir un daemon Docker.

v4.3 · además del contenedor que ya existe (prueba original), el despliegue desde bricohams.env:
docker-compose.yaml generado (válido para «docker compose config»), Docker instalado si falta,
OpenWebRX+ nativo desactivado, usuario «openwebrx» del sistema para los servicios del host,
pasos que no aplican en Docker (FT2, API de SDRplay, repositorio de luarvique) y el .env de /etc
con las rutas calculadas."""
import os
import re
import shutil
import subprocess
import tempfile

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
INSTALL = open(os.path.join(RAIZ, 'install.sh'), encoding='utf-8').read()


def funcion(nombre):
    return re.search(r'^%s\(\) \{.*?^\}' % nombre, INSTALL, re.S | re.M).group(0)


ZONA = '\n'.join(funcion(f) for f in ('coords_ok', 'zona_locator', 'zona_selector'))

root = tempfile.mkdtemp(prefix='owrx-docker-')
for child in ('etc', 'var', 'plugins'):
    os.makedirs(os.path.join(root, child))
envfile = os.path.join(root, 'bricohams.env')
with open(envfile, 'w') as stream:
    stream.write('OWRX_BACKEND="docker"\nOWRX_DOCKER_DIR="%s"\nOWRX_DOCKER_CONTAINER="owrx-test"\nSTATION_LOCATOR="IM98"\n'
                 'OWRX_DOCKER_DESPLEGAR="no"\n' % root)

mock = r'''docker() {
    [ "$1" = inspect ] || { [ "$1" = restart ] && { echo "docker restart $2" >>"$DOCKER_LOG"; return 0; }; return 2; }
    if [ "$2" != --format ]; then [ "$2" = "$OWRX_DOCKER_CONTAINER" ]; return; fi
    case "$3" in
        *State.Running*) echo true ;;
        *'/etc/openwebrx'*) printf '%s/etc' "$OWRX_DOCKER_DIR" ;;
        *'/var/lib/openwebrx'*) printf '%s/var' "$OWRX_DOCKER_DIR" ;;
        *'/usr/lib/python3/dist-packages/htdocs/plugins'*) printf '%s/plugins' "$OWRX_DOCKER_DIR" ;;
        *.Mounts*) printf '%s\n' /etc/openwebrx /var/lib/openwebrx /usr/lib/python3/dist-packages/htdocs/plugins ;;
        *) return 3 ;;
    esac
}
'''
script = r'''set -Eeuo pipefail
KIT="%s"; FILES="$KIT/files"; HTDOCS=/native; OWRX_DATA=/native; OWRX_ETC=/native; LOCATOR_CACHE=/nonexistent
si() { case "${1,,}" in 1|y|yes|s|si|sí|true|on) return 0 ;; *) return 1 ;; esac; }
fallo() { echo "FAIL $*" >&2; exit 1; }; bien() { echo "OK $*"; }; aviso() { echo "WARN $*"; }; usuario_openwebrx() { :; }
%s
%s
%s
%s
%s
cargar_env "%s"
[ "$OWRX_DATA" = "$OWRX_DOCKER_DIR/var" ]
[ "$OWRX_ETC" = "$OWRX_DOCKER_DIR/etc" ]
[ "$HTDOCS" = "$OWRX_DOCKER_DIR" ]
[ "$STATION_LAT" = 38.500000 ] && [ "$STATION_LON" = -1.000000 ]
paso_openwebrx
owrx_control restart
''' % (RAIZ, mock, ZONA, funcion('cargar_env'), funcion('owrx_control'), funcion('owrx_docker_mount') + '\n' + funcion('paso_openwebrx'), envfile)
try:
    result = subprocess.run(['bash', '-c', script], capture_output=True, text=True,
                            env=dict(os.environ, DOCKER_LOG=os.path.join(root, 'docker.log')))
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert 'volúmenes persistentes' in result.stdout
    assert open(os.path.join(root, 'docker.log')).read().strip() == 'docker restart owrx-test'
finally:
    shutil.rmtree(root)

# ---------------------------------------------------------------- v4.3 · despliegue desde bricohams.env
T = tempfile.mkdtemp(prefix='owrx-deploy-')
dd = os.path.join(T, 'owrx-docker')
log = os.path.join(T, 'ordenes.log')
bindir = os.path.join(T, 'bin')
os.makedirs(bindir)
# «docker» de mentira: antes de «compose up» no hay contenedor; después, sí, con los volúmenes del compose
with open(os.path.join(bindir, 'docker'), 'w') as f:
    f.write(r'''#!/bin/bash
echo "docker $*" >>"$LOG"
case "$1" in
    compose) [ "$2" = version ] && exit 0
             if [ "$2" = up ]; then touch "$T/arriba"; fi; exit 0 ;;
    inspect) [ -f "$T/arriba" ] || exit 1
             case "${3:-}" in
                 *State.Running*) echo true ;;
                 *Config.Image*) echo slechev/openwebrxplus-softmbe:latest ;;
                 *'"/etc/openwebrx"'*) printf '%s/etc' "$DD" ;;
                 *'"/var/lib/openwebrx"'*) printf '%s/var' "$DD" ;;
                 *'htdocs/plugins"'*) printf '%s/plugins' "$DD" ;;
                 *.Mounts*) printf '%s\n' /etc/openwebrx /var/lib/openwebrx /usr/lib/python3/dist-packages/htdocs/plugins ;;
                 *) echo '[{}]' ;;
             esac ;;
esac
exit 0
''')
os.chmod(os.path.join(bindir, 'docker'), 0o755)
deploy = r'''set -Eeuo pipefail
KIT="%s"; FILES="$KIT/files"
OWRX_BACKEND=docker; OWRX_DOCKER_DIR="%s"; HTDOCS=$OWRX_DOCKER_DIR; OWRX_DATA=$OWRX_DOCKER_DIR/var; OWRX_ETC=$OWRX_DOCKER_DIR/etc
OWRX_DOCKER_CONTAINER=owrx-mbe; OWRX_DOCKER_IMAGE=slechev/openwebrxplus-softmbe:latest
si() { case "${1,,}" in 1|y|yes|s|si|sí|true|on) return 0 ;; *) return 1 ;; esac; }
fallo() { echo "FAIL $*"; exit 1; }; bien() { echo "OK $*"; }; aviso() { echo "WARN $*"; }; info() { echo "INFO $*"; }
apt_update() { echo "apt-get update" >>"$LOG"; }; apt_i() { echo "apt-get install $*" >>"$LOG"; }
systemctl() { echo "systemctl $*" >>"$LOG"; case "$1" in is-enabled) return 0 ;; is-active) return 1 ;; esac; }
getent() { return 2; }; useradd() { echo "useradd $*" >>"$LOG"; }
curl() { return 0; }; install() { command install "$@" 2>/dev/null || mkdir -p "${@: -1}"; }
%s
%s
%s
%s
%s
%s
paso_openwebrx
''' % (RAIZ, dd, funcion('docker_compose') + '\n' + funcion('usuario_openwebrx'), funcion('esperar_owrx'), funcion('docker_preparar'),
       funcion('owrx_docker_mount'), funcion('paso_openwebrx'), '')
r = subprocess.run(['bash', '-c', deploy], capture_output=True, text=True,
                   env=dict(os.environ, LOG=log, T=T, DD=dd, PATH=bindir + ':' + os.environ['PATH']))
ordenes = open(log).read() if os.path.exists(log) else ''
try:
    assert r.returncode == 0, (r.stdout, r.stderr, ordenes)
    assert 'contenedor owrx-mbe en marcha' in r.stdout and 'volúmenes persistentes' in r.stdout, r.stdout
    assert 'systemctl disable --now openwebrx' in ordenes, 'el nativo y el contenedor no conviven'
    assert 'useradd --system' in ordenes and ' openwebrx' in ordenes, 'usuario del host para los servicios'
    assert 'docker compose pull' in ordenes and 'docker compose up -d --remove-orphans' in ordenes, ordenes
    assert ordenes.index('docker compose pull') < ordenes.index('docker compose up'), ordenes
    assert 'apt-get install' not in ordenes, 'Docker ya estaba: no se instala nada'
    for d in ('etc', 'var', 'plugins/receiver', 'plugins/map'):
        assert os.path.isdir(os.path.join(dd, d)), d
    yml = open(os.path.join(dd, 'docker-compose.yaml')).read()
    for x in ('image: "slechev/openwebrxplus-softmbe:latest"', 'container_name: "owrx-mbe"', 'network_mode: host',
              '- ./etc:/etc/openwebrx', '- ./var:/var/lib/openwebrx', '- ./plugins:/usr/lib/python3/dist-packages/htdocs/plugins',
              '/dev/bus/usb:/dev/bus/usb', 'c 189:* rmw', 'restart: unless-stopped'):
        assert x in yml, (x, yml)
    assert 'privileged' not in yml.replace('--privileged', '').replace('OWRX_DOCKER_PRIVILEGED', '')
    assert 'PASS' not in yml.upper() and 'ADMIN' not in yml.upper(), 'el compose no lleva contraseñas'
finally:
    shutil.rmtree(T)

# compose: opciones y validación
GEN = os.path.join(RAIZ, 'files/bin/bricohams-docker-compose.py')
def gen(**e):
    return subprocess.run(['python3', GEN], capture_output=True, text=True, env=dict(os.environ, **e))
b = gen(OWRX_DOCKER_RED='bridge', OWRX_DOCKER_PORT='8080', OWRX_DOCKER_PRIVILEGED='yes')
assert b.returncode == 0 and '"127.0.0.1:8080:8073"' in b.stdout and 'privileged: true' in b.stdout and 'network_mode' not in b.stdout
# v5.0 · OWRX_SOLO_LOCAL=no vuelve a publicarlo en todas las interfaces
b = gen(OWRX_DOCKER_RED='bridge', OWRX_DOCKER_PORT='8080', OWRX_SOLO_LOCAL='no')
assert b.returncode == 0 and '"8080:8073"' in b.stdout and '127.0.0.1' not in b.stdout
for malo in ({'OWRX_DOCKER_IMAGE': 'x; rm -rf /'}, {'OWRX_DOCKER_RED': 'macvlan'}, {'OWRX_DOCKER_PORT': '99999'},
             {'OWRX_DOCKER_CONTAINER': '../x'}):
    assert gen(**malo).returncode != 0, malo
try:
    import yaml
    d = yaml.safe_load(gen().stdout)
    s = d['services']['openwebrx']
    assert s['network_mode'] == 'host' and len(s['volumes']) == 4 and d['version'] == '2.4'
except ImportError:
    pass
if shutil.which('docker') and subprocess.run(['docker', 'compose', 'version'], capture_output=True).returncode == 0:
    t = tempfile.mkdtemp()
    open(os.path.join(t, 'docker-compose.yaml'), 'w').write(gen().stdout)
    c = subprocess.run(['docker', 'compose', 'config', '-q'], cwd=t, capture_output=True, text=True)
    shutil.rmtree(t)
    assert c.returncode == 0, c.stderr

# pasos que no aplican en Docker y el .env de /etc con las rutas calculadas
for paso, texto in (('paso_ft2', 'FT2 no está disponible con OpenWebRX+ en Docker'), ('paso_sdrplay', 'la API de SDRplay va dentro de la imagen')):
    out = subprocess.run(['bash', '-c', 'set -Eeuo pipefail\nsi() { case "${1,,}" in yes) return 0;; *) return 1;; esac; }\n'
                          'aviso() { echo "AVISO $*"; }\nINSTALL_SDRPLAY_API=yes; FT2_ENABLE=yes; OWRX_BACKEND=docker\n%s\n%s' % (funcion(paso), paso)],
                         capture_output=True, text=True)
    assert out.returncode == 0 and texto in out.stdout, (paso, out.stdout, out.stderr)
assert 'OpenWebRX+ en Docker (${OWRX_DOCKER_IMAGE' in funcion('paso_comprobar'), 'sin repositorio de luarvique en Docker'
T = tempfile.mkdtemp()
kitenv = os.path.join(T, 'bricohams.env')
open(kitenv, 'w').write('CALLSIGN="EA5ABC"\nAEMET_API_KEY="clave"\n')
envscript = 'set -Eeuo pipefail\nKIT="%s"; FILES="%s/files"\nfallo() { echo "FALLO $*"; exit 1; }\n%s\n%s\n%s\n' % (
    T, RAIZ, funcion('sq'), funcion('envl'), funcion('instalar_env')) + \
    'LOCATOR_DERIVADAS=(STATION_LAT STATION_LON); STATION_LAT=38.5; STATION_LON=-1.0; STATION_QTH_LOCATOR=IM98\n' + \
    'OWRX_BACKEND=docker; OWRX_DOCKER_CONTAINER=owrx-mbe; OWRX_DATA=/opt/owrx-docker/var; OWRX_ETC=/opt/owrx-docker/etc; HTDOCS=/opt/owrx-docker\n' + \
    'instalar_env "%s/etc.env"\n' % T
r = subprocess.run(['bash', '-c', envscript], capture_output=True, text=True)
assert r.returncode == 0, r.stderr
etc = open(os.path.join(T, 'etc.env')).read()
for x in ("STATION_LAT='38.5'", "STATION_QTH_LOCATOR='IM98'", "OWRX_HTDOCS='/opt/owrx-docker'", "OWRX_CLONE_DOCKER='owrx-mbe'", "CALLSIGN='EA5ABC'"):
    assert x in etc, (x, etc)
assert oct(os.stat(os.path.join(T, 'etc.env')).st_mode & 0o777) == '0o600'
v = subprocess.run(['python3', os.path.join(RAIZ, 'files/bin/bricohams-env.py'), '--comprobar', os.path.join(T, 'etc.env')], capture_output=True, text=True)
assert v.returncode == 0 and v.stderr == '', v.stderr
shutil.rmtree(T)
# revisión v4.3: volver a nativo para el contenedor; huellas con el backend; usuario del host; copia de una estación Docker
nat = subprocess.run(['bash', '-c', 'set -Eeuo pipefail\naviso() { echo "AVISO $*"; }; bien() { :; }\n'
                      'docker() { echo "docker $*" >>"$DLOG"; [ "$1" != inspect ] || return 0; }\nclave_apt() { :; }; apt_update() { :; }; apt_i() { :; }\n'
                      'systemctl() { :; }; dpkg-query() { :; }; usuario_openwebrx() { :; }\nFILES=/nada; OWRX_BACKEND=native; DEB=trixie\n%s\npaso_openwebrx' % funcion('paso_openwebrx')
                      .replace('>/etc/apt/sources.list.d/openwebrx-plus.list', '>/dev/null')], capture_output=True, text=True,
                     env=dict(os.environ, DLOG=os.path.join(tempfile.gettempdir(), 'bh-docker-nativo.log')))
dlog = open(os.path.join(tempfile.gettempdir(), 'bh-docker-nativo.log')).read()
os.unlink(os.path.join(tempfile.gettempdir(), 'bh-docker-nativo.log'))
assert nat.returncode == 0 and 'docker update --restart=no owrx-mbe' in dlog and 'docker stop owrx-mbe' in dlog, (nat.stdout, nat.stderr, dlog)
T = tempfile.mkdtemp()
open(os.path.join(T, 'bricohams.env'), 'w').write('OWRX_BACKEND="docker"\nOWRX_DOCKER_DIR="/opt/owrx-docker"\nAEMET_API_KEY="x"\n')
vp = subprocess.run(['bash', '-c', 'KIT=%s\n%s\n%s\n%s\nfor p in meteo plugins red; do echo "$p: $(vars_paso $p | tr "\\n" " ")"; done' % (
    T, funcion('vars_paso'), funcion('paso_meteo') + '\n' + funcion('escribir_meteo_env'), funcion('paso_plugins') + '\n' + funcion('paso_red'))], capture_output=True, text=True)
assert 'meteo: AEMET_API_KEY OWRX_BACKEND OWRX_DOCKER_DIR' in vp.stdout and 'red: ' in vp.stdout and 'OWRX' not in vp.stdout.split('red:')[1], vp.stdout
shutil.rmtree(T)
assert 'usuario_openwebrx' in funcion('owrx_owner') and 'usuario_openwebrx' in funcion('paso_configuracion')
assert '"$dvar/users.json" "$dvar/bookmarks.json"' in funcion('paso_configuracion')
assert '"$oc" "${dk[@]}" importar' in INSTALL and 'dk=(--docker "${OWRX_DOCKER_CONTAINER:-owrx-mbe}")' in INSTALL
assert '${EXP_DOCKER:+--docker "$EXP_DOCKER"} exportar' in INSTALL

print('OK test_instalador_docker: ENV, rutas persistentes, mounts oficiales y reinicio del contenedor; v4.3 despliegue '
      '(compose generado y válido, pull + up, nativo desactivado, usuario del host), FT2/SDRplay saltados y .env de /etc')
