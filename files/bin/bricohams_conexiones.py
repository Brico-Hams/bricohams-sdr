"""bricohams_conexiones · BricoHams
Vínculo interno IP completa -> identidad elegida (indicativo, apodo o nombre) y aviso de Telegram de «Nuevo oyente».

  - La IP completa (validada) solo vive en un SQLite 0600 del servicio, con retención corta
    (VISITAS_IP_DIAS, 14 por defecto, entre 1 y 30) y un máximo de filas. Nunca sale por API, web ni Telegram.
  - Hacia fuera solo sale la IP enmascarada: IPv4 con los dos primeros octetos (82.160.x.x) e IPv6 con los tres
    primeros grupos (2a01:4f8:1:x:x:x:x:x).
  - La IP del cliente solo se acepta del proxy de confianza (cabecera X-Forwarded-For de nginx, que la
    sobrescribe con $remote_addr): ver ip_de_proxy().
  - El texto de identidad se limpia (sin controles ni marcas de formato) y se escapa al formar el HTML de Telegram.
"""
import html
import ipaddress
import os
import sqlite3
import threading
import time
import unicodedata

RETENCION_DEFECTO_DIAS = 14
RETENCION_MIN_DIAS, RETENCION_MAX_DIAS = 1, 30
MAX_FILAS = 5000
MAX_IDENTIDAD = 80
MARCA = '\x1f'                     # hueco de la identidad en el texto guardado del aviso (nunca sale de limpiar_identidad)
PROXIES_DEFECTO = '127.0.0.1,::1'


def retencion_dias(valor=None):
    try:
        n = int(valor if valor not in (None, '') else os.environ.get('VISITAS_IP_DIAS', RETENCION_DEFECTO_DIAS))
    except ValueError:
        n = RETENCION_DEFECTO_DIAS
    return max(RETENCION_MIN_DIAS, min(RETENCION_MAX_DIAS, n))


def ip_valida(texto):
    """IP canónica, o None si no es una dirección unicast válida (sin zona, sin multicast ni reservadas)."""
    if not isinstance(texto, str) or not 2 <= len(texto.strip()) <= 45 or '%' in texto:
        return None
    try:
        a = ipaddress.ip_address(texto.strip())
    except ValueError:
        return None
    if a.version == 6 and a.ipv4_mapped:
        a = a.ipv4_mapped
    if a.is_unspecified or a.is_multicast or a.is_reserved:
        return None
    return str(a)


def enmascarar(ip):
    """82.160.12.7 -> 82.160.x.x · 2a01:4f8:1:2::3 -> 2a01:4f8:1:x:x:x:x:x · inválida -> '?'."""
    valida = ip_valida(ip)
    if valida is None:
        return '?'
    a = ipaddress.ip_address(valida)
    if a.version == 4:
        p = valida.split('.')
        return '%s.%s.x.x' % (p[0], p[1])
    g = [x.lstrip('0') or '0' for x in a.exploded.split(':')]
    return ':'.join(g[:3] + ['x'] * 5)


def redes_confiables(valor=None):
    redes = []
    for trozo in (valor if valor is not None else os.environ.get('TRUSTED_PROXIES', PROXIES_DEFECTO)).split(','):
        trozo = trozo.strip()
        if not trozo:
            continue
        try:
            redes.append(ipaddress.ip_network(trozo, strict=False))
        except ValueError:
            continue
    return redes


def ip_de_proxy(par, cabeceras_xff, redes):
    """IP del visitante: solo si la conexión TCP viene de un proxy de confianza y X-Forwarded-For trae
    exactamente una dirección válida (nginx la sobrescribe; una cadena con comas o varias cabeceras se rechaza)."""
    try:
        origen = ipaddress.ip_address(par)
    except (ValueError, TypeError):
        return None
    if origen.version == 6 and origen.ipv4_mapped:
        origen = origen.ipv4_mapped
    if not any(origen in r for r in redes):
        return None
    if not cabeceras_xff or len(cabeceras_xff) != 1 or ',' in cabeceras_xff[0]:
        return None
    return ip_valida(cabeceras_xff[0])


def limpiar_identidad(texto, n=MAX_IDENTIDAD):
    """Texto de visualización en una línea: NFKC, sin caracteres de control, formato (bidi, ancho cero) ni sin asignar."""
    t = unicodedata.normalize('NFKC', str(texto if texto is not None else ''))
    t = ''.join(' ' if c.isspace() else c for c in t)
    t = ''.join(c for c in t if c == ' ' or unicodedata.category(c) not in ('Cc', 'Cf', 'Cs', 'Co', 'Cn'))
    return ' '.join(t.split())[:n].strip()


