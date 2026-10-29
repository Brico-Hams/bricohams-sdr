#!/usr/bin/env python3
"""v4.2 · owrx-clone dentro del instalador BricoHams:
  - «install.sh --exportar FICHERO» funciona SIN bricohams.env (vale en cualquier OpenWebRX+);
  - paso_importar llama a owrx-clone con los niveles de IMPORTAR_NIVELES, activa el MQTT de las
    visitas en el settings.json importado y deja la marca /etc/bricohams/perfil-importado;
  - con esa marca, «configuracion» no regenera settings.json y «plugins» no pisa init.js;
  - herramientas instala owrx-clone y su página man; la copia diaria guarda un perfil."""
import json
import os
import re
import shutil
import subprocess
import tempfile

RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
S = open(os.path.join(RAIZ, 'install.sh'), encoding='utf-8').read()


def funcion(n):
    return re.search(r'^%s\(\) \{.*?^\}' % n, S, re.S | re.M).group(0)


def linea(n):
    return re.search(r'^%s\(\) \{.*\}$' % n, S, re.M).group(0)


T = tempfile.mkdtemp()
# ---------------------------------------------------------------- --exportar sin bricohams.env
kit = os.path.join(T, 'kit')
os.makedirs(kit + '/files/bin')
shutil.copy(os.path.join(RAIZ, 'install.sh'), kit)
shutil.copytree(os.path.join(RAIZ, 'owrx-clone'), kit + '/owrx-clone')
falso = os.path.join(T, 'falso')            # una estación OpenWebRX+ mínima
os.makedirs(falso + '/var/lib/openwebrx')
os.makedirs(falso + '/var/lib/dpkg')
open(falso + '/var/lib/dpkg/status', 'w').write('Package: openwebrx\nStatus: install ok installed\nVersion: 1.2.125\n')
json.dump({'receiver_name': 'Prueba', 'sdrs': {}}, open(falso + '/var/lib/openwebrx/settings.json', 'w'))
salida = os.path.join(T, 'perfil.owrx.tar.gz')
env = dict(os.environ, OWRX_CLONE_RAIZ=falso, OWRX_CLONE_ARCH='arm64', NO_COLOR='1')
r = subprocess.run(['bash', kit + '/install.sh', '--exportar', salida], capture_output=True, text=True, env=env)
if os.geteuid() == 0:
    assert r.returncode == 0 and os.path.isfile(salida), (r.stdout, r.stderr)
    assert 'Falta' not in r.stdout + r.stderr, 'no debe pedir bricohams.env'
else:
    assert 'sudo' in r.stdout + r.stderr
r = subprocess.run(['bash', kit + '/install.sh', '--actualizar', '--importar', salida], capture_output=True, text=True, env=env)
assert r.returncode != 0 and 'no se combina' in r.stdout + r.stderr

# ---------------------------------------------------------------- paso_importar
data = os.path.join(T, 'owrx')
os.makedirs(data)
json.dump({'receiver_name': 'Importado', 'mqtt_enabled': False}, open(data + '/settings.json', 'w'))
llamadas = os.path.join(T, 'llamadas.txt')
fake = os.path.join(T, 'owrx-clone-falso')
open(fake, 'w').write('#!/bin/bash\necho "$@" >> %s\n' % llamadas)
os.chmod(fake, 0o755)
marca = os.path.join(T, 'perfil-importado')
script = '''set -Eeuo pipefail
bien() { echo "BIEN $*"; }; aviso() { echo "AVISO $*"; }; fallo() { echo "FALLO $*"; exit 1; }; info() { echo "INFO $*"; }
install() { :; }; systemctl() { echo "systemctl $*"; }; owrx_control() { systemctl "$1" openwebrx; }; owrx_owner() { :; }; chown() { :; }; openwebrx() { echo "openwebrx $*"; }
%s
%s
%s
%s
KIT=/nada; FILES=%s; OWRX_DATA=%s; PERFIL_IMPORTADO=%s; OWRX_CLONE_BIN=%s; VISITAS_ENABLE=yes
''' % (linea('si'), linea('sq'), linea('envl'), funcion('paso_importar'), os.path.join(RAIZ, 'files'), data, marca, fake)
r = subprocess.run(['bash', '-c', script + 'IMPORTAR=""; paso_importar'], capture_output=True, text=True)
assert r.returncode == 0 and 'sin perfil que importar' in r.stdout and not os.path.exists(llamadas), r
r = subprocess.run(['bash', '-c', script + 'IMPORTAR=/tmp/p.owrx.tar.gz; IMPORTAR_NIVELES=config,web; paso_importar'], capture_output=True, text=True)
assert r.returncode == 0, (r.stdout, r.stderr)
assert open(llamadas).read().strip() == 'importar /tmp/p.owrx.tar.gz --si --niveles config,web'
assert 'no trae usuario de administración' in r.stdout, 'perfil público: hay que crear el admin'
s = json.load(open(data + '/settings.json'))
assert s['mqtt_enabled'] is True and s['mqtt_host'] == 'localhost' and s['receiver_name'] == 'Importado'
txt = open(marca).read()
assert "PERFIL='/tmp/p.owrx.tar.gz'" in txt and "NIVELES='config,web'" in txt
r = subprocess.run(['bash', '-c', script + 'IMPORTAR=""; paso_importar'], capture_output=True, text=True)
assert 'perfil importado antes: ' in r.stdout
open(fake, 'w').write('#!/bin/bash\nexit 3\n')
r = subprocess.run(['bash', '-c', script + 'IMPORTAR=/tmp/p.owrx.tar.gz; paso_importar'], capture_output=True, text=True)
assert r.returncode == 1 and 'owrx-clone deshacer' in r.stdout

# ---------------------------------------------------------------- el resto del instalador respeta lo importado
conf = funcion('paso_configuracion')
assert conf.index('if [ -f "$PERFIL_IMPORTADO" ] && ! si "${OWRX_PLANTILLA:-no}"') < conf.index('bricohams-render-settings.py')
assert "guardar=(--exclude 'receiver/init.js')" in funcion('paso_plugins') and '"${guardar[@]}"' in funcion('paso_plugins')
assert 'owrx-clone.1' in funcion('paso_herramientas') and 'importar tareas)' in S
assert S.index('if [ -n "$EXPORTAR" ]') < S.index('[ -r "$KIT/bricohams.env" ] || fallo')
tarea = open(os.path.join(RAIZ, 'files/bin/bricohams-tarea'), encoding='utf-8').read()
assert 'owrx-clone ${OWRX_CLONE_DOCKER:+--docker "$OWRX_CLONE_DOCKER"} exportar -o "$d/perfil-owrx-' in tarea
assert 'tail -n +8' not in tarea
assert 'systemctl enable --now bricohams-backup-limpieza.timer' in funcion('paso_herramientas')
shutil.rmtree(T)
print('OK test_instalador_perfil: --exportar sin bricohams.env, paso_importar (niveles, MQTT, marca, error), '
      'configuracion/plugins respetan el perfil, copia diaria con perfil')
