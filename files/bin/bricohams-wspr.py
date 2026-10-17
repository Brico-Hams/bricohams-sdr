#!/usr/bin/env python3
# =====================================================================
#  bricohams-wspr · BricoHams  (v5.0)
#  Las balizas WSPR/FST4W las decodifica OpenWebRX+ (servicio de fondo del
#  receptor de HF) y él mismo las reporta a WSPRnet. Este programa comprueba
#  que el reporte está activo y baja de wspr.live lo que la estación ha
#  reportado en las últimas 24 h para enseñarlo en «Clima en red».
#  Salida: plugins/receiver/meteo/wspr.json   (temporizador cada 15 min)
#  Uso: bricohams-wspr          · bricohams-wspr --ver
# =====================================================================
import json
import os
import re
import sys
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone

WSPR_LIVE = 'https://db1.wspr.live/?query='
BANDAS = [(0.13, 0.14, '2200m'), (0.47, 0.48, '630m'), (1.8, 2.0, '160m'), (3.5, 4.0, '80m'), (5.2, 5.5, '60m'),
          (7.0, 7.3, '40m'), (10.1, 10.15, '30m'), (14.0, 14.35, '20m'), (18.06, 18.17, '17m'), (21.0, 21.45, '15m'),
          (24.89, 24.99, '12m'), (28.0, 29.7, '10m'), (50.0, 54.0, '6m'), (70.0, 70.5, '4m'), (144.0, 146.0, '2m')]


def banda(hz):
    mhz = (hz or 0) / 1e6
    return next((n for a, b, n in BANDAS if a <= mhz <= b), '%.3f MHz' % mhz)


def ajustes_owrx(ruta):
    """Solo las claves de WSPRnet (settings.json lleva secretos: no se copia nada más)."""
    try:
        s = json.load(open(ruta, encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    return {'reporta': bool(s.get('wsprnet_enabled')), 'indicativo': str(s.get('wsprnet_callsign') or '').upper()}


def consulta(indicativo, horas=24, limite=300):
    if not re.match(r'^[A-Z0-9/]{3,12}$', indicativo):
        raise ValueError('indicativo no válido: %r' % indicativo)
    return ("SELECT time, frequency, tx_sign, tx_loc, distance, azimuth, snr, power FROM wspr.rx "
            "WHERE rx_sign = '%s' AND time > now() - INTERVAL %d HOUR ORDER BY time DESC LIMIT %d FORMAT JSON"
            % (indicativo, int(horas), int(limite)))


def resumen(filas, indicativo, owrx):
    bandas = {}
    for f in filas:
        bandas[banda(f.get('frequency'))] = bandas.get(banda(f.get('frequency')), 0) + 1
    lejano = max(filas, key=lambda f: f.get('distance') or 0) if filas else None

    def corto(f):
        return {'t': f['time'] + 'Z', 'banda': banda(f.get('frequency')), 'mhz': round(f['frequency'] / 1e6, 6),
                'call': f['tx_sign'], 'loc': f.get('tx_loc', ''), 'km': f.get('distance'),
                'snr': f.get('snr'), 'dbm': f.get('power')}
    return {'actualizado': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'indicativo': indicativo, 'reporta': owrx.get('reporta'),
            'spots_24h': len(filas), 'estaciones': len({f['tx_sign'] for f in filas}),
            'bandas': dict(sorted(bandas.items(), key=lambda kv: -kv[1])),
            'mas_lejano': corto(lejano) if lejano else None,
            'ultimos': [corto(f) for f in filas[:40]],
            'enlace': 'https://wspr.rocks/livequeue/?rx=' + urllib.parse.quote(indicativo)}


def write_atomic(path, obj):
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix='.wspr-')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False)
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


def main(argv):
    owrx = ajustes_owrx(os.environ.get('OWRX_SETTINGS_FILE', '/var/lib/openwebrx/settings.json'))
    indicativo = (os.environ.get('WSPR_CALLSIGN') or owrx.get('indicativo') or os.environ.get('CALLSIGN') or '').upper()
    salida = os.environ.get('WSPR_OUT', '/usr/lib/python3/dist-packages/htdocs/plugins/receiver/meteo/wspr.json')
    base = os.environ.get('WSPR_LIVE_URL', WSPR_LIVE)
    if not indicativo or indicativo == 'N0CALL':
        print('wspr: sin indicativo (WSPR_CALLSIGN o wsprnet_callsign en OpenWebRX+)', file=sys.stderr)
        return 1
    try:
        req = urllib.request.Request(base + urllib.parse.quote(consulta(indicativo)),
                                     headers={'User-Agent': 'BricoHams-SDR wspr 1.0'})
        filas = json.load(urllib.request.urlopen(req, timeout=30)).get('data', [])
    except Exception as e:
        print('wspr: wspr.live: %s' % e, file=sys.stderr)
        return 2
    r = resumen(filas, indicativo, owrx)
    if '--ver' in argv:
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0
    write_atomic(salida, r)
    aviso = '' if owrx.get('reporta', True) else ' · ¡OJO! OpenWebRX+ no tiene activado el reporte a WSPRnet'
    print('wspr: %s · %d escuchas en 24 h (%d estaciones)%s' % (indicativo, r['spots_24h'], r['estaciones'], aviso))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
