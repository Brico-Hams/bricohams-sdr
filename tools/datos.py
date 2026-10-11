#!/usr/bin/env python3
# =====================================================================
#  Genera docs/DATOS.md a partir de los ficheros del repositorio
#  (plantilla de settings, marcadores y bricohams.env.example), para que
#  la documentación nunca se quede atrás de la configuración.
#  Uso: python3 tools/datos.py
# =====================================================================
import json
import os
import re

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
T = json.load(open(os.path.join(RAIZ, 'files/openwebrx/settings.json.tmpl'), encoding='utf-8'))
BM = json.load(open(os.path.join(RAIZ, 'files/openwebrx/bookmarks.json'), encoding='utf-8'))
ENV = dict(re.findall(r'^([A-Z0-9_]+)="([^"]*)"', open(os.path.join(RAIZ, 'bricohams.env.example')).read(), re.M))


def mhz(hz):
    return ('%.4f' % (hz / 1e6)).rstrip('0').rstrip('.').replace('.', ',')


def ms(sr):
    return ('%.3f' % (sr / 1e6)).rstrip('0').rstrip('.').replace('.', ',')


def limpio(t):
    return re.sub(r'[\U0001F000-\U0001FFFF☀-➿️*]+', '', t).strip().replace('|', '/')


L = ['# Conjuntos de datos de la estación', '',
     '> Generado por `tools/datos.py` a partir de `files/openwebrx/settings.json.tmpl`, '
     '`files/openwebrx/bookmarks.json` y `bricohams.env.example`. No lo edites a mano: cambia la fuente y vuelve a generarlo.', '']

L += ['## 1. Receptores SDR', '',
      '| Id OpenWebRX | Nombre | Tipo | Serie (EEPROM) | Perfiles | Activo | Notas |', '|---|---|---|---|---|---|---|']
dev_env = {'__SERIAL_HAT__': 'SERIAL_HAT', '__SERIAL_MINI__': 'SERIAL_MINI', '__SERIAL_V3__': 'SERIAL_V3'}
for k, s in T['sdrs'].items():
    dev = s.get('device', '')
    serie = ENV.get(dev_env.get(dev, ''), '—')
    activo = 'según HF_SDRPLAY' if s.get('enabled') == '__HF_SDRPLAY__' else 'sí'
    notas = []
    if s.get('bias_tee') == '__SAT_BIAS_TEE__':
        notas.append('bias-tee: SAT_BIAS_TEE')
    if 'scheduler' in s:
        sc = s['scheduler']['schedule']
        notas.append('escucha automática: día %s · crepúsculo %s · noche %s' % (sc['day'], sc['greyline'], sc['night']))
    if 'direct_sampling' in s:
        notas.append('muestreo directo por perfil (HF)')
    nombre = limpio(s['name']).replace('__CALLSIGN__', ENV.get('CALLSIGN', 'CALLSIGN'))
    L.append('| `%s` | %s | %s | %s | %d | %s | %s |' % (k, nombre, s['type'], serie, len(s['profiles']), activo, '; '.join(notas)))
L += ['| — | ADS-B (fuera de OpenWebRX) | readsb rtlsdr | %s | — | ADSB_ENABLE | FlightStick de RadarBox: Beast :30005 → rbfeeder + MLAT |' % ENV['SERIAL_ADSB'], '']

for k, s in T['sdrs'].items():
    L += ['## 2.%s Perfiles de `%s` · %s' % ('abcd'[list(T['sdrs']).index(k)], k, limpio(s['name'])), '',
          '| Id | Nombre | Centro (MHz) | Muestreo (MS/s) | Cubre (MHz) | Inicio (MHz) | Modo | Paso | Muestreo directo |',
          '|---|---|---|---|---|---|---|---|---|']
    for pid, p in s['profiles'].items():
        c, sr = p['center_freq'], p['samp_rate']
        ds = p.get('direct_sampling', '')
        ds = {2: 'rama Q', 0: 'no', '': ''}.get(ds, ds)
        extra = ' (solo con el V3 como HF)' if p.get('_bh_hf_rtl') else ''
        L.append('| `%s` | %s%s | %s | %s | %s – %s | %s | %s | %s | %s |' % (
            pid, limpio(p['name']), extra, mhz(c), ms(sr), mhz(c - sr * 0.45), mhz(c + sr * 0.45),
            mhz(p.get('start_freq', c)), p.get('start_mod', ''), p.get('tuning_step', ''), ds))
    L.append('')

