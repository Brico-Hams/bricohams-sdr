#!/usr/bin/env python3
"""Antena ADS-B 1090 MHz: plano de tierra λ/4 con 4 radiales a 45° («araña»).
Uso: python3 gp1090.py [--final]"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import necsim

def construir(rad, radial, caida=45.0, n=4, r=0.001):
    m = necsim.Modelo('GP1090 %.3f %.3f' % (rad, radial))
    t = m.hilo((0, 0, 0), (0, 0, rad), r, nseg=9)[0]
    a = math.radians(caida)
    for k in range(n):
        ang = 2 * math.pi * k / n + math.pi / 4
        m.hilo((0, 0, 0), (radial * math.cos(a) * math.cos(ang), radial * math.cos(a) * math.sin(ang), -radial * math.sin(a)), r, nseg=9)
    m.alimentar(t, 1)
    return m

def barrer(rad, radial, caida=45.0):
    out = []
    for f in (1060, 1075, 1090, 1105, 1120):
        r = construir(rad, radial, caida).ejecutar(f, f, 1, patron=[(80, 0, 3, 1, 5, 0)])[0]
        g = {int(p[0]): p[2] for p in r['patron']}
        out.append({'f': f, 'z': [round(r['z'].real, 1), round(r['z'].imag, 1)], 'roe50': round(necsim.roe(r['z']), 2),
                    'g_horiz': g.get(90), 'g_5elev': g.get(85), 'g_10elev': g.get(80)})
    return out

if __name__ == '__main__':
    if '--final' in sys.argv:
        res = {'radiante_mm': 62, 'radiales_mm': 68, 'caida_grados': 45, 'barrido': barrer(0.062, 0.068)}
        d = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resultados'); os.makedirs(d, exist_ok=True)
        json.dump(res, open(os.path.join(d, 'gp1090.json'), 'w'), indent=1)
        for x in res['barrido']: print(x)
    else:
        for rad in (0.062, 0.064, 0.065, 0.066, 0.068):
            for radial in (0.068, 0.070, 0.072):
                b = barrer(rad, radial)[2]
                print(rad, radial, b)
