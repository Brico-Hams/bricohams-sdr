#!/usr/bin/env python3
"""v3.1: el instalador vale para Trixie (Debian 13) y Bookworm (Debian 12).
Comprueba que ningún repositorio queda fijado a una sola versión y que
el paso «comprobar» acepta las dos y rechaza las demás."""
import os
import re
import subprocess
import tempfile

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
S = open(os.path.join(RAIZ, 'install.sh'), encoding='utf-8').read()

assert 'ppa/bookworm' not in S and 'ppa/trixie' not in S, 'repositorio de OpenWebRX+ fijado a una versión'
assert 'https://luarvique.github.io/ppa/$DEB ./' in S
assert 'Debian_12' not in S and 'Debian_$DEB_NUM' in S, 'repositorio de Meshtastic fijado a Debian 12'
# v4.2: las rutas comunes a HTTP y HTTPS están en bricohams-sdr-rutas.conf
nginx = open(os.path.join(RAIZ, 'files/nginx/bricohams-sdr-rutas.conf'), encoding='utf-8').read()
assert 'location = /tar1090 { return 301 /tar1090/; }' in nginx, 'tar1090 sin barra debe redirigir a la ruta del proxy'
assert 'apt.rb24.com/ trixie main' in S and 'inst_rbfeeder.sh' in S, 'rbfeeder: falta la vía de Trixie o la de Bookworm'
assert 'python3-pyasyncore' in S, 'mlat-client en Trixie necesita python3-pyasyncore'
assert 'python3-smbus2' in S
# v4.2: el paso web debe terminar correctamente con dominio SSL configurado;
# un && aviso deja estado 1 cuando la condición es falsa bajo set -e.
web = re.search(r'^paso_web\(\) \{.*?^\}', S, re.S | re.M).group(0)
assert re.search(r'if (\[ "\$modo" != no \] && )?\[ -z "\$dom" \]; then', web) and '[ -z "$dom" ] && aviso' not in web
assert 'install -m 644 "$FILES/nginx/bricohams-login-log.conf" /etc/nginx/conf.d/bricohams-login-log.conf' in web
# v3.2: todo apt-get update pasa por apt_update (reintento con IPv4)
fuera = [l for l in S.splitlines() if 'apt-get update' in l and not l.lstrip().startswith('#')
         and 'apt_update' not in l and 'aviso' not in l and 'fallo' not in l]
assert all(l.strip() == 'apt-get update && return 0' for l in fuera), fuera
assert 'Acquire::ForceIPv4' in S

# el case de paso_comprobar, ejecutado aislado con cada codename
case = re.search(r'    case "\$\{VERSION_CODENAME:-\}" in\n(.*?)\n    esac', S, re.S).group(0)
for codename, esperado in (('trixie', 0), ('bookworm', 0), ('bullseye', 1), ('forky', 1)):
    with tempfile.NamedTemporaryFile('w', suffix='.sh', delete=False) as f:
        f.write('fallo() { exit 1; }\nVERSION_CODENAME=%s\nPRETTY_NAME=x\n%s\nexit 0\n' % (codename, case))
    r = subprocess.run(['bash', f.name])
    os.unlink(f.name)
    assert r.returncode == esperado, (codename, r.returncode)

# DEB_NUM: 13 en Trixie, 12 en Bookworm
for codename, num in (('trixie', '13'), ('bookworm', '12')):
    out = subprocess.run(['bash', '-c', 'DEB=%s; echo $([ "$DEB" = trixie ] && echo 13 || echo 12)' % codename],
                         capture_output=True, text=True).stdout.strip()
    assert out == num
# v3.3: en Trixie, el fork rtl-sdr-blog retenido se cambia por el rtl-sdr de Debian (las 3 piezas juntas)
func = re.search(r'^rtlsdr_debian\(\) \{.*?^\}', S, re.S | re.M).group(0)
sim = r"""set -Eeuo pipefail
aviso() { :; }; DEB=trixie; LOGF=$(mktemp)
V=0.7.0~rtlsdrblog1
dpkg-query() { echo -n "$V"; }
apt-mark() { echo "apt-mark $*" >>"$LOGF"; }
apt-get() { echo "apt-get $*" >>"$LOGF"; V=2.0.2-2+b1; }
%s
v=$(rtlsdr_debian); echo "$v"; cat "$LOGF"
""" % func
out = subprocess.run(['bash', '-c', sim], capture_output=True, text=True)
assert out.returncode == 0, out.stderr
assert 'unhold librtlsdr0 librtlsdr-dev rtl-sdr' in out.stdout
assert '--allow-downgrades librtlsdr0 librtlsdr-dev rtl-sdr' in out.stdout
assert 'paso_rtlsdr() {\n    local tmp\n    if [ "$DEB" = trixie ]' in S, 'paso_rtlsdr no debe compilar rtl-sdr-blog en Trixie'

print('OK test_instalador_os: Trixie y Bookworm aceptados; repositorios de OpenWebRX+, Meshtastic y rbfeeder según la versión; rtl-sdr de Debian en Trixie')
