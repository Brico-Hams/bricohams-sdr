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
C = {'bg': '#ffffff', 'ink': '#23272B', 'mute': '#59636B', 'line': '#9aa6b2',
     'or': '#F26B1D', 'cr': '#AA410B', 'pi': '#2e7d32', 'sdr': '#1565c0', 'rf': '#6a1b9a',
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
    b += box(330, 870, 300, 56, 'Cámara Pi Camera Module 3 Wide (IMX708)', ['CSI 15→22 pines · cámara Pi 5'], C['cam'])
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
             'Cámara Pi Camera Module 3 Wide por CSI con cable Standard–Mini 15→22 pines de la Pi 5 (máx. ~1 m dentro de la caja). No es NoIR: sin LED IR.',
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
    b += box(720, 90, 300, 150, 'Raspberry Pi 5', ['+ HAT: RTL-SDR, SX1262, GPS, RTC', '+ cámara Camera Module 3 Wide (CSI)', 'consumo 8–12 W', 'USB limitado a 0,6 A en total', '(PI5_USB_MAX_CURRENT="no")'], C['pi'], '#edf7ee')
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
    b += f"<text x='{X(cx):.1f}' y='{Y(cy + 16):.1f}' font-size='11' text-anchor='middle' fill='#263238' font-weight='bold'>cámara Camera Module 3 Wide (en la tapa)</text>"
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


# ---------------------------------------------------------------------
#  31-39: montaje de las piezas impresas en 3D (manual 52).
#  Cotas y tornillería salen de los .scad de hardware/ y de los manuales;
#  lo que no está en ellos se marca como PENDIENTE DE CONFIRMAR.
# ---------------------------------------------------------------------
def _montaje(titulo, pasos, capas, dims):
    # left: numbered step list; right: exploded layers (top to bottom) + dimensions
    n, m = len(pasos), len(capas)
    dy = 84 + m * 70
    H = max(90 + n * 74, dy + len(dims) * 16 + 36) + 30
    b = markers([C['or']])
    for i, (t, l1, l2) in enumerate(pasos):
        y0 = 90 + i * 74
        b += (f"<circle cx='44' cy='{y0 + 31}' r='15' fill='{C['or']}' stroke='{C['cr']}' stroke-width='1.5'/>"
              + txt(44, y0 + 36, i + 1, 14, C['ink'], True, 'middle'))
        b += f"<rect x='70' y='{y0}' width='700' height='62' rx='6' fill='#f7f9fb' stroke='{C['ink']}' stroke-width='1.8'/>"
        b += txt(84, y0 + 20, t, 11.5, C['ink'], True) + txt(84, y0 + 37, l1, 10.5) + txt(84, y0 + 52, l2, 10, C['mute'])
        if i < n - 1:
            b += arrow(44, y0 + 46, 44, y0 + 90, C['or'])
    for k, (num, t, sub, col, lab) in enumerate(capas):
        y = 90 + k * 70
        b += f"<rect x='820' y='{y}' width='300' height='44' rx='6' fill='#f7f9fb' stroke='{col}' stroke-width='1.8'/>"
        b += (f"<circle cx='800' cy='{y + 22}' r='12' fill='{C['or']}' stroke='{C['cr']}' stroke-width='1.5'/>"
              + txt(800, y + 27, num, 12, C['ink'], True, 'middle'))
        b += txt(970, y + 19, t, 11.5, col, True, 'middle') + txt(970, y + 35, sub, 9.5, C['mute'], False, 'middle')
        if k < m - 1:
            b += arrow(970, y + 44, 970, y + 70, C['or'], lab)
    b += f"<rect x='820' y='{dy}' width='656' height='{len(dims) * 16 + 36}' rx='8' fill='#ffffff' stroke='{C['or']}' stroke-width='2'/>"
    b += txt(832, dy + 20, 'Cotas del .scad', 12, C['cr'], True)
    for i, d in enumerate(dims):
        b += txt(832, dy + 40 + i * 16, d, 11)
    return svg(1500, H, b, titulo)


def montaje_caja_v2():
    pasos = [
        ('Insertos roscados en cuerpo, soportes de mástil y tejadillo',
         'M4 ×20: 8 orejas (y = 22, 84, 148, 210), 8 de los soportes de mástil y 4 pilares del tejadillo',
         'Soldador a 230-245 °C, de fuera hacia dentro y a ras. M3 ×16: 8 placas, 4 tapa interior, 2 visera y 2 soporte de cámara'),
        ('Pasamuros en la pared: 9 SMA, PG7 WX, M20 LAN y PG9 230 V',
         'SMA: SAT, HAM, VHF, HF, ADSB, 868, GPS, M433, IG433 (paso 15 mm, z = 26), agujero de 6,6 mm',
         'Junta tórica por fuera y latiguillo RG316 de 20 cm en cada SMA'),
        ('Compartimento de potencia: placa_potencia sobre sus 4 bosses',
         '4 × M3×8 · separación 10 mm · placa de 3 mm · 230 V por PG9 a 2 × WAGO 221-412',
         'Sin tensión y con diferencial de 30 mA aguas arriba'),
        ('tapa_potencia interior sobre 4 insertos M3',
         '4 × M3×8 (2 en y = 30 y 2 en y = 200) · altura CP_Z = 56 mm · pasamuros_usb en el hueco del tabique',
         'Tabique con hueco de 18 × 34 mm para los conectores USB'),
        ('placa_electronica con Pi 5, dongles y LilyGO',
         '4 × M3×8 a los bosses (30,6), (110,6), (30,204), (110,204) · Pi 5: 4 × M2.5×6 autorroscantes (58 × 49)',
         'LilyGO sobre la tapa interior de potencia'),
        ('Cámara: junta_ventana, policarbonato, soporte_camara y visera',
         'PC 86 × 36 × 2 + junta 1,5 mm · soporte_camara 2 × M3×35 y espuma de 1 mm · visera 2 × M3×8',
         'Ventana de 76 × 26 mm en (160, 196) · separador_ir opcional con Camera Module 3 Wide · cable CSI con holgura'),
        ('junta_tapa (TPU) en la ranura y cierre de la tapa',
         '8 × M4×12 con arandela, en cruz, hasta que la tapa toque las orejas',
         'Junta 4,4 × 4 mm en ranura de 4,2 mm (compresión ≈ 25 %); no aprietes de más'),
        ('2 × soporte_mastil en la trasera',
         '4 × M4×20 por soporte (y = 45 e y = 187; separación 30 × 19 mm) · 2 abrazaderas de 12 mm cada uno',
         'Mástil de 40 mm'),
        ('tejadillo y garita',
         'Pilares (12,20), (212,20), (12,70), (212,70): M4×30 (traseros) y M4×25 (delanteros) con arandelas de goma',
         'Garita: 3 varillas M4×140 con 6 tuercas ciegas · 2 M2 para el sensor'),
    ]
    capas = [
        (9, 'tejadillo', '4 pilares con insertos M4', C['cr'], '2 × M4×30 + 2 × M4×25 + arandela de goma'),
        (7, 'tapa + junta_tapa', '8 × M4×12 en cruz', C['sdr'], '8 × M4×12 con arandela'),
        (6, 'visera + cámara + soporte_camara', 'M3×8 ×2 · M3×35 ×2', C['cam'], 'M3 a insertos de la tapa'),
        (5, 'placa_electronica 138 × 210', '4 bosses M3 · Pi 5 M2.5', C['pi'], '4 × M3×8'),
        (4, 'tapa_potencia + placa_potencia', '4 + 4 × M3×8 · CP_Z = 56 mm', C['pwr'], '4 × M3×8 a los insertos'),
        (1, 'cuerpo 224 × 232 × 90', 'insertos · SMA, PG7, M20, PG9', C['ink'], '4 × M4×20 por soporte'),
        (8, 'soporte_mastil ×2', 'y = 45 · y = 187', C['gnd'], ''),
    ]
    dims = ['Exterior 224 × 232 × 90 mm (ancho × alto × fondo) · pared 3,2 mm · tapa 4 mm',
            'Junta TPU 4,4 × 4 mm · ranura 4,2 mm',
            'Orejas M4 en y = 22, 84, 148, 210 (4 por lado)',
            'Placa electrónica 138 × 210 · placa de potencia 58 × 210 · separación 10 · espesor 3 mm',
            'Ventana de cámara 76 × 26 en (160, 196) · PC 86,5 × 36,5 × 2 · junta 1,5 mm',
            'Inserto M3: agujero 4,0 × 6 · M4: agujero 5,6 × 8,5']
    return _montaje('Montaje de la caja v2: secuencia y despiece', pasos, capas, dims)


def montaje_caja_v3_electronica():
    pasos = [
        ('Insertos: M4 en orejas y pilares, M3 en la rejilla',
         'Soldador a 220 °C · M4: orejas en y = 24, 92, 148, 216 y 4 pilares del tejadillo · M5 en la trasera',
         'M3 en cada nudo de la placa_rejilla (paso 20 mm) · insertos a ras'),
        ('junta_tapa (TPU) en la ranura de la tapa',
         'TPU 5,6 × 4 mm en ranura de 5,8 mm · 4 puntos de cianoacrilato',
         'Ranura limpia, sin rebabas de impresión'),
        ('Pasamuros N, tapon_n y prensaestopas',
         'Agujeros N de 16,2 mm en filas z = 26, 56 y 86 (paso 27) · z = 116: M25 PWR, M20 LAN, PG7 ×4',
         'tapon_n y tapon_pg (TPU) en los que queden libres'),
        ('Ventiladores de 60 mm: entrada a la izquierda, salida a la derecha',
         'rejilla_ventilador + malla inox 1 mm entre ventilador y pared · capota fuera, boca hacia abajo',
         'Agujero 57 mm · tornillos a 50 mm (3,6 mm) · entrada (y 55, z 60) · salida (y 190, z 68)'),
        ('placa_rejilla sobre sus 5 bosses',
         '5 × M3 (4 esquinas + centro) · separación 8 mm · placa de 3 mm',
         'Soportes (dongle, hub, SDRplay, WAGO) con M3 o bridas: PENDIENTE DE CONFIRMAR'),
        ('6 × poste_bandeja + bandeja_sdr',
         'bandeja_sdr 167 × 170 a DECK_H = 38 mm · postes de 38 mm',
         'Tornillos de los postes: PENDIENTE DE CONFIRMAR · SDR con bridas'),
        ('6 × poste_medio + bandeja_sdr2',
         'bandeja_sdr2 a DECK2_H = 82 mm · postes de 41 mm',
         'Tornillos: PENDIENTE DE CONFIRMAR'),
        ('4 × poste_superior + bandeja (Pi 5 + HAT)',
         'bandeja 170 × 92 a BAND_H = 131 mm · Pi 5 en (8,10) con M2.5 autorroscante (agujero 2,4; 58 × 49)',
         'soporte_lilygo en x = 98 · soporte_rak en (129,12) · postes de 46 mm'),
        ('Fijación, cierre y tejadillo',
         'M5 en los insertos traseros (WALL_Y = 40 y 200) · tapa con 8 × M4×16 en cruz · tejadillo al final',
         'Lazos de goteo en cada cable · sudo bricohams-check'),
    ]
    capas = [
        (9, 'electronica_tejadillo', '4 pilares con insertos M4', C['cr'], 'M4 + arandela de goma (longitud PENDIENTE)'),
        (9, 'electronica_tapa + junta_tapa', '8 orejas M4 · M4×16 en cruz', C['sdr'], '8 × M4×16'),
        (8, 'electronica_bandeja', '4 × poste_superior', C['pi'], 'tornillos PENDIENTES'),
        (7, 'electronica_bandeja_sdr2', '6 × poste_medio', C['sdr'], 'M3 (PENDIENTE)'),
        (6, 'electronica_bandeja_sdr', '6 × poste_bandeja', C['sdr'], 'M3 (PENDIENTE)'),
        (5, 'electronica_placa_rejilla', '5 bosses M3 · 8 mm', C['gnd'], '5 × M3'),
        (1, 'electronica_cuerpo', 'N, PG/M, ventiladores, M5 trasera', C['ink'], ''),
    ]
    dims = ['Exterior 228 × 240 × 192 mm · pared 4,8 mm · tapa 5,2 mm',
            'Junta TPU 5,6 × 4 mm · ranura 5,8 mm',
            'Orejas M4 en y = 24, 92, 148, 216 · pilares del tejadillo M4',
            'Rejilla: espesor 3,2 mm · separación 8 mm · paso 20 mm · M3 en cada nudo',
            'Scad: DECK_H 38 · DECK2_H 82 · BAND_H 131 mm (manual 17: 30 / 71 mm, PENDIENTE DE CONFIRMAR)',
            'Ventilador 60 mm: agujero 57 mm, tornillos a 50 mm (3,6 mm) · N: agujero 16,2 mm',
            'Inserto M3: 4,0 × 6 · M4: 5,6 × 8,5 · M5: agujero 7,0 mm',
            'Cámara opcional (Camera Module 3 Wide): ventana 20 × 16 en (W/2, 210) · cajeado 27 × 26']
    return _montaje('Montaje de la caja v3 electrónica: secuencia y despiece', pasos, capas, dims)


def montaje_caja_v3_potencia_sai():
    pasos = [
        ('Insertos M4 y M5 y junta_tapa (TPU) en la ranura',
         'Potencia 170 × 200 × 112: orejas M4 en y = 24, 100, 176 · M5 trasera en y = 40 y 160',
         'SAI 228 × 240 × 140: orejas en y = 24, 92, 148, 216 · M5 trasera en y = 40 y 200'),
        ('Prensaestopas de la potencia: PG9 230 V, M25 A ELECTRONICA y PG7 VENT',
         'Salida con manguera 4 × 0,75 H07RN-F · PG7 VENT con membrana ePTFE (tapon_pg con respiradero)',
         'tapon_pg en los PG sobrantes'),
        ('potencia: soporte_schuko y brida_cargador sobre la placa_rejilla',
         'Schuko de superficie ≈ 80 × 80 × 42: M4 a ±30 mm + 4 × M3 · brida 110 × 16 × 40 con 2 × M3',
         'Cadena: disparador PD, fusible y WAGO (manual 17)'),
        ('SAI: soporte_bateria y 2 × guia_pcb sobre la placa_rejilla',
         'BAT (50,4) · PCB (6,6) · guías en y = 18 y 168 · ranura 2,2 mm con M3 prisionero',
         'Batería sujeta con correas por ventanas de correa (22 mm en el .scad)'),
        ('SAI: pletina_trafo, 2 × soporte_filtro y soporte_wago',
         'TRAFO (50,118) con ranuras M5 · EMI_OUT (138,118) y EMI_IN (176,118) con ranuras M4',
         'DC en (50,194) · WAGO con soporte_wago'),
        ('SAI: fusible ATO 15 A en BAT+ y PE a los filtros EMI',
         'Fusible a ≤ 10 cm del borne · ventilas superior e inferior abiertas (hidrógeno)',
         'SAI desenchufado y batería desconectada; espera 5 minutos'),
        ('Prensaestopas del SAI y cierre de ambas cajas',
         'SAI: PG9 RED, PG9 SALIDA, PG7 DATOS · tapa con M4×16 en cruz (6 en potencia, 8 en SAI)',
         'Lazos de goteo · tapon_pg en los PG libres'),
        ('Fijación: pletina_pared ×2 (4 tacos) o soporte_mastil ×2 con U M8',
         'M5 en los insertos traseros · módulo de potencia más bajo que la electrónica · tejadillo al final',
         'Longitud de los M5 y de las U: PENDIENTE DE CONFIRMAR'),
    ]
    capas = [
        (8, 'potencia_tejadillo / sai_tejadillo', '4 pilares con insertos M4 cada uno', C['cr'], 'M4 (longitud PENDIENTE)'),
        (7, '*_tapa + *_junta_tapa', 'M4×16 en cruz', C['sdr'], '6 (potencia) · 8 (SAI) × M4×16'),
        (4, 'sai: bateria, guia_pcb, trafo, filtro', 'soporte_wago · fusible ATO 15 A', C['pwr'], 'M3 / M4 / M5 ranurados'),
        (3, 'potencia: soporte_schuko, brida_cargador', 'M4 a ±30 · M3', C['pwr'], '4 × M3 + 2 × M3'),
        (3, '*_placa_rejilla', 'sobre bosses M3 del cuerpo', C['gnd'], 'M3'),
        (1, 'potencia_cuerpo / sai_cuerpo', 'M4, M5, PG9, M25, PG7', C['ink'], 'M5 a pared o mástil'),
        (8, '*_pletina_pared / *_soporte_mastil', 'M5 trasera · U M8', C['gnd'], ''),
    ]
    dims = ['Potencia 170 × 200 × 112 mm · SAI 228 × 240 × 140 mm',
            'Pared 4,8 mm · tapa 5,2 mm · junta TPU 5,6 × 4 mm · ranura 5,8 mm',
            'Orejas M4: potencia y = 24, 100, 176 · SAI y = 24, 92, 148, 216',
            'M5 trasera: y = 40 y 160 (potencia) · y = 40 y 200 (SAI) · x al 25 % y 75 % del ancho',
            'SAI (x,y): BAT 50,4 · PCB 6,6 · TRAFO 50,118 · EMI_OUT 138,118 · EMI_IN 176,118 · DC 50,194']
    return _montaje('Montaje de la caja v3 de potencia y del SAI: secuencia y despiece', pasos, capas, dims)


def montaje_quad():
    pasos = [
        ('quad_buje_2m ×2 y quad_buje_70 ×2 en el boom',
         'Boom cuadrado 20 × 20 (BOOM 20,4) · marcas a 0, 248, 372 y 510 mm · 2 prisioneros M5 por buje (8 en total)',
         'Cola de 500 mm tras el reflector de 2 m (manual 12)'),
        ('Varillas Ø8 en los bujes',
         'Cortadas a cruceta − 25 mm · M3 autorroscante · quad_puntera_8 ×7 en las puntas',
         'Longitudes Ø8: 378 y 345 mm (manual 12)'),
        ('Varillas Ø6 y puntas',
         'quad_puntera_6 ×8 · quad_clip_70 ×3 a 127 mm del centro (brazos arriba, abajo y −Y)',
         'Longitudes Ø6: 108 y 95 mm'),
        ('Hilo de cobre Ø2 por punteras y bujes',
         'Recorrido del hilo: manual 12',
         'Hilo Ø2 mm'),
        ('quad_alim_2m (en la punta +Y) y quad_alim_70 (en lugar del clip +Y)',
         '2 insertos M3 de latón como terminales, a 12 mm entre sí',
         'Alimentación de 2 m con RG-59 de λ/4 = 341 mm; la de 70 cm con RG-58 o RG-316'),
        ('quad_abrazadera en la cola del boom',
         'U M8 al mástil y U M6 al boom · pieza de 80 × 22 con ranura cuadrada',
         'Tamaño exacto de las U: PENDIENTE DE CONFIRMAR · alternativa v4: cruceta_mastil_quad (manual 21)'),
        ('Montaje en el mástil a 0,95 m con rumbo 205°',
         'Cola de 500 mm · comprobación de ROE antes de izar: manual 12',
         'Cable con lazo de goteo y separador_coax'),
    ]
    capas = [
        (3, 'quad_puntera_8 ×7 · quad_puntera_6 ×8', 'extremos de varilla', C['rf'], ''),
        (2, 'varillas Ø8 y Ø6', 'M3 autorroscante', C['gnd'], 'M3 en el buje'),
        (1, 'quad_buje_2m ×2 · quad_buje_70 ×2', 'boom 20 × 20 · 8 prisioneros M5', C['rf'], '2 insertos M3'),
        (5, 'quad_alim_2m · quad_alim_70', 'terminales a 12 mm', C['pwr'], 'U M8 + U M6'),
        (6, 'quad_abrazadera', 'U M8 mástil · U M6 boom', C['ink'], ''),
    ]
    dims = ['Varillas Ø8: 378 y 345 mm · Ø6: 108 y 95 mm (manual 12)',
            'Boom 20 × 20 (BOOM 20,4 mm): marcas a 0, 248, 372 y 510 mm · cola de 500 mm',
            'Espira de hilo Ø2 mm · RG-59 λ/4: 341 mm · rumbo 205°',
            'quad_abrazadera 80 × 22 mm · mástil de 0,95 m']
    return _montaje('Montaje del quad 2 m / 70 cm: secuencia y despiece', pasos, capas, dims)


def montaje_discone_adsb():
    pasos = [
        ('discone_aislador: insertos M4',
         'Ø50 × 20 mm · 3 insertos M4 arriba y 3 abajo',
         'Insertos a ras'),
        ('Disco: 12 varillas Ø4 con rosca M4 al cubo',
         'Cubo de aluminio Ø70 × 12 · discone_plantilla_disco (12 agujeros) · varillas de 327 mm',
         'Cubo al aislador con 3 × M4'),
        ('Cono: 12 varillas de 1010 mm al otro cubo',
         'discone_plantilla_cono (semiángulo 30°) · cubo al aislador con 3 × M4 (M4×10 en el manual 13)',
         'Hueco entre disco y cono: 20 mm'),
        ('tapon_varilla ×12 en las puntas',
         'En las 12 puntas del cono · agujero Ø2,5 para cordino',
         'Modo de fijación: PENDIENTE DE CONFIRMAR'),
        ('discone_adaptador_mastil al cubo',
         '60 mm de alto · 4 × M4 al cubo · 2 × M6 pasantes al mástil (z = 12 y z = 32)',
         'Par de apriete: PENDIENTE DE CONFIRMAR'),
        ('discone_capuchon',
         'Sobre el cubo del disco, con silicona neutra en el borde (manual 13)',
         'Fijación del capuchón: PENDIENTE DE CONFIRMAR'),
        ('ADS-B: adsb_base con el LNA',
         'LNA 72 × 34 × 20 · SMA de panel de 6,6 mm · PG7 de 12,7 mm · 4 tornillos de 2,8 mm para la brida',
         'Oreja para la sujeción al brazo'),
        ('adsb_tapa y adsb_radomo',
         'adsb_tapa con 4 × M3 + junta TPU de 1 mm · elemento de 62 mm y 4 radiales de 68 mm a 45° (latón Ø2)',
         'Radomo: silicona neutra (manual 14); tornillos: PENDIENTE DE CONFIRMAR'),
    ]
    capas = [
        (6, 'discone_capuchon', 'manual 13', C['rf'], ''),
        (4, 'tapon_varilla ×12', 'puntas del cono', C['rf'], ''),
        (2, 'disco: 12 varillas + plantilla', 'Ø4 · 327 mm', C['gnd'], '3 × M4'),
        (1, 'discone_aislador Ø50 × 20', '3 M4 arriba + 3 abajo', C['ink'], '3 × M4'),
        (3, 'cono: 12 varillas + plantilla', 'Ø4 · 1010 mm · 30°', C['gnd'], '4 × M4'),
        (5, 'discone_adaptador_mastil', 'M4 ×4 · M6 ×2 pasantes', C['ink'], ''),
        (7, 'adsb_base + adsb_tapa + adsb_radomo', 'LNA 72 × 34 × 20 · 4 × M3 · junta 1 mm', C['gps'], ''),
    ]
    dims = ['Aislador Ø50 × 20 mm · 3 + 3 insertos M4',
            'Cubos de aluminio Ø70 × 12 mm · varillas Ø4 con rosca M4',
            'Cono: 12 × 1010 mm, semiángulo 30° · disco: 12 × 327 mm',
            'Adaptador: 60 mm de alto · M4 ×4 al cubo · M6 ×2 pasantes (z = 12 y z = 32)',
            'ADS-B: LNA 72 × 34 × 20 · SMA 6,6 · PG7 12,7 · 4 radiales de 68 mm']
    return _montaje('Montaje del discone y de la antena ADS-B: secuencia y despiece', pasos, capas, dims)


def montaje_mla_gps():
    pasos = [
        ('mla_caja_base: 4 bosses M3 en las esquinas',
         'Interior de 90 × 60 × 36 mm (MLA_CAJA) · medias cañas laterales para los extremos del lazo',
         'PG7 para la salida del cable'),
        ('mla_junta (TPU, 1,6 mm) entre base y tapa',
         'mla_caja_tapa con 4 × M3 en los bosses (M3 × 12 inox, manual 15)',
         'Sellar las medias cañas con silicona neutra'),
        ('mla_cruz en el poste',
         'Varillas de fibra Ø10 · U M6 al poste · M3 en los brazos',
         'Poste no metálico · MLA a ≥ 5 m del mástil'),
        ('mla_clip_lazo ×4 sobre el lazo',
         'Para coaxial Ø7 (MLA_COAX)',
         'Un clip en la punta de cada brazo de la cruz'),
        ('funda_sma y funda_n (TPU) con cinta autoamalgamante',
         'funda_sma: interior 9,5 × 40 mm · funda_n: 17 × 50 mm',
         'Cinta autoamalgamante sobre la funda, de abajo arriba'),
        ('GPS: gps_soporte',
         'Puck de 48 × 40 × 15 mm · 4 agujeros Ø6,6 (M6) en x = ±16,5 e y = ±27',
         'Tornillería del puck: PENDIENTE DE CONFIRMAR'),
        ('soporte_fibra para la antena de fibra',
         'Brazo Ø25 ↔ fibra Ø26 · 64 × 20 mm · M6',
         'Tuercas y arandelas: PENDIENTE DE CONFIRMAR'),
        ('brazo_mastil, tapon_brazo, separador_coax y clip_filtro',
         'Mástil Ø40 ↔ brazo Ø25 · 80 × 22 mm · M8 al mástil y M6 al brazo',
         'separador_coax cada 50 cm, a 30 mm del mástil, con brida'),
    ]
    capas = [
        (2, 'mla_caja_tapa', '4 × M3 · PG7', C['sdr'], '4 × M3'),
        (2, 'mla_junta (TPU 1,6)', 'entre base y tapa', C['gnd'], ''),
        (1, 'mla_caja_base', 'bosses M3 · 90 × 60 × 36', C['ink'], ''),
        (3, 'mla_cruz + mla_clip_lazo ×4', 'varillas Ø10 · U M6 · coaxial Ø7', C['rf'], ''),
        (5, 'funda_sma · funda_n', 'TPU + cinta autoamalgamante', C['lora'], ''),
        (6, 'gps_soporte · soporte_fibra', 'puck 48 × 40 × 15 · Ø25 ↔ Ø26', C['gps'], ''),
        (8, 'brazo_mastil · tapon_brazo', 'separador_coax · clip_filtro', C['gnd'], ''),
    ]
    dims = ['Caja MLA: interior 90 × 60 × 36 mm · junta TPU 1,6 mm · 4 bosses M3',
            'mla_cruz: varillas Ø10 · U M6 · mla_clip_lazo para coaxial Ø7',
            'funda_sma: interior 9,5 × 40 · funda_n: 17 × 50 (TPU)',
            'gps_soporte: puck 48 × 40 × 15 · 4 × Ø6,6 · tubo Ø25',
            'brazo_mastil: mástil Ø40 y brazo Ø25 · 80 × 22 · M8 al mástil y M6 al brazo',
            'separador_coax: coaxial Ø7,5 · a 30 mm del mástil']
    return _montaje('Montaje de la MLA-30, GPS y accesorios RF: secuencia y despiece', pasos, capas, dims)


def montaje_crucetas():
    pasos = [
        ('Elige la cruceta según el par de tubos',
         'mastil_brazo (Ø40,6 / Ø25,4) · mastil_quad (Ø40,6 / boom 20,4) · brazo_fibra (Ø25,4 / Ø26) · brazo_tubo',
         'Cada cruceta = cuerpo + 2 tapas (brazo_tubo: tapa ×2)'),
        ('Tuercas hexagonales M6 en el cuerpo',
         'Tuerca de 11,3 × 5,4 mm en su alojamiento · 4 por cruceta',
         'Canales en gota: se imprimen sin soportes'),
        ('Tubo inferior en el semicanal del cuerpo',
         'Mástil Ø40,6 o brazo Ø25,4',
         'Apriete de diseño: 1 mm'),
        ('Tapa B (tubo inferior) con los tornillos desde abajo',
         '2 × M6×50 (lado mástil) o M6×40 · tuerca capturada cerca del extremo superior',
         '4 arandelas por cruceta'),
        ('Tubo superior y tapa A',
         '2 × M6 con arandela · tuercas capturadas cerca de la base',
         'Brazo, boom, fibra o tubo'),
        ('Tornillo autotaladrante antigiro',
         'Autotaladrante Ø4,8 × 19 · agujero de 5,2 mm en la tapa a x = L/4',
         '2 por cruceta'),
        ('Apriete final y comprobación',
         'Aprieta alternando los tornillos de cada tapa',
         'Par de apriete: PENDIENTE DE CONFIRMAR'),
    ]
    capas = [
        (5, 'tapa A (tubo superior)', 'tuercas M6 cerca de la base', C['sdr'], '2 × M6 + arandela'),
        (5, 'tubo superior', 'brazo / boom / fibra / tubo', C['gnd'], ''),
        (2, 'cuerpo de la cruceta', '4 tuercas hex M6 · canales en gota', C['ink'], ''),
        (3, 'tubo inferior', 'mástil Ø40,6 / brazo Ø25,4', C['gnd'], 'desde abajo'),
        (4, 'tapa B (tubo inferior)', 'M6 desde abajo · tuerca arriba', C['sdr'], ''),
    ]
    dims = ['MAST_D 40,6 · ARM_D 25,4 · FIBRA_D 26 · BOOM 20,4 mm',
            'Agujero M6 6,6 mm · tuerca hex 11,3 × 5,4 mm · apriete 1 mm',
            'Altura del cuerpo = prof(dA) + prof(dB) + 8 · longitud = max(dA, dB) + 44',
            'Antigiro: autotaladrante Ø4,8 · agujero 5,2 en x = L/4',
            'Tornillería: 4 × M6×50 (lado mástil) o M6×40 (boom, fibra, tubo) · 4 tuercas · 4 arandelas']
    return _montaje('Montaje de las crucetas de anclaje: secuencia y despiece', pasos, capas, dims)


def montaje_sensores_pico():
    pasos = [
        ('sensor_viento_brida: tuercas en sus alojamientos',
         'Patrón A: 4 × Ø6,4 sobre Ø47,1 con tuerca M5 (Ø9,4) · patrón B: 4 × Ø4,8 sobre Ø68 con M4 (Ø8,1)',
         'Se imprime volteada'),
        ('Brida sobre el tubo del brazo',
         '2 prisioneros M5 · marca N hacia el norte geográfico',
         'Veleta y anemómetro con su patrón'),
        ('Sensor sobre la brida',
         '4 tornillos M5 o M4 según el patrón',
         'Longitud: PENDIENTE DE CONFIRMAR'),
        ('pluvio_vaso sobre el poste de Ø40',
         '3 insertos M5 a r = 40 mm · 2 prisioneros M5',
         'Se imprime volteado'),
        ('pluvio_plataforma sobre el vaso',
         '160 × 70 × 6 mm · 3 × M5×40 de nivelación con muelle · 3 × M3 en ranuras',
         'Nivelación con los 3 M5'),
        ('pico_soporte a la rejilla de la caja v3',
         '80 × 100 × 3 mm · 4 × M3×8 a la rejilla de 20 mm',
         'Pico y placa perforada con 8 × M2×6'),
        ('Cableado del Pico',
         'GP4 SDA · GP5 SCL · GP22 DS18B20 · GP15 lluvia · GP16/17 PWM · GP18/19 TACH',
         'Los pines del Pico no toleran 5 V (esquema 16)'),
    ]
    capas = [
        (3, 'anemómetro / veleta', 'sobre la brida', C['i2c'], '4 × M5 o M4'),
        (2, 'sensor_viento_brida ×2', 'D92 · marca N', C['ink'], '2 prisioneros M5'),
        (5, 'pluvio_plataforma', '160 × 70 × 6', C['sdr'], '3 × M5×40 + muelles'),
        (4, 'pluvio_vaso', '3 insertos M5 · poste Ø40', C['sdr'], ''),
        (6, 'Pico + placa perforada', '8 × M2×6', C['pi'], '4 × M3×8'),
        (6, 'pico_soporte 80 × 100 × 3', 'rejilla M3 de 20 mm', C['ink'], ''),
    ]
    dims = ['Brida: D92 · patrón A 4 × Ø6,4 en Ø47,1 (M5) · patrón B 4 × Ø4,8 en Ø68 (M4)',
            'Vaso: poste Ø40 · 3 insertos M5 a r = 40 · 2 prisioneros M5',
            'Plataforma 160 × 70 × 6 mm · 3 × M5 de nivelación con muelle · 3 ranuras M3',
            'pico_soporte 80 × 100 × 3 · separadores M2 de 47 × 11,4 · placa 46 × 66 con M2',
            'El Pico no tolera 5 V · pines: manual 20 y esquema 16']
    return _montaje('Montaje de sensores de viento, lluvia y soporte del Pico: secuencia y despiece', pasos, capas, dims)


def mapa_piezas_mastil():
    W, H = 1500, 898
    b = markers([C['or']])
    b += f"<rect x='296' y='76' width='8' height='700' fill='{C['line']}'/>"
    filas = [
        ('2,9 m', 'Punta: discone', C['rf'],
         ['discone_aislador · discone_plantilla_disco y _cono · discone_adaptador_mastil · discone_capuchon · tapon_varilla ×12',
          'Manual 13 · esquema 35']),
        ('2,0 m', 'Collar de vientos (sin pieza impresa)', C['gnd'],
         ['3 cables de acero Ø3 (manual 11)']),
        ('1,7 m', 'Brazo E/O', C['sdr'],
         ['cruceta_mastil_brazo · brazo_mastil · tapon_brazo',
          'E: ADS-B (adsb_base, adsb_tapa, adsb_radomo) a 0,8 m y GPS (gps_soporte) a 0,4 m · O: fibra 433 (soporte_fibra) a 0,8 m',
          'Esquemas 35, 36 y 37']),
        ('1,5 m', 'Brazo N/S', C['i2c'],
         ['cruceta_mastil_brazo · 2 × cruceta_brazo_tubo (cuerpo + 2 tapas cada una)',
          'N: anemómetro · S: veleta · sensor_viento_brida ×2 (marca N al norte geográfico) · esquema 38']),
        ('0,95 m', 'Quad 2 m / 70 cm', C['cr'],
         ['quad_abrazadera o cruceta_mastil_quad · boom con rumbo 205°',
          'quad_buje_2m ×2 · quad_buje_70 ×2 · punteras · clips · alimentadores · esquema 34']),
        ('0,2 m', 'Brazo N/S', C['sdr'],
         ['cruceta_mastil_brazo · 2 × cruceta_brazo_tubo',
          'N: Bigsignal 868 · S: iGate 433 · esquema 37']),
        ('0,05 m', 'Garita meteorológica (caja v2)', C['pi'],
         ['garita_base · garita_plato ×6 · garita_tapa · 3 varillas M4×140',
          'Sensor GYBMEP (M2 ×2) · esquema 31']),
    ]
    for k, (h, t, col, lin) in enumerate(filas):
        y0 = 80 + k * 100
        b += txt(288, y0 + 48, 'h = ' + h, 12, C['ink'], True, 'end')
        b += arrow(300, y0 + 44, 340, y0 + 44, C['or'])
        b += box(340, y0, 1136, 88, t, lin, col)
    b += box(340, 780, 1136, 88, 'Cajas y piezas fuera del mástil', [
        'Cajas: v2 con soporte_mastil ×2 (M4×20) · v3 con soporte_mastil ×2 (M5 + U M8) o pletina_pared ×2 · esquemas 31, 32 y 33',
        'Fuera del mástil: MLA-30 (≥ 5 m, poste no metálico) y pluviómetro en poste Ø40 a 1 m (pluvio_vaso + pluvio_plataforma)',
        'Mástil Ø40 a tierra con 16 mm² · lazos de goteo y separador_coax cada 50 cm'], C['cr'])
    return svg(W, H, b, 'Mapa de piezas impresas en el mástil')


# ---------------------------------------------------------------------
#  40-49: component layout and wiring of every box (manual 52, chapter 6 bis).
#  Positions are taken from hardware/caja/caja_bricohams.scad and
#  hardware/caja_v3/caja_v3.scad (plate-local mm, y grows towards the lid
#  side of the drawing). Anything the .scad does not define is drawn dashed
#  and marked PENDIENTE DE CONFIRMAR.
# ---------------------------------------------------------------------
WIRE = {'L': '#8d5524', 'N': '#039be5', 'PE': '#2e7d32', 'V12': '#c62828', 'GND': '#37474f',
        'V5': '#ef6c00', 'USB': '#3949ab', 'RF': '#6a1b9a', 'SIG': '#00838f'}


def _plano(titulo, paneles, notas, k=2.0, gap=36, wmin=0):
    # paneles: (name, W, H, items); item: (x, y, w, h, label, sub, colour, sides[, pending])
    # sides: N/S/E/W bars mark the face where the connectors point.
    top, ox, b = 120, 30, ''
    hmax = max(p[2] for p in paneles)
    for nombre, pw, ph, items in paneles:
        b += txt(ox, top - 12, nombre, 13, C['cr'], True)
        b += f"<rect x='{ox}' y='{top}' width='{pw * k}' height='{ph * k}' fill='#fffde7' stroke='{C['ink']}' stroke-width='2'/>"
        for it in items:
            x, y, w, h, lab, sub, col, lado = it[:8]
            d = " stroke-dasharray='5 3'" if len(it) > 8 else ''
            px, py = ox + x * k, top + (ph - y - h) * k
            b += f"<rect x='{px}' y='{py}' width='{w * k}' height='{h * k}' fill='#fff' fill-opacity='0.85' stroke='{col}' stroke-width='1.6'{d}/>"
            b += txt(px + w * k / 2, py + h * k / 2 - 2, lab, 10, col, True, 'middle')
            b += txt(px + w * k / 2, py + h * k / 2 + 11, sub, 8.5, C['mute'], False, 'middle')
            for s in lado:
                bx, by, bw, bh = {'N': (px, py - 4, w * k, 4), 'S': (px, py + h * k, w * k, 4),
                                  'W': (px - 4, py, 4, h * k), 'E': (px + w * k, py, 4, h * k)}[s]
                b += f"<rect x='{bx}' y='{by}' width='{bw}' height='{bh}' fill='{C['or']}'/>"
        ox += pw * k + gap
    y = top + hmax * k + 30
    b += f"<rect x='30' y='{y - 12}' width='20' height='5' fill='{C['or']}'/>" + txt(58, y - 6, 'barra naranja = cara hacia la que miran los conectores (N = arriba del dibujo, S = hacia la pared de pasamuros)', 10.5)
    for i, t in enumerate(notas):
        b += txt(30, y + 18 + i * 17, t, 10.5)
    return svg(int(max(ox, wmin)), int(y + 36 + len(notas) * 17), b, titulo)


def rejilla_caja_v2():
    """Diagram 40: caja v2 plates (placa_electronica, placa_potencia, tapa_potencia)."""
    s, d, m, l = C['sdr'], C['gnd'], C['pwr'], C['lora']
    pe = ('placa_electronica 138 × 210 (abs. 79,6 · 6)', 138, 210, [
        (42, 141, 85, 56, 'Pi 5 + HAT', '4 × M2.5 (58 × 49)', C['pi'], '', 1),
        (3, 16, 26, 54, 'Mini RTL-SDR', 'nervios + bridas', s, 'NS'),
        (33, 16, 26, 85, 'RTL-SDR V3', 'nervios + bridas', s, 'NS'),
        (63, 16, 26, 85, 'FlightStick', 'nervios + bridas', s, 'NS'),
        (93, 16, 26, 50, 'Diplexor', 'bridas', d, '')])
    pp = ('placa_potencia 58 × 210 (abs. 9,2 · 6)', 58, 210, [
        (-3.5, 4, 65, 95, 'Cargador 45 W', 'bridas · sale 3,5 mm', m, 'N'),
        (9, 105, 40, 100, 'Hub USB', 'bridas', s, '')])
    tp = ('tapa_potencia (CP_Z = 56)', 69, 210, [
        (5, 118, 29.4, 67.4, 'LilyGO Mesh', 'cuna 29,4 × 67,4', l, '', 1),
        (38, 118, 29.4, 67.4, 'LilyGO iGate', 'cuna 29,4 × 67,4', l, '', 1)])
    notas = ['Posiciones del .scad (x, y desde la esquina inferior izquierda de cada placa). Rayado = orientación o alto PENDIENTE DE CONFIRMAR.',
             'Dongles: USB (N) hacia el pasamuros del tabique, SMA (S) hacia la fila SMA de la pared. Pi, hub y cargador: cara de conectores PENDIENTE.',
             'El cargador (65 mm) es más ancho que la placa (58 mm): el .scad solo lo dibuja con ghost() y lo sujeta con bridas.',
             'Fuente: hardware/caja/caja_bricohams.scad · manual 52, capítulo 6 bis.']
    return _plano('Rejilla de la caja v2: dónde va cada componente', [pe, pp, tp], notas, 2.0, 36, 700)


def rejilla_v3_electronica():
    """Diagram 41: v3 electronics box: placa_rejilla, bandeja_sdr, bandeja_sdr2 and Pi tray."""
    s, d, m, p = C['sdr'], C['gnd'], C['pwr'], C['pi']
    pl = ('placa_rejilla 211 × 223 (abs. 7,8 · 7,8)', 211, 223, [
        (12, 28, 26, 85, 'Mini', 'soporte_dongle', s, 'NS'), (46, 28, 26, 85, 'V3', 'soporte_dongle', s, 'NS'),
        (80, 28, 26, 85, 'Flight', 'soporte_dongle', s, 'NS'),
        (114, 28, 98, 88, 'RSPdx (bahía 100 × 90)', 'soporte_sdrplay', s, 'NS'),
        (20, 136, 145, 44, 'Hub USB 10 p.', 'soporte_hub · medir', d, '', 1),
        (182, 132, 26, 50, 'Diplexor', 'bahía 26 × 50', d, '', 1),
        (90, 186, 60, 26, 'WAGO 221-415 ×3', 'soporte_wago', m, ''),
        (20, 186, 60, 26, 'Reserva', 'ATO · 12→5 V · HL2', m, '', 1)])
    d1 = ('bandeja_sdr 167 × 170 (+38 mm)', 167, 170, [
        (20, 82, 120, 75, 'HackRF (HRF)', 'SMA W · USB E', s, 'WE'),
        (12, 20, 85, 26, 'RTL-SDR V4', 'dongle', s, 'WE'),
        (112, 6, 45, 60, 'Airspy HF+ (AHF)', 'conectores N/S', s, 'NS')])
    d2 = ('bandeja_sdr2 (+82 mm · tamaño PENDIENTE)', 167, 170, [
        (4, 85, 125, 62, 'Hermes-Lite 2', '12 V + Ethernet', s, '', 1),
        (4, 6, 85, 26, 'S1', 'dongle', s, 'WE'), (4, 36, 85, 26, 'S2', 'dongle', s, 'WE'),
        (100, 6, 52, 30, 'S3', 'Airspy Mini…', s, 'WE'), (100, 38, 52, 24, 'S4', 'RSP1B…', s, 'WE'),
        (136, 86, 26, 60, 'S5', 'vertical', s, 'NS')])
    bp = ('bandeja Pi 170 × 92 (+131 mm)', 170, 92, [
        (8, 10, 85, 56, 'Pi 5 + HAT', 'M2.5 · 58 × 49', p, '', 1),
        (98, 12, 29.4, 67.4, 'LilyGO', 'soporte_lilygo', C['lora'], '', 1),
        (129, 12, 32.8, 62.8, 'RAK', 'soporte_rak', C['lora'], '', 1)])
    notas = ['Cotas del .scad (EL_RES, SDR_DECK, SDR_DECK2, PI_OFF) relativas a la esquina inferior izquierda de cada placa. Rayado = orientación PENDIENTE DE CONFIRMAR.',
             'La bahía del RSPdx (100 × 90) sobresale ≈ 3 mm de la placa (210,8): se dibuja el volumen de 98 × 88. Postes: 38 / 41 / 46 mm.',
             'HackRF: SMA a la izquierda y USB a la derecha (manual 17). Dongles verticales: USB hacia el hub (N), SMA hacia la pared N (S).',
             'Fuente: hardware/caja_v3/caja_v3.scad · manual 17 · manual 52, capítulo 6 bis.']
    return _plano('Rejilla de la caja v3 electrónica: placa, bandejas de SDR y bandeja de la Pi', [pl, d1, d2, bp], notas, 1.5, 36, 1250)


def rejilla_v3_potencia():
    """Diagram 42: v3 power box grid plate (positions converted from box to plate coordinates)."""
    m, d = C['pwr'], C['gnd']
    pl = ('placa_rejilla 154 × 182 (abs. 7,8 · 7,8)', 154, 182, [
        (37, 22, 80, 80, 'Base Schuko', 'soporte_schuko · 2 × M4 + 4 × M3', m, 'S'),
        (42, 32, 70, 70, 'Cargador 120 W', 'enchufado a la base', m, ''),
        (22, 104, 110, 16, 'brida_cargador', '2 × M3', d, ''),
        (12, 132, 60, 20, 'Gatillo PD 12 V', 'sin soporte', m, '', 1),
        (82, 132, 60, 26, 'WAGO + fusibles', 'sin soporte', m, '', 1)])
    notas = ['Cotas del .scad (Schuko 80 × 80 × 42 en y = 30, cargador 70 × 70 × 32 a z = 42, gatillo en (20, 140), WAGO en (90, 140), cotas de la caja).',
             'El cable de 230 V entra por el PG9 de la cara inferior (S) a la base Schuko; el cargador se enchufa directamente en la base.',
             'Rayado = sin pieza impresa en el .scad: posición orientativa, PENDIENTE DE CONFIRMAR. Medir la base Schuko y el cargador reales.',
             'Fuente: hardware/caja_v3/caja_v3.scad · manual 17 · manual 52, capítulo 6 bis.']
    return _plano('Rejilla de la caja v3 potencia: Schuko, cargador de 120 W y 12 V', [pl], notas, 2.0, 36, 760)


def rejilla_v3_sai():
    """Diagram 43: v3 SAI box grid plate (SAI_LAYOUT)."""
    m, d = C['pwr'], C['gnd']
    pl = ('placa_rejilla 211 × 223 (abs. 7,8 · 7,8)', 211, 223, [
        (50, 4, 159, 106, 'soporte_bateria', 'correas 20-22 mm', C['line'], ''),
        (54, 8, 151, 100, 'Batería 12 V 151 × 100 × 65', 'de pie · bornes arriba', d, 'N'),
        (6, 6, 40, 216, 'PCB SAI', 'guia_pcb ×2 (y 18, 168)', m, 'E'),
        (50, 118, 84, 70, 'Trafo 80 × 62 × 65', 'pletina_trafo · M5', m, '', 1),
        (138, 118, 34, 86, 'Filtro EMI salida', 'soporte_filtro · M4', C['sdr'], '', 1),
        (176, 118, 34, 86, 'Filtro EMI entrada', 'soporte_filtro · M4', C['sdr'], '', 1),
        (50, 194, 84, 28, 'ATO 15 A + WAGO', 'soporte_wago', m, '')])
    notas = ['Cotas del .scad (SAI_LAYOUT, GUIA_Y, SAI_PCB 210 × 70 de canto con los componentes hacia +X). Rayado = orientación de bornes PENDIENTE DE CONFIRMAR.',
             'La batería deja los bornes arriba (N): el fusible ATO de 15 A debe quedar a ≤ 10 cm del borne positivo.',
             'Entradas de 230 V por los PG9 de la cara inferior; ventilas de entrada (abajo) y salida (arriba) siempre despejadas por el hidrógeno.',
             'Fuente: hardware/caja_v3/caja_v3.scad · manual 17 · manual 52, capítulo 6 bis.']
    return _plano('Rejilla de la caja v3 SAI: batería, placa, trafo, filtros EMI y fusible', [pl], notas, 2.0, 36, 800)


def _nodo(x, y, w, h, t, sub='', c=None, dash=False, fill='#f7f9fb'):
    c = c or C['ink']
    d = " stroke-dasharray='5 3'" if dash else ''
    s = f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='5' fill='{fill}' stroke='{c}' stroke-width='1.6'{d}/>"
    s += txt(x + w / 2, y + (h / 2 - 1 if sub else h / 2 + 4), t, 10, c, True, 'middle')
    if sub:
        s += txt(x + w / 2, y + h / 2 + 11, sub, 8.5, C['mute'], False, 'middle')
    return s


def _cable(kind, pts, label='', pos=None, dash=False):
    # kind: key of WIRE, or 'LN' / 'LNPE' for a mains bundle (brown + blue [+ green])
    pl = ' '.join(f'{x},{y}' for x, y in pts)
    d = " stroke-dasharray='6 4'" if dash else ''
    if kind in ('LN', 'LNPE'):
        s = f"<polyline points='{pl}' fill='none' stroke='{WIRE['L']}' stroke-width='7'/>"
        s += f"<polyline points='{pl}' fill='none' stroke='{WIRE['N']}' stroke-width='4'/>"
        if kind == 'LNPE':
            s += f"<polyline points='{pl}' fill='none' stroke='{WIRE['PE']}' stroke-width='1.6'/>"
        col = WIRE['L']
    elif kind == 'PE':
        s = (f"<polyline points='{pl}' fill='none' stroke='{WIRE['PE']}' stroke-width='3.5'/>"
             f"<polyline points='{pl}' fill='none' stroke='#ffd600' stroke-width='3.5' stroke-dasharray='6 6'/>")
        col = WIRE['PE']
    else:
        col = WIRE[kind]
        s = f"<polyline points='{pl}' fill='none' stroke='{col}' stroke-width='2.2'{d} marker-end='url(#a{col[1:]})'/>"
    if label:
        lx, ly = pos or ((pts[0][0] + pts[1][0]) / 2 + 4, (pts[0][1] + pts[1][1]) / 2 - 4)
        s += txt(lx, ly, label, 9, col, True)
    return s


def _pasamuros(x, y, nombre, destino='', col=None, largo=170):
    col = col or WIRE['RF']
    s = f"<circle cx='{x}' cy='{y}' r='7' fill='#fff' stroke='{col}' stroke-width='2'/>" + txt(x, y + 21, nombre, 8.5, C['ink'], True, 'middle')
    if destino:
        s += f"<line x1='{x}' y1='{y - 7}' x2='{x}' y2='{y - largo}' stroke='{col}' stroke-width='1.6' marker-end='url(#a{col[1:]})'/>"
        s += f"<text x='{x + 4}' y='{y - 12}' font-size='8.5' fill='{col}' transform='rotate(-90 {x + 4} {y - 12})'>{esc(destino)}</text>"
    return s


def _leyenda(x, y):
    items = [('L', 'L 230 V marrón'), ('N', 'N 230 V azul'), ('PE', 'PE verde/amarillo'), ('V12', '12 V rojo'),
             ('GND', 'GND negro'), ('V5', '5 V'), ('USB', 'USB'), ('RF', 'coaxial RF'), ('SIG', 'señal / I2C / 1-Wire')]
    s = txt(x, y, 'Código de colores', 11, C['ink'], True)
    for i, (k, t) in enumerate(items):
        s += f"<line x1='{x}' y1='{y + 14 + i * 17}' x2='{x + 28}' y2='{y + 14 + i * 17}' stroke='{WIRE[k]}' stroke-width='3.5'/>" + txt(x + 36, y + 18 + i * 17, t, 10)
    return s


def _wmark():
    return markers(sorted(set(WIRE.values())))


def cableado_caja_v2():
    """Diagram 44: wiring of the v2 box (single box, 230 V compartment on the left)."""
    W, H = 1180, 840
    b = _wmark()
    b += f"<rect x='40' y='100' width='760' height='520' rx='10' fill='none' stroke='{C['ink']}' stroke-width='3'/>"
    b += f"<rect x='60' y='130' width='260' height='470' rx='6' fill='#fdecea' stroke='{C['pwr']}' stroke-width='1.4' stroke-dasharray='6 4'/>"
    b += txt(70, 124, 'COMPARTIMENTO DE POTENCIA (230 V)', 10, C['pwr'], True) + txt(340, 124, 'ELECTRÓNICA (placa_electronica)', 10, C['sdr'], True)
    b += _nodo(100, 150, 110, 50, 'WAGO 221-412 ×2', 'L · N (empalme)', C['pwr'])
    b += _nodo(80, 260, 110, 70, 'Cargador 45 W', 'USB-C PD + USB-A', C['pwr'])
    b += _nodo(80, 380, 110, 80, 'Hub USB', 'alimentado (USB-A)', C['sdr'])
    b += _nodo(210, 380, 100, 80, 'LilyGO ×2', 'tapa_potencia', C['lora'])
    b += _nodo(80, 490, 230, 60, 'Filtro EMI / fusible', 'no previstos: PENDIENTE DE CONFIRMAR', C['gnd'], True)
    b += _nodo(520, 160, 150, 90, 'Pi 5 + HAT', 'SDR · LoRa · GPS · RTC', C['pi'])
    b += _nodo(700, 150, 80, 40, 'Cámara', 'tapa · CSI', C['cam'])
    for x, t in ((360, 'Mini'), (440, 'V3'), (520, 'Flight')):
        b += _nodo(x, 300, 70, 50, t, 'USB', C['sdr'])
    b += _nodo(610, 300, 90, 50, 'Diplexor', 'HF / VHF', C['gnd'])
    b += _cable('LN', [(70, 613), (70, 175), (100, 175)]) + txt(14, 400, 'A1 230 V', 9, WIRE['L'], True)
    b += _cable('LN', [(130, 200), (130, 260)], 'A3', (134, 236))
    b += _cable('V5', [(190, 280), (300, 280), (300, 195), (520, 195)], 'A4 USB-C 5 V 3 A', (230, 272))
    b += _cable('V5', [(150, 330), (150, 380)], 'A5', (154, 360))
    b += _cable('USB', [(135, 380), (135, 350), (315, 350), (315, 275), (555, 275), (555, 250)], 'A6 hub → Pi', (320, 268))
    for x in (395, 475, 555):
        b += _cable('USB', [(x, 275), (x, 300)])
    b += _cable('USB', [(190, 420), (210, 420)])
    b += _cable('SIG', [(670, 175), (700, 175)], 'A12 CSI', (672, 168))
    b += _cable('SIG', [(740, 613), (740, 260), (670, 230)], 'A11 Cat6', (746, 420))
    b += _pasamuros(75, 620, 'PG9 230 V', '', WIRE['L'])
    rf = [('SAT', 'RTL-SDR del HAT'), ('HAM', 'Mini RTL-SDR'), ('VHF', 'diplexor (VHF) → V3'), ('HF', 'MLA-30 → diplexor → V3'),
          ('ADSB', 'bias-tee 5 V → FlightStick'), ('868', 'SX1262 del HAT'), ('GPS', 'GPS del HAT'),
          ('M433', 'LilyGO Mesh (muesca)'), ('IG433', 'FBP-433s → LilyGO iGate')]
    for i, (n, t) in enumerate(rf):
        b += _pasamuros(350 + 36 * i, 620, n, t)
    b += _pasamuros(690, 620, 'PG7 WX', 'BME280 4×0,25 apantallado ≤ 5 m', WIRE['SIG'], 90)
    b += _pasamuros(740, 620, 'M20 LAN', '', WIRE['SIG'])
    b += _leyenda(850, 130)
    notas = ['• Fila inferior: 9 pasamuros SMA (SAT … IG433, paso 15 mm, z = 26), PG7 WX, M20 LAN y PG9 230 V. Sin PE: cargador clase II y caja de plástico; manguera H07RN-F 2 × 1 mm² (opción A: cable del cargador cortado a 15 cm y empalmado con 2 × WAGO 221-412).',
             '• Los coaxiales internos son latiguillos RG-316 de 20 cm SMA–SMA; el mástil va a tierra por fuera (16 mm²). Diferencial de 30 mA aguas arriba.',
             '• El pasamuros del tabique (pasamuros_usb, 5 ranuras) lleva USB-C, USB del hub y datos de los dongles al compartimento de electrónica.',
             '• Numeración A1… como en la tabla de cableado interno del manual 52 (capítulo 6 bis, caja v2).']
    for i, t in enumerate(notas):
        b += txt(40, 690 + i * 18, t, 10.5)
    return svg(W, H, b, 'Cableado interno de la caja v2')


def cableado_v3_electronica():
    """Diagram 45: wiring of the v3 electronics box (12 V bus, USB hub, Pico, RF stubs)."""
    W, H = 1260, 900
    b = _wmark()
    b += f"<rect x='40' y='90' width='1000' height='700' rx='10' fill='none' stroke='{C['ink']}' stroke-width='3'/>"
    b += _nodo(110, 125, 170, 50, 'WAGO 221-415 ×3', '+12 V · GND · reserva', C['pwr'])
    b += _nodo(300, 125, 170, 50, 'Fusibles ATO', '2 A hub · 1 A fans · 1 A viento', C['pwr'])
    b += _nodo(490, 125, 200, 50, 'Filtro π 12 V', '2×2200 µF · 100 nF · 10 µH (PENDIENTE)', C['gnd'], True)
    b += _nodo(720, 125, 150, 60, 'Pi 5 + HAT', 'bandeja Pi', C['pi'])
    b += _cable('V12', [(280, 150), (300, 150)]) + _cable('V12', [(470, 150), (490, 150)])
    b += f"<line x1='110' y1='205' x2='960' y2='205' stroke='{WIRE['V12']}' stroke-width='3'/><line x1='110' y1='218' x2='960' y2='218' stroke='{WIRE['GND']}' stroke-width='3'/>"
    b += txt(965, 209, '+12 V', 9, WIRE['V12'], True) + txt(965, 222, 'GND', 9, WIRE['GND'], True)
    b += _cable('V12', [(385, 175), (385, 205)])
    cons = [(110, 150, 'Hub USB 10 p.', '2 A'), (290, 110, 'Ventilador IN', '1 A'), (420, 110, 'Ventilador OUT', '1 A'),
            (570, 140, 'RS485 viento', '1 A → PG7'), (730, 120, 'HL2 12 V', 'reserva 3 A'), (870, 130, '12→5 V ×2', 'reserva')]
    for x, w, t, s2 in cons:
        b += _nodo(x, 240, w, 50, t, s2, C['pwr'], t in ('HL2 12 V', '12→5 V ×2'))
        b += _cable('V12', [(x + w // 2 - 8, 205), (x + w // 2 - 8, 240)])
        b += _cable('GND', [(x + w // 2 + 8, 218), (x + w // 2 + 8, 240)])
    b += f"<line x1='185' y1='290' x2='185' y2='330' stroke='{WIRE['USB']}' stroke-width='3'/><line x1='185' y1='330' x2='1010' y2='330' stroke='{WIRE['USB']}' stroke-width='3'/>"
    b += _cable('USB', [(1010, 330), (1010, 155), (870, 155)], 'E15 hub → Pi USB 3.0', (880, 148))
    usb = [(110, 60, 'Mini'), (180, 60, 'V3'), (250, 70, 'Flight'), (330, 70, 'RSPdx'), (410, 130, 'HRF·V4·AHF'), (550, 80, 'bias-tee'),
           (640, 80, 'inyector'), (730, 60, 'LilyGO'), (800, 60, 'RAK'), (870, 60, 'Pico'), (940, 60, 'RS485')]
    for x, w, t in usb:
        b += _nodo(x, 360, w, 50, t, 'USB', C['sdr'])
        b += _cable('USB', [(x + w // 2, 330), (x + w // 2, 360)])
    b += _nodo(780, 450, 110, 50, 'Q1 · Q2 2N7002', 'PWM ventiladores', WIRE['SIG']) + _nodo(900, 450, 100, 50, 'DS18B20', '1-Wire GP22', WIRE['SIG'])
    b += _cable('SIG', [(880, 410), (880, 450)]) + _cable('SIG', [(915, 410), (915, 450)])
    b += _cable('SIG', [(780, 480), (325, 480), (325, 290)], 'PWM + TACH (C18)', (460, 474))
    b += _cable('SIG', [(780, 495), (410, 495), (410, 265), (420, 265)])
    b += _nodo(110, 540, 90, 50, 'Diplexor', 'HF / VHF', C['gnd']) + _nodo(210, 540, 100, 50, 'FBP-433s', 'sobre clip_filtro', C['rf'])
    b += _nodo(920, 540, 100, 50, 'Cámara', 'tapa · CSI', C['cam']) + _cable('SIG', [(1020, 565), (1030, 565), (1030, 175), (870, 175)], 'CSI', (1034, 400))
    b += _cable('V12', [(60, 783), (60, 160), (110, 160)], 'E2 +12 V', (14, 420)) + _cable('GND', [(72, 783), (72, 168), (110, 168)])
    b += _cable('V5', [(84, 783), (84, 100), (795, 100), (795, 125)], 'E1 USB-C PD 5 V', (400, 94))
    b += _cable('SIG', [(100, 783), (100, 112), (760, 112), (760, 125)], 'E-LAN Cat6', (300, 109))
    b += _pasamuros(60, 790, 'M25 PWR', '', WIRE['V12']) + _pasamuros(100, 790, 'M20 LAN', '', WIRE['SIG'])
    for i, (n, t) in enumerate((('WX', 'BME280 → Pico GP4/GP5'), ('VIENTO', '4 hilos → RS485 + 12 V'), ('LLUVIA', 'reed → Pico GP15'), ('VENT', 'ePTFE (sin cable)'))):
        b += _pasamuros(140 + 40 * i, 790, 'PG7 ' + n, t, WIRE['SIG'], 150)
    n_rows = [['SAT', 'HAM', 'VHF', 'HF', 'ADSB', '868', 'GPS'], ['M433', 'IG433', 'DISC2', 'HF2', 'R1', 'R2', 'R3'], ['HRF', 'AHF', 'V4', 'R4']]
    dest = {'SAT': 'RTL del HAT', 'HAM': 'Mini', 'VHF': 'diplexor VHF', 'HF': 'inyector → diplexor', 'ADSB': 'bias-tee → Flight', '868': 'SX1262 HAT',
            'GPS': 'GPS HAT', 'M433': 'LilyGO', 'IG433': 'FBP-433s → RAK/LilyGO', 'HRF': 'HackRF', 'AHF': 'Airspy HF+', 'V4': 'RTL-SDR V4'}
    i = 0
    for row in n_rows:
        for n in row:
            b += _pasamuros(320 + 40 * i, 790, 'N ' + n, dest.get(n, 'tapón'), WIRE['RF'], 175 if n in dest else 30)
            i += 1
    b += _leyenda(1070, 120)
    notas = ['• Los 18 pasamuros N (filas z = 26 · 56 · 86) llevan latiguillo RG-316 de 20 cm N–SMA a cada receptor; los libres llevan tapon_n.',
             '• Sin 230 V en este módulo: solo 12 V (manguera 4 × 0,75) y 5 V (USB-C PD). Masa común: GND del WAGO, Pico, MOSFET y ventiladores.',
             '• Las posiciones de la numeración E1… coinciden con la tabla de cableado del manual 52 (capítulo 6 bis, caja v3 electrónica).']
    for k, t in enumerate(notas):
        b += txt(40, 840 + k * 18, t, 10.5)
    return svg(W, H, b, 'Cableado interno de la caja v3 electrónica')


def cableado_v3_potencia():
    """Diagram 46: wiring of the v3 power box."""
    W, H = 1100, 740
    b = _wmark()
    b += f"<rect x='40' y='90' width='700' height='520' rx='10' fill='none' stroke='{C['ink']}' stroke-width='3'/>"
    b += _nodo(60, 360, 200, 100, 'Base Schuko', 'soporte_schuko · bornas L N PE', C['pwr'])
    b += _nodo(80, 240, 160, 90, 'Cargador 120 W', 'USB-C 1 · USB-C 2 · USB-A', C['pwr'])
    b += _nodo(300, 240, 110, 60, 'Gatillo PD', '12 V', C['pwr'])
    b += _nodo(440, 240, 110, 60, 'ATO general', '(PENDIENTE)', C['pwr'], True)
    b += _nodo(300, 130, 400, 60, 'WAGO 221-415', '+12 V · GND · 2 reserva', C['pwr'])
    b += _nodo(480, 350, 220, 80, '2.ª base + adaptador 65 W', 'opción c del hub (PENDIENTE)', C['gnd'], True)
    b += _cable('LN', [(80, 610), (80, 460)]) + _cable('PE', [(110, 610), (110, 460)])
    b += txt(46, 540, 'P1-P3 230 V + PE', 9, WIRE['L'], True)
    b += _cable('LN', [(160, 330), (160, 360)], 'P4', (164, 350))
    b += _cable('V5', [(240, 260), (270, 260), (270, 540), (400, 540), (400, 603)], 'P5 USB-C 5 V', (280, 530))
    b += _cable('USB', [(240, 290), (300, 290)], 'P6', (250, 284))
    b += _cable('V12', [(410, 270), (440, 270)]) + _cable('V12', [(550, 270), (580, 270), (580, 190)], 'P7', (586, 230))
    b += _cable('V12', [(700, 175), (720, 175), (720, 520), (420, 520), (420, 603)], 'P8 12 V + GND + 2 reserva', (440, 514))
    b += _pasamuros(95, 610, 'PG9 230 V', '', WIRE['L']) + _pasamuros(410, 610, 'M25 A ELECTRÓNICA', '', WIRE['V12']) + _pasamuros(560, 610, 'PG7 VENT', '', WIRE['SIG'])
    b += _leyenda(780, 120)
    notas = ['• Entrada: H07RN-F 3G1,5 desde el PG9 «SALIDA» del SAI. La base Schuko recibe L, N y PE; el cargador se enchufa directo.',
             '• Salida por el M25: manguera 4 × 0,75 (+12 V, GND, 2 de reserva) y el cable USB-C PD de 5 V para la Pi.',
             '• Ferrita mix 31 (4 vueltas) en el cable de 12 V a la entrada de la electrónica (ver manual 52, protecciones).']
    for k, t in enumerate(notas):
        b += txt(40, 660 + k * 18, t, 10.5)
    return svg(W, H, b, 'Cableado interno de la caja v3 potencia')


def cableado_v3_sai():
    """Diagram 47: wiring of the v3 SAI box (EMI in → SAI → EMI out, battery fuse)."""
    W, H = 1160, 760
    b = _wmark()
    b += f"<rect x='40' y='90' width='560' height='570' rx='10' fill='none' stroke='{C['ink']}' stroke-width='3'/>"
    b += _nodo(74, 112, 96, 518, 'PCB SAI', 'AC in · AC out · BAT', C['pwr'])
    b += _nodo(180, 112, 202, 67, 'ATO 15 A + WAGO', '≤ 10 cm del borne +', C['pwr'])
    b += _nodo(180, 194, 202, 168, 'Trafo SAI', 'cables según placa (PENDIENTE)', C['pwr'], True)
    b += _nodo(391, 156, 82, 206, 'EMI salida', '6 A · 250 V', C['sdr'])
    b += _nodo(482, 156, 82, 206, 'EMI entrada', '6 A · 250 V', C['sdr'])
    b += _nodo(180, 381, 382, 254, 'Batería 12 V', 'BAT+ rojo · BAT− negro', C['gnd'])
    b += _cable('LNPE', [(261, 660), (261, 652), (580, 652), (580, 300), (564, 300)], 'S1 RED', (400, 646))
    b += _cable('LN', [(523, 156), (523, 102), (122, 102), (122, 112)], 'S2', (300, 98))
    b += _cable('LN', [(170, 372), (432, 372), (432, 362)], 'S3', (300, 368))
    b += _cable('LNPE', [(432, 156), (432, 126), (590, 126), (590, 640), (317, 640), (317, 660)], 'S4 SALIDA + ferrita', (440, 636))
    b += _cable('PE', [(482, 340), (473, 340)])
    b += _cable('V12', [(185, 385), (175, 385), (175, 150), (180, 150)]) + _cable('V12', [(180, 165), (170, 165)], 'S5', (176, 160))
    b += _cable('GND', [(183, 420), (172, 420)])
    b += _cable('USB', [(370, 660), (370, 646), (122, 646), (122, 630)], 'S7 DATOS', (200, 642))
    b += _pasamuros(261, 660, 'PG9 RED', '', WIRE['L']) + _pasamuros(317, 660, 'PG9 SALIDA', '', WIRE['L']) + _pasamuros(370, 660, 'PG7 DATOS', '', WIRE['USB'])
    b += _leyenda(640, 120)
    notas = ['• Orden de la corriente: 230 V red → EMI entrada → placa SAI (trafo + batería con ATO 15 A) → EMI salida → PG9 «SALIDA».',
             '• PE continuo: PG9 RED → EMI entrada → EMI salida → PG9 SALIDA → base Schuko de la caja de potencia.',
             '• Ventilas de entrada (abajo) y salida (arriba) siempre libres: la batería puede desprender hidrógeno.']
    for k, t in enumerate(notas):
        b += txt(40, 700 + k * 18, t, 10.5)
    return svg(W, H, b, 'Cableado interno de la caja v3 SAI')


def interconexion_estacion():
    """Diagram 48: whole station: mains → SAI → power → electronics → mast, sensors, network, earth."""
    W, H = 1500, 1000
    b = _wmark()
    b += _nodo(40, 120, 200, 70, 'Red 230 V', 'magnetotérmico (PEND.) + 30 mA', C['pwr'], False, '#fdecea')
    b += _nodo(300, 110, 230, 90, 'Caja SAI', 'EMI · SAI · batería', C['pwr'])
    b += _nodo(300, 290, 230, 90, 'Caja potencia', 'Schuko · cargador 120 W · PD 12 V', C['pwr'])
    b += _nodo(300, 470, 330, 120, 'Caja electrónica', 'Pi 5 · SDR · hub · Pico · 18 N', C['pi'])
    b += _nodo(300, 700, 230, 60, 'Red Ethernet', 'switch / router (PoE PEND.)', C['net'])
    b += _nodo(40, 600, 200, 70, 'Toma de tierra', 'edificio · mástil 16 mm²', C['pi'])
    b += _nodo(40, 800, 340, 100, 'Alternativa: caja v2 (una sola)', 'PG9 230 V + 9 SMA + WX + LAN', C['gnd'], True)
    b += _cable('LNPE', [(240, 155), (300, 155)], 'X1 3G1,5 · PG9 RED', (244, 146))
    b += _cable('LNPE', [(415, 200), (415, 290)], 'X2 3G1,5 · SALIDA → 230 V', (421, 250))
    b += _cable('V12', [(380, 380), (380, 470)], 'X3 4×0,75 · M25 → M25', (386, 430))
    b += _cable('V5', [(340, 380), (340, 470)], 'X3b USB-C PD', (260, 430))
    b += _cable('USB', [(300, 175), (270, 175), (270, 450), (330, 450), (330, 470)], 'X4 DATOS (PEND.)', (150, 350), True)
    b += _cable('SIG', [(415, 590), (415, 700)], 'X10 Cat6 FTP · M20 LAN', (421, 650))
    b += _cable('PE', [(240, 640), (990, 640)])
    ants = [('Eggbeater SAT', 'C8 · N SAT'), ('Quad 2 m/70 cm', 'C2 · N HAM'), ('Discone VHF', 'C1 · N VHF'), ('MLA-30 + inyector', 'C9 · N HF'),
            ('ADS-B + LNA 1090', 'C3 · N ADSB'), ('Bigsignal 868', 'C6 · N 868'), ('GPS activa', 'C4 · N GPS'), ('Fibra 433', 'C5 · N M433'),
            ('Bigsignal 433', 'C7 · N IG433')]
    for i, (n, t) in enumerate(ants):
        y = 90 + i * 56
        b += _nodo(960, y, 250, 46, n, t, WIRE['RF'])
        b += f"<line x1='630' y1='{500 + i * 8}' x2='960' y2='{y + 23}' stroke='{WIRE['RF']}' stroke-width='1.6' marker-end='url(#a{WIRE['RF'][1:]})'/>"
    sens = [('Anemómetro + veleta', 'C12 · PG7 VIENTO'), ('Pluviómetro', 'C13 · PG7 LLUVIA'), ('BME280 (garita)', 'C11 · PG7 WX')]
    for i, (n, t) in enumerate(sens):
        y = 620 + i * 56
        b += _nodo(960, y, 250, 46, n, t, WIRE['SIG'])
        b += f"<line x1='630' y1='{560 + i * 8}' x2='960' y2='{y + 23}' stroke='{WIRE['SIG']}' stroke-width='1.6' marker-end='url(#a{WIRE['SIG'][1:]})'/>"
    b += _nodo(960, 800, 250, 46, 'Cámara Module 3 Wide', 'dentro de la tapa · CSI', C['cam'])
    b += f"<rect x='1235' y='80' width='14' height='580' fill='{C['line']}'/>" + txt(1262, 370, 'MÁSTIL', 11, C['mute'], True)
    b += _leyenda(1290, 120)
    notas = ['• Coaxiales: bucle de goteo bajo cada pasamuros, funda_n + cinta autovulcanizante, abrazados al mástil cada 50 cm con separador_coax.',
             '• Descargador coaxial por línea (opcional, recomendado) a la tierra de la caja; mástil a tierra con 16 mm². Distancia módulos–pie de mástil ≈ 5 m.',
             '• Etiquetas X1… y C1… como en la tabla de interconexión del manual 52 (capítulo 6 bis, sección 5).']
    for k, t in enumerate(notas):
        b += txt(420, 880 + k * 18, t, 10.5)
    return svg(W, H, b, 'Interconexión de la estación: cajas, mástil, sensores, red y tierra')


def protecciones():
    """Diagram 49: protection chain from the mains to the loads."""
    W, H = 1500, 600
    b = _wmark()
    cadena = [('Red 230 V', 'toma de pared', C['pwr']), ('Magnetotérmico', 'PENDIENTE', C['gnd']), ('Diferencial', '30 mA', C['pwr']),
              ('PG9 RED', 'H07RN-F 3G1,5', C['ink']), ('EMI entrada', '6 A · 250 V', C['sdr']), ('SAI + ATO 15 A', 'batería 12 V', C['pwr']),
              ('EMI salida', '6 A · 250 V', C['sdr'])]
    for i, (t, s2, c) in enumerate(cadena):
        x = 30 + i * 205
        b += _nodo(x, 110, 175, 60, t, s2, c, t == 'Magnetotérmico')
        if i:
            b += _cable('L', [(x - 30, 140), (x, 140)])
    cadena2 = [('Ferrita mix 31', '4 vueltas · 230 V', C['gnd']), ('Schuko + cargador', '120 W', C['pwr']), ('Gatillo PD', '12 V', C['pwr']),
               ('ATO general', 'PENDIENTE', C['gnd']), ('Ferrita mix 31', '4 vueltas · 12 V', C['gnd']), ('WAGO 12 V', 'bus +12 V / GND', C['pwr']),
               ('ATO 2 A · 1 A · 1 A', 'hub · fans · viento', C['pwr'])]
    for i, (t, s2, c) in enumerate(cadena2):
        x = 30 + i * 205
        b += _nodo(x, 260, 175, 60, t, s2, c, s2 == 'PENDIENTE')
        if i:
            b += _cable('V12', [(x - 30, 290), (x, 290)])
    b += _cable('L', [(1347, 170), (1347, 215), (118, 215), (118, 260)], 'SALIDA SAI → PG9 230 V', (500, 209))
    b += _nodo(30, 400, 260, 60, 'Descargador coaxial (opcional)', 'por línea N · a la tierra de la caja', WIRE['RF'], True)
    b += _nodo(330, 400, 260, 60, 'Mástil a tierra', '16 mm² · tierra del edificio', C['pi'])
    b += _nodo(630, 400, 260, 60, 'PE continuo', 'toma → EMI → EMI → Schuko', WIRE['PE'])
    b += _nodo(930, 400, 260, 60, 'Cargas de 12 V', 'hub · ventiladores · RS485 · reserva', C['pwr'])
    b += txt(30, 520, 'Orden de la corriente: red → magnetotérmico → diferencial → EMI entrada → SAI → EMI salida → ferrita → Schuko → cargador → gatillo → ATO → ferrita → WAGO → ATO por rama.', 10.5)
    b += txt(30, 540, 'Valores sin confirmar en las fuentes (magnetotérmico, ATO general, descargador, derivación a tierra) se marcan PENDIENTE DE CONFIRMAR.', 10.5)
    return svg(W, H, b, 'Protecciones: de la red de 230 V a las cargas')


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
                     ('24_blindaje', blindaje), ('25_lora_owrx', lora_owrx),
                     ('31_montaje_caja_v2', montaje_caja_v2),
                     ('32_montaje_caja_v3_electronica', montaje_caja_v3_electronica),
                     ('33_montaje_caja_v3_potencia_sai', montaje_caja_v3_potencia_sai),
                     ('34_montaje_quad', montaje_quad), ('35_montaje_discone_adsb', montaje_discone_adsb),
                     ('36_montaje_mla_gps', montaje_mla_gps), ('37_montaje_crucetas', montaje_crucetas),
                     ('38_montaje_sensores_pico', montaje_sensores_pico),
                     ('39_mapa_piezas_mastil', mapa_piezas_mastil),
                     ('40_rejilla_caja_v2', rejilla_caja_v2),
                     ('41_rejilla_v3_electronica', rejilla_v3_electronica),
                     ('42_rejilla_v3_potencia', rejilla_v3_potencia), ('43_rejilla_v3_sai', rejilla_v3_sai),
                     ('44_cableado_caja_v2', cableado_caja_v2),
                     ('45_cableado_v3_electronica', cableado_v3_electronica),
                     ('46_cableado_v3_potencia', cableado_v3_potencia), ('47_cableado_v3_sai', cableado_v3_sai),
                     ('48_interconexion_estacion', interconexion_estacion), ('49_protecciones', protecciones)]:
        s = fn()
        open(os.path.join(OUT, name + '.svg'), 'w', encoding='utf-8').write(s)
        if cairosvg:
            cairosvg.svg2png(bytestring=s.encode(), write_to=os.path.join(OUT, name + '.png'))
        print('esquema', name)


if __name__ == '__main__':
    main()
