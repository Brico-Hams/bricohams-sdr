#!/usr/bin/env python3
"""v3: comprueba las piezas de antenas y de la caja v3 (selector en el .scad,
STL presente y ≤ 250 mm), los resultados NEC2 que usan los manuales y el
cálculo de viento del mástil (sin vientos falla, con vientos aguanta)."""
import json
import math
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

# 2d. intemperie (España, sol/UV, 45 °C, lluvia con viento, polvo, condensación): reglas que usa el diseño
par = num


assert Tc >= 3.2 and abs(Tc / 0.4 - round(Tc / 0.4)) < 1e-9 and Tc / 0.4 >= 8, 'pared ASA: ≥ 8 perímetros de 0,4 (≥ 3,2 mm)'
assert par('LID_T') >= 4.0, 'tapa < 4 mm'
gap_lid, gasket_h, gasket_w, groove_w = par('GAP_LID'), par('GASKET_H'), par('GASKET_W'), par('GROOVE_W')
comp = (gasket_h - gap_lid) / gasket_h
assert 0.20 <= comp <= 0.30, ('compresión de la junta fuera de 20–30 %', comp)
assert gasket_w < groove_w, 'la junta debe ser más estrecha que la ranura (se ensancha al comprimirse)'
assert re.search(r'GASKET_COMP = \(GASKET_H - GAP_LID\) / GASKET_H', SRC) and 'assert(GASKET_COMP >= 0.20 && GASKET_COMP <= 0.30' in SRC
skirt_h, drip_out, belt_out = par('SKIRT_H'), par('DRIP_OUT'), par('BELT_OUT')
assert skirt_h - gap_lid >= 8, 'el faldón de la tapa debe solapar ≥ 8 mm la pared por debajo de la junta (alero)'
assert drip_out >= 1.0, 'el faldón debe sobresalir ≥ 1 mm del remate de la caja (goteo)'
assert num('BELT_TOP') >= skirt_h - gap_lid + 1, 'el remate de la caja no debe tocar el faldón'
assert 'linear_extrude(SKIRT_H + E) difference() { offset(LID_OFF) outline(); offset(SKIRT_CL) outline(); }' in SRC, 'la tapa no lleva faldón'
assert Hc + 2 * (belt_out + drip_out) <= 250 and Wc + 2 * (num('EAR_L') + 0.5) <= 250, 'la tapa con faldón y orejas no cabe en 250 mm'
roof_w = Wc + 16
roof_l = Dc + gap_lid + par('LID_T') + par('ROOF_FRONT')
assert roof_w <= 250 and roof_l / 0.9961 <= 250, 'el tejadillo no cabe en 250 mm'
assert par('ROOF_FRONT') >= 25 and num('ROOF_GAP') >= 10 and 'ROOF_SIDE_H' in SRC and 'ROOF_L - 2.5' in SRC, 'tejadillo: vuelo, cámara de aire 10 mm, faldones y canto de goteo'
assert re.search(r'DRAIN_D = 3\.\d', SRC) and 'for (x = [DRAIN_X, W - DRAIN_X], z = [8, D - 12])' in SRC, 'faltan los orificios de drenaje'
assert 3 <= num('DRAIN_D') <= 4, 'drenaje: ≥ 3 mm no se tapa y ≤ 4 mm frena a los insectos'
assert '["PG7", 12.7, "VENT"]' in re.search(r'GLANDS_E = .+', SRC).group(0) and '["PG7", 12.7, "VENT"]' in re.search(r'GLANDS_P = .+', SRC).group(0), 'falta el respiradero'
assert 'RESPIRO' in SRC and 'BREATH_D' in SRC and num('BREATH_MEMB') <= 12.7 - 4, 'respiradero: tapón con orificio y membrana que cabe'
assert 'ceja_techo(34, 78)' in SRC and 'ceja_techo(30, 90)' in SRC and 'ceja_techo(30, 80)' in SRC and num('RAIN_CURB_H') >= 3, 'rejillas superiores sin ceja antilluvia'
assert 'capota' in SRC and 'boca hacia abajo' in SRC, 'capotas con la boca hacia abajo'
assert 'cube([3.5, T + 2' in SRC and 'cube([3.2, 80, T + 4])' in SRC, 'rejillas con lamas ≤ 3,5 mm'
for t in ('tapon_n', 'tapon_pg'):   # la cabeza del tapón debe cubrir la punta de la gota (radio 0,707·d)
    assert re.search(r'module %s\(.*?\* 1\.42 \+ 2' % t, SRC, re.S), 'la cabeza de %s no cubre la punta de la gota' % t
assert 'N_HOLE * 1.42 + 2' in SRC and (num('N_HOLE') * 1.42 + 2) / 2 > num('N_HOLE') * 0.7072 + 1, 'tapón N'
assert (num('N_HOLE') * 1.42 + 2) <= num('N_PITCH'), 'las cabezas de tapón_n no deben solaparse'
assert 12.7 * 1.42 + 2 <= 12.7 + 8, 'las cabezas de tapon_pg no deben solaparse con el prensaestopas vecino'
assert 'rotate([-90, 0, 0]) cylinder(d = DRAIN_D' in SRC
assert 'assert(GASKET_COMP' in SRC and 'assert(SKIRT_H - GAP_LID >= 8' in SRC, 'faltan los assert de intemperie en el .scad'
# soportes de pared: los nervios de la espalda son verticales (el agua baja entre la caja y la pared)
assert 'for (x = [W * 0.25, W * 0.75]) translate([x - 3, R, -6]) cube([6, H - 2 * R, 6 + E]);' in SRC