def esc(texto):
    return html.escape(str(texto if texto is not None else ''), quote=False)


def fragmento(identidad):
    """Parte HTML del aviso de Telegram con la identidad (vacía si no hay)."""
    identidad = limpiar_identidad(identidad)
    return ' · 👤 <b>%s</b>' % esc(identidad) if identidad else ''


class Conexiones:
    def __init__(self, ruta, reloj=time.time, dias=None, maximo=MAX_FILAS):
        os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
        mascara = os.umask(0o077)
        try:
            self.c = sqlite3.connect(ruta, check_same_thread=False, timeout=5)
        finally:
            os.umask(mascara)
        try:
            os.chmod(ruta, 0o600)
        except OSError:
            pass                                   # sistemas de ficheros sin permisos POSIX
        self.reloj, self.maximo = reloj, maximo
        self.dias = retencion_dias(dias)
        self.lock = threading.Lock()
        self.c.execute('''CREATE TABLE IF NOT EXISTS conexion (
            ip TEXT PRIMARY KEY, visto INTEGER NOT NULL, identidad TEXT, tipo TEXT,
            aviso_msg INTEGER, aviso_base TEXT)''')
        self.c.execute('CREATE INDEX IF NOT EXISTS conexion_visto ON conexion(visto)')
        self.c.commit()
        with self.lock:
            self._limpiar()

    def _limpiar(self):
        self.c.execute('DELETE FROM conexion WHERE visto < ?', (int(self.reloj()) - self.dias * 86400,))
        self.c.execute('DELETE FROM conexion WHERE ip NOT IN (SELECT ip FROM conexion ORDER BY visto DESC LIMIT ?)',
                       (self.maximo,))
        self.c.commit()

    def visto(self, ip):
        ip = ip_valida(ip)
        if ip is None:
            return False
        with self.lock:
            self.c.execute('INSERT INTO conexion (ip, visto) VALUES (?, ?) '
                           'ON CONFLICT(ip) DO UPDATE SET visto = excluded.visto', (ip, int(self.reloj())))
            self._limpiar()
        return True

    def identificar(self, ip, identidad, tipo):
        ip, identidad = ip_valida(ip), limpiar_identidad(identidad)
        if ip is None or not identidad:
            return False
        with self.lock:
            self.c.execute('INSERT INTO conexion (ip, visto, identidad, tipo) VALUES (?, ?, ?, ?) '
                           'ON CONFLICT(ip) DO UPDATE SET visto = excluded.visto, identidad = excluded.identidad, '
                           'tipo = excluded.tipo', (ip, int(self.reloj()), identidad, tipo))
            self._limpiar()
        return True

    def identidad(self, ip):
        """(identidad, tipo) vigente de esa IP, o None."""
        ip = ip_valida(ip)
        if ip is None:
            return None
        with self.lock:
            fila = self.c.execute('SELECT identidad, tipo FROM conexion WHERE ip = ? AND identidad IS NOT NULL '
                                  'AND visto >= ?', (ip, int(self.reloj()) - self.dias * 86400)).fetchone()
        return tuple(fila) if fila else None

    def guardar_aviso(self, ip, mensaje_id, base):
        ip = ip_valida(ip)
        if ip is None or not isinstance(mensaje_id, int):
            return False
        with self.lock:
            self.c.execute('INSERT INTO conexion (ip, visto, aviso_msg, aviso_base) VALUES (?, ?, ?, ?) '
                           'ON CONFLICT(ip) DO UPDATE SET aviso_msg = excluded.aviso_msg, '
                           'aviso_base = excluded.aviso_base', (ip, int(self.reloj()), mensaje_id, base[:3000]))
            self.c.commit()
        return True

    def aviso(self, ip):
        ip = ip_valida(ip)
        if ip is None:
            return None
        with self.lock:
            fila = self.c.execute('SELECT aviso_msg, aviso_base FROM conexion WHERE ip = ? '
                                  'AND aviso_msg IS NOT NULL', (ip,)).fetchone()
        return tuple(fila) if fila else None

    def cerrar(self):
        self.c.close()


def texto_aviso(base, identidad):
    return base.replace(MARCA, fragmento(identidad))


def reflejar(con, ip, identidad, tipo, editar):
    """Guarda la identidad elegida y, si ya se avisó de esa conexión, edita ese mismo aviso (no manda otro)."""
    if con is None or not con.identificar(ip, identidad, tipo):
        return False
    previo = con.aviso(ip)
    if previo and editar:
        try:
            editar(previo[0], texto_aviso(previo[1], identidad))
        except Exception:                          # noqa: BLE001 — editar es best effort (mensaje antiguo, red)
            pass
    return True
