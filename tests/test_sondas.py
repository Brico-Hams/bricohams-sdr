#!/usr/bin/env python3
"""v5.6: módulo de radiosondas (ADR-72): puente UDP -> sondas.json/MQTT, predicción y station.cfg de auto_rx."""
import importlib.machinery
import importlib.util
import json
import os
import socket
import struct
import sys
import tempfile
import threading

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
loader = importlib.machinery.SourceFileLoader('sondas', os.path.join(RAIZ, 'files/bin/bricohams-sondas.py'))
spec = importlib.util.spec_from_loader('sondas', loader)
s = importlib.util.module_from_spec(spec)
loader.exec_module(s)


def paquete(**kw):
    d = {'type': 'PAYLOAD_SUMMARY', 'station': 'EA7XXX', 'callsign': 'S4530123', 'latitude': 38.0,
         'longitude': -1.17, 'altitude': 1200.5, 'speed': 36.0, 'heading': 270.0, 'time': '12:00:00',
         'model': 'M10', 'freq': 403.4, 'temp': 12.5, 'frame': 100, 'datetime': '2026-01-01T12:00:00Z',
         'vel_v': 5.1, 'humidity': 40.0, 'sats': 9, 'batt': 3.2, 'snr': 12.0}
    d.update(kw)
    return json.dumps(d)


# --- validación ---------------------------------------------------------
p, motivo = s.validar_paquete(paquete())
assert motivo is None and p['serie'] == 'S4530123' and p['alt'] == 1200.5 and p['freq'] == 403.4, p
assert p['vel_v'] == 5.1 and p['sats'] == 9 and p['modelo'] == 'M10'
assert s.validar_paquete(paquete().encode())[0] == p
# freq de auto_rx: cadena «403.400 MHz», número en MHz o en Hz
for f_in in ('403.400 MHz', 403.4, 403400000, '403.4', 403400000.0):
    assert s.validar_paquete(paquete(freq=f_in))[0]['freq'] == 403.4, f_in
for f_in in ('mucho MHz', '1.5 MHz', 1.5, 900000000, True, None, [403.4], '403.4 kHz'):
    assert s.validar_paquete(paquete(freq=f_in))[0]['freq'] is None, f_in
# un paquete mínimo vale; los opcionales absurdos se ignoran sin tumbar el paquete
p2, _ = s.validar_paquete(paquete(temp=9999, humidity='x', vel_v=None))
assert p2 is not None and p2['temp'] is None and p2['humedad'] is None and p2['vel_v'] is None

malos = [
    'no es json', '', '[1,2,3]', '"texto"', 'null', '{"callsign":',
    paquete(callsign='../../etc/passwd'), paquete(callsign='ab'), paquete(callsign='A' * 21),
    paquete(callsign='S1;rm -rf /'), paquete(callsign='<script>'), paquete(callsign=None), paquete(callsign=123),
    paquete(latitude=91), paquete(latitude=-90.0001), paquete(longitude=181), paquete(longitude='1'),
    paquete(latitude=True), paquete(altitude=50001), paquete(altitude=-501), paquete(altitude=None),
    paquete(altitude=False), paquete(frame=True), paquete(frame=-1), paquete(frame=1.5), paquete(frame='1'),
    paquete(type='OTRO'),
    '{"type":"PAYLOAD_SUMMARY","callsign":"S1234","latitude":NaN,"longitude":1,"altitude":1}',
    '{"type":"PAYLOAD_SUMMARY","callsign":"S1234","latitude":Infinity,"longitude":1,"altitude":1}',
    '[' * 5000,
]
for m in malos:
    assert s.validar_paquete(m)[0] is None, m
assert s.validar_paquete(b'\xff\xfe\x00')[0] is None
assert s.validar_paquete(b'{"x":"' + b'A' * (s.MAX_PAQUETE + 1) + b'"}')[0] is None
sucio, _ = s.validar_paquete(paquete(model='<img src=x onerror=1>' + 'A' * 100, datetime='\x00\x1b[31m' + 'x' * 100))
assert len(sucio['modelo']) <= 24 and len(sucio['datetime']) <= 40 and '\x00' not in sucio['datetime']
assert s.main(['x', '--paquete', paquete()]) == 0 and s.main(['x', '--paquete', 'basura']) == 1

