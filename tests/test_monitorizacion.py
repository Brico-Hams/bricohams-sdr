#!/usr/bin/env python3
"""v5.0 · paso_monitorizacion de install.sh (Prometheus + node-exporter + Grafana).

Comprueba, sin instalar nada:
  - la fusión de prometheus.yml (script Python embebido): conserva trabajos ajenos, descarta duplicados
    de prometheus/node y es idempotente;
  - la prioridad de la clave de Grafana: GRAFANA_ADMIN_PASS > grafana-access.txt > aleatoria (líneas reales);
  - grafana.ini: solo 127.0.0.1, sub-ruta /settings/bricohams/grafana/, [paths] para «grafana cli», sin registro;
  - adopción de instalaciones manuales: drop-ins con 127.0.0.1 y ExecStart= vacío;
  - nginx: Grafana solo detrás de auth_request (sesión de administrador) y líneas #@GF@ que paso_web activa o borra;
  - el panel de Grafana es JSON válido y usa la fuente «prometheus».
"""
import json
import os
import re
import subprocess
import sys
import tempfile

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INST = open(os.path.join(R, 'install.sh'), encoding='utf-8').read()

m = re.search(r'\npaso_monitorizacion\(\) \{\n(.*?)\n\}\n', INST, re.S)
assert m, 'paso_monitorizacion no encontrado en install.sh'
PASO = m.group(1)
assert 'monitorizacion' in re.search(r'PASOS=\(?["\']?([^\n]*)', INST).group(1), 'monitorizacion debe estar en PASOS'
assert 'si "${MONITORIZACION:-no}"' in PASO, 'el paso debe poder desactivarse con MONITORIZACION=no'

# --- 1. fusión de prometheus.yml -------------------------------------------------------------------------
py = re.search(r"python3 - \"\$py\" <<'PY'[^\n]*\n(.*?)\nPY\n", PASO, re.S)
assert py, 'script de fusión de prometheus.yml no encontrado'
SCRIPT = py.group(1)
try:
    import yaml
except ImportError:
    yaml = None

