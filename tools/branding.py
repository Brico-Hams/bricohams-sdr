#!/usr/bin/env python3
"""v4: rehace la imagen superior de OpenWebRX (files/branding/receiver_top_photo.png)
con la tarjeta del logo de BricoHams MÁS PEQUEÑA, arriba a la derecha, para que no
tape la web. Parte de la imagen v3 (paisaje de Mi QTH a la izquierda) y de
files/branding/logo_tarjeta.png.

Uso: python3 tools/branding.py [escala]     (escala de la tarjeta, por defecto 0.42)
"""
import os
import sys

from PIL import Image

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
B = os.path.join(RAIZ, 'files', 'branding')


def fondo(w, h, x0=0):
    """Degradado del fondo original (#24262a → #352b27 de izquierda a derecha)."""
    a, b = (0x24, 0x26, 0x2a), (0x35, 0x2b, 0x27)
    img = Image.new('RGB', (w, h))
    px = img.load()
    for x in range(w):
        f = (x0 + x) / 1919.0
        c = tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))
        for y in range(h):
            px[x, y] = c
    return img


def main(escala=0.42):
    base = Image.open(os.path.join(B, 'receiver_top_photo_v3.png')).convert('RGB')
    W, H = base.size
    # borra la tarjeta grande (zona derecha, sin tocar las franjas inferiores)
    bg = fondo(W, H - 14)
    region = base.crop((0, 0, W, H - 14))
    mask = Image.new('L', (W, H - 14), 0)
    px = mask.load()
    for x in range(W):                     # se funde en 780–860 (como la v3) y queda solo el fondo desde 860
        a = 255 if x < 780 else (0 if x >= 860 else int(255 * (860 - x) / 80))
        for y in range(H - 14):
            px[x, y] = a
    base.paste(Image.composite(region, bg, mask), (0, 0))
    card = Image.open(os.path.join(B, 'logo_tarjeta.png')).convert('RGBA')
    cw, ch = int(card.width * escala), int(card.height * escala)
    card = card.resize((cw, ch), Image.LANCZOS)
    base.paste(card.convert('RGB'), (W - cw - 36, 26))
    base.save(os.path.join(B, 'receiver_top_photo.png'), optimize=True)
    print('receiver_top_photo.png: tarjeta %d×%d (escala %.2f)' % (cw, ch, escala))


if __name__ == '__main__':
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 0.42)
