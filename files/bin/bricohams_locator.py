#!/usr/bin/env python3
"""Locator Maidenhead ⇄ coordenadas (v4.3).

  bricohams_locator.py IM98iu            → «38.854167 -1.291667» (centro de la cuadrícula)
  bricohams_locator.py --a-locator 37.9838 -1.1280   → «IM97KX»
  bricohams_locator.py --espana IM98iu   → sale con 0 si cae en España (península, Baleares,
                                           Canarias, Ceuta o Melilla) y con 3 si no

Funciones para los demás scripts: locator_to_latlon, latlon_to_locator, celda (límites de la
cuadrícula), dentro_de_celda y en_espana.
"""
import sys

ANCHOS = ((20.0, 10.0), (2.0, 1.0), (1 / 12, 1 / 24), (1 / 120, 1 / 240), (1 / 2880, 1 / 5760))
LETRAS_CAMPO = 'ABCDEFGHIJKLMNOPQR'
LETRAS = 'ABCDEFGHIJKLMNOPQRSTUVWX'

# Cajas generosas de España (sur, oeste, norte, este). Portugal, el sur de Francia, Andorra y
# Gibraltar caen dentro de la de la península: se descartan con sus cajas (aproximadas, solo
# sirven para avisar de un locator mal escrito, nunca para parar la instalación).
ESPANA = {
    'península': (35.95, -9.40, 43.85, 3.40),
    'Baleares': (38.55, 1.10, 40.15, 4.40),
    'Canarias': (27.55, -18.25, 29.50, -13.30),
    'Ceuta': (35.85, -5.40, 35.93, -5.25),
    'Melilla': (35.25, -2.99, 35.33, -2.91),
}
# Portugal por franjas de latitud: (sur, oeste, norte, este) con el este en la frontera aproximada
PORTUGAL = [(36.90, -9.60, 37.55, -7.44), (37.55, -9.60, 38.20, -7.30), (38.20, -9.60, 38.75, -7.15),
            (38.75, -9.60, 39.25, -7.05), (39.25, -9.60, 39.70, -7.33), (39.70, -9.60, 40.30, -6.95),
            (40.30, -9.60, 41.05, -6.83), (41.05, -9.60, 41.45, -6.45), (41.45, -9.60, 41.65, -6.20),
            (41.65, -9.60, 41.95, -6.55), (41.95, -9.60, 42.03, -8.20)]
# Francia al norte del Pirineo, Andorra y Gibraltar (también dentro de la caja de la península)
OTROS_PAISES = [(43.32, -1.76, 43.90, 3.40), (42.95, -1.35, 43.32, 3.40), (42.88, -1.00, 42.95, 3.40),
                (42.47, 1.80, 42.88, 3.40), (42.42, 1.40, 42.66, 1.79), (36.10, -5.37, 36.16, -5.33)]


def locator_to_latlon(locator):
    """Centro de la cuadrícula de un locator de 4, 6, 8 o 10 caracteres."""
    s, o, n, e = celda(locator)
    return round((s + n) / 2, 6), round((o + e) / 2, 6)


def celda(locator):
    """(sur, oeste, norte, este) de la cuadrícula."""
    locator = str(locator).strip().upper()
    if len(locator) not in (4, 6, 8, 10):
        raise ValueError('Maidenhead locator must contain 4, 6, 8, or 10 characters')
    longitude, latitude = -180.0, -90.0
    for pair_index in range(len(locator) // 2):
        longitude_width, latitude_width = ANCHOS[pair_index]
        first, second = locator[pair_index * 2], locator[pair_index * 2 + 1]
        if pair_index in (0, 2, 4):
            alphabet = LETRAS_CAMPO if pair_index == 0 else LETRAS
            if first not in alphabet or second not in alphabet:
                raise ValueError('Invalid Maidenhead field/subsquare: %s' % locator)
            longitude += alphabet.index(first) * longitude_width
            latitude += alphabet.index(second) * latitude_width
        else:
            if not first.isdigit() or not second.isdigit():
                raise ValueError('Invalid Maidenhead square: %s' % locator)
            longitude += int(first) * longitude_width
            latitude += int(second) * latitude_width
    return latitude, longitude, latitude + latitude_width, longitude + longitude_width


def latlon_to_locator(lat, lon, largo=6):
    """Locator (4, 6, 8 o 10 caracteres) de unas coordenadas."""
    if largo not in (4, 6, 8, 10):
        raise ValueError('largo debe ser 4, 6, 8 o 10')
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError('coordenadas fuera de rango')
    lon_r, lat_r = min(lon + 180, 359.9999999), min(lat + 90, 179.9999999)
    out = ''
    for i in range(largo // 2):
        w_lon, w_lat = ANCHOS[i]
        a, b = int(lon_r // w_lon), int(lat_r // w_lat)
        lon_r -= a * w_lon
        lat_r -= b * w_lat
        if i in (0, 2, 4):
            alf = LETRAS_CAMPO if i == 0 else LETRAS
            out += alf[a] + alf[b] if i == 0 else (alf[a] + alf[b]).lower()
        else:
            out += '%d%d' % (a, b)
    return out


def dentro_de_celda(locator, lat, lon, margen_km=0.0):
    s, o, n, e = celda(locator)
    m_lat = margen_km / 111.0
    return s - m_lat <= lat <= n + m_lat and o - m_lat * 1.3 <= lon <= e + m_lat * 1.3


def en_espana(lat, lon):
    """Nombre de la zona de España en la que caen las coordenadas, o None."""
    for nombre, (s, o, n, e) in ESPANA.items():
        if s <= lat <= n and o <= lon <= e:
            if nombre == 'península' and any(ps <= lat <= pn and po <= lon <= pe for ps, po, pn, pe in PORTUGAL + OTROS_PAISES):
                continue
            return nombre
    return None


if __name__ == '__main__':
    args = sys.argv[1:]
    try:
        if len(args) == 3 and args[0] == '--a-locator':
            print(latlon_to_locator(float(args[1]), float(args[2])))
        elif len(args) == 2 and args[0] == '--espana':
            lat, lon = locator_to_latlon(args[1])
            zona = en_espana(lat, lon)
            print(zona or 'fuera de España')
            sys.exit(0 if zona else 3)
        elif len(args) == 1:
            lat, lon = locator_to_latlon(args[0])
            print('%.6f %.6f' % (lat, lon))
        else:
            sys.exit('uso: bricohams_locator.py <locator> | --a-locator LAT LON | --espana <locator>')
    except ValueError as error:
        sys.exit(str(error))
