#!/usr/bin/env python3
# =====================================================================
#  tools/datos_personales.py · BricoHams SDR (v5.1, manual 38)
#
#  Comprueba que lo que va al GitHub PÚBLICO no lleva datos personales ni
#  claves de la estación. NUNCA imprime el valor encontrado: solo qué tipo de
#  dato es, el fichero y (con --historial) el commit.
#
#  Busca:
#   1. huellas SHA-256 de tools/datos_personales_huellas.txt (red de casa,
#      usuario del sistema, coordenadas exactas…). Se guardan como huella para
#      que la propia lista no publique lo que quiere esconder;
#   2. si hay un bricohams.env personal (--env, por defecto ./bricohams.env):
#      sus claves (PASS, KEY, TOKEN, PSK, PASSCODE, SSID, URL de canal de
#      Meshtastic y sus PSK en base64/hex), STATION_LAT/LON con 4 decimales y
#      las palabras de DATOS_PERSONALES="usuario,otra".
#
#  Uso:  python3 tools/datos_personales.py                 (árbol de trabajo)
#        python3 tools/datos_personales.py --historial     (todo el historial y los .zip de dentro)
#        python3 tools/datos_personales.py --zip kit.zip   (un zip antes de entregarlo)
#        python3 tools/datos_personales.py --huella TEXTO  (línea para el fichero de huellas)
#  Sale con 0 si está limpio y con 1 si encuentra algo.
# =====================================================================
import argparse
import base64
import hashlib
import io
import os
import re
import subprocess
import sys
import zipfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
HUELLAS = os.environ.get('DATOS_PERSONALES_HUELLAS') or os.path.join(AQUI, 'datos_personales_huellas.txt')
NO_MIRAR = ('hardware/gcode/', 'tests/datos/', '.git/')
BINARIOS = ('.png', '.jpg', '.jpeg', '.gif', '.ico', '.hex', '.uf2', '.bin', '.stl', '.3mf', '.pdf', '.gcode', '.woff', '.woff2')
PUBLICOS = {'SDRPLAY_API_URL'}

# fichas candidatas: IPv4 (y sus 3 primeros octetos), números con 4+ decimales (truncados a 4) y palabras
RX_IP = re.compile(rb'(?<![\d.])(\d{1,3}\.\d{1,3}\.\d{1,3})\.(\d{1,3})(?![\d])')
RX_DEC = re.compile(rb'(?<![\d.])-?(\d{1,3}\.\d{4})\d*')
RX_PAL = re.compile(rb'[A-Za-z0-9_\-]{3,40}')


def huella(texto):
    return hashlib.sha256(texto.strip().lower().encode('utf-8')).hexdigest()


def cargar_huellas(ruta=HUELLAS):
    d = {}
    try:
        for l in open(ruta, encoding='utf-8'):
            l = l.strip()
            if l and not l.startswith('#'):
                h, _, tipo = l.partition(' ')
                d[h.lower()] = tipo.strip() or 'dato personal'
    except OSError:
        pass
    return d


def valores_env(ruta):
    """{valor: tipo} con lo que nunca debe salir de bricohams.env."""
    out = {}
    try:
        txt = open(ruta, encoding='utf-8', errors='replace').read()
    except OSError:
        return out
    for k, v in re.findall(r'^([A-Z][A-Z0-9_]*)=("[^"]*"|\'[^\']*\'|[^\s#]*)', txt, re.M):
        v = v.strip('"\'').strip()
        if not v or k in PUBLICOS:
            continue
        if k in ('STATION_LAT', 'STATION_LON'):
            m = re.match(r'-?(\d{1,3}\.\d{4})', v)
            if m:
                out[m.group(1)] = 'coordenada exacta (%s)' % k
            continue
        if k == 'DATOS_PERSONALES':
            for p in v.split(','):
                if len(p.strip()) >= 3:
                    out[p.strip()] = 'dato personal (DATOS_PERSONALES)'
            continue
        clave = any(x in k for x in ('PASS', 'KEY', 'TOKEN', 'PSK', 'SECRET', 'SSID', 'CHANNEL_URL', 'MQTT_USER'))
        if not clave or len(v) < 5:
            continue
        if 'CHANNEL_URL' in k and '#' in v:
            try:
                b = base64.urlsafe_b64decode(v.split('#', 1)[1] + '==')
                for m in re.finditer(rb'\x12\x20(.{32})', b, re.S):
                    out[base64.b64encode(m.group(1)).decode()] = 'PSK de %s (base64)' % k
                    out[m.group(1).hex()] = 'PSK de %s (hex)' % k
            except (ValueError, TypeError):
                pass
            if 'meshtastic.org/e/#' in v and len(v.split('#', 1)[1]) > 40:
                out[v.split('#', 1)[1]] = k
            continue
        out[v] = k
    return out


