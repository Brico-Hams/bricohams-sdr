#!/usr/bin/env python3
"""Genera docs/ESTRUCTURA_FICHEROS.md: árbol completo del repositorio y qué hace cada fichero.

La descripción de cada fichero sale, por orden, de:
  1. DESCRIPCIONES (texto escrito a mano para los ficheros clave),
  2. la cabecera del propio fichero (docstring, primer comentario o título Markdown),
  3. una regla por extensión/carpeta (STL, vistas PNG, esquemas SVG...).

Uso:  python3 tools/estructura.py [--check]
  --check  no escribe; sale con 1 si el documento no está al día (lo usa tests/).
"""
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, 'docs', 'ESTRUCTURA_FICHEROS.md')
IGNORAR_DIR = {'.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv'}
IGNORAR_EXT = {'.pyc', '.pyo'}

CARPETAS = {
    '.': 'Raíz del repositorio',
    'data': 'Datos de entrada: repetidores, marcadores, satélites y catálogo de localizadores',
    'data/locator': 'Catálogo de localidades → locator Maidenhead y repetidores por zona (bricohams-locator)',
    'docs': 'Documentación: arquitectura (ADR), componentes, datos, hardware y esta estructura',
    'docs/esquemas': 'Diagramas generados por tools/esquemas.py (SVG fuente + PNG)',
    'docs/manuales': 'Manuales paso a paso numerados (instalación, cada servicio y cada panel)',
    'files': 'Todo lo que install.sh copia al sistema',
    'files/bin': 'Ejecutables instalados en /usr/local/bin: servicios, parcheadores de OpenWebRX+ y utilidades',
    'files/branding': 'Imagen BricoHams (cabecera, avatar, favicon) que se aplica a OpenWebRX+',
    'files/grafana': 'Paneles de Grafana aprovisionados por install.sh',
    'files/htdocs': 'Recursos web servidos por OpenWebRX+ (plugins del cliente)',
    'files/htdocs/plugins': 'Plugins del cliente web de OpenWebRX+ (init.js los carga)',
    'files/motd': 'Mensaje de bienvenida de la consola',
    'files/nginx': 'Plantillas del sitio nginx (proxy, TLS, rutas /settings/bricohams/...)',
    'files/openwebrx': 'Plantillas de configuración de OpenWebRX+ (settings, marcadores, conf.d)',
    'files/share': 'Módulos compartidos que los parcheadores insertan en OpenWebRX+',
    'files/web': 'Portal estático /bricohams/ y página de privacidad',
    'firmware': 'Firmware para los microcontroladores de la estación',
    'firmware/pico-io': 'MicroPython de la Raspberry Pi Pico (sensores y ventiladores)',
    'firmware/rak4631-lora-aprs': 'Firmware iGate LoRa APRS (solo RX) para RAK4631 y placas compatibles (PlatformIO)',
    'hardware': 'Diseño mecánico y de RF (OpenSCAD, STL, NEC2)',
    'hardware/anclajes': 'Crucetas y soportes impresos del mástil',
    'hardware/antenas': 'Antenas propias: modelo OpenSCAD, piezas STL y simulación NEC2',
    'hardware/caja': 'Caja de intemperie v2 (mástil)',
    'hardware/caja_v3': 'Caja v3 en dos módulos (electrónica + potencia)',
    'owrx-clone': 'Herramienta independiente (MIT) para clonar una instalación de OpenWebRX+',
    'tests': 'Pruebas automáticas (bash tests/run_tests.sh)',
    'tests/datos': 'Datos de prueba (fixtures) usados por los tests',
    'tools': 'Generadores y herramientas de desarrollo (esquemas, datos, STL, TAK, compilación RAK)',
}

