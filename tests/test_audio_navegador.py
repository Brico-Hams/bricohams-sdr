#!/usr/bin/env python3
"""v4.2 · Plugins de audio en un navegador DE VERDAD (Chromium sin pantalla, Playwright).

Simula lo mínimo de OpenWebRX+: la barra de botones, Plugins.load() y un AudioEngine con
un AudioContext real cuyo «audioNode» es un pitido de 1 kHz + ruido de banda ancha (la «voz»). Comprueba:
  1. los tres plugins cargan sin errores y ponen sus botones FILTRO y DSP;
  2. con el filtro apagado el 1 kHz llega al altavoz; con el filtro y el notch automático
     encendidos (clic en la interfaz) baja más de 20 dB, y la banda 300–700 Hz sigue igual;
  3. el DSP se enciende y sus medidores se mueven;
  4. al apagar los dos, el audio vuelve a ser el original.
Si no hay Playwright/Chromium, la prueba se omite (lo demás está en test_audio_plugins.py)."""
import functools
import http.server
import os
import shutil
import sys
import tempfile
import threading

RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('OK test_audio_navegador: OMITIDA (no hay Playwright)')
    sys.exit(0)

HTML = r'''<!doctype html><meta charset="utf-8"><title>prueba audio</title>
<script src="jquery.js"></script>
<div class="openwebrx-main-buttons"><div class="button" id="ea5kao-solar-button">SOL</div></div>
<script>
var Plugins = { load: async function (name) {
    Plugins[name] = { _version: 0 };
    await new Promise(function (ok, ko) { var s = document.createElement('script');
        s.src = 'plugins/receiver/' + name + '/' + name + '.js'; s.onload = ok; s.onerror = ko; document.head.appendChild(s); });
    if (Plugins[name].init && !(await Plugins[name].init())) throw new Error(name + ' no arranca');
} };
var errores = [];
window.addEventListener('error', function (e) { errores.push(String(e.message)); });
var ctx = new AudioContext();
var fuente = ctx.createGain();                       // hace de AudioWorklet de OpenWebRX+
// «voz»: ruido de banda ancha (no es un pitido) + un pitido de 1 kHz, como un heterodino
var o = ctx.createOscillator(); o.frequency.value = 1000;
var g = ctx.createGain(); g.gain.value = 0.3; o.connect(g); g.connect(fuente); o.start();
var buf = ctx.createBuffer(1, ctx.sampleRate * 2, ctx.sampleRate), dat = buf.getChannelData(0);
for (var i = 0; i < dat.length; i++) dat[i] = (Math.random() * 2 - 1) * 0.2;
var ruido = ctx.createBufferSource(); ruido.buffer = buf; ruido.loop = true; ruido.connect(fuente); ruido.start();
var volumen = ctx.createGain(), mira = ctx.createAnalyser();
mira.fftSize = 8192; mira.smoothingTimeConstant = 0;
volumen.connect(mira); mira.connect(ctx.destination);
var audioEngine = { audioContext: ctx, audioNode: fuente, gainNode: volumen,
                    onStart: function (cb) { ctx.resume().then(function () { cb('AudioWorklet'); }); } };
fuente.connect(volumen);
var toma = ctx.createAnalyser(); toma.fftSize = 8192; fuente.connect(toma);   // como el osciloscopio de rig_skin
function nivelToma(hz) { var b = new Float32Array(toma.frequencyBinCount); toma.getFloatFrequencyData(b);
    var i = Math.round(hz / (ctx.sampleRate / toma.fftSize)), m = -200;
    for (var k = i - 3; k <= i + 3; k++) m = Math.max(m, b[k]); return m; }
function nivel(hz) { var b = new Float32Array(mira.frequencyBinCount); mira.getFloatFrequencyData(b);
    var i = Math.round(hz / (ctx.sampleRate / mira.fftSize)), m = -200;
    for (var k = i - 3; k <= i + 3; k++) m = Math.max(m, b[k]); return m; }
function banda(f0, f1) { var b = new Float32Array(mira.frequencyBinCount); mira.getFloatFrequencyData(b);
    var hz = ctx.sampleRate / mira.fftSize, s = 0, n = 0;
    for (var k = Math.round(f0 / hz); k <= Math.round(f1 / hz); k++) { s += b[k]; n++; } return s / n; }
var listo = (async function () { for (const n of ['audio_cadena', 'filtro_audio', 'dsp_audio']) await Plugins.load(n); return true; })();
</script>'''


