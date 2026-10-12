"""
BricoHams - Squelch por subtono CTCSS para la demodulacion FM (nfm) de OpenWebRX+.

El modulo se inserta en la cadena NFm (FmDemod -> Limit -> NfmDeemphasis -> [CtcssSquelch] -> Agc)
solo cuando el usuario (o el marcador) fija un subtono. Con 0 / None se retira de la cadena
y el comportamiento de OpenWebRX queda exactamente como el original.

Deteccion:
  * paso-banda 55-280 Hz (Butterworth, con estado) y diezmado a ~1200 Hz
  * ventana Hann de 1 s, evaluada cada 0.1 s, DFT directa en las 50 frecuencias EIA
  * r = |X_tono|^2 / (sum(x^2) * N/8)  -> 1.0 para un tono puro, ~3/N para ruido blanco
  * abre si r > ABRIR y el tono pedido es el mas fuerte (x2) entre los tonos estandar
  * cierra si r < CERRAR durante HOLD segundos
Audio: con el squelch abierto se aplica un paso-alto de 300 Hz (elimina el subtono audible);
cerrado se emiten ceros. La ganancia se rampa para evitar clics.
"""

import logging
import threading

import numpy as np
from scipy import signal

logger = logging.getLogger(__name__)

TONOS_EIA = (
    67.0, 69.3, 71.9, 74.4, 77.0, 79.7, 82.5, 85.4, 88.5, 91.5, 94.8, 97.4, 100.0, 103.5,
    107.2, 110.9, 114.8, 118.8, 123.0, 127.3, 131.8, 136.5, 141.3, 146.2, 150.0, 151.4,
    156.7, 159.8, 162.2, 165.5, 167.9, 171.3, 173.8, 177.3, 179.9, 183.5, 186.2, 189.9,
    192.8, 196.6, 199.5, 203.5, 206.5, 210.7, 218.1, 225.7, 229.1, 233.6, 241.8, 250.3, 254.1,
)

TONO_MIN = 60.0
TONO_MAX = 260.0

ABRIR = 0.25
CERRAR = 0.08
HOLD = 0.4
VENTANA = 1.0
SALTO = 0.1
FS_OBJETIVO = 1200.0


def normalizar_tono(valor):
    """Devuelve el tono como float con 1 decimal, o 0.0 si esta desactivado/vacio.
    Lanza ValueError si esta fuera de rango."""
    if valor is None or valor == "" or valor is False:
        return 0.0
    try:
        t = round(float(valor), 1)
    except (TypeError, ValueError):
        raise ValueError("Subtono CTCSS no valido: {}".format(valor))
    if t != t or t <= 0:
        return 0.0
    if t < TONO_MIN or t > TONO_MAX:
        raise ValueError("Subtono CTCSS fuera de rango ({}-{} Hz): {}".format(TONO_MIN, TONO_MAX, valor))
    return t


class CtcssDetector(object):
    """Detector puro (numpy/scipy). Se alimenta con bloques de audio float y devuelve abierto/cerrado."""

    def __init__(self, fs, tono):
        self.fs = float(fs)
        self.dec = max(1, int(round(self.fs / FS_OBJETIVO)))
        self.fsd = self.fs / self.dec
        self.n = int(round(VENTANA * self.fsd))
        self.salto = max(1, int(round(SALTO * self.fsd)))
        self.sos = signal.butter(4, [55.0, 280.0], btype="bandpass", fs=self.fs, output="sos")
        self.zi = signal.sosfilt_zi(self.sos) * 0.0
        self.fase = 0
        self.buf = np.zeros(self.n, dtype=np.float64)
        self.lleno = 0
        self.pend = 0
        self.ventana = np.hanning(self.n)
        self.abierto = False
        self.bajo = 0.0
        self.r = 0.0
        self.setTono(tono)

    def setTono(self, tono):
        self.tono = float(tono)
        otros = [f for f in TONOS_EIA if abs(f - self.tono) > 1.5]
        freqs = np.array([self.tono] + otros, dtype=np.float64)
        t = np.arange(self.n) / self.fsd
        self.matriz = np.exp(-2j * np.pi * np.outer(freqs, t)) * self.ventana[None, :]
        self.abierto = False
        self.bajo = 0.0

    def _evaluar(self):
        x = self.buf - self.buf.mean()
        energia = float(np.dot(x, x))
        if energia <= 1e-20:
            self.r = 0.0
            dominante = False
        else:
            p = np.abs(self.matriz @ x) ** 2
            self.r = float(p[0] / (energia * self.n / 8.0))
            dominante = p.size == 1 or p[0] >= 2.0 * float(p[1:].max())
        if self.abierto:
            if self.r < CERRAR:
                self.bajo += self.salto / self.fsd
                if self.bajo >= HOLD:
                    self.abierto = False
                    self.bajo = 0.0
            else:
                self.bajo = 0.0
        elif self.r > ABRIR and dominante and self.lleno >= self.n // 2:
            self.abierto = True
            self.bajo = 0.0

    def procesar(self, bloque):
        y, self.zi = signal.sosfilt(self.sos, bloque, zi=self.zi)
        d = y[self.fase::self.dec]
        self.fase = (self.fase - len(y)) % self.dec
        i = 0
        while i < len(d):
            k = min(self.salto - self.pend, len(d) - i)
            self.buf = np.roll(self.buf, -k)
            self.buf[-k:] = d[i:i + k]
            self.lleno = min(self.n, self.lleno + k)
            self.pend += k
            i += k
            if self.pend >= self.salto:
                self.pend = 0
                self._evaluar()
        return self.abierto