DESCRIPCIONES = {
    'install.sh': 'Instalador por pasos, idempotente: dependencias, servicios, parches de OpenWebRX+, nginx, Meshtastic, APRS, TAK, Grafana/Prometheus y copias (--lista, --solo, --backup, --actualizar)',
    'README.md': 'Presentación del proyecto, puesta en marcha rápida, estructura resumida y reglas',
    'CHANGELOG.md': 'Historial de versiones y de cada cambio',
    'bricohams.env.example': 'Plantilla pública de configuración de la estación, sin credenciales (copiar a bricohams.env)',
    '.gitignore': 'Excluye claves (bricohams.env), cachés y artefactos de compilación',
    '.gitattributes': 'Fuerza finales de línea LF (los scripts se ejecutan en Linux)',
    'docs/ARQUITECTURA.md': 'Decisiones de arquitectura (ADR-01 en adelante): contexto, decisión y consecuencias',
    'docs/COMPONENTES.md': 'Ficha de cada componente: función, ficheros, servicio, puertos, configuración y pruebas',
    'docs/ESTRUCTURA_FICHEROS.md': 'Este documento (generado por tools/estructura.py)',
    'docs/DATOS.md': 'Conjuntos de datos: SDR, perfiles, marcadores, puertos, servicios, I2C (generado por tools/datos.py)',
    'docs/CANALES_Y_FRECUENCIAS.md': 'Canales y frecuencias de todos los grupos de marcadores (generado por tools/canales.py)',
    'files/bin/bricohams-mesh-admin': 'Panel de administración (solo /settings, con sesión): Meshtastic 433/868, iGate RAK, APRS, TAK (credenciales) y Monitorización',
    'files/bin/bricohams-mesh-owrx': 'Integra Meshtastic en la web de OpenWebRX+ (solo información de nodos y registro APRS, sin configuración)',
    'files/bin/bricohams-mesh-url': 'Genera/lee las URL de canales Meshtastic compartidas entre los nodos 433 y 868',
    'files/bin/bricohams-rak-aprs': 'Puente del iGate RAK4631 (USB serie) hacia APRS-IS y el registro mostrado en la web',
    'files/bin/bricohams-owrx-botones': 'Parche de OpenWebRX+: botones TAK y Monitorización en /settings (nunca en la página pública)',
    'files/bin/bricohams-owrx-bookmarks-io': 'Parche de OpenWebRX+: importar/exportar bookmarks en /settings/bookmarks',
    'files/bin/bricohams-owrx-repeaterbook': 'Parche de OpenWebRX+: campo de clave API de RepeaterBook en /settings/general',
    'files/bin/bricohams-owrx-ctcss': 'Parche de OpenWebRX+: subtono CTCSS (FM) en bookmarks y silenciador por tono',
    'files/bin/bricohams-owrx-rbimport': 'Parche de OpenWebRX+: importar repetidores de RepeaterBook por región a bookmarks (con subtono)',
    'files/bin/bricohams-check': 'Diagnóstico de la estación: SDR, servicios, GPS, sensores, red y certificados',
    'files/bin/bricohams-servicios': 'Lista y controla los servicios BricoHams (estado, arranque, logs)',
    'files/bin/bricohams-env.py': 'Lee y valida bricohams.env; lo usan install.sh y los servicios',
    'tools/instalar_tak.sh': 'Instala OpenTAKServer (venv, PostgreSQL, CA, usuarios con clave aleatoria en /etc/bricohams/tak-access.txt)',
    'tools/estructura.py': 'Genera docs/ESTRUCTURA_FICHEROS.md (este árbol con descripciones)',
    'files/bin/bricohams-locator': 'Zona de la estación según su locator: coordenadas, AEMET y FM cercanas, marcadores [AUTO-LOCATOR] y METEO_STATIONS (manual 32)',
    'files/htdocs/plugins/map/bricohams_live/bricohams_live.js': 'Plugin de mapa: capas en vivo de trazas APRS, aeronaves ADS-B y marcadores TAK sobre el mapa de OpenWebRX+',
    'files/htdocs/plugins/map/reduce_map_legend_sections/reduce_map_legend_sections.js': 'Plugin de mapa: compacta las secciones de la leyenda',
    'files/htdocs/plugins/receiver/antenna_switcher/antenna_switcher.cfg': 'Configuración del plugin conmutador de antenas (pines GPIO de salida)',
    'files/htdocs/plugins/receiver/compact_analog_modes/compact_analog_modes.js': 'Plugin de receptor: agrupa los modos analógicos en un selector compacto',
    'files/htdocs/plugins/receiver/show_band_plan/show_band_plan.js': 'Plugin de receptor: dibuja el plan de bandas sobre la cascada',
    'files/htdocs/plugins/receiver/search_bookmarks/LICENSE': 'Licencia del plugin de terceros search_bookmarks',
    'firmware/rak4631-lora-aprs/LICENSE': 'Licencia del firmware iGate LoRa-APRS para RAK4631',
    'owrx-clone/LICENSE': 'Licencia de owrx-clone',
    'files/openwebrx/settings.json.tmpl': 'Plantilla de settings.json de OpenWebRX+ (receptor, perfiles, ubicación) rellenada desde bricohams.env',
    'files/web/index.html.tmpl': 'Plantilla de la portada web de la estación rellenada desde bricohams.env',
    'files/web/clima.html': 'v5.0 · Clima en red: estaciones WX por APRS, balizas WSPR, pases grabados e informe AMSAT',
    'firmware/rak4631-lora-aprs/bin/bricohams-rak4631-lora-aprs.hex': 'Firmware iGate precompilado (Intel HEX, para nrfutil/SWD)',
    'firmware/rak4631-lora-aprs/bin/bricohams-rak4631-lora-aprs.uf2': 'Firmware iGate precompilado (UF2, arrastrar a la unidad del bootloader)',
    'firmware/rak4631-lora-aprs/bin/bricohams-rak4631-lora-aprs.zip': 'Paquete DFU del firmware iGate (adafruit-nrfutil por USB serie, el que usa el instalador)',
    'firmware/rak4631-lora-aprs/bin/SHA256SUMS': 'Sumas SHA-256 de los binarios del firmware iGate',
    'hardware/antenas/sim/opt_quad.py': 'Optimizador NEC de la antena quad 2 m/70 cm (longitudes y separación)',
    'owrx-clone/owrx-clone.1': 'Página de manual (man) de owrx-clone',
    'tests/datos/owrx/htdocs/lib/jquery-3.7.1.min.js': 'Copia de referencia de OpenWebRX+ usada por los tests de parches (jQuery)',
    'tests/datos/owrx/htdocs/lib/MessagePanel.js': 'Copia de referencia de OpenWebRX+ (MessagePanel.js) para probar los parches',
    'tests/datos/owrx/owrx/modes.py': 'Copia de referencia de OpenWebRX+ (owrx/modes.py) para probar los parches',
    'tests/datos/owrx/owrx/wsjt.py': 'Copia de referencia de OpenWebRX+ (owrx/wsjt.py) para probar el parche FT2',
    'tests/datos/owrx-1.2.126/htdocs_lib_settings_BookmarkTable.js': 'Original de OpenWebRX+ 1.2.126 (BookmarkTable.js) para probar parches de marcadores/CTCSS',
    'tests/datos/owrx-1.2.126/owrx_bookmarks.py': 'Original de OpenWebRX+ 1.2.126 (owrx/bookmarks.py) para probar parches de marcadores',
    'tests/datos/owrx-1.2.126/owrx_controllers_settings_bookmarks.py': 'Original de OpenWebRX+ 1.2.126 (controlador de marcadores) para probar parches',
    'tests/datos/owrx-1.2.126/owrx_dsp.py': 'Original de OpenWebRX+ 1.2.126 (owrx/dsp.py) para probar el parche CTCSS',
    'tools/compilar_rak.sh': 'Compila el firmware iGate para todas las placas (PlatformIO) y deja los binarios',
    'tools/tak-requirements.txt': 'Versiones fijadas de Python para OpenTAKServer',
    'tests/run_tests.sh': 'Lanza todas las pruebas: shellcheck, sintaxis y tests de Python',
}

