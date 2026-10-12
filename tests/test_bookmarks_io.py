#!/usr/bin/env python3
"""v5.0 · bricohams-owrx-bookmarks-io: botones Importar/Exportar en /settings/bookmarks (solo
administrador). El parche es idempotente, no mete '$' en la plantilla (string.Template), deja un
controlador que compila, se quita sin dejar rastro y el instalador lo engancha a apt."""
import importlib.machinery
import importlib.util
import os
import shutil
import string
import tempfile

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
RUTA = os.path.join(RAIZ, 'files', 'bin', 'bricohams-owrx-bookmarks-io')

HTML = """<html><head><title>Bookmarks</title></head>
<body>
${header}
<div class="container">
    <div class="buttons">
        <button type="button" class="btn btn-primary bookmark-add">Add a new bookmark</button>
    </div>
    ${bookmarks}
</div>
</body>
</html>
"""

PY = """import json
import logging

logger = logging.getLogger(__name__)


class BookmarksController(object):
    def render_table(self):
        return "<table></table>"

    def template_variables(self):
        variables = {}
        variables["bookmarks"] = self.render_table()
        return variables
"""

tmp = tempfile.mkdtemp()
try:
    html = os.path.join(tmp, 'bookmarks.html')
    py = os.path.join(tmp, 'bookmarks.py')
    for ruta, txt in ((html, HTML), (py, PY)):
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(txt)
    os.environ['OWRX_BOOKMARKS_HTML'] = html
    os.environ['OWRX_BOOKMARKS_PY'] = py
    cargador = importlib.machinery.SourceFileLoader('bmio', RUTA)
    spec = importlib.util.spec_from_loader('bmio', cargador)
    m = importlib.util.module_from_spec(spec)
    cargador.exec_module(m)

    assert '$' not in m.bloque(), 'el bloque HTML no puede llevar $ (string.Template)'
    assert m.main(['-q']) == 0
    h1, p1 = open(html, encoding='utf-8').read(), open(py, encoding='utf-8').read()
    for i in ('bh-bm-importar', 'bh-bm-exportar', 'bh-bm-exportar-ed', 'bh-bm-fichero', 'bh-bm-estado'):
        assert 'id="%s"' % i in h1, i
    assert h1.index('bookmark-add') < h1.index(m.MARCA_INI), 'los botones van detrás de «Add»'
    assert h1.count(m.MARCA_INI) == 1 and h1.count(m.MARCA_FIN) == 1
    # la plantilla sigue siendo válida para string.Template de OpenWebRX+
    string.Template(h1).substitute(header='', bookmarks='')
    assert p1.count(m.MARCA_PY) == len(m.LINEAS_PY)
    compile(p1, py, 'exec')
    assert 'bh-bm-todos' in p1 and '\\\\u003c' in p1

    # idempotente
    assert m.main(['-q']) == 0
    assert open(html, encoding='utf-8').read() == h1 and open(py, encoding='utf-8').read() == p1

    # el código inyectado funciona: lista de bookmarks escapada y bien formada
    import json
    import types

    class B:
        def __init__(self, f, src):
            self.f, self.src = f, src

        def getFrequency(self):
            return self.f

        def getSrcFile(self):
            return self.src

        def __dict__(self):
            return {'name': '</script><b>', 'frequency': self.f, 'modulation': 'nfm'}

    class Bk:
        @staticmethod
        def getSharedInstance():
            return types.SimpleNamespace(getBookmarks=lambda: [B(145500000, None), B(98800000, 'x.json')])

    ns = {'Bookmarks': Bk}
    exec(compile(p1, py, 'exec'), ns)
    salida = ns['BookmarksController']().template_variables()['bookmarks']
    assert salida.count('</script>') == 1, 'el nombre del bookmark no puede cerrar el <script>'
    datos = json.loads(salida.split('id="bh-bm-todos">', 1)[1].rsplit('</script>', 1)[0])
    assert [b['frequency'] for b in datos['todos']] == [98800000, 145500000]
    assert datos['editable'] == [False, True]

    # sin ancla en el HTML: se pone antes de </body>
    with open(html, 'w', encoding='utf-8') as f:
        f.write('<html><body>\n</body></html>\n')
    assert m.main(['-q']) == 0
    assert m.MARCA_INI in open(html, encoding='utf-8').read()
    with open(html, 'w', encoding='utf-8') as f:
        f.write(h1)

    # --quitar deja los ficheros como estaban
    assert m.main(['-q', '--quitar']) == 0
    assert open(html, encoding='utf-8').read() == HTML
    assert open(py, encoding='utf-8').read() == PY

    # controlador irreconocible: no se toca y sale con error (en silencio con -q sale 0)
    with open(py, 'w', encoding='utf-8') as f:
        f.write('x = 1\n')
    assert m.main([]) == 1 and m.main(['-q']) == 0
    assert open(py, encoding='utf-8').read() == 'x = 1\n'

    inst = open(os.path.join(RAIZ, 'install.sh'), encoding='utf-8').read()
    assert 'install -m 755 "$FILES/bin/bricohams-owrx-bookmarks-io" /usr/local/bin/bricohams-owrx-bookmarks-io' in inst
    assert '99bricohams-owrx-bookmarks-io' in inst and 'bricohams-owrx-bookmarks-io -q' in inst
    print('OK bookmarks import/export')
finally:
    shutil.rmtree(tmp, ignore_errors=True)
