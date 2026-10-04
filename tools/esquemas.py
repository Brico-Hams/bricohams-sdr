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
            f"<text x='24' y='58' font-size='12' fill='{C['mute']}'>BricoHams SDR · EA5KAO · Mi QTH (Región de Murcia) · generado por tools/esquemas.py</text>"
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
        for c in set(colors)) + '</defs>'


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
            ('meshtasticd', 'nodo 868 · web :9443 · API :4403'), ('gpsd + chrony', 'hora GPS + PPS · :2947'),
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
            (470, 'Red Meshtastic 433', 'mismos canales, EU_433'), (580, 'APRS-IS (euro.aprs2.net)', 'iGate EA5KAO-10 · WX EA5KAO-13 · OWRX EA5KAO'),
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
           7: 'DS18B20 caja (v3)', 11: 'pluviómetro (v3)', 15: 'tacómetro vent. 1 (v3)', 29: 'tacómetro vent. 2 (v3)',
           32: 'PWM vent. entrada (v3)', 33: 'PWM vent. salida (v3)', 14: 'GND pluviómetro'}
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
           ('spi', 'SPI1 spidev1.0: LoRa SX1262'), ('fan', 'v3: PWM y tacómetros (ventiladores)'),
           ('w1', 'v3: 1-Wire DS18B20'), ('wx', 'v3: pluviómetro')]
    for i, (k, t) in enumerate(ley):
        b += f"<rect x='930' y='{510 + i * 26}' width='14' height='14' fill='{col[k]}'/><text x='952' y='{522 + i * 26}' font-size='12' fill='{C['ink']}'>{esc(t)}</text>"
    b += (f"<text x='24' y='{790}' font-size='12' fill='{C['cr']}' font-weight='bold'>⚠ Pines del HAT tomados de la guía AIO de HackerGadgets: A VERIFICAR con su documentación (bricohams.env, HAT_*).</text>")
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
            ('9443/tcp', 'meshtasticd: web (https)', 'solo LAN', C['lora']),
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
             '• bricohams-wx publica en APRS-IS (EA5KAO-13): dirección, velocidad media de 1 min, racha de 5 min, lluvia de 1 h, 24 h y desde medianoche.',
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
                     ('15_alimentacion_v3', alimentacion_v3)]:
        s = fn()
        open(os.path.join(OUT, name + '.svg'), 'w', encoding='utf-8').write(s)
        if cairosvg:
            cairosvg.svg2png(bytestring=s.encode(), write_to=os.path.join(OUT, name + '.png'))
        print('esquema', name)


if __name__ == '__main__':
    main()
