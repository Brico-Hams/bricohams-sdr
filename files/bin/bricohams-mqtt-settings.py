#!/usr/bin/env python3
# v4.2 · Tras importar un perfil (install.sh --importar), activa en settings.json el informe
# MQTT de OpenWebRX+ que usa «bricohams-visitas» (oyentes, países y Telegram), sin tocar nada más.
# v4.5 · con --lora además deja OpenWebRX+ escuchando «+/APRS» y «+/Meshtastic» (mqtt_aprs, mqtt_meshtastic):
# así pinta en su mapa lo que oyen el RAK4631 y los nodos Meshtastic (bricohams-rak-aprs, bricohams-mesh-owrx).
# Uso: bricohams-mqtt-settings.py /var/lib/openwebrx/settings.json [--lora] [--chat]
import json
import os
import sys

p = sys.argv[1]
s = json.load(open(p, encoding='utf-8'))
lora = '--lora' in sys.argv[2:]
chat = '--chat' in sys.argv[2:]
if s.get('mqtt_enabled') and s.get('mqtt_host') and (not lora or (s.get('mqtt_aprs') and s.get('mqtt_meshtastic'))) and (not chat or s.get('mqtt_chat')):
    sys.exit(0)
if lora:
    s['mqtt_aprs'] = True
    s['mqtt_meshtastic'] = True
if chat:
    s['mqtt_chat'] = True
s['mqtt_enabled'] = True
s['mqtt_host'] = s.get('mqtt_host') or 'localhost'
s['mqtt_topic'] = s.get('mqtt_topic') or 'openwebrx'
tmp = p + '.tmp'
with open(tmp, 'w', encoding='utf-8') as f:
    json.dump(s, f, indent=4, ensure_ascii=False)
os.replace(tmp, p)
print('  ! settings.json importado: activo el MQTT de OpenWebRX+ (visitas y, con --lora, mapa LoRa/Meshtastic)')
