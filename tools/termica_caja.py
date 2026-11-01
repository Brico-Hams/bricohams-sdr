#!/usr/bin/env python3
"""Estudio térmico y de caudal de la caja v3 (electrónica, potencia y SAI) a 47 °C de ambiente.

Calcula, para cada módulo: calor interno, ganancia solar (con y sin tejadillo, ASA blanco y oscuro),
pérdida pasiva por las paredes, caudal necesario para ΔT de 5/10/15 K, caudal disponible de los dos
ventiladores de 60 mm (con la pérdida por capotas, malla y rejilla) y temperatura interior al 30/60/100 %.
Los consumos salen de tools/presupuesto_potencia.py y las medidas de hardware/caja_v3/caja_v3.scad.

Uso:  python3 tools/termica_caja.py            (informe)
      python3 tools/termica_caja.py --json     (resultados en JSON)
      python3 tools/termica_caja.py --opcion c (hub USB con su adaptador de 65 W en el módulo de potencia)

Todo es un modelo de régimen estacionario con supuestos explícitos (se imprimen); verifica con el
DS18B20 / RAK4631 de la caja y ajusta FAN_T_CAJA_* con las medidas reales.
"""
import inspect
import json
import math
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import presupuesto_potencia as pp  # noqa: E402
import sai_calculo as sc  # noqa: E402

SCAD = os.path.join(AQUI, '..', 'hardware', 'caja_v3', 'caja_v3.scad')

# ---- clima y físico ----
T_AMB = 47.0             # °C a la sombra (docs/manuales/17_CAJA_V3.md · Clima de diseño)
RHO, CP = 1.09, 1007.0   # aire a ~50 °C, kg/m³ y J/(kg·K)
G_SOL = 1000.0           # W/m² de irradiancia
ALFA_BLANCO, ALFA_OSCURO = 0.30, 0.90   # absortividad solar del ASA blanco / de uno oscuro
ELEV, AZ = 60.0, 30.0    # sol de verano: elevación y ángulo respecto a la normal de la cara delantera
REEMISION = 0.25         # parte del calor absorbido por el tejadillo que baja al techo de la caja
K_ASA, H_EXT, H_INT = 0.17, 10.0, 5.0   # W/mK, W/m²K fuera (viento ligero) y dentro (aire en calma)
M3H_A_CFM = 0.5886

# ---- rendimientos (supuestos) ----
EFIC_BUCK = 0.90         # reductor 12→5 V
EFIC_HUB = 0.82          # conversión interna del hub USB de 20 V a 5 V
EFIC_BOOST = 0.90        # elevador 12→20 V (opción b)
EFIC_ADAPTADOR = 0.85    # adaptador original de 65 W (opción c)
PERDIDAS_VARIAS_POTENCIA = 1.0   # W: gatillo PD, portafusibles, regleta y cableado
SAI_FLOTACION_W = 1.5    # W: calor de la carga de flotación de la batería y del transformador en reposo
SAI_PASO = 0.03          # pérdida del SAI en paso de red (line-interactive) sobre la potencia que pasa

# ---- ventiladores: 60 × 25 mm 12 V PWM de 4 hilos (tipo Noctua NF-A6x25 PWM; cifras de catálogo, a verificar) ----
VENT = {"modelo": "60 × 25 mm 12 V PWM (tipo Noctua NF-A6x25)", "q_m3h": 29.2, "p_pa": 21.0}
N_VENT = 2               # entrada abajo-izquierda y salida arriba-derecha, en serie (push-pull)
DERATING = 0.5           # pérdida de caudal de un ventilador por capota, malla antiinsectos y rejilla (40–60 %)
DUTIES = (0.3, 0.6, 1.0)

# ---- rejillas pasivas de potencia y SAI (copiadas de cuerpo() en el .scad; test_termica_caja.py las comprueba) ----
# (x0, x1, paso, ancho, alto) de cada ranura: entrada abajo y salida arriba; CD = coeficiente de descarga; la malla tapa la mitad
VENTS = {
    "potencia": ((20, 150, 9, 3.5, 18), (30, 140, 9, 3.5, 50)),
    "sai": ((20, 208, 9, 3.5, 24), (30, 198, 9, 3.5, 60)),
}
CD, LIBRE = 0.6, 0.5

