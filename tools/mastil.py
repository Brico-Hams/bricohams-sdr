#!/usr/bin/env python3
"""Plan del mástil BricoHams: posición de cada antena, separaciones entre las
que transmiten y las que reciben, y cálculo de viento del mástil TELESCÓPICO
(3 tramos × 3,00 m, 2 solapes de 0,35–0,45 m, ≈ 8,20 m montado).

Uso:  python3 tools/mastil.py            (tabla + comprobación)
      python3 tools/mastil.py --png      (además docs/esquemas/11_plan_mastil.png)

Alturas en metros sobre el pie del mástil (z = 0). El mástil se modela como una
viga continua de EI variable (elementos finitos de Euler-Bernoulli), articulada
o empotrada en el pie, con apoyo rígido en el ANCLAJE a la pared y los vientos
como muelles. Todo lo marcado PENDIENTE son valores típicos a sustituir por los
medidos en el mástil comprado.

Viento de diseño: vb,0 = 26 m/s (zona A del CTE DB-SE-AE / EN 1991-1-4, Murcia),
presión básica qb = ½·ρ·vb² y coeficiente de exposición ce(z) del CTE (grado de
aspereza III: vega con obstáculos aislados). Las rachas observadas en la región
(~100 km/h) quedan por debajo: ver V_RACHA_OBS_KMH.
"""
import math
import os
import sys

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

# nombre, altura z (m), brazo (m, + este / − oeste o norte/sur según rumbo), rumbo, área expuesta (m²), Cd, peso (kg), TX?, banda
Z0_ANT = 1.30   # las antenas ya existentes conservan sus alturas relativas (separaciones TX/RX) desplazadas Z0_ANT sobre el pie
ANTENAS = [
    ('X50 Diamond (2 m/70 cm)',            8.85, 0.00, 'punta', 0.055, 1.2, 1.10, True,  '144/430 MHz'),   # 1,70 m, base a 8,00 m; estimado
    ('Discono Moonraker SkyScan',          6.40, 0.50, 'E',     0.070, 1.2, 1.40, False, '25–2000 MHz'),   # 0,95 m + placa; estimado, ver MOONRAKER
    ('Discone grande (MULTIPERFIL)',       Z0_ANT + 2.90, 0.00, 'punta', 0.080, 1.2, 1.1, False, '88–1300 MHz'),
    ('ADS-B λ/4 + LNA',                    Z0_ANT + 1.70, 0.80, 'E',     0.012, 1.2, 0.35, False, '1090 MHz'),
    ('GPS activa',                         Z0_ANT + 1.70, 0.40, 'E',     0.004, 1.2, 0.15, False, '1575 MHz'),
    ('Meshtastic 433 (fibra)',             Z0_ANT + 1.70, 0.80, 'O',     0.030, 1.2, 0.40, True,  '433 MHz'),
    ('Anemómetro RS485',                   Z0_ANT + 1.50, 0.80, 'N',     0.020, 1.2, 0.30, False, '—'),
    ('Veleta RS485',                       Z0_ANT + 1.50, 0.80, 'S',     0.025, 1.2, 0.30, False, '—'),
    ('Quad 2 m/70 cm (RADIOAFICIONADOS)',  Z0_ANT + 0.95, 0.00, 'rumbo', 0.065, 1.2, 1.30, False, '144/430 MHz'),
    ('Bigsignal 868 (Meshtastic HAT)',     Z0_ANT + 0.20, 0.80, 'N',     0.030, 1.2, 0.45, True,  '868 MHz'),
    ('Bigsignal 433 (iGate)',              Z0_ANT + 0.20, 0.80, 'S',     0.030, 1.2, 0.45, False, '433 MHz'),
    ('Garita BME280',                      Z0_ANT + 0.05, 0.45, 'N',     0.020, 1.2, 0.60, False, '—'),
]
BRAZOS = [(Z0_ANT + 1.70, 1.60), (Z0_ANT + 1.50, 1.60), (Z0_ANT + 0.20, 1.60), (Z0_ANT + 0.95, 0.50)]   # (altura, longitud) de brazos Ø25 y extensión del boom
EXTRAS_KG = 4.0                    # brazos y abrazaderas (solo peso), a Z0_ANT + 1 m
X50 = {'largo_m': 1.70, 'base_z_m': 8.00, 'conector': 'N hembra (X-50N)', 'masa_kg': 1.1, 'area_m2': 0.055}   # Ø de mástil admitido y carga de viento: mirar la hoja de Diamond
MOONRAKER = {'alto_m': 0.95, 'radiales_cm': '4 × 8 + 8 × 29,5', 'base_z_m': 5.90, 'masa_kg': 1.4, 'area_m2': 0.070,
             'nota': 'es de sobremesa (base magnética Ø125): placa metálica ≥ Ø250 mm en un brazo del mástil y coaxial de baja pérdida con N en lugar del RG58 BNC de 4 m'}

