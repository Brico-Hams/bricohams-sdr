#!/usr/bin/env python3
# =====================================================================
#  Genera los esquemas de docs/esquemas/ (SVG, y PNG si hay cairosvg).
#  Uso: python3 tools/esquemas.py
#  Las asignaciones salen de bricohams.env.example, así que si cambias un
#  pin o una serie allí, vuelve a ejecutar este script.
# =====================================================================
import os
import re
from xml.sax.saxutils import escape as _esc


def esc(t):
    # sin emojis (la fuente de los PNG no los tiene)
    return _esc(''.join(ch for ch in str(t) if ord(ch) < 0x2600 or 0x2190 <= ord(ch) <= 0x21FF or ch in '⚠')).replace('  ', ' ').strip()

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(RAIZ, 'docs', 'esquemas')
ENV = dict(re.findall(r'^([A-Z0-9_]+)="([^"]*)"', open(os.path.join(RAIZ, 'bricohams.env.example')).read(), re.M))

FONT = "font-family='DejaVu Sans, Arial, sans-serif'"
C = {'bg': '#ffffff', 'ink': '#1d2733', 'mute': '#5f6b78', 'line': '#9aa6b2',
     'or': '#F26B21', 'cr': '#A6192E', 'pi': '#2e7d32', 'sdr': '#1565c0', 'rf': '#6a1b9a',
     'lora': '#00838f', 'gps': '#ef6c00', 'i2c': '#2e7d32', 'pwr': '#c62828', 'gnd': '#37474f',
     'spi': '#6a1b9a', 'uart': '#ef6c00', 'free': '#eceff1', 'cam': '#455a64', 'net': '#00695c'}


def svg(w, h, body, title):
    return (f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}' {FONT}>"
            f"<rect width='{w}' height='{h}' fill='{C['bg']}'/>"
            f"<text x='24' y='36' font-size='22' font-weight='bold' fill='{C['ink']}'>{esc(title)}</text>"
            f"<text x='24' y='58' font-size='12' fill='{C['mute']}'>BricoHams SDR · generado por tools/esquemas.py</text>"
            f"<rect x='0' y='{h - 8}' width='{w}' height='8' fill='{C['or']}'/><rect x='0' y='{h - 10}' width='{w}' height='2' fill='{C['cr']}'/>"
            + body + "</svg>")


def box(x, y, w, h, title, lines=(), color=C['ink'], fill='#f7f9fb'):
    s = f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='8' fill='{fill}' stroke='{color}' stroke-width='2'/>"
    s += f"<rect x='{x}' y='{y}' width='{w}' height='24' rx='8' fill='{color}'/><rect x='{x}' y='{y + 14}' width='{w}' height='10' fill='{color}'/>"
    s += f"<text x='{x + 10}' y='{y + 17}' font-size='13' font-weight='bold' fill='#fff'>{esc(title)}</text>"
    for i, ln in enumerate(lines):
        s += f"<text x='{x + 10}' y='{y + 42 + i * 16}' font-size='11.5' fill='{C['ink']}'>{esc(ln)}</text>"
    return s


def arrow(x1, y1, x2, y2, color=C['line'], label='', dash=False, w=2):
    d = " stroke-dasharray='6 4'" if dash else ''
    s = (f"<line x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}' stroke='{color}' stroke-width='{w}'{d} marker-end='url(#a{color[1:]})'/>")
    if label:
        s += f"<text x='{(x1 + x2) / 2 + 4}' y='{(y1 + y2) / 2 - 4}' font-size='10.5' fill='{color}'>{esc(label)}</text>"
    return s


def markers(colors):
    return '<defs>' + ''.join(
        f"<marker id='a{c[1:]}' markerWidth='10' markerHeight='8' refX='9' refY='4' orient='auto'><path d='M0,0 L10,4 L0,8 z' fill='{c}'/></marker>"
        for c in sorted(set(colors))) + '</defs>'


# ---------------------------------------------------------------------
def bloques():
    W, H = 1500, 960
    b = markers([C['line'], C['sdr'], C['lora'], C['gps'], C['net'], C['rf'], C['cam'], C['i2c']])
    # antenas
    ants = [('Eggbeater 2 m/70 cm + LNA', 90, C['rf']), ('Colineal 2 m/70 cm', 170, C['rf']),
            ('Discone 25-1300 MHz', 250, C['rf']), ('Hilo largo HF + diplexor', 330, C['rf']),
            ('Antena 1090 MHz', 410, C['rf']), ('Antena 868 MHz', 490, C['lora']), ('Antena GPS activa', 570, C['gps']),
            ('Antena 433 MHz (Meshtastic)', 650, C['lora']), ('Antena 433 MHz (iGate)', 730, C['lora'])]
    b += f"<text x='24' y='86' font-size='14' font-weight='bold' fill='{C['rf']}'>ANTENAS (mástil)</text>"
    for t, y, c in ants:
        b += f"<rect x='24' y='{y - 2}' width='230' height='34' rx='6' fill='#fff' stroke='{c}' stroke-width='1.5'/>"
        b += f"<text x='36' y='{y + 20}' font-size='12' fill='{c}'>📡 {esc(t)}</text>"
    # receptores
    b += box(330, 80, 300, 70, 'RTL-SDR del HAT (R860, TCXO)', ['serie ' + ENV['SERIAL_HAT'] + ' · bias-tee → LNA', '→ OpenWebRX 🛰️ SATÉLITES'], C['sdr'])
    b += box(330, 160, 300, 70, 'Mini RTL-SDR HackerGadgets (R860)', ['serie ' + ENV['SERIAL_MINI'], '→ OpenWebRX 🟢 RADIOAFICIONADOS'], C['sdr'])
    b += box(330, 240, 300, 110, 'RTL-SDR Blog V3 (R820T2)', ['serie ' + ENV['SERIAL_V3'], '→ OpenWebRX 🔵 MULTIPERFIL', 'HF 160-15 m: muestreo directo rama Q', '(12-6 m y VHF: sintonizador normal)'], C['sdr'])
    b += box(330, 400, 300, 56, 'FlightStick AirNav RadarBox', ['serie ' + ENV['SERIAL_ADSB'] + ' · LNA + filtro 1090'], C['sdr'])
    b += box(330, 470, 300, 140, 'HAT HackerGadgets', ['LoRa SX1262 868 (SPI1) → meshtasticd', 'GPS GPS+BDS (UART0) + PPS GPIO' + ENV['HAT_PPS_GPIO'],
                                                       'RTC PCF85063A (I2C-1, 0x51) con pila', 'RTL-SDR (USB) ↑', 'pines A VERIFICAR (guía AIO)'], C['lora'])
    b += box(330, 640, 300, 56, 'LilyGO T3 V1.6.1 · 433 (USB)', ['/dev/lilygo-mesh → Meshtastic EU_433'], C['lora'])
    b += box(330, 720, 300, 56, 'LilyGO T3 V1.6.1 · 433 (USB)', ['/dev/lilygo-igate → iGate LoRa APRS RX'], C['lora'])
    b += box(330, 800, 300, 56, 'Sensor BME280/BMP280 (garita)', ['I2C-1 0x76/0x77 · cable 4 hilos'], C['i2c'])
    b += box(330, 870, 300, 56, 'Cámara WPI408 (OV5647 + 2 IR)', ['CSI 15→22 pines · cámara Pi 5'], C['cam'])
    for (y1, y2, c) in [(107, 107, C['rf']), (187, 187, C['rf']), (267, 270, C['rf']), (347, 320, C['rf']),
                        (427, 428, C['rf']), (507, 495, C['lora']), (587, 525, C['gps']), (667, 668, C['lora']), (747, 748, C['lora'])]:
        b += arrow(256, y1, 328, y2, c)
    # Pi 5
    b += box(700, 80, 360, 846, 'Raspberry Pi 5 · Bookworm 64 bits', [], C['pi'], '#f3faf3')
    svcs = [('OpenWebRX+ :8073', 'rx SAT · HAM · MULTI (+HF) · SDRplay*'), ('Plugins web', 'DX · SOL · METEO · CAM · BricoHams'),
            ('readsb', 'Beast :30005 · tar1090 en :80'), ('rbfeeder + MLAT', 'AirNav RadarBox'),
            ('meshtasticd', 'nodo 868 · web :8443 (admin) · API :4403'), ('gpsd + chrony', 'hora GPS + PPS · :2947'),
            ('bricohams-wx', 'sensor → sensor.json · WX APRS'), ('bricohams-meteo', 'AEMET + Open-Meteo (10 min)'),
            ('MediaMTX', 'RTSP :8554 · WebRTC :8889 · HLS :8888'), ('bricohams-camsnap', 'foto cada 60 s → web :8073'),
            ('bricohams-lilygo', 'config. Meshtastic 433 e iGate'), ('bricohams-backup', 'copia diaria 04:30')]
    for i, (n, d) in enumerate(svcs):
        y = 116 + i * 66
        b += f"<rect x='716' y='{y}' width='328' height='56' rx='6' fill='#fff' stroke='{C['pi']}'/>"
        b += f"<text x='728' y='{y + 22}' font-size='13' font-weight='bold' fill='{C['pi']}'>{esc(n)}</text>"
        b += f"<text x='728' y='{y + 42}' font-size='11.5' fill='{C['ink']}'>{esc(d)}</text>"
    for y in (115, 195, 295):
        b += arrow(632, y, 714, 144, C['sdr'])
    b += arrow(632, 428, 714, 276, C['sdr'], 'USB')
    b += arrow(632, 500, 714, 408, C['lora'], 'SPI1')
    b += arrow(632, 530, 714, 474, C['gps'], 'UART0+PPS')
    b += arrow(632, 668, 714, 804, C['lora'], 'USB')
    b += arrow(632, 748, 714, 804, C['lora'])
    b += arrow(632, 828, 714, 540, C['i2c'], 'I2C-1')
    b += arrow(632, 898, 714, 672, C['cam'], 'CSI')
    # salidas
    outs = [(140, 'Navegador · visitantes', 'http://<pi>:8073'), (250, 'AirNav RadarBox', 'Beast + MLAT'),
            (360, 'Red Meshtastic 868', 'SFNarrow · Murcia · Cartagena · Test · Alicante'),
            (470, 'Red Meshtastic 433', 'mismos canales, EU_433'), (580, 'APRS-IS (euro.aprs2.net)', 'iGate N0CALL-10 · WX N0CALL-13 · OWRX N0CALL'),
            (690, 'PSKReporter · WSPRnet', 'FT8/WSPR de OpenWebRX'), (800, 'AEMET · Open-Meteo · NOAA', 'datos de entrada')]
    b += f"<text x='1130' y='120' font-size='14' font-weight='bold' fill='{C['net']}'>SERVICIOS EXTERNOS</text>"
    for y, t, d in outs:
        b += f"<rect x='1130' y='{y}' width='340' height='60' rx='6' fill='#fff' stroke='{C['net']}' stroke-width='1.5'/>"
        b += f"<text x='1142' y='{y + 24}' font-size='13' font-weight='bold' fill='{C['net']}'>{esc(t)}</text>"
        b += f"<text x='1142' y='{y + 44}' font-size='11' fill='{C['ink']}'>{esc(d)}</text>"
        b += arrow(1062, y + 30, 1128, y + 30, C['net'])
    b += f"<text x='1130' y='900' font-size='11' fill='{C['mute']}'>* SDRplay: preparado, se activa con HF_SDRPLAY=yes</text>"
    return svg(W, H, b, 'Arquitectura del sistema')


