#!/usr/bin/env python3
"""Motor mínimo NEC2 (nec2c) para las antenas BricoHams.

Construye el mazo de tarjetas (GW/GE/EX/FR/RP), ejecuta nec2c y lee
impedancia de entrada y diagramas. Sin dependencias fuera de la librería
estándar; las gráficas, si hay matplotlib.
"""
import math
import os
import re
import subprocess
import tempfile

C = 299.792458  # m·MHz


class Modelo:
    def __init__(self, titulo='BricoHams'):
        self.titulo = titulo
        self.hilos = []      # (tag, nseg, x1, y1, z1, x2, y2, z2, r)
        self.fuente = None   # (tag, seg)
        self.cargas = []     # tarjetas LD ya formateadas
        self.suelo = None

    def hilo(self, p1, p2, r, nseg=None, lambda_min=None):
        tag = len(self.hilos) + 1
        largo = math.dist(p1, p2)
        if nseg is None:
            lam = lambda_min or 0.5
            nseg = max(1, int(math.ceil(largo / (lam / 20))))
            if nseg % 2 == 0:
                nseg += 1
        self.hilos.append((tag, nseg) + tuple(p1) + tuple(p2) + (r,))
        return tag, nseg

    def poligono(self, puntos, r, cerrar=True, lambda_min=None, abierto_en=None):
        """Une los puntos con hilos. abierto_en=i deja sin unir el tramo i (hueco)."""
        tags = []
        n = len(puntos)
        tramos = range(n if cerrar else n - 1)
        for i in tramos:
            if abierto_en is not None and i == abierto_en:
                continue
            tags.append(self.hilo(puntos[i], puntos[(i + 1) % n], r, lambda_min=lambda_min))
        return tags

    def alimentar(self, tag, seg=None):
        nseg = [h for h in self.hilos if h[0] == tag][0][1]
        self.fuente = (tag, seg or (nseg + 1) // 2)

    def mazo(self, f_ini, f_fin, pasos, patron=None):
        """patron: lista de (theta0, phi0, ntheta, nphi, dtheta, dphi)."""
        out = ['CM %s' % self.titulo, 'CE']
        for h in self.hilos:
            out.append('GW %d %d %.5f %.5f %.5f %.5f %.5f %.5f %.6f' % h)
        out.append('GE 0' if self.suelo is None else 'GE 1')
        if self.suelo:
            out.append(self.suelo)
        out += self.cargas
        df = (f_fin - f_ini) / (pasos - 1) if pasos > 1 else 0
        out.append('FR 0 %d 0 0 %.4f %.5f' % (pasos, f_ini, df))
        out.append('EX 0 %d %d 0 1.0 0.0' % self.fuente)
        for p in (patron or []):
            out.append('RP 0 %d %d 1000 %.2f %.2f %.2f %.2f' % (p[2], p[3], p[0], p[1], p[4], p[5]))
        if not patron:
            out.append('XQ')
        out.append('EN')
        return '\n'.join(out) + '\n'

    def ejecutar(self, f_ini, f_fin, pasos, patron=None, guardar=None):
        mazo = self.mazo(f_ini, f_fin, pasos, patron)
        with tempfile.TemporaryDirectory() as d:
            fi, fo = os.path.join(d, 'm.nec'), os.path.join(d, 'm.out')
            open(fi, 'w').write(mazo)
            subprocess.run(['nec2c', '-i', fi, '-o', fo], check=True, capture_output=True)
            txt = open(fo, errors='replace').read()
        if guardar:
            open(guardar, 'w').write(mazo)
        return leer_salida(txt)


def leer_salida(txt):
    """Devuelve lista de dicts por frecuencia: f, z (complex), patron [(theta, phi, gdb)]."""
    res = []
    bloques = re.split(r'-+ FREQUENCY -+', txt)[1:]
    for b in bloques:
        m = re.search(r'FREQUENCY\s*[=:]\s*([0-9.E+-]+)\s*MHZ', b, re.I)
        f = float(m.group(1))
        mz = re.search(r'ANTENNA INPUT PARAMETERS.*?\n(?:.*\n){2}\s*\d+\s+\d+\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)', b)
        z = complex(float(mz.group(5)), float(mz.group(6))) if mz else None
        pat = []
        for mp in re.finditer(r'RADIATION PATTERNS.*?\n(?:.*\n){4}((?:\s*[-0-9.]+\s+[-0-9.]+\s+[-0-9.]+\s+[-0-9.]+\s+[-0-9.]+.*\n)+)', b):
            for ln in mp.group(1).splitlines():
                c = ln.split()
                if len(c) >= 5:
                    try:
                        pat.append((float(c[0]), float(c[1]), float(c[4]), float(c[2]), float(c[3])))
                    except ValueError:
                        pass
        res.append({'f': f, 'z': z, 'patron': pat})
    return res


def roe(z, z0=50.0):
    g = abs((z - z0) / (z + z0))
    return (1 + g) / (1 - g) if g < 1 else float('inf')


def ganancia(pat, theta, phi):
    best = None
    for t, p, g, *_ in pat:
        if abs(t - theta) < 1e-6 and abs((p - phi) % 360) < 1e-6:
            best = g
    return best


def maximo(pat):
    return max(pat, key=lambda x: x[2]) if pat else None