# --- mástil telescópico: 3 tramos × 3,00 m, 2 solapes (PENDIENTE: diámetros, paredes y solape reales) ----------
TRAMOS = [(50.0, 2.0, 3.00), (45.0, 2.0, 3.00), (40.0, 2.0, 3.00)]   # (d mm, t mm, L m) de abajo arriba; valores típicos galvanizados, PENDIENTE
SOLAPE_NOM = 0.40                  # m; se da el rango 0,35–0,45
SOLAPES = (0.35, 0.40, 0.45)
ANCLAJE_Z = 2.0                    # m, abrazadera a la pared (apoyo rígido lateral): PENDIENTE
GUY_Z = (5.5, 7.6)                 # m, collarines de vientos: ≈ 2/3 de la altura (en el solape 2) y tramo superior: PENDIENTE
GUY_R = 4.0                        # m, distancia horizontal de los anclajes al pie: PENDIENTE
GUY_EA = 100e9 * 4.2e-6            # N, cable inox Ø3 (7 × 19): ≈ 4,2 mm² metálicos, E aparente 100 GPa
GUY_MBL = 4500.0                   # N, rotura del cable Ø3 (estimada)
GUY_FS = 2.5                       # coeficiente mínimo de rotura frente a la tensión de cálculo
BASES = {'articulada': 0.0, 'empotrada': 1e12}   # rigidez al giro del pie (N·m/rad): se toma la envolvente de ambas
K_SOLAPE = 1.5                     # concentración de tensión en la boca del tubo exterior (estimada)
FLECHA_REL = 50                    # flecha máxima en cabeza = H / 50 (criterio de servicio, PENDIENTE de revisar)
Z_PIE = 0.0                        # m, altura del pie sobre el terreno (PENDIENTE: suma el tejado si va sobre uno)
E_ACERO = 210e9                    # Pa
RHO_ACERO = 7850.0                 # kg/m³
CF_MASTIL = 1.2                    # coeficiente de fuerza de un cilindro
FY = 235.0                         # MPa, acero S235 galvanizado
GAMMA = 1.5                        # coeficiente de seguridad en la carga de viento
G = 9.81
VB0 = 26.0                         # m/s, velocidad básica (zona A del CTE DB-SE-AE, Murcia)
RHO_AIRE = 1.25                    # kg/m³
QB = 0.5 * RHO_AIRE * VB0 ** 2     # Pa
RUGOSIDAD = (0.19, 0.05, 2.0)      # k, L, Z del grado III del CTE (rural con obstáculos aislados)
V_RACHA_OBS_KMH = 100.0            # rachas observadas en la región (Águilas, 99 km/h en enero de 2023)


def ce(z):
    """Coeficiente de exposición del CTE DB-SE-AE a la altura z sobre el pie."""
    k, l, zmin = RUGOSIDAD
    f = k * math.log(max(z + Z_PIE, zmin) / l)
    return f * (f + 7 * k)


