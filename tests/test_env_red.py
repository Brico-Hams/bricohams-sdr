#!/usr/bin/env python3
"""v4.2 · Los dos fallos de la instalación real en la Pi de EA5KAO:
  1. «bricohams.env: line 182: Clave2026: unbound variable»: una clave con «$».
     → bricohams-env.py lee el fichero sin ejecutarlo; los .env derivados van entre comillas simples.
  2. «curl: (6) Could not resolve host: luarvique.github.io» justo después del paso «red».
     → paso_red modifica la conexión en vez de borrarla, esperar_red antes de cada paso,
       claves y scripts de terceros con reintentos y error claro.
Y la auditoría de «[ … ] && …» como última orden de una función (el arreglo de paso_web)."""
import glob
import os
import re
import shlex
import subprocess
import tempfile

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
ENVPY = os.path.join(RAIZ, 'files/bin/bricohams-env.py')
S = open(os.path.join(RAIZ, 'install.sh'), encoding='utf-8').read()


def envpy(modo, texto):
    with tempfile.NamedTemporaryFile('w', suffix='.env', delete=False, encoding='utf-8') as f:
        f.write(texto)
    r = subprocess.run(['python3', ENVPY, modo, f.name], capture_output=True, text=True)
    os.unlink(f.name)
    return r


# ---------------------------------------------------------------- 1. lector de bricohams.env
CASO = r'''# comentario
QRZ_USER="EA5KAO"
QRZ_PASS="abc&def\$Clave2026"                       # secreta: con \$ escapado (lo que hizo EA5KAO)
HAMQTH_PASS="abc$Clave2026"          # $ sin escapar: ahora literal (antes: unbound variable)
TELEGRAM_TOKEN='123:AA$bb"cc'
export WIFI_PASS="Wifi@Prueba!"
VACIA=""
SIN_COMILLAS=ES   # país
CON_COMILLA="o'brien"
ESPACIOS="EA5KAO WX · Mi QTH"
'''
r = envpy('--shell', CASO)
assert r.returncode == 0, r.stderr
assert 'HAMQTH_PASS' in r.stderr and 'LITERAL' in r.stderr, 'debe avisar del $ sin escapar'
bash = subprocess.run(['bash', '-c', 'set -Eeuo pipefail\neval "$1"\nfor v in QRZ_USER QRZ_PASS HAMQTH_PASS TELEGRAM_TOKEN WIFI_PASS VACIA SIN_COMILLAS CON_COMILLA ESPACIOS; do printf "%s=[%s]\\n" "$v" "${!v}"; done',
                       '_', r.stdout], capture_output=True, text=True)
assert bash.returncode == 0, bash.stderr
esperado = {'QRZ_USER': 'EA5KAO', 'QRZ_PASS': 'abc&def$Clave2026', 'HAMQTH_PASS': 'abc$Clave2026',
            'TELEGRAM_TOKEN': '123:AA$bb"cc', 'WIFI_PASS': 'Wifi@Prueba!', 'VACIA': '', 'SIN_COMILLAS': 'ES',
            'CON_COMILLA': "o'brien", 'ESPACIOS': 'EA5KAO WX · Mi QTH'}
got = dict(re.findall(r'^(\w+)=\[(.*)\]$', bash.stdout, re.M))
assert got == esperado, got
# la copia normalizada se lee igual con bash (scripts) y con reglas de shell (systemd/python)
n = envpy('--normalizar', CASO)
assert n.returncode == 0
b2 = subprocess.run(['bash', '-c', 'set -u; . /dev/stdin; printf "%s|%s|%s" "$QRZ_PASS" "$CON_COMILLA" "$ESPACIOS"'],
                    input=n.stdout, capture_output=True, text=True)
assert b2.stdout == "abc&def$Clave2026|o'brien|EA5KAO WX · Mi QTH", b2
for linea in n.stdout.splitlines():
    if linea and not linea.startswith('#'):
        k, _, v = linea.partition('=')
        assert shlex.split(v) in ([esperado[k]], []) and (esperado[k] or v == "''"), (k, v)
# errores de sintaxis: se paran con mensaje y número de línea
for malo, msg in (('A="sin cerrar\n', 'comillas dobles'), ("B='x\n", 'comillas simples'),
                  ('C=dos palabras\n', 'faltan comillas'), ('esto no\n', 'NOMBRE=valor'),
                  ('UID="5"\n', 'variable del sistema')):
    r = envpy('--shell', malo)
    assert r.returncode == 1 and msg in r.stderr and 'línea 1' in r.stderr, (malo, r.stderr)
# el bricohams.env.example real se lee igual que con bash (no tiene «$»)
ej = open(os.path.join(RAIZ, 'bricohams.env.example'), encoding='utf-8').read()
r = envpy('--shell', ej)
assert r.returncode == 0 and r.stderr == '', r.stderr
nombres = re.findall(r'^export (\w+)=', r.stdout, re.M)
script = 'set -a; . "$1"; set +a; for v in %s; do printf "%%s=%%s\\0" "$v" "${!v}"; done' % ' '.join(nombres)
with tempfile.NamedTemporaryFile('w', suffix='.env', delete=False, encoding='utf-8') as f:
    f.write(ej)
con_bash = subprocess.run(['bash', '-c', script, '_', f.name], capture_output=True, text=True).stdout
script2 = 'eval "$1"; for v in %s; do printf "%%s=%%s\\0" "$v" "${!v}"; done' % ' '.join(nombres)
con_lector = subprocess.run(['bash', '-c', script2, '_', r.stdout], capture_output=True, text=True).stdout
os.unlink(f.name)
assert con_bash == con_lector and len(nombres) > 100, 'el lector debe dar lo mismo que bash con el .example'