# --- duplicados, traza y reventón ---------------------------------------
seg = s.Seguimiento(prediccion=False)
assert seg.procesar(paquete(frame=1), 1000) is not None
assert seg.procesar(paquete(frame=1), 1001) is None          # misma serie+frame
assert seg.procesar(paquete(frame=1, callsign='S9999999'), 1001) is not None   # otra serie
assert seg.procesar('basura', 1002) is None and seg.descartados == 2
for i in range(2, 32):
    seg.procesar(paquete(frame=i, altitude=1000 + 500 * i, vel_v=5.0), 1000 + i)
assert seg.sondas['S4530123']['burst'] is None
seg.procesar(paquete(frame=40, altitude=31000, vel_v=0.2), 1040)
seg.procesar(paquete(frame=41, altitude=30500, vel_v=-0.5), 1041)   # ruido: aún no es reventón
assert seg.sondas['S4530123']['burst'] is None
seg.procesar(paquete(frame=42, altitude=29000, vel_v=-30.0), 1042)
b = seg.sondas['S4530123']['burst']
assert b and b['alt'] == 31000.0, b
seg.procesar(paquete(frame=43, altitude=20000, vel_v=-40.0), 1043)
assert seg.sondas['S4530123']['burst']['alt'] == 31000.0
# traza acotada
corto = s.Seguimiento(prediccion=False)
for i in range(s.MAX_PUNTOS + 50):
    corto.procesar(paquete(frame=i, altitude=500), 2000 + i)
assert len(corto.sondas['S4530123']['traza']) == s.MAX_PUNTOS

# --- caducidad -----------------------------------------------------------
seg.expirar(1043 + s.CADUCA_S - 1)
assert 'S4530123' in seg.sondas
seg.expirar(1043 + s.CADUCA_S + 1)
assert 'S4530123' not in seg.sondas and not seg.sondas.get('S9999999')

# --- JSON atómico, persistencia y secretos ------------------------------
with tempfile.TemporaryDirectory() as t:
    estado = os.path.join(t, 'estado', 'estado.json')
    salida = os.path.join(t, 'meteo', 'sondas.json')
    seg = s.Seguimiento(estado, prediccion=False)
    seg.procesar(paquete(frame=1), 5000)
    cfg = {'mqtt': True, 'mqtt_host': '127.0.0.1', 'mqtt_puerto': 1883, 'mqtt_tema': 'bricohams/sondas',
           'mqtt_user': 'usuario-secreto', 'mqtt_pass': 'clave-secreta'}
    doc = seg.documento(s.mqtt_publico(cfg, True), 5001)
    s.escribir_atomico(salida, doc)
    seg.guardar()
    assert sorted(os.listdir(os.path.dirname(salida))) == ['sondas.json'], 'queda un temporal'
    assert oct(os.stat(salida).st_mode & 0o777) == oct(0o644) or os.name == 'nt'
    crudo = open(salida, encoding='utf-8').read()
    assert 'secreto' not in crudo and 'usuario' not in crudo and 'pass' not in crudo.lower().replace('passwd', '')
    d = json.loads(crudo)
    assert d['mqtt'] == {'activo': True, 'host': '127.0.0.1', 'puerto': 1883, 'tema': 'bricohams/sondas',
                         'conectado': True}
    assert d['sitio']['id'] == '08430' and d['sondas'][0]['serie'] == 'S4530123' and d['sondas'][0]['activa']
    assert d['proximo_lanzamiento'] % 43200 == 0 and d['proximo_lanzamiento'] > 5001
    assert 'recientes' not in d['sondas'][0]
    if os.name != 'nt':
        assert oct(os.stat(estado).st_mode & 0o777) == oct(0o600)
    # reinicio: se conserva la traza; lo caducado o corrupto se descarta
    nuevo = s.Seguimiento(estado, prediccion=False)
    nuevo.cargar(5100)
    assert len(nuevo.sondas['S4530123']['traza']) == 1 and nuevo.sondas['S4530123']['alt'] == 1200.5
    viejo = s.Seguimiento(estado, prediccion=False)
    viejo.cargar(5000 + s.CADUCA_S + 5)
    assert not viejo.sondas
    with open(estado, 'w') as f:
        f.write('{"../x": 1, "S4530123": {"visto": 5000, "traza": [[999, 0, 0, 0]], "lat": 1, "lon": 1, "alt": 1}')
    roto = s.Seguimiento(estado, prediccion=False)
    roto.cargar(5100)
    assert not roto.sondas
    with open(estado, 'w') as f:
        f.write('{"../x": {"visto": 5000}, "S4530123": {"visto": 5000, "traza": [[999, 0, 0, 0]], "lat": 1, "lon": 1, "alt": 1}}')
    roto.cargar(5100)
    assert not roto.sondas