# ---------------------------------------------------------------------
def gpio():
    # cabecera de 40 pines de la Raspberry Pi 5 (numeración física / BCM)
    pins = {1: ('3V3', 'pwr'), 2: ('5V', 'pwr'), 3: ('GPIO2 SDA1', 'i2c'), 4: ('5V', 'pwr'), 5: ('GPIO3 SCL1', 'i2c'), 6: ('GND', 'gnd'),
            7: ('GPIO4 1-Wire', 'w1'), 8: ('GPIO14 TXD0', 'uart'), 9: ('GND', 'gnd'), 10: ('GPIO15 RXD0', 'uart'), 11: ('GPIO17', 'wx'),
            12: ('GPIO18 SPI1 CE0', 'spi'), 13: ('GPIO27', None), 14: ('GND', 'gnd'), 15: ('GPIO22', 'fan'), 16: ('GPIO23', None),
            17: ('3V3', 'pwr'), 18: ('GPIO24', 'spi'), 19: ('GPIO10', None), 20: ('GND', 'gnd'), 21: ('GPIO9', None), 22: ('GPIO25', 'spi'),
            23: ('GPIO11', None), 24: ('GPIO8', None), 25: ('GND', 'gnd'), 26: ('GPIO7', None), 27: ('ID_SD', None), 28: ('ID_SC', None),
            29: ('GPIO5', 'fan'), 30: ('GND', 'gnd'), 31: ('GPIO6', 'gps'), 32: ('GPIO12 PWM0', 'fan'), 33: ('GPIO13 PWM0', 'fan'), 34: ('GND', 'gnd'),
            35: ('GPIO19 SPI1 MISO', 'spi'), 36: ('GPIO16', None), 37: ('GPIO26', 'spi'), 38: ('GPIO20 SPI1 MOSI', 'spi'),
            39: ('GND', 'gnd'), 40: ('GPIO21 SPI1 SCLK', 'spi')}
    uso = {3: 'RTC 0x51 + BME280 SDA', 5: 'RTC 0x51 + BME280 SCL', 8: 'GPS RX (HAT)', 10: 'GPS TX (HAT)',
           12: 'LoRa NSS/CS', 18: 'LoRa BUSY', 22: 'LoRa RESET', 31: 'GPS PPS', 35: 'LoRa MISO', 37: 'LoRa DIO1/IRQ',
           38: 'LoRa MOSI', 40: 'LoRa SCK', 1: 'BME280 VIN · pull-ups', 9: 'BME280 GND', 2: 'alimentación HAT', 4: 'alimentación HAT', 6: 'GND HAT',
           7: 'DS18B20 (solo sin HAT)', 11: 'pluviómetro (solo sin HAT)', 15: 'tacóm. 1 (solo sin HAT)', 29: 'tacóm. 2 (solo sin HAT)',
           32: 'PWM vent. 1 (solo sin HAT)', 33: 'PWM vent. 2 (solo sin HAT)', 14: 'GND'}
    col = {'pwr': C['pwr'], 'gnd': C['gnd'], 'i2c': C['i2c'], 'uart': C['uart'], 'spi': C['spi'], 'gps': C['gps'],
           'fan': '#5d4037', 'w1': '#8e24aa', 'wx': '#0277bd'}
    W, H = 1240, 820
    b = markers([C['line']])
    x0, y0, rowh = 470, 110, 32
    b += f"<rect x='{x0 - 20}' y='{y0 - 20}' width='300' height='{20 * rowh + 30}' rx='10' fill='#1b5e20'/>"
    for n in range(1, 41):
        r = (n - 1) // 2; left = n % 2 == 1
        cx = x0 + (100 if left else 160); cy = y0 + r * rowh + 6
        name, k = pins[n]
        c = col.get(k, '#b0bec5')
        b += f"<rect x='{cx - 13}' y='{cy - 13}' width='26' height='26' rx='4' fill='{c}' stroke='#fff'/>"
        b += f"<text x='{cx}' y='{cy + 4}' font-size='10.5' text-anchor='middle' fill='#fff' font-weight='bold'>{n}</text>"
        tx = x0 - 30 if left else x0 + 290
        anchor = 'end' if left else 'start'
        b += f"<text x='{tx}' y='{cy - 1}' font-size='11.5' text-anchor='{anchor}' fill='{c if k else C['mute']}' font-weight='bold'>{esc(name)}</text>"
        if n in uso:
            b += f"<text x='{tx}' y='{cy + 13}' font-size='10.5' text-anchor='{anchor}' fill='{C['ink']}'>{esc(uso[n])}</text>"
    b += f"<text x='{x0 + 130}' y='{y0 - 28}' font-size='12' text-anchor='middle' fill='{C['ink']}'>Cabecera de 40 pines (vista desde arriba, USB/Ethernet abajo)</text>"
    ley = [('pwr', 'Alimentación 3V3 / 5V'), ('gnd', 'GND'), ('i2c', 'I2C-1: RTC 0x51 + BME280 0x76/77'),
           ('uart', 'UART0 ttyAMA0 9600: GPS'), ('gps', 'PPS → /dev/pps0'),
           ('spi', 'SPI1 spidev1.0: LoRa SX1262'), ('fan', 'IO_MODE=gpio: ventiladores (con HAT: Pico)'),
           ('w1', 'IO_MODE=gpio: DS18B20'), ('wx', 'IO_MODE=gpio: pluviómetro')]
    for i, (k, t) in enumerate(ley):
        b += f"<rect x='930' y='{510 + i * 26}' width='14' height='14' fill='{col[k]}'/><text x='952' y='{522 + i * 26}' font-size='12' fill='{C['ink']}'>{esc(t)}</text>"
    b += (f"<text x='24' y='{790}' font-size='12' fill='{C['cr']}' font-weight='bold'>⚠ Pines del HAT tomados de la guía AIO de HackerGadgets: A VERIFICAR con su documentación (bricohams.env, HAT_*).</text>")
    b += (f"<text x='24' y='{770}' font-size='12' fill='{C['or']}' font-weight='bold'>v4: con el HAT puesto la cabecera queda ocupada; sensores y ventiladores van a la Pico «bricohams-io» por USB (esquema 16).</text>")
    return svg(W, H, b, 'Raspberry Pi 5: asignación de GPIO')


# ---------------------------------------------------------------------
def bme280():
    W, H = 1200, 640
    b = markers([C['line']])
    # módulo
    b += f"<rect x='80' y='130' width='240' height='300' rx='10' fill='#6a1b9a'/>"
    b += f"<text x='200' y='160' font-size='15' text-anchor='middle' fill='#fff' font-weight='bold'>GY-BME/BMP280 (GYBMEP)</text>"
    b += f"<text x='200' y='180' font-size='10.5' text-anchor='middle' fill='#e1bee7'>regulador 662K 3,3 V</text>"
    b += f"<text x='200' y='196' font-size='10.5' text-anchor='middle' fill='#e1bee7'>+ adaptación de nivel I2C</text>"
    b += f"<rect x='170' y='330' width='60' height='60' rx='6' fill='#cfd8dc'/><text x='200' y='366' font-size='10' text-anchor='middle' fill='#37474f'>sensor</text>"
    mp = [('VIN', C['pwr']), ('GND', C['gnd']), ('SCL', C['i2c']), ('SDA', C['i2c'])]
    pp = [('pin 1 · 3V3', C['pwr']), ('pin 9 · GND', C['gnd']), ('pin 5 · GPIO3 SCL1', C['i2c']), ('pin 3 · GPIO2 SDA1', C['i2c'])]
    wires = ['rojo', 'negro', 'amarillo', 'azul']
    for i, ((m, c), (p, c2), wcol) in enumerate(zip(mp, pp, wires)):
        y = 220 + i * 26
        b += f"<circle cx='300' cy='{y}' r='7' fill='#ffd54f' stroke='#5d4037'/><text x='286' y='{y + 4}' font-size='12' text-anchor='end' fill='#fff' font-weight='bold'>{m}</text>"
        wc = {'rojo': '#d32f2f', 'negro': '#212121', 'amarillo': '#fbc02d', 'azul': '#1976d2'}[wcol]
        b += f"<path d='M307,{y} C520,{y} 620,{y} 840,{y}' stroke='{wc}' stroke-width='4' fill='none'/>"
        b += f"<text x='560' y='{y - 5}' font-size='11' text-anchor='middle' fill='{C['ink']}'>{wcol}</text>"
        b += f"<rect x='840' y='{y - 11}' width='22' height='22' rx='3' fill='{c2}'/><text x='872' y='{y + 4}' font-size='12.5' fill='{C['ink']}' font-weight='bold'>{p}</text>"
    b += f"<text x='840' y='190' font-size='13' fill='{C['pi']}' font-weight='bold'>Raspberry Pi 5 (o pines pasantes del HAT)</text>"
    notes = ['• Alimentar a 3,3 V (pin 1): el bus I2C de la Pi es de 3,3 V.',
             '• Dirección 0x76 (SDO a GND, lo normal en GYBMEP) o 0x77: el software prueba las dos.',
             '• El chip se reconoce solo: ID 0x60 = BME280 (con humedad), 0x58 = BMP280 (sin humedad).',
             '• Comparte el bus con el RTC del HAT (0x51): no hay conflicto de direcciones.',
             '• Cable apantallado de 4 hilos, máx. ~2 m a 100 kHz. Más largo: extensor I2C (P82B715) o el sensor junto a la caja.',
             '• Garita de radiación ventilada a la sombra, 1,5-2 m del suelo y lejos de la caja de la Pi (que calienta).',
             '• Comprobar: sudo i2cdetect -y 1 → 51 (RTC) y 76/77 (sensor) · sudo bricohams-wx --una']
    for i, t in enumerate(notes):
        b += f"<text x='80' y='{480 + i * 20}' font-size='12.5' fill='{C['ink']}'>{esc(t)}</text>"
    return svg(W, H, b, 'Cableado del sensor BME280/BMP280 (I2C-1)')


# ---------------------------------------------------------------------
def rf():
    W, H = 1400, 900
    b = markers([C['rf'], C['sdr'], C['lora'], C['gps'], C['cam'], C['pwr']])
    rows = [('Eggbeater 2 m/70 cm (sat)', 'LNA 2 m/70 cm', 'RTL HAT · SATÉLITES', 'bias-tee 5 V opcional (SAT_BIAS_TEE)'),
            ('Colineal 2 m/70 cm', '—', 'Mini RTL · RADIOAFICIONADOS', 'repetidores, hotspots, PMR, LoRa'),
            ('Discone 25-1300 MHz', 'diplexor HF/VHF (corte ~30 MHz)', 'RTL V3 · MULTIPERFIL', 'un solo SMA: HF por la rama Q'),
            ('Hilo largo / EFHW HF', '↑ entrada HF del diplexor', '(mismo V3)', '160-15 m muestreo directo'),
            ('Antena 1090 MHz', '— (LNA+filtro dentro)', 'FlightStick RadarBox · ADS-B', 'readsb + rbfeeder + MLAT'),
            ('Antena 868 MHz', '—', 'SX1262 del HAT · Meshtastic 868', '869,618 MHz BW 62,5 kHz SF7'),
            ('GPS activa (GPS+BDS)', '—', 'GPS del HAT · gpsd + PPS', 'hora para MLAT, FT8 y logs'),
            ('433 MHz', '—', 'LilyGO 1 · Meshtastic EU_433', 'transmite: separar ≥1 m de las RX'),
            ('433 MHz', '—', 'LilyGO 2 · iGate LoRa APRS', 'solo recepción 433,775 MHz')]
    xs = [24, 330, 640, 1000]
    heads = ['ANTENA', 'FILTRO / LNA', 'RECEPTOR', 'NOTA']
    for x, t in zip(xs, heads):
        b += f"<text x='{x}' y='96' font-size='13' font-weight='bold' fill='{C['ink']}'>{t}</text>"
    for i, row in enumerate(rows):
        y = 112 + i * 70
        cc = C['lora'] if ('LilyGO' in row[2] or 'SX1262' in row[2]) else C['gps'] if 'GPS' in row[2] else C['rf']
        for j, (x, t) in enumerate(zip(xs, row)):
            w = 280 if j < 3 else 370
            fill = '#fff' if j != 2 else '#eef4fb'
            b += f"<rect x='{x}' y='{y}' width='{w}' height='48' rx='6' fill='{fill}' stroke='{cc if j == 0 else C['sdr'] if j == 2 else C['line']}' stroke-width='1.5'/>"
            b += f"<text x='{x + 10}' y='{y + 29}' font-size='12.5' fill='{C['ink']}'>{esc(t)}</text>"
        b += arrow(306, y + 24, 328, y + 24, cc)
        b += arrow(612, y + 24, 638, y + 24, cc)
    b += (f"<text x='24' y='{760}' font-size='13' font-weight='bold' fill='{C['pwr']}'>Alimentación y USB</text>")
    notes = ['En la caja: cargador USB de 45 W. USB-C PD (5 V 3 A) a la Pi 5; USB-A al hub alimentado (esquema 06).',
             'Mini, V3, FlightStick y los 2 LilyGO cuelgan del HUB USB 2.0 ALIMENTADO; a la Pi solo llegan sus datos.',
             'Cámara WPI408 por CSI con cable 15→22 pines de la Pi 5 (máx. ~1 m dentro de la caja). Los LED IR toman 3,3 V de la placa de la cámara.',
             'El módulo LX-LBU2C (power bank 18650, 5 V 2,4 A) NO sirve para la Pi 5: ver docs/EVALUACION_MODULOS.md.']
    for i, t in enumerate(notes):
        b += f"<text x='24' y='{784 + i * 20}' font-size='12' fill='{C['ink']}'>{esc(t)}</text>"
    return svg(W, H, b, 'Cadena de RF, antenas y alimentación')


# ---------------------------------------------------------------------
def red():
    W, H = 1240, 760
    b = markers([C['net']])
    rows = [('8073/tcp', 'OpenWebRX+ (web, foto de la cámara, meteo)', 'ABRIR al exterior', C['pi']),
            ('80/tcp', 'lighttpd: tar1090 (mapa de aviones)', 'opcional', C['sdr']),
            ('8889/tcp + 8189/udp', 'MediaMTX WebRTC (vídeo en directo)', 'opcional', C['cam']),
            ('8888/tcp', 'MediaMTX HLS', 'solo LAN', C['cam']),
            ('8554/tcp', 'MediaMTX RTSP (rtsp://<pi>:8554/mastil)', 'solo LAN', C['cam']),
            ('8443/tcp', 'Meshtastic Web (sesión admin)', 'solo LAN', C['lora']),
            ('4403/tcp', 'meshtasticd: API (CLI, apps)', 'solo LAN', C['lora']),
            ('30005/tcp', 'readsb: salida Beast (rbfeeder)', 'local', C['sdr']),
            ('2947/tcp', 'gpsd', 'local', C['gps']),
            ('9997/tcp', 'MediaMTX API (127.0.0.1)', 'local', C['cam']),
            ('14580/tcp saliente', 'APRS-IS: iGate, WX y OpenWebRX', 'saliente', C['net']),
            ('443/tcp saliente', 'AEMET, Open-Meteo, NOAA, RadarBox, apt', 'saliente', C['net'])]
    for i, (p, d, e, c) in enumerate(rows):
        y = 96 + i * 50
        b += f"<rect x='24' y='{y}' width='190' height='38' rx='6' fill='{c}'/><text x='36' y='{y + 24}' font-size='13' font-weight='bold' fill='#fff'>{esc(p)}</text>"
        b += f"<text x='232' y='{y + 24}' font-size='13' fill='{C['ink']}'>{esc(d)}</text>"
        ec = C['cr'] if e.startswith('ABRIR') else C['mute']
        b += f"<text x='880' y='{y + 24}' font-size='12.5' fill='{ec}' font-weight='bold'>{esc(e)}</text>"
    return svg(W, H, b, 'Red: puertos y servicios')