def q(z):
    """Presión de viento de cálculo (N/m²) a la altura z."""
    return QB * ce(z)


def v_equiv_kmh(z):
    return math.sqrt(2 * q(z) / RHO_AIRE) * 3.6


def modulo(d, t):
    di = d - 2 * t
    return math.pi / 32 * (d ** 4 - di ** 4) / d   # mm³


def inercia(d, t):
    di = d - 2 * t
    return math.pi / 64 * (d ** 4 - di ** 4) * 1e-12   # m⁴


def area(d, t):
    di = d - 2 * t
    return math.pi / 4 * (d ** 2 - di ** 2) * 1e-6     # m²


def altura(solape=SOLAPE_NOM):
    return sum(l for _, _, l in TRAMOS) - (len(TRAMOS) - 1) * solape


def tramos_pos(solape=SOLAPE_NOM):
    """[(z0, z1, d, t)] de cada tramo: cada uno entra `solape` m en el inferior."""
    out, z0 = [], 0.0
    for d, t, l in TRAMOS:
        out.append((z0, z0 + l, d, t))
        z0 += l - solape
    return out


def solapes_pos(solape=SOLAPE_NOM):
    """[(z_boca_exterior, z_inicio_interior, índice del exterior)] de cada solape."""
    s = tramos_pos(solape)
    return [(s[j][1], s[j + 1][0], j) for j in range(len(s) - 1)]


def peso_mastil_kg(solape=SOLAPE_NOM):
    return sum(area(d, t) * (z1 - z0) for z0, z1, d, t in tramos_pos(solape)) * RHO_ACERO


def viga(zs, ei, w, F, Mn, muelle_w, muelle_th):
    """Viga de Euler-Bernoulli con nodos en zs (EI y w por elemento, F y Mn por nodo)
    y muelles de traslación/giro (dict nodo → rigidez). Devuelve (desplazamientos,
    giros, |momento| máximo en cada nodo)."""
    n = len(zs)
    nd = 2 * n
    K = [[0.0] * nd for _ in range(nd)]
    f = [0.0] * nd
    ke_l = []
    for e in range(n - 1):
        l = zs[e + 1] - zs[e]
        c = ei[e] / l ** 3
        ke = [[12 * c, 6 * l * c, -12 * c, 6 * l * c], [6 * l * c, 4 * l * l * c, -6 * l * c, 2 * l * l * c],
              [-12 * c, -6 * l * c, 12 * c, -6 * l * c], [6 * l * c, 2 * l * l * c, -6 * l * c, 4 * l * l * c]]
        fe = [w[e] * l / 2, w[e] * l * l / 12, w[e] * l / 2, -w[e] * l * l / 12]
        ke_l.append((ke, fe))
        for a in range(4):
            f[2 * e + a] += fe[a]
            for b in range(4):
                K[2 * e + a][2 * e + b] += ke[a][b]
    for i in range(n):
        f[2 * i] += F[i]
        f[2 * i + 1] += Mn[i]
    for i, k in muelle_w.items():
        K[2 * i][2 * i] += k
    for i, k in muelle_th.items():
        K[2 * i + 1][2 * i + 1] += k
    # eliminación gaussiana en banda (matriz simétrica definida positiva, semiancho 3)
    for c in range(nd):
        piv = K[c][c]
        for r in range(c + 1, min(nd, c + 4)):
            m = K[r][c] / piv
            if m:
                for k in range(c, min(nd, c + 4)):
                    K[r][k] -= m * K[c][k]
                f[r] -= m * f[c]
    x = [0.0] * nd
    for i in range(nd - 1, -1, -1):
        s = f[i] - sum(K[i][k] * x[k] for k in range(i + 1, min(nd, i + 4)))
        x[i] = s / K[i][i]
    mom = [0.0] * n
    for e in range(n - 1):
        ke, fe = ke_l[e]
        d = x[2 * e:2 * e + 4]
        for a in (1, 3):
            m = abs(sum(ke[a][b] * d[b] for b in range(4)) - fe[a])
            nodo = e if a == 1 else e + 1
            mom[nodo] = max(mom[nodo], m)
    return [x[2 * i] for i in range(n)], [x[2 * i + 1] for i in range(n)], mom