# límite de temperatura del aire interior de cada módulo (°C): marca el veredicto
LIMITE = {"electronica": 60.0, "potencia": 60.0, "sai": 45.0}
MARGINAL = 5.0           # hasta límite + 5 K = «marginal»; más = «overheat»

COMPONENTES = [
    # nombre, límite del componente (°C), ΔT propio sobre el aire a plena carga (K) o None, nota y refrigeración
    ("Raspberry Pi 5 (SoC)", 85.0, 40.0, "throttling a 85 °C: refrigerador activo obligatorio y la Pi junto a la salida; limita la carga continua"),
    ("RTL-SDR V4 / dongles RTL", 70.0, 20.0, "carcasa de aluminio o disipador adhesivo en el R828D y el RTL2832U; en el flujo de entrada"),
    ("HackRF One / Pro", 70.0, 25.0, "disipadores adhesivos en la FPGA y el MAX2839; carcasa de aluminio con almohadilla térmica"),
    ("Airspy HF+ Discovery", 70.0, 15.0, "poca disipación (~0,8 W); aluminio de serie"),
    ("SDRplay RSPdx", 70.0, 20.0, "caja metálica; que le llegue el aire de entrada (bahía de expansión, abajo)"),
    ("LilyGO / RAK4631", 85.0, 10.0, "módulos industriales; sin disipador, lejos de los reductores"),
    ("Reductores 12→5 V", 85.0, 35.0, "disipador adhesivo en el inductor y el CI; fuera de la sombra de otros módulos; derate de corriente"),
    ("Cargador USB de 120 W (GaN)", 40.0, 30.0, "suele darse para ≤ 40 °C de ambiente: a 47 °C hay que ventilarlo o reducir la carga"),
    ("Batería de plomo del SAI", 40.0, 5.0, "a más de 40–45 °C la vida se reduce a la mitad por cada +8–10 K: a la sombra, ventilada y con flotación compensada"),
]


def dimensiones():
    """W, H, D de cada módulo y datos del tejadillo, leídos del .scad."""
    src = open(SCAD, encoding='utf-8').read()

    def trio(n):
        m = re.search(r'\b%s = EL \? ([\d.]+) : SAI \? ([\d.]+) : ([\d.]+);' % n, src)
        v = [float(x) for x in m.groups()]
        return {"electronica": v[0], "sai": v[1], "potencia": v[2]}

    def num(n):
        return float(re.search(r'\b%s = ([\d.]+);' % n, src).group(1))
    W, H, D = trio('W'), trio('H'), trio('D')
    return {"W": W, "H": H, "D": D, "T": num('T'), "GAP_LID": num('GAP_LID'), "LID_T": num('LID_T'),
            "ROOF_FRONT": num('ROOF_FRONT'), "ROOF_A": num('ROOF_A')}


def u_pared(t_mm):
    return 1.0 / (1.0 / H_EXT + t_mm / 1000.0 / K_ASA + 1.0 / H_INT)


def areas(w, h, d):
    """Áreas en m²: delante, arriba, un lado y total."""
    a_f, a_t, a_s = w * h * 1e-6, w * d * 1e-6, d * h * 1e-6
    return a_f, a_t, a_s, 2 * (a_f + a_t + a_s)


def solar(dim, mod, alfa, tejadillo):
    """(W absorbidos en las superficies, W que entran al interior)."""
    w, h, d = dim["W"][mod], dim["H"][mod], dim["D"][mod]
    a_f, a_t, a_s, _ = areas(w, h, d)
    e, f = math.radians(ELEV), math.radians(AZ)
    k_t, k_f, k_s = math.sin(e), math.cos(e) * math.cos(f), math.cos(e) * math.sin(f)
    if tejadillo:
        sombra = min(1.0, dim["ROOF_FRONT"] * math.tan(e) / math.cos(f) / h)   # fracción de la cara delantera a la sombra
        roof_l = d + dim["GAP_LID"] + dim["LID_T"] + dim["ROOF_FRONT"]
        a_roof = (w + 16) * roof_l * 1e-6
        q = alfa * G_SOL * (a_f * k_f * (1 - sombra) + a_s * k_s) + alfa * G_SOL * a_roof * k_t * REEMISION
    else:
        q = alfa * G_SOL * (a_t * k_t + a_f * k_f + a_s * k_s)
    return q, q * u_pared(dim["T"]) / H_EXT


