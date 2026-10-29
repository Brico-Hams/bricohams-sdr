#!/usr/bin/env python3
"""Planos acotados de las antenas a partir de los resultados NEC2
(hardware/antenas/sim/resultados/*.json) → docs/esquemas/08–10 (PNG)."""
import json
import math
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
RES = os.path.join(RAIZ, 'hardware', 'antenas', 'sim', 'resultados')
OUT = os.path.join(RAIZ, 'docs', 'esquemas')
AZ, VE, NA, GR, RO = '#1565c0', '#2e7d32', '#ef6c00', '#455a64', '#c62828'


def cota(ax, p1, p2, txt, off=0.0, color=GR, fs=8.5, rot=None):
    ax.annotate('', xy=p1, xytext=p2, arrowprops=dict(arrowstyle='<->', color=color, lw=0.9))
    mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
    ax.text(mx + off, my + off, txt, color=color, fontsize=fs, ha='center', va='center', rotation=rot,
            bbox=dict(fc='white', ec='none', pad=1))


def titulo(fig, t, s):
    fig.text(0.02, 0.97, t, fontsize=14, weight='bold', va='top')
    fig.text(0.02, 0.935, s, fontsize=9.5, va='top', color=GR)


def quad():
    d = json.load(open(os.path.join(RES, 'quad_2m70.json')))
    el = {e['elemento']: e for e in d['medidas']}
    fig = plt.figure(figsize=(14, 10.5))
    titulo(fig, 'Quad doble 2 m / 70 cm · RADIOAFICIONADOS (polarización vertical)',
           'Medidas entre ejes de hilo (Ø2 mm) en mm. Simulada con NEC2: 2 m 8,5 dBi F/B 33 dB · 70 cm 9,8 dBi F/B 36 dB. Fuente: hardware/antenas/sim')
    # vista lateral
    ax = fig.add_axes([0.03, 0.08, 0.55, 0.8]); ax.set_aspect('equal'); ax.axis('off')
    ax.add_patch(Rectangle((-520, -10), 1080, 20, color='#b0bec5'))
    ax.text(-260, -40, 'boom aluminio 20×20 (500 mm de cola hasta el mástil)', fontsize=8, ha='center', color=GR)
    ax.add_patch(Rectangle((-540, -700), 20, 1150, color='#78909c')); ax.text(-560, 430, 'mástil', rotation=90, fontsize=8, color=GR, ha='right')
    for n, c in (('2 m reflector', AZ), ('70 cm reflector', NA), ('2 m excitado', AZ), ('70 cm excitado', NA), ('70 cm director', NA)):
        e = el[n]; x = e['x_mm']; a = e['cruceta_mm']
        off = 6 if '70 cm excitado' in n else 0
        ax.plot([x + off, x + off], [-a, a], color=c, lw=3 if '2 m' in n else 2.2)
        ax.text(x + off, a + 30 + (40 if '70' in n else 0), n.rsplit(' ', 1)[0] + '\n' + n.rsplit(' ', 1)[1], fontsize=8, ha='center', color=c)
    xs = sorted({el[n]['x_mm'] for n in el})
    for i in range(len(xs) - 1):
        cota(ax, (xs[i], -470 - 30 * i), (xs[i + 1], -470 - 30 * i), '%d' % (xs[i + 1] - xs[i]))
    cota(ax, (0, -620), (xs[-1], -620), 'boom útil %d mm' % xs[-1])
    ax.set_xlim(-620, 700); ax.set_ylim(-680, 560)
    ax.text(el['2 m excitado']['x_mm'] + 20, 0 + 120, 'alimentación 2 m:\nvértice lateral (+Y)\nλ/4 de RG-59 (75 Ω) %d mm' % d['adaptacion_2m']['lambda4_rg59_mm'], fontsize=7.5, color=RO)
    # vista frontal (rombos)
    ax2 = fig.add_axes([0.6, 0.3, 0.38, 0.6]); ax2.set_aspect('equal'); ax2.axis('off')
    for n, c, lw in (('2 m reflector', '#90caf9', 1.5), ('2 m excitado', AZ, 2.5), ('70 cm excitado', NA, 2.5)):
        a = el[n]['cruceta_mm']
        ax2.plot([0, a, 0, -a, 0], [a, 0, -a, 0, a], color=c, lw=lw)
    a2 = el['2 m reflector']['cruceta_mm']
    ax2.plot([-a2, a2], [0, 0], color='#9e9e9e', lw=1, ls='--'); ax2.plot([0, 0], [-a2, a2], color='#9e9e9e', lw=1, ls='--')
    for n, c in (('2 m excitado', RO), ('70 cm excitado', RO)):
        a = el[n]['cruceta_mm']; ax2.plot([a], [0], 'o', color=c, ms=7)
    ax2.text(el['2 m excitado']['cruceta_mm'] + 15, 25, 'alim. 2 m', color=RO, fontsize=8)
    ax2.text(el['70 cm excitado']['cruceta_mm'] + 10, 25, 'alim. 70 cm', color=RO, fontsize=8)
    ax2.text(0, -a2 - 70, 'Vista desde delante: rombos, crucetas en «+» (fibra Ø8 / Ø6).\nAlimentación en el vértice lateral → polarización VERTICAL (repetidores FM).\n* Cruceta: distancia del centro del boom al vértice (marca para el clip o la puntera).',
             fontsize=8.5, ha='center')
    filas = [('Elemento', 'Posición', 'Lado', 'Perímetro (corte)', 'Cruceta*')]
    for e in d['medidas']:
        filas.append((e['elemento'], '%d' % e['x_mm'], '%d' % e['lado_mm'], '%d (+20 para unir)' % e['perimetro_mm'], '%d' % e['cruceta_mm']))
    t = ax2.table(cellText=filas[1:], colLabels=filas[0], loc='bottom', bbox=[-0.18, -0.5, 1.12, 0.36], cellLoc='center')
    t.auto_set_font_size(False); t.set_fontsize(7.5)
    fig.savefig(os.path.join(OUT, '08_quad_2m70.png'), dpi=110)


