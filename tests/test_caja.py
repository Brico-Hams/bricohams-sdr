#!/usr/bin/env python3
"""Comprueba la caja: que están todas las piezas, que caben en la Kobra S1
y que las cotas clave del modelo son coherentes entre sí."""
import os
import re
import sys

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import stl_util  # noqa: E402

CAJA = os.path.join(RAIZ, 'hardware', 'caja')
SCAD = open(os.path.join(CAJA, 'caja_bricohams.scad'), encoding='utf-8').read()


def v(n):
    return float(re.search(r'^%s\s*=\s*([0-9.]+)' % n, SCAD, re.M).group(1))


PIEZAS = re.search(r'PIEZAS=\(([^)]*)\)', open(os.path.join(RAIZ, 'tools', 'caja.sh')).read()).group(1).split()

# 1. cada pieza del script existe en el .scad y en stl/, y cabe en 250 mm
for p in PIEZAS:
    assert 'PART == "%s"' % p in SCAD, 'pieza sin selector: ' + p
    f = os.path.join(CAJA, 'stl', p + '.stl')
    assert os.path.exists(f), 'falta el STL ' + p
    d, n = stl_util.medidas(f)
    assert n > 10 and all(0 < x <= 250 for x in d), (p, d)

# 2. cotas
W, H, D, T, EAR_L = v('W'), v('H'), v('D'), v('T'), v('EAR_L')
assert W + 2 * EAR_L + 1 <= 250 and H + 5 <= 250, 'el cuerpo con orejetas no cabe'
assert v('GASKET_H') - v('GAP_LID') == 1, 'la junta debe comprimirse 1 mm (25 %)'
assert v('GASKET_W') > v('GROOVE_W') > v('T'), 'junta a presión en la ranura y ranura mayor que la pared'
labels = re.search(r'SMA_LABELS = \[([^\]]*)\]', SCAD).group(1).count('"') // 2
xe = v('T') + v('PWR_W') + v('TP')
assert (labels - 1) * v('SMA_PITCH') + v('SMA_HOLE') < W - T - xe - 10, 'los SMA no caben en la zona de electrónica'
assert labels == 9, 'deben ser 9 SMA'
cp_z = D - float(re.search(r'CP_Z = D - ([0-9.]+)', SCAD).group(1))
assert cp_z + v('CP_T') + 4 + 12 < D + v('GAP_LID') - 2, 'los LilyGO tocan la tapa'
cam_x = float(re.search(r'CAM_C = \[([0-9.]+)', SCAD).group(1))
half = 86.5 / 2 + v('CAM_FRAME')
assert xe < cam_x - half and cam_x + half < W - T - 2, 'el marco de la cámara se sale de la zona de electrónica'
print('OK test_caja: %d piezas, todas ≤ 250 mm; junta, SMA, LilyGO y cámara coherentes' % len(PIEZAS))