# 2c. módulo SAI: todo cabe en la rejilla sin solaparse y las cuentas del manual 17 §1.2 cuadran
import sai_calculo  # noqa: E402
assert re.search(r'W = EL \? 228 : SAI \? 228 : 170;', SRC) and re.search(r'D = EL \? 192 : SAI \? 140 : 112;', SRC)
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

# 2e. guardas de regresión: insertos M3 de los pilares de la rejilla, selectores de caja_v3.sh, tejadillo y cejas
CUERPO = re.search(r'module cuerpo\(\) \{.*?\n\}\n', SRC, re.S).group(0)
assert 'for (b = PL_BOSS) col(PL[0] + b[0], PL[1] + b[1], 10, T - E, T + STANDOFF);' in CUERPO, 'faltan los pilares de la rejilla (PL_BOSS)'
assert ('for (b = PL_BOSS) translate([PL[0] + b[0], PL[1] + b[1], T + STANDOFF - INS_M3_L]) '
        'cylinder(d = INS_M3, h = INS_M3_L + 1);') in CUERPO, 'faltan los agujeros de los insertos M3 de los pilares de la placa_rejilla'
assert num('INS_M3') >= 4.0 and num('INS_M3_L') >= 6 and len(re.search(r'PL_BOSS = (.+);', SRC).group(1).split('], [')) == 5, 'PL_BOSS: 4 esquinas + centro'
for _p in com + se + sp + ss:   # cada pieza de caja_v3.sh tiene selector (sin depender de los STL)
    assert re.search(r'PART == "%s"\) \w+\(' % re.escape(_p), SRC), 'pieza de caja_v3.sh sin selector: ' + _p
assert re.search(r'module ceja_techo\(z0, z1\)', SRC), 'ceja_techo se llama pero no está definido: no se genera la ceja'
assert 'ROOF_SKIRT_Z' in SRC and 1 <= num('ROOF_SKIRT_Z') <= 3, 'los faldones laterales del tejadillo deben bajar hasta ≤ 3 mm del techo de la caja'
assert 'polygon([[0, ROOF_SKIRT_Z], [ROOF_L, ROOF_SKIRT_Z]' in SRC, 'faldón lateral del tejadillo'
assert (Hc + num('LID_T') + 0) <= 250 and 3 <= num('RAIN_CURB_H') <= 6

# 2f. hub USB Amazon Basics de 10 puertos (electrónica): medidas, hueco libre y sin choques
hub, hub_o, hub_end = vec('HUB'), vec('HUB_O'), num('HUB_END')
assert hub == [145, 44, 23] and 'PENDIENTE de medir' in re.search(r'\bHUB = .*', SRC).group(0), 'HUB sin marcar como pendiente de medir'
assert 'soporte_dongle(36, 124)' not in SRC and 'HUB[0]' in re.search(r'module soporte_hub\(\).*?\n\}\n', SRC, re.S).group(0), 'soporte_hub no usa HUB'
assert 'cube(HUB)' in SRC, 'el fantasma del hub no usa HUB'
assert hub_end >= 15, 'el hub necesita ≥ 15 mm libres en cada extremo'
res = {n: (float(x), float(y), float(l), float(w), float(h)) for n, x, y, l, w, h in re.findall(
    r'\["(\w+)", \[(\d+), (\d+)\], \[(\d+), (\d+), (\d+)\]\]', re.search(r'EL_RES = (.+?);', SRC, re.S).group(1))}
assert set(res) == {'dongles', 'bahia', 'diplexor', 'wago', 'reserva'}, res
assert res['dongles'][1] == num('DONGLE_Y') and res['bahia'][1] == num('DONGLE_Y'), 'EL_RES y DONGLE_Y deben coincidir'
pl_w, pl_h = Wc - 2 * Tc - 6, Hc - 2 * Tc - 6
hz = (hub_o[0] - hub_end, hub_o[1] - 4, hub[0] + 2 * hub_end, hub[1] + 8)   # hub + extremos libres + cuna
assert hz[0] >= 2 and hz[1] >= 2 and hz[0] + hz[2] <= pl_w - 2 and hz[1] + hz[3] <= pl_h - 2, ('el hub se sale de la rejilla', hz)


def _sep(a, b):   # separación entre dos rectángulos (x, y, ancho, alto)
    return max(b[0] - a[0] - a[2], a[0] - b[0] - b[2], b[1] - a[1] - a[3], a[1] - b[1] - b[3])


for n, (x, y, l, w, h) in res.items():
    assert _sep(hz, (x, y, l, w)) >= 1, ('el hub pisa el hueco', n)