@functools.lru_cache()
def servidor():
    d = tempfile.mkdtemp()
    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(HTML)
    shutil.copy(os.path.join(RAIZ, 'tests/datos/owrx/htdocs/lib/jquery-3.7.1.min.js'), os.path.join(d, 'jquery.js'))
    os.makedirs(os.path.join(d, 'plugins'))
    os.symlink(os.path.join(RAIZ, 'files/htdocs/plugins/receiver'), os.path.join(d, 'plugins/receiver'))
    class Callado(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    h = functools.partial(Callado, directory=d)
    s = http.server.ThreadingHTTPServer(('127.0.0.1', 0), h)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, d


s, d = servidor()
url = 'http://127.0.0.1:%d/index.html' % s.server_address[1]
try:
    with sync_playwright() as pw:
        try:
            nav = pw.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        except Exception as e:  # noqa: BLE001
            print('OK test_audio_navegador: OMITIDA (Chromium no arranca: %s)' % str(e).splitlines()[0])
            sys.exit(0)
        pg = nav.new_page()
        consola = []
        pg.on('console', lambda m: consola.append(m.type + ': ' + m.text) if m.type in ('error', 'warning') else None)
        pg.goto(url)
        assert pg.evaluate('listo') is True
        pg.wait_for_timeout(600)
        assert pg.locator('#ea5kao-filtro-button').count() == 1 and pg.locator('#ea5kao-dsp-button').count() == 1
        orden = pg.evaluate("$('.openwebrx-main-buttons .button').map(function(){return this.id}).get()")
        assert orden == ['ea5kao-solar-button', 'ea5kao-filtro-button', 'ea5kao-dsp-button'], orden

        sin = pg.evaluate('nivel(1000)')
        voz_sin = pg.evaluate('banda(300, 700)')
        assert sin > -40, 'sin filtro el 1 kHz debe oírse: %.1f dB' % sin
        # encender el filtro desde la interfaz (modo AM: 100–4500 Hz)
        pg.click('#ea5kao-filtro-button')
        pg.click('#ea5kao-filtro .bha-chip[data-k="am"]')
        pg.click('#ea5kao-filtro .bha-sw:has-text("Filtro activo")')
        pg.wait_for_timeout(2500)
        con = pg.evaluate('nivel(1000)')
        voz_con = pg.evaluate('banda(300, 700)')
        estado = pg.inner_text('#ea5kao-filtro')
        assert sin - con > 20, 'el notch automático debe quitar el 1 kHz: %.1f → %.1f dB · %s' % (sin, con, estado)
        assert abs(voz_con - voz_sin) < 4, 'la «voz» (300–700 Hz) tiene que seguir pasando: %.1f → %.1f dB' % (voz_sin, voz_con)
        assert 'quitando 99' in estado or 'quitando 100' in estado, estado
        assert pg.evaluate('nivelToma(1000)') > -40, 'otros plugins que cuelgan del audio (osciloscopio de rig_skin) siguen recibiéndolo'

        # DSP: encender y ver que los medidores se mueven
        pg.click('#ea5kao-dsp-button')
        pg.click('#ea5kao-dsp .bha-sw:has-text("DSP activo")')
        pg.wait_for_timeout(800)
        txt = pg.inner_text('#ea5kao-dsp')
        assert 'dBFS' in txt and 'compresión' in txt, txt
        ruta = pg.evaluate("Plugins.audio_cadena.reconectar()")
        assert ruta == ['filtro_audio', 'dsp_audio'], ruta

        # apagar todo: vuelve el audio original
        pg.click('#ea5kao-filtro .bha-sw:has-text("Filtro activo")')
        pg.click('#ea5kao-dsp .bha-sw:has-text("DSP activo")')
        pg.wait_for_timeout(800)
        assert pg.evaluate("Plugins.audio_cadena.reconectar()") == []
        otra = pg.evaluate('nivel(1000)')
        assert abs(otra - sin) < 3, 'apagado = audio original (%.1f vs %.1f)' % (otra, sin)
        # los ajustes se guardan en el navegador
        assert pg.evaluate("JSON.parse(localStorage.getItem('bh_filtro_audio')).modo") == 'am'
        if os.environ.get('CAPTURA'):
            pg.click('#ea5kao-filtro .bha-sw:has-text("Filtro activo")'); pg.click('#ea5kao-dsp .bha-sw:has-text("DSP activo")')
            pg.wait_for_timeout(1500)
            pg.screenshot(path=os.environ['CAPTURA'])
        errores = pg.evaluate('errores')
        assert not errores and not [c for c in consola if c.startswith('error')], (errores, consola)
        nav.close()
finally:
    s.shutdown()
    shutil.rmtree(d, ignore_errors=True)

print('OK test_audio_navegador: en Chromium real el notch automático quita un pitido de 1 kHz (%.0f dB), '
      'deja pasar la voz, el DSP mide y al apagar vuelve el audio original' % (sin - con))