# ---------------------------------------------------------------------
SCAD = open(os.path.join(RAIZ, 'hardware', 'caja', 'caja_bricohams.scad'), encoding='utf-8').read()


def scad(nombre):
    return float(re.search(r'^%s\s*=\s*([0-9.]+)' % nombre, SCAD, re.M).group(1))


def alimentacion():
    W, H = 1400, 860
    b = markers([C['pwr'], C['sdr'], C['lora'], C['pi']])
    b += box(24, 150, 230, 120, '230 V · red', ['manguera H07RN-F 2 × 1 mm²', 'diferencial 30 mA', 'prensaestopas PG9', 'empalme WAGO 221 + anclaje'], C['pwr'], '#fdecea')
    b += box(330, 130, 280, 160, 'Cargador USB 45 W', ['multitoma, clase II, marcado CE', 'USB-C PD: 5 V 3 A (15 W)', 'USB-A: 5 V 2,4 A (12 W)', 'resto de puertos: reserva', '(compartimento de potencia)'], C['pwr'], '#fdecea')
    b += arrow(254, 210, 328, 210, C['pwr'], '230 V')
    b += box(720, 90, 300, 150, 'Raspberry Pi 5', ['+ HAT: RTL-SDR, SX1262, GPS, RTC', '+ cámara WPI408 + LED IR (CSI)', 'consumo 8–12 W', 'USB limitado a 0,6 A en total', '(PI5_USB_MAX_CURRENT="no")'], C['pi'], '#edf7ee')
    b += arrow(610, 170, 718, 170, C['pwr'], 'USB-C')
    b += box(720, 330, 300, 120, 'Hub USB 2.0 alimentado', ['«regleta USB energizada»', 'alimentado por el USB-A del cargador', 'consumo de lo que cuelga: ~6 W'], C['sdr'], '#eef4fb')
    b += arrow(610, 250, 718, 380, C['pwr'], 'USB-A 5 V')
    b += arrow(870, 330, 870, 242, C['sdr'], 'datos (upstream)', dash=True)
    dev = [('Mini RTL-SDR', '0,3 A', C['sdr']), ('RTL-SDR V3', '0,3 A', C['sdr']), ('FlightStick', '0,35 A', C['sdr']),
           ('LilyGO Meshtastic', '0,1 A (+TX)', C['lora']), ('LilyGO iGate', '0,1 A', C['lora'])]
    for i, (n, a, c) in enumerate(dev):
        y = 90 + i * 74
        b += box(1110, y, 260, 56, n, [a], c)
        b += arrow(1020, 390, 1108, y + 28, c)
    b += f"<text x='24' y='540' font-size='15' font-weight='bold' fill='{C['ink']}'>Presupuesto de potencia</text>"
    rows = [('Raspberry Pi 5 + HAT + cámara', 'USB-C PD', '8–12 W', '15 W'),
            ('3 RTL-SDR + 2 LilyGO (hub)', 'USB-A', '5–7 W', '12 W'),
            ('Total', '', '13–19 W', '45 W (≈ 40 %)')]
    xs = [24, 420, 640, 820]
    for j, t in enumerate(['Consumidor', 'Puerto', 'Típico', 'Disponible']):
        b += f"<text x='{xs[j]}' y='572' font-size='12.5' font-weight='bold' fill='{C['mute']}'>{t}</text>"
    for i, r in enumerate(rows):
        for j, t in enumerate(r):
            wgt = " font-weight='bold'" if i == 2 else ''
            b += f"<text x='{xs[j]}' y='{600 + i * 24}' font-size='13' fill='{C['ink']}'{wgt}>{esc(t)}</text>"
    notes = ['La Pi 5 solo negocia 5 A con la fuente oficial: con el cargador de 45 W arranca a 5 V 3 A y limita sus USB a 0,6 A.',
             'Por eso los SDR y los LilyGO van al hub alimentado; a la Pi solo llegan sus datos. El RTL del HAT se alimenta de la propia Pi.',
             'Cable USB-C de 3 A y lo más corto posible: si bricohams-check avisa de get_throttled ≠ 0x0, revisa cable y puerto.',
             'El SDRplay futuro irá al USB 3.0 de la Pi (0,2 A, cabe en el límite de 0,6 A).']
    for i, t in enumerate(notes):
        b += f"<text x='24' y='{700 + i * 22}' font-size='12.5' fill='{C['ink']}'>{esc(t)}</text>"
    return svg(W, H, b, 'Alimentación dentro de la caja (cargador USB de 45 W)')


def caja():
    Wc, Hc, T, PW = scad('W'), scad('H'), scad('T'), scad('PWR_W')
    k = 2.6                     # px por mm
    ox, oy = 60, 100
    W, H = int(ox + Wc * k + 520), int(oy + Hc * k + 240)

    def X(x): return ox + x * k

    def Y(y): return oy + (Hc - y) * k      # y de la caja hacia arriba

    def r(x, y, w, h, fill, stroke, label='', sub='', fs=12):
        s = f"<rect x='{X(x):.1f}' y='{Y(y + h):.1f}' width='{w * k:.1f}' height='{h * k:.1f}' rx='4' fill='{fill}' stroke='{stroke}' stroke-width='1.6'/>"
        if label:
            s += f"<text x='{X(x + w / 2):.1f}' y='{Y(y + h / 2) - (3 if sub else -4):.1f}' font-size='{fs}' text-anchor='middle' font-weight='bold' fill='{C['ink']}'>{esc(label)}</text>"
        if sub:
            s += f"<text x='{X(x + w / 2):.1f}' y='{Y(y + h / 2) + 13:.1f}' font-size='10.5' text-anchor='middle' fill='{C['mute']}'>{esc(sub)}</text>"
        return s
    b = f"<rect x='{X(0)}' y='{Y(Hc)}' width='{Wc * k}' height='{Hc * k}' rx='14' fill='#fafafa' stroke='{C['ink']}' stroke-width='3'/>"
    XP = T + PW
    b += r(T, T, PW, Hc - 2 * T, '#fdecea', C['pwr'])
    b += f"<text x='{X(T + PW / 2)}' y='{Y(Hc - 10)}' font-size='13' text-anchor='middle' font-weight='bold' fill='{C['pwr']}'>POTENCIA</text>"
    b += r(XP, T, scad('TP'), Hc - 2 * T, C['ink'], C['ink'])
    b += f"<text x='{X(XP + 40 + (Wc - XP) / 2 - 40)}' y='{Y(Hc - 10)}' font-size='13' text-anchor='middle' font-weight='bold' fill='{C['sdr']}'>ELECTRÓNICA</text>"
    # potencia (bajo la tapa interior)
    b += r(T + 2.5, 10, 65, 95, '#ffffff', C['pwr'], 'Cargador', 'USB 45 W')
    b += r(T + 15, 115, 40, 100, '#f1f1f1', C['gnd'])
    b += f"<text x='{X(T + 35):.1f}' y='{Y(200):.1f}' font-size='11.5' text-anchor='middle' font-weight='bold' fill='{C['ink']}'>Hub USB alimentado</text>"
    # LilyGO sobre la tapa interior (dibujados con trazo discontinuo)
    for i, n in enumerate(['Mesh', 'iGate']):
        x = T + 0.5 + 5 + i * 33 + 1.2
        b += f"<rect x='{X(x):.1f}' y='{Y(T + 0.5 + 118 + 1.2 + 65):.1f}' width='{27 * k:.1f}' height='{65 * k:.1f}' rx='3' fill='#e0f2f1' stroke='{C['lora']}' stroke-width='1.6' stroke-dasharray='5 3'/>"
        b += f"<text x='{X(x + 13.5):.1f}' y='{Y(T + 0.5 + 118 + 34):.1f}' font-size='11' text-anchor='middle' font-weight='bold' fill='{C['lora']}'>LilyGO</text>"
        b += f"<text x='{X(x + 13.5):.1f}' y='{Y(T + 0.5 + 118 + 34) + 14:.1f}' font-size='10.5' text-anchor='middle' fill='{C['lora']}'>{n}</text>"
    # pasos del tabique
    b += r(XP - 1, 176, 5, 18, C['or'], C['or'])
    b += r(XP - 1, 140, 5, 18, C['lora'], C['lora'])
    # electrónica (sobre la placa)
    pe = scad('XE') if False else XP + scad('TP') + 3.2
    b += r(pe, 6, 138, 210, '#fffde7', '#c9b458')
    for x, w, h, n in [(3, 26, 54, 'Mini'), (33, 26, 85, 'V3'), (63, 26, 85, 'Flight')]:
        b += r(pe + x, 22, w, h, '#e3f2fd', C['sdr'], n, '', 11)
    b += r(pe + 93, 22, 26, 50, '#eceff1', C['gnd'], 'Dipl.', '', 11)
    b += r(pe + 42, 147, 85, 56, '#e8f5e9', C['pi'], 'Pi 5 + HAT', 'SDR · LoRa · GPS · RTC')
    cx, cy = 160, 196
    b += f"<rect x='{X(cx - 38):.1f}' y='{Y(cy + 14):.1f}' width='{76 * k:.1f}' height='{28 * k:.1f}' rx='3' fill='none' stroke='#263238' stroke-width='2.2' stroke-dasharray='7 4'/>"
    b += f"<text x='{X(cx):.1f}' y='{Y(cy + 16):.1f}' font-size='11' text-anchor='middle' fill='#263238' font-weight='bold'>cámara WPI408 (en la tapa)</text>"
    # cara inferior
    labels = re.search(r'SMA_LABELS = \[([^\]]*)\]', SCAD).group(1).replace('"', '').replace(' ', '').split(',')
    pitch = scad('SMA_PITCH')
    xe = XP + scad('TP')
    x0 = xe + (Wc - T - xe) / 2 - (len(labels) - 1) * pitch / 2
    yb = oy + Hc * k + 26
    b += f"<text x='{ox}' y='{yb}' font-size='13' font-weight='bold' fill='{C['ink']}'>Cara inferior (vista desde delante): conectores de izquierda a derecha</text>"
    b += f"<rect x='{X(0)}' y='{yb + 12}' width='{Wc * k}' height='60' rx='8' fill='#f5f5f5' stroke='{C['ink']}' stroke-width='2'/>"
    b += f"<circle cx='{X(T + PW / 2)}' cy='{yb + 42}' r='{7.7 * k}' fill='#fff' stroke='{C['pwr']}' stroke-width='2'/><text x='{X(T + PW / 2)}' y='{yb + 46}' font-size='10' text-anchor='middle' fill='{C['pwr']}' font-weight='bold'>PG9 230V</text>"
    for i, n in enumerate(labels):
        x = X(x0 + i * pitch)
        b += f"<circle cx='{x:.1f}' cy='{yb + 34}' r='{3.3 * k:.1f}' fill='#ffd54f' stroke='#8d6e00' stroke-width='1.5'/>"
        b += f"<text x='{x:.1f}' y='{yb + 64}' font-size='10.5' text-anchor='middle' font-weight='bold' fill='{C['ink']}'>{esc(n)}</text>"
    b += f"<text x='{ox}' y='{yb + 100}' font-size='12' fill='{C['mute']}'>2.ª fila: prensaestopas PG7 «WX» (BME280), M20 «LAN» (Ethernet) y rejillas de entrada. Las rejillas de salida van en el techo, bajo el tejadillo.</text>"
    # leyenda
    lx = int(X(Wc) + 40)
    items = [('#fdecea', C['pwr'], 'Potencia: 230 V bajo la tapa interior'), ('#e0f2f1', C['lora'], 'LilyGO sobre la tapa interior'),
             (C['or'], C['or'], 'Pasamuros TPU: cables USB'), (C['lora'], C['lora'], 'Muesca: coaxiales 433'),
             ('#fffde7', '#c9b458', 'Placa de electrónica'), ('#e3f2fd', C['sdr'], 'Dongles RTL-SDR'), ('#e8f5e9', C['pi'], 'Pi 5 + HAT')]
    for i, (f, st, t) in enumerate(items):
        y = oy + 10 + i * 34
        b += f"<rect x='{lx}' y='{y}' width='26' height='20' rx='3' fill='{f}' stroke='{st}' stroke-width='1.6'/><text x='{lx + 36}' y='{y + 15}' font-size='12.5' fill='{C['ink']}'>{esc(t)}</text>"
    dims = ['Cuerpo: %d × %d × %d mm (+ orejetas: %d mm de ancho)' % (Wc, Hc, scad('D'), Wc + 2 * scad('EAR_L')),
            'Paredes de %.1f mm · junta TPU en ranura · 8 tornillos M4' % T,
            'Mástil Televés Ø%d mm: 2 sillas en V + abrazaderas' % scad('MAST_D'),
            'PETG blanco + TPU 95A · Anycubic Kobra S1',
            'Vista frontal con la tapa quitada', 'Fuente: hardware/caja/caja_bricohams.scad']
    for i, t in enumerate(dims):
        b += f"<text x='{lx}' y='{oy + 290 + i * 22}' font-size='12' fill='{C['ink']}'>{esc(t)}</text>"
    return svg(W, H, b, 'Caja de intemperie: distribución interior y conectores')

