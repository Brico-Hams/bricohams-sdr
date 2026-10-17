"""Las consultas API sin sesion no redirigen ni consumen intentos de password."""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
t = (root / 'files/nginx/bricohams-sdr.conf.tmpl').read_text(encoding='utf-8')
r = (root / 'files/nginx/bricohams-sdr-rutas.conf').read_text(encoding='utf-8')
assert 'map $request_method $bh_login_key {\n    default "";\n    POST $binary_remote_addr;\n}' in t
assert 'limit_req_zone $bh_login_key zone=bh_login_post:10m rate=12r/m;' in t
assert 'limit_req zone=bh_login_post burst=5 nodelay;' in r and 'limit_req_status 429;' in r
for prefijo in ('#@MW@', '#@M43@'):
    lineas = [x[len(prefijo):] for x in t.splitlines() if x.startswith(prefijo)]
    texto = '\n'.join(lineas)
    raiz = re.search(r'    location / \{(.*?)\n    \}', texto, re.S).group(1)
    assert 'error_page 401 = @bh_login;' in raiz and 'auth_request /_bh_auth;' in raiz
    assert texto.count('error_page 401 = @bh_login;') == 1
    for api in re.findall(r'    location ([^ ]*api/) \{(.*?)\n    \}', texto, re.S):
        assert 'auth_request /_bh_auth;' in api[1]
        assert 'error_page' not in api[1]
    assert 'location @bh_login { return 302 https://$host/login?ref=settings; }' in texto
print('OK: POST limitado12/min, GET sin consumo; APIs401, navegacion al login, autenticacion conservada')