def _cubren(secs, z):
    return [s for s in secs if s[0] - 1e-9 <= z <= s[1] + 1e-9]


def tension_tubo(secs, z, m, n=0.0):
    """Tensión máxima (MPa) de los tubos que cubren z con momento m (N·m) y axil n (N):
    en un solape los dos tubos flectan juntos, repartiéndose el momento según su inercia."""
    cub = _cubren(secs, z)
    i_tot = sum(inercia(s[2], s[3]) for s in cub)
    a_tot = sum(area(s[2], s[3]) for s in cub)
    return max((m * (s[2] / 2000) / i_tot + n / a_tot) / 1e6 for s in cub)


def tension_sola(d, t, m, n=0.0):
    """Tensión (MPa) de un tubo solo, con momento m (N·m) y axil n (N)."""
    return m * 1e3 / modulo(d, t) + n / area(d, t) / 1e6


def analizar(solape=SOLAPE_NOM, vientos=True, base='articulada'):
    """Mástil bajo el viento de diseño. Con vientos=False solo hay pie y anclaje a pared.
    Tensiones con GAMMA sobre el viento; flecha y reacciones sin mayorar."""
    secs = tramos_pos(solape)
    h = altura(solape)
    puntuales = [(z, q(z) * cd * a) for n, z, b, r, a, cd, p, tx, banda in ANTENAS]
    puntuales += [(z, q(z) * 1.2 * l * 0.025) for z, l in BRAZOS]
    claves = {0.0, round(h, 3), ANCLAJE_Z}
    claves |= {round(z, 3) for s in secs for z in (s[0], s[1])}
    claves |= set(GUY_Z) | {round(z, 3) for z, _ in puntuales if z <= h}
    zs = sorted({round(i * 0.1, 3) for i in range(int(h / 0.1 + 1e-6) + 1)} | claves)
    zs = [z for i, z in enumerate(zs) if i == 0 or z - zs[i - 1] > 0.0095]
    idx = {round(z, 3): i for i, z in enumerate(zs)}
    n = len(zs)
    ei, w = [], []
    for e in range(n - 1):
        zm = (zs[e] + zs[e + 1]) / 2
        cub = _cubren(secs, zm)
        ei.append(E_ACERO * sum(inercia(s[2], s[3]) for s in cub))
        w.append(q(zm) * CF_MASTIL * cub[0][2] / 1000)
    F, Mn = [0.0] * n, [0.0] * n
    for z, fz in puntuales:
        if z > h + 1e-9:
            F[n - 1] += fz
            Mn[n - 1] += fz * (z - h)
        else:
            F[idx[round(z, 3)]] += fz
    mw, mth = {0: 1e12}, {0: BASES[base]}
    mw[idx[round(ANCLAJE_Z, 3)]] = mw.get(idx[round(ANCLAJE_Z, 3)], 0.0) + 1e12
    guys = []
    if vientos:
        for zg in GUY_Z:
            lg = math.hypot(zg, GUY_R)
            kh = GUY_EA / lg * (GUY_R / lg) ** 2
            mw[idx[round(zg, 3)]] = mw.get(idx[round(zg, 3)], 0.0) + kh
            guys.append((zg, kh, GUY_R / lg))
    u, th, mom = viga(zs, ei, w, F, Mn, mw, mth)
    tens = []
    for zg, kh, ca in guys:
        hh = kh * u[idx[round(zg, 3)]]
        tens.append((zg, abs(hh) / ca * GAMMA, abs(hh) / ca * math.sqrt(1 - ca * ca) * GAMMA))   # (z, T, componente vertical)
    # axil: pesos por encima de cada nodo + componente vertical de los vientos
    masas = [(z, p) for n_, z, b, r, a, cd, p, tx, bd in ANTENAS] + [(Z0_ANT + 1.0, EXTRAS_KG)]
    Naxil = []
    for i, z in enumerate(zs):
        nn = sum(p * G for zp, p in masas if zp > z + 1e-9)
        nn += sum(area(secs_[2], secs_[3]) * RHO_ACERO * G * (min(secs_[1], h) - max(secs_[0], z)) for secs_ in secs if secs_[1] > z)
        nn += sum(tv for (zg, _, tv) in tens if zg > z + 1e-9)
        Naxil.append(nn)

    def sig(i):
        return tension_tubo(secs, zs[i], GAMMA * mom[i], Naxil[i])

    s_base = max(sig(i) for i in range(n) if zs[i] <= secs[1][0] + 1e-9)
    s_max = max(sig(i) for i in range(n))
    solapes = []
    for zb, zi, j in solapes_pos(solape):
        ib, ii = idx[round(zb, 3)], idx[round(zi, 3)]
        s_boca = tension_sola(secs[j + 1][2], secs[j + 1][3], K_SOLAPE * GAMMA * mom[ib], Naxil[ib])
        s_fondo = tension_sola(secs[j][2], secs[j][3], K_SOLAPE * GAMMA * mom[ii], Naxil[ii])
        solapes.append({'z_boca': zb, 'z_fondo': zi, 'M_boca': GAMMA * mom[ib], 'M_fondo': GAMMA * mom[ii],
                        'sigma_boca': s_boca, 'sigma_fondo': s_fondo})
    s_sol = max([max(s['sigma_boca'], s['sigma_fondo']) for s in solapes] + [s_max])
    return {'H': h, 'solape': solape, 'vientos': vientos, 'base': base, 'zs': zs, 'u': u, 'M': [GAMMA * m for m in mom],
            'M_base': GAMMA * mom[0], 'sigma_base': s_base, 'sigma_max': s_max, 'sigma_cr': s_sol, 'solapes': solapes,
            'flecha_top_mm': u[-1] * 1000, 'flecha_max_mm': max(abs(x) for x in u) * 1000, 'guys': tens,
            'peso_kg': peso_mastil_kg(solape) + sum(a[6] for a in ANTENAS) + EXTRAS_KG}