# ---------------------------------------------------------------------
#  v3: conexiones completas
# ---------------------------------------------------------------------
def linea(x1, y1, x2, y2, c=None, w=2, dash=False):
    d = " stroke-dasharray='6 4'" if dash else ''
    return f"<line x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}' stroke='{c or C['ink']}' stroke-width='{w}'{d}/>"


def txt(x, y, t, s=11, c=None, b=False, a='start'):
    return f"<text x='{x}' y='{y}' font-size='{s}' fill='{c or C['ink']}'{' font-weight=\"bold\"' if b else ''} text-anchor='{a}'>{esc(t)}</text>"


def caja_s(x, y, w, h, t, sub='', c=None, fill='#f7f9fb', arriba=False):
    c = c or C['ink']
    s = f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='6' fill='{fill}' stroke='{c}' stroke-width='1.8'/>"
    if arriba:
        s += txt(x + w / 2, y + 20, t, 11.5, c, True, 'middle')
        if sub:
            s += txt(x + w / 2, y + 36, sub, 9.5, C['mute'], False, 'middle')
        return s
    s += txt(x + w / 2, y + (h / 2 if not sub else h / 2 - 4), t, 11.5, c, True, 'middle')
    if sub:
        s += txt(x + w / 2, y + h / 2 + 11, sub, 9.5, C['mute'], False, 'middle')
    return s


def rf_completo():
    W, H = 1500, 1020
    b = markers([C['rf'], C['pwr']])
    cols = [24, 250, 470, 640, 850, 1080, 1290]
    for x, t in zip(cols, ['ANTENA (mástil)', 'EN LA ANTENA', 'BAJADA (~7 m)', 'PASAMUROS', 'DENTRO DE LA CAJA', 'RECEPTOR', 'ALIMENTACIÓN DC']):
        b += txt(x, 92, t, 12, C['ink'], True)
    filas = [
        ('Eggbeater 2 m/70', 'LNA 2 m/70 (proyecto)', 'RG-213 / H155', 'N «SAT»', 'pigtail N–SMA', 'RTL del HAT', 'bias-tee del HAT 5 V'),
        ('Quad 2 m/70 (2 feeds)', 'diplexor 2 m/70 (proyecto)', 'H155 / LMR-240', 'N «HAM»', 'pigtail N–SMA', 'Mini RTL-SDR', '—'),
        ('Discone grande', '—', 'H155 / LMR-240', 'N «VHF»', 'diplexor HF/VHF · entrada VHF', 'RTL-SDR V3', '—'),
        ('Lazo MLA-30', 'amplificador del lazo', 'RG-58 (10 m del kit)', 'N «HF»', 'inyector MLA-30 → diplexor HF', '(mismo V3)', 'inyector 12 V (USB del hub)'),
        ('ADS-B λ/4', 'LNA 1090 (20,5 dB)', 'LMR-400 / Hyperflex 5', 'N «ADSB»', 'bias-tee 5 V → pigtail', 'FlightStick', 'bias-tee: 5 V del hub'),
        ('Bigsignal 868', '—', 'H155 / LMR-240', 'N «868»', '[filtro SAW 868 solo RX*]', 'SX1262 del HAT', '—'),
        ('GPS activa', '—', 'RG-58 del GPS', 'N «GPS»', 'pigtail N–SMA/u.FL', 'GPS del HAT', '3,3–5 V del HAT'),
        ('Fibra 433 (Meshtastic)', '—', 'H155 / LMR-240', 'N «M433»', 'pigtail', 'LilyGO Meshtastic', '—'),
        ('Bigsignal 433 (iGate)', '—', 'H155 / LMR-240', 'N «IG433»', 'filtro FBP-433s', 'LilyGO iGate', '—'),
        ('Discone compacta (futuro)', '—', 'H155', 'N «DISC2»', 'pigtail', 'bahía de expansión', '—'),
    ]
    for i, f in enumerate(filas):
        y = 108 + i * 72
        for j, (x, t) in enumerate(zip(cols, f)):
            w = 200 if j != 4 else 210
            c = C['rf'] if j == 0 else C['sdr'] if j == 5 else C['pwr'] if j == 6 and t != '—' else C['line']
            b += f"<rect x='{x}' y='{y}' width='{w}' height='46' rx='5' fill='#fff' stroke='{c}' stroke-width='1.4'/>"
            b += txt(x + 8, y + 28, t, 10.5)
            if j < 5:
                b += f"<line x1='{x + w}' y1='{y + 23}' x2='{cols[j + 1]}' y2='{y + 23}' stroke='{C['rf']}' stroke-width='1.6' marker-end='url(#a{C['rf'][1:]})'/>"
    notas = ['* El filtro SAW de 868 aguanta ~18 dBm: no va en el camino de TX del HAT (22 dBm). Úsalo solo si mides bloqueo por LTE800 y entonces baja lora.tx_power a 17 dBm.',
             'Coaxiales: N macho en ambos extremos; en la caja, pasamuros N hembra y latiguillo N macho–SMA macho RG-316 de 20 cm hasta cada receptor.',
             'Pérdida en 7 m a 1090 MHz: RG-58 ≈ 4 dB · H155 ≈ 1,8 dB · LMR-400 ≈ 1,6 dB. Por eso el LNA de 1090 va en la antena y no en la caja.',
             'Bias-tee: corta la continua hacia el receptor. Nunca conectes un receptor con bias-tee activo a una antena sin LNA (cortocircuito en continua).']
    for k, t in enumerate(notas):
        b += txt(24, 850 + k * 22, t, 11.5)
    return svg(W, H, b, 'Cadena de RF completa: de cada antena a su receptor')


def ventiladores():
    W, H = 1400, 880
    b = markers([C['pwr']])
    # Raspberry
    b += caja_s(40, 100, 230, 390, 'Raspberry Pi 5', 'cabecera de 40 pines', C['pi'], '#edf7ee', arriba=True)
    pines = [('pin 32 · GPIO12 (PWM0 c0)', 170), ('pin 33 · GPIO13 (PWM0 c1)', 220), ('pin 15 · GPIO22 (tacómetro 1)', 290),
             ('pin 29 · GPIO5 (tacómetro 2)', 340), ('pin 7 · GPIO4 (1-Wire)', 410), ('pin 1 · 3V3', 450), ('pin 39 · GND', 470)]
    for t, y in pines:
        b += txt(260, y, t, 10.5, C['ink'], False, 'end')
        b += linea(270, y - 4, 330, y - 4, C['ink'], 1.5)
    # driver PWM con 2N7002 (uno por ventilador)
    for k, (y, nom) in enumerate(((166, 'ENTRADA (abajo izq.)'), (216, 'SALIDA (arriba dcha.)'))):
        x = 340 + k * 0
        yb = 130 + k * 170
        b += caja_s(500, yb, 230, 120, 'Q%d · 2N7002 (o BSS138)' % (k + 1), 'G ← 1 kΩ ← GPIO · 100 kΩ G–S · S a GND', C['spi'])
        b += linea(330, y, 500, yb + 40, C['spi'], 1.5)
        b += caja_s(840, yb, 270, 120, 'Ventilador %d · 60 mm 12 V PWM' % (k + 1), nom, C['sdr'], '#eef4fb')
        b += linea(730, yb + 60, 840, yb + 60, C['spi'], 1.8)
        b += txt(785, yb + 54, 'D → PWM (azul)', 10, C['spi'], False, 'middle')
        for j, (t, c) in enumerate((('negro · GND', C['gnd']), ('amarillo · +12 V', C['pwr']), ('verde · TACH', C['uart']), ('azul · PWM', C['spi']))):
            b += txt(1120, yb + 26 + j * 22, t, 10.5, c)
    b += linea(330, 286, 1180, 286, C['uart'], 1.5, True); b += linea(1180, 286, 1180, 196, C['uart'], 1.5, True)
    b += linea(330, 336, 470, 336, C['uart'], 1.5, True); b += linea(470, 336, 470, 440, C['uart'], 1.5, True)
    b += linea(470, 440, 1180, 440, C['uart'], 1.5, True); b += linea(1180, 440, 1180, 366, C['uart'], 1.5, True)
    b += txt(560, 278, 'TACH 1 (verde) → GPIO22 · pull-up 10 kΩ a 3V3 (pin 1) + 1 kΩ en serie', 10, C['uart'])
    b += txt(560, 456, 'TACH 2 (verde) → GPIO5 · igual', 10, C['uart'])
    # DS18B20
    b += caja_s(500, 500, 230, 90, 'DS18B20 (interior de la caja)', 'DQ ← GPIO4 · 4,7 kΩ DQ–3V3', C['i2c'])
    b += linea(330, 406, 500, 545, C['i2c'], 1.5)
    # 12 V
    b += caja_s(840, 520, 270, 80, 'Bus 12 V (WAGO) · fusible 1 A', 'del gatillo USB-C PD del módulo de potencia', C['pwr'], '#fdecea')
    b += linea(975, 520, 975, 430, C['pwr'], 2); b += linea(975, 300, 975, 250, C['pwr'], 2, True)
    b += txt(990, 470, '+12 V a los dos ventiladores', 10, C['pwr'])
    notas = ['• El 2N7002 invierte la señal (GPIO alto → PWM a masa): por eso FAN_PWM_INVERT="yes". Sin MOSFET (PWM directo con 3,3 V, admitido por casi todos los ventiladores de 4 hilos): FAN_PWM_INVERT="no".',
             '• Masa común: el GND de la Pi y el negativo del bus de 12 V tienen que estar unidos (en el WAGO de masa).',
             '• PWM por hardware a 25 kHz: dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4 (lo escribe el instalador). Si no aparece pwmchip, bricohams-fan usa PWM por software (lgpio).',
             '• Curva: arrancan con la caja a 35 °C o la CPU a 55 °C (30 %); al 100 % con 45 °C / 75 °C; histéresis de 3 °C. Golpe al 100 % al arrancar desde parado.',
             '• Alarma: si el ciclo es ≥ 40 % y un tacómetro marca < 300 rpm, bricohams-check y la web (tarjeta METEO) avisan del ventilador parado.',
             '• Flujo: entra abajo a la izquierda con filtro de malla y sale arriba a la derecha; las dos bocas tienen capota impresa con la abertura hacia abajo.']
    for k, t in enumerate(notas):
        b += txt(40, 660 + k * 26, t, 11.2)
    return svg(W, H, b, 'Ventilación de la caja: conexión y control desde la Raspberry')


def sensores_wx():
    W, H = 1400, 860
    b = markers([C['line']])
    b += caja_s(40, 100, 250, 420, 'Raspberry Pi 5', 'I2C · GPIO · USB', C['pi'], '#edf7ee', arriba=True)
    for t, y in (('pin 1 · 3V3', 170), ('pin 3 · SDA1', 200), ('pin 5 · SCL1', 230), ('pin 9 · GND', 260), ('pin 11 · GPIO17', 330), ('pin 14 · GND', 360), ('USB (hub)', 450)):
        b += txt(280, y, t, 10.5, C['ink'], False, 'end'); b += linea(290, y - 4, 360, y - 4, C['ink'], 1.4)
    b += caja_s(560, 130, 260, 120, 'BME280 en la garita', 'cable apantallado 4 hilos ≤ 5 m, PG7 «WX»', C['i2c'])
    b += linea(360, 196, 560, 190, C['i2c'], 1.8)
    b += txt(450, 182, 'VIN, SDA, SCL, GND', 10, C['i2c'], False, 'middle')
    b += caja_s(560, 290, 260, 110, 'Pluviómetro (reed)', 'Misol WH-SP-RG · 0,2794 mm/vuelco', C['sdr'])
    b += linea(360, 326, 560, 330, C['sdr'], 1.8); b += linea(360, 356, 560, 370, C['gnd'], 1.8)
    b += txt(450, 318, 'GPIO17 · pull-up 10 kΩ + 100 nF a GND', 10, C['sdr'], False, 'middle')
    b += caja_s(560, 430, 260, 110, 'Adaptador USB-RS485', 'CH340 → /dev/rs485 (udev)', C['uart'])
    b += linea(360, 446, 560, 480, C['uart'], 1.8)
    b += caja_s(980, 380, 300, 90, 'Anemómetro RS485', 'Modbus dirección 1 · 4800 8N1', C['net'])
    b += caja_s(980, 500, 300, 90, 'Veleta RS485', 'Modbus dirección 2 · 0–7 × 45°', C['net'])
    for y in (425, 545):
        b += linea(820, 485, 980, y, C['uart'], 1.6)
    b += txt(830, 470, 'A+ amarillo · B− azul · GND negro', 10, C['uart'])
    b += caja_s(980, 620, 300, 80, 'Bus 12 V (WAGO) · fusible 1 A', 'alimenta los sensores de viento (10–30 V)', C['pwr'], '#fdecea')
    b += linea(1130, 620, 1130, 590, C['pwr'], 2)
    b += txt(1145, 610, 'marrón +12 V · negro GND', 10, C['pwr'])
    notas = ['• Un solo cable de 4 hilos (PG7 «VIENTO») lleva +12 V, GND, A y B a los dos sensores, conectados en paralelo (bus RS485).',
             '• La veleta sale de fábrica con la dirección 1, igual que el anemómetro: cámbiala a 2 antes de instalarla (manual 19).',
             '• El pluviómetro solo cierra un contacto: dos hilos al PG7 «LLUVIA». El condensador de 100 nF y el antirrebote de 20 ms evitan dobles cuentas.',
             '• bricohams-wx publica en APRS-IS (N0CALL-13): dirección, velocidad media de 1 min, racha de 5 min, lluvia de 1 h, 24 h y desde medianoche.',
             '• Alternativa: los mismos sensores en un 3.er LilyGO con el firmware LoRa_APRS_Wx_Station de CA2RXU (bricohams-lilygo wxstation): emite por LoRa a 433,775.']
    for k, t in enumerate(notas):
        b += txt(40, 720 + k * 24, t, 11.2)
    return svg(W, H, b, 'Estación meteorológica: BME280, viento RS485 y pluviómetro')


