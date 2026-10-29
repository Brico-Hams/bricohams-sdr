#!/usr/bin/env python3
"""Cálculos del módulo SAI (manual 17 §1.2): autonomía con la batería de plomo del SAI,
fusibles, sección de cable, caída de tensión y frecuencia de corte del filtro LC de 12 V.

Uso:  python3 tools/sai_calculo.py [--carga 25] [--ah 7] [--envejecimiento 0.8]

Compara las dos formas de reutilizar el SAI:
  A) SAI completo (230 V): batería → inversor del SAI → filtro EMI → cargador de 120 W → 12 V/5 V.
  B) Solo su batería (12 V): cargador de 13,8 V con función SAI → batería → filtro LC → bus de 12 V.
"""
import argparse
import math

V_NOM = 12.0                 # batería de plomo (6 celdas)
V_CORTE_SAI = 10.5           # el SAI se apaga hacia 1,75 V/celda
RHO_CU = 0.0175              # Ω·mm²/m a 20 °C
FUSIBLES_ATO = [1, 2, 3, 5, 7.5, 10, 15, 20, 25, 30]
CABLES = [(0.75, 6), (1.0, 10), (1.5, 15), (2.5, 20), (4.0, 30)]   # (mm², A admisibles en caja cerrada, conservador)


def potencia_bateria_ac(p_carga, eta_cargador=0.85, eta_inversor=0.75, p_reposo=4.0):
    """W que salen de la batería con el SAI invirtiendo: el inversor de un SAI de 600 VA rinde mal al 10 % de carga."""
    return p_carga / eta_cargador / eta_inversor + p_reposo


def potencia_bateria_dc(p_carga, eta_dcdc=0.92):
    """W de batería alimentando el bus de 12 V directamente (sólo el reductor de 5 V de la Pi pierde algo)."""
    return p_carga / eta_dcdc


def autonomia_h(c20_ah, corriente_a, k=1.15, envejecimiento=0.8, dod=1.0):
    """Ley de Peukert referida a la capacidad C20 de la etiqueta (AGM: k ≈ 1,1–1,2)."""
    if corriente_a <= 0:
        raise ValueError('corriente nula')
    t = 20.0 * (c20_ah / (20.0 * corriente_a)) ** k
    return t * envejecimiento * dod


def fusible(corriente_a, margen=1.5):
    """Primer fusible de cuchilla (ATO) ≥ corriente × margen."""
    objetivo = corriente_a * margen
    for f in FUSIBLES_ATO:
        if f >= objetivo:
            return f
    raise ValueError('más de 30 A: usar fusible MIDI/ANL')


def seccion(fusible_a):
    """Sección mínima que protege el fusible (el cable aguanta más que el fusible)."""
    for s, i in CABLES:
        if i >= fusible_a:
            return s
    raise ValueError('sección > 4 mm²')


def caida_v(corriente_a, largo_m, seccion_mm2):
    """Caída de ida y vuelta en un cable de cobre."""
    return 2 * largo_m * RHO_CU / seccion_mm2 * corriente_a


def fc_lc(l_uh, c_uf):
    """Frecuencia de corte (Hz) del filtro LC (π) del bus de 12 V."""
    return 1.0 / (2 * math.pi * math.sqrt(l_uh * 1e-6 * c_uf * 1e-6))


def flotacion_v(temp_c, v25=13.65, mv_c_celda=-3.0):
    """Tensión de flotación compensada en temperatura (−3 mV/°C/celda, 6 celdas)."""
    return v25 + 6 * mv_c_celda / 1000.0 * (temp_c - 25)


def corriente_carga(c20_ah):
    """Corriente de carga recomendable: 0,1 C … 0,25 C."""
    return 0.1 * c20_ah, 0.25 * c20_ah


def informe(carga_w=25.0, ah=7.0, env=0.8):
    pa, pb = potencia_bateria_ac(carga_w), potencia_bateria_dc(carga_w)
    ia, ib = pa / V_NOM, pb / V_NOM
    r = {
        'A_w_bateria': pa, 'A_a': ia, 'A_h': autonomia_h(ah, ia, envejecimiento=env),
        'B_w_bateria': pb, 'B_a': ib, 'B_h': autonomia_h(ah, ib, envejecimiento=env),
        'B_h_50': autonomia_h(ah, ib, envejecimiento=env, dod=0.5),
        'fus_bat_A': 15, 'fus_bat_B': fusible(ib + corriente_carga(ah)[1]),
        'fus_bus': fusible(ib),
        'fc_lc': fc_lc(10, 2200),
        'caida_1m_15': caida_v(ib, 1.0, 1.5),
        'carga_a': corriente_carga(ah),
        'flot_40': flotacion_v(40),
    }
    r['sec_bat_B'] = seccion(r['fus_bat_B'])
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--carga', type=float, default=25.0, help='consumo de la estación en W (defecto 25)')
    ap.add_argument('--ah', type=float, default=7.0, help='capacidad C20 de la batería del SAI (defecto 7)')
    ap.add_argument('--envejecimiento', type=float, default=0.8, help='capacidad que le queda (1 = nueva)')
    a = ap.parse_args()
    r = informe(a.carga, a.ah, a.envejecimiento)
    print('Estación: %.0f W · batería 12 V %.0f Ah al %.0f %%' % (a.carga, a.ah, a.envejecimiento * 100))
    print('A) SAI completo a 230 V : %.1f W de batería (%.1f A) → %.1f h hasta que corta el SAI'
          % (r['A_w_bateria'], r['A_a'], r['A_h']))
    print('B) batería a 12 V       : %.1f W de batería (%.1f A) → %.1f h (%.1f h al 50 %% de descarga)'
          % (r['B_w_bateria'], r['B_a'], r['B_h'], r['B_h_50']))
    print('Fusible en BAT+ (≤ 10 cm del borne): A %d A · B %s A con %.1f mm²' % (r['fus_bat_A'], r['fus_bat_B'], r['sec_bat_B']))
    print('Fusible del bus de 12 V: %s A · caída en 1 m de 2 × 1,5 mm²: %.2f V' % (r['fus_bus'], r['caida_1m_15']))
    print('Carga: %.1f–%.1f A · flotación 13,65 V a 25 °C, %.2f V a 40 °C' % (r['carga_a'] + (r['flot_40'],)))
    print('Filtro LC 10 µH + 2200 µF: corte en %.0f Hz' % r['fc_lc'])


if __name__ == '__main__':
    main()
