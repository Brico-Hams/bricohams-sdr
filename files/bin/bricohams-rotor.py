#!/usr/bin/env python3
# =====================================================================
#  bricohams-rotor · BricoHams
#  Apunta el rotor AZ/EL PortableSatLite (ESP32, repo antenaSatCommrotor)
#  a los pases que graba bricohams-satrec:
#   - usa el mismo plan que satrec (pases.json, SATREC_MIN_EL, exclusiones);
#   - antes del AOS lleva la antena al azimut de entrada y durante el pase
#     manda az/el verdaderos (SGP4) por la Wi-Fi de casa (/api/goto_true);
#   - los METEOR (137 MHz) no se siguen: salen por la QFH fija;
#   - fuera de pase, o con racha ≥ ROTOR_VIENTO_MAX_KMH en meteo.json,
#     aparca la antena en ROTOR_PARQUE_AZ/EL.
#  La clave del rotor (16+ caracteres, la misma que se pone desde el punto
#  de acceso del ESP32 con /api/key) va en ROTOR_CLAVE_FICHERO; nunca en el
#  registro ni en la URL.
#  Uso: bricohams-rotor   (servicio bricohams-rotor)
# =====================================================================
import importlib.machinery
import importlib.util
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime


def _modulo(nombre, ruta):
    loader = importlib.machinery.SourceFileLoader(nombre, ruta)
    spec = importlib.util.spec_from_loader(nombre, loader)
    m = importlib.util.module_from_spec(spec)
    loader.exec_module(m)
    return m


def cfg_desde_env(sr, env=os.environ):
    c = sr.cfg_desde_env(env)
    c.update({
        'url': env.get('ROTOR_URL', '').rstrip('/'),
        'clave_rotor': env.get('ROTOR_CLAVE_FICHERO', '/etc/bricohams/rotor.clave'),
        'meteo': env.get('METEO_JSON', os.path.join(sr.HTDOCS, 'plugins/receiver/meteo/meteo.json')),
        'viento_max': float(env.get('ROTOR_VIENTO_MAX_KMH', '36')),      # 10 m/s: límite de MECHANICAL.md
        'parque': (float(env.get('ROTOR_PARQUE_AZ', '0')), float(env.get('ROTOR_PARQUE_EL', '90'))),
        'antes': int(env.get('ROTOR_ANTES_S', '120')),
    })
    return c


def leer_clave(ruta):
    try:
        return open(ruta, encoding='utf-8').read().strip()
    except OSError:
        return ''


def http_post(url, campos, timeout=5):
    datos = urllib.parse.urlencode(campos).encode()
    with urllib.request.urlopen(urllib.request.Request(url, data=datos), timeout=timeout) as r:
        return r.status, r.read().decode('utf-8', 'replace')


class Rotor:
    def __init__(self, cfg, sr, sp, post=http_post, reloj=time.time):
        self.cfg, self.sr, self.sp, self.post, self.reloj = cfg, sr, sp, post, reloj
        self.obs = sp.ecef_observador(cfg['lat'], cfg['lon'], cfg['asl'])
        self.ultimo = None          # último (az, el) enviado
        self.estado = ''
        self.aparcado_viento = False
        self.sats = {}

    def avisar(self, estado):
        if estado != self.estado:
            self.estado = estado
            print('rotor: %s' % estado, flush=True)

    def viento(self, ahora):
        """Racha en km/h, o None si no hay meteo.json; ValueError si el dato es viejo."""
        try:
            j = json.load(open(self.cfg['meteo'], encoding='utf-8'))
        except FileNotFoundError:
            return None
        except (OSError, ValueError):
            raise ValueError('meteo.json ilegible')
        t = datetime.fromisoformat(str(j.get('updated', '')).replace('Z', '+00:00')).timestamp()
        if ahora - t > 3 * 3600:
            raise ValueError('meteo.json de hace más de 3 h')
        cur = (j.get('model') or {}).get('current') or {}
        v = cur.get('wind_gusts_10m', cur.get('wind_speed_10m'))
        if v is None:
            raise ValueError('meteo.json sin viento')
        return float(v)

    def pase_actual(self, ahora):
        try:
            pases = json.load(open(self.cfg['pases'], encoding='utf-8')).get('pases', [])
        except (OSError, ValueError):
            return None
        for p in self.sr.plan(pases, self.cfg, ahora):
            if p['accion'] == 'grabar' and p.get('omm') and p['aos'] - self.cfg['antes'] <= ahora <= p['los']:
                return p
        return None

    def az_el(self, p, ts):
        n = p['norad']
        if n not in self.sats:
            self.sats[n] = self.sp.satrec_de_omm(p['omm'])
        r, jd = self.sp.posicion(self.sats[n], ts)
        return self.sp.az_el(r, jd, self.cfg['lat'], self.cfg['lon'], self.obs) if r else None

    def mover(self, az, el):
        el = min(max(el, 0.0), 90.0)
        if self.ultimo and abs(self.ultimo[0] - az) < 0.5 and abs(self.ultimo[1] - el) < 0.5:
            return
        estado, texto = self.post(self.cfg['url'] + '/api/goto_true',
                                  {'az': '%.1f' % az, 'el': '%.1f' % el, 'key': leer_clave(self.cfg['clave_rotor'])})
        if estado != 200:
            raise OSError('rotor respondió %s: %s' % (estado, texto[:80]))
        self.ultimo = (az, el)

    def paso(self):
        ahora = self.reloj()
        try:
            v = self.viento(ahora)
        except ValueError as e:
            v, motivo = None, str(e)
            self.aparcado_viento = True
        else:
            motivo = 'racha %.0f km/h' % v if v is not None else ''
            if v is not None and v >= self.cfg['viento_max']:
                self.aparcado_viento = True
            elif v is None or v < 0.8 * self.cfg['viento_max']:         # histéresis para no cabecear con racheo
                self.aparcado_viento = False
        p = None if self.aparcado_viento else self.pase_actual(ahora)
        if p:
            ae = self.az_el(p, max(ahora, p['aos']))
            if ae:
                az, el = ae
                self.mover(az, el)
                self.avisar('siguiendo %s' % p['nombre'] if ahora >= p['aos'] else 'esperando el AOS de %s' % p['nombre'])
                return
        self.mover(*self.cfg['parque'])
        self.avisar('aparcado (%s)' % motivo if self.aparcado_viento else 'aparcado, sin pase')


def main(argv):
    sr = _modulo('bh_satrec', os.environ.get('SATREC_PY', '/usr/local/bin/bricohams-satrec'))
    cfg = cfg_desde_env(sr)
    if not cfg['url']:
        print('rotor: falta ROTOR_URL (p. ej. http://satlite.local)', file=sys.stderr)
        return 2
    if len(leer_clave(cfg['clave_rotor'])) < 16:
        print('rotor: falta la clave en %s (16+ caracteres, la misma de /api/key)' % cfg['clave_rotor'], file=sys.stderr)
        return 2
    r = Rotor(cfg, sr, sr._satpass())
    while True:
        try:
            r.paso()
        except Exception as e:                       # rotor apagado o sin red: se reintenta
            r.ultimo = None
            r.avisar('error: %s' % e)
        time.sleep(2)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
