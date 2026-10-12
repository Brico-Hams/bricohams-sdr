#!/usr/bin/env python3
"""v5.0 · bricohams-owrx-repeaterbook: campo «RepeaterBook API key» en /settings/general (solo
administrador). El parche es idempotente, deja un controlador que compila, va antes de «Map
settings», no se duplica si OpenWebRX+ ya trae el campo y se quita sin dejar rastro."""
import importlib.machinery
import importlib.util
import os
import shutil
import tempfile

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
RUTA = os.path.join(RAIZ, 'files', 'bin', 'bricohams-owrx-repeaterbook')

PY = '''from owrx.form.input import (
    TextInput,
    PasswordInput,
)
from owrx.form.section import Section


class GeneralSettingsController(object):
    def getSections(self):
        return [
            Section(
                "Receiver information",
                TextInput("receiver_admin", "Receiver admin"),
            ),
            Section(
                "Map settings",
                TextInput("map_type", "Map type"),
            ),
        ]
'''

tmp = tempfile.mkdtemp()
try:
    py = os.path.join(tmp, 'general.py')
    with open(py, 'w', encoding='utf-8') as f:
        f.write(PY)
    os.environ['OWRX_GENERAL_PY'] = py
    cargador = importlib.machinery.SourceFileLoader('rbk', RUTA)
    spec = importlib.util.spec_from_loader('rbk', cargador)
    m = importlib.util.module_from_spec(spec)
    cargador.exec_module(m)

    assert m.main(['-q']) == 0
    p1 = open(py, encoding='utf-8').read()
    compile(p1, py, 'exec')
    assert p1.count('"repeaterbook_api_key"') == 1
    assert p1.index('"RepeaterBook"') < p1.index('"Map settings"'), 'la sección va antes de Map settings'
    assert 'PasswordInput(' in p1 and m.MARCA in p1

    assert m.main(['-q']) == 0
    assert open(py, encoding='utf-8').read() == p1, 'el parche debe ser idempotente'

    assert m.main(['--quitar', '-q']) == 0
    assert open(py, encoding='utf-8').read() == PY, '--quitar deja el fichero original'

    nativo = PY.replace('TextInput("map_type", "Map type"),',
                        'TextInput("map_type", "Map type"),\n                PasswordInput(\n'
                        '                    "repeaterbook_api_key", "x"),')
    with open(py, 'w', encoding='utf-8') as f:
        f.write(nativo)
    assert m.main(['-q']) == 0
    assert open(py, encoding='utf-8').read() == nativo, 'no duplica un campo nativo'

    with open(py, 'w', encoding='utf-8') as f:
        f.write('class X: pass\n')
    assert m.main(['-q']) == 0, 'en modo -q (apt) nunca falla'
    assert m.main([]) == 1, 'sin -q avisa si el controlador es irreconocible'
    assert open(py, encoding='utf-8').read() == 'class X: pass\n'
finally:
    shutil.rmtree(tmp)
print('OK test_repeaterbook')