# --- MQTT con editor falso ----------------------------------------------
class Falso:
    def __init__(self):
        self.enviado = []

    def publicar(self, tema, datos, retener=False):
        self.enviado.append((tema, datos, retener))
        return True


falso = Falso()
seg = s.Seguimiento(prediccion=True, fetcher=lambda serie: [], publicador=falso, tema='bricohams/sondas')
assert seg.temas('S4530123') == {'telemetria': 'bricohams/sondas/S4530123/telemetria',
                                 'aterrizaje': 'bricohams/sondas/S4530123/aterrizaje',
                                 'estado': 'bricohams/sondas/estado'}
sonda = seg.procesar(paquete(frame=7), 7000)
seg.publicar_telemetria(sonda)
tema, datos, retener = falso.enviado[-1]
assert tema == 'bricohams/sondas/S4530123/telemetria' and retener is True
assert datos['serie'] == 'S4530123' and 'traza' not in datos and 'recientes' not in datos
assert '+' not in tema and '#' not in tema

# --- predicción: limitada y validada -----------------------------------
llamadas = []
respuesta = [{'vehicle': 'S4530123', 'time': 1700000000, 'data': json.dumps(
    [{'time': 1, 'lat': 38.1, 'lon': -1.0, 'alt': 20000}, {'time': 2, 'lat': 38.3, 'lon': -0.8, 'alt': 100}])}]


def fetcher(serie):
    llamadas.append(serie)
    return respuesta


falso = Falso()
seg = s.Seguimiento(prediccion=True, fetcher=fetcher, publicador=falso)
seg.procesar(paquete(frame=1), 1000)
assert seg.actualizar_predicciones(1000) == 1 and llamadas == ['S4530123']
pred = seg.sondas['S4530123']['prediccion']
assert pred['lat'] == 38.3 and pred['lon'] == -0.8 and pred['alt'] == 100.0 and len(pred['ruta']) == 2
assert falso.enviado[-1][0].endswith('/S4530123/aterrizaje') and falso.enviado[-1][2] is True
assert seg.actualizar_predicciones(1100) == 0                 # < 5 min
assert seg.actualizar_predicciones(1299) == 0
assert seg.actualizar_predicciones(1301) == 0                 # >5 min pero sin señal: inactiva
seg.procesar(paquete(frame=2), 1295)
assert seg.actualizar_predicciones(1301) == 1 and len(llamadas) == 2
fallos = []


def roto_fetch(serie):
    fallos.append(serie)
    raise OSError('sin red')


seg2 = s.Seguimiento(prediccion=True, fetcher=roto_fetch)
seg2.procesar(paquete(frame=1), 1000)
assert seg2.actualizar_predicciones(1000) == 1 and seg2.sondas['S4530123']['prediccion'] is None
assert seg2.actualizar_predicciones(1010) == 0                # un fallo también espera 5 min
apagada = s.Seguimiento(prediccion=False, fetcher=fetcher)
apagada.procesar(paquete(frame=1), 1000)
assert apagada.actualizar_predicciones(1000) == 0 and len(llamadas) == 2
for malo in ([{'vehicle': 'OTRA', 'data': '[]'}], [{'vehicle': 'S4530123', 'data': 'no json'}], 'x', None,
             [{'vehicle': 'S4530123', 'data': [{'lat': 91, 'lon': 0, 'alt': 0}]}],
             [{'vehicle': 'S4530123', 'data': [{'lat': 1, 'lon': 0, 'alt': 1e9}]}], [1, 2]):
    assert s.validar_prediccion(malo, 'S4530123') is None, malo
assert s.AGENTE.startswith('BricoHams') and s.PREDICCION_CADA_S == 300
assert s.siguiente_lanzamiento(0) == 43200 and s.siguiente_lanzamiento(43199) == 43200
assert s.siguiente_lanzamiento(43200) == 86400

