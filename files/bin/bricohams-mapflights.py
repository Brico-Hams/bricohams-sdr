#!/usr/bin/env python3
# BricoHams: alimenta map.flights desde readsb (además de RadarBox).
# Añade, cambia o quita en NET_OPTIONS de /etc/default/readsb el conector
#   --net-connector=feed.map.flights,30004,beast_reduce_plus_out,uuid=<UUID>
# sin tocar el resto de opciones. Sin UUID, quita el conector.
# Uso: bricohams-mapflights.py /etc/default/readsb [UUID] [HOST] [PUERTO]
#      bricohams-mapflights.py --uuid UUID   (solo valida y normaliza)
# El UUID es una etiqueta de estación, no una contraseña, pero map.flights
# pide no publicarlo: el script nunca lo imprime entero.
import re
import shlex
import sys

HOST = 'feed.map.flights'
PUERTO = '30004'
PROTOCOLO = 'beast_reduce_plus_out'


def uuid_valido(u):
    """UUID de map.flights normalizado (8-4-4-4-12, minúsculas) o None."""
    h = (u or '').strip().lower().replace('-', '')
    if not re.fullmatch(r'[0-9a-f]{32}', h):
        return None
    return '%s-%s-%s-%s-%s' % (h[:8], h[8:12], h[12:16], h[16:20], h[20:])


def es_mapflights(op, host):
    m = re.match(r'--net-connector[= ](.*)', op)
    return bool(m) and m.group(1).split(',')[0].strip().lower() in (HOST, host.lower())


def aplicar(texto, uuid, host=HOST, puerto=PUERTO):
    """Devuelve el contenido de /etc/default/readsb con el conector puesto (o quitado si uuid es None)."""
    lineas = texto.splitlines()
    hecho = False
    for i, linea in enumerate(lineas):
        m = re.match(r'^(\s*NET_OPTIONS=)(.*)$', linea)
        if not m:
            continue
        try:
            ops = shlex.split(m.group(2))
            ops = ops[0].split() if len(ops) == 1 else ops
        except ValueError:
            ops = m.group(2).strip('"\'').split()
        # «--net-connector X» en dos palabras: se junta para poder reconocerlo
        juntas = []
        for op in ops:
            if juntas and juntas[-1] == '--net-connector':
                juntas[-1] = '--net-connector=' + op
            else:
                juntas.append(op)
        ops = [op for op in juntas if not es_mapflights(op, host)]
        if uuid:
            ops.append('--net-connector=%s,%s,%s,uuid=%s' % (host, puerto, PROTOCOLO, uuid))
        lineas[i] = '%s"%s"' % (m.group(1), ' '.join(ops))
        hecho = True
    if not hecho:
        base = '--net --net-heartbeat 60 --net-ro-size 1250 --net-ro-interval 0.05 --net-ri-port 0 ' \
               '--net-ro-port 30002 --net-sbs-port 30003 --net-bi-port 30004,30104 --net-bo-port 30005'
        lineas.append('NET_OPTIONS="%s"' % base)
        return aplicar('\n'.join(lineas) + '\n', uuid, host, puerto)
    return '\n'.join(lineas) + '\n'


def main(argv):
    if len(argv) >= 2 and argv[0] == '--uuid':
        u = uuid_valido(argv[1])
        if not u:
            return 1
        print(u)
        return 0
    if not argv:
        print(__doc__ or 'uso: bricohams-mapflights.py /etc/default/readsb [UUID] [HOST] [PUERTO]', file=sys.stderr)
        return 2
    ruta = argv[0]
    crudo = argv[1] if len(argv) > 1 else ''
    host = argv[2] if len(argv) > 2 and argv[2] else HOST
    puerto = argv[3] if len(argv) > 3 and argv[3] else PUERTO
    uuid = None
    if crudo:
        uuid = uuid_valido(crudo)
        if not uuid:
            print('map.flights: el UUID no es válido (32 cifras hexadecimales, con o sin guiones)', file=sys.stderr)
            return 1
    if not re.fullmatch(r'[A-Za-z0-9.-]+', host) or not re.fullmatch(r'[0-9]{1,5}', puerto):
        print('map.flights: host o puerto no válidos', file=sys.stderr)
        return 1
    with open(ruta) as fh:
        antes = fh.read()
    despues = aplicar(antes, uuid, host, puerto)
    if despues != antes:
        with open(ruta, 'w') as fh:
            fh.write(despues)
    if uuid:
        print('readsb: conector Beast a %s:%s (%s, uuid=%s…)' % (host, puerto, PROTOCOLO, uuid[:8]))
    else:
        print('readsb: sin conector a map.flights')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
