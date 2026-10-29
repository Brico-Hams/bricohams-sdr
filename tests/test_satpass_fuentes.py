"""Catalogo y fallback orbital: nunca asociar TLE de otro NORAD."""
import importlib.machinery
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

root = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader('satpass_fuentes', str(root / 'files/bin/bricohams-satpass.py'))
sp = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
loader.exec_module(sp)
assert sp.Satrec is not None, 'Falta la dependencia del proyecto sgp4'
catalogo = json.loads((root / 'data/satelites.json').read_text(encoding='utf-8'))['satelites']
por_nombre = {s['nombre']: s for s in catalogo}
for nombre, norad, mhz in (('RS-44', 44909, 435.640), ('FO-29', 24278, 435.850),
                           ('SO-50', 27607, 436.795), ('ISS', 25544, 145.800),
                           ('Replicator-2', 69927, 400.500), ('SAKHACUBE-CHOLBON', 67290, 437.350),
                           ('MARMOTSat', 69912, 145.875)):
    assert por_nombre[nombre]['norad'] == norad and por_nombre[nombre]['mhz'] == mhz
template = json.loads((root / 'files/openwebrx/settings.json.tmpl').read_text(encoding='utf-8'))
for nombre in ('RS-44', 'FO-29', 'SO-50', 'ISS', 'Replicator-2', 'SAKHACUBE-CHOLBON', 'MARMOTSat'):
    sat = por_nombre[nombre]
    receptor, perfil = sat['perfil'].split('|')
    cfg = template['sdrs'][receptor]['profiles'][perfil]
    assert abs(sat['mhz'] * 1e6 - cfg['center_freq']) + 15000 < cfg['samp_rate'] / 2
fixture = json.loads((root / 'tests/datos/iss_omm.json').read_text())
entrada = {'norad_cat_id': 99999, 'tle0': '0 ISS', 'tle1': fixture['tle'][0], 'tle2': fixture['tle'][1]}
solicitudes = []
def descargar(req, timeout):
    solicitudes.append(req.full_url)
    if 'celestrak.org' in req.full_url:
        raise TimeoutError('fallo simulado')
    return io.BytesIO(json.dumps([entrada]).encode())
with tempfile.TemporaryDirectory() as tmp, patch.object(sp.urllib.request, 'urlopen', descargar):
    cache = str(Path(tmp) / 'tle.json')
    datos = sp.descargar_omm([25544], cache, satnogs_ids={25544: 99999})
    assert int(datos[25544]['NORAD_CAT_ID']) == 25544
    assert 'norad_cat_id=99999' in solicitudes[-1]
    assert json.loads(Path(cache).read_text())['25544']['fuente'] == 'SatNOGS'
    solicitudes.clear()
    assert sp.descargar_omm([25544], cache) == datos and not solicitudes
    assert not sp.descargar_omm([12345], str(Path(tmp) / 'otro.json'), satnogs_ids={12345: 99999})
print('OK: siete satelites, perfiles con margen Doppler, fallback validado y cache.')