CASA = {439450000, 431850000, 439375000, 431775000, 438950000, 431350000, 438250000}
nuevos = [b for b in BM if b['frequency'] in CASA and b['modulation'] in ('dmr', 'ysf')]
L += ['## 3. Marcadores', '', 'Total en el kit: **%d**. Hotspots de casa y repetidores digitales de Sierra Espuña:' % len(BM), '',
      '| Frecuencia (MHz) | Modo | Nombre | Descripción | Perfil que la cubre |', '|---|---|---|---|---|']
for b in sorted(nuevos, key=lambda x: x['frequency']):
    f = b['frequency']
    perfil = '70rep (437,7–439,9)' if f > 435e6 else '70in (429,9–432,1)'
    L.append('| %s | %s | %s | %s | %s |' % (mhz(f), b['modulation'], limpio(b['name']), limpio(b.get('description', '')), perfil))
L += ['', '⚠ En los marcadores anteriores ya estaba **ED5ZAN** (DMR BrandMeister, 438,250 / entrada 430,650). EA5KAO indica ahora **438,950 / 431,350** como repetidor digital de Sierra Espuña: se han dejado los dos hasta confirmar cuál está activo.',
      '', 'Convención: la **salida** del hotspot/repetidor es lo que oyes (TX del equipo), la **entrada** es donde transmites (RX del equipo).', '']

L += ['## 4. Puertos de red', '', '| Puerto | Servicio | Alcance |', '|---|---|---|']
for p, s, a in [('443/tcp', 'v4.2 · nginx https: /login y /settings forzados (y todo, si se quiere)', '**abrir al exterior**'),
                ('80/tcp', 'v4.2 · nginx: receptor público por HTTP (SSL_MODO=admin), Let\'s Encrypt', '**abrir al exterior**'),
                ('8073/tcp', 'OpenWebRX+ (detrás de nginx desde v4)', 'LAN'),
                ('8504/tcp', 'v4 · lighttpd · tar1090 (detrás de nginx)', '127.0.0.1'),
                ('8075/tcp', 'v4 · bricohams-api (indicativos)', '127.0.0.1'),
                ('1883/tcp', 'v4 · mosquitto (informes de clientes de OpenWebRX)', '127.0.0.1'),
                ('8889/tcp + 8189/udp', 'MediaMTX WebRTC (vídeo en directo)', 'opcional'),
                ('8888/tcp', 'MediaMTX HLS', 'LAN'), ('8554/tcp', 'MediaMTX RTSP `rtsp://<pi>:8554/mastil`', 'LAN'),
                ('9997/tcp', 'MediaMTX API', '127.0.0.1'), ('9443/tcp', 'meshtasticd web (https)', '127.0.0.1'), ('8443/tcp', 'nginx: Meshtastic Web (solo admin)', 'LAN'),
                ('8445/tcp', 'v4.6 · nginx: interfaz web de OpenTAKServer (usuario TAK)', 'LAN'),
                ('8089/tcp', 'v4.6 · OpenTAKServer CoT TLS con certificado de cliente', 'LAN'),
                ('8446/tcp', 'v4.6 · nginx: alta de certificados TAK (enrollment)', 'LAN'),
                ('8447/tcp', 'v4.6 · nginx: Marti API TAK con certificado de cliente', 'LAN'),
                ('8081/tcp', 'v4.6 · OpenTAKServer interno', '127.0.0.1'),
                ('5432, 5672/tcp', 'v4.6 · PostgreSQL y RabbitMQ de TAK (cortafuegos `bricohams-tak-fw`)', '127.0.0.1'),
                ('4403/tcp', 'meshtasticd API', 'LAN'), ('30005/tcp', 'readsb salida Beast', 'local'),
                ('30003, 30002, 30104/tcp', 'readsb SBS / raw / entrada Beast', 'local'), ('2947/tcp', 'gpsd', 'local'),
                ('14580/tcp saliente', 'APRS-IS (iGate, WX, OpenWebRX)', 'saliente'),
                ('443/tcp saliente', 'AEMET, Open-Meteo, NOAA, RadarBox, apt, GitHub', 'saliente')]:
    L.append('| %s | %s | %s |' % (p, s, a))

