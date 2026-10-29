#!/usr/bin/env python3
"""Discone de banda ancha (MULTIPERFIL) con látigo opcional para bajar en frecuencia.

Modelo de varillas: N varillas de disco (radiales horizontales unidas al vivo)
y N varillas de cono (a 30° del eje, unidas a la malla). Alimentación con un
tramo vertical corto entre el centro del disco y el vértice del cono.

Uso:  python3 discone.py            (barrido de variantes)
      python3 discone.py --final    (diseño elegido, tabla y gráfica)
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import necsim  # noqa: E402

FREQS = [50, 70, 88, 100, 118, 137, 145, 156, 174, 225, 300, 400, 435, 500, 650, 800, 868, 1000, 1090, 1200, 1300]


def construir(L, rdisco, n=8, semiangulo=30.0, hueco=0.02, r_cono0=0.025, latigo=0.0, r=0.002, lam=0.23):
    m = necsim.Modelo('discone L=%.2f D=%.2f latigo=%.2f' % (L, rdisco, latigo))
    z_disco = hueco / 2
    z_cono = -hueco / 2
    feed = m.hilo((0, 0, z_cono), (0, 0, z_disco), r, nseg=1)[0]
    # anillos pequeños: el centro del disco y la boca del cono son buje metálico
    a = math.radians(semiangulo)
    for k in range(n):
        ang = 2 * math.pi * k / n
        c, s = math.cos(ang), math.sin(ang)
        # disco
        m.hilo((0, 0, z_disco), (rdisco * c, rdisco * s, z_disco), r, lambda_min=lam)
        # cono: arranca en un buje de radio r_cono0 unido al vértice
        p0 = (r_cono0 * c, r_cono0 * s, z_cono)
        m.hilo((0, 0, z_cono), p0, r, nseg=1)
        p1 = (p0[0] + L * math.sin(a) * c, p0[1] + L * math.sin(a) * s, z_cono - L * math.cos(a))
        m.hilo(p0, p1, r, lambda_min=lam)
    if latigo > 0:
        m.hilo((0, 0, z_disco), (0, 0, z_disco + latigo), r, lambda_min=lam)
    m.alimentar(feed)
    return m


def barrer(**kw):
    filas = []
    for f in FREQS:
        m = construir(lam=min(0.23, 299.79 / f), **kw)
        res = m.ejecutar(f, f, 1, patron=[(60, 0, 2, 1, 30, 0)])[0]
        g_h = necsim.ganancia(res['patron'], 90, 0)
        g_60 = necsim.ganancia(res['patron'], 60, 0)
        filas.append({'f': f, 'z': [round(res['z'].real, 1), round(res['z'].imag, 1)],
                      'roe50': round(necsim.roe(res['z']), 2), 'g_horiz': g_h, 'g_30elev': g_60})
    return filas


VARIANTES = [
    dict(L=0.70, rdisco=0.24),
    dict(L=0.75, rdisco=0.26),
    dict(L=0.75, rdisco=0.30),
    dict(L=0.80, rdisco=0.28),
    dict(L=0.75, rdisco=0.26, latigo=1.0),
    dict(L=1.0, rdisco=0.35, n=12),
]

FINAL = dict(L=1.0, rdisco=0.35, n=12)   # elegido: ROE ≤ 2.7 de 88 a 1300 MHz (salvo ~1090)

MODELOS = {
    'grande':   dict(L=1.0, rdisco=0.35, n=12),    # MULTIPERFIL: FM, aire, marina, DAB (88–470 MHz)
    'compacta': dict(L=0.75, rdisco=0.26, n=12),   # UHF y SDR futuro: 120–1300 MHz con mejor horizonte en UHF
}

if __name__ == '__main__':
    if '--final' in sys.argv:
        d = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resultados')
        os.makedirs(d, exist_ok=True)
        todo = {k: {'geometria': v, 'barrido': barrer(**v)} for k, v in MODELOS.items()}
        json.dump(todo, open(os.path.join(d, 'discone.json'), 'w'), indent=1)
        for k, v in todo.items():
            print(k, v['geometria'])
            for f in v['barrido']:
                print('  ', f)
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
            for k, col in (('grande', '#1565c0'), ('compacta', '#ef6c00')):
                fl = todo[k]['barrido']; g = todo[k]['geometria']
                lab = '%s: cono %d mm, disco Ø%d mm' % (k, g['L'] * 1000, g['rdisco'] * 2000)
                ax[0].semilogx([x['f'] for x in fl], [min(x['roe50'], 10) for x in fl], 'o-', color=col, label=lab)
                ax[1].semilogx([x['f'] for x in fl], [x['g_horiz'] for x in fl], 'o-', color=col, label=k + ' · horizonte')
            ax[0].axhline(2, ls='--', color='gray'); ax[0].set_ylim(1, 10); ax[0].set_xlabel('MHz'); ax[0].set_ylabel('ROE 50 Ω')
            ax[0].legend(fontsize=8); ax[0].grid(alpha=.3, which='both'); ax[0].set_title('ROE')
            ax[1].set_ylim(-20, 4); ax[1].set_xlabel('MHz'); ax[1].set_ylabel('dBi'); ax[1].legend(fontsize=8)
            ax[1].grid(alpha=.3, which='both'); ax[1].set_title('Ganancia en el horizonte (vertical)')
            fig.suptitle('Discones BricoHams (12 + 12 varillas de Ø4 mm, cono a 30°) · NEC2, espacio libre', fontsize=10)
            fig.tight_layout(); fig.savefig(os.path.join(d, 'discone.png'), dpi=110)
        except ImportError:
            pass
    else:
        for v in VARIANTES:
            fl = barrer(**v)
            print(v, ' '.join('%d:%.1f' % (x['f'], x['roe50']) for x in fl))
