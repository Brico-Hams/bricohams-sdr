#!/usr/bin/env python3
"""v5.1: moderador del chat de bricohams-visitas. Reglas (inyección, enlaces,
palabras vetadas, avalancha, repetidos, longitud), umbral con olvido, línea
«BAN ip=» que lee Fail2ban, aviso Telegram con IP parcial y LAN nunca moderada."""
import importlib.machinery
import importlib.util
import os
import re
import tempfile

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
loader = importlib.machinery.SourceFileLoader('vis', os.path.join(RAIZ, 'files/bin/bricohams-visitas.py'))
spec = importlib.util.spec_from_loader('vis', loader)
vis = importlib.util.module_from_spec(spec)
loader.exec_module(vis)

FILTRO = re.compile(r'^\S+ BAN ip=(?P<host>\S+) motivo=')     # = failregex del jail bricohams-chat

d = tempfile.mkdtemp()
log = os.path.join(d, 'sub', 'moderador.log')
reloj = [1_790_000_000.0]
avisos = []


def nuevo(**kw):
    base = dict(ahora=lambda: reloj[0], log_path=log, tg=avisos.append, max_msg=6, ventana=30,
                umbral=10, max_len=300, enlaces='no', palabras=['spamword'])
    base.update(kw)
    return vis.ModeradorChat(**base)


def bans():
    if not os.path.exists(log):
        return []
    return [l for l in open(log, encoding='utf-8') if ' BAN ' in l]


m = nuevo()
# Mensajes normales
assert m.revisar('83.45.12.7', 'EA5XYZ', 'Hola, 73 desde Murcia') == (True, '')
# LAN / loopback / sin IP / IP inválida: nunca se moderan
for ip in ('192.168.1.5', '127.0.0.1', '10.0.0.1', '', 'nope', '::1'):
    assert m.revisar(ip, 'x', '<script>alert(1)</script>')[0], ip
assert bans() == []

# Inyección: bloqueo inmediato (10 puntos)
ok, motivo = m.revisar('151.20.1.1', 'malo', '<img src=x onerror=alert(1)>')
assert not ok and 'inyeccion' in motivo
assert len(bans()) == 1 and FILTRO.match(bans()[0]).group('host') == '151.20.1.1'
assert '151.20.x.x' in avisos[-1] and '151.20.1.1' not in avisos[-1], 'Telegram solo con IP parcial'
# Ya baneada: se descarta sin repetir BAN
assert m.revisar('151.20.1.1', 'malo', 'hola') == (False, 'baneada')
assert len(bans()) == 1

# Enlace: se descarta pero no banea a la primera (3 < 10)
ok, motivo = m.revisar('8.8.4.4', 'sp', 'visita www.ejemplo.com')
assert not ok and motivo == 'enlace' and len(bans()) == 1
# Palabra vetada + enlace acumulan -> 3+4+3 = 10 -> BAN
m.revisar('8.8.4.4', 'sp', 'compra spamword')
ok, motivo = m.revisar('8.8.4.4', 'sp', 'https://x.top')
assert not ok and len(bans()) == 2 and 'ip=8.8.4.4 ' in bans()[-1]

# Olvido: 1 punto por minuto
m2 = nuevo()
m2.revisar('1.1.1.1', 'a', 'www.a.com')      # 3
reloj[0] += 600                               # 10 min -> 0
for i in range(3):
    m2.revisar('1.1.1.1', 'a', 'www.a%d.com' % i)   # 3 cada uno -> 9 < 10
assert not any('ip=1.1.1.1 ' in l for l in bans())

# Avalancha: más de 6 mensajes en 30 s (y repetidos)
m3 = nuevo()
res = [m3.revisar('9.9.9.9', 'f', 'msg %d' % i) for i in range(7)]
assert all(r[0] for r in res[:6]) and not res[6][0] and res[6][1] == 'avalancha'
# Repetido 3 veces
m4 = nuevo()
r = [m4.revisar('4.4.4.4', 'r', 'CQ CQ') for _ in range(3)]
assert r[0][0] and r[1][0] and r[2] == (False, 'repetido')
# Largo
assert nuevo().revisar('5.5.5.5', 'l', 'x' * 301) == (False, 'largo')
# Enlaces permitidos
assert nuevo(enlaces='yes').revisar('6.6.6.6', 'e', 'mira https://qrz.com')[0]

# Palabras desde fichero
pf = os.path.join(d, 'palabras.txt')
open(pf, 'w', encoding='utf-8').write('# comentario\nFoo\nbar baz\n')
assert vis.cargar_palabras('@' + pf) == ['foo', 'bar baz']
assert vis.cargar_palabras('a, B ,') == ['a', 'b'] and vis.cargar_palabras('@/no/existe') == []

# Integración con Visitas: el mensaje bloqueado no llega a Telegram
class GeoFalsa:
    def buscar(self, ip):
        return {'cc': 'ES', 'pais': 'España', 'ciudad': ''}


os.environ['VISITAS_CHAT'] = 'yes'
tg = []
v = vis.Visitas(vis.abrir_db(os.path.join(d, 'v.sqlite')), GeoFalsa(), tg.append, ahora=lambda: reloj[0],
                moderador=nuevo(tg=None))
v.evento({'state': 'ChatMessage', 'ip': '77.1.2.3', 'name': 'ok', 'message': 'buenas'})
v.evento({'state': 'ChatMessage', 'ip': '77.1.2.4', 'name': 'bad', 'message': '<script>x</script>'})
v.evento({'state': 'ChatMessage', 'name': 'APRS', 'message': 'sin ip'})   # APRS: sin IP, no se modera
assert len(tg) == 2 and 'buenas' in tg[0] and 'sin ip' in tg[1], tg
assert vis.ultimos_bloqueos(log)[-1].endswith('motivo=inyeccion')
print('OK test_chat_moderador: reglas, umbral con olvido, BAN para Fail2ban, IP parcial en Telegram y LAN exenta')