def discone():
    d = json.load(open(os.path.join(RES, 'discone.json')))
    fig, axs = plt.subplots(1, 2, figsize=(14, 8))
    titulo(fig, 'Discones BricoHams: 12 varillas de disco + 12 de cono (aluminio Ø4, rosca M4)',
           'Cono a 30° del eje. Hueco disco–cono 20 mm (aislador impreso). Bujes de aluminio Ø70 × 12 mm. Medidas en mm.')
    for ax, k in zip(axs, ('grande', 'compacta')):
        g = d[k]['geometria']; L = g['L'] * 1000; rd = g['rdisco'] * 1000
        ax.set_aspect('equal'); ax.axis('off')
        a = math.radians(30)
        ax.plot([-rd, rd], [10, 10], color=AZ, lw=3)
        for s in (-1, 1):
            ax.plot([s * 25, s * (25 + L * math.sin(a))], [-10, -10 - L * math.cos(a)], color=VE, lw=2.5)
        ax.add_patch(Rectangle((-25, -10), 50, 20, color='#b0bec5'))
        ax.add_patch(Rectangle((-20, -10 - L * math.cos(a) - 250), 40, L * math.cos(a) + 240, color='#78909c', alpha=0.5))
        cota(ax, (-rd, 60), (rd, 60), 'disco Ø%d (varillas de %d desde el buje Ø70 → %d de varilla)' % (2 * rd, rd, rd - 35), fs=8)
        cota(ax, (40, -25), (40 + L * math.sin(a), -25 - L * math.cos(a)), 'cono %d' % L, off=25)
        cota(ax, (-(25 + L * math.sin(a)), -L * math.cos(a) - 60), (25 + L * math.sin(a), -L * math.cos(a) - 60), 'boca del cono Ø%d' % (2 * (25 + L * math.sin(a))))
        ax.text(-30, -30, '30°', fontsize=9, color=VE)
        fl = d[k]['barrido']
        buenos = [x['f'] for x in fl if x['roe50'] <= 2.8]
        ax.set_title('Discone %s · ROE ≤ 2,8 de %d a %d MHz\n%s' % (k, min(buenos), max(buenos),
                     'MULTIPERFIL: FM, aire, marina, DAB, 2 m' if k == 'grande' else 'UHF / SDR futuro: mejor horizonte en 400–1300 MHz'), fontsize=10)
        ax.set_xlim(-650, 650); ax.set_ylim(-1250, 200)
    fig.savefig(os.path.join(OUT, '09_discones.png'), dpi=110)


def adsb():
    d = json.load(open(os.path.join(RES, 'gp1090.json')))
    fig, ax = plt.subplots(figsize=(10, 7.5)); ax.set_aspect('equal'); ax.axis('off')
    titulo(fig, 'ADS-B 1090 MHz: plano de tierra λ/4 con LNA en la base',
           'Radiante %d mm y 4 radiales de %d mm a 45° (latón Ø2). ROE 1,17 a 1090 MHz, 2,2 dBi en el horizonte (NEC2).' % (d['radiante_mm'], d['radiales_mm']))
    ax.add_patch(Rectangle((-25, -60), 50, 60, color='#cfd8dc')); ax.text(0, -30, 'base impresa\n+ LNA 1090\n(20,5 dB, NF 0,4)', ha='center', va='center', fontsize=8)
    ax.plot([0, 0], [0, d['radiante_mm']], color=AZ, lw=4)
    for s in (-1, 1):
        ax.plot([0, s * d['radiales_mm'] * math.cos(math.radians(45))], [0, -d['radiales_mm'] * math.sin(math.radians(45))], color=VE, lw=3)
    cota(ax, (12, 0), (12, d['radiante_mm']), '%d' % d['radiante_mm'], off=8)
    cota(ax, (-6, -6), (-6 - d['radiales_mm'] * 0.707, -6 - d['radiales_mm'] * 0.707), '%d' % d['radiales_mm'], off=-8)
    ax.text(70, 40, 'Cadena:\nradiante → SMA de panel (brida 4 agujeros)\n→ LNA IN · LNA OUT → pigtail SMA–N\n→ coaxial de baja pérdida (LMR-400 / Hyperflex 5)\n→ caja: bias-tee 5 V → FlightStick\n\nRadomo impreso Ø30 (PETG blanco)', fontsize=9, va='top')
    ax.set_xlim(-90, 230); ax.set_ylim(-80, 110)
    fig.savefig(os.path.join(OUT, '10_adsb_gp.png'), dpi=110)


if __name__ == '__main__':
    quad(); discone(); adsb()
    print('planos 08, 09 y 10 generados')
