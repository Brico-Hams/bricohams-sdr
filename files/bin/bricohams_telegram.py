"""bricohams_telegram · BricoHams (v5.0)
Avisos a Telegram para los servicios en Python (registro de oyentes, mensajes
Meshtastic de canal y mensajes APRS). Solo biblioteca estándar: sirve también
dentro del entorno pipx de meshtastic.
  - Cola con hilo propio: quien avisa nunca se bloquea esperando a Telegram.
  - Límite de ritmo (MAX_MIN avisos por minuto) y sin repetidos en 5 minutos.
  - parse_mode HTML: usa esc() con todo lo que venga de fuera.
  - El token no se escribe nunca en el registro (los errores se limpian).
Credenciales: TELEGRAM_TOKEN y TELEGRAM_CHAT_ID del entorno del servicio.
"""
import collections
import html
import json
import os
import queue
import re
import sys
import threading
import time
import urllib.parse
import urllib.error
import urllib.request

MAX_MIN = 20
REPETIDO_S = 300


def enviar_mensaje(token, chat, texto, formato_html=True):
    if not token or not chat:
        raise ValueError('Telegram sin configurar (token o destino ausente).')
    campos = {'chat_id': chat, 'text': texto, 'disable_web_page_preview': 'true'}
    if formato_html:
        campos['parse_mode'] = 'HTML'
    datos = urllib.parse.urlencode(campos).encode()
    try:
        with urllib.request.urlopen('https://api.telegram.org/bot%s/sendMessage' % token,
                                    datos, timeout=20) as respuesta:
            resultado = json.load(respuesta)
    except urllib.error.HTTPError as ex:
        try:
            resultado = json.load(ex)
        except (ValueError, OSError) as lectura:
            raise RuntimeError('Telegram HTTP %s; respuesta no válida.' % ex.code) from lectura
    except OSError as ex:
        raise RuntimeError('Telegram: fallo de conexión (%s).' % type(ex).__name__) from None
    if not resultado.get('ok'):
        detalle = str(resultado.get('description', 'Respuesta sin confirmación')).replace(token, '***')[:250]
        if resultado.get('parameters', {}).get('migrate_to_chat_id'):
            detalle += ' El grupo ha migrado: sincroniza TELEGRAM_CHAT_ID en todos los servicios.'
        raise RuntimeError('Telegram %s: %s' % (resultado.get('error_code', ''), detalle))
    return resultado['result']


def obtener_actualizaciones(token, offset=None, timeout=25):
    """Lee mensajes nuevos del bot por long polling, ocultando el token en errores."""
    if not token:
        raise ValueError('Telegram sin configurar (token ausente).')
    campos = {'timeout': int(timeout), 'allowed_updates': json.dumps(['message'])}
    if offset is not None:
        campos['offset'] = int(offset)
    url = 'https://api.telegram.org/bot%s/getUpdates?%s' % (
        token, urllib.parse.urlencode(campos))
    try:
        with urllib.request.urlopen(url, timeout=int(timeout) + 10) as respuesta:
            resultado = json.load(respuesta)
    except urllib.error.HTTPError as ex:
        try:
            resultado = json.load(ex)
        except (ValueError, OSError) as lectura:
            raise RuntimeError('Telegram HTTP %s; respuesta no válida.' % ex.code) from lectura
    except OSError as ex:
        raise RuntimeError('Telegram: fallo de conexión (%s).' % type(ex).__name__) from None
    if not isinstance(resultado, dict):
        raise RuntimeError('Telegram: respuesta de actualizaciones no válida.')
    if not resultado.get('ok'):
        detalle = str(resultado.get('description', 'Respuesta sin confirmación')).replace(token, '***')[:250]
        raise RuntimeError('Telegram %s: %s' % (resultado.get('error_code', ''), detalle))
    actualizaciones = resultado.get('result')
    if not isinstance(actualizaciones, list):
        raise RuntimeError('Telegram: respuesta de actualizaciones no válida.')
    return actualizaciones


def esc(texto):
    return html.escape(str(texto if texto is not None else ''), quote=False)


def activo(valor, defecto='yes'):
    v = str(valor if valor not in (None, '') else defecto).strip().lower()
    return v in ('1', 'yes', 'si', 'sí', 'true', 'on')


class Avisador:
    def __init__(self, token=None, chat=None, nombre='bricohams', enviar=None, ahora=time.time):
        self.token = (token if token is not None else os.environ.get('TELEGRAM_TOKEN', '')).strip()
        self.chat = (chat if chat is not None else os.environ.get('TELEGRAM_CHAT_ID', '')).strip()
        self.nombre, self.ahora = nombre, ahora
        self._enviar = enviar or self._http
        self.cola = queue.Queue(maxsize=200)
        self.ultimos = collections.deque()
        self.vistos = {}
        self.lock = threading.Lock()
        self.hilo = None

    @property
    def configurado(self):
        return bool(self.token and self.chat)

    def admitir(self, texto):
        """True si el aviso entra (no repetido y dentro del límite por minuto)."""
        t = self.ahora()
        with self.lock:
            self.vistos = {k: v for k, v in self.vistos.items() if t - v < REPETIDO_S}
            if texto in self.vistos:
                return False
            while self.ultimos and t - self.ultimos[0] >= 60:
                self.ultimos.popleft()
            if len(self.ultimos) >= MAX_MIN:
                return False
            self.ultimos.append(t)
            self.vistos[texto] = t
            return True

    def avisar(self, texto):
        """Encola un aviso en HTML (ya escapado). False si no se manda."""
        if not self.configurado or not texto or not self.admitir(texto):
            return False
        try:
            self.cola.put_nowait(texto[:4000])
        except queue.Full:
            return False
        with self.lock:
            if self.hilo is None or not self.hilo.is_alive():
                self.hilo = threading.Thread(target=self._bucle, daemon=True)
                self.hilo.start()
        return True

    def _bucle(self):
        while True:
            texto = self.cola.get()
            try:
                self._enviar(texto)
            except Exception as e:           # noqa: BLE001 — sin red, token caducado…: se registra y se sigue
                print('%s: Telegram: %s' % (self.nombre, str(e).replace(self.token, '***')[:200]),
                      file=sys.stderr, flush=True)
            time.sleep(1)

    def _http(self, texto):
        return enviar_mensaje(self.token, self.chat, texto)


def limpio(texto, n=300):
    """Texto de radio en una línea, sin caracteres de control."""
    return re.sub(r'[\x00-\x1f\x7f]+', ' ', str(texto or '')).strip()[:n]