L += ['', '## 5. Servicios systemd', '', '| Unidad | Qué hace | Paso de install.sh |', '|---|---|---|']
for u, q, pa in [('openwebrx', 'receptor web', 'openwebrx / configuracion'), ('sdrplay', 'API del SDRplay', 'sdrplay (pendiente)'),
                 ('bricohams-hat-power', 'GPIO de alimentación de módulos del HAT', 'hat'), ('gpsd', 'GPS del HAT', 'hat'),
                 ('chrony', 'hora NMEA + PPS', 'hat'), ('meshtasticd', 'nodo Meshtastic 868', 'meshtastic'),
                 ('mediamtx', 'vídeo de la cámara', 'camara'), ('bricohams-camsnap', 'foto para la web', 'camara'),
                 ('bricohams-meteo.timer', 'AEMET + Open-Meteo cada 10 min', 'meteo'),
                 ('bricohams-wx', 'sensor BME280 + viento RS485 + lluvia + WX APRS', 'sensor'),
                 ('bricohams-fan', 'ventiladores de la caja v3 (PWM + tacómetros + DS18B20)', 'ventilacion'), ('readsb', 'decodificador ADS-B', 'adsb'),
                 ('rbfeeder', 'envío a RadarBox + MLAT', 'adsb'), ('lighttpd', 'tar1090', 'adsb'),
                 ('bricohams-backup.timer', 'copia diaria 04:30 (v4: desactivado, lo hace cron)', 'herramientas'),
                 ('bricohams-io', 'v4 · puente USB con la Pico (sensores y ventiladores)', 'io'),
                 ('bricohams-satpass.timer', 'v4 · próximos pases de satélites', 'satelites'),
                 ('nginx', 'v4 · https y proxy', 'web'), ('bricohams-api', 'v4 · ficha de indicativos (RadioID/QRZ)', 'web'),
                 ('mosquitto', 'v4 · MQTT local', 'visitas'), ('bricohams-visitas', 'v4 · oyentes, GeoIP y Telegram', 'visitas'),
                 ('cron (`/etc/cron.d/bricohams`)', 'v4 · copias, actualización, reinicio, salud, resumen', 'tareas')]:
    L.append('| `%s` | %s | %s |' % (u, q, pa))

L += ['', '## 6. Bus I2C-1 (GPIO2/GPIO3)', '', '| Dirección | Dispositivo | Uso |', '|---|---|---|',
      '| 0x51 | PCF85063A (HAT) | RTC, `dtoverlay=i2c-rtc,pcf85063a` → /dev/rtc0 |',
      '| 0x76 / 0x77 | BME280 (ID 0x60) o BMP280 (ID 0x58) | `bricohams-wx` |', '']

