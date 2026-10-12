#!/usr/bin/env python3
"""v5.0 · bricohams-owrx-ctcss: subtono CTCSS («Subtono FM») en bookmarks y squelch CTCSS.

Se aplica sobre copias reales de OpenWebRX+ 1.2.126 (tests/datos/owrx-1.2.126):
el parche es idempotente, deja Python que compila, marca todas sus líneas,
copia el módulo y el JS, y --quitar deja los ficheros byte a byte como estaban.
Si hay numpy, además se prueba el detector CTCSS con señales sintéticas."""
import importlib.machinery
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
RUTA = os.path.join(RAIZ, 'files', 'bin', 'bricohams-owrx-ctcss')
SRC = os.path.join(RAIZ, 'files', 'share', 'bricohams-ctcss')
DATOS = os.path.join(RAIZ, 'tests', 'datos', 'owrx-1.2.126')

FICHEROS = {
    'OWRX_CTCSS_BOOKMARKS_PY': 'owrx_bookmarks.py',
    'OWRX_CTCSS_CTRL_PY': 'owrx_controllers_settings_bookmarks.py',
    'OWRX_CTCSS_DSP_PY': 'owrx_dsp.py',
    'OWRX_CTCSS_TABLE_JS': 'htdocs_lib_settings_BookmarkTable.js',
    'OWRX_CTCSS_INDEX_HTML': 'htdocs_index.html',
}


def leer(r):
    with open(r, encoding='utf-8', newline='') as f:
        return f.read()


def cargar(nombre, ruta):
    cargador = importlib.machinery.SourceFileLoader(nombre, ruta)
    spec = importlib.util.spec_from_loader(nombre, cargador)
    m = importlib.util.module_from_spec(spec)
    cargador.exec_module(m)
    return m


tmp = tempfile.mkdtemp()
try:
    originales = {}
    for var, nombre in FICHEROS.items():
        r = os.path.join(tmp, nombre)
        shutil.copyfile(os.path.join(DATOS, nombre), r)
        os.environ[var] = r
        originales[r] = leer(r)
    os.environ['OWRX_CTCSS_MOD_DST'] = os.path.join(tmp, 'bricohams_ctcss.py')
    os.environ['OWRX_CTCSS_JS_DST'] = os.path.join(tmp, 'bricohams-ctcss.js')
    os.environ['BH_CTCSS_SRC'] = SRC
    m = cargar('bhctcss', RUTA)

    assert m.main(['-q']) == 0
    parcheados = {r: leer(r) for r in originales}
    for r, t in parcheados.items():
        assert t != originales[r], '%s debe quedar parcheado' % os.path.basename(r)
        assert m.MARCA in t
        if r.endswith('.py'):
            compile(t, r, 'exec')
    assert leer(os.environ['OWRX_CTCSS_MOD_DST']) == leer(os.path.join(SRC, 'bricohams_ctcss.py'))
    assert leer(os.environ['OWRX_CTCSS_JS_DST']) == leer(os.path.join(SRC, 'bricohams-ctcss.js'))

    bm = parcheados[os.environ['OWRX_CTCSS_BOOKMARKS_PY']]
    assert '"ctcss"' in bm or "'ctcss'" in bm, 'el bookmark guarda el campo ctcss'
    ctl = parcheados[os.environ['OWRX_CTCSS_CTRL_PY']]
    assert 'Subtono FM' in ctl, 'columna «Subtono FM» en /settings/bookmarks'
    assert 'NFM' not in ''.join(l for l in ctl.splitlines() if m.MARCA in l), 'en la interfaz se llama «FM»'
    assert 'bricohams-ctcss.js' in parcheados[os.environ['OWRX_CTCSS_INDEX_HTML']]
    assert 'bricohams_ctcss' in parcheados[os.environ['OWRX_CTCSS_DSP_PY']]

    assert m.main(['-q']) == 0
    for r, t in parcheados.items():
        assert leer(r) == t, 'idempotente: %s' % os.path.basename(r)

    assert m.main(['--quitar', '-q']) == 0
    for r, t in originales.items():
        assert leer(r) == t, '--quitar restaura %s' % os.path.basename(r)
    assert not os.path.exists(os.environ['OWRX_CTCSS_MOD_DST'])
    assert not os.path.exists(os.environ['OWRX_CTCSS_JS_DST'])

    # Sin el módulo de origen no se parchea nada (OpenWebRX seguiría arrancando)
    os.environ['BH_CTCSS_SRC'] = os.path.join(tmp, 'no-existe')
    m.main(['-q'])
    for r, t in originales.items():
        assert leer(r) == t, 'sin módulo no se toca %s' % os.path.basename(r)
    os.environ['BH_CTCSS_SRC'] = SRC

    # El JS de cliente y el JS parcheado son sintácticamente válidos (si hay node)
    if shutil.which('node'):
        m.main(['-q'])
        for js in (os.environ['OWRX_CTCSS_TABLE_JS'], os.environ['OWRX_CTCSS_JS_DST']):
            subprocess.run(['node', '--check', js], check=True)
        m.main(['--quitar', '-q'])
finally:
    shutil.rmtree(tmp)

# ---- módulo DSP: normalización y detector (numpy opcional) -------------------
try:
    import numpy as np
except ImportError:
    np = None

if np is not None:
    sys.modules.setdefault('pycsdr', type(sys)('pycsdr'))
    try:
        c = cargar('bricohams_ctcss_t', os.path.join(SRC, 'bricohams_ctcss.py'))
    except ImportError:
        c = None
    if c is not None:
        assert c.normalizar_tono('88.54') == 88.5
        assert c.normalizar_tono(None) == 0.0 and c.normalizar_tono(0) == 0.0
        try:
            c.normalizar_tono(500)
            raise AssertionError('500 Hz fuera de rango')
        except ValueError:
            pass
        FS = 12000

        def senal(seg, tono=None, amp=0.15, voz=0.5):
            t = np.arange(int(FS * seg)) / FS
            x = voz * np.sin(2 * np.pi * 1000 * t)
            if tono:
                x = x + amp * np.sin(2 * np.pi * tono * t)
            return x.astype(np.float32)

        def abre(cfg, x, bloque=256):
            p = c.Procesador(FS, cfg)
            for i in range(0, len(x), bloque):
                y = p.procesar(x[i:i + bloque])
                if i > FS and np.abs(y).max() > 0.05:
                    return True
            return False

        assert abre(88.5, senal(3, 88.5)), 'el tono correcto abre'
        for mal in (85.4, 91.5, 177.3):
            assert not abre(88.5, senal(3, mal)), 'el tono %.1f no abre 88.5' % mal
        assert not abre(88.5, senal(3, None)), 'voz sin tono no abre'
print('OK test_ctcss_patch')