REGLAS_EXT = {
    '.stl': 'Pieza 3D lista para imprimir',
    '.scad': 'Modelo paramétrico OpenSCAD',
    '.png': 'Imagen / vista renderizada',
    '.svg': 'Diagrama vectorial',
    '.jpg': 'Imagen',
    '.ico': 'Icono',
    '.wav': 'Audio de prueba',
    '.nec': 'Modelo de antena NEC2',
    '.out': 'Resultado de simulación NEC2',
    '.csv': 'Tabla de datos',
    '.json': 'Datos JSON',
    '.css': 'Hoja de estilos',
    '.html': 'Página HTML',
    '.ini': 'Configuración (PlatformIO / servicio)',
    '.txt': 'Texto',
    '.yml': 'Configuración YAML',
    '.yaml': 'Configuración YAML',
    '.conf': 'Configuración',
    '.service': 'Unidad systemd',
}

COMENTARIO = re.compile(r'^\s*(?:#|//|--|;|/\*+|\*)\s?(.*?)\s*(?:\*/)?\s*$')
RUIDO = re.compile(r'^(!|-\*-|shellcheck|SPDX|eslint|jshint|@ts-|vim:|coding[:=]|pylint|noqa|use strict|=+$|-+$|\*+$|·+$|_+$)', re.I)


def _limpia(t):
    t = re.sub(r'\s+', ' ', t).strip(' -·:—*#/"\'')
    return t if len(t) <= 160 else t[:157].rstrip() + '...'


