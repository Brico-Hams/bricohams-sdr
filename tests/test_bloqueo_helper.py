#!/usr/bin/env python3
"""v5.1 · bricohams-bloqueo (root) y bricohams-login-aviso (Telegram).
El helper nunca mete la LAN en nft, carga todo en una sola transacción y siempre deja estado.json;
el aviso solo salta con logins correctos y no repite la misma IP en 10 minutos."""
import importlib.machinery
import importlib.util
import json
import os
import shutil
import tempfile

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
BIN = os.path.join(RAIZ, 'files', 'bin')


def cargar(nombre, fichero):
    c = importlib.machinery.SourceFileLoader(nombre, os.path.join(BIN, fichero))
    m = importlib.util.module_from_spec(importlib.util.spec_from_loader(nombre, c))
    c.exec_module(m)
    return m


tmp = tempfile.mkdtemp()
try:
    os.environ.update(BRICOHAMS_BLOQUEO_CONF=os.path.join(tmp, 'bloqueo.json'),
                      BRICOHAMS_BLOQUEO_VAR=os.path.join(tmp, 'var'),
                      BRICOHAMS_KIT_ENV=os.path.join(tmp, 'kit.env'))
    B = cargar('bricohams_bloqueo', 'bricohams-bloqueo')

    class R:
        def __init__(self, rc=0, out=''):
            self.returncode, self.stdout, self.stderr = rc, out, 'error nft'

    nfts, runs = [], []
    hay_tabla = [True]

    def falso_nft(*args, entrada=None):
        nfts.append((args, entrada))
        if args[:1] == ('list',):
            if not hay_tabla[0]:
                return R(1)
            return R(0, 'ip saddr @manual4 counter packets 5 bytes 300 drop comment "bloqueo manual"\n'
                        'ip6 saddr @manual6 counter packets 2 bytes 100 drop comment "bloqueo manual"\n'
                        'ip saddr @geo4 counter packets 9 bytes 500 drop comment "bloqueo por país"\n')
        return R(0)

    def falso_run(cmd, **k):
        runs.append(list(cmd))
        if cmd[:2] == ['fail2ban-client', 'status']:
            return R(0, 'Status\n`- Banned IP list:\t203.0.113.4 basura 2001:db8::9\n')
        if cmd[0] == 'systemctl':
            return R(0, 'active\n')
        return R(0)
    B.nft = falso_nft
    B.subprocess.run = falso_run
    B.shutil.which = lambda x: '/usr/sbin/' + x

    # --- la conf se depura: nada de LAN, ni redes enormes, ni basura
    with open(B.CONF, 'w', encoding='utf-8') as f:
        json.dump({'ips': [{'red': '203.0.113.7'}, '192.168.1.0/24', '10.1.2.3', '1.0.0.0/4', 'x',
                           {'red': '2001:db8::/48'}, '203.0.113.7/32'],
                   'paises': ['RU', 'es', 'es', 'xyz', '1a']}, f)
    ips, paises = B.leer_conf()
    assert ips == ['203.0.113.7/32', '2001:db8::/48'] and paises == ['ru', 'es'], (ips, paises)

    # --- zonas de país: se filtran las redes protegidas
    os.makedirs(B.ZONAS)
    with open(os.path.join(B.ZONAS, 'ru.zone'), 'w') as f:
        f.write('# c\n5.8.0.0/16\n5.9.0.0/16\n192.168.0.0/16\nmal\n2a00::/16\n')
    with open(os.path.join(B.ZONAS, 'ru-v6.zone'), 'w') as f:
        f.write('2a00:1::/32\nfe80::/10\n')
    txt, ngeo = B.reglas(ips, paises)
    assert ngeo == 3, ngeo
    assert '5.8.0.0/15' in txt and '192.168' not in txt and 'fe80' not in txt
    assert 'elements = { 203.0.113.7/32 }' in txt and '2001:db8::/48' in txt
    assert txt.index('iif "lo" accept') < txt.index('drop')
    # nft rechaza "set ip4"/"set ip6" (palabras reservadas): fallo real visto en la Pi
    assert 'set ip4 ' not in txt and 'set ip6 ' not in txt and '@ip4' not in txt and '@ip6' not in txt

    # --- aplicar: una sola transacción con borrado previo
    B.aplicar()
    args, entrada = nfts[-1]
    assert args == ('-f', '-') and entrada.startswith('table inet bricohams_bloqueo {}\ndelete table inet ')
    B.nft = lambda *a, entrada=None: R(1) if a[0] == '-f' else R(0)
    try:
        B.aplicar()
        raise AssertionError('nft falló y aplicar no avisó')
    except SystemExit as ex:
        assert 'rechazó' in str(ex)
    B.nft = falso_nft
    # sin bloqueos: se quita la tabla
    with open(B.CONF, 'w', encoding='utf-8') as f:
        json.dump({'ips': [], 'paises': []}, f)
    del nfts[:]
    B.aplicar()
    assert nfts[-1][0] == ('delete', 'table', 'inet', 'bricohams_bloqueo')
    B.shutil.which = lambda x: None
    try:
        B.aplicar()
        raise AssertionError('sin nft debía fallar')
    except SystemExit:
        pass
    B.shutil.which = lambda x: '/usr/sbin/' + x

    # --- estado
    with open(B.CONF, 'w', encoding='utf-8') as f:
        json.dump({'ips': ['203.0.113.7'], 'paises': ['ru', 'cn']}, f)
    B.estado()
    with open(B.ESTADO, encoding='utf-8') as f:
        e = json.load(f)
    assert e['tabla'] == {'bloqueo manual': 7, 'bloqueo por país': 9}, e['tabla']
    assert e['baneados']['sshd'] == ['203.0.113.4', '2001:db8::9']
    assert e['zonas']['ru'] > 0 and e['zonas']['cn'] == 0 and e['ips'] == 1
    assert e['unidades']['nginx'] == 'active'
    assert not [x for x in os.listdir(B.VAR) if x.startswith('tmp')], 'quedó un temporal'
    hay_tabla[0] = False
    B.estado()
    with open(B.ESTADO, encoding='utf-8') as f:
        assert json.load(f)['tabla'] is None
    hay_tabla[0] = True

    # --- desbanear: solo IPs válidas, y el fichero se consume
    with open(B.DESBANEAR, 'w', encoding='utf-8') as f:
        json.dump(['203.0.113.4', '1.2.3.4; reboot', '2001:db8::9'], f)
    del runs[:]
    B.desbanear()
    assert runs == [['fail2ban-client', 'unban', '203.0.113.4'], ['fail2ban-client', 'unban', '2001:db8::9']]
    assert not os.path.exists(B.DESBANEAR)
    B.desbanear()

    # --- main
    assert B.main(['x', 'rm -rf']) == 2 and B.main(['x']) == 2
    os.remove(B.ESTADO)
    assert B.main(['x', 'estado']) == 0 and os.path.exists(B.ESTADO)
    os.remove(B.ESTADO)
    B.nft = lambda *a, entrada=None: R(1) if a[0] == '-f' else R(0)
    try:
        B.main(['x', 'aplicar'])
    except SystemExit:
        pass
    assert os.path.exists(B.ESTADO), 'el estado se escribe aunque falle la orden'
    B.nft = falso_nft
    del nfts[:]
    B.main(['x', 'quitar'])
    assert ('delete', 'table', 'inet', 'bricohams_bloqueo') in [a for a, _ in nfts]

    # ===== bricohams-login-aviso
    L = cargar('bricohams_login_aviso', 'bricohams-login-aviso')
    BIEN = '203.0.113.20 - [15/Oct/2026:10:00:00 +0200] "POST /login HTTP/1.1" 303 "/settings"\n'
    MAL = '203.0.113.20 - [15/Oct/2026:10:00:01 +0200] "POST /login HTTP/1.1" 303 "/login?ref=/settings&error=1"\n'
    assert L.analizar(BIEN) == ('203.0.113.20', '15/Oct/2026:10:00:00 +0200', True)
    assert L.analizar(MAL)[2] is False
    assert L.analizar('203.0.113.20 - [x] "POST /login HTTP/1.1" 303 "login?error=1"')[2] is False
    assert L.analizar('203.0.113.20 - [x] "GET /login HTTP/1.1" 200 "-"') is None
    assert L.analizar('203.0.113.20 - [x] "POST /login HTTP/1.1" 429 "-"') is None
    assert L.analizar('basura') is None and L.analizar('') is None
    assert '(LAN)' in L.texto_aviso('192.168.1.10', 'h') and '(LAN)' not in L.texto_aviso('8.8.8.8', 'h')

    enviados, ahora = [], [1000.0]
    A = L.Avisador(enviar=enviados.append, reloj=lambda: ahora[0])
    assert A.linea(BIEN) and not A.linea(MAL)
    ahora[0] += 300
    assert not A.linea(BIEN), 'la misma IP no repite antes de 10 min'
    assert A.linea(BIEN.replace('203.0.113.20', '198.51.100.1'))
    ahora[0] += 301
    assert A.linea(BIEN)
    assert len(enviados) == 3 and '203.0.113.20' in enviados[0]

    assert L.activo() is False
    for valor, esperado in (('"yes"', True), ('no', False), ('si', True), ('', False)):
        with open(os.environ['BRICOHAMS_KIT_ENV'], 'w', encoding='utf-8') as f:
            f.write('# TG_AVISO_LOGIN=yes\nTG_AVISO_LOGIN=%s\n' % valor)
        assert L.activo() is esperado, valor
    print('OK test_bloqueo_helper')
finally:
    shutil.rmtree(tmp, ignore_errors=True)