class Buscador:
    def __init__(self, huellas, valores):
        self.huellas, self.valores = huellas, {k.encode('utf-8'): t for k, t in valores.items()}

    def mirar(self, data):
        tipos = set()
        for v, t in self.valores.items():
            if v in data:
                tipos.add(t)
        if self.huellas:
            fichas = set()
            for m in RX_IP.finditer(data):
                fichas.add(m.group(1) + b'.' + m.group(2))
                fichas.add(m.group(1))
            fichas.update(m.group(1) for m in RX_DEC.finditer(data))
            fichas.update(RX_PAL.findall(data))
            for f in fichas:
                t = self.huellas.get(hashlib.sha256(f.lower()).hexdigest())
                if t:
                    tipos.add(t)
        return tipos


def recorrer_arbol(raiz):
    for r, ds, fs in os.walk(raiz):
        ds[:] = [d for d in ds if d not in ('.git', '__pycache__', 'node_modules')]
        for f in fs:
            p = os.path.join(r, f)
            rel = os.path.relpath(p, raiz).replace(os.sep, '/')
            if rel.startswith(NO_MIRAR) or rel.endswith(BINARIOS) or rel in ('bricohams.env', 'tools/datos_personales_huellas.txt'):
                continue
            if re.search(r'(^|/)[^/]*\.env$', rel) and not rel.endswith('.env.example'):
                continue          # los env personales están en .gitignore: no se suben
            try:
                yield rel, open(p, 'rb').read()
            except OSError:
                pass


def miembros_zip(nombre, data):
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        return
    for n in z.namelist():
        if not n.endswith('/') and not n.endswith(BINARIOS):
            yield nombre + '!' + n, z.read(n)


def recorrer_historial(raiz):
    git = ['git', '-C', raiz]
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0')
    vistos = set()
    for c in subprocess.run(git + ['rev-list', '--all'], capture_output=True, text=True, env=env).stdout.split():
        arbol = subprocess.run(git + ['ls-tree', '-r', c], capture_output=True, text=True, env=env).stdout
        for l in arbol.splitlines():
            meta, ruta = l.split('\t', 1)
            _, tipo, sha = meta.split()
            if tipo != 'blob' or sha in vistos or ruta.startswith(NO_MIRAR) or ruta.endswith(BINARIOS):
                continue
            vistos.add(sha)
            yield '%s %s' % (c[:7], ruta), subprocess.run(git + ['cat-file', 'blob', sha], capture_output=True, env=env).stdout


def main(argv=None):
    a = argparse.ArgumentParser(description='Datos personales y claves fuera del GitHub público')
    a.add_argument('--historial', action='store_true')
    a.add_argument('--zip')
    a.add_argument('--raiz', default=RAIZ)
    a.add_argument('--env', default=None)
    a.add_argument('--huella')
    o = a.parse_args(argv)
    if o.huella:
        print(huella(o.huella), '<tipo de dato>')
        return 0
    envf = o.env or os.path.join(o.raiz, 'bricohams.env')
    b = Buscador(cargar_huellas(), valores_env(envf))
    if o.zip:
        fuente = miembros_zip(os.path.basename(o.zip), open(o.zip, 'rb').read())
    elif o.historial:
        fuente = recorrer_historial(o.raiz)
    else:
        fuente = recorrer_arbol(o.raiz)
    hall, n = {}, 0
    for nombre, data in fuente:
        n += 1
        partes = [(nombre, data)]
        if nombre.endswith('.zip'):
            partes += list(miembros_zip(nombre, data))
        for nm, d in partes:
            for t in b.mirar(d):
                hall.setdefault(t, []).append(nm)
    print('ficheros mirados: %d · huellas: %d · valores del env: %d%s' % (
        n, len(b.huellas), len(b.valores), '' if os.path.exists(envf) else ' (sin bricohams.env personal)'))
    for t in sorted(hall):
        print('✘ %-40s %3d sitios · %s' % (t, len(hall[t]), '; '.join(sorted(hall[t])[:5])))
    if not hall:
        print('✔ limpio: nada personal ni claves')
    return 1 if hall else 0


if __name__ == '__main__':
    sys.exit(main())