# --- station.cfg ---------------------------------------------------------
env = {'SONDAS_SDR_SERIAL': 'RTL-0042', 'SONDAS_MIN_FREQ': '400.05', 'SONDAS_MAX_FREQ': '406.0',
       'SONDAS_ALWAYS_SCAN': '403.4,401.5', 'SONDAS_PPM': '3', 'SONDAS_GAIN': '-1', 'SONDAS_SONDEHUB': 'no',
       'STATION_LAT': '38.0', 'STATION_LON': '-1.1', 'STATION_ASL': '100', 'CALLSIGN': 'EA7XXX'}
PLANTILLA_TXT = """# plantilla de ejemplo (como station.cfg.example de auto_rx)
[sdr]
sdr_type = RTLSDR
sdr_quantity = 2

[sdr_1]
device_idx = 0
ppm = 0
gain = 30.0
bias = True

[search_params]
min_freq = 400.0
max_freq = 403.0
always_scan = []
never_scan = []
only_scan = []
rx_timeout = 120

[location]
station_lat = 0.0
station_lon = 0.0
station_alt = 0.0

[habitat]
uploader_callsign = CHANGEME

[sondehub]
sondehub_enabled = True

[aprs]
aprs_enabled = True

[email]
email_enabled = True

[rotator]
rotator_enabled = False

[oziplotter]
payload_summary_enabled = False
payload_summary_host = 192.168.1.5
payload_summary_port = 55672

[advanced]
synchronous_upload = True
Max_Peaks = 10

[filtering]
max_altitude = 50000
archive_age = 120

[logging]
per_sonde_log = True

[web]
web_host = 0.0.0.0
web_port = 5000
web_control = True
archive_age = 120
"""
_tmp_plantilla = tempfile.TemporaryDirectory()
PLANTILLA = os.path.join(_tmp_plantilla.name, 'station.cfg.example')
with open(PLANTILLA, 'w') as f:
    f.write(PLANTILLA_TXT)
cfg = s.generar_station_cfg(PLANTILLA, env)
lineas = cfg.splitlines()
for linea in ('[sdr]', 'sdr_type = RTLSDR', 'sdr_quantity = 1', 'device_idx = RTL-0042', 'ppm = 3', 'gain = -1',
              'min_freq = 400.050', 'max_freq = 406.000', 'always_scan = [403.400, 401.500]',
              'station_lat = 38.00000', 'station_alt = 100', 'uploader_callsign = EA7XXX',
              'sondehub_enabled = False', 'payload_summary_enabled = True', 'payload_summary_host = 127.0.0.1',
              'payload_summary_port = 55673', 'web_host = 127.0.0.1', 'web_port = 5000', 'web_control = False',
              'aprs_enabled = False', 'email_enabled = False',
              # claves de la plantilla que no tocamos (y con mayúsculas) se conservan
              '[advanced]', 'synchronous_upload = True', 'Max_Peaks = 10', '[filtering]', 'max_altitude = 50000',
              'archive_age = 120', '[logging]', 'per_sonde_log = True', '[rotator]', 'rotator_enabled = False'):
    assert linea in lineas, linea
assert 'web_host = 0.0.0.0' not in cfg and cfg.count('[web]') == 1
assert 'sondehub_enabled = True' in s.generar_station_cfg(PLANTILLA, dict(env, SONDAS_SONDEHUB='yes')).splitlines()
assert '[web]\nweb_host' in cfg
with tempfile.TemporaryDirectory() as t:
    for nombre, texto in (('sin-sdr', '[search_params]\nmin_freq = 400\n[web]\nweb_port = 1\n'),
                          ('sin-search', '[sdr]\nsdr_type = RTLSDR\n[web]\nweb_port = 1\n'),
                          ('sin-web', '[sdr]\nsdr_type = RTLSDR\n[search_params]\nmin_freq = 400\n'),
                          ('vacia', ''), ('basura', 'esto no es ini')):
        ruta = os.path.join(t, nombre)
        with open(ruta, 'w') as f:
            f.write(texto)
        try:
            s.generar_station_cfg(ruta, env)
        except ValueError:
            pass
        else:
            raise AssertionError('plantilla %s aceptada' % nombre)
    try:
        s.generar_station_cfg(os.path.join(t, 'no-existe'), env)
    except ValueError as exc:
        assert 'plantilla' in str(exc)
    else:
        raise AssertionError('plantilla inexistente aceptada')
    assert s.main(['x', '--station-cfg', os.path.join(t, 'no-existe')]) == 2
    assert s.main(['x', '--station-cfg']) == 2
