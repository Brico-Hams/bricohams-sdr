#!/usr/bin/env python3
# =====================================================================
#  Esquemas 28-30 (v5.4): Meshtastic dual, acceso/administracion y despliegues acotados.
#  Reutiliza el estilo de tools/esquemas.py, pero solo genera estos tres (SVG y PNG si hay
#  cairosvg) y los PNG que falten de 26 y 27. No regenera el resto de esquemas.
#  Uso: python3 tools/esquemas_modulos.py
# =====================================================================
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esquemas import C, OUT, arrow, caja_s, markers, svg, txt  # noqa: E402


def mesh_dual():
    b = markers([C['ink'], C['lora'], C['or'], C['pi'], C['net'], C['sdr']])
    b += caja_s(30, 90, 330, 150, 'LilyGO T3 · 433 MHz', 'USB serie · /dev/lilygo-mesh', C['or'], '#fff3e0', arriba=True)
    b += caja_s(30, 330, 330, 150, 'HAT SX1262 · 868 MHz', 'meshtasticd en la Pi', C['pi'], '#e8f5e9', arriba=True)
    b += caja_s(450, 90, 380, 150, 'bricohams-mesh-puente', 'unico dueno del puerto serie (DynamicUser)', C['or'], '#ffffff', arriba=True)
    b += txt(470, 170, '127.0.0.1:4404 · API stream', 11) + txt(470, 196, '127.0.0.1:4480 · API HTTP del cliente web', 11)
    b += caja_s(450, 330, 380, 150, 'meshtasticd', 'API TCP 127.0.0.1:4403 · web 127.0.0.1:9443', C['pi'], '#ffffff', arriba=True)
    b += caja_s(450, 540, 380, 130, 'bricohams-mesh-owrx · mesh-admin', 'mapa, chat, nombres y telemetria', C['sdr'], '#ffffff', arriba=True)
    b += caja_s(930, 90, 330, 150, 'nginx :8444 (433)', 'cliente oficial de Meshtastic', C['net'], '#e0f2f1', arriba=True)
    b += caja_s(930, 330, 330, 150, 'nginx :8443 (868)', 'cliente oficial de Meshtastic', C['net'], '#e0f2f1', arriba=True)
    b += caja_s(930, 540, 330, 130, 'Sesion de administrador', 'de /settings: sin ella, no hay acceso', C['cr'], '#fdecea', arriba=True)
    b += arrow(360, 165, 450, 165, C['or'], 'USB')
    b += arrow(360, 405, 450, 405, C['pi'], 'SPI')
    b += arrow(830, 165, 930, 165, C['net'], 'HTTP')
    b += arrow(830, 405, 930, 405, C['net'], 'HTTPS')
    b += (f"<polyline points='450,200 405,200 405,605 450,605' fill='none' stroke='{C['sdr']}' stroke-width='2' marker-end='url(#a{C['sdr'][1:]})'/>"
          + txt(372, 590, '4404', 10.5, C['sdr']))
    b += arrow(740, 480, 740, 540, C['sdr'], '4403')
    b += arrow(1095, 540, 1095, 480, C['cr'])
    b += txt(30, 740, 'Solo escuchan 127.0.0.1: desde fuera se llega unicamente por nginx y con sesion.', 12)
    b += txt(30, 770, 'Despliegue acotado y reversible: sudo tools/desplegar-mesh-dual.sh <bricohams.env> (manual 35).', 12)
    return svg(1300, 820, b, 'Meshtastic dual 433/868 y puente USB (v5.4)')


