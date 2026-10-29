#!/usr/bin/env python3
"""v4: genera docs/CANALES_Y_FRECUENCIAS.md a partir de data/marcadores_v4.json y de
los repetidores de files/openwebrx/bookmarks.json. Uso: python3 tools/canales.py"""
import json
import os
from collections import OrderedDict

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
V4 = json.load(open(os.path.join(RAIZ, 'data', 'marcadores_v4.json'), encoding='utf-8'))['marcadores']
BM = json.load(open(os.path.join(RAIZ, 'files', 'openwebrx', 'bookmarks.json'), encoding='utf-8'))
MOD = {'nfm': 'FM', 'am': 'AM', 'wfm': 'FM ancha', 'usb': 'USB', 'lsb': 'LSB', 'cw': 'CW', 'dab': 'DAB+', 'dmr': 'DMR',
       'ysf': 'YSF', 'ft8': 'FT8', 'ft4': 'FT4', 'wspr': 'WSPR', 'js8': 'JS8', 'packet': 'APRS 1200'}


def mhz(f):
    return ('%.5f' % f).rstrip('0').rstrip('.').replace('.', ',')


def limpio(t):
    return ''.join(ch for ch in t if ord(ch) < 0x2600 or ch in '·–—').strip().replace('|', '/')


L = ['# Canales y frecuencias de la estación', '',
     'Generado por `tools/canales.py` a partir de `data/marcadores_v4.json` y `files/openwebrx/bookmarks.json`.',
     'Todo está como marcador en la web: pulsa encima para sintonizar. En los repetidores, la entrada y el subtono van en',
     'la descripción (OpenWebRX no tiene campo de subtono y para escuchar no hace falta).', '',
     '> **No se incluyen comunicaciones privadas:** ni radiotaxis, ni TETRA de emergencias o policía, ni servicios de',
     '> seguridad. En España escucharlas o difundirlas puede vulnerar el secreto de las comunicaciones (Ley 11/2022 General',
     '> de Telecomunicaciones), y un receptor público en Internet las estaría retransmitiendo. El perfil «TETRA 420–422,4»',
     '> sigue disponible solo como exploración de la banda.', '']
grupos = OrderedDict()
for e in V4:
    grupos.setdefault(e['grupo'], []).append(e)
for g, es in grupos.items():
    L += ['## %s' % g, '', '| MHz | Nombre | Modo | Notas |', '|---|---|---|---|']
    for e in sorted(es, key=lambda x: x['mhz']):
        L.append('| %s | %s | %s | %s |' % (mhz(e['mhz']), limpio(e['name']), MOD.get(e['modulation'], e['modulation']),
                                            limpio(e['description'])))
    fuentes = sorted({e['fuente'] for e in es if e.get('fuente', '').startswith('http')})
    if fuentes:
        L += ['', 'Fuente: ' + ' · '.join(fuentes)]
    L.append('')
rep = sorted([b for b in BM if b['name'].startswith(('🔁', '🟢', '🏛️ RU'))], key=lambda b: b['frequency'])
L += ['## Repetidores (zona EA5)', '', '| Salida MHz | Nombre | Entrada y subtono |', '|---|---|---|']
for b in rep:
    L.append('| %s | %s | %s |' % (mhz(b['frequency'] / 1e6), limpio(b['name']), limpio(b.get('description', ''))))
L += ['', '## Puertos de la Región de Murcia (VHF marina)', '',
      '- **Cartagena:** escucha permanente en el **16**. Los prácticos y las operaciones portuarias usan el 12, 13 y 14 (perfil «⛵ VHF Marina»).',
      '  La estación costera Cartagena Radio está en el **65** dúplex (bajada 160,875, perfil «⚓ Costeras»).',
      '  Salvamento Marítimo da los boletines meteorológicos en el **10**.',
      '- **Mazarrón:** el puerto deportivo trabaja en el **9**.',
      '- **AIS** (161,975 y 162,025): las posiciones de los barcos salen en el mapa de OpenWebRX+.', '',
      '## Aeropuertos', '',
      '- **Región de Murcia (LEMI, Corvera):** torre 121,325 y rodadura 121,750. Aproximación San Javier 130,300.',
      '- **San Javier (LELC, AGA):** torre 124,425, rodadura 121,600, ATIS 128,605.',
      '- **Alicante (LEAL):** torre 118,150, autorizaciones 119,850, rodadura 130,650, ATIS 120,075; Valencia Control 118,800 / 120,400.',
      '- Las frecuencias de 8,33 kHz se dan como portadora real; el AIP las publica como «canal» (121,330 → 121,325).', '']
open(os.path.join(RAIZ, 'docs', 'CANALES_Y_FRECUENCIAS.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('docs/CANALES_Y_FRECUENCIAS.md: %d líneas' % len(L))
