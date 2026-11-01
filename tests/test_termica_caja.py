#!/usr/bin/env python3
"""Estudio térmico de la caja v3 (tools/termica_caja.py): ambiente de diseño 47 °C, coherencia física
del modelo, rejillas del .scad y que los manuales y los valores por defecto del ventilador lo recojan."""
import os
import re
import sys

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import termica_caja as tc  # noqa: E402


def leer(*ruta):
    return open(os.path.join(RAIZ, *ruta), encoding='utf-8').read()


assert tc.T_AMB == 47.0, 'el aire de diseño es 47 °C'
r = tc.resultados()
e, p, s = r['electronica'], r['potencia'], r['sai']

# el calor de la electrónica parte del presupuesto de potencia (46,2 W de equipos + pérdidas de conversión)
import presupuesto_potencia as pp  # noqa: E402
w_equipos = sum(a * (12.0 if c == '12V' else 5.0) for _, c, a, _ in pp.EQUIPOS)
assert e['carga_W'] > w_equipos and e['carga_W'] < 1.4 * w_equipos, (e['carga_W'], w_equipos)
assert r['carga_cargador'] <= pp.MARGEN_MAX, 'el cargador va justo con el hub de 20 V'

# sol: tejadillo < sin tejadillo; oscuro > blanco (≈ 3×, α 0,9/0,3)
for m in (e, p, s):
    so = m['solar']
    assert so['blanco_con_tejadillo'] < so['blanco_sin_tejadillo'], so
    assert abs(so['oscuro_sin_tejadillo'] / so['blanco_sin_tejadillo'] - 3.0) < 1e-6, so
    assert so['entra_blanco_con_tejadillo'] < so['blanco_con_tejadillo'], 'solo una parte del calor absorbido entra al interior'
    assert 0 < m['UA_W_K'] < 3

# caudal necesario: ΔT 5 > 10 > 15 y Q = P/(ρ·cp·ΔT)
q = e['requerido']
assert q[5]['m3h'] > q[10]['m3h'] > q[15]['m3h'] > 0
assert abs(q[5]['m3h'] / q[10]['m3h'] - 2.0) < 1e-9 and abs(q[10]['cfm'] / q[10]['m3h'] - 0.5886) < 1e-3

# ventiladores: más duty, más caudal y menos temperatura; el 100 % mantiene la electrónica ≤ 65 °C a 47 °C
assert 10 < e['disponible_m3h'] < 29.2 * 2
assert e['interior'][30] > e['interior'][60] > e['interior'][100] > tc.T_AMB
assert e['interior']['sin_ventilador'] > 90, 'sin ventilador la electrónica debe salirse de rango'
assert 50 < e['interior_100'] <= 65, e['interior_100']
assert e['veredicto'] in ('ok', 'marginal') and e['interior_100'] <= tc.LIMITE['electronica'] + tc.MARGINAL
assert e['interior_oscuro_100'] > e['interior_sin_tejadillo_100'] > e['interior_100']
sens = r['sensibilidad_derating']
assert sens[0.4] > sens[0.5] > sens[0.6] > 0
assert tc.caudal_ventiladores(1.0) > tc.caudal_ventiladores(1.0, 0.6)
assert abs(tc.caudal_ventiladores(0.5) * 2 - tc.caudal_ventiladores(1.0)) < 1e-9, 'el caudal escala con el duty'

# potencia y SAI sin ventilador: el tiro térmico es pequeño; la batería de plomo se marca (límite 45 °C)
assert 0 < p['disponible_m3h'] < 3 and 0 < s['disponible_m3h'] < 3
assert s['veredicto'] == 'overheat', 'la batería del SAI a 47 °C de ambiente debe quedar marcada'
assert s['interior_100'] > tc.LIMITE['sai']

# opción c (adaptador de 65 W en potencia): la electrónica se enfría y potencia se calienta
rc = tc.resultados('c')
assert rc['electronica']['carga_W'] < e['carga_W'] and rc['potencia']['carga_W'] > 0
assert rc['electronica']['interior_100'] < e['interior_100']

# la salida JSON lleva las claves pedidas
tabla = tc.tabla_json(r)
assert [t['module'] for t in tabla] == ['electronica', 'potencia', 'sai']
assert all({'load_W', 'solar_W', 'required_m3h_dT10', 'available_m3h', 'interior_C_full_fan', 'verdict'} <= set(t) for t in tabla)

# rejillas pasivas del modelo = las del .scad
scad = leer('hardware', 'caja_v3', 'caja_v3.scad')
for cadena in ('for (x = [20 : 9 : W - 20]) translate([x, -1, 82]) cube([3.5, T + 2, 18])',
               'for (x = [30 : 9 : W - 30]) translate([x, H - T - 1, 30]) cube([3.5, T + 2, 50])',
               'for (x = [20 : 9 : W - 20]) translate([x, -1, 90]) cube([3.5, T + 2, 24])',
               'for (x = [30 : 9 : W - 30]) translate([x, H - T - 1, 30]) cube([3.5, T + 2, 60])'):
    assert cadena in scad, cadena
assert tc.VENTS['potencia'][0] == (20, 170 - 20, 9, 3.5, 18) and tc.VENTS['sai'][1] == (30, 228 - 30, 9, 3.5, 60)

# la documentación y los valores por defecto del ventilador usan 47 °C
man = leer('docs', 'manuales', '18_VENTILACION.md')
assert '47 °C' in man and 'termica_caja.py' in man, 'el manual de ventilación debe citar los 47 °C y la herramienta'
assert 'aire de diseño de 40 °C' not in man
env = leer('bricohams.env.example')
inst = leer('install.sh')
vals = {}
for k in ('FAN_T_CAJA_MIN', 'FAN_T_CAJA_MAX', 'FAN_T_CPU_MIN', 'FAN_T_CPU_MAX'):
    a = re.search(r'^%s="(\d+)"' % k, env, re.M).group(1)
    vals[k] = int(a)
    assert ('%s=${%s:-%s}' % (k, k, a)) in inst, ('install.sh no coincide con bricohams.env.example', k)
    assert ("env('%s', '%s')" % (k, a)) in leer('files', 'bin', 'bricohams-fan.py'), ('bricohams-fan.py no coincide', k)
assert '| `FAN_T_CPU_MIN` / `MAX` | %d / %d °C' % (vals['FAN_T_CPU_MIN'], vals['FAN_T_CPU_MAX']) in man, 'tabla de 18_VENTILACION.md sin los valores por defecto'
assert '| `FAN_T_CAJA_MIN` / `MAX` | %d / %d °C' % (vals['FAN_T_CAJA_MIN'], vals['FAN_T_CAJA_MAX']) in man
assert vals['FAN_T_CAJA_MIN'] < vals['FAN_T_CAJA_MAX'] and vals['FAN_T_CPU_MIN'] < vals['FAN_T_CPU_MAX']
assert vals['FAN_T_CAJA_MAX'] <= e['interior_100'], 'a 47 °C el aire de la caja debe estar ya al 100 % del ventilador'
assert vals['FAN_T_CPU_MAX'] <= 75, 'a 75 °C de SoC la Pi 5 debe tener el ventilador al máximo (se limita a 85 °C)'

print('OK test_termica_caja: electrónica %.1f °C al 100 %% (%.1f m³/h), potencia %.1f °C, SAI %.1f °C con 47 °C de ambiente'
      % (e['interior_100'], e['disponible_m3h'], p['interior_100'], s['interior_100']))