L += ['## 7. Indicativos y WiFi', '', '| Indicativo | Qué es | Dónde |', '|---|---|---|',
    '| %s | iGate APRS de OpenWebRX (packet 144,800) | settings.json `aprs_callsign` |' % ENV.get('CALLSIGN', 'CALLSIGN'),
      '| %s | iGate LoRa APRS 433,775 (LilyGO, solo RX) | `IGATE_CALLSIGN` |' % ENV['IGATE_CALLSIGN'],
      '| %s | Estación meteorológica (BME280 + viento + lluvia) | `WX_APRS_CALLSIGN` |' % ENV['WX_APRS_CALLSIGN'],
      '| %s | Estación WX LoRa alternativa (3.er LilyGO, CA2RXU) | `WXLORA_CALLSIGN` |' % ENV.get('WXLORA_CALLSIGN', 'EA5KAO-14'),
      '| %s / %s | Nodo Meshtastic 868 (HAT) | `MESH_LONG_NAME` |' % (ENV.get('MESH_LONG_NAME', ''), ENV.get('MESH_SHORT_NAME', '')),
      '| %s / %s | Nodo Meshtastic 433 (LilyGO) | `MESH433_LONG_NAME` |' % (ENV['MESH433_LONG_NAME'], ENV['MESH433_SHORT_NAME']), '']

L += ['## 8. Canales Meshtastic (QR de la red)', '',
      'Origen: `MESH_CHANNEL_URL` (QR aportado por EA5KAO el 04/10/2026). Claves por defecto públicas (índices 1 y 2).', '',
      '| Índice | Canal | Clave |', '|---|---|---|', '| 0 (principal) | SFNarrow | por defecto (AQ==) |',
      '| 1 | Murcia | por defecto |', '| 2 | Cartagena | por defecto |', '| 3 | Test | por defecto nº 2 · posición activada |',
      '| 4 | Alicante | por defecto |',
      '| 5 | BricoHams (`MESH868_PRIVATE_NAME`) | **privada AES-256** (`MESH868_PRIVATE_PSK`, solo en bricohams.env) · **solo nodo 868** |', '',
      'Radio del QR: EU_868, **869,618 MHz**, BW 62,5 kHz, SF7, CR 4/5, saltos 3, potencia 27 dBm (el SX1262 del HAT se queda en 22 dBm), ganancia RX reforzada. '
      'En el LilyGO 433 se cargan los mismos canales y luego la radio pasa a EU_433 LONG_FAST.', '']

