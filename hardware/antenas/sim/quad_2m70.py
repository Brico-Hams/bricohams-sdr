#!/usr/bin/env python3
"""Quad de doble resonancia 2 m / 70 cm para el receptor RADIOAFICIONADOS.

Polarización VERTICAL (repetidores FM): los cuadros van en rombo y se
alimentan en el vértice lateral. Cada banda tiene su propio punto de
alimentación; un diplexor 2 m/70 cm (el del proyecto) los une en un coaxial.
Cuando se simula una banda, el excitado de la otra queda ABIERTO en su
punto de alimentación, que es lo que ve a través de la rama contraria del
diplexor.

Uso:  python3 quad_2m70.py            (tabla de configuraciones)
      python3 quad_2m70.py --final    (diseño elegido + diagramas)
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import necsim  # noqa: E402

R_HILO = 0.001     # hilo de 2 mm (cobre o aluminio)
DELTA = 0.006      # media longitud del hueco de alimentación


def rombo(m, x, lado, alimentado, abierto, lam):
    """Cuadro en rombo en el plano YZ a la cota x. Devuelve el tag de la fuente."""
    a = lado / math.sqrt(2)
    top, bot, izq = (x, 0, a), (x, 0, -a), (x, -a, 0)
    A, B = (x, a - DELTA, DELTA), (x, a - DELTA, -DELTA)
    m.hilo(top, A, R_HILO, lambda_min=lam)
    tag = None
    if alimentado or not abierto:
        tag = m.hilo(A, B, R_HILO, nseg=1)[0]
    m.hilo(B, bot, R_HILO, lambda_min=lam)
    m.hilo(bot, izq, R_HILO, lambda_min=lam)
    m.hilo(izq, top, R_HILO, lambda_min=lam)
    return tag


def cuadrado(m, x, lado, alimentado, abierto, lam):
    """Cuadro con lados vertical/horizontal, alimentado en el centro del lado vertical +y."""
    h = lado / 2
    p1, p2, p3, p4 = (x, h, h), (x, -h, h), (x, -h, -h), (x, h, -h)
    A, B = (x, h, DELTA), (x, h, -DELTA)
    m.hilo(A, p1, R_HILO, lambda_min=lam)
    m.hilo(p1, p2, R_HILO, lambda_min=lam)
    m.hilo(p2, p3, R_HILO, lambda_min=lam)
    m.hilo(p3, p4, R_HILO, lambda_min=lam)
    m.hilo(p4, B, R_HILO, lambda_min=lam)
    tag = None
    if alimentado or not abierto:
        tag = m.hilo(B, A, R_HILO, nseg=1)[0]
    return tag


def construir(cfg, banda):
    """cfg: dict con la geometría (m). banda: '2m' o '70'."""
    m = necsim.Modelo('quad 2m70 %s %s' % (cfg['nombre'], banda))
    lam = 0.68 if banda == '70' else 2.07
    forma70 = cuadrado if cfg.get('forma70') == 'cuadrado' else rombo
    # 2 m
    rombo(m, 0.0, cfg['r2'], False, False, lam)
    t2 = rombo(m, cfg['x_d2'], cfg['d2'], banda == '2m', banda != '2m', lam)
    for x, lado in cfg.get('dir2', []):
        rombo(m, x, lado, False, False, lam)
    # 70 cm
    forma70(m, cfg['x_r7'], cfg['r7'], False, False, lam)
    t7 = forma70(m, cfg['x_d7'], cfg['d7'], banda == '70', banda != '70', lam)
    for x, lado in cfg.get('dir7', []):
        forma70(m, x, lado, False, False, lam)
    m.alimentar(t2 if banda == '2m' else t7)
    return m


def evaluar(cfg, banda, freqs=None):
    freqs = freqs or ((144.0, 146.0, 5) if banda == '2m' else (430.0, 440.0, 6))
    m = construir(cfg, banda)
    res = m.ejecutar(freqs[0], freqs[1], freqs[2], patron=[(90, 0, 1, 2, 0, 180)])
    out = []
    for r in res:
        gf = necsim.ganancia(r['patron'], 90, 0)
        gb = necsim.ganancia(r['patron'], 90, 180)
        out.append({'f': r['f'], 'z': [round(r['z'].real, 1), round(r['z'].imag, 1)],
                    'roe50': round(necsim.roe(r['z'], 50), 2), 'g': gf, 'fb': round(gf - gb, 1)})
    return out


def P(f):            # perímetro CX1DDR (m)
    return 306.4 / f


def base(nombre, **kw):
    s2, s7 = P(145.0) / 4, P(435.0) / 4
    cfg = {'nombre': nombre, 'r2': s2 * 1.05, 'd2': s2, 'x_d2': 0.2 * 299.79 / 145,
           'r7': s7 * 1.05, 'd7': s7}
    cfg['x_d7'] = cfg['x_d2']
    cfg['x_r7'] = cfg['x_d2'] - 0.2 * 299.79 / 435
    cfg.update(kw)
    return cfg


CONFIGS = [
    base('A rombos coplanares'),
    base('B 70 cm en cuadrado', forma70='cuadrado'),
    base('C 70 cm delante del excitado de 2 m', x_r7=0.414 + 0.03, x_d7=0.414 + 0.03 + 0.138),
    base('D 70 cm con director', dir7=[(0.414 + 0.12, P(435.0) / 4 * 0.95)]),
]


def resumen(cfg):
    fila = {'nombre': cfg['nombre']}
    for b in ('2m', '70'):
        ev = evaluar(cfg, b)
        fila[b] = ev
    return fila


def imprimir(fila):
    print('\n## %s' % fila['nombre'])
    for b in ('2m', '70'):
        print('  %-3s' % b + '  '.join('%5.1f MHz Z=%6.1f%+7.1fj ROE %5.2f G %5.2f dBi F/B %5.1f' %
                                       (e['f'], e['z'][0], e['z'][1], e['roe50'], e['g'], e['fb']) for e in fila[b][:1]))
        for e in fila[b][1:]:
            print('       %5.1f MHz Z=%6.1f%+7.1fj ROE %5.2f G %5.2f dBi F/B %5.1f' %
                  (e['f'], e['z'][0], e['z'][1], e['roe50'], e['g'], e['fb']))


LAM2, LAM7 = 299.79 / 145.0, 299.79 / 436.0
S2, S7 = P(145.0) / 4, P(436.0) / 4


def final(mastil=None):
    """Diseño elegido tras la optimización (opt_quad.py). Medidas en metros."""
    d2 = S2 * 0.99
    d7 = S7 * 1.02
    x_d2 = 0.18 * LAM2
    cfg = {'nombre': 'FINAL', 'r2': d2 * 1.09, 'd2': d2, 'x_d2': x_d2,
           'd7': d7, 'r7': d7 * 1.05, 'x_d7': x_d2, 'x_r7': x_d2 - 0.18 * LAM7,
           'dir7': [(x_d2 + 0.20 * LAM7, d7 * 0.95)]}
    if mastil is not None:
        cfg['mastil'] = mastil
    return cfg


_construir = construir


def construir(cfg, banda):  # noqa: F811  (añade el mástil si se pide)
    m = _construir(cfg, banda)
    if cfg.get('mastil') is not None:
        x = cfg['mastil']
        m.hilo((x, 0, -2.0), (x, 0, 1.0), 0.02, lambda_min=0.68 if banda == '70' else 2.07)
    return m


def medidas(cfg):
    filas = [('2 m reflector', 0.0, cfg['r2']), ('70 cm reflector', cfg['x_r7'], cfg['r7']),
             ('2 m excitado', cfg['x_d2'], cfg['d2']), ('70 cm excitado', cfg['x_d7'], cfg['d7'])]
    filas += [('70 cm director', x, lado) for x, lado in cfg.get('dir7', [])]
    return [{'elemento': n, 'x_mm': round(x * 1000), 'lado_mm': round(lado * 1000),
             'perimetro_mm': round(4 * lado * 1000), 'cruceta_mm': round(lado / math.sqrt(2) * 1000)}
            for n, x, lado in sorted(filas, key=lambda f: f[1])]


def informe():
    cfg = final()
    out = {'medidas': medidas(cfg), 'bandas': {}, 'mastil_0.5m': {}}
    for b, fr in (('2m', (143.0, 147.0, 9)), ('70', (428.0, 442.0, 8))):
        out['bandas'][b] = evaluar(cfg, b, fr)
        out['mastil_0.5m'][b] = evaluar(final(mastil=-0.5), b, (fr[0], fr[1], 3))
    # λ/4 de 75 Ω en 2 m
    z = complex(*[e for e in out['bandas']['2m'] if e['f'] == 145.0][0]['z'])
    zt = 75.0 ** 2 / z
    out['adaptacion_2m'] = {'z_antena': [round(z.real, 1), round(z.imag, 1)], 'z_tras_lambda4_75': [round(zt.real, 1), round(zt.imag, 1)],
                            'roe50': round(necsim.roe(zt), 2), 'lambda4_rg59_mm': round(299.79 / 145.0 / 4 * 0.66 * 1000)}
    # diagramas
    pats = {}
    for b, f in (('2m', 145.0), ('70', 436.0)):
        m = construir(cfg, b)
        r = m.ejecutar(f, f, 1, patron=[(90, 0, 1, 73, 0, 5), (0, 0, 37, 1, 5, 0), (0, 180, 37, 1, 5, 0)])
        pats[b] = r[0]['patron']
    return out, pats


if __name__ == '__main__' and '--final' in sys.argv:
    res, pats = informe()
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resultados')
    os.makedirs(d, exist_ok=True)
    json.dump(res, open(os.path.join(d, 'quad_2m70.json'), 'w'), indent=1)
    for e in res['medidas']:
        print(e)
    for b in ('2m', '70'):
        for e in res['bandas'][b]:
            print(b, e)
        print('con mástil a 0.5 m:', res['mastil_0.5m'][b])
    print(res['adaptacion_2m'])
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig = plt.figure(figsize=(11, 8))
        for i, b in enumerate(('2m', '70')):
            az = sorted(dict((p[1] % 360, p[2]) for p in pats[b] if p[0] == 90).items())
            az.append((360.0, az[0][1]))
            el = sorted(dict([((90 - p[0]) % 360, p[2]) for p in pats[b] if p[1] == 0] +
                             [((90 + p[0]) % 360, p[2]) for p in pats[b] if p[1] == 180]).items())
            ax = fig.add_subplot(2, 3, 1 + 3 * i, projection='polar')
            ax.plot([math.radians(a) for a, _ in az], [max(g, -30) for _, g in az], color='#1565c0')
            ax.set_rlim(-30, 12); ax.set_title('%s · azimut (horizonte)' % ('2 m 145 MHz' if b == '2m' else '70 cm 436 MHz'), fontsize=9)
            ax2 = fig.add_subplot(2, 3, 2 + 3 * i, projection='polar')
            ax2.plot([math.radians(a) for a, _ in el], [max(g, -30) for _, g in el], color='#2e7d32')
            ax2.set_rlim(-30, 12); ax2.set_title('elevación (plano vertical)', fontsize=9)
            ax3 = fig.add_subplot(2, 3, 3 + 3 * i)
            ev = res['bandas'][b]
            ax3.plot([e['f'] for e in ev], [e['roe50'] for e in ev], 'o-', color='#c62828', label='ROE 50 Ω (directo)')
            if b == '2m':
                ax3.plot([e['f'] for e in ev], [necsim.roe(75.0 ** 2 / complex(*e['z'])) for e in ev], 's-', color='#ef6c00', label='con λ/4 de 75 Ω')
            ax3.set_ylim(1, 3); ax3.grid(alpha=.3); ax3.legend(fontsize=8); ax3.set_xlabel('MHz')
            ax3.set_title('G %.1f dBi · F/B %.0f dB (centro)' % (ev[len(ev) // 2]['g'], ev[len(ev) // 2]['fb']), fontsize=9)
        fig.suptitle('Quad doble 2 m / 70 cm BricoHams · NEC2 (nec2c), espacio libre, polarización vertical', fontsize=11)
        fig.tight_layout()
        fig.savefig(os.path.join(d, 'quad_2m70.png'), dpi=110)
    except ImportError:
        pass
elif __name__ == '__main__':
    if '--final' not in sys.argv:
        for c in CONFIGS:
            imprimir(resumen(c))