def envolvente(vientos=True):
    """Peor caso entre pie articulado/empotrado y solape 0,35–0,45 m."""
    rs = [analizar(s, vientos, b) for s in SOLAPES for b in BASES]
    peor = {k: max(r[k] for r in rs) for k in ('sigma_base', 'sigma_max', 'sigma_cr', 'M_base')}
    peor['flecha_top_mm'] = max(abs(r['flecha_top_mm']) for r in rs)
    peor['guy_T_N'] = max([t for r in rs for _, t, _ in r['guys']] or [0.0])
    peor['H_min'], peor['H_max'] = altura(max(SOLAPES)), altura(min(SOLAPES))
    peor['vale'] = (peor['sigma_cr'] <= FY and peor['flecha_top_mm'] <= peor['H_min'] * 1000 / FLECHA_REL
                    and peor['guy_T_N'] * GUY_FS <= GUY_MBL)
    return peor, rs


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
             ('Meshtastic 433 (fibra)', 'ADS-B λ/4 + LNA', 433), ('Meshtastic 433 (fibra)', 'Discone grande (MULTIPERFIL)', 433),
             ('X50 Diamond (2 m/70 cm)', 'Discono Moonraker SkyScan', 433), ('X50 Diamond (2 m/70 cm)', 'Discone grande (MULTIPERFIL)', 433),
             ('X50 Diamond (2 m/70 cm)', 'Bigsignal 433 (iGate)', 433), ('Meshtastic 433 (fibra)', 'Discono Moonraker SkyScan', 433),
             ('Bigsignal 868 (Meshtastic HAT)', 'Discono Moonraker SkyScan', 868)]
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
    print('\nPeso total de antenas: %.1f kg (más brazos y abrazaderas, ≈ %.1f kg)\n' % (peso, peso + EXTRAS_KG))
    secs = tramos_pos()
    print('**Mástil telescópico** (PENDIENTE: diámetros, paredes y solape reales): %d tramos, %.2f m montado (%.2f–%.2f m con solapes de %.2f–%.2f m), %.1f kg\n' % (
        len(TRAMOS), altura(), altura(max(SOLAPES)), altura(min(SOLAPES)), min(SOLAPES), max(SOLAPES), peso_mastil_kg()))
    print('| Tramo | Ø × pared (mm) | Desde z (m) | Hasta z (m) | W (mm³) |')
    print('|---|---|---|---|---|')
    for i, (z0, z1, d, t) in enumerate(secs):
        print('| %d | %.0f × %.1f | %.2f | %.2f | %.0f |' % (i + 1, d, t, z0, z1, modulo(d, t)))
    print('\nAnclaje a pared a %.1f m (PENDIENTE) · vientos a %s m (PENDIENTE), %d cables inox Ø3 a 120°, anclajes a %.1f m del pie\n' % (
        ANCLAJE_Z, ' y '.join('%.1f' % z for z in GUY_Z), 3, GUY_R))
    print('**Viento de diseño:** vb,0 = %.0f m/s (zona A, CTE DB-SE-AE; Murcia), qb = %.0f N/m², grado III. A %.1f m: ce = %.2f, q = %.0f N/m² (≈ %.0f km/h; rachas observadas %.0f km/h).\n' % (
        VB0, QB, altura(), ce(altura()), q(altura()), v_equiv_kmh(altura()), V_RACHA_OBS_KMH))
    print('| Caso | Altura | σ base | σ solape 1 | σ solape 2 | σ máx. | Flecha en cabeza | T vientos (×%.1f) | ¿Vale? |' % GAMMA)
    print('|---|---|---|---|---|---|---|---|---|')
    res = []
    for vientos in (False, True):
        peor, rs = envolvente(vientos)
        res.append((vientos, peor))
        for r in rs:
            if r['solape'] not in (min(SOLAPES), SOLAPE_NOM, max(SOLAPES)):
                continue
            so = r['solapes']
            tm = max([t for _, t, _ in r['guys']] or [0.0])
            print('| %s, pie %s, solape %.2f m | %.2f m | %.0f MPa | %.0f MPa | %.0f MPa | %.0f MPa | %.0f mm | %.0f N | %s |' % (
                'con vientos' if vientos else '**sin vientos**', r['base'], r['solape'], r['H'], r['sigma_base'],
                max(so[0]['sigma_boca'], so[0]['sigma_fondo']), max(so[1]['sigma_boca'], so[1]['sigma_fondo']), r['sigma_cr'],
                abs(r['flecha_top_mm']), tm, 'sí' if r['sigma_cr'] <= FY else '**no**'))
    peor = res[1][1]
    print('\n**Envolvente con vientos:** σ base %.0f MPa, σ solapes/máx. %.0f MPa (límite S235 %.0f), flecha en cabeza %.0f mm (límite H/%d = %.0f mm), tensión de cálculo de los vientos %.0f N (rotura Ø3 ≈ %.0f N, mínimo ×%.1f): %s.' % (
        peor['sigma_base'], peor['sigma_cr'], FY, peor['flecha_top_mm'], FLECHA_REL, peor['H_min'] * 1000 / FLECHA_REL,
        peor['guy_T_N'], GUY_MBL, GUY_FS, 'VALE' if peor['vale'] else '**NO VALE**'))
    print('\n| Transmite | Recibe | Distancia (m) | Separación vertical (m) | En λ |')
    print('|---|---|---|---|---|')
    for a, b, d, dz, nl in separaciones():
        print('| %s | %s | %.2f | %.2f | %.1f |' % (a, b, d, dz, nl))
    return res


