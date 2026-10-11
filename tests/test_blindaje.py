#!/usr/bin/env python3
"""v4.4 · bricohams-blindaje sobre un sistema de mentira (BH_RAIZ): el cortafuegos que genera
(y que nft lo acepta, si hay nft), la auditoría (fugas de claves sin enseñarlas nunca, permisos,
bricohams.env dentro del git, sudo sin contraseña, posición exacta publicada), «aplicar» (SSH solo
con clave únicamente si hay claves), «confirmar» y «deshacer»."""
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
import time

RAIZ_KIT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
B = os.path.join(RAIZ_KIT, 'files', 'bin', 'bricohams-blindaje')
SECRETO = 'ClaveDePrueba-9x7Q'
ANON = 'anonPublicaSupabase123'


def poner(raiz, ruta, texto, modo=0o644):
    p = raiz + ruta
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(texto)
    os.chmod(p, modo)


def correr(raiz, *args):
    env = dict(os.environ, BH_RAIZ=raiz, BH_VUELTA_SEG='60')
    r = subprocess.run(['bash', B] + list(args), capture_output=True, text=True, env=env)
    return r.returncode, r.stdout + r.stderr


def modo(raiz, ruta):
    return stat.S_IMODE(os.stat(raiz + ruta).st_mode)


# ------------------------------------------------------------------ 1. cortafuegos
def nft(raiz, extra=''):
    poner(raiz, '/etc/bricohams/bricohams.env', 'BLINDAJE_LAN="192.168.1.0/24"\n' + extra, 0o600)
    return correr(raiz, 'genera-nft')[1]


T = tempfile.mkdtemp()
r = nft(T)
assert 'policy drop' in r and 'tcp dport { 80, 443, 8073 } ct state new accept' in r, r
assert 'ip saddr @lan4 tcp dport { 22, 4403, 8554, 9443 }' in r and 'elements = { 192.168.1.0/24 }' in r
assert 'ct state established,related accept' in r and 'iif "lo" accept' in r and 'ipv6-icmp' in r
r2 = nft(T, 'BLINDAJE_8073="lan"\nBLINDAJE_SSH="todos"\nBLINDAJE_PUERTOS_LAN=""\n')
assert 'tcp dport { 80, 443, 22 } ct state new accept' in r2 and 'ip saddr @lan4 tcp dport { 8073 }' in r2, r2
r3 = nft(T, 'BLINDAJE_LAN="192.168.1.0/24, 10.8.0.0/24"\n')
assert 'elements = { 192.168.1.0/24, 10.8.0.0/24 }' in r3
if shutil.which('nft') and os.geteuid() == 0:
    for x in (r, r2, r3):
        f = os.path.join(T, 'x.nft'); open(f, 'w').write(x)
        c = subprocess.run(['nft', '-c', '-f', f], capture_output=True, text=True)
        assert c.returncode == 0 or 'Operation not permitted' in c.stderr, c.stderr
shutil.rmtree(T)

# ------------------------------------------------------------------ 2. auditoría
A = tempfile.mkdtemp()
HT = '/usr/lib/python3/dist-packages/htdocs'
poner(A, '/etc/os-release', 'PRETTY_NAME="Debian GNU/Linux 13 (trixie)"\n')
poner(A, '/etc/bricohams/bricohams.env', "CALLSIGN='EA5ZZZ'\nQRZ_PASS='%s'\nLISTENERS_SUPABASE_KEY='%s'\nSSL_MODO='admin'\n"
      "BLINDAJE_8073='publico'\nOWRX_DATA='/var/lib/openwebrx'\nOWRX_HTDOCS='%s'\n" % (SECRETO, ANON, HT), 0o644)
