#!/usr/bin/env python3
"""v4: bricohams-visitas. IP parcial, GeoIP (simulada), avisos de Telegram con
límite por IP, chat, desconexión, resumen para la web (sin IPs) y que la IP
completa NO llega nunca a la base de datos."""
import importlib.machinery
import importlib.util
import json
import os
import tempfile

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
loader = importlib.machinery.SourceFileLoader('vis', os.path.join(RAIZ, 'files/bin/bricohams-visitas.py'))
spec = importlib.util.spec_from_loader('vis', loader)
vis = importlib.util.module_from_spec(spec)
loader.exec_module(vis)

assert vis.ip_parcial('83.45.12.7') == '83.45.x.x'
assert vis.ip_parcial('2a01:4f8:1:2::3') == '2a01:4f8:…'
assert vis.bandera('ES') == '🇪🇸' and vis.bandera('') == '🏳️'


class GeoFalsa:
    def buscar(self, ip):
        if ip.startswith('192.168.'):
            return {'cc': 'LAN', 'pais': 'Red local', 'ciudad': ''}
        return {'83.': {'cc': 'ES', 'pais': 'España', 'ciudad': 'Murcia'},
                '151': {'cc': 'IT', 'pais': 'Italia', 'ciudad': 'Roma'}}.get(ip[:3], {'cc': 'US', 'pais': 'Estados Unidos', 'ciudad': ''})


mensajes = []
reloj = [1_790_000_000.0]
d = tempfile.mkdtemp()
db = vis.abrir_db(os.path.join(d, 'v.sqlite'))
os.environ['VISITAS_CHAT'] = 'yes'
v = vis.Visitas(db, GeoFalsa(), mensajes.append, ahora=lambda: reloj[0])

v.evento({'mode': 'CLIENT', 'state': 'Connected', 'ip': '83.45.12.7', 'clients': 1})
v.evento({'mode': 'CLIENT', 'state': 'Connected', 'ip': '151.20.1.1', 'clients': 2})
v.evento({'mode': 'CLIENT', 'state': 'Connected', 'ip': '192.168.1.50', 'clients': 3})      # LAN: sin aviso
reloj[0] += 60
v.evento({'mode': 'CLIENT', 'state': 'Disconnected', 'ip': '83.45.12.7', 'clients': 2})
v.evento({'mode': 'CLIENT', 'state': 'Connected', 'ip': '83.45.12.7', 'clients': 3})       # reconexión: sin 2.º aviso
v.evento({'mode': 'CLIENT', 'state': 'ChatMessage', 'ip': '151.20.1.1', 'name': 'IU1ABC', 'message': 'hola <b>'})
assert len(mensajes) == 3, mensajes
assert 'Murcia, España' in mensajes[0] and '83.45.x.x' in mensajes[0] and '🇪🇸' in mensajes[0]
assert 'Roma' in mensajes[1] and 'IU1ABC' in mensajes[2] and '&lt;b&gt;' in mensajes[2]
v.evento({'mode': 'CLIENT', 'state': 'ChatMessage', 'name': 'N0CALL (Telegram)', 'message': 'respuesta',
          'telegram_bridge': True})
assert len(mensajes) == 3, 'la respuesta de Telegram no debe generar un eco de vuelta a Telegram'

r = v.resumen()
assert r['ahora'] == 3 and r['hoy'] == 4 and r['total'] == 4, r
assert r['paises_ahora'] == ['ES', 'IT'], r['paises_ahora']
assert {p['cc']: p['n'] for p in r['paises_30d']} == {'ES': 2, 'IT': 1, 'LAN': 1}
web = json.dumps(r)
assert '83.45' not in web and '151.20' not in web, 'la web no debe llevar IPs'

filas = db.execute('SELECT ip, cc, fin FROM visitas').fetchall()
volcado = json.dumps(filas) + open(os.path.join(d, 'v.sqlite'), 'rb').read().decode('latin-1')
assert '83.45.12.7' not in volcado and '151.20.1.1' not in volcado, 'la IP completa no se guarda'
assert any(f[0] == '83.45.x.x' and f[2] is not None for f in filas), 'la desconexión cierra la visita'

reloj[0] += 100 * 86400
v.limpiar(90)
assert db.execute('SELECT COUNT(*) FROM visitas').fetchone()[0] == 0
assert db.execute('SELECT SUM(n) FROM diario').fetchone()[0] == 4      # el contador por días se conserva
print('OK test_visitas: IP parcial, avisos (1 por IP / 10 min), chat, resumen sin IPs y limpieza a 90 días')