def acceso_admin():
    b = markers([C['ink'], C['or'], C['cr'], C['sdr'], C['net'], C['pi']])
    b += caja_s(30, 100, 260, 120, 'Navegador', 'visitante o administrador', C['ink'], '#fafafa', arriba=True)
    b += caja_s(380, 100, 400, 200, 'nginx (bricohams-sdr)', 'limit_req login POST', C['net'], '#e0f2f1', arriba=True)
    b += txt(400, 180, 'POST de login: 12 por minuto, rafaga 5', 11) + txt(400, 206, 'superado: 429 sin consumir la clave', 11)
    b += txt(400, 232, 'API sin sesion: no redirige ni cuenta intentos', 11)
    b += caja_s(880, 100, 380, 120, '/settings (administracion)', 'OpenWebRX+ · login + aviso por Telegram', C['cr'], '#fdecea', arriba=True)
    b += caja_s(880, 270, 380, 130, 'Paneles privados', 'satelites, clima, Meshtastic', C['sdr'], '#ffffff', arriba=True)
    b += txt(900, 350, 'bricohams-mesh-admin · copia antes de actuar', 11)
    b += caja_s(380, 380, 400, 130, 'Files (bricohams-owrx-files)', 'servidor protegido', C['or'], '#fff3e0', arriba=True)
    b += txt(400, 460, 'sin botones, 403 incluso autenticado, no borra', 11)
    b += caja_s(30, 380, 260, 130, 'Grabador', 'bricohams-satrec', C['pi'], '#e8f5e9', arriba=True)
    b += arrow(290, 160, 380, 160, C['ink'], 'HTTPS')
    b += arrow(780, 160, 880, 160, C['cr'], 'login')
    b += arrow(1070, 220, 1070, 270, C['sdr'])
    b += arrow(580, 300, 580, 380, C['or'])
    b += arrow(290, 445, 380, 445, C['pi'], 'ficheros')
    b += txt(30, 600, 'Pase de satelite en curso: el despliegue no toca nada (ventana AOS-90 s a LOS+90 s).', 12)
    b += txt(30, 630, 'Ver manuales 24, 26, 35 y 42.', 12, C['mute'])
    return svg(1300, 680, b, 'Acceso, administracion y Files protegidos (v5.4)')


def despliegues():
    b = markers([C['ink'], C['or'], C['cr'], C['pi'], C['sdr']])
    pasos = [('1 Validar', 'sudo, rutas absolutas, sintaxis, estado del kit', C['sdr']),
             ('2 Respaldo', '/var/backups/bricohams/... verificado', C['or']),
             ('3 Aplicar', 'solo los ficheros previstos, sin tocar RF', C['pi']),
             ('4 Comprobar', 'nginx -t y systemctl is-active', C['ink']),
             ('5 Restaurar', 'automatico si algo falla', C['cr'])]
    for i, (t, s, c) in enumerate(pasos):
        x = 30 + i * 250
        b += caja_s(x, 100, 220, 120, t, s, c, '#ffffff', arriba=True)
        if i < 4:
            b += arrow(x + 220, 160, x + 250, 160, c)
    b += caja_s(30, 290, 380, 130, 'desplegar-mesh-dual.sh', 'puente 433, cliente 8444 y 8443', C['or'], '#fff3e0', arriba=True)
    b += caja_s(440, 290, 380, 130, 'desplegar-agenda-telegram.sh', 'agendas, avisos, perfil sat400', C['sdr'], '#eef4fb', arriba=True)
    b += caja_s(850, 290, 380, 130, 'finalizar-satelites-ctcss.sh', 'panel CTCSS externo, grabaciones', C['pi'], '#e8f5e9', arriba=True)
    b += txt(30, 480, 'Ninguno guarda contrasenas: usan sudo. Se detienen si el respaldo no se verifica.', 12)
    b += txt(30, 510, 'Pruebas: test_mesh_puente.py, test_agendas_admin.py, test_satpass_fuentes.py, test_finalizar_satelites_ctcss.py.', 12, C['mute'])
    return svg(1300, 560, b, 'Despliegues acotados con copia de seguridad (v5.4)')


def render_png(svg_txt, destino):
    """PNG con cairosvg o, si falta cairo, con resvg-py; False si no hay ninguno."""
    try:
        import cairosvg
        cairosvg.svg2png(bytestring=svg_txt.encode(), write_to=destino)
        return True
    except (ImportError, OSError):
        pass
    try:
        import resvg_py
    except ImportError:
        return False
    open(destino, 'wb').write(bytes(resvg_py.svg_to_bytes(svg_string=svg_txt, font_dirs=[r'C:\Windows\Fonts'] if os.name == 'nt' else None)))
    return True


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, fn in [('28_meshtastic_dual', mesh_dual), ('29_acceso_administracion', acceso_admin),
                     ('30_despliegues_acotados', despliegues)]:
        s = fn()
        open(os.path.join(OUT, name + '.svg'), 'w', encoding='utf-8').write(s)
        render_png(s, os.path.join(OUT, name + '.png'))
        print('esquema', name)
    for f in sorted(os.listdir(OUT)):
        png = os.path.join(OUT, f[:-4] + '.png')
        if f.startswith(('26_', '27_')) and f.endswith('.svg') and not os.path.exists(png):
            if render_png(open(os.path.join(OUT, f), encoding='utf-8').read(), png):
                print('png', f)


if __name__ == '__main__':
    main()
