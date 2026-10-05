#!/usr/bin/env python3
"""v4.3 · docker-compose.yaml de OpenWebRX+ (imagen de slechev) a partir de bricohams.env.

Lo usa install.sh cuando OWRX_BACKEND="docker" (manual 33, ADR-44). Lee del entorno:
  OWRX_DOCKER_IMAGE        imagen (por defecto slechev/openwebrxplus-softmbe:latest: con DMR, D-Star, YSF…)
  OWRX_DOCKER_CONTAINER    container_name (por defecto owrx-mbe)
  OWRX_DOCKER_RED          host (por defecto: MQTT, rtl_tcp y nginx en 127.0.0.1 como en la Pi nativa)
                           o bridge (publica OWRX_DOCKER_PORT → 8073)
  OWRX_DOCKER_PORT         puerto en la Pi en modo bridge (por defecto 8073)
  OWRX_DOCKER_PRIVILEGED   yes = contenedor privilegiado (SDRplay, o si un SDR no aparece); por defecto no
  TZ                       zona horaria (por defecto Europe/Madrid)

Los tres volúmenes son carpetas de OWRX_DOCKER_DIR (bind mounts), en las rutas que pide la imagen:
  ./etc → /etc/openwebrx · ./var → /var/lib/openwebrx · ./plugins → /usr/lib/python3/dist-packages/htdocs/plugins
Sin contraseñas: el administrador se crea con «docker exec -it … openwebrx admin adduser».

Uso: bricohams-docker-compose.py > /opt/owrx-docker/docker-compose.yaml
"""
import os
import re
import sys

MONTAJES = [('./etc', '/etc/openwebrx'), ('./var', '/var/lib/openwebrx'),
            ('./plugins', '/usr/lib/python3/dist-packages/htdocs/plugins')]


def env(k, d=''):
    v = os.environ.get(k, '').strip()
    return v if v else d


def si(v):
    return v.strip().lower() in ('1', 'y', 'yes', 's', 'si', 'sí', 'true', 'on')


def comillas(v):
    return '"%s"' % v.replace('\\', '\\\\').replace('"', '\\"')


def compose():
    imagen = env('OWRX_DOCKER_IMAGE', 'slechev/openwebrxplus-softmbe:latest')
    nombre = env('OWRX_DOCKER_CONTAINER', 'owrx-mbe')
    red = env('OWRX_DOCKER_RED', 'host').lower()
    puerto = env('OWRX_DOCKER_PORT', '8073')
    tz = env('TZ', 'Europe/Madrid')
    if not re.match(r'^[a-z0-9][a-z0-9._/-]*(:[A-Za-z0-9._-]+)?(@sha256:[0-9a-f]{64})?$', imagen):
        raise ValueError('OWRX_DOCKER_IMAGE no válida: %s' % imagen)
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_.-]*$', nombre):
        raise ValueError('OWRX_DOCKER_CONTAINER no válido: %s' % nombre)
    if red not in ('host', 'bridge'):
        raise ValueError('OWRX_DOCKER_RED debe ser host o bridge')
    if not puerto.isdigit() or not 1 <= int(puerto) <= 65535:
        raise ValueError('OWRX_DOCKER_PORT no válido: %s' % puerto)
    if not re.match(r'^[A-Za-z0-9_+./-]+$', tz):
        raise ValueError('TZ no válida: %s' % tz)
    y = ['# Generado por install.sh (BricoHams SDR v4.3) desde bricohams.env: OWRX_DOCKER_*.',
         '# Para cambiarlo, edita bricohams.env y: sudo bash install.sh --solo openwebrx',
         '# Actualizar la imagen a mano: cd %s && docker compose pull && docker compose up -d' % env('OWRX_DOCKER_DIR', '/opt/owrx-docker'),
         'version: "2.4"                          # 2.4: también la entiende docker-compose 1.29 (Bookworm)',
         'services:',
         '  openwebrx:',
         '    image: %s' % comillas(imagen),
         '    container_name: %s' % comillas(nombre),
         '    restart: unless-stopped',
         '    environment:',
         '      TZ: %s' % comillas(tz)]
    if red == 'host':
        y += ['    network_mode: host                    # 8073, MQTT (visitas) y rtl_tcp en 127.0.0.1 como en la Pi nativa']
    else:
        y += ['    ports:', '      - %s' % comillas('%s:8073' % puerto)]
    if si(env('OWRX_DOCKER_PRIVILEGED', 'no')):
        y += ['    privileged: true                      # OWRX_DOCKER_PRIVILEGED=yes (SDRplay o SDR que no aparece)']
    else:
        y += ['    # USB con conexión en caliente sin --privileged: toda la carpeta y la regla del grupo 189 (usb_device)',
              '    device_cgroup_rules:', '      - "c 189:* rmw"']
    y += ['    tmpfs:', '      - /tmp',
          '    volumes:']
    y += ['      - %s:%s' % m for m in MONTAJES]
    y += ['      - /dev/bus/usb:/dev/bus/usb']
    return '\n'.join(y) + '\n'


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] in ('-h', '--help'):
        print(__doc__)
        sys.exit(0)
    try:
        sys.stdout.write(compose())
    except ValueError as e:
        sys.exit('bricohams-docker-compose: %s' % e)
