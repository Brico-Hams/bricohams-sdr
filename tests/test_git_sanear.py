#!/usr/bin/env python3
"""v5.1 · tools/git_sanear.sh y tools/datos_personales.py (manual 38).
Reproduce el fallo real: un cliente de sincronización en la nube dejó copias
«(# Name clash … #)» dentro de .git, la ref origin/HEAD con ceros, la rama
[gone] y un commit hecho en la web que borra .gitignore."""
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SANEAR = os.path.join(RAIZ, 'tools', 'git_sanear.sh')
DP = os.path.join(RAIZ, 'tools', 'datos_personales.py')
t = tempfile.mkdtemp(prefix='bh-git-')
E = dict(os.environ, GIT_AUTHOR_NAME='p', GIT_AUTHOR_EMAIL='p@example.org', GIT_COMMITTER_NAME='p',
         GIT_COMMITTER_EMAIL='p@example.org', GIT_TERMINAL_PROMPT='0', HOME=t)


def g(cwd, *a, ok=True):
    r = subprocess.run(['git', '-c', 'init.defaultBranch=main', '-c', 'protocol.file.allow=always'] + list(a),
                       cwd=cwd, capture_output=True, text=True, env=E)
    assert not ok or r.returncode == 0, (a, r.stderr)
    return r.stdout


def sanear(cwd, *a):
    r = subprocess.run(['bash', SANEAR] + list(a), cwd=cwd, capture_output=True, text=True, env=E)
    return r.returncode, r.stdout + r.stderr


try:
    remoto, kit, web = os.path.join(t, 'remoto.git'), os.path.join(t, 'kit'), os.path.join(t, 'web')
    g(t, 'init', '-q', '--bare', remoto)
    g(t, 'clone', '-q', remoto, kit)
    open(os.path.join(kit, '.gitignore'), 'w').write('bricohams.env\n')
    open(os.path.join(kit, 'README.md'), 'w').write('kit\n')
    g(kit, 'add', '.')
    g(kit, 'commit', '-qm', 'v5.0')
    g(kit, 'push', '-q', 'origin', 'main')
    # «Delete .gitignore» hecho en la web de GitHub
    g(t, 'clone', '-q', remoto, web)
    g(web, 'rm', '-q', '.gitignore')
    g(web, 'commit', '-qm', 'Delete .gitignore')
    g(web, 'push', '-q', 'origin', 'main')
    g(kit, 'fetch', '-q')                     # el commit de la web ya estaba bajado (como en la Pi real)
    # lo que dejó el cliente de la nube en .git
    refs = os.path.join(kit, '.git', 'refs', 'remotes', 'origin')
    os.remove(os.path.join(refs, 'main'))
    open(os.path.join(refs, 'HEAD (# Name clash 2026-10-11 vrc3kbC #)'), 'w').write('ref: refs/remotes/origin/main\n')
    open(os.path.join(refs, 'roto'), 'w').write('0' * 40 + '\n')
    assert ': gone]' in g(kit, 'branch', '-vv')
    open(os.path.join(kit, 'bricohams.env'), 'w').write('APRS_PASSCODE="12345"\n')

    rc, o = sanear(kit)
    assert rc == 1, o
    for txt in ('copias de conflicto', 'ref rota', 'existe en GitHub', 'el remoto BORRA .gitignore', '[gone]',
                'bricohams.env no está en el git', 'algo sincroniza esta carpeta'):
        assert txt in o, (txt, o)
    assert os.path.exists(os.path.join(refs, 'HEAD (# Name clash 2026-10-11 vrc3kbC #)')), 'sin --reparar no se toca nada'

    rc, o = sanear(kit, '--reparar')
    assert 'apartado' in o and '_conflictos_' in o, o
    assert not [f for f in os.listdir(refs) if 'Name clash' in f or f == 'roto'], os.listdir(refs)
    assert os.path.exists(os.path.join(refs, 'main')), 'el fetch recupera origin/main'
    assert ': gone]' not in g(kit, 'branch', '-vv')
    apartados = [d for d in os.listdir(os.path.join(kit, '.git')) if d.startswith('_conflictos_')]
    assert apartados, 'lo apartado se conserva (nada se borra)'
    rc, o = sanear(kit)
    assert 'copias de conflicto' not in o and 'ref rota' not in o and 'solo falta traer' in o, o

    # datos_personales: el env personal no cuenta, su contenido sí si se copia a otro fichero
    rc = subprocess.run([sys.executable, DP, '--raiz', kit], capture_output=True, text=True)
    assert rc.returncode == 0 and 'limpio' in rc.stdout, rc.stdout
    huellas = os.path.join(t, 'huellas.txt')
    open(huellas, 'w').write(subprocess.run([sys.executable, DP, '--huella', '10.99.88'], capture_output=True,
                                            text=True).stdout.replace('<tipo de dato>', 'red de casa'))
    open(os.path.join(kit, 'notas.md'), 'w').write('el passcode es 12345 y la red 10.99.88.7\n')
    rc = subprocess.run([sys.executable, DP, '--raiz', kit], capture_output=True, text=True,
                        env=dict(os.environ, DATOS_PERSONALES_HUELLAS=huellas))
    assert rc.returncode == 1 and 'APRS_PASSCODE' in rc.stdout and 'red de casa' in rc.stdout, rc.stdout
    assert '12345' not in rc.stdout and '10.99.88' not in rc.stdout, 'nunca imprime el valor'
    # el árbol del propio kit, limpio (sin env personal: solo huellas)
    rc = subprocess.run([sys.executable, DP, '--raiz', RAIZ, '--env', os.devnull], capture_output=True, text=True)
    assert rc.returncode == 0, rc.stdout
finally:
    shutil.rmtree(t, ignore_errors=True)
print('OK test_git_sanear: copias «Name clash» en .git, ref rota, rama [gone], .gitignore borrado en la web, '
      'reparación sin borrar nada y repositorio sin datos personales')