# install.sh ya no ejecuta bricohams.env y los .env derivados van entre comillas
assert '. "$KIT/bricohams.env"' not in S and 'set -a; . "$KIT/bricohams.env"' not in S
assert S.count('cargar_env "$KIT/bricohams.env"') >= 3
assert 'instalar_env "$ETC_BH/bricohams.env"' in S and 'install -m 600 "$KIT/bricohams.env"' not in S
for secreto in ('HAMQTH_PASS', 'QRZ_PASS', 'TELEGRAM_TOKEN', 'DUCKDNS_TOKEN'):
    assert 'envl %s ' % secreto in S, secreto
assert 'APRS_PASSCODE=$(sq "${APRS_PASSCODE:-}")' in S and 'AEMET_API_KEY=$(sq "${AEMET_API_KEY:-}")' in S
sqf = re.search(r'^sq\(\) \{.*\}$', S, re.M).group(0)
envl = re.search(r'^envl\(\) \{.*\}$', S, re.M).group(0)
out = subprocess.run(['bash', '-c', sqf + '\n' + envl + '\nenvl X "$1"', '_', "a'b$c d"], capture_output=True, text=True).stdout
assert subprocess.run(['bash', '-c', 'set -u; ' + out + 'printf %s "$X"'], capture_output=True, text=True).stdout == "a'b$c d"

# ---------------------------------------------------------------- 2. red
red = re.search(r'^paso_red\(\) \{.*?^\}', S, re.S | re.M).group(0)
assert 'connection delete' not in red and 'connection modify' in red and red.rstrip().endswith('esperar_red\n}'), red
assert 'if necesita_red "$PASO_ACTUAL"; then esperar_red; fi' in S
# solo esperan a la red los pasos que bajan algo (revisión v4.2: «--solo red» sin WiFi no debe quedarse esperando)
nr = re.search(r'^necesita_red\(\) \{.*?^\}', S, re.S | re.M).group(0)
pasos = {p: re.search(r'^paso_%s\(\) \{.*?^\}' % p, S, re.S | re.M).group(0) for p in ('red', 'comprobar', 'openwebrx', 'base', 'configuracion', 'hat', 'adsb', 'web')}
r = subprocess.run(['bash', '-c', nr + '\n' + '\n'.join(pasos.values()) + '\nfor p in %s; do if necesita_red $p; then echo "$p:si"; else echo "$p:no"; fi; done' % ' '.join(pasos)],
                   capture_output=True, text=True)
res = dict(l.split(':') for l in r.stdout.split())
assert res == {'red': 'no', 'comprobar': 'no', 'openwebrx': 'si', 'base': 'si', 'configuracion': 'no', 'hat': 'si', 'adsb': 'si', 'web': 'si'}, res
assert 'bash -c "$(wget' not in S and 'curl -fsSL https://luarvique' not in S
assert S.count('clave_apt ') >= 4 and S.count('script_remoto ') >= 4
esp = re.search(r'^esperar_red\(\) \{.*?^\}', S, re.S | re.M).group(0)
sim = '''set -Eeuo pipefail
N=0; bien() { echo "BIEN $*"; }; aviso() { echo "AVISO $*"; }; fallo() { echo "FALLO $*"; exit 1; }
sleep() { :; }; nmcli() { :; }
getent() { N=$((N+1)); [ "$N" -gt "$FALLOS" ]; }
%s
esperar_red; echo FIN''' % esp
r = subprocess.run(['bash', '-c', 'FALLOS=3\n' + sim], capture_output=True, text=True)
assert r.returncode == 0 and 'red disponible tras' in r.stdout and 'FIN' in r.stdout, (r.stdout, r.stderr)
r = subprocess.run(['bash', '-c', 'FALLOS=999\n' + sim], capture_output=True, text=True)
assert r.returncode == 1 and 'FALLO' in r.stdout and 'FIN' not in r.stdout
r = subprocess.run(['bash', '-c', 'FALLOS=0\n' + sim], capture_output=True, text=True)
assert r.stdout.strip() == 'FIN', 'con red no debe decir nada'
srem = re.search(r'^script_remoto\(\) \{.*?^\}', S, re.S | re.M).group(0)
r = subprocess.run(['bash', '-c', 'set -Eeuo pipefail\nesperar_red() { :; }\nCURL=(false)\n%s\nif script_remoto http://x; then echo MAL; else echo BIEN; fi' % srem],
                   capture_output=True, text=True)
assert 'BIEN' in r.stdout, 'una descarga fallida no puede pasar por buena'

# ---------------------------------------------------------------- 3. «[ … ] && …» al final de una función
def es_bash(f):
    if not os.path.isfile(f):
        return False
    with open(f, errors='ignore') as fh:
        return 'bash' in fh.readline()


malas = []
for p in [os.path.join(RAIZ, 'install.sh')] + [f for f in glob.glob(os.path.join(RAIZ, 'files/bin/*')) if es_bash(f)]:
    s = open(p, errors='ignore').read()
    for m in re.finditer(r'^(\w[\w-]*)\(\) \{\n(.*?)^\}', s, re.S | re.M):
        lineas = [x.strip() for x in m.group(2).split('\n') if x.strip() and not x.strip().startswith('#')]
        if lineas and re.match(r'^(\[\[?|test |grep |command -v)[^|]*&&', lineas[-1]) and '||' not in lineas[-1]:
            malas.append('%s:%s' % (os.path.basename(p), m.group(1)))
assert not malas, 'funciones que acaban en «[ … ] && …» (devuelven 1 con set -e): %s' % malas

print('OK test_env_red: claves con «$» sin romper el instalador, .env derivados entre comillas, '
      'espera de red y descargas con reintento, sin «[ ] &&» al final de funciones')
