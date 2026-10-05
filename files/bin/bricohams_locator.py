#!/usr/bin/env python3
"""Convert Maidenhead locators to the center coordinates of their cell."""
import sys


def locator_to_latlon(locator):
    locator = str(locator).strip().upper()
    if len(locator) not in (4, 6, 8, 10):
        raise ValueError('Maidenhead locator must contain 4, 6, 8, or 10 characters')

    longitude = -180.0
    latitude = -90.0
    widths = ((20.0, 10.0), (2.0, 1.0), (1 / 12, 1 / 24),
              (1 / 120, 1 / 240), (1 / 2880, 1 / 5760))
    for pair_index in range(len(locator) // 2):
        longitude_width, latitude_width = widths[pair_index]
        first = locator[pair_index * 2]
        second = locator[pair_index * 2 + 1]
        if pair_index in (0, 2, 4):
            alphabet = 'ABCDEFGHIJKLMNOPQR' if pair_index == 0 else 'ABCDEFGHIJKLMNOPQRSTUVWX'
            if first not in alphabet or second not in alphabet:
                raise ValueError('Invalid Maidenhead field/subsquare: %s' % locator)
            longitude += alphabet.index(first) * longitude_width
            latitude += alphabet.index(second) * latitude_width
        else:
            if not first.isdigit() or not second.isdigit():
                raise ValueError('Invalid Maidenhead square: %s' % locator)
            longitude += int(first) * longitude_width
            latitude += int(second) * latitude_width

    longitude += longitude_width / 2
    latitude += latitude_width / 2
    return round(latitude, 6), round(longitude, 6)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('uso: bricohams_locator.py <locator>')
    try:
        lat, lon = locator_to_latlon(sys.argv[1])
    except ValueError as error:
        sys.exit(str(error))
    print('%.6f %.6f' % (lat, lon))