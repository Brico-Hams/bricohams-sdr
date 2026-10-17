"""Paneles privados de satelites y clima: formularios, backup y acciones reales simuladas."""
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import time

root = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader('agendas_admin', str(root / 'files' / 'bin' / 'bricohams-mesh-admin'))
mod = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
loader.exec_module(mod)
with tempfile.TemporaryDirectory() as tmp:
    base = Path(tmp)
    mod.ENV_ETC = str(base / 'etc.env')
    mod.ENV_KIT = str(base / 'kit.env')
    mod.AGENDA_BACKUPS = str(base / 'backups')
    lista, pases, estado, wx = [str(base / n) for n in ('lista.json', 'pases.json', 'estado.json', 'wx.json')]
    contenido = '\n'.join('%s="%s"' % (k, v) for k, v in (
        ('SAT_LIST', lista), ('SATREC_PASES', pases), ('SATREC_OUT', estado), ('WXRED_OUT', wx),
        ('SECRETO_TEST', 'no-visible'), ('SATREC_EXCLUIR', 'ANTIGUO'), ('AMSAT_REPORT', 'no'))) + '\n'
    for f in (mod.ENV_ETC, mod.ENV_KIT):
        Path(f).write_text(contenido, encoding='utf-8')
    ahora = int(time.time())
    p = {'nombre': 'SAT<test>', 'norad': 1, 'aos': ahora + 3600, 'los': ahora + 4200, 'max_el': 50}
    for f, datos in ((lista, {'satelites': [{'nombre': p['nombre'], 'norad': 1}]}),
                     (pases, {'pases': [p]}), (estado, {'plan': [p], 'capturas': []}),
                     (wx, {'conectado': True})):
        Path(f).write_text(json.dumps(datos), encoding='utf-8')
    for ruta, funcion in ((mod.SATELITES, mod.pagina_satelites), (mod.CLIMA, mod.pagina_clima)):
        html = funcion('SesionAdmin_1234567890')
        assert 'name="csrf"' in html and ruta in html and 'no-visible' not in html
        assert 'alert-danger' not in html
        assert not mod.ACCIONES[mod.BASE].match('sat-guardar')
        assert not mod.ACCIONES[mod.BASE].match('wx-guardar')
    assert 'SAT&lt;test&gt;' in mod.pagina_satelites('sesion')
    ps = [dict(p, nombre='FO-29', norad=24278, hz=435850000),
          dict(p, nombre='Replicator-2', norad=69927, hz=400500000),
          dict(p, nombre='ISS', norad=25544, hz=145800000)]
    Path(pases).write_text(json.dumps({'pases': ps}), encoding='utf-8')
    for filtros, visible, ocultos in (
        ({'banda': '70cm'}, 'FO-29', ('Replicator-2', 'ISS')),
        ({'banda': '400'}, 'Replicator-2', ('FO-29', 'ISS')),
        ({'desde_mhz': '145,800', 'hasta_mhz': '145.800'}, 'ISS', ('FO-29', 'Replicator-2')),
    ):
        html = mod.pagina_satelites('sesion', filtros=filtros)
        assert '<td>%s</td>' % visible in html
        assert all('<td>%s</td>' % x not in html for x in ocultos)
        assert 'no cambian las capturas programadas' in html
        assert 'name="sat_1"' in html, 'filtrar no oculta ni desmarca las agendas'
    for filtros in ({'banda': 'inventada'}, {'desde_mhz': 'nan'}, {'hasta_mhz': '-1'},
                    {'desde_mhz': '436', 'hasta_mhz': '400'}, {'desde_mhz': '<script>'}):
        assert 'alert-danger' in mod.pagina_satelites('sesion', filtros=filtros)
    Path(pases).write_text(json.dumps({'pases': [p]}), encoding='utf-8')
    informes = mod.informes_capturas(
        [{'norad': 44881, 'nombre': 'TO-108', 'aos': 1792232748, 'estado': 'grabado', 'amsat': ''},
         {'norad': 25544, 'nombre': 'ISS', 'aos': 1792232748, 'estado': 'error: perfil'},
         {'norad': 44881, 'nombre': '<test>', 'aos': 1792232748, 'estado': 'grabado', 'amsat_enviado': True}],
        [{'norad': 44881, 'amsat': 'TO-108_[U/v]'}],
        {'CALLSIGN': 'N0TEST', 'STATION_LAT': '48', 'STATION_LON': '11'})
    assert informes.count('action="https://www.amsat.org/status/submit.php"') == 1
    assert 'name="SatReport" required' in informes and 'value="" disabled selected' in informes
    for nombre in ('SatName', 'SatCall', 'SatGridSquare', 'SatHour', 'SatPeriod', 'SatSubmit'):
        assert 'name="%s"' % nombre in informes
    assert 'No disponible' in informes and 'ya enviado' in informes and '&lt;test&gt;' in informes
    assert 'TO-108_[U/v]' in informes and 'no es una vista previa' in informes
    assert 'action="https://www.amsat.org' not in mod.informes_capturas(
        [{'norad': 44881, 'aos': 1792232748, 'estado': 'grabado'}],
        [{'norad': 44881, 'amsat': 'TO-108_[U/v]'}], {'CALLSIGN': 'N0CALL'})
    ordenes = []
    real_run = mod.subprocess.run
    def run(args, **kwargs):
        ordenes.append(args)
        return subprocess.CompletedProcess(args, 0)
    mod.subprocess.run = run
    try:
        for a, campos in (
            ('sat-omitir', {'pase': '1:%s' % p['aos']}),
            ('sat-incluir', {'pase': '1:%s' % p['aos']}),
            ('sat-guardar', {'SATREC_MIN_EL': '30', 'SATREC_ENABLE': 'yes', 'sat_1': 'yes'}),
            ('wx-guardar', {'WXRED_RADIO_KM': '120', 'WXRED_HORAS': '4', 'WXRED_SATELITES': 'yes'}),
        ):
            antes = Path(mod.ENV_ETC).read_bytes()
            mensaje = mod.accion(dict(campos, accion=a))
            assert 'Backup verificado' in mensaje
            assert mod.leer_env(mod.ENV_ETC) == mod.leer_env(mod.ENV_KIT)
            copia = sorted((base / 'backups').iterdir(), key=lambda f: f.stat().st_mtime_ns)[-1]
            with tarfile.open(copia / 'previo.tar.gz') as t:
                assert t.extractfile(Path(mod.ENV_ETC).as_posix().split(':', 1)[-1].lstrip('/')).read() == antes
            assert (copia / 'RESTAURAR.sh').is_file()
            assert mod.leer_env()['AMSAT_REPORT'] == 'no'
        assert mod.leer_env()['SATREC_EXCLUIR'] == 'ANTIGUO'
        assert mod.leer_env()['SATREC_OMITIR_PASES'] == ''
        n = len(ordenes)
        for campos in (
            {'accion': 'sat-omitir', 'pase': '999:1'},
            {'accion': 'wx-guardar', 'WXRED_RADIO_KM': '501', 'WXRED_HORAS': '3'},
            {'accion': 'wx-guardar', 'WXRED_RADIO_KM': '100', 'WXRED_HORAS': 'nan'},
            {'accion': 'sat-guardar', 'SATREC_MIN_EL': '91'},
        ):
            try:
                mod.accion(campos)
                raise AssertionError('Entrada invalida aceptada')
            except ValueError:
                pass
        assert len(ordenes) == n
        Path(pases).write_text(json.dumps({'pases': [dict(p, aos=ahora - 20, los=ahora + 600)]}))
        try:
            mod.accion({'accion': 'sat-guardar', 'SATREC_MIN_EL': '20'})
            raise AssertionError('Interrumpe un pase')
        except ValueError as x:
            assert 'pase en curso' in str(x)
        assert len(ordenes) == n
        backup_real = mod.backup_agendas
        def fallo_backup():
            raise OSError('Fallo de copia simulado')
        mod.backup_agendas = fallo_backup
        antes = Path(mod.ENV_ETC).read_bytes()
        try:
            mod.accion({'accion': 'wx-guardar', 'WXRED_RADIO_KM': '90', 'WXRED_HORAS': '3'})
            raise AssertionError('Guarda sin backup')
        except OSError:
            pass
        assert Path(mod.ENV_ETC).read_bytes() == antes and len(ordenes) == n
        mod.backup_agendas = backup_real
        def fallo_servicio(args, **kwargs):
            return subprocess.CompletedProcess(args, 1)
        mod.subprocess.run = fallo_servicio
        try:
            mod.accion({'accion': 'wx-guardar', 'WXRED_RADIO_KM': '90', 'WXRED_HORAS': '3'})
            raise AssertionError('Oculta fallo del servicio')
        except OSError as x:
            assert 'RESTAURAR.sh' in str(x) and 'sin confirmar' in str(x)
    finally:
        mod.subprocess.run = real_run
print('OK: agendas satelite/clima, backup, validacion, exclusiones, errores y proteccion de pases')