def alimentacion_v3():
    W, H = 1400, 900
    b = markers([C['pwr'], C['sdr'], C['pi']])
    b += caja_s(30, 140, 190, 90, '230 V · red', 'diferencial 30 mA · H07RN-F', C['pwr'], '#fdecea')
    b += caja_s(270, 110, 250, 150, 'MÓDULO DE POTENCIA', 'base Schuko + cargador USB 120 W', C['pwr'], '#fdecea')
    b += arrow(220, 185, 268, 185, C['pwr'], 'PG9')
    b += caja_s(600, 90, 220, 70, 'USB-C 1 (PD)', '5 V 3 A → Raspberry Pi 5', C['pi'])
    b += caja_s(600, 190, 220, 70, 'USB-C 2 + gatillo PD', '12 V (hasta 5 A)', C['pwr'])
    b += caja_s(600, 290, 220, 60, 'USB-A', 'reserva', C['line'])
    for y in (125, 225, 320):
        b += arrow(520, 185, 598, y, C['pwr'])
    b += caja_s(900, 90, 230, 70, 'Raspberry Pi 5 + HAT', '+ cámara · ~8–12 W', C['pi'], '#edf7ee')
    b += arrow(820, 125, 898, 125, C['pi'], 'M25')
    b += caja_s(900, 190, 230, 80, 'Bus 12 V (WAGO 221)', 'portafusibles de cuchilla', C['pwr'], '#fdecea')
    b += arrow(820, 225, 898, 225, C['pwr'], 'M25')
    cargas = [('2 ventiladores 60 mm', 'fusible 1 A', 320), ('Viento RS485 (10–30 V)', 'fusible 1 A', 410), ('Regleta USB Vansuny', '12 V 2 A · fusible 2 A', 500)]
    for t, f, y in cargas:
        b += caja_s(1160, y - 30, 220, 70, t, f, C['pwr'])
        b += arrow(1015, 270, 1158, y, C['pwr'])
    b += caja_s(1120, 600, 270, 230, 'Regleta USB Vansuny (USB 3.0)', '', C['sdr'], '#eef4fb', arriba=True)
    for k, t in enumerate(['Mini RTL-SDR', 'RTL-SDR V3', 'FlightStick', 'LilyGO Meshtastic', 'LilyGO iGate', 'adaptador USB-RS485',
                           'inyector MLA-30 (5 V → 12 V)', 'bias-tee LNA 1090 (5 V)']):
        b += txt(1135, 650 + k * 22, '• ' + t, 10.5)
    b += arrow(1270, 540, 1270, 598, C['pwr'])
    b += linea(1015, 160, 1015, 180, C['sdr'], 1.6, True)
    b += linea(1130, 140, 1395, 140, C['sdr'], 1.6, True); b += linea(1395, 140, 1395, 598, C['sdr'], 1.6, True)
    b += txt(1390, 132, 'datos USB 3.0 (upstream de la regleta a la Pi)', 9.5, C['sdr'], False, 'end')
    filas = [('Raspberry Pi 5 + HAT + cámara', 'USB-C PD 5 V', '8–12 W', '15 W'), ('Regleta: 3 SDR + 2 LilyGO + RS485 + LNA + MLA-30', '12 V (regleta)', '7–9 W', '24 W'),
             ('2 ventiladores', '12 V', '0–2 W', '—'), ('Viento RS485', '12 V', '< 1 W', '—'), ('Total', '', '16–24 W', '120 W (20 %)')]
    b += txt(30, 420, 'Presupuesto', 13, C['ink'], True)
    for i, f in enumerate(filas):
        for j, t in enumerate(f):
            b += txt([30, 420, 560, 680][j] - (0 if j else 0), 448 + i * 22, t, 10.5, C['ink'], i == 4)
    notas = ['• Un solo cable de red, una sola fuente: el cargador de 120 W da el USB-C de la Pi y, con un gatillo USB-C PD fijado a 12 V, todo el bus de 12 V.',
             '• El alimentador FX24E-120200C (12 V 2 A) de la regleta Vansuny queda como repuesto: no hace falta un segundo transformador de 230 V.',
             '• La Pi negocia 5 A solo con su fuente oficial: con el cargador arranca a 5 V 3 A y limita sus USB a 0,6 A. Todo lo USB va a la regleta alimentada.',
             '• Masa común entre el bus de 12 V y la Pi (por el USB). Fusibles de cuchilla en cada derivación de 12 V.']
    for k, t in enumerate(notas):
        b += txt(30, 590 + k * 24, t, 10.8)
    return svg(W, H, b, 'Alimentación v3: módulo de potencia → módulo de electrónica')


# ---------------------------------------------------------------------
#  v4
# ---------------------------------------------------------------------
def pico_io():
    """Esquema 16: Raspberry Pi Pico «bricohams-io» por USB (la cabecera de la Pi la ocupa el HAT)."""
    W, H = 1500, 1000
    b = markers([C['pwr']])
    b += caja_s(40, 90, 260, 120, 'Raspberry Pi 5 + HAT', 'la cabecera de 40 pines la usa el HAT', C['pi'], '#edf7ee')
    b += caja_s(40, 260, 260, 80, 'Regleta USB Vansuny', 'alimentada por el bus de 12 V', C['sdr'], '#eef4fb')
    b += linea(170, 210, 170, 260, C['sdr'], 3)
    b += txt(180, 240, 'USB 3.0 (datos)', 10, C['sdr'])
    # Pico
    px, py = 420, 160
    b += caja_s(px, py, 300, 560, 'Raspberry Pi Pico «bricohams-io»', 'MicroPython · /dev/bricohams-io (2e8a:0005)', C['or'], '#fff3e0', arriba=True)
    b += linea(300, 300, px, 300, C['sdr'], 3)
    b += txt(310, 292, 'cable micro-USB (datos + 5 V)', 10, C['sdr'])
    pines = [('GP4 · pin 6 · SDA (I2C0)', 240, C['i2c']), ('GP5 · pin 7 · SCL (I2C0)', 270, C['i2c']),
             ('GP22 · pin 29 · 1-Wire', 330, C['i2c']), ('GP15 · pin 20 · pluviómetro', 390, C['net']),
             ('GP16 · pin 21 · PWM ventilador 1', 460, C['spi']), ('GP17 · pin 22 · PWM ventilador 2', 490, C['spi']),
             ('GP18 · pin 24 · TACH 1', 550, C['uart']), ('GP19 · pin 25 · TACH 2', 580, C['uart']),
             ('3V3(OUT) · pin 36', 640, C['pwr']), ('GND · pin 38 (y 3, 8, 13…)', 670, C['gnd'])]
    for t, y, c in pines:
        b += txt(px + 290, y, t, 10.5, c, False, 'end')
        b += linea(px + 300, y - 4, px + 360, y - 4, c, 1.6)
    b += txt(px + 366, 640, '→ VIN del BME280, VDD del DS18B20 y pull-ups', 9.5, C['pwr'])
    b += txt(px + 366, 670, '→ masa común (sensores, MOSFET y bus de 12 V)', 9.5, C['gnd'])
    # BME280
    b += caja_s(860, 200, 270, 90, 'BME280 / BMP280 (garita)', 'VIN 3V3 · GND · SDA · SCL · cable ≤ 5 m', C['i2c'], '#edf7ee')
    b += linea(780, 236, 860, 236, C['i2c'], 1.6); b += linea(780, 266, 860, 266, C['i2c'], 1.6)
    # DS18B20
    b += caja_s(860, 310, 270, 70, 'DS18B20 (aire de la caja)', 'DQ · 4,7 kΩ entre DQ y 3V3', C['i2c'], '#edf7ee')
    b += linea(780, 326, 860, 340, C['i2c'], 1.6)
    # pluviómetro
    b += caja_s(860, 395, 270, 70, 'Pluviómetro (reed)', '10 kΩ a 3V3 + 100 nF a GND · otro hilo a GND', C['net'], '#e0f2f1')
    b += linea(780, 386, 860, 425, C['net'], 1.6)
    # MOSFET y ventiladores
    for k, yb in enumerate((470, 620)):
        b += caja_s(860, yb, 230, 110, 'Q%d · 2N7002 (o BSS138)' % (k + 1), 'G ← 1 kΩ ← GP%d · 100 kΩ G–S · S a GND' % (16 + k), C['spi'])
        b += linea(780, (456, 486)[k], 860, yb + 40, C['spi'], 1.5)
        b += caja_s(1180, yb, 280, 110, 'Ventilador %d · 60 mm 12 V PWM' % (k + 1), ('ENTRADA (abajo izq.)', 'SALIDA (arriba dcha.)')[k], C['sdr'], '#eef4fb')
        b += linea(1090, yb + 55, 1180, yb + 55, C['spi'], 1.8)
        b += txt(1135, yb + 48, 'D → PWM azul', 9.5, C['spi'], False, 'middle')
    b += linea(780, 546, 840, 546, C['uart'], 1.5, True); b += linea(840, 546, 840, 600, C['uart'], 1.5, True)
    b += linea(840, 600, 1470, 600, C['uart'], 1.5, True); b += linea(1470, 600, 1470, 560, C['uart'], 1.5, True)
    b += linea(780, 576, 820, 576, C['uart'], 1.5, True); b += linea(820, 576, 820, 750, C['uart'], 1.5, True)
    b += linea(820, 750, 1470, 750, C['uart'], 1.5, True); b += linea(1470, 750, 1470, 710, C['uart'], 1.5, True)
    b += txt(1140, 616, 'TACH verde → GP18 · 10 kΩ a 3V3 + 1 kΩ en serie', 9.5, C['uart'], False, 'middle')
    b += txt(1140, 766, 'TACH verde → GP19 · igual', 9.5, C['uart'], False, 'middle')
    b += caja_s(1180, 790, 280, 70, 'Bus 12 V (WAGO) · fusible 1 A', '+12 V amarillo a los dos ventiladores', C['pwr'], '#fdecea')
    notas = ['• El GND del bus de 12 V, el de la Pico y el de los ventiladores tienen que estar unidos (masa común en el WAGO de masa).',
             '• La Pico NO admite 5 V en sus pines: tacómetro y PWM siempre con las resistencias / el MOSFET del esquema.',
             '• Firmware: firmware/pico-io/main.py (MicroPython). Grabar: BOOTSEL + UF2 de MicroPython, después «sudo bricohams-io instalar».',
             '• Seguridad: si la Pi deja de mandar órdenes 60 s, la Pico pone los ventiladores al 100 % ella sola.']
    for k, t in enumerate(notas):
        b += txt(40, 890 + k * 24, t, 11.2)
    return svg(W, H, b, 'Puente USB «bricohams-io»: sensores y ventiladores en una Raspberry Pi Pico')


