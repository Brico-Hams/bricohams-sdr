#!/usr/bin/env python3
"""Plan del mástil BricoHams: posición de cada antena, separaciones entre las
que transmiten y las que reciben, y carga de viento sobre el mástil Televés.

Uso:  python3 tools/mastil.py            (tabla + comprobación)
      python3 tools/mastil.py --png      (además docs/esquemas/11_plan_mastil.png)

Alturas en metros sobre la abrazadera superior del mástil (la que lo sujeta a
la pared o la chimenea). El mástil trabaja como una ménsula desde ese punto.
"""
import math
import os
import sys

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

# nombre, altura z (m), brazo (m, + este / − oeste o norte/sur según rumbo), rumbo, área expuesta (m²), Cd, peso (kg), TX?, banda
ANTENAS = [
    ('Discone grande (MULTIPERFIL)',       2.90, 0.00, 'punta', 0.080, 1.2, 1.1, False, '88–1300 MHz'),
    ('ADS-B λ/4 + LNA',                    1.70, 0.80, 'E',     0.012, 1.2, 0.35, False, '1090 MHz'),
    ('GPS activa',                         1.70, 0.40, 'E',     0.004, 1.2, 0.15, False, '1575 MHz'),
    ('Meshtastic 433 (fibra)',             1.70, 0.80, 'O',     0.030, 1.2, 0.40, True,  '433 MHz'),
    ('Anemómetro RS485',                   1.50, 0.80, 'N',     0.020, 1.2, 0.30, False, '—'),
    ('Veleta RS485',                       1.50, 0.80, 'S',     0.025, 1.2, 0.30, False, '—'),
    ('Quad 2 m/70 cm (RADIOAFICIONADOS)',  0.95, 0.00, 'rumbo', 0.065, 1.2, 1.30, False, '144/430 MHz'),
    ('Bigsignal 868 (Meshtastic HAT)',     0.20, 0.80, 'N',     0.030, 1.2, 0.45, True,  '868 MHz'),
    ('Bigsignal 433 (iGate)',              0.20, 0.80, 'S',     0.030, 1.2, 0.45, False, '433 MHz'),
    ('Garita BME280',                      0.05, 0.45, 'N',     0.020, 1.2, 0.60, False, '—'),
]
BRAZOS = [(1.70, 1.60), (1.50, 1.60), (0.20, 1.60), (0.95, 0.50)]   # (altura, longitud) de brazos Ø25 y extensión del boom
L_MASTIL = 3.0                     # altura libre del mástil sobre la abrazadera superior
MASTILES = [('Televés Ø40 × 2 mm', 40, 2.0), ('Televés Ø45 × 2 mm', 45, 2.0), ('Ø50 × 2,5 mm', 50, 2.5)]
FY = 235.0                         # MPa, acero S235 galvanizado
GAMMA = 1.5                        # coeficiente de seguridad en la carga


def q(v_kmh):
    v = v_kmh / 3.6
    return 0.5 * 1.25 * v * v       # N/m²


def momento(v_kmh, d_mastil_mm):
    m = 0.0
    filas = []
    for n, z, b, rumbo, a, cd, p, tx, banda in ANTENAS:
        f = q(v_kmh) * cd * a
        m += f * z
        filas.append((n, z, f))
    for z, l in BRAZOS:
        f = q(v_kmh) * 1.2 * l * 0.025
        m += f * z
    # el propio mástil (carga repartida)
    f_m = q(v_kmh) * 1.2 * L_MASTIL * d_mastil_mm / 1000
    m += f_m * L_MASTIL / 2
    return m, filas


def cargas(v_kmh, d_mastil_mm):
    """Lista de fuerzas puntuales (z, F) incluyendo brazos y el mástil discretizado."""
    c = [(z, q(v_kmh) * cd * a) for n, z, b, r, a, cd, p, tx, banda in ANTENAS]
    c += [(z, q(v_kmh) * 1.2 * l * 0.025) for z, l in BRAZOS]
    n = 30
    for i in range(n):
        z = (i + 0.5) * L_MASTIL / n
        c.append((z, q(v_kmh) * 1.2 * (L_MASTIL / n) * d_mastil_mm / 1000))
    return c


Z_VIENTOS = 2.0      # altura del collarín de vientos (3 cables a 120°)


def momento_con_vientos(v_kmh, d_mastil_mm):
    """Mástil apoyado en la abrazadera (z=0, empotrado) y en los vientos (z=Z_VIENTOS).
    Estimación conservadora: el mayor entre el voladizo por encima de los vientos y
    el vano entre abrazadera y vientos tratado como biapoyado."""
    c = cargas(v_kmh, d_mastil_mm)
    m_voladizo = sum(f * (z - Z_VIENTOS) for z, f in c if z > Z_VIENTOS)
    m_vano = 0.0
    for zp in [i * Z_VIENTOS / 40 for i in range(1, 40)]:
        m = 0.0
        for z, f in c:
            if z <= Z_VIENTOS:
                m += f * (z * (Z_VIENTOS - zp) / Z_VIENTOS if z <= zp else zp * (Z_VIENTOS - z) / Z_VIENTOS)
        m_vano = max(m_vano, m)
    return max(m_voladizo, m_vano), m_voladizo, m_vano