L += ['## 9. Rutas importantes en la Raspberry', '', '| Ruta | Contenido |', '|---|---|']
for r, c in [('/etc/bricohams/bricohams.env', 'configuración y claves (600 root)'), ('/etc/bricohams/meteo.env, wx.env', 'variables de los servicios (640 root:openwebrx)'),
             ('/var/lib/openwebrx/', 'settings.json, users.json, bookmarks.json, imágenes'), ('/usr/lib/python3/dist-packages/htdocs/plugins/', 'plugins web'),
             ('…/plugins/receiver/meteo/meteo.json, sensor.json', 'datos del tiempo para la web'), ('…/plugins/receiver/camara/snap/', 'foto de la cámara (tmpfs)'),
             ('/var/lib/bricohams/wx-history.json', 'histórico 24 h del sensor'), ('/var/lib/bricohams/lluvia.json', 'contador del pluviómetro (v3)'),
             ('/etc/bricohams/fan.env', 'curva de los ventiladores (v3)'), ('/run/bricohams/caja.json, …/meteo/caja.json', 'estado de la caja y ventiladores (v3)'),
             ('/etc/udev/rules.d/99-bricohams-rs485.rules', '/dev/rs485 (adaptador USB-RS485, v3)'), ('/etc/meshtasticd/config.d/hackergadgets-hat.yaml', 'pines LoRa del HAT'),
             ('/etc/mediamtx/mediamtx.yml', 'cámara'), ('/etc/default/readsb, /etc/rbfeeder.ini', 'ADS-B'),
             ('/etc/udev/rules.d/99-bricohams-lilygo.rules', '/dev/lilygo-mesh y /dev/lilygo-igate'),
             ('/boot/firmware/config.txt', 'bloque `# >>> BricoHams`'), ('/var/backups/bricohams/', 'copias diarias (14 últimas)'),
             ('/opt/bricohams/kit/', 'copia del kit (sin claves)'), ('/var/log/bricohams-install.log', 'registro del instalador'),
             ('/etc/bricohams/{web,api,visitas,telegram}.env', 'v4 · variables de los servicios web (640)'),
             ('/var/lib/bricohams/visitas.sqlite', 'v4 · oyentes (IP parcial, 90 días)'), ('/var/lib/bricohams/dbip-city-lite.mmdb', 'v4 · GeoIP local (DB-IP Lite)'),
             ('/var/lib/bricohams/indicativos.sqlite', 'v4 · caché de RadioID/QRZ (7 días)'), ('/var/lib/bricohams/tle.json', 'v4 · elementos orbitales de CelesTrak'),
             ('/etc/cron.d/bricohams, /etc/sudoers.d/bricohams', 'v4 · tareas de la cuenta de servicio'), ('/dev/bricohams-io', 'v4 · Pico (udev 2e8a:0005)'),
             ('/run/bricohams/io.json, fan.cmd', 'v4 · lecturas de la Pico y orden de ventiladores'),
             ('/var/lib/bricohams/kit-estado', 'v4.1 · huellas de los pasos para `install.sh --actualizar` (600)'),
             ('/var/lib/bricohams/bookmarks.kit.json', 'v4.1 · marcadores del kit instalado (para conservar los propios)'),
             ('/var/lib/bricohams/actualizaciones.log', 'v4.1 · historial de actualizaciones'),
             ('/var/lib/bricohams/locator/{aemet,fmdx}.json', 'v4.3 · datos de zona bajados en la Pi (caché 30 días)'),
             ('/usr/local/lib/bricohams/, /usr/local/bin/bricohams-locator', 'v4.3 · zona por locator (manual 32)'),
             ('/opt/owrx-docker/{docker-compose.yaml,etc,var,plugins}', 'v4.3 · OpenWebRX+ en Docker (OWRX_BACKEND=docker, manual 33)'),
             ('/usr/local/sbin/bricohams-blindaje, /etc/bricohams/cortafuegos.nft', 'v4.4 · blindaje y cortafuegos del host (manual 34)'),
             ('/etc/ssh/sshd_config.d/90-bricohams.conf, /etc/fail2ban/jail.d/bricohams.conf, /etc/sysctl.d/90-bricohams.conf', 'v4.4 · SSH, fail2ban y núcleo endurecidos'),
             ('/var/backups/bricohams-blindaje/', 'v4.4 · copias de «aplicar» para «deshacer» (700)'),
             ('/run/bricohams-rak/rak-aprs.json', 'v4.5 · estado del RAK4631: firmware, caja, GPS redondeado, oídos (manual 35)'),
             ('/run/bricohams-mesh/mesh.json', 'v4.5 · nodos Meshtastic 433/868 y lo publicado en el mapa de OpenWebRX+'),
             ('/opt/bricohams/firmware/rak4631-lora-aprs/bin/', 'v4.5 · firmware del RAK4631 (.zip DFU, .uf2, .hex)'),
             ('/etc/udev/rules.d/99-bricohams-dispositivos.rules', 'v4.5 · /dev/rak-aprs y /dev/lilygo-mesh por VID:PID y serie'),
             ('/etc/issue.net, /etc/update-motd.d/20-bricohams', 'v4.5 · banner SSH: aviso legal y estado al entrar'),
             ('/etc/nginx/snippets/bricohams-sdr-rutas.conf', 'v4.2 · rutas comunes HTTP/HTTPS de nginx'),
             ('/usr/local/bin/owrx-clone, /var/backups/owrx-clone/', 'v4.2 · perfiles de OpenWebRX+ y copias previas de cada importación'),
             ('/var/backups/bricohams/perfil-owrx-*.owrx.tar.gz', 'v4.2 · perfil diario de OpenWebRX+ (7 últimos)'),
             ('/etc/bricohams/perfil-importado', 'v4.2 · marca: la configuración viene de un perfil importado')]:
    L.append('| `%s` | %s |' % (r, c))

