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
com, se, sp, ss = lista('caja_v3.sh', 'COMUNES'), lista('caja_v3.sh', 'SOLO_E'), lista('caja_v3.sh', 'SOLO_P'), lista('caja_v3.sh', 'SOLO_S')
n_c3 = comprobar(os.path.join(C3, 'caja_v3.scad'), os.path.join(C3, 'stl'), com + se, 'electronica_')
n_c3 += comprobar(os.path.join(C3, 'caja_v3.scad'), os.path.join(C3, 'stl'), com + sp, 'potencia_')
n_c3 += comprobar(os.path.join(C3, 'caja_v3.scad'), os.path.join(C3, 'stl'), com + ss, 'sai_')

# 2b. caja v3: holguras de la bandeja de SDR (HackRF One, RTL-SDR V4, Airspy HF+) y de la 3.ª fila de N
SRC = open(os.path.join(C3, 'caja_v3.scad'), encoding='utf-8').read()


def num(nombre):   # valor del módulo de electrónica («EL ? a : b» → a)
    v = re.search(r'\b%s = ([^;]+);' % nombre, SRC).group(1).strip()
    m = re.match(r'EL \? ([\d.]+) :', v)
    return float(m.group(1)) if m else float(eval(v, {}, {}))


def vec(nombre):
    return [float(x) for x in re.search(r'\b%s = \[([^\]]+)\];' % nombre, SRC).group(1).split(',')]


Wc, Hc, Dc, Tc = num('W'), num('H'), num('D'), num('T')
pz = Tc + num('STANDOFF') + num('PL_T')
pl = Tc + 3
d_o, deck = vec('DECK_O'), vec('DECK')
deck_h, deck_t, band_h = num('DECK_H'), num('DECK_T'), num('BAND_H')
band, band_y = vec('BAND'), num('BAND_Y')
sdr = [(n, float(x), float(y), float(l), float(w), float(h)) for n, x, y, l, w, h in re.findall(
    r'\["(\w+)", \[(\d+), (\d+)\], \[(\d+), (\d+), (\d+)\]\]', re.search(r'SDR_DECK = (.+);', SRC).group(1))]
assert [s[0] for s in sdr] == ['HRF', 'V4', 'AHF'], sdr
postes = [(pl + float(a), pl + float(b)) for a, b in re.findall(r'PL\[0\] \+ (\d+), PL\[1\] \+ (\d+)', re.search(r'DECK_FRONT = (.+);', SRC).group(1))]
assert len(postes) == 2 and all(int(p[0] - pl) % 20 == 0 and int(p[1] - pl) % 20 == 0 for p in postes), postes   # en nudos
postes += [(pl + 20 + x, pl + band_y + y) for x in (6, band[0] - 6) for y in (6, band[1] - 6)]
for n, x, y, l, w, h in sdr:
    assert 4 <= x and 4 <= y and x + l <= deck[0] - 4 and y + w <= deck[1] - 4, ('SDR fuera de la bandeja', n)
    for px, py in postes:   # ni el resalte (Ø12) ni los carriles (2 mm) pisan un poste
        qx, qy = px - d_o[0], py - d_o[1]
        assert not (x - 8 < qx < x + l + 8 and y - 8 < qy < y + w + 8), ('poste bajo el SDR', n, px, py)
for i, a in enumerate(sdr):   # ≥ 12 mm entre SDR para los conectores y los carriles
    for b in sdr[i + 1:]:
        sep = max(b[1] - (a[1] + a[3]), a[1] - (b[1] + b[3]), b[2] - (a[2] + a[4]), a[2] - (b[2] + b[4]))
        assert sep >= 12, ('SDR demasiado juntos', a[0], b[0], sep)
fan_out = vec('FAN_OUT')
assert d_o[0] > Tc + 25 + 1, 'la bandeja de SDR choca con el ventilador de entrada'
assert d_o[0] + deck[0] < Wc - Tc - 25 or d_o[1] + deck[1] < fan_out[0] - 30, 'choca con el ventilador de salida'
assert d_o[1] >= 50, 'la bandeja de SDR invade la zona de latiguillos de los N (y < 50)'
assert deck_h > 3 + 32 + 2, 'la bandeja de SDR toca el SDRplay de la bahía de expansión'
assert deck_h + deck_t + max(s[5] for s in sdr) + 4 <= band_h, 'los SDR tocan la bandeja de la Pi'
assert pz + band_h + 41 <= Dc + num('GAP_LID') - num('RIB_H'), 'la Pi + HAT toca la tapa'

# segunda bandeja de SDR: Hermes-Lite 2 y plazas futuras; sin pisar postes ni solaparse; alturas encadenadas
deck2_h = num('DECK2_H')
sdr2 = [(n, float(x), float(y), float(l), float(w), float(h)) for n, x, y, l, w, h in re.findall(
    r'\["(\w+)", \[(\d+), (\d+)\], \[(\d+), (\d+), (\d+)\]\]', re.search(r'SDR_DECK2 = (.+?);', SRC, re.S).group(1))]
