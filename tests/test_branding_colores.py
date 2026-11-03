#!/usr/bin/env python3
"""Manual de color BricoHams: los tokens existen y la paleta antigua ya no aparece en las interfaces propias."""
import glob
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TOKENS_CLAROS = ('--bg:#FFFFFF', '--surface:#F6F7F8', '--text:#23272B', '--link:#AA410B', '--brand-orange:#F26B1D')
TOKENS_OSCUROS = ('--bg:#111518', '--surface:#1C2329', '--text:#F6F8FA', '--link:#FFA06A', '--focus:#FFC18F')
PALETA_ANTIGUA = ('#f7941d', '#f26b21', '#a64b00', '#0b1418', '#0e1420', '#111d22', '#172131',
                  '#89b9ff', '#205da8', '#ff6b00', '#0a2540')


def leer(*r):
    return open(os.path.join(RAIZ, *r), encoding='utf-8').read()


def propios():
    rutas = glob.glob(os.path.join(RAIZ, 'files', 'web', '*.html')) + [os.path.join(RAIZ, 'files', 'web', 'index.html.tmpl')]
    rutas += [os.path.join(RAIZ, 'files', 'bin', b) for b in ('bricohams-mesh-admin', 'bricohams-owrx-botones', 'bricohams-google-auth')]
    base = os.path.join(RAIZ, 'files', 'htdocs', 'plugins')
    for sub in ('receiver', 'map'):
        for ext in ('js', 'css'):
            rutas += glob.glob(os.path.join(base, sub, '**', '*.' + ext), recursive=True)
    # plugins de terceros / upstream: fuera del manual
    ajenos = ('uikit', 'rig_skin', 'doppler', 'notify', 'keyboard_shortcuts', 'ui_basic_theme', 'ui_status',
              'ui_chat', 'thumbtune', 'toggle_scannable', 'example_theme', 'html2canvas', 'layer_qth_maidenhead')
    return [r for r in rutas if not any(os.sep + a in r for a in ajenos)]


def main():
    compact = lambda s: re.sub(r'\s+', '', s)

    marca = compact(leer('files', 'htdocs', 'plugins', 'receiver', 'marca', 'marca.js'))
    for t in TOKENS_CLAROS + TOKENS_OSCUROS:
        assert compact(t) in marca or compact(t).lower() in marca.lower(), 'marca.js sin token ' + t
    assert 'data-theme' in marca and 'bh_theme' in marca

    index = compact(leer('files', 'web', 'index.html.tmpl'))
    for t in TOKENS_CLAROS + TOKENS_OSCUROS:
        assert compact(t) in index, 'index.html.tmpl sin token ' + t
    assert 'localStorage' in index and 'data-theme' in index

    for p in propios():
        txt = leer(os.path.relpath(p, RAIZ)).lower()
        for viejo in PALETA_ANTIGUA:
            assert viejo not in txt, '%s conserva %s' % (os.path.relpath(p, RAIZ), viejo)

    for p in glob.glob(os.path.join(RAIZ, 'files', 'web', '*.html')):
        txt = open(p, encoding='utf-8').read()
        assert ':focus-visible' in txt and 'var(--focus)' in txt, p

    print('OK test_branding_colores')


if __name__ == '__main__':
    main()