poner(A, '/etc/bricohams/meteo.env', "AEMET_API_KEY='x'\n", 0o644)
poner(A, HT + '/plugins/receiver/fuga/fuga.js', 'var k = "%s";' % SECRETO)                     # fuga de verdad
poner(A, HT + '/plugins/receiver/init.js', "const LISTENERS = { key: '%s' };\nwindow.solar_config = { lat: 0.0, lon: 0.0 };\n" % ANON)
poner(A, '/var/lib/openwebrx/settings.json', json.dumps({'receiver_gps': {'lat': 0.0, 'lon': 0.0}, 'receiver_admin': 'a@b.es'}), 0o644)
poner(A, '/var/lib/openwebrx/users.json', '[]', 0o644)
poner(A, '/etc/shadow', 'root:!:1::::::\nvacio::1::::::\naelm:$y$hash:1::::::\n', 0o640)
poner(A, '/etc/sudoers.d/010_pi-nopasswd', 'pi ALL=(ALL) NOPASSWD: ALL\n', 0o440)
poner(A, '/etc/sudoers.d/bricohams', 'bricohams ALL=(root) NOPASSWD: /usr/local/sbin/bricohams-tarea\n', 0o440)
kit = A + '/home/pi/bricohams-sdr'
poner(A, '/home/pi/bricohams-sdr/bricohams.env', "QRZ_PASS='%s'\n" % SECRETO, 0o644)
subprocess.run(['git', 'init', '-q', kit], check=True)
subprocess.run(['git', '-C', kit, 'add', 'bricohams.env'], check=True)
os.makedirs(A + '/var/backups/bricohams', mode=0o755)
os.chmod(A + '/var/backups/bricohams', 0o755)
poner(A, '/var/backups/bricohams/backup-openwebrx-2026-10-10.tar.gz', 'x', 0o644)
rc, out = correr(A, 'auditar')
assert SECRETO not in out and ANON not in out, 'el informe nunca enseña una clave'
assert rc != 0, 'con hallazgos altos sale con error'
assert re.search(r'clave QRZ_PASS aparece en .*fuga\.js', out), out
assert 'LISTENERS_SUPABASE_KEY aparece' not in out, 'la clave anon de Supabase es pública por diseño'
assert 'cuentas SIN contraseña: vacio' in out
assert 'sudo sin contraseña: pi' in out and 'bricohams ALL' not in out
assert 'bricohams.env está DENTRO del git' in out
assert re.search(r'copia de bricohams.env en /etc: /etc/bricohams/bricohams.env tiene permisos 644', out)
assert re.search(r'bricohams.env del kit .* tiene permisos 644', out)
assert 'users.json (contraseñas de admin): /var/lib/openwebrx/users.json tiene permisos 644' in out
assert 'publica la posición exacta de tu casa' in out and 'init.js (lo descarga cualquiera) lleva la posición exacta' in out
assert 'receiver_admin publica tu correo' in out
assert 'copias de seguridad (llevan claves y usuarios): /var/backups/bricohams tiene permisos 755' in out
assert 'router abre el 8073 a Internet' in out
assert re.search(r'Resultado: \d+ alto', out)
rc, res = correr(A, 'auditar', '--resumen')
assert res.count('\n') <= 3 and 'Resultado:' in res, res

# ------------------------------------------------------------------ 3. aplicar / confirmar / deshacer
poner(A, '/etc/apt/apt.conf.d/20auto-upgrades', '// el de antes\n')
rc, out = correr(A, 'aplicar', '--sudo-con-clave')
assert rc == 0, out
assert SECRETO not in out
for f in ('/etc/sysctl.d/90-bricohams.conf', '/etc/fail2ban/jail.d/bricohams.conf', '/etc/bricohams/cortafuegos.nft',
          '/etc/systemd/system/bricohams-cortafuegos.service', '/etc/systemd/system/openwebrx.service.d/bricohams-umask.conf',
          '/etc/ssh/sshd_config.d/90-bricohams.conf'):
    assert os.path.exists(A + f), f
