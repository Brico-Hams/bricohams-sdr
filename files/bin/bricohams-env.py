#!/usr/bin/env python3
# =====================================================================
#  bricohams-env · lector SEGURO de bricohams.env (v4.2)
#
#  Antes, install.sh hacía «. bricohams.env». Si una clave llevaba un «$»
#  entre comillas dobles (QRZ_PASS="abc$Clave2026"), bash lo tomaba por una
#  variable y el instalador se paraba con «Clave2026: unbound variable»
#  (o, peor, la clave se guardaba recortada sin avisar).
#
#  Este lector entiende la sintaxis de bricohams.env SIN ejecutar nada:
#    NOMBRE="valor"     comillas dobles: \" \\ \$ \` son escapes; un «$» suelto es LITERAL
#    NOMBRE='valor'     comillas simples: todo literal
#    NOMBRE=valor       sin comillas, hasta el primer espacio o « #»
#    export NOMBRE=…    también vale
#    # comentario       y comentarios al final de la línea
#
#  Uso:
#    bricohams-env.py --shell FICHERO        líneas «export NOMBRE='valor'» para eval en bash
#    bricohams-env.py --normalizar FICHERO   copia limpia, todo entre comillas simples
#                                            (la que se instala en /etc/bricohams/bricohams.env)
#    bricohams-env.py --comprobar FICHERO    solo avisos y errores
#  Los avisos van a stderr. Sale con 1 si hay un error de sintaxis.
# =====================================================================
import re
import sys

NOMBRE_RE = re.compile(r'^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$')
# variables de bash de solo lectura o con significado especial: un «UID=…» rompería el instalador
RESERVADAS = {'UID', 'EUID', 'PPID', 'BASHOPTS', 'SHELLOPTS', 'BASH_VERSINFO', 'BASHPID', 'GROUPS', 'FUNCNAME',
              'PATH', 'IFS', 'HOME', 'SHELL', 'PWD', 'OLDPWD', 'LANG', 'LC_ALL', 'BASH_ENV', 'ENV', 'PS4', 'SHLVL'}
ESCAPES_DOBLES = '"\\$`'


class ErrorEnv(Exception):
    pass


def leer_valor(resto, n):
    """Interpreta lo que hay tras «=». Devuelve (valor, avisos)."""
    i, out, avisos = 0, [], []
    while i < len(resto):
        c = resto[i]
        if c == '"':
            j = i + 1
            while True:
                if j >= len(resto):
                    raise ErrorEnv('línea %d: falta cerrar las comillas dobles' % n)
                d = resto[j]
                if d == '\\' and j + 1 < len(resto) and resto[j + 1] in ESCAPES_DOBLES:
                    out.append(resto[j + 1]); j += 2; continue
                if d == '"':
                    break
                if d == '$' and j + 1 < len(resto) and re.match(r'[A-Za-z_{(]', resto[j + 1]):
                    avisos.append('línea %d: «$%s…» entre comillas dobles se toma LITERAL (no es una variable). '
                                  'Para que quede claro, usa comillas simples: NOMBRE=\'…\'' % (n, resto[j + 1]))
                out.append(d); j += 1
            i = j + 1
        elif c == "'":
            j = resto.find("'", i + 1)
            if j < 0:
                raise ErrorEnv('línea %d: falta cerrar las comillas simples' % n)
            out.append(resto[i + 1:j]); i = j + 1
        elif c in ' \t':
            rest = resto[i:].strip()
            if rest and not rest.startswith('#'):
                raise ErrorEnv('línea %d: texto suelto tras el valor («%s»): ¿faltan comillas?' % (n, rest[:20]))
            break
        elif c == '#' and (i == 0 or resto[i - 1] in ' \t'):
            break
        elif c == '\\' and i + 1 < len(resto):
            out.append(resto[i + 1]); i += 2
        else:
            out.append(c); i += 1
    return ''.join(out), avisos


def leer(texto):
    """Devuelve ([(nombre, valor)…], avisos). El último valor de un nombre repetido gana."""
    vars_, avisos, vistos = {}, [], {}
    for n, linea in enumerate(texto.splitlines(), 1):
        linea = linea.rstrip('\r')
        if not linea.strip() or linea.lstrip().startswith('#'):
            continue
        m = NOMBRE_RE.match(linea)
        if not m:
            raise ErrorEnv('línea %d: no es NOMBRE=valor: «%s»' % (n, linea.strip()[:40]))
        nombre = m.group(1)
        if nombre in RESERVADAS:
            raise ErrorEnv('línea %d: %s es una variable del sistema; ponle otro nombre' % (n, nombre))
        valor, av = leer_valor(m.group(2), n)
        avisos += ['%s (%s)' % (a, nombre) for a in av]
        if nombre in vistos:
            avisos.append('línea %d: %s repetida (ya estaba en la línea %d): vale la última' % (n, nombre, vistos[nombre]))
        vistos[nombre] = n
        vars_[nombre] = valor
    return list(vars_.items()), avisos


def sq(v):
    """Comillas simples de shell (también las entiende systemd EnvironmentFile)."""
    return "'" + v.replace("'", "'\\''") + "'"


def main(argv):
    if len(argv) != 3 or argv[1] not in ('--shell', '--normalizar', '--comprobar'):
        print(__doc__ or 'uso: bricohams-env.py --shell|--normalizar|--comprobar FICHERO', file=sys.stderr)
        return 2
    try:
        with open(argv[2], encoding='utf-8') as f:
            pares, avisos = leer(f.read())
    except (OSError, UnicodeDecodeError, ErrorEnv) as e:
        print('✘ %s: %s' % (argv[2], e), file=sys.stderr)
        return 1
    for a in avisos:
        print('  ! bricohams.env %s' % a, file=sys.stderr)
    if argv[1] == '--shell':
        for k, v in pares:
            print('export %s=%s' % (k, sq(v)))
    elif argv[1] == '--normalizar':
        print('# Generado por install.sh desde bricohams.env (v4.2): valores entre comillas simples,')
        print('# sin expansión de «$». No lo edites aquí: edita bricohams.env en el kit.')
        for k, v in pares:
            print('%s=%s' % (k, sq(v)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