def caudal_ventiladores(duty=1.0, derating=DERATING, n=N_VENT):
    """m³/h de n ventiladores en serie contra la resistencia de capotas+malla+rejilla.

    Curva lineal del ventilador P = Pmax·(1 − Q/Qmax) y sistema P = K·Q², con K tal que UN ventilador
    pierde `derating` de su caudal libre. En serie las presiones se suman; con la velocidad el caudal escala lineal."""
    assert 0 < derating < 1
    qmax, pmax = VENT["q_m3h"], VENT["p_pa"]
    q1, p1 = qmax * (1 - derating), pmax * derating
    k = p1 / q1 ** 2
    b, c = n * pmax / qmax, -n * pmax
    return duty * (-b + math.sqrt(b * b - 4 * k * c)) / (2 * k)


def cap_aire(q_m3h):
    return RHO * CP * q_m3h / 3600.0   # W/K


def caudal_natural(mod, h_mm, p_w, ua):
    """Tiro térmico por las ranuras (sin ventilador): itera ΔT ↔ caudal. Devuelve (m³/h, ΔT)."""
    def area(v):
        x0, x1, paso, an, al = v
        return (int((x1 - x0) // paso) + 1) * an * al * 1e-6 * LIBRE
    ai, ao = (area(v) for v in VENTS[mod])
    ae = 1.0 / math.sqrt(1.0 / ai ** 2 + 1.0 / ao ** 2)
    dt, q = 10.0, 0.0
    for _ in range(60):
        q = CD * ae * math.sqrt(2 * 9.81 * (h_mm / 1000.0) * dt / (T_AMB + 273.15 + dt)) * 3600.0
        dt = p_w / (ua + cap_aire(q))
    return q, dt


def cargas(opcion="b"):
    """Calor disipado en cada módulo (W) y su desglose. opcion: b = elevador 12→20 V en la electrónica,
    c = adaptador original de 65 W en el módulo de potencia."""
    r = pp.calcular()
    a = r["A"]
    p5pi, p5, p12 = a["5V-Pi"] * 5.0, a["5V"] * 5.0, a["12V"] * 12.0
    efic_cargador = (r["w5"] + r["w12"]) / r["total_w"]   # el mismo 0,88 de presupuesto_potencia
    dispositivos = p5pi + p5 + p12
    perd_pi = p5pi / EFIC_BUCK - p5pi
    p_hub_in = p5 / EFIC_HUB
    perd_hub = p_hub_in - p5
    if opcion == "b":
        perd_boost = p_hub_in / EFIC_BOOST - p_hub_in
        salida_cargador = p5pi / EFIC_BUCK + p_hub_in / EFIC_BOOST + p12
        perd_adaptador = 0.0
    else:
        perd_boost = 0.0
        salida_cargador = p5pi / EFIC_BUCK + p12
        perd_adaptador = p_hub_in / EFIC_ADAPTADOR - p_hub_in
    entrada_cargador = salida_cargador / efic_cargador
    perd_cargador = entrada_cargador - salida_cargador
    sai_reposo = inspect.signature(sc.potencia_bateria_ac).parameters["p_reposo"].default
    return {
        "electronica": {"W": dispositivos + perd_pi + perd_hub + perd_boost,
                        "desglose": {"dispositivos": dispositivos, "reductor Pi 5": perd_pi, "hub USB (interno)": perd_hub,
                                     "elevador 12→20 V": perd_boost}},
        "potencia": {"W": perd_cargador + perd_adaptador + PERDIDAS_VARIAS_POTENCIA,
                     "desglose": {"cargador 120 W": perd_cargador, "adaptador 65 W del hub": perd_adaptador, "varios": PERDIDAS_VARIAS_POTENCIA}},
        "sai": {"W": sai_reposo + SAI_PASO * entrada_cargador + SAI_FLOTACION_W,
                "desglose": {"reposo del SAI": sai_reposo, "paso de red": SAI_PASO * entrada_cargador, "flotación y transformador": SAI_FLOTACION_W}},
        "carga_cargador": salida_cargador / pp.CARGADOR_W,
        "eficiencia_cargador": efic_cargador,
    }


def veredicto(t, mod):
    lim = LIMITE[mod]
    return "ok" if t <= lim else "marginal" if t <= lim + MARGINAL else "overheat"


def resultados(opcion="b", derating=DERATING):
    dim = dimensiones()
    ca = cargas(opcion)
    out = {}
    for mod in ("electronica", "potencia", "sai"):
        w, h, d = dim["W"][mod], dim["H"][mod], dim["D"][mod]
        ua = u_pared(dim["T"]) * areas(w, h, d)[3]
        p = ca[mod]["W"]
        s_blanco_sin, in_blanco_sin = solar(dim, mod, ALFA_BLANCO, False)
        s_blanco, in_blanco = solar(dim, mod, ALFA_BLANCO, True)
        s_oscuro_sin, in_oscuro_sin = solar(dim, mod, ALFA_OSCURO, False)
        s_oscuro, in_oscuro = solar(dim, mod, ALFA_OSCURO, True)
        total = p + in_blanco
        req = {dt: {"m3h": total / (RHO * CP * dt) * 3600.0} for dt in (5, 10, 15)}
        for dt in req:
            req[dt]["cfm"] = req[dt]["m3h"] * M3H_A_CFM
        r = {"dim": (w, h, d), "UA_W_K": ua, "carga_W": p, "desglose": ca[mod]["desglose"],
             "solar": {"blanco_sin_tejadillo": s_blanco_sin, "blanco_con_tejadillo": s_blanco,
                       "oscuro_sin_tejadillo": s_oscuro_sin, "oscuro_con_tejadillo": s_oscuro,
                       "entra_blanco_con_tejadillo": in_blanco, "entra_blanco_sin_tejadillo": in_blanco_sin},
             "requerido": req}
        if mod == "electronica":
            r["disponible_m3h"] = caudal_ventiladores(1.0, derating)
            r["interior"] = {int(round(100 * du)): T_AMB + total / (ua + cap_aire(caudal_ventiladores(du, derating))) for du in DUTIES}
            r["interior"]["sin_ventilador"] = T_AMB + total / ua
            r["interior_sin_tejadillo_100"] = T_AMB + (p + in_blanco_sin) / (ua + cap_aire(r["disponible_m3h"]))
            r["interior_oscuro_100"] = T_AMB + (p + in_oscuro_sin) / (ua + cap_aire(r["disponible_m3h"]))
            r["interior_100"] = r["interior"][100]
        else:
            q, _ = caudal_natural(mod, h, total, ua)
            r["disponible_m3h"] = q
            r["interior_100"] = T_AMB + total / (ua + cap_aire(q))
            r["interior"] = {"sin_tejadillo": T_AMB + (p + in_blanco_sin) / (ua + cap_aire(q)), "oscuro_sin_tejadillo": T_AMB + (p + in_oscuro_sin) / (ua + cap_aire(q))}
        r["veredicto"] = veredicto(r["interior_100"], mod)
        out[mod] = r
    out["carga_cargador"] = ca["carga_cargador"]
    out["eficiencia_cargador"] = ca["eficiencia_cargador"]
    out["sensibilidad_derating"] = {d: caudal_ventiladores(1.0, d) for d in (0.4, 0.5, 0.6)}
    return out


def tabla_json(res):
    return [{"module": m, "load_W": round(res[m]["carga_W"], 1), "solar_W": round(res[m]["solar"]["blanco_con_tejadillo"], 1),
             "required_m3h_dT10": round(res[m]["requerido"][10]["m3h"], 1), "available_m3h": round(res[m]["disponible_m3h"], 1),
             "interior_C_full_fan": round(res[m]["interior_100"], 1), "verdict": res[m]["veredicto"]}
            for m in ("electronica", "potencia", "sai")]


def informe(opcion="b"):
    res = resultados(opcion)
    print("ESTUDIO TÉRMICO · caja v3 · aire exterior %.0f °C a la sombra · opción del hub USB: %s" % (T_AMB, opcion))
    print("Supuestos: sol %.0f W/m² (elevación %.0f°, %.0f° de la normal), α blanco %.1f / oscuro %.1f, ASA k=%.2f W/mK, h exterior %.0f, interior %.0f W/m²K,"
          % (G_SOL, ELEV, AZ, ALFA_BLANCO, ALFA_OSCURO, K_ASA, H_EXT, H_INT))
    print("  aire ρ=%.2f kg/m³ cp=%.0f J/kgK; reductor %.0f %%, hub %.0f %%, elevador %.0f %%, adaptador %.0f %%, cargador %.0f %% (de presupuesto_potencia)."
          % (RHO, CP, 100 * EFIC_BUCK, 100 * EFIC_HUB, 100 * EFIC_BOOST, 100 * EFIC_ADAPTADOR, 100 * res["eficiencia_cargador"]))
    print("  Ventilador: %s, %.1f m³/h (%.1f CFM) libre, %.0f Pa; pérdida de caudal por capota+malla+rejilla %.0f %%, %d en serie."
          % (VENT["modelo"], VENT["q_m3h"], VENT["q_m3h"] * M3H_A_CFM, VENT["p_pa"], 100 * DERATING, N_VENT))
    print("  Carga del cargador de 120 W: %.0f %% (máximo %.0f %%)" % (100 * res["carga_cargador"], 100 * pp.MARGEN_MAX))
    for mod in ("electronica", "potencia", "sai"):
        r = res[mod]
        w, h, d = r["dim"]
        print("\n== módulo %s (%.0f × %.0f × %.0f mm) · UA paredes %.2f W/K · límite del aire %.0f °C" % (mod, w, h, d, r["UA_W_K"], LIMITE[mod]))
        print("  calor interno %.1f W: %s" % (r["carga_W"], ", ".join("%s %.1f" % kv for kv in r["desglose"].items())))
        s = r["solar"]
        print("  sol absorbido: blanco %.1f W sin tejadillo / %.1f W con; oscuro %.1f / %.1f W; al interior (blanco+tejadillo) %.1f W"
              % (s["blanco_sin_tejadillo"], s["blanco_con_tejadillo"], s["oscuro_sin_tejadillo"], s["oscuro_con_tejadillo"], s["entra_blanco_con_tejadillo"]))
        print("  caudal necesario ΔT 5/10/15 K: " + " · ".join("%.1f / %.1f CFM" % (r["requerido"][k]["m3h"], r["requerido"][k]["cfm"]) for k in (5, 10, 15))
              + " (m³/h / CFM)")
        if mod == "electronica":
            print("  caudal disponible 100 %%: %.1f m³/h (%.1f CFM); interior a 30 / 60 / 100 %%: %.1f / %.1f / %.1f °C; sin ventilador %.0f °C"
                  % (r["disponible_m3h"], r["disponible_m3h"] * M3H_A_CFM, r["interior"][30], r["interior"][60], r["interior"][100], r["interior"]["sin_ventilador"]))
            print("  sin tejadillo: %.1f °C; caja oscura sin tejadillo: %.1f °C" % (r["interior_sin_tejadillo_100"], r["interior_oscuro_100"]))
        else:
            print("  sin ventilador: tiro térmico %.2f m³/h → interior %.1f °C (sin tejadillo %.1f, caja oscura %.1f)"
                  % (r["disponible_m3h"], r["interior_100"], r["interior"]["sin_tejadillo"], r["interior"]["oscuro_sin_tejadillo"]))
        print("  VEREDICTO: %s (%.1f °C)" % (r["veredicto"].upper(), r["interior_100"]))
    print("\nSensibilidad (caudal de los 2 ventiladores al 100 %): " + ", ".join("pérdida %.0f %% → %.1f m³/h" % (100 * k, v) for k, v in res["sensibilidad_derating"].items()))
    t_e = res["electronica"]["interior_100"]
    print("\nLímites de componentes (aire interior de la electrónica %.0f °C):" % t_e)
    for nom, lim, dt, nota in COMPONENTES:
        t = t_e if "Batería" not in nom and "Cargador" not in nom else (res["sai"]["interior_100"] if "Batería" in nom else res["potencia"]["interior_100"])
        est = "OK" if t + dt <= lim else "AL LÍMITE" if t <= lim else "SUPERA EL LÍMITE"
        print("  %-30s límite %3.0f °C · %s (aire %.0f + %.0f K) · %s" % (nom, lim, est, t, dt, nota))
    return res


if __name__ == "__main__":
    opc = "c" if "--opcion" in sys.argv and sys.argv[sys.argv.index("--opcion") + 1] == "c" else "b"
    if "--json" in sys.argv:
        print(json.dumps(tabla_json(resultados(opc)), ensure_ascii=False, indent=1))
    else:
        informe(opc)