SCAD = open(os.path.join(RAIZ, 'hardware', 'caja', 'caja_bricohams.scad'), encoding='utf-8').read()
SMA = re.search(r'SMA_LABELS = \[([^\]]*)\]', SCAD).group(1).replace('"', '').replace(' ', '').split(',')
DESTINO = {'SAT': 'RTL del HAT (eggbeater + LNA)', 'HAM': 'Mini RTL-SDR (colineal)', 'VHF': 'diplexor VHF/UHF → V3 (discone)',
           'HF': 'diplexor HF → V3 (hilo largo)', 'ADSB': 'FlightStick (1090 MHz)', '868': 'SX1262 del HAT',
           'GPS': 'GPS del HAT (antena activa)', 'M433': 'LilyGO Meshtastic (transmite)', 'IG433': 'LilyGO iGate (solo RX)'}
L += ['', '## 10. Caja v2 (en el mástil): conectores de la cara inferior (de izquierda a derecha)', '',
      'Origen: `SMA_LABELS` de `hardware/caja/caja_bricohams.scad`.', '', '| Pos. | Rótulo | Tipo | Va a |', '|---|---|---|---|',
      '| 0 | 230 V | prensaestopas PG9 | cargador USB 45 W (compartimento de potencia) |']
for i, n in enumerate(SMA, 1):
    L.append('| %d | %s | SMA hembra pasamuros | %s |' % (i, n, DESTINO.get(n, '')))
L += ['| 2.ª fila | WX | prensaestopas PG7 | cable del BME280 |', '| 2.ª fila | LAN | prensaestopas M20 | Ethernet (opcional) |', '',
      '## 11. Alimentación en la caja v2 (la v3 está en MEMORIA_TECNICA y en el esquema 15)', '', '| Puerto del cargador 45 W | Consumidor | Típico | Máximo del puerto |', '|---|---|---|---|',
      '| USB-C PD 5 V 3 A | Raspberry Pi 5 + HAT + cámara | 8–12 W | 15 W |',
      '| USB-A 5 V 2,4 A | hub alimentado: Mini, V3, FlightStick, 2 LilyGO | 5–7 W | 12 W |',
      '| — | **Total** | **13–19 W** | **45 W** |', '',
      '## 12. Redes WiFi (NetworkManager)', '', '| Conexión | SSID | Prioridad | Quién |', '|---|---|---|---|',
      '| bricohams-wifi-1 | `%s` | 20 | Raspberry Pi (5 GHz) |' % (ENV.get('WIFI_SSID_1') or 'WIFI_SSID_1'),
      '| bricohams-wifi-2 | `%s` | 10 | Raspberry Pi (respaldo 2,4 GHz) |' % (ENV.get('WIFI_SSID_2') or 'WIFI_SSID_2'),
      '| — | `%s` | — | iGate LilyGO (solo 2,4 GHz) |' % (ENV.get('LILYGO_WIFI_SSID') or 'LILYGO_WIFI_SSID'),
      '', 'La contraseña solo está en `bricohams.env` (`WIFI_PASS`, `LILYGO_WIFI_PASS`).', '']

# ----------------------------- v3.0 ---------------------------------
import sys  # noqa: E402
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import mastil  # noqa: E402

S3 = open(os.path.join(RAIZ, 'hardware', 'caja_v3', 'caja_v3.scad'), encoding='utf-8').read()
FILAS = re.findall(r'\[(\d+), \[([^\]]*)\]\]', re.search(r'N_ROWS = \[(.*)\];', S3).group(1))
DEST3 = {'SAT': 'RTL del HAT (eggbeater + LNA)', 'HAM': 'Mini RTL-SDR (quad 2 m/70 + diplexor)', 'VHF': 'diplexor → V3 (discone grande)',
         'HF': 'inyector MLA-30 → diplexor → V3', 'ADSB': 'bias-tee 5 V → FlightStick (LNA en la antena)', '868': 'SX1262 del HAT (Bigsignal 868)',
         'GPS': 'GPS del HAT', 'M433': 'LilyGO Meshtastic (fibra 433)', 'IG433': 'FBP-433s → LilyGO iGate (Bigsignal 433)',
         'DISC2': 'discone compacta → bahía de expansión', 'HF2': 'SDRplay antena B (futura)', 'R1': 'reserva', 'R2': 'reserva', 'R3': 'reserva'}
