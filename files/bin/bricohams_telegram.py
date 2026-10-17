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
import os
import queue
import re
import sys
import threading
import time
import urllib.parse
import urllib.request

MAX_MIN = 20
REPETIDO_S = 300


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
        datos = urllib.parse.urlencode({'chat_id': self.chat, 'text': texto, 'parse_mode': 'HTML',
                                        'disable_web_page_preview': 'true'}).encode()
        urllib.request.urlopen('https://api.telegram.org/bot%s/sendMessage' % self.token, datos, timeout=15).read()


def limpio(texto, n=300):
    """Texto de radio en una línea, sin caracteres de control."""
    return re.sub(r'[\x00-\x1f\x7f]+', ' ', str(texto or '')).strip()[:n]
