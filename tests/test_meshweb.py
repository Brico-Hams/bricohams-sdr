#!/usr/bin/env python3
"""Guarded client adapter: pinning, idempotence and preservation of vendor files."""
import hashlib
import importlib.machinery
import importlib.util
from pathlib import Path
import tempfile

root = Path(__file__).resolve().parent.parent
loader = importlib.machinery.SourceFileLoader('meshweb', str(root / 'files' / 'bin' / 'bricohams-meshweb'))
m = importlib.util.module_from_spec(importlib.util.spec_from_loader('meshweb', loader))
loader.exec_module(m)
with tempfile.TemporaryDirectory() as d:
    p = Path(d)
    original = p / m.ORIGINAL
    original.write_bytes(b'const official = true;')
    html = p / 'index.html'
    initial = '<html><script type="module" src="/%s"></script></html>' % m.ORIGINAL
    html.write_text(initial, encoding='utf-8')
    adapter = root / 'files' / 'meshweb' / 'favoritos.js'
    try:
        m.preparar(p, adapter)
        raise AssertionError('no se rechaza un cliente desconocido')
    except ValueError:
        assert html.read_text(encoding='utf-8') == initial
    m.SHA256 = hashlib.sha256(original.read_bytes()).hexdigest()
    nombre = m.preparar(p, adapter, comprobar=True)
    assert not (p / nombre).exists() and html.read_text(encoding='utf-8') == initial
    assert m.preparar(p, adapter) == nombre
    assert (p / nombre).read_bytes().startswith(original.read_bytes() + b'\n')
    assert original.read_bytes() == b'const official = true;'
    assert nombre in html.read_text(encoding='utf-8')
    assert m.preparar(p, adapter) == nombre
    html.write_text('<html></html>', encoding='utf-8')
    try:
        m.preparar(p, adapter)
        raise AssertionError('no se rechaza un indice desconocido')
    except ValueError:
        assert html.read_text(encoding='utf-8') == '<html></html>'
print('OK meshweb: checksum, rechazo de versiones desconocidas, archivo original intacto e idempotencia')
