#!/usr/bin/env python3
"""bricohams-archivo-files: archivo permanente de «Files» y rotación a los últimos."""
import importlib.machinery
import importlib.util
import os
import tempfile
import time

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
loader = importlib.machinery.SourceFileLoader('af', os.path.join(RAIZ, 'files/bin/bricohams-archivo-files.py'))
spec = importlib.util.spec_from_loader('af', loader)
af = importlib.util.module_from_spec(spec)
loader.exec_module(af)


def entorno():
    base = tempfile.mkdtemp()
    cfg = {'files': os.path.join(base, 'tmp'), 'archivo': os.path.join(base, 'archivo'),
           'satrec': os.path.join(base, 'sat'), 'ultimos': 2, 'min_libre_mb': 0, 'reposo_s': 60}
    for d in (cfg['files'], os.path.join(cfg['satrec'], 'grabaciones')):
        os.makedirs(d)
    return cfg


def fichero(ruta, datos, edad):
    with open(ruta, 'wb') as f:
        f.write(datos)
    t = time.time() - edad
    os.utime(ruta, (t, t))


def nombres_archivo(cfg):
    return sorted(f for _, _, fs in os.walk(cfg['archivo']) for f in fs)


def test_archiva_todo_y_deja_los_dos_ultimos():
    cfg = entorno()
    for i, n in enumerate(['METEOR-261019-101500.png', 'SSTV-261019-101600-14230.png',
                           'FAX-261019-101700.png', 'REC-261019-101800-145800.mp3']):
        fichero(os.path.join(cfg['files'], n), b'x' * (i + 1), 600 - i * 60)
        time.sleep(0.02)                                    # ctime distinto
    fichero(os.path.join(cfg['files'], 'otro.log'), b'no', 600)
    res = af.vuelta(cfg, log=lambda *_: None)
    assert len(res['copiados']) == 4 and not res['errores']
    assert nombres_archivo(cfg) == sorted(['METEOR-261019-101500.png', 'SSTV-261019-101600-14230.png',
                                           'FAX-261019-101700.png', 'REC-261019-101800-145800.mp3'])
    assert sorted(os.listdir(cfg['files'])) == ['FAX-261019-101700.png', 'REC-261019-101800-145800.mp3', 'otro.log']
    # Segunda vuelta: nada nuevo, no duplica
    res = af.vuelta(cfg, log=lambda *_: None)
    assert res['copiados'] == [] and res['borrados'] == []
    assert len(nombres_archivo(cfg)) == 4


def test_no_toca_ficheros_en_escritura():
    cfg = entorno()
    for i in range(4):
        fichero(os.path.join(cfg['files'], 'REC-261019-10180%d.mp3' % i), b'a', 5)
    res = af.vuelta(cfg, log=lambda *_: None)
    assert res['copiados'] == [] and res['borrados'] == [] and len(res['pendientes']) == 4
    assert len(os.listdir(cfg['files'])) == 4


def test_mismo_nombre_otro_contenido_no_sobrescribe():
    cfg = entorno()
    ruta = os.path.join(cfg['files'], 'SSTV-261019-101600.png')
    fichero(ruta, b'uno', 600)
    af.vuelta(cfg, log=lambda *_: None)
    fichero(ruta, b'dos-distinto', 600)
    af.vuelta(cfg, log=lambda *_: None)
    assert nombres_archivo(cfg) == ['SSTV-261019-101600.png', 'SSTV-261019-101600~1.png']


def test_enlaces_satrec_se_archivan_pero_no_se_quitan():
    cfg = entorno()
    grab = os.path.join(cfg['satrec'], 'grabaciones')
    for i in range(3):
        n = 'SO50-26101%d-082700-436795.mp3' % i
        fichero(os.path.join(grab, n), b'mp3%d' % i, 600)
        try:
            os.symlink(os.path.join(grab, n), os.path.join(cfg['files'], n))
        except OSError:
            print('SKIP enlaces simbólicos no permitidos en este sistema')
            return
    res = af.vuelta(cfg, log=lambda *_: None)
    assert len(res['copiados']) == 3 and res['borrados'] == []
    assert len(os.listdir(cfg['files'])) == 3
    assert all(not os.path.islink(os.path.join(r, f)) for r, _, fs in os.walk(cfg['archivo']) for f in fs)


def test_enlaces_ajenos_a_satrec_se_ignoran():
    cfg = entorno()
    ajeno = os.path.join(os.path.dirname(cfg['files']), 'secreto.txt')
    fichero(ajeno, b'no-archivar', 600)
    enlace = os.path.join(cfg['files'], 'FAX-261019-101800.txt')
    try:
        os.symlink(ajeno, enlace)
    except OSError:
        print('SKIP enlaces simbólicos no permitidos en este sistema')
        return
    res = af.vuelta(cfg, log=lambda *_: None)
    assert res['copiados'] == [] and res['borrados'] == [] and nombres_archivo(cfg) == []
    assert os.path.islink(enlace) and open(ajeno, 'rb').read() == b'no-archivar'


def test_sin_espacio_no_copia_ni_borra():
    cfg = entorno()
    cfg['min_libre_mb'] = 1e15
    for i in range(4):
        fichero(os.path.join(cfg['files'], 'FAX-261019-10170%d.png' % i), b'f', 600)
    res = af.vuelta(cfg, log=lambda *_: None)
    assert res['errores'] == ['sin espacio']
    assert len(os.listdir(cfg['files'])) == 4 and nombres_archivo(cfg) == []


def test_simular_no_modifica():
    cfg = entorno()
    for i in range(4):
        fichero(os.path.join(cfg['files'], 'FAX-261019-10170%d.png' % i), b'f%d' % i, 600)
        time.sleep(0.02)
    res = af.vuelta(cfg, simular=True, log=lambda *_: None)
    assert len(res['copiados']) == 4 and res['borrados'] == []   # sin copia previa no se quitaría nada
    assert len(os.listdir(cfg['files'])) == 4 and nombres_archivo(cfg) == []


if __name__ == '__main__':
    for nombre, f in list(globals().items()):
        if nombre.startswith('test_'):
            f()
            print('OK', nombre)
