#!/usr/bin/env python3
"""Genera y fusiona marcadores de OpenWebRX:

 1. Repetidores de la zona EA5 desde la lista de EA5KGV (data/repetidores_EA5KGV_zonaEA5.csv).
    OpenWebRX no tiene campo de subtono en los marcadores (solo nombre, frecuencia,
    modulación, descripción y «escaneable»), y para ESCUCHAR un repetidor el subtono
    no hace falta: se sintoniza su SALIDA. Por eso la entrada y el subtono (el que hay
    que transmitir para abrirlo) van en la descripción, que sale al pasar el ratón.
 2. Emisora destacada de FM comercial (Wifon FM 97,5) con estrella, la primera.

Uso:  python3 tools/marcadores.py          (actualiza files/openwebrx/bookmarks.json)
      python3 tools/marcadores.py --dry    (solo muestra lo que haría)
"""
import csv
import json
import os
import sys

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
BM = os.path.join(RAIZ, 'files', 'openwebrx', 'bookmarks.json')
CSV = os.path.join(RAIZ, 'data', 'repetidores_EA5KGV_zonaEA5.csv')

FM_DESTACADA = {'name': '⭐ 97.5 Wifon FM', 'frequency': 97500000, 'modulation': 'wfm', 'scannable': True,
                'description': 'Wifon FM · Murcia · la emisora destacada de BricoHams'}

CIUDADES = {'ED5YAP': 'Valencia', 'ED5YAT': 'Águilas', 'ED5YAG': 'Alicante', 'ED5YAW': 'Albacete',
            'ED5YAK': 'Sierra Espuña', 'ED5YAL': 'Sierra Espuña', 'ED5YBF': 'Carrascoy'}


def mhz(f):
    return ('%.4f' % (f / 1e6)).rstrip('0').rstrip('.').replace('.', ',')


def canal(f_out):
    """Nombre del canal IARU R1 por la salida (2 m: R0 = 145,600; 70 cm: RU-70 = 438,650)."""
    if 145.5875e6 <= f_out <= 145.7875e6:
        n = round((f_out - 145.6e6) / 12500)
        return 'R%d%s' % (n // 2, 'X' if n % 2 else '')
    if 438.6e6 <= f_out <= 439.45e6:
        return 'RU-%d' % round(70 + (f_out - 438.65e6) / 25000)
    return ''


def leer_csv():
    filas = []
    for r in csv.DictReader(open(CSV, encoding='utf-8')):
        nombre = r['name'].strip()
        if nombre[:1].isdigit():            # el prefijo numérico de la lista es el distrito
            nombre = nombre[1:]
        ind = nombre.split()[0]
        f_rx = round(float(r['rxFrequency']) * 1e6)
        f_tx = round(float(r['txFrequency']) * 1e6) if r['txFrequency'] else None
        # en la lista hay subtonos solo en rxTone: son el de transmitir (columnas cruzadas en origen)
        tono = r['txTone'] if r['txTone'] not in ('', 'OFF') else (r['rxTone'] if r['rxTone'] not in ('', 'OFF') else None)
        if any(f['ind'] == ind and f['f_out'] == f_rx for f in filas):
            continue                        # la lista repite algunos repetidores (selección nacional + distrito)
        filas.append({'ind': ind, 'ciudad': CIUDADES.get(ind, ''), 'f_out': f_rx, 'f_in': f_tx, 'tono': tono, 'slot': r['slot']})
    return filas


def marcador(r):
    simplex = r['f_in'] in (None, r['f_out'])
    can = canal(r['f_out'])
    nombre = '🔁 %s%s%s' % ((can + ' ') if can else '', r['ind'], (' ' + r['ciudad']) if r['ciudad'] else '')
    if simplex:
        nombre = '🔁 %s (simplex)' % r['ind']
    partes = []
    if not simplex:
        partes.append('Entrada %s MHz (%s MHz)' % (mhz(r['f_in']), ('%+.1f' % ((r['f_in'] - r['f_out']) / 1e6)).replace('.', ',')))
    partes.append(('Subtono %s Hz para abrirlo (para escuchar no hace falta)' % r['tono'].replace('.', ',')) if r['tono'] else 'Sin subtono')
    partes.append('lista EA5KGV, posición %s' % r['slot'])
    return {'name': nombre, 'frequency': r['f_out'], 'modulation': 'nfm', 'scannable': True, 'description': ' · '.join(partes)}


def fusionar(bm, filas):
    """Añade un marcador por salida de repetidor. Si ya hay uno en esa frecuencia
    (otra lista o un repetidor que comparte canal), se anota en su descripción."""
    por_f = {}
    for b in bm:
        por_f.setdefault(b['frequency'], []).append(b)
    añadidos = anotados = 0
    for r in filas:
        n = marcador(r)
        existentes = [b for b in por_f.get(n['frequency'], []) if b.get('modulation') != 'wfm']
        if not existentes:
            bm.append(n)
            por_f.setdefault(n['frequency'], []).append(n)
            añadidos += 1
            continue
        b = existentes[0]
        if r['ind'] in b['name'] and 'lista EA5KGV' in b.get('description', ''):
            continue                        # ya es el marcador generado (se puede repetir sin duplicar)
        quien = r['ind'] if r['ind'] in b['name'] else 'también %s%s' % (r['ind'], (' ' + r['ciudad']) if r['ciudad'] else '')
        extra = '[EA5KGV %s: %s]' % (quien, n['description'].replace(' · lista EA5KGV, posición %s' % r['slot'], ''))
        if extra not in b.get('description', ''):
            b['description'] = (b.get('description', '') + ' ' if b.get('description') else '') + extra
            anotados += 1
    return añadidos, anotados


def fm_destacada(bm):
    bm[:] = [b for b in bm if b['frequency'] != FM_DESTACADA['frequency'] or b.get('modulation') != 'wfm']
    bm.insert(0, dict(FM_DESTACADA))


def main():
    bm = json.load(open(BM, encoding='utf-8'))
    antes = len(bm)
    a, n = fusionar(bm, leer_csv())
    fm_destacada(bm)
    print('marcadores: %d → %d (repetidores nuevos %d, anotados %d, Wifon FM destacada)' % (antes, len(bm), a, n))
    if '--comprobar' in sys.argv:   # prueba: el fichero ya está al día (idempotente) y Wifon va primera
        assert a == 0 and n == 0 and len(bm) == antes, 'bookmarks.json no está al día: ejecuta tools/marcadores.py'
        assert json.load(open(BM, encoding='utf-8'))[0]['frequency'] == FM_DESTACADA['frequency'], 'Wifon FM no es la primera'
        print('OK marcadores: al día e idempotente, Wifon FM la primera')
        return
    if '--dry' not in sys.argv:
        json.dump(bm, open(BM, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
