#!/usr/bin/env python3
"""Regresiones de HSTS y conservacion de la separacion de datos desplegada."""
import importlib.util
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "hsts", ROOT / "files/bin/bricohams-nginx-hsts.py")
hsts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hsts)

source = """# add_header Ignorado si; {
location / {
    add_header Cache-Control "literal { } #";
    add_header X-Test yes;
    location /child { add_header Otro valor; }
}
location /hereda { return 200; }
"""
result = hsts.proteger(source)
assert result.count(hsts.HEADER) == 2
assert hsts.proteger(result) == result, "HSTS debe ser idempotente"
assert 'location /hereda { return 200; }' in result
assert hsts.proteger('location / { return 200; }') == 'location / { return 200; }'
existing = 'location / { add_header Other yes; add_header Strict-Transport-Security "max-age=1" always; }'
assert hsts.proteger(existing) == existing, "No duplicar ni cambiar una politica existente"
for invalid in ('}', 'location / {'):
    try:
        hsts.proteger(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("Configuracion ambigua aceptada")

installer = (ROOT / "install.sh").read_text(encoding="utf-8")
assert 'rsync -a --no-perms --no-owner --no-group' in installer
for name in ("sensor", "caja"):
    assert f"--exclude 'meteo/{name}.json'" in installer
assert 'readlink "$R/$dato"' in installer
assert '"/var/lib/bricohams/web/$dato"' in installer
assert 'chown root:root "$R/$carpeta"; chmod 755 "$R/$carpeta"' in installer
assert 'if [ ! -f "$ETC_BH/web-data.env" ]; then' in installer
assert 'install -o root -g root -m 644 "$R/$carpeta/$carpeta.js"' in installer
assert re.search(r'if \[ -f /etc/nginx/snippets/bricohams-static-seguro.conf \]; then\s+'
                 r"printf .*include /etc/nginx/snippets/bricohams-static-seguro.conf;", installer)
assert 'python3 "$FILES/bin/bricohams-nginx-hsts.py"' in installer
template = (ROOT / "files/nginx/bricohams-sdr.conf.tmpl").read_text(encoding="utf-8")
assert '#@TODO@    location / { return 301 https://__DOMINIO__$request_uri; }' in template
assert '#@ADMIN@        return 301 https://__DOMINIO__$request_uri;' in template
tak = (ROOT / "tools/instalar_tak.sh").read_text(encoding="utf-8")
assert tak.count('proxy_pass http://127.0.0.1:8081;') == 5
assert tak.count('proxy_cache off;') == 5
assert tak.count('proxy_hide_header Cache-Control;') == 5
assert tak.count('add_header Cache-Control "no-store" always;') == 5
print("OK: HSTS por bloque, idempotencia, fallo cerrado y persistencia de protecciones")