def cabecera(ruta):
    """Primera línea descriptiva del fichero (o '')."""
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            lineas = f.read(6000).splitlines()
    except (UnicodeDecodeError, OSError):
        return ''
    ext = os.path.splitext(ruta)[1].lower()
    if ext == '.md':
        for li in lineas:
            if li.startswith('#'):
                return _limpia(li.lstrip('#'))
        return ''
    if ext == '.json':
        m = re.search(r'"(?:description|descripcion|_comentario|name)"\s*:\s*"([^"]{8,})"', '\n'.join(lineas))
        return _limpia(m.group(1)) if m else ''
    texto = '\n'.join(lineas)
    m = re.search(r'^(?:#![^\n]*\n)?(?:#[^\n]*\n)*\s*(?:"""|\'\'\')\s*([^\n]+)', texto)
    if ext == '.py' and m:
        return _limpia(m.group(1))
    for li in lineas[:25]:
        if not li.strip() or li.startswith('#!'):
            continue
        c = COMENTARIO.match(li)
        if not c:
            if ext in ('.py', '.sh', '') and re.match(r'^(set |import |from |[A-Z_]+=)', li.strip()):
                continue
            break
        t = c.group(1)
        if t and not RUIDO.match(t) and re.search(r'[A-Za-zÁÉÍÓÚáéíóúñ]{3}', t):
            return _limpia(t)
    return ''


def descripcion(rel, abs_):
    if rel in DESCRIPCIONES:
        return DESCRIPCIONES[rel]
    d = cabecera(abs_)
    if d:
        return d
    ext = os.path.splitext(rel)[1].lower()
    base = os.path.splitext(os.path.basename(rel))[0].replace('_', ' ').replace('-', ' ')
    if ext in REGLAS_EXT:
        return f'{REGLAS_EXT[ext]}: {base}'
    return f'Fichero {base}'


def recorrer():
    """Devuelve [(rel_dir, [(nombre, rel, desc)], [subdirs])] en orden."""
    filas = []
    for dirpath, dirnames, filenames in os.walk(RAIZ):
        dirnames[:] = sorted(d for d in dirnames if d not in IGNORAR_DIR)
        rel_dir = os.path.relpath(dirpath, RAIZ).replace(os.sep, '/')
        fic = []
        for n in sorted(filenames, key=str.lower):
            if os.path.splitext(n)[1].lower() in IGNORAR_EXT:
                continue
            rel = n if rel_dir == '.' else f'{rel_dir}/{n}'
            fic.append((n, rel, descripcion(rel, os.path.join(dirpath, n))))
        filas.append((rel_dir, fic))
    return filas


def generar():
    filas = recorrer()
    total = sum(len(f) for _, f in filas)
    out = [
        '# Estructura de ficheros',
        '',
        '> Documento **generado** por `python3 tools/estructura.py`. No lo edites a mano:',
        '> cambia la cabecera del fichero o `DESCRIPCIONES` en el generador y vuelve a ejecutarlo.',
        '',
        f'El repositorio tiene **{total} ficheros** en **{len(filas)} carpetas**.',
        '',
        '## Árbol de carpetas',
        '',
        '```',
    ]
    for rel_dir, fic in filas:
        nivel = 0 if rel_dir == '.' else rel_dir.count('/') + 1
        nombre = '.' if rel_dir == '.' else rel_dir.split('/')[-1] + '/'
        izq = '  ' * nivel + nombre
        out.append(f'{izq:<34} {len(fic):>4}  {CARPETAS.get(rel_dir, "")}'.rstrip())
    out += ['```', '', '## Qué hace cada fichero', '']
    for rel_dir, fic in filas:
        if not fic:
            continue
        titulo = '/ (raíz)' if rel_dir == '.' else rel_dir + '/'
        out.append(f'### `{titulo}`')
        if CARPETAS.get(rel_dir):
            out.append('')
            out.append(CARPETAS[rel_dir] + '.')
        out += ['', '| Fichero | Qué hace |', '|---|---|']
        for n, _rel, d in fic:
            out.append(f'| `{n}` | {d.replace("|", "/")} |')
        out.append('')
    return '\n'.join(out).rstrip() + '\n'


def main():
    texto = generar()
    if '--check' in sys.argv:
        try:
            with open(SALIDA, encoding='utf-8') as f:
                actual = f.read()
        except OSError:
            actual = ''
        if actual != texto:
            print('docs/ESTRUCTURA_FICHEROS.md no está al día: ejecuta python3 tools/estructura.py')
            return 1
        print('estructura: OK')
        return 0
    with open(SALIDA, 'w', encoding='utf-8', newline='\n') as f:
        f.write(texto)
    print(f'escrito {os.path.relpath(SALIDA, RAIZ)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
