#!/usr/bin/env python3
# Une marcadores de OpenWebRX (clave: frecuencia + modo).
#
#  Restaurar una copia (instalación con --backup):
#    bricohams-merge-bookmarks.py copia.json kit.json salida.json
#    → todos los de la copia + los del kit que no estén en ella.
#
#  Actualizar (v4.1, paso «configuracion» con marcadores ya puestos):
#    bricohams-merge-bookmarks.py --tres kit_anterior.json actuales.json kit_nuevo.json salida.json
#    → los del kit nuevo (ganan: así llegan las correcciones de nombre o tono)
#      + los «propios»: los actuales que no venían en el kit anterior (añadidos desde la web).
#    Si no existe kit_anterior.json (estaciones de antes de la v4.1), son propios los
#    actuales que no están en el kit nuevo.
import json
import os
import sys


def clave(b):
    return (b.get('frequency'), b.get('modulation'))


def leer(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def escribir(datos, p):
    tmp = p + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)
    os.replace(tmp, p)


def restaurar(copia, kit):
    have = {clave(b) for b in copia}
    added = [b for b in kit if clave(b) not in have]
    return copia + added, len(copia), len(added)


def tres_vias(anterior, actuales, nuevo):
    """Devuelve (resultado, n_kit, n_propios)."""
    ref = {clave(b) for b in (anterior if anterior is not None else nuevo)}
    claves_nuevo = {clave(b) for b in nuevo}
    propios, vistos = [], set()
    for b in actuales:
        k = clave(b)
        if k in ref or k in claves_nuevo or k in vistos:
            continue
        vistos.add(k)
        propios.append(b)
    return nuevo + propios, len(nuevo), len(propios)


def main(a):
    if a and a[0] == '--tres':
        if len(a) != 5:
            sys.exit('uso: bricohams-merge-bookmarks.py --tres kit_anterior.json actuales.json kit_nuevo.json salida.json')
        anterior = leer(a[1]) if os.path.exists(a[1]) else None
        res, n_kit, n_propios = tres_vias(anterior, leer(a[2]), leer(a[3]))
        escribir(res, a[4])
        print('marcadores: %d del kit + %d propios (añadidos desde la web)%s' % (
            n_kit, n_propios, '' if anterior is not None else ' · primera vez: sin kit anterior de referencia'))
        return 0
    if len(a) != 3:
        sys.exit('uso: bricohams-merge-bookmarks.py copia.json kit.json salida.json')
    res, n_copia, n_nuevos = restaurar(leer(a[0]), leer(a[1]))
    escribir(res, a[2])
    print('marcadores: %d de la copia + %d nuevos del kit' % (n_copia, n_nuevos))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
