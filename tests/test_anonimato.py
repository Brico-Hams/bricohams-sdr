#!/usr/bin/env python3
"""Rama genérica: ningún fichero puede llevar datos de la estación original.

Los patrones se construyen troceados para que este test no se detecte a sí mismo.
"""
import os
import re
import sys
import stat

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROHIBIDOS = {
    'indicativo original': 'EA5' + 'KAO',
    'pueblo del QTH original': 'Lorqu' + '[ií]',
    'locator de 6 caracteres original': 'IM98' + '(ib|wb)',
    'latitud de la casa': r'38\.0' + r'8[0-9]{2}',
    'longitud de la casa': r'-1\.2' + r'5[0-9]{2}',
    'coordenadas exactas de la estación': r'37\.' + r'9838[0-9]{2,}|-1\.' + r'1280[0-9]{2,}',
    'APRS de la casa': '3804' + r'\.8|0011' + r'5\.0',
    'LAN original': r'192\.168' + r'\.254\.',
    'usuario de la Pi original': r'\bael' + r'm\b',
    'usuario de Windows original': r'(?i)(?:Users[\\/])anato' + r'l(?:\.lopez)?[\\/]',
}
# Ficheros con números que coinciden por casualidad (tablas de firmware, claves)
EXCLUIR_NOMBRES = {'mastil.py', 'magic_key.js', 'test_anonimato.py', 'LICENSE', '.git'}
EXCLUIR_EXT = {'.hex', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.uf2', '.bin',
               '.stl', '.pdf', '.woff', '.woff2', '.ttf', '.zip', '.gz'}


def ficheros():
    for base, dirs, nombres in os.walk(RAIZ):
        dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__', 'node_modules')]
        for n in nombres:
            if n in EXCLUIR_NOMBRES or os.path.splitext(n)[1].lower() in EXCLUIR_EXT:
                continue
            ruta = os.path.join(base, n)
            try:
                if stat.S_ISREG(os.lstat(ruta).st_mode):
                    yield ruta
            except OSError:
                continue


def main():
    regex = {k: re.compile(v, re.I) for k, v in PROHIBIDOS.items()}
    fallos = []
    for ruta in ficheros():
        try:
            with open(ruta, encoding='utf-8') as f:
                texto = f.read()
        except (UnicodeDecodeError, OSError):
            continue
        for motivo, rx in regex.items():
            for m in rx.finditer(texto):
                linea = texto.count('\n', 0, m.start()) + 1
                fallos.append(f'{os.path.relpath(ruta, RAIZ)}:{linea}: {motivo} ({m.group(0)})')
    if fallos:
        print('\n'.join(fallos[:50]))
        print(f'FALLO test_anonimato: {len(fallos)} restos de la estación original')
        return 1
    print('OK test_anonimato: sin indicativo, QTH, locator, LAN ni usuarios de la estación original')
    return 0


if __name__ == '__main__':
    sys.exit(main())
