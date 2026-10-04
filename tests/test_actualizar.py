#!/usr/bin/env python3
"""v4.1 · install.sh --actualizar.

Ejecuta de verdad (en bash, con un kit de juguete en una carpeta temporal) las
funciones de install.sh que deciden qué se actualiza:
  - huellas por paso: código, ficheros del kit y variables de bricohams.env;
  - plan: solo los pasos que han cambiado (+ comprobar y herramientas);
  - variables nuevas del .env.example añadidas sin tocar las existentes;
  - git pull --ff-only y nueva vuelta con el install.sh recién bajado;
y la unión de marcadores en tres vías (bricohams-merge-bookmarks --tres)."""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import tempfile

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
S = open(os.path.join(RAIZ, 'install.sh'), encoding='utf-8').read()


def funcion(nombre):
    m = re.search(r'^%s\(\) \{.*?^\}' % re.escape(nombre), S, re.S | re.M) or \
        re.search(r'^%s\(\) \{[^\n]*\}$' % re.escape(nombre), S, re.M)
    assert m, nombre
    return m.group(0)


FUNCS = '\n'.join(funcion(n) for n in (
    'h16', 'ficheros_paso', 'vars_paso', 'huella_paso', 'estado_guardar', 'motivo_paso',
    'env_nuevas', 'plan_actualizar', 'kit_g', 'kit_git', 'arreglar_kit'))

# ------------------------------------------------------------------ estático
for op in ('--actualizar)', '--simular)', '--todo)', '--sin-git)', '--sin-apt)', '--continuar)'):
    assert op in S, op
assert 'estado_guardar "$PASO_ACTUAL"' in S, 'el bucle de pasos debe guardar la huella'
assert 'pull --ff-only' in S and 'sudo -H -u "$du" git' in S
assert '--force-confold' in S and 'apt-get -s upgrade' in S
assert 'BRICOHAMS_LOG_ACTIVO=1' in S and '--continuar' in S
assert 'if [ -f /etc/cron.d/bricohams ]; then\n        systemctl disable --now bricohams-backup.timer' in S, \
    'herramientas no debe reactivar el timer de copia si manda el cron'
assert '--tres "$bm_ant"' in S and '/opt/bricohams/kit/files/openwebrx/bookmarks.json' in S, 'configuracion debe conservar los marcadores propios'
assert re.search(r'copia_previa\b', S) and 'resumen_actualizacion' in S

# ------------------------------------------------------------------ plan con un kit de juguete
tmp = tempfile.mkdtemp()
kit = os.path.join(tmp, 'kit')
os.makedirs(os.path.join(kit, 'files/bin'))
os.makedirs(os.path.join(kit, 'files/htdocs/plugins/receiver'))
os.makedirs(os.path.join(kit, 'firmware/pico'))
open(os.path.join(kit, 'files/bin/uno'), 'w').write('uno v1\n')
open(os.path.join(kit, 'files/htdocs/plugins/receiver/x.js'), 'w').write('x v1\n')
open(os.path.join(kit, 'firmware/pico/main.py'), 'w').write('fw v1\n')
open(os.path.join(kit, 'bricohams.env'), 'w').write('VAR_A="1"\nVAR_B="clave-secreta"   # comentario\n')
open(os.path.join(kit, 'bricohams.env.example'), 'w').write(
    'VAR_A="0"   # a\nVAR_B=""   # b\nVAR_C="defecto"   # nueva en esta versión\n# VAR_D="comentada"\n')

CABECERA = r'''set -Eeuo pipefail
KIT=%s; FILES=$KIT/files; ESTADO_KIT=%s/estado; OWRX_CAMBIO=0; TODO=0; SIMULAR=0
bien() { echo "BIEN $*"; }; aviso() { echo "AVISO $*"; }; info() { echo "INFO $*"; }; fallo() { echo "FALLO $*"; exit 1; }
PASOS=(comprobar uno dos tres configuracion herramientas)
paso_comprobar() { [ -e "$FILES/bin/uno" ]; }
paso_uno() { install -m 755 "$FILES/bin/uno" /dev/null; echo "$VAR_A"; }
paso_dos() { rsync -a "$FILES/htdocs/plugins/" /nonexistent/; }
paso_tres() { cp "$KIT/firmware/pico/main.py" /dev/null; echo "${VAR_B:-}"; }
paso_configuracion() { :; }
paso_herramientas() { :; }
%s
. "$KIT/bricohams.env"
''' % (kit, tmp, FUNCS)


def bash(cuerpo, extra=''):
    r = subprocess.run(['bash', '-c', CABECERA + extra + '\n' + cuerpo], capture_output=True, text=True)
    assert r.returncode == 0, (r.stdout, r.stderr)
    return r.stdout


def plan(extra=''):
    out = bash('plan_actualizar >/dev/null; echo "PLAN ${PLAN[*]}"', extra)
    return out.strip().splitlines()[-1].split()[1:]


