#!/usr/bin/env python3
# =====================================================================
#  bricohams-ft2-patch · EA5KAO · BricoHams  (v4, experimental)
#  Añade el modo FT2 a OpenWebRX+ (que no lo trae) tocando 3 ficheros del
#  paquete instalado, con marcas «BRICOHAMS-FT2» para poder repetir o quitar:
#    owrx/wsjt.py        clase Ft2Profile (ciclo 3,75 s, decodifica con
#                        bricohams-ft2-decode, que imita la salida de jt9)
#    owrx/modes.py       WsjtMode("ft2", "FT2")
#    htdocs/lib/MessagePanel.js   'FT2' en la lista de modos del panel
#  Un «hook» de apt lo vuelve a aplicar tras cada actualización de openwebrx.
#  Uso: bricohams-ft2-patch [--quitar] [--raiz /usr/lib/python3/dist-packages] [--silencioso]
# =====================================================================
import os
import shutil
import sys

MARCA = 'BRICOHAMS-FT2'

WSJT_CLASE = '''# >>> BRICOHAMS-FT2 (modo FT2 de IU8LMC con decodium-rx; lo pone bricohams-ft2-patch)
class Ft2Profile(WsjtProfile):
    def getInterval(self):
        return 3.75

    def decoder_commandline(self, file):
        return ["bricohams-ft2-decode", "-d", str(self.decoding_depth()), file]

    def getMode(self):
        return "FT2"
# <<< BRICOHAMS-FT2


'''
WSJT_ANCLA = '        elif mode == "ft4":\n            return StaticProfileSource([Ft4Profile()])\n'
WSJT_RAMA = WSJT_ANCLA + '        elif mode == "ft2":  # BRICOHAMS-FT2\n            return StaticProfileSource([Ft2Profile()])  # BRICOHAMS-FT2\n'
MODES_ANCLA = '        WsjtMode("ft4", "FT4"),\n'
MODES_LINEA = MODES_ANCLA + '        WsjtMode("ft2", "FT2"),  # BRICOHAMS-FT2\n'
JS_ANCLA = "this.qsoModes = ['FT8', 'JT65', 'JT9', 'FT4', 'FST4', 'Q65', 'MSK144'];"
JS_LINEA = "this.qsoModes = ['FT8', 'JT65', 'JT9', 'FT4', 'FST4', 'Q65', 'MSK144', 'FT2'];  // BRICOHAMS-FT2"


def _editar(ruta, fn, quitar):
    if not os.path.exists(ruta):
        return 'falta %s' % ruta
    s = open(ruta, encoding='utf-8').read()
    nuevo = fn(s, quitar)
    if nuevo is None:
        return 'no encuentro el punto de anclaje en %s (¿cambió OpenWebRX+?)' % ruta
    if nuevo != s:
        if not os.path.exists(ruta + '.antes-ft2'):
            shutil.copy2(ruta, ruta + '.antes-ft2')
        open(ruta, 'w', encoding='utf-8').write(nuevo)
        return 'cambiado'
    return 'sin cambios'


def f_wsjt(s, quitar):
    if quitar:
        return s.replace(WSJT_CLASE, '').replace(WSJT_RAMA, WSJT_ANCLA)
    if MARCA in s:
        return s
    if WSJT_ANCLA not in s or 'class Fst4Profile(WsjtProfile)' not in s:
        return None
    s = s.replace(WSJT_ANCLA, WSJT_RAMA)
    i = s.find('class Fst4Profile(WsjtProfile)')
    return s[:i] + WSJT_CLASE + s[i:]


def f_modes(s, quitar):
    if quitar:
        return s.replace(MODES_LINEA, MODES_ANCLA)
    if MARCA in s:
        return s
    return s.replace(MODES_ANCLA, MODES_LINEA) if MODES_ANCLA in s else None


def f_js(s, quitar):
    if quitar:
        return s.replace(JS_LINEA, JS_ANCLA)
    if MARCA in s:
        return s
    return s.replace(JS_ANCLA, JS_LINEA) if JS_ANCLA in s else None


def main(argv):
    raiz = '/usr/lib/python3/dist-packages'
    if '--raiz' in argv:
        raiz = argv[argv.index('--raiz') + 1]
    quitar = '--quitar' in argv
    res = {
        'owrx/wsjt.py': _editar(os.path.join(raiz, 'owrx/wsjt.py'), f_wsjt, quitar),
        'owrx/modes.py': _editar(os.path.join(raiz, 'owrx/modes.py'), f_modes, quitar),
        'htdocs/lib/MessagePanel.js': _editar(os.path.join(raiz, 'htdocs/lib/MessagePanel.js'), f_js, quitar),
    }
    mal = [k for k, v in res.items() if v not in ('cambiado', 'sin cambios')]
    if '--silencioso' not in argv or mal:
        for k, v in res.items():
            print('ft2: %-28s %s' % (k, v))
    return 1 if mal else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
