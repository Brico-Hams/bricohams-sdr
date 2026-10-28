#!/usr/bin/env python3
# =====================================================================
#  bricohams-render-settings · BricoHams
#  Rellena settings.json.tmpl con los valores de bricohams.env
#  (variables de entorno) y escribe settings.json para OpenWebRX+.
#  Uso: bricohams-render-settings.py plantilla.json salida.json
# =====================================================================
import json
import os
import sys
from bricohams_locator import locator_to_latlon


def env(k, d=''):
    return os.environ.get(k, d).strip()


def as_bool(v):
    return str(v).strip().lower() in ('1', 'yes', 'si', 'sí', 'true', 'on')


def main(src, dst):
    callsign = env('CALLSIGN', 'N0CALL').upper()
    station_lat = float(env('STATION_LAT', '0.0'))
    station_lon = float(env('STATION_LON', '0.0'))
    if env('STATION_LOCATOR') and not (station_lat or station_lon):    # v4.3 · las coordenadas, si están, mandan
        station_lat, station_lon = locator_to_latlon(env('STATION_LOCATOR'))
    # v4.4 · la posición del receptor es PÚBLICA (mapa, /status.json, directorios de receptores):
    # se redondea (2 decimales ≈ 1 km) para no publicar la casa. Vacío o «exacta» = sin redondear.
    decimales = env('OWRX_GPS_DECIMALES', '2')
    if decimales.isdigit():
        station_lat, station_lon = round(station_lat, int(decimales)), round(station_lon, int(decimales))
    station_country = env('STATION_COUNTRY', 'ES').upper()
    if len(station_country) != 2 or not station_country.isascii() or not station_country.isalpha():
        sys.exit('STATION_COUNTRY debe ser un código ISO de dos letras')
    aprs_passcode = env('APRS_PASSCODE')
    aprs_igate_option = env('APRS_IGATE_ENABLE')
    aprs_igate_enabled = as_bool(aprs_igate_option) if aprs_igate_option else bool(
        aprs_passcode and callsign and callsign != 'N0CALL')
    if aprs_igate_enabled and (not aprs_passcode or not callsign or callsign == 'N0CALL'):
        sys.exit('APRS_IGATE_ENABLE requiere CALLSIGN propio y APRS_PASSCODE configurado')

    vals = {
        '__CALLSIGN__': callsign,
        '__STATION_QTH__': env('STATION_QTH', ''),
        '__STATION_COUNTRY__': station_country,
        '__RECEIVER_NAME__': '%s · SDR MULTIUSUARIO' % callsign,
        '__RECEIVER_LOCATION__': '%s, %s' % (env('STATION_QTH', ''), station_country),
        '__RECEIVER_COUNTRY__': station_country,
        '__PHOTO_TITLE__': '%s · Receptor SDR' % callsign,
        '__PHOTO_DESC__': 'Receptor SDR multiusuario de %s en %s (%s).' % (
            callsign, env('STATION_QTH', ''), station_country),
        '__APRS_IGATE_ENABLED__': aprs_igate_enabled,
        '__MAGIC_KEY__': env('MAGIC_KEY'),
        '__RECEIVERBOOK_KEY__': env('RECEIVERBOOK_KEY'),
        '__OPENWEATHERMAP_KEY__': env('OPENWEATHERMAP_KEY'),
        '__APRS_PASSCODE__': env('APRS_PASSCODE'),
        '__ADMIN_EMAIL__': env('ADMIN_EMAIL'),
        '__LAT__': station_lat,
        '__LON__': station_lon,
        '__ASL__': int(float(env('STATION_ASL', '200'))),
        '__SERIAL_HAT__': env('SERIAL_HAT', '00000101'),
        '__SERIAL_MINI__': env('SERIAL_MINI', '00000102'),
        '__SERIAL_V3__': env('SERIAL_V3', '00000103'),
        '__HF_SDRPLAY__': as_bool(env('HF_SDRPLAY', 'no')),
        '__SAT_BIAS_TEE__': as_bool(env('SAT_BIAS_TEE', 'no')),
        '__SDRPLAY_ANTENNA__': env('SDRPLAY_ANTENNA'),
        '__HF_HERMES__': as_bool(env('HF_HERMES', 'no')),
        '__HERMES_IP__': env('HERMES_IP'),
        '__HERMES_GAIN__': int(env('HERMES_GAIN', '20') or 20),
        '__MQTT_ENABLED__': as_bool(env('VISITAS_ENABLE', 'yes')) or as_bool(env('OWRX_MAPA_LORA', 'yes')),   # visitas (v4) y mapa LoRa/Meshtastic (v4.5)
    }

    def walk(o):
        if isinstance(o, dict):
            for k in list(o.keys()):
                v = o[k]
                if isinstance(v, str) and v in vals:
                    nv = vals[v]
                    if k in ('antenna', 'remote') and nv == '':      # remote vacío: el HL2 se busca por difusión
                        del o[k]          # RSP1A/RSP1B: sin selector de antena
                        continue
                    o[k] = nv
                else:
                    walk(v)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                if isinstance(v, str) and v in vals:
                    o[i] = vals[v]
                else:
                    walk(v)
        return o

    data = walk(json.load(open(src, encoding='utf-8')))
    # HF: en el V3 (muestreo directo) hasta que llegue el SDRplay; con HF_SDRPLAY=yes pasa al SDRplay
    sdrplay = vals['__HF_SDRPLAY__']
    hermes = vals['__HF_HERMES__']
    for sdr in data['sdrs'].values():
        for pid in list(sdr.get('profiles', {})):
            prof = sdr['profiles'][pid]
            if prof.pop('_bh_hf_rtl', False) and (sdrplay or hermes):
                del sdr['profiles'][pid]
    if not env('RECEIVERBOOK_KEY'):
        data['receiver_keys'] = []
    left = [m for m in vals if m in json.dumps(data)] + (['_bh_hf_rtl'] if '_bh_hf_rtl' in json.dumps(data) else [])
    if left:
        sys.exit('Marcadores sin rellenar: %s' % ', '.join(left))
    with open(dst, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print('settings.json: %d receptores (%d activos), %d perfiles; HF en %s' % (
        len(data['sdrs']), sum(1 for s in data['sdrs'].values() if s.get('enabled', True)),
        sum(len(s.get('profiles', {})) for s in data['sdrs'].values()), ' + '.join(n for n, x in (('SDRplay', sdrplay), ('Hermes Lite 2', hermes)) if x) or 'RTL-SDR V3'))


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit('uso: %s plantilla.json salida.json' % sys.argv[0])
    main(sys.argv[1], sys.argv[2])