L += ['## 13. Caja v3: pasamuros N de la cara inferior', '',
      'Origen: `N_ROWS` de `hardware/caja_v3/caja_v3.scad` (manual 17).', '', '| Fila (altura z) | Rótulo | Va a |', '|---|---|---|']
for z, nombres in FILAS:
    for n in nombres.replace('"', '').replace(' ', '').split(','):
        L.append('| z = %s mm | %s | %s |' % (z, n, DEST3.get(n, '')))
L += ['| z = 88 mm | M25 PWR · M20 LAN · PG7 WX · PG7 VIENTO · PG7 LLUVIA · PG7 RES | prensaestopas |', '']

L += ['## 14. v4 · Pico «bricohams-io» (con el HAT puesto, `IO_MODE="pico"`)', '', '| Pin Pico | GP | Uso |', '|---|---|---|']
for pin, g, u in [('6 / 7', 'GP4 / GP5', 'I2C0 SDA / SCL · BME280 (0x76/0x77)'), ('29', 'GP22', 'DS18B20 1-Wire (4,7 kΩ a 3V3)'),
                  ('20', 'GP15', 'pluviómetro (10 kΩ a 3V3 + 100 nF)'), ('21 / 22', 'GP16 / GP17', 'PWM 25 kHz ventiladores (2N7002, invertido)'),
                  ('24 / 25', 'GP18 / GP19', 'tacómetros (10 kΩ a 3V3 + 1 kΩ)'), ('36 / 38', '3V3(OUT) / GND', 'alimentación de sensores')]:
    L.append('| %s | %s | %s |' % (pin, g, u))
L += ['', 'Protocolo: una línea JSON cada 2 s; órdenes `FAN d1 d2` y `PING`; sin órdenes en 60 s → ventiladores al 100 %%. Modo actual: `IO_MODE=%s`.' % ENV.get('IO_MODE', 'pico'), '']
L += ['### 14 bis. GPIO de la Pi (solo sin HAT, `IO_MODE="gpio"`)', '', '| Pin | GPIO | Uso | Variable |', '|---|---|---|---|']
fp = ENV.get('FAN_PWM_GPIOS', '12,13').split(','); ft = ENV.get('FAN_TACH_GPIOS', '22,5').split(',')
for pin, g, u, var in [('7', ENV.get('W1_GPIO', '4'), 'DS18B20 (1-Wire)', 'W1_GPIO'), ('11', ENV.get('RAIN_GPIO', '17'), 'pluviómetro', 'RAIN_GPIO'),
                       ('15', ft[0], 'tacómetro ventilador de entrada', 'FAN_TACH_GPIOS'), ('29', ft[1], 'tacómetro ventilador de salida', 'FAN_TACH_GPIOS'),
                       ('32', fp[0], 'PWM ventilador de entrada (PWM0 c0)', 'FAN_PWM_GPIOS'), ('33', fp[1], 'PWM ventilador de salida (PWM0 c1)', 'FAN_PWM_GPIOS')]:
    L.append('| %s | GPIO%s | %s | `%s` |' % (pin, g, u, var))
L += ['', 'Viento: RS485 Modbus RTU %s 8N1 por `%s` · anemómetro en dirección %s, veleta en %s (`%s`).' % (
      ENV.get('WIND_BAUD'), ENV.get('WIND_PORT'), ENV.get('WIND_ADDR_SPEED'), ENV.get('WIND_ADDR_DIR'), ENV.get('WIND_DIR_MODE')),
      'Curva de ventiladores: CPU %s–%s °C, caja %s–%s °C, mínimo %s %%, histéresis %s °C.' % (
      ENV.get('FAN_T_CPU_MIN'), ENV.get('FAN_T_CPU_MAX'), ENV.get('FAN_T_CAJA_MIN'), ENV.get('FAN_T_CAJA_MAX'), ENV.get('FAN_DUTY_MIN'), ENV.get('FAN_HIST')), '']