d = tempfile.mkdtemp()
try:
    s = os.path.join(d, 'fusion.py')
    open(s, 'w', encoding='utf-8').write(SCRIPT)
    ruta = os.path.join(d, 'prometheus.yml')
    open(ruta, 'w', encoding='utf-8').write(
        "global:\n  scrape_interval: 15s\nscrape_configs:\n"
        "  - job_name: prometheus\n    static_configs:\n      - targets: ['localhost:9090']\n"
        "  - job_name: node_exporter\n    static_configs:\n      - targets: ['localhost:9100']\n"
        "  - job_name: duplicado\n    static_configs:\n      - targets: ['0.0.0.0:9100']\n"
        "  - job_name: openwebrx\n    static_configs:\n      - targets: ['127.0.0.1:8000']\n")

    def fusion():
        r = subprocess.run([sys.executable, s, ruta], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        return r.stdout, open(ruta, encoding='utf-8').read()

    out1, c1 = fusion()
    assert c1.startswith('# BricoHams SDR'), 'falta la cabecera que marca el fichero como generado'
    if yaml:
        cfg = yaml.safe_load(c1)
        jobs = [j['job_name'] for j in cfg['scrape_configs']]
        assert jobs == ['prometheus', 'node', 'openwebrx'], jobs
        assert cfg['scrape_configs'][0]['static_configs'][0]['targets'] == ['127.0.0.1:9090']
        assert '1 trabajo(s) extra' in out1, out1
        out2, c2 = fusion()
        assert c2 == c1, 'la fusión debe ser idempotente'
    else:
        assert "127.0.0.1:9090" in c1 and "127.0.0.1:9100" in c1
finally:
    import shutil
    shutil.rmtree(d)

# --- 2. prioridad de la clave de Grafana (líneas reales del paso) ----------------------------------------
lineas = [ln.strip() for ln in PASO.splitlines()
          if ln.strip().startswith('[ -n "$pass" ]') or 'pass="${GRAFANA_ADMIN_PASS' in ln]
assert len(lineas) == 3, lineas
bloque = lineas[0].replace('local gi=/etc/grafana/grafana.ini ', '') + '\n' + '\n'.join(lineas[1:]) + '\nprintf "%s" "$pass"\n'


def clave(env_pass, guardada):
    with tempfile.TemporaryDirectory() as t:
        if guardada is not None:
            open(os.path.join(t, 'grafana-access.txt'), 'w').write("GRAFANA_USUARIO='admin'\nGRAFANA_PASS='%s'\n" % guardada)
        env = dict(os.environ, ETC_BH=t, GRAFANA_ADMIN_PASS=env_pass)
        r = subprocess.run(['bash', '-c', 'set -eu\n' + bloque], capture_output=True, text=True, env=env)
        assert r.returncode == 0, r.stderr
        return r.stdout


assert clave('admin', 'guardada') == 'admin', 'GRAFANA_ADMIN_PASS debe mandar'
assert clave('', 'guardada') == 'guardada', 'sin GRAFANA_ADMIN_PASS se reutiliza la clave guardada'
a = clave('', None)
assert re.fullmatch(r'[A-Za-z0-9]{16,20}', a) and a != clave('', None), 'sin nada: clave aleatoria de 16-20 caracteres'

# --- 3. grafana.ini -----------------------------------------------------------------------------------------
gi = re.search(r'cat >"\$gi" <<GRAF\n(.*?)\nGRAF\n', PASO, re.S).group(1)
for k in ('[paths]', 'data = /var/lib/grafana', 'http_addr = 127.0.0.1', 'http_port = 3000',
          'root_url = %(protocol)s://%(domain)s/settings/bricohams/grafana/', 'serve_from_sub_path = true',
          'admin_password = $pass', 'allow_sign_up = false', 'reporting_enabled = false'):
    assert k in gi, 'grafana.ini sin «%s»' % k
assert 'chmod 640 "$gi"' in PASO, 'grafana.ini contiene la clave: 640'
assert 'chmod 600 "$ETC_BH/grafana-access.txt"' in PASO
assert '.bak-manual' in PASO, 'las configuraciones manuales previas se guardan una vez'
assert 'reset-admin-password' in INST, 'la clave debe aplicarse también a una base de datos ya existente'

# --- 4. adopción de instalaciones manuales: solo 127.0.0.1 -------------------------------------------------
drop = re.findall(r'\[Service\]\nExecStart=\nExecStart=(\S+)[^\n]*--web\.listen-address=(\S+)', PASO)
assert ('/usr/local/bin/prometheus', '127.0.0.1:9090') in drop, drop
assert ('/usr/local/bin/node_exporter', '127.0.0.1:9100') in drop, drop
assert '--web.listen-address=127.0.0.1:9090' in PASO and '--web.listen-address=127.0.0.1:9100' in PASO
assert not re.search(r'listen-address=(0\.0\.0\.0)?:\d', PASO), 'nada debe escuchar fuera de 127.0.0.1'

# --- 5. nginx: Grafana solo con sesión de administrador -----------------------------------------------------
rutas = open(os.path.join(R, 'files', 'nginx', 'bricohams-sdr-rutas.conf'), encoding='utf-8').read()
gf = '\n'.join(ln[len('#@GF@'):] for ln in rutas.splitlines() if ln.startswith('#@GF@'))
assert 'location /settings/bricohams/grafana/' in gf and 'auth_request /_bh_gf_auth;' in gf
assert gf.index('auth_request') < gf.index('proxy_pass http://127.0.0.1:3000'), 'auth_request antes del proxy'
assert 'internal;' in gf and '127.0.0.1:8076/settings/bricohams/auth' in gf
assert ':3000' not in '\n'.join(ln for ln in rutas.splitlines() if not ln.startswith('#@GF@')), \
    'Grafana no puede quedar publicado sin las líneas #@GF@'
assert "sed -e 's/^#@GF@//'" in INST and "sed -e '/^#@GF@/d'" in INST, 'paso_web debe activar o borrar las líneas #@GF@'

# --- 6. panel ---------------------------------------------------------------------------------------------
panel = json.load(open(os.path.join(R, 'files', 'grafana', 'bricohams.json'), encoding='utf-8'))
assert panel.get('panels'), 'el panel de Grafana no tiene gráficas'
assert 'prometheus' in json.dumps(panel), 'el panel debe usar la fuente de datos «prometheus»'

print('OK test_monitorizacion: prometheus.yml fusionado e idempotente (trabajos ajenos conservados), clave '
      'GRAFANA_ADMIN_PASS > guardada > aleatoria, grafana.ini local con sub-ruta, drop-ins 127.0.0.1 y '
      'Grafana solo tras auth_request')
