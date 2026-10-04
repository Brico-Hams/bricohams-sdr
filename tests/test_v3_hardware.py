#!/usr/bin/env python3
"""v3: comprueba las piezas de antenas y de la caja v3 (selector en el .scad,
STL presente y ≤ 250 mm), los resultados NEC2 que usan los manuales y el
cálculo de viento del mástil (sin vientos falla, con vientos aguanta)."""
import json
import os
import re
import sys

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import stl_util  # noqa: E402
import mastil  # noqa: E402


def lista(script, var):
    txt = open(os.path.join(RAIZ, 'tools', script), encoding='utf-8').read()
    return re.search(r'%s=\(([^)]*)\)' % var, txt, re.S).group(1).split()


def comprobar(scad, stl_dir, piezas, prefijo=''):
    src = open(scad, encoding='utf-8').read()
    for p in piezas:
        assert 'PART == "%s"' % p in src, 'pieza sin selector en %s: %s' % (os.path.basename(scad), p)
        f = os.path.join(stl_dir, prefijo + p + '.stl')
        assert os.path.exists(f), 'falta el STL ' + f
        d, n = stl_util.medidas(f)
        assert n > 10 and all(0 < x <= 250 for x in d), (p, d)
    return len(piezas)


# 1. antenas
ANT = os.path.join(RAIZ, 'hardware', 'antenas')
n_ant = comprobar(os.path.join(ANT, 'antenas_bricohams.scad'), os.path.join(ANT, 'stl'), lista('antenas.sh', 'PIEZAS'))

# 2. caja v3 (dos módulos)
C3 = os.path.join(RAIZ, 'hardware', 'caja_v3')
com, se, sp = lista('caja_v3.sh', 'COMUNES'), lista('caja_v3.sh', 'SOLO_E'), lista('caja_v3.sh', 'SOLO_P')
n_c3 = comprobar(os.path.join(C3, 'caja_v3.scad'), os.path.join(C3, 'stl'), com + se, 'electronica_')
n_c3 += comprobar(os.path.join(C3, 'caja_v3.scad'), os.path.join(C3, 'stl'), com + sp, 'potencia_')

# 3. resultados NEC2 que citan los manuales 12–14
R = os.path.join(ANT, 'sim', 'resultados')
q = json.load(open(os.path.join(R, 'quad_2m70.json')))
assert q['adaptacion_2m']['roe50'] < 1.5 and q['adaptacion_2m']['lambda4_rg59_mm'] == 341
b70 = [x for x in q['bandas']['70'] if 432 <= x['f'] <= 440]
assert b70 and max(x['roe50'] for x in b70) < 1.6 and min(x['g'] for x in b70) > 9, b70
b2 = [x for x in q['bandas']['2m'] if 144 <= x['f'] <= 146]
assert min(x['g'] for x in b2) > 8 and max(x['fb'] for x in b2) > 30
g = json.load(open(os.path.join(R, 'gp1090.json')))
p1090 = [x for x in g['barrido'] if x['f'] == 1090][0]
assert p1090['roe50'] < 1.3 and g['radiante_mm'] == 62 and g['radiales_mm'] == 68
dsc = json.load(open(os.path.join(R, 'discone.json')))
assert set(dsc) == {'grande', 'compacta'}

# 4. mástil Ø40 × 2: sin vientos falla a 130 km/h, con vientos aguanta 150 km/h
W = mastil.modulo(40, 2.0)
s_libre = mastil.GAMMA * mastil.momento(130, 40)[0] * 1000 / W
s_vientos = mastil.GAMMA * mastil.momento_con_vientos(150, 40)[0] * 1000 / W
assert s_libre > mastil.FY > s_vientos, (s_libre, s_vientos)

print('OK test_v3_hardware: %d piezas de antenas y %d de la caja v3 ≤ 250 mm; NEC2 coherente; '
      'mástil %.0f MPa sin vientos / %.0f MPa con vientos' % (n_ant, n_c3, s_libre, s_vientos))
