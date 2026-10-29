"""Bloqueo servidor Files: sin botones, 403 incluso autenticado, sin borrar."""
import ast
import importlib.machinery
import importlib.util
from pathlib import Path

root = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader('files_protegidos', str(root / 'files/bin/bricohams-owrx-files'))
mod = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
loader.exec_module(mod)
original = '''
class FilesController:
    def isAuthorized(self):
        return True
    def template_variables(self):
        admin = self.isAuthorized()
        return {"buttons": "delete" if admin else "", "download": True}
    def delete(self):
        Storage.getSharedInstance().deleteFile("test")
'''
nuevo = mod.proteger(original)
assert mod.proteger(nuevo) == nuevo
assert 'deleteFile' not in nuevo
ast.parse(nuevo)
ns = {}
exec(nuevo, ns)
c = ns['FilesController']()
assert c.isAuthorized()
assert c.template_variables() == {'buttons': '', 'download': True}
respuestas = []
c.send_response = lambda *a, **kw: respuestas.append((a, kw))
for autorizado in (True, False):
    c.isAuthorized = lambda: autorizado
    c.delete()
    assert respuestas[-1][1]['code'] == 403
    assert 'deshabilitado' in respuestas[-1][0][0]
for malo in ('class Other: pass', original.replace('admin = self.isAuthorized()', 'x = True')):
    try:
        mod.proteger(malo)
        raise AssertionError('Controlador incompatible aceptado')
    except ValueError:
        pass
install = (root / 'install.sh').read_text(encoding='utf-8')
assert '99bricohams-owrx-files' in install
assert 'bricohams-owrx-files ||' in install
print('OK: Files sin botones de borrado, servidor403 admin/visitantes, descargas intactas, idempotente')
