#!/usr/bin/env python3
# =====================================================================
#  bricohams-camsnap · EA5KAO · BricoHams
#  Saca una foto de la cámara del mástil cada CAM_SNAPSHOT_SECONDS desde
#  el RTSP de MediaMTX y la deja en la carpeta del plugin "camara", que
#  OpenWebRX sirve por su mismo puerto. La carpeta snap/ es un tmpfs
#  (no gasta la tarjeta SD).
# =====================================================================
import os
import subprocess
import sys
import time
from datetime import datetime

RTSP = os.environ.get('CAM_RTSP', 'rtsp://127.0.0.1:8554/mastil')
OUT = os.environ.get('CAM_SNAPSHOT', '/usr/lib/python3/dist-packages/htdocs/plugins/receiver/camara/snap/mastil.jpg')
EVERY = max(10, int(os.environ.get('CAM_SNAPSHOT_SECONDS', '60')))
LABEL = os.environ.get('CAM_LABEL', 'EA5KAO · Mi QTH (Murcia) · BricoHams')
WIDTH = int(os.environ.get('CAM_SNAPSHOT_WIDTH', '1280'))
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
TXT = os.path.join(os.environ.get('RUNTIME_DIRECTORY', '/run/bricohams'), 'camsnap.txt')


def snap():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    os.makedirs(os.path.dirname(TXT), exist_ok=True)
    with open(TXT, 'w', encoding='utf-8') as f:
        f.write('%s  %s' % (LABEL, datetime.now().strftime('%d/%m/%Y %H:%M')))
    tmp = OUT + '.tmp.jpg'
    vf = ('scale=%d:-2,drawtext=fontfile=%s:textfile=%s:expansion=none:fontsize=h/34:'
          'fontcolor=white:box=1:boxcolor=0x000000@0.55:boxborderw=8:x=12:y=h-th-14') % (WIDTH, FONT, TXT)
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-rtsp_transport', 'tcp', '-i', RTSP,
           '-frames:v', '1', '-vf', vf, '-q:v', '5', '-y', tmp]
    r = subprocess.run(cmd, timeout=40)
    if r.returncode == 0 and os.path.getsize(tmp) > 0:
        os.chmod(tmp, 0o644)
        os.replace(tmp, OUT)
        return True
    return False


def main():
    fails = 0
    while True:
        t0 = time.time()
        try:
            ok = snap()
        except Exception as e:
            ok = False
            print('camsnap: %s' % e, file=sys.stderr)
        fails = 0 if ok else fails + 1
        if fails in (1, 10):
            print('camsnap: no se pudo sacar la foto de %s (¿MediaMTX en marcha?)' % RTSP, file=sys.stderr)
        time.sleep(max(1, EVERY - (time.time() - t0)) if fails < 10 else 60)


if __name__ == '__main__':
    main()