L += ['## 15. Plan del mástil', '', 'Origen: `ANTENAS` de `tools/mastil.py` (esquema 11).', '',
      '| Antena | Altura (m) | Brazo (m) | Rumbo | Banda | Transmite |', '|---|---|---|---|---|---|']
for n, z, b, r, a, cd, pe, tx, banda in sorted(mastil.ANTENAS, key=lambda x: -x[1]):
    L.append('| %s | %s | %s | %s | %s | %s |' % (n, ('%.2f' % z).replace('.', ','), ('%.2f' % b).replace('.', ','), r, banda, 'sí' if tx else 'no'))
W40 = mastil.modulo(40, 2.0)
L += ['', 'Mástil Ø40 × 2: %d MPa a 130 km/h sin vientos (límite S235: 235 MPa) → **vientos a %s m**: %d MPa a 150 km/h.' % (
      round(mastil.GAMMA * mastil.momento(130, 40)[0] * 1000 / W40), ('%.1f' % mastil.Z_VIENTOS).replace('.', ','),
      round(mastil.GAMMA * mastil.momento_con_vientos(150, 40)[0] * 1000 / W40)), '']

R = os.path.join(RAIZ, 'hardware', 'antenas', 'sim', 'resultados')
Q = json.load(open(os.path.join(R, 'quad_2m70.json'), encoding='utf-8'))
G = json.load(open(os.path.join(R, 'gp1090.json'), encoding='utf-8'))
L += ['## 16. Antenas construidas: resultados NEC2', '', 'Origen: `hardware/antenas/sim/resultados/*.json`.', '',
      '| Antena | f (MHz) | Ganancia (dBi) | F/B (dB) | ROE 50 Ω |', '|---|---|---|---|---|']
for banda in ('2m', '70'):
    for x in Q['bandas'][banda]:
        if x['f'] in (144.0, 145.0, 146.0, 432.0, 436.0, 440.0):
            roe = Q['adaptacion_2m']['roe50'] if banda == '2m' and x['f'] == 145.0 else x['roe50']
            nota = ' (con λ/4 de 75 Ω)' if banda == '2m' and x['f'] == 145.0 else (' (sin adaptar)' if banda == '2m' else '')
            L.append('| Quad %s | %s | %s | %s | %s%s |' % ('2 m' if banda == '2m' else '70 cm', ('%g' % x['f']).replace('.', ','),
                     ('%.1f' % x['g']).replace('.', ','), ('%.0f' % x['fb']), ('%.2f' % roe).replace('.', ','), nota))
for x in G['barrido']:
    if x['f'] == 1090:
        L.append('| ADS-B λ/4 (%d / %d mm) | 1090 | %s (horizonte) | — | %s |' % (G['radiante_mm'], G['radiales_mm'],
                 ('%.2f' % x['g_horiz']).replace('.', ','), ('%.2f' % x['roe50']).replace('.', ',')))
L += ['', 'Medidas de corte: manuales 12 (quad), 13 (discones) y 14 (ADS-B).', '']

rep = [b for b in BM if b['name'].startswith('🔁')]
L += ['## 17. Repetidores en los marcadores (subtono en la descripción)', '',
      'Origen: `data/repetidores_EA5KGV_zonaEA5.csv` → `tools/marcadores.py`. Primer marcador: **%s**.' % limpio(BM[0]['name']), '',
      '| Frecuencia (MHz) | Nombre | Descripción |', '|---|---|---|']
for b in sorted(rep, key=lambda x: x['frequency']):
    L.append('| %s | %s | %s |' % (mhz(b['frequency']), limpio(b['name']), limpio(b.get('description', ''))))
L.append('')

open(os.path.join(RAIZ, 'docs', 'DATOS.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('docs/DATOS.md: %d líneas' % len(L))
