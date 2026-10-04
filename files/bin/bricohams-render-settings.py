#!/usr/bin/env python3
# =====================================================================
#  bricohams-render-settings · EA5KAO · BricoHams
#  Rellena settings.json.tmpl con los valores de bricohams.env
#  (variables de entorno) y escribe settings.json para OpenWebRX+.
#  Uso: bricohams-render-settings.py plantilla.json salida.json
# =====================================================================
import json
import os
import sys


def env(k, d=''):
    return os.environ.get(k, d).strip()


def as_bool(v):
    return str(v).strip().lower() in ('1', 'yes', 'si', 'sí', 'true', 'on')


def main(src, dst):
    vals = {
        '__MAGIC_KEY__': env('MAGIC_KEY'),
        '__RECEIVERBOOK_KEY__': env('RECEIVERBOOK_KEY'),
        '__OPENWEATHERMAP_KEY__': env('OPENWEATHERMAP_KEY'),
        '__APRS_PASSCODE__': env('APRS_PASSCODE'),
        '__ADMIN_EMAIL__': env('ADMIN_EMAIL'),
        '__LAT__': float(env('STATION_LAT', '0.0')),
        '__LON__': float(env('STATION_LON', '0.0')),
        '__ASL__': int(float(env('STATION_ASL', '200'))),
        '__SERIAL_HAT__': env('SERIAL_HAT', '00000101'),
        '__SERIAL_MINI__': env('SERIAL_MINI', '00000102'),
        '__SERIAL_V3__': env('SERIAL_V3', '00000103'),
        '__HF_SDRPLAY__': as_bool(env('HF_SDRPLAY', 'no')),
        '__SAT_BIAS_TEE__': as_bool(env('SAT_BIAS_TEE', 'no')),
        '__SDRPLAY_ANTENNA__': env('SDRPLAY_ANTENNA'),
        '__MQTT_ENABLED__': as_bool(env('VISITAS_ENABLE', 'yes')),   # v4: avisos de conexión (bricohams-visitas)
    }

    def walk(o):
        if isinstance(o, dict):
            for k in list(o.keys()):
                v = o[k]
                if isinstance(v, str) and v in vals:
                    nv = vals[v]
                    if k == 'antenna' and nv == '':
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
    for sdr in data['sdrs'].values():
        for pid in list(sdr.get('profiles', {})):
            prof = sdr['profiles'][pid]
            if prof.pop('_bh_hf_rtl', False) and sdrplay:
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
        sum(len(s.get('profiles', {})) for s in data['sdrs'].values()), 'SDRplay' if sdrplay else 'RTL-SDR V3'))


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit('uso: %s plantilla.json salida.json' % sys.argv[0])
    main(sys.argv[1], sys.argv[2])
