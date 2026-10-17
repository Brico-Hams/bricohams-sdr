#!/bin/bash
set -Eeuo pipefail
umask 077
[[ $EUID -eq 0 ]] || { echo "Ejecuta con sudo." >&2; exit 1; }
NUEVO="${1:?Ruta del kit nuevo}"
KIT="${2:?Ruta del kit instalado}"
[[ "$NUEVO" = /* && "$KIT" = /* ]] || exit 1
python3 - "$NUEVO" "$KIT" <<'PY'
import ast
import json
from pathlib import Path
import sys
import time
nuevo, kit = map(Path, sys.argv[1:])
for nombre in ('bricohams-mesh-admin', 'bricohams-satpass.py', 'bricohams_telegram.py',
               'bricohams-visitas.py', 'bricohams-login-aviso'):
    ast.parse((nuevo / 'files/bin' / nombre).read_text())
for nombre, clave in (('pases.json', 'pases'), ('grabaciones.json', 'plan')):
    ruta = Path('/usr/lib/python3/dist-packages/htdocs/plugins/receiver/satelites') / nombre
    if any(p['aos'] - 90 <= time.time() <= p['los'] + 90 for p in json.loads(ruta.read_text())[clave]):
        raise RuntimeError('Pase protegido: no se ha modificado nada; repetir al terminar.')
if not (kit / 'bricohams.env').is_file():
    raise RuntimeError('Kit instalado no valido')
settings = json.loads(Path('/var/lib/openwebrx/settings.json').read_text())
perfil = json.loads((nuevo / 'files/openwebrx/settings.json.tmpl').read_text())['sdrs']['sat']['profiles']['sat400']
actual = settings['sdrs']['sat']['profiles'].get('sat400')
if actual is not None and actual != perfil:
    raise RuntimeError('Perfil sat400 personalizado: no se ha modificado nada.')
PY
B="/var/backups/bricohams/agenda-telegram-$(date +%Y%m%d-%H%M%S)-$$"
install -d -m 700 "$B"
python3 - "$NUEVO" "$KIT" "$B" <<'PY'
import json
from pathlib import Path
import shlex
import sys
nuevo, kit, backup = map(Path, sys.argv[1:])
def leer(ruta):
    env = {}
    for linea in ruta.read_text().splitlines():
        if '=' in linea and not linea.lstrip().startswith('#'):
            k, v = linea.split('=', 1)
            partes = shlex.split(v, comments=True)
            env[k.strip()] = partes[0] if partes else ''
    return env
env = leer(Path('/etc/bricohams/bricohams.env'))
catalogo = Path(env.get('SAT_LIST', '/opt/bricohams/kit/data/satelites.json'))
copias = {}
for nombre, destino in (
    ('bricohams-mesh-admin', '/usr/local/bin/bricohams-mesh-admin'),
    ('bricohams-satpass.py', '/usr/local/bin/bricohams-satpass'),
    ('bricohams_telegram.py', '/usr/local/bin/bricohams_telegram.py'),
    ('bricohams-telegram', '/usr/local/bin/bricohams-telegram'),
    ('bricohams-visitas.py', '/usr/local/bin/bricohams-visitas'),
    ('bricohams-login-aviso', '/usr/local/sbin/bricohams-login-aviso'),
    ('bricohams-tarea', '/usr/local/sbin/bricohams-tarea')):
    copias[str(Path(destino))] = str(nuevo / 'files/bin' / nombre)
    copias[str(kit / 'files/bin' / nombre)] = str(nuevo / 'files/bin' / nombre)
for relativo in ('install.sh', 'data/satelites.json', 'files/openwebrx/settings.json.tmpl',
                 'files/htdocs/plugins/receiver/satelites/satelites.js'):
    copias[str(kit / relativo)] = str(nuevo / relativo)
copias[str(catalogo)] = str(nuevo / 'data/satelites.json')
copias['/usr/lib/python3/dist-packages/htdocs/plugins/receiver/satelites/satelites.js'] = str(
    nuevo / 'files/htdocs/plugins/receiver/satelites/satelites.js')
entornos = ['/etc/bricohams/bricohams.env', str(kit / 'bricohams.env'),
            '/etc/bricohams/telegram.env', '/etc/bricohams/api.env', '/etc/bricohams/visitas.env']
otros = ['/var/lib/openwebrx/settings.json', '/etc/cron.d/bricohams',
         '/var/lib/bricohams/tle.json']
for nombre in ('pases.json', 'grabaciones.json', 'pases.ics'):
    otros.append('/usr/lib/python3/dist-packages/htdocs/plugins/receiver/satelites/' + nombre)
rutas = list(dict.fromkeys(list(copias) + entornos + otros))
presentes, ausentes = [], []
for ruta in rutas:
    p = Path(ruta)
    if not p.is_absolute() or p.is_symlink() or p.is_dir():
        raise RuntimeError('Destino no admitido: ' + ruta)
    (presentes if p.is_file() else ausentes).append(ruta.lstrip('/'))
(backup / 'archivos.txt').write_text('\n'.join(presentes) + '\n')
(backup / 'ausentes.txt').write_text('\n'.join(ausentes) + ('\n' if ausentes else ''))
(backup / 'operaciones.json').write_text(json.dumps({'copias': copias, 'entornos': entornos}))
PY
tar --acls --xattrs -czf "$B/previo.tar.gz" -C / -T "$B/archivos.txt"
tar --compare --gzip --file "$B/previo.tar.gz" -C /
sha256sum "$B/previo.tar.gz" "$B/ausentes.txt" >"$B/SHA256SUMS"
sha256sum -c "$B/SHA256SUMS"
cat >"$B/RESTAURAR.sh" <<'EOF'
#!/bin/bash
set -Eeuo pipefail
[[ $EUID -eq 0 ]] || exit 1
B="$(cd "$(dirname "$0")" && pwd)"
sha256sum -c "$B/SHA256SUMS"
while IFS= read -r ruta; do
    [[ -n "$ruta" && "$ruta" != *".."* && "$ruta" != /* ]] || exit 1
    rm -f -- "/$ruta"
done <"$B/ausentes.txt"
tar --acls --xattrs -xzf "$B/previo.tar.gz" -C /
systemctl restart openwebrx bricohams-satrec bricohams-mesh-admin bricohams-api bricohams-visitas bricohams-login-aviso
EOF
chmod 700 "$B/RESTAURAR.sh"
bash -n "$B/RESTAURAR.sh"
echo "BACKUP_VERIFICADO=$B"
echo "RESTAURACION: sudo bash $B/RESTAURAR.sh"
trap 'echo "ERROR: restaura con sudo bash $B/RESTAURAR.sh" >&2' ERR
python3 - "$NUEVO" "$B" <<'PY'
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
nuevo, backup = map(Path, sys.argv[1:])
ops = json.loads((backup / 'operaciones.json').read_text())
for destino, origen in ops['copias'].items():
    shutil.copyfile(origen, destino)
    os.chmod(destino, 0o755 if '/bin/' in destino or '/sbin/' in destino or destino.endswith('install.sh') else 0o644)
def guardar(ruta, texto):
    p = Path(ruta)
    st = p.stat()
    fd, tmp = tempfile.mkstemp(dir=p.parent, prefix='.agenda-telegram-')
    with os.fdopen(fd, 'w') as f:
        f.write(texto)
    os.chmod(tmp, st.st_mode & 0o777)
    os.chown(tmp, st.st_uid, st.st_gid)
    os.replace(tmp, p)
auxiliar = Path('/etc/bricohams/telegram.env').read_text()
credenciales = {}
for k in ('TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID'):
    m = re.search(r'^' + k + r'=(.*)$', auxiliar, re.M)
    if not m or not m[1].strip():
        raise RuntimeError('Credenciales auxiliares ausentes: no se puede sincronizar')
    credenciales[k] = m[1]
for ruta in ops['entornos']:
    texto = Path(ruta).read_text()
    cambios = dict(credenciales)
    if not ruta.endswith(('api.env', 'telegram.env')):
        cambios['VISITAS_AVISAR_LAN'] = '"yes"'
    if ruta.endswith('/bricohams.env'):
        cambios['TG_AVISO_LOGIN'] = '"yes"'
    for k, v in cambios.items():
        linea = k + '=' + v
        texto = re.sub(r'^' + k + r'=.*$', lambda m: linea, texto, flags=re.M) if re.search(
            r'^' + k + '=', texto, re.M) else texto.rstrip() + '\n' + linea + '\n'
    guardar(ruta, texto)
p = '/var/lib/openwebrx/settings.json'
settings = json.loads(Path(p).read_text())
plantilla = json.loads((nuevo / 'files/openwebrx/settings.json.tmpl').read_text())
perfiles = settings['sdrs']['sat']['profiles']
perfil = plantilla['sdrs']['sat']['profiles']['sat400']
if 'sat400' in perfiles and perfiles['sat400'] != perfil:
    raise RuntimeError('Perfil sat400 personalizado: no se sobrescribe')
perfiles['sat400'] = perfil
guardar(p, json.dumps(settings, ensure_ascii=False, indent=4) + '\n')
p = '/etc/cron.d/bricohams'
cron = Path(p).read_text()
if not re.search(r'bricohams-tarea estado\s*$', cron, re.M):
    cron += '\n0 */6 * * * bricohams sudo -n /usr/local/sbin/bricohams-tarea estado\n'
guardar(p, cron)
print('Catalogo, perfil400, filtros y destinos Telegram sincronizados; secretos no mostrados.')
PY
bash -n "$KIT/install.sh"
bash -n /usr/local/bin/bricohams-telegram
bash -n /usr/local/sbin/bricohams-tarea
systemctl restart openwebrx bricohams-satrec bricohams-mesh-admin bricohams-api bricohams-visitas bricohams-login-aviso
systemctl is-active --quiet openwebrx bricohams-satrec bricohams-mesh-admin bricohams-api bricohams-visitas bricohams-login-aviso
systemctl restart bricohams-satpass
/usr/local/sbin/bricohams-tarea estado
echo "DESPLIEGUE_COMPLETO: servicios activos y estado aceptado por Telegram."
