#!/usr/bin/env python3
# BricoHams: deja /etc/rbfeeder.ini leyendo la salida Beast de readsb
# (127.0.0.1:30005) con la posición de la antena y MLAT activado,
# conservando la clave de compartición que ya tenga.
# Uso: bricohams-rbfeeder-ini.py /etc/rbfeeder.ini LAT LON ALT_ANTENA_M
import configparser
import sys

f, lat, lon, alt = sys.argv[1:5]
c = configparser.ConfigParser(strict=False, interpolation=None)
c.optionxform = str
c.read(f)
for sec in ('client', 'network', 'mlat'):
    if not c.has_section(sec):
        c.add_section(sec)
c['client'].update({'network_mode': 'true', 'lat': lat, 'lon': lon, 'alt': alt})
c['network'].update({'mode': 'beast', 'external_host': '127.0.0.1', 'external_port': '30005'})
c['mlat'].update({'autostart_mlat': 'true'})
with open(f, 'w') as fh:
    c.write(fh)
print('rbfeeder.ini: red Beast 127.0.0.1:30005, %s %s %s m, MLAT activado' % (lat, lon, alt))
