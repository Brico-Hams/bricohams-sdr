#!/usr/bin/env python3
"""init.js loads the two receiver skins with the station calibration and no longer forces Rig."""
import os
import re

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'files', 'htdocs', 'plugins', 'receiver')
init = open(os.path.join(R, 'init.js'), encoding='utf-8').read()

assert 'RIG_POR_DEFECTO' not in init and 'bh_rig_default' not in init, 'Rig must no longer be forced by default'
lista = re.search(r"for \(const name of \[(.*?)\]\)", init, re.S).group(1)
nombres = re.findall(r"'([a-z0-9_]+)'", lista)
for skin in ('bh_skin_bricofx', 'bh_skin_militar'):
    assert skin in nombres, skin + ' must be loaded'
    assert nombres.index(skin) < nombres.index('bricohams'), skin + ' must load before bricohams (selector and default)'
    assert re.search(r"window\.%s_config\s*=\s*\{\s*smeter:\s*\{\s*offset_hf:\s*7,\s*offset_vhf:\s*-50,\s*iaru_vhf:\s*true\s*\}" % skin, init), \
        skin + ' must use the station S-meter calibration'
for d in ('bh_skin_bricofx', 'bh_skin_militar'):
    for f in (d + '.js', d + '.css'):
        assert os.path.isfile(os.path.join(R, d, f)), d + '/' + f
print('Receiver skins init.js: PASS')
