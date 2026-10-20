#!/usr/bin/env python3
# =====================================================================
#  bricohams-archivo-files · BricoHams
#  Tarea periódica (bricohams-archivo-files.timer):
#   1. Copia al archivo permanente de satélites todo lo que aparece en
#      «Files» de OpenWebRX+ (imágenes METEOR/SatDump, SSTV, FAX, MP3 de
#      pases y grabaciones): ARCHIVO_DIR/AAAA-MM/<nombre>, verificando
#      tamaño y SHA-256 antes de darlo por archivado. Nunca borra el archivo.
#   2. Deja en «Files» solo los ARCHIVO_FILES_ULTIMOS (2) más recientes;
#      solo elimina de Files lo que ya está archivado y verificado.
#      Los enlaces de bricohams-satrec no se tocan: los gestiona él
#      (SATREC_EN_FILES).
#  Si el disco del archivo baja de ARCHIVO_MIN_LIBRE_MB no copia ni borra.
#  Uso: bricohams-archivo-files [--simular]
# =====================================================================
import hashlib
import os
import re
import shutil
import sys
import time

# Mismo patrón que owrx/storage.py (Storage.filePattern) de OpenWebRX+
PATRON = re.compile(r'[A-Z0-9]+-[0-9]+-[0-9]+(-[0-9]+)?(-[0-9]+)?\.(bmp|png|txt|mp3)$')


def cfg_desde_env(env=os.environ):
    return {
        'files': env.get('SATREC_FILES_DIR', '/tmp'),
        'archivo': env.get('ARCHIVO_DIR', '/var/lib/bricohams/satelites/archivo'),
        'satrec': env.get('SATREC_DIR', '/var/lib/bricohams/satelites'),
        'ultimos': max(0, int(env.get('ARCHIVO_FILES_ULTIMOS', '2'))),
        'min_libre_mb': float(env.get('ARCHIVO_MIN_LIBRE_MB', '500')),
        'reposo_s': float(env.get('ARCHIVO_REPOSO_S', '60')),
    }


def sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, 'rb') as f:
        for bloque in iter(lambda: f.read(1 << 20), b''):
            h.update(bloque)
    return h.hexdigest()


def es_enlace_satrec(ruta, cfg):
    if not os.path.islink(ruta):
        return False
    grab = os.path.realpath(os.path.join(cfg['satrec'], 'grabaciones'))
    return os.path.realpath(ruta).startswith(grab + os.sep)


def candidatos(cfg):
    try:
        nombres = os.listdir(cfg['files'])
    except OSError:
        return []
    salida = []
    for n in nombres:
        ruta = os.path.join(cfg['files'], n)
        # en /tmp cualquiera puede crear enlaces: solo se siguen los de bricohams-satrec
        if os.path.islink(ruta) and not es_enlace_satrec(ruta, cfg):
            continue
        if PATRON.match(n) and os.path.isfile(ruta):
            salida.append(ruta)
    return salida


def destino(cfg, ruta):
    mes = time.strftime('%Y-%m', time.localtime(os.path.getmtime(ruta)))
    return os.path.join(cfg['archivo'], mes, os.path.basename(ruta))


def archivado(cfg, ruta):
    """Ruta del archivo si ya existe una copia idéntica (mismo tamaño y SHA-256)."""
    nombre = os.path.basename(ruta)
    base, ext = os.path.splitext(nombre)
    d = os.path.dirname(destino(cfg, ruta))
    tam = os.path.getsize(ruta)
    h = None
    for cand in [nombre] + ['%s~%d%s' % (base, i, ext) for i in range(1, 100)]:
        p = os.path.join(d, cand)
        if not os.path.exists(p):
            return None
        if os.path.getsize(p) == tam:
            h = h or sha256(ruta)
            if sha256(p) == h:
                return p
    return None


def libre_mb(ruta):
    os.makedirs(ruta, exist_ok=True)
    return shutil.disk_usage(ruta).free / 1e6


def copiar(cfg, ruta):
    """Copia verificada; nunca sobrescribe otra captura con el mismo nombre."""
    dest = destino(cfg, ruta)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    base, ext = os.path.splitext(dest)
    i = 0
    while os.path.exists(dest):
        i += 1
        dest = '%s~%d%s' % (base, i, ext)
    tmp = os.path.join(os.path.dirname(dest), '.%s.tmp' % os.path.basename(dest))
    h = sha256(ruta)
    try:
        with open(ruta, 'rb') as src, open(tmp, 'wb') as dst:
            shutil.copyfileobj(src, dst, 1 << 20)
            dst.flush()
            os.fsync(dst.fileno())
        if os.path.getsize(tmp) != os.path.getsize(ruta) or sha256(tmp) != h:
            raise OSError('verificación fallida de %s' % os.path.basename(ruta))
        st = os.stat(ruta)
        os.utime(tmp, (st.st_atime, st.st_mtime))
        os.chmod(tmp, 0o644)
        os.replace(tmp, dest)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return dest


def vuelta(cfg, ahora=None, simular=False, log=print):
    ahora = time.time() if ahora is None else ahora
    res = {'copiados': [], 'borrados': [], 'pendientes': [], 'errores': [], 'avisos': []}
    libre = libre_mb(cfg['archivo'])
    if libre < cfg['min_libre_mb']:
        log('archivo-files: solo %.0f MB libres (< %.0f): no se copia ni se borra nada'
            % (libre, cfg['min_libre_mb']))
        res['errores'].append('sin espacio')
        return res
    fich = candidatos(cfg)
    seguros = set()
    for ruta in fich:
        try:
            if ahora - os.path.getmtime(ruta) < cfg['reposo_s']:
                res['pendientes'].append(os.path.basename(ruta))   # aún escribiéndose
                continue
            if archivado(cfg, ruta):
                seguros.add(ruta)
                continue
            if simular:
                res['copiados'].append(os.path.basename(ruta))
                continue
            dest = copiar(cfg, ruta)
            seguros.add(ruta)
            res['copiados'].append(os.path.basename(ruta))
            log('archivo-files: %s → %s' % (os.path.basename(ruta), dest))
        except OSError as e:
            res['errores'].append('%s: %s' % (os.path.basename(ruta), e))
            log('archivo-files: ERROR %s: %s' % (os.path.basename(ruta), e))
    propios = [r for r in fich if not es_enlace_satrec(r, cfg)]
    propios.sort(key=lambda r: os.path.getctime(r), reverse=True)
    for ruta in propios[cfg['ultimos']:]:
        if ruta not in seguros:
            continue
        if simular:
            res['borrados'].append(os.path.basename(ruta))
            continue
        try:
            os.unlink(ruta)
            res['borrados'].append(os.path.basename(ruta))
        except OSError as e:
            # p. ej. fichero de otro usuario en /tmp (bit sticky): queda en Files, ya está archivado
            res['avisos'].append('%s: %s' % (os.path.basename(ruta), e))
            log('archivo-files: AVISO no se puede quitar de Files (ya archivado) %s: %s'
                % (os.path.basename(ruta), e.strerror or e))
    if res['borrados']:
        log('archivo-files: Files deja los %d últimos; quitados de Files (ya archivados): %s'
            % (cfg['ultimos'], ', '.join(res['borrados'])))
    return res


def main(argv):
    cfg = cfg_desde_env()
    res = vuelta(cfg, simular='--simular' in argv)
    if '--simular' in argv:
        print('copiaría: %s\nquitaría de Files: %s' % (res['copiados'], res['borrados']))
    return 1 if res['errores'] else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