# sin huellas: todos los pasos
assert plan() == ['comprobar', 'uno', 'dos', 'tres', 'configuracion', 'herramientas']
bash('for p in "${PASOS[@]}"; do estado_guardar "$p"; done')
assert oct(os.stat(os.path.join(tmp, 'estado')).st_mode & 0o777) == '0o600'
assert 'clave-secreta' not in open(os.path.join(tmp, 'estado')).read(), 'la huella no debe guardar valores'
# todo al día: solo comprobar
assert plan() == ['comprobar'], plan()
# fichero de un plugin → dos (+ herramientas)
open(os.path.join(kit, 'files/htdocs/plugins/receiver/x.js'), 'w').write('x v2\n')
out = bash('plan_actualizar')
assert 'dos            ficheros del kit' in out and plan() == ['comprobar', 'dos', 'herramientas'], out
# fichero nuevo dentro de una carpeta que copia el paso → también
open(os.path.join(kit, 'files/htdocs/plugins/receiver/nuevo.js'), 'w').write('n\n')
assert plan() == ['comprobar', 'dos', 'herramientas'], plan()
bash('estado_guardar dos'); assert plan() == ['comprobar'], plan()
open(os.path.join(kit, 'files/htdocs/plugins/receiver/otro.js'), 'w').write('o\n')
assert plan() == ['comprobar', 'dos', 'herramientas'], plan()
bash('estado_guardar dos; estado_guardar herramientas')
# firmware (ruta $KIT/…) → tres
open(os.path.join(kit, 'firmware/pico/main.py'), 'w').write('fw v2\n')
assert plan() == ['comprobar', 'tres', 'herramientas'], plan()
bash('estado_guardar tres; estado_guardar herramientas')
# variable que lee un paso → ese paso + configuracion (lee todas)
env = open(os.path.join(kit, 'bricohams.env')).read().replace('clave-secreta', 'otra-clave')
open(os.path.join(kit, 'bricohams.env'), 'w').write(env)
out = bash('plan_actualizar')
assert plan() == ['comprobar', 'tres', 'configuracion', 'herramientas'], out
assert 'variables de bricohams.env' in out
bash('for p in "${PASOS[@]}"; do estado_guardar "$p"; done')
# código del paso cambiado (nueva versión de install.sh) → solo ese paso
assert plan('paso_uno() { install -m 755 "$FILES/bin/uno" /dev/null; echo "$VAR_A cambiado"; }') == ['comprobar', 'uno', 'herramientas']
# OpenWebRX+ actualizado → plugins y ft2 (aquí: ninguno de los dos existe) ; --todo → todos
assert plan('TODO=1') == ['comprobar', 'uno', 'dos', 'tres', 'configuracion', 'herramientas']

# ------------------------------------------------------------------ variables nuevas del .env.example
out = bash('env_nuevas mostrar')
assert 'VAR_C' in out and 'VAR_D' not in out
assert 'VAR_C' not in open(os.path.join(kit, 'bricohams.env')).read(), '«mostrar» no debe escribir'
bash('env_nuevas')
e = open(os.path.join(kit, 'bricohams.env')).read()
assert 'VAR_C="defecto"' in e and 'VAR_A="1"' in e and 'otra-clave' in e and 'VAR_A="0"' not in e, e
bash('env_nuevas')
assert open(os.path.join(kit, 'bricohams.env')).read() == e, 'env_nuevas debe ser idempotente'

# ------------------------------------------------------------------ git pull y nueva vuelta con el install.sh nuevo
G = ['git', '-c', 'user.name=t', '-c', 'user.email=t@t', '-c', 'init.defaultBranch=main']
remoto = os.path.join(tmp, 'remoto.git')
subprocess.run(G + ['init', '-q', '--bare', remoto], check=True)
trabajo = os.path.join(tmp, 'trabajo')
subprocess.run(G + ['clone', '-q', remoto, trabajo], check=True, stderr=subprocess.DEVNULL)
os.makedirs(os.path.join(trabajo, 'files/bin'))
open(os.path.join(trabajo, 'install.sh'), 'w').write('echo VIEJO\n')
open(os.path.join(trabajo, 'leeme'), 'w').write('1\n')
subprocess.run(G + ['-C', trabajo, 'add', '-A'], check=True)
subprocess.run(G + ['-C', trabajo, 'commit', '-qm', 'v1'], check=True)
subprocess.run(G + ['-C', trabajo, 'push', '-q', 'origin', 'main'], check=True, stderr=subprocess.DEVNULL)
kit2 = os.path.join(tmp, 'kit2')
subprocess.run(G + ['clone', '-q', remoto, kit2], check=True, stderr=subprocess.DEVNULL)
open(os.path.join(kit2, 'bricohams.env'), 'w').write('VAR_A="1"\n')   # sin seguimiento, como en la Pi


def vuelta(extra=''):
    c = CABECERA.replace('KIT=%s;' % kit, 'KIT=%s;' % kit2) + 'ARGS=(--actualizar); KIT_ANTES=""; KIT_DESPUES=""\n' + extra + \
        '\nkit_git; echo "FIN $KIT_ANTES $KIT_DESPUES"'
    r = subprocess.run(['bash', '-c', c], capture_output=True, text=True)
    return r


