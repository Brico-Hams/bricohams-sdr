#!/usr/bin/env python3
"""Unidades systemd que escribe install.sh: sin ciclos de orden.

Una unidad con WantedBy=multi-user.target hace que el target vaya *después* de ella
(dependencias por defecto de los targets). Si además lleva After=multi-user.target hay un
ciclo, y al arrancar systemd lo rompe borrando el trabajo de alguna unidad del ciclo: así
bricohams-wx (After=bricohams-io) no arrancaba nunca y no salía el tiempo a APRS-IS."""
import os
import re

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
S = open(os.path.join(RAIZ, 'install.sh'), encoding='utf-8').read()

unidades = {}
for nombre, _, cuerpo in re.findall(r"cat >/etc/systemd/system/([\w@.-]+\.(?:service|timer|path|socket))\s*<<'?(\w+)'?\n(.*?)\n\2\n", S, re.S):
    claves = {}
    for linea in cuerpo.splitlines():
        m = re.match(r'^(After|Before|WantedBy|RequiredBy)=(.*)$', linea.strip())
        if m:
            claves.setdefault(m.group(1), []).extend(m.group(2).split())
    unidades[nombre] = claves
assert len(unidades) > 20 and 'bricohams-io.service' in unidades and 'bricohams-wx.service' in unidades, sorted(unidades)

# lo que install.sh añade luego con sed (bricohams-wx espera a la Pico)
for unidad, extra in re.findall(r"s/\^After=network-online\.target\$/After=network-online\.target ([\w.@-]+)/' /etc/systemd/system/([\w.@-]+)", S):
    unidades.setdefault(extra, {}).setdefault('After', []).append(unidad)
assert 'bricohams-io.service' in unidades['bricohams-wx.service']['After']

# grafo «X va después de Y»
despues = {}
for u, c in unidades.items():
    for v in c.get('After', []):
        despues.setdefault(u, set()).add(v)
    for v in c.get('Before', []):
        despues.setdefault(v, set()).add(u)
    for t in c.get('WantedBy', []) + c.get('RequiredBy', []):
        if t.endswith('.target'):
            despues.setdefault(t, set()).add(u)

for u, c in sorted(unidades.items()):
    for t in c.get('WantedBy', []):
        assert t not in c.get('After', []), '%s: WantedBy=%s y After=%s es un ciclo' % (u, t, t)


def ciclo(desde):
    pila, vistos = [(desde, [desde])], set()
    while pila:
        n, camino = pila.pop()
        for s in despues.get(n, ()):
            if s == desde:
                return camino + [s]
            if s not in vistos:
                vistos.add(s)
                pila.append((s, camino + [s]))
    return None


for u in sorted(despues):
    c = ciclo(u)
    assert c is None, 'ciclo de orden: ' + ' → '.join(c)
print('OK test_systemd_unidades: %d unidades de install.sh sin ciclos de orden (bricohams-wx arranca tras bricohams-io)' % len(unidades))
