#!/usr/bin/env python3
"""Utilidades STL sin dependencias.
  stl_util.py binario <dir>   convierte los STL ASCII de OpenSCAD a binario (ocupan ~5 veces menos)
  stl_util.py medidas <dir>   medidas de cada pieza; sale con error si alguna no cabe en 250 mm
"""
import os
import re
import struct
import sys

LIM = 250.0


def leer(path):
    """Devuelve la lista de triángulos ((n), (v1), (v2), (v3)) de un STL ASCII o binario."""
    data = open(path, 'rb').read()
    if data[:5] == b'solid' and b'facet' in data[:400]:
        nums = re.findall(rb'(?:normal|vertex)\s+(\S+)\s+(\S+)\s+(\S+)', data)
        v = [tuple(map(float, n)) for n in nums]
        return [tuple(v[i:i + 4]) for i in range(0, len(v), 4)]
    n = struct.unpack('<I', data[80:84])[0]
    tris = []
    for k in range(n):
        f = struct.unpack('<12f', data[84 + k * 50: 84 + k * 50 + 48])
        tris.append((f[0:3], f[3:6], f[6:9], f[9:12]))
    return tris


def binario(path):
    tris = leer(path)
    with open(path, 'wb') as fh:
        fh.write(b'BricoHams SDR - caja N0CALL'.ljust(80, b' '))
        fh.write(struct.pack('<I', len(tris)))
        for t in tris:
            fh.write(struct.pack('<12fH', *t[0], *t[1], *t[2], *t[3], 0))


def medidas(path):
    pts = [p for t in leer(path) for p in t[1:]]
    return tuple(max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3)), len(pts) // 3


def main():
    modo, carpeta = sys.argv[1], sys.argv[2]
    ficheros = sorted(f for f in os.listdir(carpeta) if f.endswith('.stl'))
    if modo == 'binario':
        for f in ficheros:
            binario(os.path.join(carpeta, f))
        return 0
    mal = 0
    print(f"{'pieza':20s} {'X':>7s} {'Y':>7s} {'Z':>7s} {'triáng.':>8s}")
    for f in ficheros:
        d, n = medidas(os.path.join(carpeta, f))
        ok = all(v <= LIM for v in d)
        mal += not ok
        print(f"{f[:-4]:20s} {d[0]:7.1f} {d[1]:7.1f} {d[2]:7.1f} {n:8d} {'OK' if ok else 'NO CABE'}")
    return 1 if mal else 0


if __name__ == '__main__':
    sys.exit(main())
