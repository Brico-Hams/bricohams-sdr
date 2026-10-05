#!/usr/bin/env python3
"""Verifica backend Docker de OpenWebRX+ sin requerir un daemon Docker."""
import os
import re
import shutil
import subprocess
import tempfile

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
INSTALL = open(os.path.join(RAIZ, 'install.sh'), encoding='utf-8').read()


def funcion(nombre):
    return re.search(r'^%s\(\) \{.*?^\}' % nombre, INSTALL, re.S | re.M).group(0)


root = tempfile.mkdtemp(prefix='owrx-docker-')
for child in ('etc', 'var', 'plugins'):
    os.makedirs(os.path.join(root, child))
envfile = os.path.join(root, 'bricohams.env')
with open(envfile, 'w') as stream:
    stream.write('OWRX_BACKEND="docker"\nOWRX_DOCKER_DIR="%s"\nOWRX_DOCKER_CONTAINER="owrx-test"\nSTATION_LOCATOR="IM98"\n' % root)

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
KIT="%s"; FILES="$KIT/files"; HTDOCS=/native; OWRX_DATA=/native; OWRX_ETC=/native
fallo() { echo "FAIL $*" >&2; exit 1; }; bien() { echo "OK $*"; }; aviso() { echo "WARN $*"; }
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
''' % (RAIZ, mock, funcion('cargar_env'), funcion('owrx_control'), funcion('owrx_docker_mount') + '\n' + funcion('paso_openwebrx'), envfile)
try:
    result = subprocess.run(['bash', '-c', script], capture_output=True, text=True,
                            env=dict(os.environ, DOCKER_LOG=os.path.join(root, 'docker.log')))
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert 'volúmenes persistentes' in result.stdout
    assert open(os.path.join(root, 'docker.log')).read().strip() == 'docker restart owrx-test'
finally:
    shutil.rmtree(root)

print('OK test_instalador_docker: ENV, rutas persistentes, mounts oficiales y reinicio del contenedor')