for px, py in postes:
    assert _sep(hz, (px - pl - 6, py - pl - 6, 12, 12)) >= 0, ('el hub pisa un poste', px, py)
# FAN_OUT está en la pared derecha y FAN_IN en la izquierda (abajo)
assert _sep(hz, (Wc - Tc - 25 - pl, fan_out[0] - 30 - pl, 25, 60)) >= 1, 'el hub pisa la zona del ventilador de salida'
fan_in = vec('FAN_IN')
assert _sep(hz, (-3, fan_in[0] - 30 - pl, 25, 60)) >= 1
assert pz + res['diplexor'][4] <= fan_out[1] - 30, 'el diplexor toca el ventilador de salida'
assert deck_h >= hub[2] + 3 + 4, 'el hub toca la bandeja de SDR'
assert 'assert(HUB_END >= 15' in SRC and 'el hub USB pisa el hueco' in SRC, 'faltan los assert del hub en el .scad'

# 4. mástil telescópico 3 × 3,00 m con 2 solapes: geometría, solver y datos de diseño
_l, _n = 3.0, 30
_ei = mastil.E_ACERO * mastil.inercia(50, 2.0)
_w0 = 100.0
_zs = [_l * i / _n for i in range(_n + 1)]
_u = mastil.viga(_zs, [_ei] * _n, [_w0] * _n, [0.0] * (_n + 1), [0.0] * (_n + 1), {0: 1e12}, {0: 1e12})[0]
assert abs(_u[-1] - _w0 * _l ** 4 / (8 * _ei)) < 0.01 * _w0 * _l ** 4 / (8 * _ei), 'el solver de viga no reproduce la ménsula'
assert abs(mastil.altura() - 8.2) < 1e-9 and abs(mastil.altura(0.35) - 8.3) < 1e-9 and abs(mastil.altura(0.45) - 8.1) < 1e-9
assert len(mastil.TRAMOS) == 3 and all(abs(t[2] - 3.0) < 1e-9 for t in mastil.TRAMOS)
assert abs(mastil.SOLAPE_NOM - 0.40) < 1e-9 and (min(mastil.SOLAPES), max(mastil.SOLAPES)) == (0.35, 0.45)
assert mastil.VB0 == 26 and abs(mastil.QB - 422.5) < 0.1
nombres = [a[0] for a in mastil.ANTENAS]
assert 'X50 Diamond (2 m/70 cm)' in nombres and 'Discono Moonraker SkyScan' in nombres
zx = dict((a[0], a[1]) for a in mastil.ANTENAS)
assert zx['X50 Diamond (2 m/70 cm)'] > zx['Discono Moonraker SkyScan'] > zx['Discone grande (MULTIPERFIL)'], 'el X50 va arriba y el discono debajo'
assert mastil.q(8.85) > mastil.q(2.0) > 0 and mastil.v_equiv_kmh(8.85) > mastil.V_RACHA_OBS_KMH
s_sin = mastil.analizar(mastil.SOLAPE_NOM, False, 'articulada')
assert s_sin['sigma_cr'] > mastil.FY, ('sin vientos el mástil debería superar el límite', s_sin['sigma_cr'])
peor, _rs = mastil.envolvente(True)
assert all(math.isfinite(v) for v in (peor['sigma_base'], peor['sigma_cr'], peor['flecha_top_mm'], peor['guy_T_N'])), peor
assert isinstance(peor['vale'], bool) and peor['H_min'] == mastil.altura(0.45) and peor['H_max'] == mastil.altura(0.35)

# 5. cámara Raspberry Pi Camera Module 3 Wide en el .scad (sin restos de la WPI408)
assert 'WPI408' not in SRC, 'la WPI408 ya no debe aparecer en caja_v3.scad'
for nombre in ('CAM_PCB', 'CAM_HOLES', 'CAM_WIN', 'CAM_D', 'CAM_FOV_H', 'CAM_FOV_V', 'CAM_VIS_WIN'):
    assert re.search(r'^%s\s*=' % nombre, SRC, re.M), 'falta %s en caja_v3.scad' % nombre
_d = sum(float(re.search(r'^%s\s*=\s*([\d.]+)' % n, SRC, re.M).group(1)) for n in ('CAM_GAP', 'CAM_VID_T'))   # CAM_D = CAM_GAP + CAM_VID_T
_win = [float(x) for x in re.search(r'^CAM_WIN\s*=\s*\[([\d.]+),\s*([\d.]+)\]', SRC, re.M).groups()]
assert _win[0] >= 2 * _d * math.tan(math.radians(102 / 2)) + 8 and _win[1] >= 2 * _d * math.tan(math.radians(67 / 2)) + 8, 'la ventana recorta el campo de 102 × 67°'

print('OK test_v3_hardware: %d piezas de antenas y %d de la caja v3 ≤ 250 mm; NEC2 coherente; '
      'mástil telescópico %.2f m: sin vientos %.0f MPa, con vientos σ máx. %.0f MPa y flecha %.0f mm; ventana de cámara %.0f × %.0f mm' % (
          n_ant, n_c3, mastil.altura(), s_sin['sigma_cr'], peor['sigma_cr'], peor['flecha_top_mm'], _win[0], _win[1]))