def filtros_lna():
    """Esquema 17: dónde va cada filtro, el LNA de ADS-B y los bias-tee."""
    W, H = 1500, 900
    b = markers([C['rf'], C['pwr']])
    filas = [
        ('Bigsignal 433 (iGate)', 'pasamuros N «IG433»', 'FBP-433s (430–438 MHz, 1 W)', 'LilyGO iGate (solo RX)', C['lora']),
        ('Fibra 433 (Meshtastic)', 'pasamuros N «M433»', 'sin filtro (TX 20 dBm; ver manual 16)', 'LilyGO Meshtastic 433', C['lora']),
        ('Bigsignal 868 (Meshtastic)', 'pasamuros N «868»', 'sin filtro (TX 22 dBm > SAW 18 dBm)', 'SX1262 del HAT', C['lora']),
        ('Plano de tierra 1090 + LNA en la base', 'pasamuros N «ADSB»', 'bias-tee 5 V (RF+DC ← · → RF · DC ← USB)', 'FlightStick RadarBox', C['sdr']),
        ('Eggbeater 2 m/70 cm + LNA', 'pasamuros N «SAT»', 'bias-tee del propio HAT (SAT_BIAS_TEE=yes)', 'RTL-SDR del HAT', C['rf']),
        ('Quad 2 m/70 cm + diplexor (cabecera)', 'pasamuros N «HAM»', '—', 'Mini RTL-SDR', C['rf']),
        ('Lazo MLA-30 + discone grande', 'N «HF» y N «VHF»', 'inyector MLA-30 (12 V) + diplexor HF/VHF', 'RTL-SDR V3', C['rf']),
    ]
    xs = [40, 380, 640, 1080]
    for k, (a, n, f, r, c) in enumerate(filas):
        y = 100 + k * 100
        b += caja_s(xs[0], y, 300, 64, a, '', c, '#f3e5f5')
        b += caja_s(xs[1], y, 220, 64, n, 'coaxial LMR-400 / H155', C['cam'])
        b += caja_s(xs[2], y, 400, 64, f, '', C['pwr'] if 'bias' in f or 'inyector' in f else C['ink'], '#fdecea' if ('bias' in f or 'inyector' in f) else '#f7f9fb')
        b += caja_s(xs[3], y, 360, 64, r, '', C['sdr'], '#eef4fb')
        for x1, x2 in ((340, 380), (600, 640), (1040, 1080)):
            b += arrow(x1, y + 32, x2, y + 32, C['rf'])
    notas = ['• FBP-433s atornillado directo al pasamuros N por dentro (adaptador N macho–SMA hembra) y apoyado en «clip_filtro»; latiguillo SMA de 20 cm al LilyGO.',
             '• Bias-tee de ADS-B: el LNA admite 5 V como máximo. Nunca conectar el bias-tee a una antena sin LNA (cortocircuito de continua).',
             '• FBP-868s: solo en recepción y solo si hay bloqueo por LTE800 (nunca en la TX de 22 dBm del HAT).']
    for k, t in enumerate(notas):
        b += txt(40, 820 + k * 24, t, 11.2)
    return svg(W, H, b, 'Filtros, preamplificadores y bias-tee: de cada antena a su receptor')


def red_servicios():
    """Esquema 18: servicios web, SSL, MQTT, Telegram y tareas automáticas."""
    W, H = 1500, 900
    b = markers([C['net'], C['ink'], C['or'], C['pi'], C['sdr']])
    b += caja_s(40, 110, 220, 70, 'Internet (oyentes)', 'http(s)://SSL_DOMAIN', C['net'], '#e0f2f1')
    b += caja_s(40, 240, 220, 80, 'Router de casa', 'abrir SOLO 80 y 443 TCP', C['cam'])
    b += arrow(150, 180, 150, 240, C['net'], 'HTTP + HTTPS')
    b += caja_s(360, 210, 260, 140, 'nginx · SSL_MODO=admin', '', C['or'], '#fff3e0', arriba=True)
    b += txt(490, 262, 'HTTP :80  → receptor público', 10.5, C['ink'], False, 'middle')
    b += txt(490, 282, 'HTTPS :443 → /login, /settings…', 10.5, C['cr'], True, 'middle')
    b += txt(490, 302, '(http://…/settings → 301 https)', 10, C['mute'], False, 'middle')
    b += txt(490, 322, 'cookie owrx-session: Secure', 10, C['mute'], False, 'middle')
    b += arrow(260, 280, 360, 280, C['net'])
    dest = [('/  → OpenWebRX+ 127.0.0.1:8073', 120, C['pi']), ('/tar1090/ → lighttpd 127.0.0.1:8504', 200, C['sdr']),
            ('/camara/ → MediaMTX HLS 127.0.0.1:8888', 280, C['cam']), ('/bricohams/ → portal y privacidad', 360, C['ink']),
            ('/bricohams/api/ → bricohams-api 127.0.0.1:8075', 440, C['ink'])]
    for t, y, c in dest:
        b += caja_s(760, y - 30, 420, 56, t, '', c)
        b += arrow(620, 280, 760, y - 2, C['ink'], w=1.5)
    b += caja_s(760, 520, 420, 70, 'mosquitto 127.0.0.1:1883', 'tema openwebrx/CLIENT (conexiones y chat)', C['net'], '#e0f2f1')
    b += linea(1180, 118, 1240, 118, C['ink'], 1.5, True); b += linea(1240, 118, 1240, 555, C['ink'], 1.5, True)
    b += arrow(1240, 555, 1180, 555, C['net'], 'MQTT')
    b += caja_s(760, 640, 420, 70, 'bricohams-visitas', 'GeoIP local · IP truncada · visitas.json para la web', C['or'], '#fff3e0')
    b += arrow(970, 590, 970, 640, C['net'])
    b += caja_s(1250, 640, 210, 70, 'Telegram', 'grupo de operadores', C['sdr'], '#eef4fb')
    b += arrow(1180, 675, 1250, 675, C['sdr'], 'avisos')
    b += caja_s(40, 520, 560, 190, 'cron · cuenta de servicio «bricohams»', '', C['pi'], '#edf7ee', arriba=True)
    for k, t in enumerate(['04:30 copia diaria', 'lunes 03:30 apt update + upgrade', 'lunes 05:00 reinicio preventivo (se aplaza si hay pase)',
                           'cada 30 min bricohams-check → Telegram si falla', '21:00 resumen de visitas · día 2: GeoIP']):
        b += txt(60, 580 + k * 24, '• ' + t, 11)
    b += txt(60, 700, 'sudo -n /usr/local/sbin/bricohams-tarea <verbo>  (sudoers: solo ese programa, sin contraseña)', 10, C['mute'])
    b += arrow(600, 675, 760, 675, C['pi'])
    b += txt(40, 780, '• Desde casa sigue funcionando http://IP:8073 sin nginx (la ficha DMR/YSF y el portal necesitan nginx).', 11.2)
    b += txt(40, 828, '• v4.2: el certificado protege la administración; SSL_MODO=todo pone todo en HTTPS y SSL_MODO=no lo quita (solo LAN).', 11.2)
    b += txt(40, 804, '• Solo LAN: Meshtastic Web https://IP:8443 (admin), API 4403, RTSP 8554. No abrir esos puertos en el router.', 11.2)
    return svg(W, H, b, 'Servicios web, SSL (solo administración), visitas y tareas automáticas')


def actualizar():
    """Esquema 19: install.sh --actualizar (v4.1)."""
    W, H = 1500, 930
    b = markers([C['ink'], C['or'], C['pi'], C['sdr'], C['cr']])
    pasos = [('1 · Kit (git)', 'git pull --ff-only como el dueño del kit', 'install.sh nuevo → se relanza (--continuar)', C['sdr'], '#eef4fb'),
             ('2 · bricohams.env', 'añade las variables nuevas del .example', 'nunca cambia las tuyas ni tus claves', C['or'], '#fff3e0'),
             ('3 · Copia', 'bricohams-backup → /var/backups/bricohams', 'si falla, no sigue', C['pi'], '#edf7ee'),
             ('4 · Sistema (apt)', 'apt update (IPv4 si hace falta) + upgrade', 'respeta lo retenido y tus .conf', C['cam'], '#eceff1'),
             ('5 · Plan de pasos', 'huella actual  ≠  huella guardada ?', 'solo esos pasos + comprobar + herramientas', C['cr'], '#fdecee'),
             ('6 · Pasos', 'paso_x … y guarda su huella', 'si se corta, se relanza y sigue', C['ink'], '#f7f9fb'),
             ('7 · Final', 'bricohams-check · Telegram', 'actualizaciones.log · ¿reiniciar?', C['pi'], '#edf7ee')]
    y = 90
    for k, (t, s1, s2, c, f) in enumerate(pasos):
        b += caja_s(40, y, 430, 82, t, '', c, f, arriba=True)
        b += txt(255, y + 52, s1, 10.5, C['ink'], False, 'middle') + txt(255, y + 70, s2, 10, C['mute'], False, 'middle')
        if k < len(pasos) - 1:
            b += arrow(255, y + 82, 255, y + 110, C['ink'])
        y += 110
    # huella
    b += caja_s(560, 90, 900, 300, 'Huella de cada paso · /var/lib/bricohams/kit-estado (600, sin valores)', '', C['cr'], '#fff', arriba=True)
    filas = [('código', 'declare -f paso_x | sha256', 'cambia el paso en install.sh', 'web → solo web'),
             ('ficheros', 'sha256 de los $FILES/… y $KIT/… que usa', 'plugin nuevo, firmware, plantilla…', 'htdocs/plugins → plugins'),
             ('variables', 'NOMBRE=valor de las que lee (configuracion: todas)', 'cambias bricohams.env', 'WX_APRS_COMMENT → sensor')]
    b += txt(590, 150, 'huella', 11, C['mute'], True) + txt(700, 150, 'cómo se calcula', 11, C['mute'], True)
    b += txt(1060, 150, 'cuándo cambia', 11, C['mute'], True) + txt(1280, 150, 'ejemplo', 11, C['mute'], True)
    for k, (a, c1, c2, c3) in enumerate(filas):
        yy = 185 + k * 52
        b += linea(580, yy - 22, 1440, yy - 22, C['line'], 1)
        b += txt(590, yy, a, 11.5, C['cr'], True) + txt(700, yy, c1, 10.5) + txt(1060, yy, c2, 10.5) + txt(1280, yy, c3, 10.5)
    b += txt(590, 355, 'Sin huellas (estación anterior a la v4.1): se aplican todos los pasos, igual que una instalación, sin perder nada.', 10.5, C['mute'])
    b += linea(560, 240, 515, 240, C['cr'], 1.5, True) + linea(515, 240, 515, 570, C['cr'], 1.5, True)
    b += arrow(515, 570, 472, 570, C['cr'], dash=True, w=1.5) + txt(522, 410, 'compara', 10.5, C['cr'])
    # marcadores
    b += caja_s(560, 440, 900, 230, 'Marcadores en tres vías (paso configuracion)', '', C['or'], '#fff', arriba=True)
    b += caja_s(600, 500, 230, 60, 'kit anterior', 'bookmarks.kit.json', C['mute'])
    b += caja_s(890, 500, 230, 60, 'actuales (web)', '/var/lib/openwebrx/bookmarks.json', C['ink'])
    b += caja_s(1180, 500, 230, 60, 'kit nuevo', 'files/openwebrx/bookmarks.json', C['sdr'])
    b += txt(1010, 600, 'resultado = kit nuevo (gana) + propios (actuales que no venían en el kit anterior)', 11, C['ink'], True, 'middle')
    b += txt(1010, 625, 'clave: frecuencia + modo · copia previa bookmarks.json.antes-FECHA', 10.5, C['mute'], False, 'middle')
    # opciones
    b += caja_s(560, 710, 900, 160, 'Órdenes', '', C['pi'], '#edf7ee', arriba=True)
    for k, t in enumerate(['sudo bash install.sh --actualizar --simular  →  ver qué haría, sin cambiar nada',
                           'sudo bash install.sh --actualizar  →  actualizar',
                           'opciones: --sin-git (kit copiado del zip) · --sin-apt · --todo (repite todos los pasos)',
                           'El cron semanal solo hace apt: bajar código y ejecutarlo como root, a mano (ADR-37).']):
        b += txt(590, 765 + k * 24, t, 11)
    return svg(W, H, b, 'Actualizar la estación: install.sh --actualizar')


def audio_navegador():
    """Esquema 20: plugins de audio en el navegador (v4.2)."""
    W, H = 1500, 760
    b = markers([C['ink'], C['or'], C['pi'], C['sdr'], C['cr'], C['net']])
    b += caja_s(30, 90, 300, 110, 'Raspberry Pi · OpenWebRX+', 'demodula y decodifica (FT8, DMR, APRS…)', C['pi'], '#edf7ee', arriba=True)
    b += txt(180, 172, 'el audio va comprimido al navegador', 10, C['mute'], False, 'middle')
    b += arrow(330, 145, 400, 145, C['net']) + txt(335, 135, 'websocket', 10, C['net'])
    b += caja_s(400, 80, 1070, 380, 'Navegador de CADA oyente (Web Audio API)', '', C['sdr'], '#f4f8fd', arriba=True)
    b += caja_s(420, 125, 150, 60, 'AudioWorklet', 'audioNode', C['ink'])
    etapas = [('2× pasa-altos', 'corte bajo'), ('2× pasa-bajos', 'corte alto'), ('notch manual', 'Hz · Q'), ('notch auto', 'sigue el pitido')]
    x = 600
    b += txt(x, 222, 'FILTRO · filtro_audio (orden 10)', 11.5, C['or'], True)
    for i, (t, sub) in enumerate(etapas):
        b += caja_s(x + i * 112, 125, 104, 60, t, sub, C['or'], '#fff3e0')
        if i:
            b += arrow(x + i * 112 - 8, 155, x + i * 112, 155, C['or'], w=1.5)
    b += arrow(570, 155, 600, 155, C['ink'])
    y2 = 270
    dsp = [('graves', '250 Hz'), ('medios', '1,2 kHz'), ('agudos', '3 kHz'), ('puerta', '−30 dB'), ('AGC', 'compresor'), ('compensa', '+dB'), ('limitador', '−1 dBFS')]
    b += txt(470, y2 + 92, 'DSP · dsp_audio (orden 20)', 11.5, C['cr'], True)
    for i, (t, sub) in enumerate(dsp):
        b += caja_s(470 + i * 118, y2, 108, 60, t, sub, C['cr'], '#fdecee')
        if i:
            b += arrow(470 + i * 118 - 10, y2 + 30, 470 + i * 118, y2 + 30, C['cr'], w=1.5)
    b += linea(1032, 185, 1032, 230, C['ink']) + linea(1032, 230, 525, 230, C['ink']) + arrow(525, 230, 525, y2, C['ink'])
    b += caja_s(1300, 380, 150, 60, 'volumen', 'gainNode', C['ink'])
    b += linea(1290, y2 + 30, 1375, y2 + 30, C['ink']) + arrow(1375, y2 + 30, 1375, 380, C['ink'])
    b += caja_s(1300, 470, 150, 50, 'altavoz', '', C['pi'], '#edf7ee')
    b += arrow(1375, 440, 1375, 470, C['ink'])
    b += txt(420, 420, 'audio_cadena: mete las etapas ACTIVAS entre audioNode y volumen, por orden. Todo apagado = audio original.', 11)
    b += txt(420, 442, 'Mover un deslizador solo cambia parámetros (sin recablear, sin chasquidos).', 11, C['mute'])
    b += caja_s(30, 520, 1180, 190, 'Lo que NO cambia', '', C['mute'], '#fafafa', arriba=True)
    for k, t in enumerate(['La Raspberry no hace nada más: cada oyente procesa su propio audio en su navegador.',
                           'Los demás oyentes oyen lo suyo: los ajustes se guardan en el navegador de cada uno (localStorage).',
                           'Los decodificadores (FT8, DMR, APRS, ADS-B…) van en el servidor con la señal original.',
                           'La grabación del botón REC guarda el audio original, sin procesar.',
                           'Botones FILTRO y DSP en la barra superior; apagados por defecto (init.js: activo: true para encenderlos).']):
        b += txt(55, 575 + k * 26, '• ' + t, 11.2)
    return svg(W, H, b, 'Audio en el navegador: filtro_audio y dsp_audio (v4.2)')


