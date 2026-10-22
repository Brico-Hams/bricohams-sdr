#!/usr/bin/env python3
"""Presupuesto de potencia de la estación con los SDR futuros.

Consumos NOMINALES (verifícalos con la hoja de datos de tu unidad). Carril 12 V = bus de la caja de
potencia; dos reductores 12→5 V de 5 A independientes: «5V-Pi» (solo la Pi y su electrónica) y «5V» (hub alimentado de los SDR USB).
Uso: python3 tools/presupuesto_potencia.py
"""
CARGADOR_W = 120.0            # cargador de la caja de potencia
MARGEN_MAX = 0.60             # carga continua máxima sobre el cargador
REDUCTOR_5V_A = 5.0           # reductor 12→5 V
MARGEN_5V = 0.80              # carga continua máxima sobre el reductor

# (equipo, carril, amperios nominales, estado)
EQUIPOS = [
    ("Pi 5 + HAT + LilyGO + RAK4631 + ventiladores + Pico", "5V-Pi", 3.6, "actual"),
    ("Mini + V3 + FlightStick + V4 (USB)", "5V", 1.1, "actual"),
    ("HackRF Pro (USB)", "5V", 0.50, "futuro"),
    ("Airspy HF+ Discovery (USB)", "5V", 0.20, "futuro"),
    ("RSPdx (USB)", "5V", 0.30, "futuro"),
    ("3 dongles RTL/FlightStick adicionales (USB)", "5V", 0.90, "futuro"),
    ("Hermes-Lite 2 (12 V, Ethernet)", "12V", 1.10, "futuro"),
]
FUSIBLES = {"5V": 5.0, "5V-Pi": 5.0, "12V": 3.0}   # A, ATO por carril


def calcular():
    carril = {"5V": 0.0, "5V-Pi": 0.0, "12V": 0.0}
    for _, c, a, _ in EQUIPOS:
        carril[c] += a
    w5 = (carril["5V"] + carril["5V-Pi"]) * 5.0
    w12 = carril["12V"] * 12.0
    total_w = (w5 + w12) / 0.88          # rendimiento del reductor/PD ≈ 88 %
    return {"A": carril, "w5": w5, "w12": w12, "total_w": total_w,
            "carga": total_w / CARGADOR_W, "a5_reductor": max(carril["5V"], carril["5V-Pi"])}


if __name__ == "__main__":
    r = calcular()
    for n, c, a, e in EQUIPOS:
        print("%-55s %-6s %5.2f A  %s" % (n, c, a, e))
    print("5 V (el reductor más cargado): %.1f A de %.1f A · 12 V: %.1f A · total desde el cargador %.0f W (%.0f %% de %.0f W)"
          % (r["a5_reductor"], REDUCTOR_5V_A, r["A"]["12V"], r["total_w"], 100 * r["carga"], CARGADOR_W))
