#!/usr/bin/env python3
# v4.2 · Tras importar un perfil (install.sh --importar), activa en settings.json el informe
# MQTT de OpenWebRX+ que usa «bricohams-visitas» (oyentes, países y Telegram), sin tocar nada más.
# Uso: bricohams-mqtt-settings.py /var/lib/openwebrx/settings.json
import json
import os
import sys

p = sys.argv[1]
s = json.load(open(p, encoding='utf-8'))
if s.get('mqtt_enabled') and s.get('mqtt_host'):
    sys.exit(0)
s['mqtt_enabled'] = True
s['mqtt_host'] = s.get('mqtt_host') or 'localhost'
s['mqtt_topic'] = s.get('mqtt_topic') or 'openwebrx'
tmp = p + '.tmp'
with open(tmp, 'w', encoding='utf-8') as f:
    json.dump(s, f, indent=4, ensure_ascii=False)
os.replace(tmp, p)
print('  ! settings.json importado: activo el informe MQTT de OpenWebRX+ para «visitas» (VISITAS_ENABLE)')