def clonar_openwebrx():
    """Esquema 21: owrx-clone (v4.2)."""
    W, H = 1500, 900
    b = markers([C['ink'], C['or'], C['pi'], C['sdr'], C['cr'], C['net']])
    b += caja_s(30, 90, 420, 360, 'Equipo de ORIGEN', 'sudo owrx-clone exportar [--cifrar] [--publico]', C['pi'], '#edf7ee', arriba=True)
    niveles = [('config', '/var/lib/openwebrx: settings, users, bookmarks, imágenes'), ('etc', '/etc/openwebrx entero'),
               ('web', 'htdocs: plugins e init.js añadidos'), ('paquetes', 'SDR y decodificadores instalados a mano'),
               ('sistema', 'udev, modprobe rtl/dvb, systemd, codecserver'), ('parches', 'ficheros del paquete retocados (md5)'),
               ('extra', '--incluir RUTA')]
    for i, (n, d) in enumerate(niveles):
        c = C['pi'] if i < 4 else C['cr']
        b += txt(50, 165 + i * 36, n, 12, c, True) + txt(140, 165 + i * 36, d, 10.5)
    b += txt(50, 430, 'verde: se importan por defecto · rojo: solo pidiéndolos (código como root)', 9.8, C['mute'])
    b += arrow(450, 270, 560, 270, C['ink'], 'perfil')
    b += caja_s(560, 160, 380, 230, 'perfil .owrx.tar.gz(.enc)', '', C['or'], '#fff3e0', arriba=True)
    for k, t in enumerate(['manifiesto.json: origen, niveles, receptores,', '   paquetes y SHA-256 de cada fichero',
                           'LEEME.txt', 'archivos/<nivel>/… ({DATA}, {HTDOCS})', 'cifrado opcional: AES-256 + PBKDF2',
                           '--publico: sin users.json ni claves']):
        b += txt(580, 215 + k * 26, t, 11)
    b += arrow(940, 270, 1050, 270, C['ink'], 'copiar')
    b += caja_s(1050, 90, 420, 520, 'Equipo de DESTINO', 'sudo owrx-clone importar perfil [--simular] [--todo]', C['sdr'], '#eef4fb', arriba=True)
    pasos = ['1  comprueba SHA-256 y rutas (nada fuera de su sitio)', '2  repositorio luarvique de ESTE sistema',
             '   (bookworm · trixie · noble · jammy · bullseye)', '3  apt install de los paquetes del perfil',
             '4  COPIA de lo que se sobrescribe', '   → /var/backups/owrx-clone/copia-FECHA', '5  para OpenWebRX+ y copia los ficheros',
             '   (modo y dueño: users.json 600, openwebrx)', '6  --mapear serial=VIEJO=>serial=NUEVO', '7  arranca y espera /status.json',
             '8  avisa de los SDR que no ve conectados']
    for k, t in enumerate(pasos):
        b += txt(1070, 160 + k * 30, t, 11)
    b += caja_s(1050, 640, 420, 90, 'sudo owrx-clone deshacer', 'devuelve lo sobrescrito y borra lo creado', C['cr'], '#fdecee')
    b += arrow(1260, 610, 1260, 640, C['cr'])
    b += caja_s(30, 500, 940, 230, 'Dentro del kit BricoHams', '', C['ink'], '#fafafa', arriba=True)
    for k, t in enumerate(['sudo bash install.sh --exportar [fichero]       (no necesita bricohams.env)',
                           'sudo bash install.sh --importar perfil.owrx.tar.gz   → paso «importar» (IMPORTAR_NIVELES)',
                           'marca /etc/bricohams/perfil-importado: «configuracion» no regenera settings.json y «plugins» no pisa init.js',
                           'OWRX_PLANTILLA="yes" vuelve a la plantilla de BricoHams',
                           'copia diaria: /var/backups/bricohams/perfil-owrx-FECHA.owrx.tar.gz (cinco días)']):
        b += txt(50, 555 + k * 30, '• ' + t, 11)
    b += txt(30, 800, 'owrx-clone es genérico: cualquier OpenWebRX+ en Debian 11-13, Ubuntu 22.04/24.04 o Raspberry Pi OS (amd64, arm64, armhf).', 11.5)
    b += txt(30, 826, 'Un solo fichero Python 3 sin dependencias · README es/en · man owrx-clone · owrx-clone ayuda {niveles,seguridad,dispositivos,migrar,problemas} · MIT', 11, C['mute'])
    return svg(W, H, b, 'Clonar OpenWebRX+ a otro equipo: owrx-clone (v4.2)')


def zona_locator():
    """Esquema 22: marcadores y meteo de la zona según el locator (v4.3)."""
    W, H = 1500, 900
    b = markers([C['ink'], C['or'], C['pi'], C['sdr'], C['cr'], C['net'], C['rf']])
    b += caja_s(30, 90, 330, 250, 'bricohams.env', '', C['or'], '#fff3e0', arriba=True)
    for k, t in enumerate(['STATION_LOCATOR="IN52pf"', 'STATION_LAT / STATION_LON  (si están, mandan)',
                           'LOCATOR_CATALOG=data/locator/catalogo_es.json', 'LOCATOR_RADIUS_KM=100 · LOCATOR_MAX_SITES=3',
                           'LOCATOR_ONLINE=aemet,fmdx', 'LOCATOR_RADIOS=regional,local (MAX 30)', 'LOCATOR_METEO=yes · LOCATOR_KIT_ZONA_KM=150']):
        b += txt(45, 140 + k * 26, t, 10.8)
    b += caja_s(30, 380, 330, 300, 'Catálogo de España (en el kit)', 'tools/locator_catalogo.py', C['pi'], '#edf7ee', arriba=True)
    for k, t in enumerate(['aeropuertos: OurAirports (dominio público)', '   frecuencias; 8,33 kHz → frecuencia real',
                           'estaciones AEMET: 150 indicativos', 'puertos: interés general + deportivos',
                           '   canales 9 / 12 / 14 / 16', 'NAVTEX 518 y 490 kHz (alcance 550 km)']):
        b += txt(45, 440 + k * 30, t, 10.8)
    b += caja_s(30, 710, 330, 110, 'En la Pi, al instalar (caché 30 días)', '', C['net'], '#e0f2f1', arriba=True)
    b += txt(45, 760, 'AEMET OpenData: todas las estaciones', 10.8) + txt(45, 784, 'maps.fmdx.org (FMLIST): FM de la zona', 10.8)
    b += arrow(360, 215, 470, 330, C['ink'])
    b += arrow(360, 530, 470, 410, C['ink'])
    b += arrow(360, 765, 470, 450, C['net'], dash=True)
    b += caja_s(470, 230, 470, 330, 'bricohams_locator_bookmarks.py', 'paso «configuracion» · bricohams-locator', C['sdr'], '#eef4fb', arriba=True)
    for k, t in enumerate(['1  locator → coordenadas (o las exactas del env)', '2  distancia a cada sitio del catálogo',
                           '3  los 3 más cercanos de cada categoría en 100 km', '   (aeropuerto y AEMET: al menos uno, hasta 250 km)',
                           '4  FM: regionales y locales que mejor se oyen', '   (potencia / distancia², una por frecuencia)',
                           '5  canales repetidos juntos: Canal 16 · A / B', '6  etiqueta [AUTO-LOCATOR] y distancia en km',
                           '7  fuera de la zona ejemplo: marcadores del kit']):
        b += txt(490, 290 + k * 28, t, 10.8)
    b += arrow(940, 330, 1060, 200, C['ink']) + txt(950, 245, 'marcadores', 10.5, C['ink'])
    b += arrow(940, 420, 1060, 470, C['ink']) + txt(948, 425, 'METEO', 10.5, C['ink'])
    b += arrow(940, 500, 1060, 700, C['ink']) + txt(1000, 570, 'informe', 10.5, C['ink'])
    b += caja_s(1060, 90, 410, 270, 'OpenWebRX+ · bookmarks.json', '', C['rf'], '#f3e5f5', arriba=True)
    for k, t in enumerate(['los tuyos: nunca se tocan', 'los del kit: se quedan en la zona de ejemplo',
                           '   o se adaptan a los datos de la zona', '[AUTO-LOCATOR]: se sustituyen en cada pasada',
                           '   (misma frecuencia que uno tuyo: gana el tuyo)', 'sudo bricohams-locator marcadores --aplicar']):
        b += txt(1075, 140 + k * 34, t, 10.8)
    b += caja_s(1060, 400, 410, 170, 'Meteo (bricohams-meteo)', '', C['pi'], '#edf7ee', arriba=True)
    for k, t in enumerate(['meteo.env: METEO_STATIONS de la zona', 'LOCATOR_METEO="no" conserva la tuya', 'plugin METEO de la web: tiempo real AEMET']):
        b += txt(1075, 450 + k * 30, t, 10.8)
    b += caja_s(1060, 610, 410, 210, 'bricohams-locator info', '', C['ink'], '#fafafa', arriba=True)
    for k, t in enumerate(['QTH IN52PF · 42.23, -8.71 · península', 'aeropuertos, AEMET, puertos, FM y NAVTEX', 'con su distancia',
                           'refrescar · meteo · coordenadas · locator', 'bricohams-check: «zona … N marcadores»']):
        b += txt(1075, 660 + k * 28, t, 10.8)
    b += txt(30, 860, 'Vale para cualquier locator de España: IN, IM, JN, JM (península y Baleares), IL (Canarias), IM75 (Ceuta) e IM85 (Melilla). '
                      'Fuera de España avisa. Manual 32 · ADR-43.', 11, C['mute'])
    return svg(W, H, b, 'Zona de la estación por locator: aeropuertos, AEMET, puertos y FM (v4.3)')