def modulo(d, t):
    di = d - 2 * t
    return math.pi / 32 * (d ** 4 - di ** 4) / d   # mm³


def separaciones():
    """Distancias entre antenas que transmiten y las que reciben en la misma banda o cerca."""
    pos = {}
    for n, z, b, rumbo, *_ in ANTENAS:
        ang = {'E': 0, 'N': 90, 'O': 180, 'S': 270}.get(rumbo)
        x = b * math.cos(math.radians(ang)) if ang is not None else 0.0
        y = b * math.sin(math.radians(ang)) if ang is not None else 0.0
        pos[n] = (x, y, z)
    pares = [('Meshtastic 433 (fibra)', 'Bigsignal 433 (iGate)', 433), ('Bigsignal 868 (Meshtastic HAT)', 'Bigsignal 433 (iGate)', 868),
             ('Meshtastic 433 (fibra)', 'Quad 2 m/70 cm (RADIOAFICIONADOS)', 433), ('Bigsignal 868 (Meshtastic HAT)', 'Quad 2 m/70 cm (RADIOAFICIONADOS)', 868),
             ('Meshtastic 433 (fibra)', 'ADS-B λ/4 + LNA', 433), ('Meshtastic 433 (fibra)', 'Discone grande (MULTIPERFIL)', 433)]
    out = []
    for a, b, f in pares:
        pa, pb = pos[a], pos[b]
        d = math.dist(pa, pb)
        dz = abs(pa[2] - pb[2])
        lam = 299.79 / f
        out.append((a, b, round(d, 2), round(dz, 2), round(d / lam, 1)))
    return out


def main():
    print('# Plan del mástil y carga de viento\n')
    print('| Antena | Altura (m) | Brazo (m) | Rumbo | Área (m²) | Peso (kg) | Transmite |')
    print('|---|---|---|---|---|---|---|')
    for n, z, b, r, a, cd, p, tx, banda in ANTENAS:
        print('| %s | %.2f | %.2f | %s | %.3f | %.2f | %s |' % (n, z, b, r, a, p, 'sí' if tx else 'no'))
    peso = sum(x[6] for x in ANTENAS)
    print('\nPeso total de antenas: %.1f kg (más brazos y abrazaderas, ≈ %.1f kg)\n' % (peso, peso + 4))
    print('| Mástil | Viento | Momento en la abrazadera | Tensión (×%.1f) | ¿Vale? |' % GAMMA)
    print('|---|---|---|---|---|')
    res = []
    for nombre, d, t in MASTILES:
        for v in (130, 150):
            m, _ = momento(v, d)
            s = GAMMA * m * 1000 / modulo(d, t)
            ok = s <= FY
            res.append((nombre, v, m, s, ok))
            print('| %s | %d km/h | %.0f N·m | %.0f MPa | %s |' % (nombre, v, m, s, 'sí' if ok else '**no**'))
    print('\n**Con vientos a %.1f m** (collarín con 3 cables de acero inox Ø3 a 120°, tensores y anclajes):\n' % Z_VIENTOS)
    print('| Mástil | Viento | Momento máximo | Tensión (×%.1f) | ¿Vale? |' % GAMMA)
    print('|---|---|---|---|---|')
    for nombre, d, t in MASTILES:
        for v in (130, 150):
            m, mv, ms = momento_con_vientos(v, d)
            s = GAMMA * m * 1000 / modulo(d, t)
            res.append((nombre + ' + vientos', v, m, s, s <= FY))
            print('| %s | %d km/h | %.0f N·m | %.0f MPa | %s |' % (nombre, v, m, s, 'sí' if s <= FY else '**no**'))
    print('\n| Transmite | Recibe | Distancia (m) | Separación vertical (m) | En λ |')
    print('|---|---|---|---|---|')
    for a, b, d, dz, nl in separaciones():
        print('| %s | %s | %.2f | %.2f | %.1f |' % (a, b, d, dz, nl))
    return res