for cambio in ({'SONDAS_SDR_SERIAL': ''}, {'SONDAS_SDR_SERIAL': 'a b'}, {'SONDAS_SDR_SERIAL': 'x\n[web]'},
               {'SONDAS_MIN_FREQ': '399'}, {'SONDAS_MAX_FREQ': '407'}, {'SONDAS_MIN_FREQ': '405', 'SONDAS_MAX_FREQ': '404'},
               {'SONDAS_MIN_FREQ': 'nan'}, {'SONDAS_ALWAYS_SCAN': '300'}, {'SONDAS_ALWAYS_SCAN': 'x'},
               {'SONDAS_PPM': '500'}, {'SONDAS_GAIN': '99'}, {'STATION_LAT': '95'}, {'STATION_LON': 'abc'}):
    try:
        s.generar_station_cfg(PLANTILLA, dict(env, **cambio))
    except ValueError:
        pass
    else:
        raise AssertionError('station.cfg acepta %r' % cambio)
inyeccion = s.generar_station_cfg(PLANTILLA, dict(env, CALLSIGN='EA7;\n[web]\nweb_host=0.0.0.0'))
assert inyeccion.count('[web]') == 1 and inyeccion.count('web_host') == 1 and 'web_host = 127.0.0.1' in inyeccion
sin_asl = dict(env)
del sin_asl['STATION_ASL']
assert 'station_alt = 0' in s.generar_station_cfg(PLANTILLA, sin_asl)

# --- configuración y credenciales ---------------------------------------
with tempfile.TemporaryDirectory() as t:
    fcred = os.path.join(t, 'sondas.env')
    with open(fcred, 'w') as f:
        f.write("SONDAS_MQTT_USER='usu'\nSONDAS_MQTT_PASS='a'\\''b'\n")
    c = s.cfg_desde_env({'SONDAS_ENV_FILE': fcred, 'SONDAS_MQTT': 'yes', 'SONDAS_MQTT_PORT': 'x',
                         'SONDAS_MQTT_TOPIC': '/bricohams/sondas/'})
    assert c['mqtt_user'] == 'usu' and c['mqtt_pass'] == "a'b" and c['mqtt_puerto'] == 1883
    assert c['mqtt'] and c['mqtt_tema'] == 'bricohams/sondas' and c['prediccion']
    assert 'usu' not in json.dumps(s.mqtt_publico(c))
    off = s.cfg_desde_env({})
    assert not off['mqtt'] and s.mqtt_publico(off)['host'] is None and off['mqtt_user'] == ''
    assert s.leer_credenciales(os.path.join(t, 'no-existe')) == {}

# --- bricohams_mqtt: retener y testamento (LWT) --------------------------
sys.path.insert(0, os.path.join(RAIZ, 'files/bin'))
import bricohams_mqtt  # noqa: E402

srv = socket.socket()
srv.bind(('127.0.0.1', 0))
srv.listen(1)
recibido = []


def broker():
    c, _ = srv.accept()
    recibido.append(c.recv(4096))
    c.sendall(b'\x20\x02\x00\x00')
    recibido.append(c.recv(4096))
    c.close()


th = threading.Thread(target=broker, daemon=True)
th.start()
pub = bricohams_mqtt.Publicador('127.0.0.1', srv.getsockname()[1], 'sondas-test', 'u', 'p',
                                testamento=('bricohams/sondas/estado', 'offline', True))
assert pub.publicar('bricohams/sondas/estado', 'online', True)
th.join(5)
conn = recibido[0]
assert conn[0] == 0x10 and conn[9] & 0x04 and conn[9] & 0x20 and conn[9] & 0x80 and conn[9] & 0x40
assert b'bricohams/sondas/estado' in conn and b'offline' in conn
assert recibido[1][0] == 0x31 and recibido[1].endswith(b'online')
assert struct.unpack('!H', conn[10:12])[0] == 60
print('OK: radiosondas (validación, duplicados, reventón, caducidad, JSON atómico, MQTT, predicción, station.cfg)')