r = vuelta()
assert r.returncode == 0 and 'ya estaba al día' in r.stdout, (r.stdout, r.stderr)
# cambio que no toca install.sh: avanza sin volver a lanzarse
open(os.path.join(trabajo, 'leeme'), 'w').write('2\n')
subprocess.run(G + ['-C', trabajo, 'commit', '-qam', 'v2 leeme'], check=True)
subprocess.run(G + ['-C', trabajo, 'push', '-q'], check=True, stderr=subprocess.DEVNULL)
r = vuelta()
assert r.returncode == 0 and 'v2 leeme' in r.stdout and 'FIN ' in r.stdout and 'VIEJO' not in r.stdout, (r.stdout, r.stderr)
assert open(os.path.join(kit2, 'leeme')).read() == '2\n'
# install.sh nuevo: se vuelve a lanzar con --continuar y el registro ya abierto
open(os.path.join(trabajo, 'install.sh'), 'w').write(
    'echo "NUEVO $* log=$BRICOHAMS_LOG_ACTIVO antes=$BRICOHAMS_KIT_ANTES"\n')
subprocess.run(G + ['-C', trabajo, 'commit', '-qam', 'v3 install'], check=True)
subprocess.run(G + ['-C', trabajo, 'push', '-q'], check=True, stderr=subprocess.DEVNULL)
r = vuelta()
assert r.returncode == 0 and 'NUEVO --actualizar --continuar log=1 antes=' in r.stdout and 'FIN ' not in r.stdout, (r.stdout, r.stderr)
# cambios locales que chocan: para con instrucciones y no pierde nada
open(os.path.join(trabajo, 'leeme'), 'w').write('3\n')
subprocess.run(G + ['-C', trabajo, 'commit', '-qam', 'v4'], check=True)
subprocess.run(G + ['-C', trabajo, 'push', '-q'], check=True, stderr=subprocess.DEVNULL)
open(os.path.join(kit2, 'leeme'), 'w').write('cambio local\n')
r = vuelta()
assert r.returncode != 0 and 'git stash' in r.stdout, (r.stdout, r.stderr)
assert open(os.path.join(kit2, 'leeme')).read() == 'cambio local\n'
# --simular: cuenta lo que hay en el remoto sin bajarlo
subprocess.run(['git', '-C', kit2, 'checkout', '-q', 'leeme'], check=True)
r = vuelta('SIMULAR=1')
assert r.returncode == 0 and '1 cambios nuevos' in r.stdout and open(os.path.join(kit2, 'leeme')).read() == '2\n', (r.stdout, r.stderr)
# kit sin git (copiado del zip): avisa y sigue
shutil.rmtree(os.path.join(kit2, '.git'))
r = vuelta()
assert r.returncode == 0 and 'no es un clon de git' in r.stdout

# ------------------------------------------------------------------ marcadores en tres vías
spec = importlib.util.spec_from_file_location('mb', os.path.join(RAIZ, 'files/bin/bricohams-merge-bookmarks.py'))
mb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mb)
B = lambda f, n, m='nfm': {'name': n, 'frequency': f, 'modulation': m}  # noqa: E731
anterior = [B(145325000, 'viejo'), B(27335000, 'CB 33', 'am'), B(438775000, 'RU-75')]
actuales = anterior + [B(145500000, 'mi llamada'), B(145500000, 'mi llamada dup')]
nuevo = [B(145325000, 'Radio Club 145,325'), B(27325000, 'CB 32', 'am'), B(438775000, 'RU-75 · 77,0 Hz')]
res, n_kit, n_prop = mb.tres_vias(anterior, actuales, nuevo)
nombres = {(b['frequency'], b['name']) for b in res}
assert (145325000, 'Radio Club 145,325') in nombres and (145325000, 'viejo') not in nombres, 'el kit nuevo gana'
assert (27335000, 'CB 33') not in nombres, 'lo que el kit quitó no vuelve'
assert (145500000, 'mi llamada') in nombres and n_prop == 1, 'se conservan los propios (sin duplicar)'
res, _, n_prop = mb.tres_vias(None, actuales, nuevo)   # primera vez: sin kit anterior
assert n_prop == 2 and (27335000, 'CB 33') in {(b['frequency'], b['name']) for b in res}
d = tempfile.mkdtemp()
for n, v in (('a.json', anterior), ('x.json', actuales), ('n.json', nuevo)):
    json.dump(v, open(os.path.join(d, n), 'w'))
r = subprocess.run(['python3', os.path.join(RAIZ, 'files/bin/bricohams-merge-bookmarks.py'), '--tres',
                    os.path.join(d, 'a.json'), os.path.join(d, 'x.json'), os.path.join(d, 'n.json'), os.path.join(d, 'x.json')],
                   capture_output=True, text=True)
assert r.returncode == 0 and '3 del kit + 1 propios' in r.stdout, r
assert len(json.load(open(os.path.join(d, 'x.json')))) == 4
shutil.rmtree(d)
shutil.rmtree(tmp)

print('OK test_actualizar: huellas por paso (código, ficheros, variables), plan mínimo, variables nuevas sin tocar claves, '
      'git pull + nueva vuelta con install.sh nuevo, marcadores propios conservados')