ssh = open(A + '/etc/ssh/sshd_config.d/90-bricohams.conf').read()
assert 'PermitRootLogin no' in ssh and 'MaxAuthTries 3' in ssh
assert 'PasswordAuthentication no' not in ssh, 'sin claves en authorized_keys NO se quita la contraseña (te quedarías fuera)'
assert 'sigue aceptando contraseña porque no hay claves' in out
assert modo(A, '/etc/bricohams/bricohams.env') == 0o600 and modo(A, '/home/pi/bricohams-sdr/bricohams.env') == 0o600
assert modo(A, '/var/lib/openwebrx/users.json') == 0o600 and modo(A, '/var/lib/openwebrx/settings.json') & 0o007 == 0
assert modo(A, '/etc/bricohams/meteo.env') & 0o007 == 0
assert modo(A, '/var/backups/bricohams') == 0o700 and modo(A, '/var/backups/bricohams/backup-openwebrx-2026-10-10.tar.gz') & 0o077 == 0
assert 'NOPASSWD' in open(A + '/etc/sudoers.d/bricohams').read(), 'la cuenta de servicio sigue sin contraseña (solo bricohams-tarea)'
assert open(A + '/etc/sudoers.d/010_pi-nopasswd').read().startswith('# bricohams-blindaje: pi')
assert 'Unattended-Upgrade "1"' in open(A + '/etc/apt/apt.conf.d/20auto-upgrades').read()
assert 'UMask=0027' in open(A + '/etc/systemd/system/openwebrx.service.d/bricohams-umask.conf').read()
assert os.path.exists(A + '/var/backups/bricohams-blindaje/pendiente') and 'confirmar' in out
rc, out = correr(A, 'confirmar')
assert rc == 0 and not os.path.exists(A + '/var/backups/bricohams-blindaje/pendiente')
# con claves SSH: solo clave
poner(A, '/home/pi/.ssh/authorized_keys', 'ssh-ed25519 AAAA… pi@pc\n', 0o600)
time.sleep(1.1)
rc, out = correr(A, 'aplicar', '--sin-cortafuegos')
assert rc == 0 and 'PasswordAuthentication no' in open(A + '/etc/ssh/sshd_config.d/90-bricohams.conf').read(), out
# deshacer la última (SSH vuelve a la de la primera pasada) y luego la primera (todo como al principio)
rc, out = correr(A, 'deshacer')
assert rc == 0 and 'PasswordAuthentication no' not in open(A + '/etc/ssh/sshd_config.d/90-bricohams.conf').read(), out
rc, out = correr(A, 'deshacer')
assert rc == 0, out
for f in ('/etc/sysctl.d/90-bricohams.conf', '/etc/fail2ban/jail.d/bricohams.conf', '/etc/ssh/sshd_config.d/90-bricohams.conf',
          '/etc/bricohams/cortafuegos.nft', '/etc/systemd/system/openwebrx.service.d/bricohams-umask.conf'):
    assert not os.path.exists(A + f), ('deshacer debe quitar lo creado', f)
assert open(A + '/etc/apt/apt.conf.d/20auto-upgrades').read() == '// el de antes\n'
assert open(A + '/etc/sudoers.d/010_pi-nopasswd').read() == 'pi ALL=(ALL) NOPASSWD: ALL\n'
rc, out = correr(A, 'deshacer')
assert rc != 0 and 'no hay copias' in out
rc, out = correr(A, 'aplicar', '--opcion-rara')
assert rc != 0 and 'opción desconocida' in out
shutil.rmtree(A)

S = open(os.path.join(RAIZ_KIT, 'install.sh'), encoding='utf-8').read()
assert 'install -m 755 "$FILES/bin/bricohams-blindaje" /usr/local/sbin/bricohams-blindaje' in S
print('OK test_blindaje: cortafuegos (público 80/443/8073, SSH y resto solo LAN, nft -c), auditoría sin enseñar claves '
      '(fugas, permisos, env en git, sudo, posición exacta), aplicar/confirmar/deshacer y SSH solo-clave solo si hay claves')
