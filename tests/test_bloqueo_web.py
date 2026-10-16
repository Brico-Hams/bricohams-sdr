#!/usr/bin/env python3
"""v5.1 · Ajustes > Seguridad: bloqueo por IP/país, panel del cortafuegos y alta/baja de usuarios.
Nunca se bloquea la LAN, la clave de un usuario jamás viaja en argv ni aparece en la página,
y no se puede desactivar ni borrar al último usuario activo."""
import importlib.machinery
import importlib.util
import json
import os
import re
import shutil
import tempfile
import time

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
BIN = os.path.join(RAIZ, 'files', 'bin')
tmp = tempfile.mkdtemp()
try:
    ej = open(os.path.join(RAIZ, 'bricohams.env.example'), encoding='utf-8').read()
    urls = dict(re.findall(r'^(MESH_CHANNEL_URL|MESH433_CHANNEL_URL)="([^"]+)"', ej, re.M))
    kit = os.path.join(tmp, 'kit.env')
    with open(kit, 'w', encoding='utf-8') as f:
        f.write('MESH433_CHANNEL_URL="%s"\nMESH_CHANNEL_URL="%s"\n' % (urls['MESH433_CHANNEL_URL'],
                                                                   urls['MESH_CHANNEL_URL']))
    usuarios = os.path.join(tmp, 'users.json')
    with open(usuarios, 'w', encoding='utf-8') as f:
        json.dump([{'user': 'admin', 'enabled': True, 'password': {'encoding': 'hash', 'value': 'HASHSECRETO'}},
                   {'user': 'viejo', 'enabled': False}], f)
    os.environ.update(MESH_ADMIN_OWRX='127.0.0.1:9', BRICOHAMS_ENV=kit, BRICOHAMS_KIT_ENV=kit, RAK_RUN_DIR=tmp,
                      MESH_URL_CLI=os.path.join(BIN, 'bricohams-mesh-url'),
                      BACKUP_REMOTO_CONF=os.path.join(tmp, 'br', 'c.json'),
                      BACKUP_REMOTO_SECRET=os.path.join(tmp, 'br', 's.json'), BACKUP_REMOTO_DIR=os.path.join(tmp, 'brd'),
                      BRICOHAMS_BLOQUEO_CONF=os.path.join(tmp, 'etc', 'bloqueo.json'),
                      BRICOHAMS_BLOQUEO_VAR=os.path.join(tmp, 'var'), BRICOHAMS_OWRX_USUARIOS=usuarios)
    cargador = importlib.machinery.SourceFileLoader('mesh_admin_bloqueo', os.path.join(BIN, 'bricohams-mesh-admin'))
    M = importlib.util.module_from_spec(importlib.util.spec_from_loader('mesh_admin_bloqueo', cargador))
    cargador.exec_module(M)
    M.TRABAJO.lanzar = lambda *a, **k: True

    llamadas = []

    class R:
        def __init__(self, rc=0, out=''):
            self.returncode, self.stdout, self.stderr = rc, out, ''

    def falso_run(cmd, **k):
        llamadas.append((list(cmd), dict(k.get('env') or {})))
        return R()
    M.subprocess.run = falso_run
    M.estado_unidad = lambda u: (u != 'fail2ban', True, 'active')
    M.registro = lambda u, n=20: 'linea de %s' % u

    def falla(f, *a):
        try:
            f(*a)
        except (ValueError, OSError) as ex:
            return str(ex)
        raise AssertionError('debía fallar: %r' % (a,))

    # --- direcciones
    assert M.bloqueo_red(' 203.0.113.7 ') == '203.0.113.7/32'
    assert M.bloqueo_red('198.51.100.9/24') == '198.51.100.0/24'
    assert M.bloqueo_red('2001:db8::1') == '2001:db8::1/128'
    for malo in ('', 'hola', '192.168.1.50', '10.0.0.0/8', '127.0.0.1', '0.0.0.0/0', '1.0.0.0/7',
                 '::1', 'fe80::1', '2000::/3', '169.254.1.1', '224.0.0.1', 'x' * 60):
        falla(M.bloqueo_red, malo)

    # --- bloquear / desbloquear IP
    assert 'Bloqueada' in M.accion_seguridad({'accion': 'seg-bloquearip', 'red': '203.0.113.7, 198.51.100.0/24',
                                              'nota': 'fuerza\x00bruta'})
    d = M.bloqueo_leer()
    assert [x['red'] for x in d['ips']] == ['203.0.113.7/32', '198.51.100.0/24'] and d['ips'][0]['nota'] == 'fuerzabruta'
    assert llamadas[-1][0] == ['systemctl', 'start', '--no-block', 'bricohams-bloqueo@aplicar.service']
    if os.name == 'posix':
        assert os.stat(M.BLOQUEO_CONF).st_mode & 0o077 == 0
    falla(M.accion_seguridad, {'accion': 'seg-bloquearip', 'red': '203.0.113.8 192.168.1.1'})
    assert len(M.bloqueo_leer()['ips']) == 2, 'una entrada LAN no debe dejar guardar ninguna'
    falla(M.accion_seguridad, {'accion': 'seg-bloquearip'})
    M.accion_seguridad({'accion': 'seg-bloquearip', 'red': '203.0.113.7'})
    assert len(M.bloqueo_leer()['ips']) == 2, 'sin duplicados'
    M.accion_seguridad({'accion': 'seg-desbloquearip', 'red': '203.0.113.7/32'})
    assert [x['red'] for x in M.bloqueo_leer()['ips']] == ['198.51.100.0/24']

    # --- países
    assert 'CN, RU' in M.accion_seguridad({'accion': 'seg-bloquearpais', 'paises': 'CN ru,cn'})
    assert M.bloqueo_leer()['paises'] == ['cn', 'ru']
    assert llamadas[-1][0][-1] == 'bricohams-bloqueo@geo-actualizar.service'
    for malo in ('', 'china', 'c1', 'es;rm -rf'):
        falla(M.accion_seguridad, {'accion': 'seg-bloquearpais', 'paises': malo})
    M.accion_seguridad({'accion': 'seg-desbloquearpais', 'pais': 'cn'})
    assert M.bloqueo_leer()['paises'] == ['ru']

    # --- fichero roto o manipulado: se ignora lo malo, nunca entra la LAN
    with open(M.BLOQUEO_CONF, 'w', encoding='utf-8') as f:
        json.dump({'ips': ['192.168.0.0/16', {'red': '203.0.113.1'}, 'basura', 5], 'paises': ['es', 'ESP', 'es']}, f)
    d = M.bloqueo_leer()
    assert [x['red'] for x in d['ips']] == ['203.0.113.1/32'] and d['paises'] == ['es']
    with open(M.BLOQUEO_CONF, 'w', encoding='utf-8') as f:
        f.write('[roto')
    assert M.bloqueo_leer() == {'ips': [], 'paises': []}

    # --- desbanear, refrescar, recargar
    M.accion_seguridad({'accion': 'seg-desbanear', 'ip': '203.0.113.50'})
    M.accion_seguridad({'accion': 'seg-desbanear', 'ip': '203.0.113.50'})
    M.accion_seguridad({'accion': 'seg-desbanear', 'ip': '2001:db8::5'})
    with open(os.path.join(M.BLOQUEO_VAR, 'desbanear.json'), encoding='utf-8') as f:
        assert json.load(f) == ['2001:db8::5', '203.0.113.50']
    assert llamadas[-1][0][-1] == 'bricohams-bloqueo@desbanear.service'
    falla(M.accion_seguridad, {'accion': 'seg-desbanear', 'ip': '1.2.3.4; reboot'})
    M.accion_seguridad({'accion': 'seg-refrescar'})
    assert llamadas[-1][0][-1] == 'bricohams-bloqueo@estado.service'
    del llamadas[:]
    M.accion_seguridad({'accion': 'seg-recargarfw'})
    ordenes = [c for c, _ in llamadas]
    assert ['systemctl', 'restart', 'bricohams-cortafuegos.service'] in ordenes
    assert ['systemctl', 'reload', 'nginx.service'] in ordenes
    assert not any('fail2ban.service' in c for c in ordenes), 'solo se recargan unidades instaladas'
    assert ordenes[-1][-1] == 'bricohams-bloqueo@aplicar.service'
    M.subprocess.run = lambda cmd, **k: R(1)
    assert 'no se pudo lanzar' in falla(M.accion_seguridad, {'accion': 'seg-refrescar'})
    M.subprocess.run = falso_run

    # --- usuarios
    CLAVE = 'ClaveMuySegura#2026'
    assert M.owrx_usuarios() == [('admin', True), ('viejo', False)]
    del llamadas[:]
    assert 'creado' in M.accion_seguridad({'accion': 'seg-usuarionuevo', 'usuario': 'operador',
                                           'clave': CLAVE, 'clave2': CLAVE})
    cmd, env = llamadas[-1]
    assert cmd == ['openwebrx', 'admin', '--noninteractive', 'adduser', 'operador']
    assert env.get('OWRX_PASSWORD') == CLAVE and CLAVE not in ' '.join(cmd)
    for campos in ({'usuario': 'otro', 'clave': CLAVE, 'clave2': CLAVE + 'x'},
                   {'usuario': 'otro', 'clave': 'corta', 'clave2': 'corta'},
                   {'usuario': 'otro', 'clave': 'con espacios dentro', 'clave2': 'con espacios dentro'},
                   {'usuario': 'admin', 'clave': CLAVE, 'clave2': CLAVE},
                   {'usuario': 'mal usuario', 'clave': CLAVE, 'clave2': CLAVE},
                   {'usuario': '../etc', 'clave': CLAVE, 'clave2': CLAVE}):
        falla(M.accion_seguridad, dict(campos, accion='seg-usuarionuevo'))
    M.accion_seguridad({'accion': 'seg-usuarioclave', 'usuario': 'admin', 'clave': CLAVE, 'clave2': CLAVE})
    assert llamadas[-1][0][-2:] == ['resetpassword', 'admin'] and llamadas[-1][1]['OWRX_PASSWORD'] == CLAVE
    falla(M.accion_seguridad, {'accion': 'seg-usuarioclave', 'usuario': 'nadie', 'clave': CLAVE, 'clave2': CLAVE})
    # admin es el único activo: ni desactivarlo ni borrarlo
    assert 'único' in falla(M.accion_seguridad, {'accion': 'seg-usuariodesactivar', 'usuario': 'admin'})
    assert 'único' in falla(M.accion_seguridad, {'accion': 'seg-usuarioborrar', 'usuario': 'admin',
                                                  'confirmar': 'admin'})
    M.accion_seguridad({'accion': 'seg-usuarioactivar', 'usuario': 'viejo'})
    assert llamadas[-1][0][-2:] == ['enableuser', 'viejo'] and 'OWRX_PASSWORD' not in llamadas[-1][1]
    falla(M.accion_seguridad, {'accion': 'seg-usuarioborrar', 'usuario': 'viejo'})
    with open(usuarios, 'w', encoding='utf-8') as f:
        json.dump([{'user': 'admin', 'enabled': True}, {'user': 'viejo', 'enabled': True}], f)
    M.accion_seguridad({'accion': 'seg-usuarioborrar', 'usuario': 'viejo', 'confirmar': 'viejo'})
    assert llamadas[-1][0][-2:] == ['removeuser', 'viejo']
    M.accion_seguridad({'accion': 'seg-usuariodesactivar', 'usuario': 'viejo'})
    assert llamadas[-1][0][-2:] == ['disableuser', 'viejo']
    falla(M.accion_seguridad, {'accion': 'seg-usuarioraro', 'usuario': 'admin'})
    M.subprocess.run = lambda cmd, **k: R(1)
    falla(M.accion_seguridad, {'accion': 'seg-usuarioactivar', 'usuario': 'admin'})
    M.subprocess.run = falso_run
    # Docker: la clave pasa con -e NOMBRE (sin valor) y por entorno
    with open(kit, 'a', encoding='utf-8') as f:
        f.write('OWRX_BACKEND="docker"\nOWRX_DOCKER_CONTAINER="owrx-mbe"\n')
    M.accion_seguridad({'accion': 'seg-usuarioclave', 'usuario': 'admin', 'clave': CLAVE, 'clave2': CLAVE})
    cmd, env = llamadas[-1]
    assert cmd[:5] == ['docker', 'exec', '-e', 'OWRX_PASSWORD', 'owrx-mbe'] and CLAVE not in ' '.join(cmd)
    assert env['OWRX_PASSWORD'] == CLAVE

    # --- la página
    with open(M.BLOQUEO_CONF, 'w', encoding='utf-8') as f:
        json.dump({'ips': [{'red': '203.0.113.9', 'nota': '<script>x</script>', 'fecha': '2026-10-15 10:00'}],
                   'paises': ['ru', 'cn']}, f)
    os.makedirs(M.BLOQUEO_VAR, exist_ok=True)
    with open(os.path.join(M.BLOQUEO_VAR, 'estado.json'), 'w', encoding='utf-8') as f:
        json.dump({'fecha': int(time.time()), 'tabla': {'ip': 7, 'geo': 3}, 'zonas': {'ru': int(time.time()), 'cn': 0},
                   'baneados': {'nginx-login': ['198.51.100.66']}}, f)
    html = M.pagina_seguridad('SesionAdmin_1234567890')
    for trozo in ('Bloqueo por IP y por país', '203.0.113.9/32', '&lt;script&gt;', 'RU', 'sin descargar',
                  '198.51.100.66', 'seg-desbanear', 'seg-recargarfw', 'Cortafuegos y nginx', 'linea de fail2ban',
                  'Usuarios de la web', 'seg-usuarionuevo', 'seg-usuarioborrar', 'name="csrf"', 'ip 7'):
        assert trozo in html, trozo
    assert '<script>' not in html and 'HASHSECRETO' not in html and CLAVE not in html
    assert 'Estado a —' not in html
    os.remove(os.path.join(M.BLOQUEO_VAR, 'estado.json'))
    html = M.pagina_seguridad('SesionAdmin_1234567890')
    assert 'sin aplicar todavía' in html and 'Estado a —' in html
    assert M.ACCIONES[M.SEGURIDAD].match('seg-usuarionuevo') and not M.ACCIONES[M.BASE].match('seg-bloquearip')
    print('OK test_bloqueo_web')
finally:
    shutil.rmtree(tmp, ignore_errors=True)