def openwebrx_docker():
    """Esquema 23: OpenWebRX+ en Docker (v4.3)."""
    W, H = 1500, 900
    b = markers([C['ink'], C['or'], C['pi'], C['sdr'], C['cr'], C['net']])
    b += caja_s(30, 90, 360, 300, 'bricohams.env', '', C['or'], '#fff3e0', arriba=True)
    for k, t in enumerate(['OWRX_BACKEND="docker"', 'OWRX_DOCKER_IMAGE=slechev/openwebrxplus-softmbe', 'OWRX_DOCKER_CONTAINER="owrx-mbe"',
                           'OWRX_DOCKER_DIR="/opt/owrx-docker"', 'OWRX_DOCKER_RED="host" (o bridge + PORT)', 'OWRX_DOCKER_PRIVILEGED="no"',
                           'OWRX_DOCKER_DESPLEGAR / _ACTUALIZAR="yes"']):
        b += txt(45, 140 + k * 32, t, 10.8)
    b += arrow(390, 240, 480, 240, C['ink']) + txt(435, 228, 'paso', 10, C['ink'], a='middle')
    b += caja_s(480, 90, 470, 300, 'install.sh → docker_preparar', '', C['sdr'], '#eef4fb', arriba=True)
    for k, t in enumerate(['1  docker.io + docker compose si faltan', '2  para y desactiva el OpenWebRX+ nativo', '3  usuario openwebrx del sistema (servicios)',
                           '4  /opt/owrx-docker/{etc,var,plugins}', '5  docker-compose.yaml (bricohams-docker-compose.py)',
                           '6  docker compose pull · up -d', '7  espera /status.json · comprueba los volúmenes']):
        b += txt(495, 140 + k * 32, t, 10.8)
    b += arrow(950, 240, 1040, 240, C['ink'])
    b += caja_s(1040, 90, 430, 420, 'Contenedor owrx-mbe', 'red host · restart unless-stopped', C['net'], '#e0f2f1', arriba=True)
    vols = [('./etc', '/etc/openwebrx'), ('./var', '/var/lib/openwebrx'), ('./plugins', '…/htdocs/plugins'), ('/dev/bus/usb', '/dev/bus/usb (c 189:* rmw)')]
    for k, (a, d) in enumerate(vols):
        b += txt(1055, 165 + k * 34, a, 11, C['sdr'], True) + txt(1175, 165 + k * 34, '→ ' + d, 10.8)
    for k, t in enumerate(['OpenWebRX+ corre como root dentro', 'SDRplay y codecs (softmbe) en la imagen', ':8073 en la Pi (red host)',
                           'MQTT a 127.0.0.1:1883 (visitas)']):
        b += txt(1055, 330 + k * 30, '• ' + t, 10.8)
    b += caja_s(30, 440, 920, 250, 'Lo demás de BricoHams sigue en la Pi (sin cambios)', '', C['pi'], '#edf7ee', arriba=True)
    for k, t in enumerate(['configuracion · plugins · meteo · cámara · visitas · satélites escriben en /opt/owrx-docker/{var,plugins}',
                           '   (HTDOCS=/opt/owrx-docker, OWRX_DATA=…/var: install.sh las guarda en /etc/bricohams/bricohams.env)',
                           'se reinicia el contenedor (docker restart) en vez de systemctl restart openwebrx',
                           'nginx, SSL, ADS-B, Meshtastic, LilyGO, WX: igual que en la instalación nativa',
                           'no aplican en Docker: FT2 (parche del código) · API de SDRplay en el host · repositorio luarvique',
                           'copia diaria: /opt/owrx-docker y un perfil owrx-clone --docker · tarea actualizar: compose pull + up']):
        b += txt(45, 495 + k * 30, '• ' + t, 10.8)
    b += caja_s(1040, 550, 430, 270, 'owrx-clone 1.1 --docker owrx-mbe', '', C['cr'], '#fdecee', arriba=True)
    for k, t in enumerate(['volúmenes por docker inspect', 'config → ./var · etc → ./etc · web → ./plugins', 'sin apt (la imagen) ni parches',
                           'nativo → Docker y Docker → nativo', 'deshacer: docker stop / start', 'sin volumen de /etc o /var: se para']):
        b += txt(1055, 600 + k * 32, '• ' + t, 10.8)
    b += caja_s(30, 720, 920, 100, 'Pasar de nativo a Docker (manual 33)', '', C['ink'], '#fafafa', arriba=True)
    b += txt(45, 770, 'sudo owrx-clone exportar -o p.owrx.tar.gz  →  OWRX_BACKEND="docker"  →  sudo bash install.sh --actualizar', 10.8)
    b += txt(45, 795, '→  sudo owrx-clone --docker owrx-mbe importar p.owrx.tar.gz', 10.8)
    b += txt(30, 860, 'Imagen oficial de OpenWebRX+ en Docker Hub: slechev/openwebrxplus (y -softmbe). Manual 33 · ADR-44 y ADR-45.', 11, C['mute'])
    return svg(W, H, b, 'OpenWebRX+ en Docker desde bricohams.env (v4.3)')


def blindaje():
    """Esquema 24: capas de seguridad de la estación (v4.4)."""
    W, H = 1500, 900
    b = markers([C['ink'], C['or'], C['pi'], C['sdr'], C['cr'], C['net']])
    b += caja_s(30, 90, 250, 300, 'Internet', 'sdr.example.org', C['cr'], '#fdecee', arriba=True)
    for k, t in enumerate(['oyentes', 'robots que prueban', 'contraseñas', 'directorios de', 'receptores']):
        b += txt(50, 160 + k * 26, t, 11)
    b += caja_s(330, 90, 230, 300, 'Cortafuegos externo', '(router)', C['or'], '#fff3e0', arriba=True)
    for k, t in enumerate(['80  → Pi', '443 → Pi', '8073 → Pi  (!)', 'nada más']):
        b += txt(350, 165 + k * 32, t, 12, C['ink'], k < 3)
    b += txt(350, 320, '(!) /login por 8073 va', 10.5, C['cr']) + txt(350, 338, 'sin cifrar: ciérralo', 10.5, C['cr'])
    b += arrow(280, 240, 330, 240, C['cr'])
    b += arrow(560, 240, 610, 240, C['ink'])
    b += caja_s(610, 90, 860, 600, 'Raspberry Pi 5 · IP-DE-LA-PI', 'bricohams-blindaje aplicar · confirmar · deshacer', C['sdr'], '#eef4fb', arriba=True)
    capas = [('Cortafuegos del host (nftables)', 'público 80/443/8073 · LAN: SSH, 4403, 8443, 8554 · resto: descartado y registrado', C['or']),
             ('nginx', '/settings → HTTPS · /login 12/min (429) · sin versión · X-Frame · ocultos 404', C['net']),
             ('SSH', 'solo LAN · sin root · 3 intentos · solo clave si la hay · fail2ban', C['pi']),
             ('Claves', 'bricohams.env 600 · .env 640 · copias 700 · users.json 600 · fugas: buscadas', C['cr']),
             ('Privacidad', 'posición pública a 2 decimales (~1 km): mapa, status.json, init.js, meteo, pases', C['sdr']),
             ('Sistema', 'unattended-upgrades · sysctl · UMask 0027 · Bluetooth fuera', C['ink'])]
    for k, (t, d, c) in enumerate(capas):
        y = 150 + k * 84
        b += caja_s(630, y, 820, 70, t, d, c, '#ffffff')
    b += caja_s(30, 430, 530, 260, 'Procedimiento (manual 34)', '', C['ink'], '#fafafa', arriba=True)
    for k, t in enumerate(['1  sudo bash install.sh --actualizar', '2  sudo bricohams-blindaje auditar   (no cambia nada)',
                           '3  ssh-copy-id usuario@IP-DE-LA-PI', '4  sudo bricohams-blindaje aplicar', '5  otra ventana: ¿entro? ¿va la web?',
                           '6  sudo bricohams-blindaje confirmar  (si no, 3 min y se quita)', '7  sudo bricohams-blindaje auditar']):
        b += txt(50, 485 + k * 28, t, 11)
    b += txt(30, 760, 'La auditoría nunca enseña una clave: solo la variable y el fichero donde aparece. bricohams-check muestra el resumen cada 30 min.', 11)
    b += txt(30, 860, 'HAT, Mini RTL-SDR y SDRplay pendientes: sus errores no son de seguridad. Manual 34 · ADR-47 y ADR-48.', 11, C['mute'])
    return svg(W, H, b, 'Blindaje de seguridad de la estación (v4.4)')


def lora_owrx():
    """Esquema 25: RAK4631 LoRa APRS, nodos Meshtastic y su integración en OpenWebRX+ (v4.5)."""
    W, H = 1500, 930
    b = markers([C['ink'], C['lora'], C['sdr'], C['or'], C['net'], C['pi']])
    b += caja_s(30, 80, 360, 250, 'RAK4631 WisBlock · 433,775 MHz', 'firmware BricoHams RAK APRS (port CA2RXU)', C['lora'], '#e0f7fa', arriba=True)
    for k, t in enumerate(['SX1262 · SF12 · BW 125 · CR 4/5 · 20 dBm', 'digipeater WIDE1-1 · baliza · estado', 'GPS slot A · sensor de la caja (SHTC3/BME)',
                           'KISS por USB + orden 0x06 «BH:…»', 'N0CALL-15 · /dev/rak-aprs']):
        b += txt(50, 150 + k * 30, t, 11)
    b += caja_s(30, 370, 360, 190, 'LilyGO T3 V1.6.1 · 433', 'Meshtastic EU_433 LongFast · 10 dBm', C['or'], '#fff3e0', arriba=True)
    for k, t in enumerate(['URL de la red 433 (MESH433_CHANNEL_URL)', 'SDR BricoHams 433 · SB43', '/dev/lilygo-mesh']):
        b += txt(50, 440 + k * 30, t, 11)
    b += caja_s(30, 600, 360, 170, 'HAT · SX1262 868 (en camino)', 'meshtasticd · 127.0.0.1:4403', C['pi'], '#e8f5e9', arriba=True)
    for k, t in enumerate(['869,618 MHz · BW 62,5 · SF7 · 27 dBm', 'SDR BricoHams 868 · SB86']):
        b += txt(50, 670 + k * 30, t, 11)
    b += caja_s(480, 80, 430, 690, 'Raspberry Pi 5', 'servicios sin root (DynamicUser)', C['sdr'], '#eef4fb', arriba=True)
    b += caja_s(500, 140, 390, 170, 'bricohams-rak-aprs', 'RF → APRS-IS (qAR) · baliza/telemetría · APRS-IS → RF (mensajes)', C['lora'], '#ffffff')
    b += caja_s(500, 340, 390, 150, 'bricohams-mesh-owrx', 'API Meshtastic (serie y TCP) → posiciones, nombres, telemetría', C['or'], '#ffffff')
    b += caja_s(500, 520, 390, 110, 'mosquitto 127.0.0.1:1883', 'lora433/APRS · mesh433/Meshtastic · mesh868/Meshtastic', C['net'], '#ffffff')
    b += caja_s(500, 650, 390, 100, 'OpenWebRX+ 1.2.126', 'mqtt_aprs · mqtt_meshtastic → MAPA · LoRa APRS y Meshtastic por SDR (lorarx)', C['sdr'], '#ffffff')
    b += arrow(390, 200, 500, 220, C['lora'], 'USB KISS')
    b += arrow(390, 460, 500, 400, C['or'], 'USB serie')
    b += arrow(390, 680, 500, 440, C['pi'], 'TCP 4403')
    b += arrow(700, 310, 700, 520, C['lora'])
    b += arrow(760, 490, 760, 520, C['or'])
    b += arrow(700, 630, 700, 650, C['net'])
    b += caja_s(1000, 80, 470, 200, 'APRS-IS', 'rotate.aprs2.net:14580 · filtro m/10', C['ink'], '#fafafa', arriba=True)
    b += txt(1020, 160, 'sube lo oído por RF (sin TCPIP/NOGATE/RFONLY)', 11) + txt(1020, 188, 'baja mensajes para estaciones oídas (30 min)', 11)
    b += txt(1020, 216, 'aprs.fi · N0CALL-15', 11, C['lora'], True)
    b += arrow(890, 220, 1000, 180, C['ink'], 'passcode')
    b += caja_s(1000, 320, 470, 450, 'Mapa público de OpenWebRX+', 'https://sdr.example.org/map', C['sdr'], '#eef4fb', arriba=True)
    for k, t in enumerate(['estaciones LoRa APRS oídas (icono APRS, RSSI/SNR)', 'nodos Meshtastic 433 y 868 (icono M)',
                           'posición de NUESTROS nodos a 2 decimales (~1 km)', 'mensajes directos: nunca', 'chat de canales públicos: MESH_OWRX_CHAT=yes',
                           'sin HAT: el 868 espera solo (no es un fallo)']):
        b += txt(1020, 400 + k * 34, t, 11)
    b += arrow(890, 700, 1000, 600, C['sdr'])
    b += txt(30, 830, 'Grabar: sudo bricohams-rak-aprs grabar (DFU por USB) · sudo bricohams-lilygo firmware · Probar: sudo bricohams-rak-aprs prueba · sudo bricohams-check', 11)
    b += txt(30, 880, 'Manual 35 · ADR-49 (RAK: radio en el RAK, Internet en la Pi) · ADR-50 (mapa por MQTT) · ADR-51 (URLs de Meshtastic)', 11, C['mute'])
    return svg(W, H, b, 'LoRa APRS y Meshtastic en OpenWebRX+ (v4.5)')


def main():
    os.makedirs(OUT, exist_ok=True)
    try:
        import cairosvg
    except ImportError:
        cairosvg = None
    for name, fn in [('01_arquitectura', bloques), ('02_gpio_pi5', gpio), ('03_cableado_bme280', bme280),
                     ('04_rf_antenas_alimentacion', rf), ('05_red_puertos', red),
                     ('06_alimentacion_caja', alimentacion), ('07_caja_distribucion', caja),
                     ('12_cadena_rf', rf_completo), ('13_ventiladores', ventiladores), ('14_sensores_wx', sensores_wx),
                     ('15_alimentacion_v3', alimentacion_v3), ('16_pico_io', pico_io), ('17_filtros_lna', filtros_lna),
                     ('18_red_servicios', red_servicios), ('19_actualizar', actualizar),
                     ('20_audio_navegador', audio_navegador), ('21_clonar_openwebrx', clonar_openwebrx),
                     ('22_zona_locator', zona_locator), ('23_openwebrx_docker', openwebrx_docker),
                     ('24_blindaje', blindaje), ('25_lora_owrx', lora_owrx)]:
        s = fn()
        open(os.path.join(OUT, name + '.svg'), 'w', encoding='utf-8').write(s)
        if cairosvg:
            cairosvg.svg2png(bytestring=s.encode(), write_to=os.path.join(OUT, name + '.png'))
        print('esquema', name)


if __name__ == '__main__':
    main()