def png():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    fig, ax = plt.subplots(figsize=(11, 15))
    ht = altura()
    ax.set_aspect('equal'); ax.set_xlim(-2.6, 3.4); ax.set_ylim(-1.6, ht + 1.9); ax.axis('off')
    for (z0, z1, d, t), c in zip(tramos_pos(), ('#78909c', '#90a4ae', '#b0bec5')):
        ax.add_patch(Rectangle((-d / 2000 * 3, z0), d / 1000 * 3, z1 - z0, color=c, alpha=0.85))   # ancho ×3 para que se vea
    for zb, zi, j in solapes_pos():
        ax.add_patch(Rectangle((-0.08, zi), 0.16, zb - zi, color='#ef6c00', alpha=0.6))
    ax.add_patch(Rectangle((-0.35, -0.05), 0.7, 0.05, color='#455a64'))
    ax.text(0.4, 0.0, 'pie (z = 0): %s / empotrado según la base' % 'articulado', fontsize=9, va='center', color='#455a64')
    ax.add_patch(Rectangle((-0.2, ANCLAJE_Z - 0.03), 0.4, 0.06, color='#455a64'))
    ax.text(0.25, ANCLAJE_Z, 'anclaje a pared %.1f m (PENDIENTE)' % ANCLAJE_Z, fontsize=9, va='center', color='#455a64')
    ax.text(0.15, ht, 'altura montada %.2f m (solapes naranja)' % ht, fontsize=9, va='bottom', color='#e65100')
    for zg in GUY_Z:
        for sx in (-1, 1):
            ax.plot([0, sx * GUY_R], [zg, 0], color='#8d6e63', lw=1, ls='--')
        ax.plot([-0.07, 0.07], [zg, zg], color='#8d6e63', lw=5)
    ax.text(-2.5, -0.35, 'vientos a %s m (PENDIENTE): 3 cables Ø3 a 120°, anclajes a %.1f m del pie' % (' y '.join('%.1f' % z for z in GUY_Z), GUY_R), fontsize=8, color='#8d6e63')
    cols = {True: '#c62828', False: '#2e7d32'}
    for n, z, b, r, a, cd, p, tx, banda in ANTENAS:
        x = {'E': b, 'O': -b, 'N': b * 0.7, 'S': -b * 0.7}.get(r, 0)
        if r in ('punta', 'rumbo'):
            ax.plot([0, 0], [z - 0.4, z + 0.4], color=cols[tx], lw=4)
            ax.text(0.12, z, n + ('  [TX]' if tx else ''), fontsize=8, color=cols[tx], va='center')
            continue
        ax.plot([0, x], [z, z], color='#90a4ae', lw=2)
        ax.add_patch(Rectangle((x - 0.02, z), 0.04, 0.3, color=cols[tx]))
        ax.text(x + (0.06 if x >= 0 else -0.06), z + 0.15, n + ('  [TX]' if tx else '') + '  (%s)' % r, fontsize=7.5, color=cols[tx], ha='left' if x >= 0 else 'right')
    ax.text(-2.55, ht + 1.7, 'Plan del mástil telescópico BricoHams (vista frontal; N/S dibujados en perspectiva)', fontsize=13, weight='bold')
    ax.text(-2.55, ht + 1.5, 'Rojo: antenas que transmiten. Verde: solo recepción. Eggbeater (SAT) y lazo MLA-30 (HF) en postes aparte.', fontsize=9.5)
    ax.text(-2.55, -0.7, 'Fuera del mástil:\n• Eggbeater 2 m/70 cm (SATÉLITES): poste propio a ≥ 3 m, cielo despejado.\n'
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