def png():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Polygon, Circle
    fig, ax = plt.subplots(figsize=(11, 11))
    ax.set_aspect('equal'); ax.set_xlim(-2.1, 2.6); ax.set_ylim(-2.1, 3.75); ax.axis('off')
    ax.add_patch(Rectangle((-0.02, -1.0), 0.04, 1.0 + L_MASTIL, color='#78909c'))
    ax.add_patch(Rectangle((-0.35, -1.05), 0.7, 0.08, color='#455a64')); ax.add_patch(Rectangle((-0.35, -0.03), 0.7, 0.06, color='#455a64'))
    ax.text(0.4, -0.02, 'abrazadera superior (z = 0)', fontsize=9, va='center', color='#455a64')
    ax.text(0.4, -1.01, 'abrazadera inferior (≥ 0,8 m más abajo)', fontsize=9, va='center', color='#455a64')
    # discone
    zt = 2.90
    for k in range(-6, 7):
        a = math.radians(30) * k / 6
        ax.plot([0, 1.0 * math.sin(a)], [zt, zt - 1.0 * math.cos(math.radians(30)) * math.cos(a) / math.cos(math.radians(30)) * math.cos(math.radians(30))], color='#1565c0', lw=0.6)
    ax.plot([-0.35, 0.35], [zt + 0.03, zt + 0.03], color='#1565c0', lw=3)
    ax.plot([-0.5, 0.5], [zt - 0.866, zt - 0.866], color='#1565c0', lw=0.6, ls=':')
    ax.text(0.6, zt + 0.05, 'Discone grande Ø0,70 / cono 1,0 m\nMULTIPERFIL (V3, vía diplexor)', fontsize=9, color='#1565c0')
    # brazos (vista frontal: E derecha, O izquierda; N/S dibujados a 45° como profundidad)
    for z, l in BRAZOS[:3]:
        ax.plot([-l / 2, l / 2], [z, z], color='#90a4ae', lw=3)
    cols = {True: '#c62828', False: '#2e7d32'}
    for n, z, b, r, a, cd, p, tx, banda in ANTENAS[1:]:
        if 'Quad' in n:
            continue
        x = {'E': b, 'O': -b, 'N': b * 0.7, 'S': -b * 0.7}.get(r, 0)
        h = 0.55 if 'Bigsignal' in n or 'fibra' in n else (0.12 if 'ADS' in n else 0.08)
        ax.add_patch(Rectangle((x - 0.02, z), 0.04, h, color=cols[tx]))
        dy = -0.12 if 'GPS' in n else h + 0.03
        ax.text(x + (0.06 if x >= 0 else -0.06), z + dy, n + ('  [TX]' if tx else '') + '  (%s)' % r, fontsize=8, color=cols[tx], ha='left' if x >= 0 else 'right')
    # quad (vista lateral simplificada)
    zq = 0.95
    ax.plot([0, 1.06], [zq, zq], color='#6a1b9a', lw=3)
    for x, s in ((0.5, 0.570), (0.748, 0.188), (0.872, 0.523), (1.01, 0.170)):
        ax.plot([x, x], [zq - s / math.sqrt(2), zq + s / math.sqrt(2)], color='#6a1b9a', lw=2)
    ax.text(1.12, zq + 0.05, 'Quad 2 m/70 cm\nmontaje trasero: mástil 0,5 m\ndetrás del reflector\napunta al rumbo elegido', fontsize=8.5, color='#6a1b9a')
    ax.annotate('', xy=(-0.9, 0.2), xytext=(-0.9, 1.7), arrowprops=dict(arrowstyle='<->', color='#c62828'))
    ax.text(-1.2, 1.05, '1,5 m\nTX 433 ↔\niGate 433', fontsize=8.5, color='#c62828', ha='right', va='center')
    for sx in (-1, 1):
        ax.plot([0, sx * 1.9], [Z_VIENTOS, -0.95], color='#8d6e63', lw=1, ls='--')
    ax.plot([-0.07, 0.07], [Z_VIENTOS, Z_VIENTOS], color='#8d6e63', lw=5)
    ax.text(-1.95, -0.85, 'vientos: 3 cables inox Ø3 a 120°\ncon tensor, desde el collarín a %.1f m' % Z_VIENTOS, fontsize=8, color='#8d6e63')
    ax.text(-2.05, 3.55, 'Plan del mástil BricoHams (vista frontal; N/S dibujados en perspectiva)', fontsize=13, weight='bold')
    ax.text(-2.05, 3.42, 'Rojo: antenas que transmiten. Verde: solo recepción. Eggbeater (SAT) y lazo MLA-30 (HF) en postes aparte.', fontsize=9.5)
    ax.text(-2.05, -1.25, 'Fuera del mástil:\n• Eggbeater 2 m/70 cm (SATÉLITES): poste propio a ≥ 3 m, cielo despejado.\n'
                         '• Lazo MLA-30 (HF): poste no metálico a ≥ 5 m del mástil y de cables de red, 2–3 m de altura.\n'
                         '• Pluviómetro: soporte nivelado en barandilla o muro, sin salpicaduras ni sombra de lluvia.\n'
                         '• Caja de la estación: al pie, a ~5 m (coaxiales de baja pérdida).', fontsize=9, va='top')
    out = os.path.join(RAIZ, 'docs', 'esquemas', '11_plan_mastil.png')
    fig.savefig(out, dpi=110, bbox_inches='tight')
    print('esquema', out)


if __name__ == '__main__':
    main()
    if '--png' in sys.argv:
        png()
