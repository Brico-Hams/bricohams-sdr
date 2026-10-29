#!/usr/bin/env python3
"""v4: anclajes impresos. Cada pieza de tools/anclajes.sh tiene selector en el
.scad y STL ≤ 250 mm; las crucetas aprietan (media caña 1 mm menos que el radio) y
los tornillos de las dos tapas no se cruzan."""
import math
import os
import re
import sys

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import stl_util  # noqa: E402

A = os.path.join(RAIZ, 'hardware', 'anclajes')
SCAD = open(os.path.join(A, 'anclajes_bricohams.scad'), encoding='utf-8').read()
txt = open(os.path.join(RAIZ, 'tools', 'anclajes.sh'), encoding='utf-8').read()
piezas = re.search(r'PIEZAS=\(([^)]*)\)', txt, re.S).group(1).split()
for p in piezas:
    assert 'PART == "%s"' % p in SCAD, p
    d, n = stl_util.medidas(os.path.join(A, 'stl', p + '.stl'))
    assert n > 10 and all(0 < x <= 250 for x in d), (p, d)

v = lambda k: float(re.search(r'^%s\s*=\s*([0-9.]+)' % k, SCAD, re.M).group(1))
assert v('APRIETE') >= 0.5, 'las medias cañas deben apretar'
# tornillos: tapa A en (±(L/2-9), ±(dA/2+6.5)); tapa B girada -90°
for dA, dB in ((v('ARM_D'), v('MAST_D')), (v('BOOM'), v('MAST_D')), (v('FIBRA_D'), v('ARM_D')), (v('ARM_D'), v('ARM_D'))):
    L = max(dA, dB) + 44
    ta = [(-L / 2 + 9, dA / 2 + 6.5), (L / 2 - 9, -(dA / 2 + 6.5))]
    tb = [(y, -x) for x, y in [(-L / 2 + 9, dB / 2 + 6.5), (L / 2 - 9, -(dB / 2 + 6.5))]]
    for a in ta:
        for b in tb:
            assert math.dist(a, b) > 13, ('tornillos demasiado cerca', dA, dB, a, b)
        assert abs(a[1]) - dA / 2 > 3 and abs(a[0]) < L / 2 - 5        # fuera del tubo y dentro del bloque
print('OK test_anclajes: %d piezas ≤ 250 mm, crucetas que aprietan y tornillos sin cruces' % len(piezas))