class Procesador(object):
    """Detector + filtro de audio + rampa de ganancia, independiente de pycsdr (testeable)."""

    def __init__(self, fs, tono):
        self.fs = fs
        self.det = CtcssDetector(fs, tono)
        self.sos_hp = signal.butter(6, 300.0, btype="highpass", fs=fs, output="sos")
        self.zi_hp = signal.sosfilt_zi(self.sos_hp) * 0.0
        self.ganancia = 0.0

    def setTono(self, tono):
        self.det.setTono(tono)

    def procesar(self, x):
        x = np.asarray(x, dtype=np.float64)
        abierto = self.det.procesar(x)
        audio, self.zi_hp = signal.sosfilt(self.sos_hp, x, zi=self.zi_hp)
        objetivo = 1.0 if abierto else 0.0
        n = len(audio)
        if objetivo == self.ganancia or n == 0:
            out = audio * objetivo
        else:
            paso = 1.0 / max(1.0, 0.02 * self.fs)
            g = self.ganancia + np.sign(objetivo - self.ganancia) * paso * np.arange(1, n + 1)
            g = np.clip(g, 0.0, 1.0)
            out = audio * g
            self.ganancia = float(g[-1])
        return out.astype(np.float32)


try:
    from csdr.module import ThreadModule
    from pycsdr.types import Format

    class CtcssSquelch(ThreadModule):
        def __init__(self, rateFn, tono):
            self.rateFn = rateFn
            self.tono = float(tono)
            self.lock = threading.Lock()
            self.proc = None
            self.fs = None
            super().__init__()

        def getInputFormat(self):
            return Format.FLOAT

        def getOutputFormat(self):
            return Format.FLOAT

        def setTono(self, tono):
            with self.lock:
                self.tono = float(tono)
                if self.proc is not None:
                    self.proc.setTono(self.tono)

        def setReader(self, reader):
            # Al reemplazar NfmDeemphasis (cambio de samplerate) la cadena nos da un lector nuevo:
            # se detiene el antiguo para desbloquear read() y el bucle continua con el nuevo.
            anterior = self.reader
            super().setReader(reader)
            if anterior is not None and anterior is not reader:
                try:
                    anterior.stop()
                except Exception:
                    pass

        def run(self):
            resto = b""
            while self.doRun:
                reader = self.reader
                if reader is None:
                    break
                data = reader.read()
                if data is None:
                    if self.doRun and self.reader is not None and self.reader is not reader:
                        resto = b""
                        continue
                    break
                # El lector entrega bytes (memoryview 'B'); se conservan los bytes sobrantes de un float incompleto
                raw = resto + bytes(data)
                corte = len(raw) - (len(raw) % 4)
                resto = raw[corte:]
                x = np.frombuffer(raw[:corte], dtype=np.float32)
                if x.size == 0:
                    continue
                try:
                    with self.lock:
                        fs = int(self.rateFn())
                        if self.proc is None or fs != self.fs:
                            self.fs = fs
                            self.proc = Procesador(fs, self.tono)
                        out = self.proc.procesar(x)
                except Exception:
                    logger.exception("Error en squelch CTCSS; se deja pasar el audio")
                    out = x
                writer = self.writer
                if writer is None:
                    break
                try:
                    writer.write(out.tobytes())
                except (BrokenPipeError, ValueError):
                    break

    def aplicar(demod, tono):
        """Inserta/actualiza/retira el squelch CTCSS en una cadena NFm. Nunca lanza excepciones."""
        try:
            from csdr.chain.analog import NFm
            if demod is None or not isinstance(demod, NFm):
                return
            idx = demod.indexOf(lambda w: isinstance(w, CtcssSquelch))
            try:
                t = normalizar_tono(tono)
            except ValueError:
                t = 0.0
            if t > 0:
                if idx >= 0:
                    demod.workers[idx].setTono(t)
                else:
                    pos = min(3, len(demod.workers))
                    demod.insert(pos, CtcssSquelch(lambda: demod.sampleRate, t))
                    logger.info("CTCSS %.1f Hz activado", t)
            elif idx >= 0:
                demod.remove(idx)
                logger.info("CTCSS desactivado")
        except Exception:
            logger.exception("No se pudo aplicar el subtono CTCSS")

except ImportError:  # pragma: no cover - fuera de OpenWebRX (tests)
    CtcssSquelch = None

    def aplicar(demod, tono):
        return