assert sdr2[0][0] == 'HL2' and len(sdr2) >= 6, sdr2
assert deck_h + deck_t + max(s[5] for s in sdr) + 4 <= deck2_h, 'la bandeja 1 toca la 2'
assert deck2_h + deck_t + max(s[5] for s in sdr2) + 4 <= band_h, 'la bandeja 2 toca la de la Pi'
for n, x, y, l, w, h in sdr2:
    assert 4 <= x and 4 <= y and x + l <= deck[0] - 4 and y + w <= deck[1] - 4, ('SDR2 fuera de la bandeja', n)
    for px, py in postes:
        qx, qy = px - d_o[0], py - d_o[1]
        assert not (x - 2 < qx + 6 and qx - 6 < x + l + 2 and y - 2 < qy + 6 and qy - 6 < y + w + 2), ('poste bajo el SDR2', n)
for i, a in enumerate(sdr2):
    for b in sdr2[i + 1:]:
        sep = max(b[1] - (a[1] + a[3]), a[1] - (b[1] + b[3]), b[2] - (a[2] + a[4]), a[2] - (b[2] + b[4]))
        assert sep >= 2, ('SDR2 demasiado juntos', a[0], b[0], sep)
assert 'RAK_O' in SRC and 'soporte_rak' in se and 'bandeja_sdr2' in se and 'poste_medio' in se

# presupuesto de potencia con los SDR futuros (HackRF Pro, Airspy HF+, RSPdx, Hermes-Lite 2)
import presupuesto_potencia as pp  # noqa: E402
_r = pp.calcular()
assert _r['carga'] <= pp.MARGEN_MAX, ('el cargador va justo', _r['carga'])
assert _r['a5_reductor'] <= pp.REDUCTOR_5V_A * pp.MARGEN_5V, ('un reductor de 5 V va justo', _r['a5_reductor'])
assert all(_r['A'][c] <= pp.FUSIBLES[c] * 0.8 for c in pp.FUSIBLES), _r['A']
filas = [(int(z), [e.strip(' "') for e in s.split(',')]) for z, s in re.findall(r'\[(\d+), \[([^\]]*)\]\]', re.search(r'N_ROWS = (.+);', SRC).group(1))]
assert len(filas) == 3 and sum(len(f[1]) for f in filas) == 18 and filas[2][1][:3] == ['HRF', 'AHF', 'V4'], filas
assert all(b[0] - a[0] >= 27 for a, b in zip(filas, filas[1:])), filas
assert all((len(f[1]) - 1) * num('N_PITCH') + num('N_HOLE') + 12 <= Wc - 2 * num('R') for f in filas)
assert filas[-1][0] + 13 + 2 < num('GL_Z') - 25.4 / 2 and num('GL_Z') + 25.4 / 2 + 8 <= Dc, 'prensaestopas'
assert Dc <= 250 - 10

# 2c. módulo SAI: todo cabe en la rejilla sin solaparse y las cuentas del manual 17 §1.2 cuadran
import sai_calculo  # noqa: E402
assert re.search(r'W = EL \? 228 : SAI \? 228 : 170;', SRC) and re.search(r'D = EL \? 190 : SAI \? 140 : 112;', SRC)
pl_w, pl_h = Wc - 2 * Tc - 6, Hc - 2 * Tc - 6
lay = [(n, float(x), float(y), float(a), float(b), float(c)) for n, x, y, a, b, c in re.findall(
    r'\["(\w+)", \[(\d+), (\d+)\], \[(\d+), (\d+), (\d+)\]\]', re.search(r'SAI_LAYOUT = (.+?);', SRC, re.S).group(1))]
assert [s[0] for s in lay] == ['BAT', 'PCB', 'TRAFO', 'EMI_OUT', 'EMI_IN', 'DC'], lay
for n, x, y, a, b, c in lay:
    assert x >= 2 and y >= 2 and x + a <= pl_w - 2 and y + b <= pl_h - 2, ('fuera de la rejilla', n)
    assert pz + c <= Dc + num('GAP_LID') - num('RIB_H'), ('toca la tapa', n)
for i, a in enumerate(lay):
    for b in lay[i + 1:]:
        sep = max(b[1] - (a[1] + a[3]), a[1] - (b[1] + b[3]), b[2] - (a[2] + a[4]), a[2] - (b[2] + b[4]))
        assert sep >= 4, ('se solapan', a[0], b[0], sep)
bat = vec('SAI_BAT')
assert bat[0] + 8 <= lay[0][3] and bat[1] + 4 <= lay[0][4], 'la batería de 151 × 100 no cabe en la cuna'
assert 'PG9", 15.5, "RED"' in SRC and 'PG9", 15.5, "SALIDA"' in SRC, 'prensaestopas del SAI'
r = sai_calculo.informe(25, 7, 0.8)
assert r['B_h'] > r['A_h'] * 1.5, 'la opción de 12 V debe dar bastante más autonomía que el inversor'
assert 0.9 < r['A_h'] < 1.4 and 1.6 < r['B_h'] < 2.2, r
assert r['fus_bat_B'] == 7.5 and r['fus_bus'] == 5 and 1000 < r['fc_lc'] < 1150
assert abs(sai_calculo.caida_v(2.3, 1, 1.5) - 0.054) < 0.002 and sai_calculo.seccion(15) == 1.5
assert abs(sai_calculo.flotacion_v(40) - 13.38) < 0.01

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
