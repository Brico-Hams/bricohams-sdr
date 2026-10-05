#!/usr/bin/env python3
"""v4.2 · Plugins de audio (audio_cadena, filtro_audio, dsp_audio) con node:
  - la cadena se mete entre audioNode y gainNode de OpenWebRX+, en orden, y se puede quitar;
  - el notch automático encuentra un pitido de 1 kHz en un espectro real (FFT de numpy si
    está, si no uno sintético) y no salta con ruido ni con voz;
  - el seguimiento necesita dos detecciones y suelta a los 2 s;
  - los cortes de cada modo, los preajustes del DSP y la puerta con histéresis."""
import json
import os
import shutil
import subprocess
import sys

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
R = os.path.join(RAIZ, 'files/htdocs/plugins/receiver')
if not shutil.which('node'):
    print('OK test_audio_plugins: OMITIDA (no hay node)')
    sys.exit(0)

JS = r'''
const vm = require('vm'), fs = require('fs'), assert = require('assert');
const ctx = { console, Math, Date, Float32Array, Promise, setTimeout: (f) => f(), JSON,
              window: { localStorage: { _d: {}, getItem(k) { return k in this._d ? this._d[k] : null; }, setItem(k, v) { this._d[k] = v; } } },
              Plugins: { audio_cadena: {}, filtro_audio: {}, dsp_audio: {} } };
ctx.window.window = ctx.window;
vm.createContext(ctx);
for (const p of ['audio_cadena', 'filtro_audio', 'dsp_audio'])
    vm.runInContext(fs.readFileSync(process.argv[2] + '/' + p + '/' + p + '.js', 'utf8'), ctx, { filename: p });
// objetos de otro «realm» (vm): se comparan por su JSON
const eq = (a, b, m) => assert.strictEqual(JSON.stringify(a), JSON.stringify(b), m);
const C = ctx.Plugins.audio_cadena, F = ctx.Plugins.filtro_audio.util, D = ctx.Plugins.dsp_audio.util;

// ---------------- cadena con nodos falsos que apuntan las conexiones
let log = [];
const nodo = (n) => ({ n, sal: new Set(),
    connect(o) { log.push(n + '>' + o.n); this.sal.add(o); },
    disconnect(o) { if (o) { if (!this.sal.has(o)) throw new Error('no conectado'); this.sal.delete(o); log.push(n + ' x ' + o.n); }
                    else { this.sal.clear(); log.push(n + ' x'); } } });
const fuente = nodo('worklet'), dest = nodo('volumen');
const e1 = { id: 'filtro', orden: 10, activa: true, entrada: nodo('f.in'), salida: nodo('f.out') };
const e2 = { id: 'dsp', orden: 20, activa: true, entrada: nodo('d.in'), salida: nodo('d.out') };
eq(C.conectar(fuente, [e2, e1], dest), ['filtro', 'dsp']);
eq(log.filter(x => x.includes('>')), ['worklet>f.in', 'f.out>d.in', 'd.out>volumen']);
log = []; e1.activa = false;
eq(C.conectar(fuente, [e1, e2], dest), ['dsp']);
eq(log.filter(x => x.includes('>')), ['worklet>d.in', 'd.out>volumen']);
log = []; e2.activa = false;
C.conectar(fuente, [e1, e2], dest);
eq(log.filter(x => x.includes('>')), ['worklet>volumen'], 'todo apagado = audio original');

// ---------------- registrar + arranque del audio (AudioEngine falso de OpenWebRX+)
log = [];
const fakeCtx = { sampleRate: 48000, currentTime: 0 };
let arrancar = null;
const wk = nodo('worklet'), vol = nodo('volumen'), osc = nodo('osciloscopio');
wk.connect(vol); wk.connect(osc);           // como OpenWebRX+ (volumen) y rig_skin (su analizador)
ctx.window.audioEngine = { audioNode: wk, gainNode: vol, audioContext: fakeCtx,
                           onStart(cb) { arrancar = cb; } };
let creado = 0;
const pr = C.registrar({ id: 'x', orden: 10, activa: true, crear(c) { creado++; assert.strictEqual(c, fakeCtx); return { entrada: nodo('x.in'), salida: nodo('x.out') }; } });
assert.strictEqual(creado, 0, 'no crea nodos antes de que el oyente active el audio');
arrancar();
assert.strictEqual(creado, 1);
assert.ok(log.includes('worklet>x.in') && log.includes('x.out>volumen'), log.join(' '));
assert.ok(wk.sal.has(osc) && !wk.sal.has(vol), 'la toma del osciloscopio sigue; la directa al volumen se quita');
log = [];
eq(C.activar('x', false), []);
assert.ok(log.includes('worklet>volumen'));
assert.ok(wk.sal.has(osc) && wk.sal.has(vol) && wk.sal.size === 2, 'apagado: worklet → volumen y osciloscopio');
eq(C.activar('x', true), ['x']);
eq(C.activar('x', true), ['x']);
assert.ok(wk.sal.has(osc) && wk.sal.size === 2, 'recablear varias veces no deja conexiones de más ni quita la ajena');

// ---------------- filtro: cortes
eq(F.cortes({ modo: 'voz' }, 12000), { bajo: 300, alto: 2700 });
eq(F.cortes({ modo: 'cw', cwTono: 700, cwAncho: 200 }, 48000), { bajo: 600, alto: 800 });
eq(F.cortes({ modo: 'fm' }, 12000), { bajo: 50, alto: 5700 }, 'no pasa de 0,95·Nyquist');
const lib = F.cortes({ modo: 'libre', bajo: 2000, alto: 1000 }, 48000);
assert.ok(lib.alto >= lib.bajo + 50, 'corte alto siempre por encima del bajo');
eq(F.cortes({ modo: 'raro' }, 48000), { bajo: 300, alto: 2700 });

// ---------------- notch automático sobre espectros (dB por bin) que manda python
const E = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const hzBin = 48000 / 4096;
const t = F.buscarTono(E.tono, hzBin, 150, 4000, 25, 120);
assert.ok(t !== null && Math.abs(t - 1000) < hzBin / 2, 'pitido de 1000 Hz: ' + t);
assert.strictEqual(F.buscarTono(E.ruido, hzBin, 150, 4000, 25, 120), null, 'ruido: sin falso pitido');
assert.strictEqual(F.buscarTono(E.voz, hzBin, 150, 4000, 25, 120), null, 'voz (banda ancha): no la toma por pitido');
assert.strictEqual(F.buscarTono(E.tono, hzBin, 1500, 4000, 25, 120), null, 'fuera del margen');

let s = { hz: null, candidato: null, visto: 0 };
s = F.seguir(s, 1000, 0); assert.strictEqual(s.hz, null, 'una sola detección no basta');
s = F.seguir(s, 1010, 200); assert.strictEqual(s.hz, 1010);
s = F.seguir(s, 1500, 400); assert.strictEqual(s.hz, 1010, 'un salto aislado no lo mueve');
s = F.seguir(s, null, 1500); assert.strictEqual(s.hz, 1010, 'aguanta sin tono');
s = F.seguir(s, null, 2300); assert.strictEqual(s.hz, null, 'a los 2 s sin tono se quita');

// ---------------- DSP
assert.ok(D.PREAJUSTES.voz && D.PREAJUSTES.plano && D.AGC.medio && D.AGC.no === null);
const v = D.aplicarPreajuste({ activo: true, graves: 9 }, 'am');
assert.strictEqual(v.activo, true); assert.strictEqual(v.graves, 3); assert.strictEqual(v.agc, 'suave'); assert.strictEqual(v.preajuste, 'am');
assert.ok(D.DEFECTO.nombre === undefined && D.DEFECTO.preajuste === 'voz' && D.DEFECTO.activo === false);
const seno = new Float32Array(480).map((_, i) => 0.5 * Math.sin(2 * Math.PI * i / 48));
assert.ok(Math.abs(D.rmsDb(seno) - (20 * Math.log10(0.5 / Math.SQRT2))) < 0.1);
let g = { abierta: true, ultima: 0 };
g = D.puerta(g, -70, -55, 100, 300); assert.strictEqual(g.abierta, true, 'hold: no cierra al instante');
g = D.puerta(g, -70, -55, 500, 300); assert.strictEqual(g.abierta, false, 'cierra tras el hold');
g = D.puerta(g, -56, -55, 600, 300); assert.strictEqual(g.abierta, false, 'histéresis: no abre por debajo del umbral');
g = D.puerta(g, -40, -55, 700, 300); assert.strictEqual(g.abierta, true);
g = D.puerta(g, -57, -55, 1500, 300); assert.strictEqual(g.abierta, true, 'dentro de los 3 dB de histéresis sigue abierta');
console.log('ok');
'''


def espectros():
    """Espectros en dB (4096 puntos a 48 kHz) de: tono 1 kHz + ruido, solo ruido, voz sintética."""
    try:
        import numpy as np
        rng = np.random.default_rng(1)
        fs, n = 48000, 4096
        t = np.arange(n) / fs
        w = np.blackman(n)

        def db(x):
            return (20 * np.log10(np.abs(np.fft.rfft(x * w))[:n // 2] / n + 1e-9)).tolist()
        ruido = 0.02 * rng.standard_normal(n)
        tono = ruido + 0.3 * np.sin(2 * np.pi * 1000 * t)
        voz = ruido + sum(0.05 * np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * (1 + 0.5 * np.sin(2 * np.pi * 3 * t))
                          for f in np.arange(200, 3000, 37.0)) + 0.03 * rng.standard_normal(n)
        return {'tono': db(tono), 'ruido': db(ruido), 'voz': db(voz)}
    except ImportError:
        import random
        random.seed(1)
        base = [-90 + random.uniform(-3, 3) for _ in range(2048)]
        tono = list(base)
        k = 1000 / (48000 / 4096)
        for i in range(2048):
            tono[i] = max(tono[i], -30 - 12 * (i - k) ** 2)
        voz = [-55 + random.uniform(-6, 6) if 17 <= i <= 256 else b for i, b in enumerate(base)]
        return {'tono': tono, 'ruido': base, 'voz': voz}


import tempfile  # noqa: E402
d = tempfile.mkdtemp()
open(os.path.join(d, 'prueba.js'), 'w').write(JS)
json.dump(espectros(), open(os.path.join(d, 'espectros.json'), 'w'))
r = subprocess.run(['node', os.path.join(d, 'prueba.js'), R, os.path.join(d, 'espectros.json')], capture_output=True, text=True)
shutil.rmtree(d)
assert r.returncode == 0 and r.stdout.strip() == 'ok', (r.stdout, r.stderr)
init = open(os.path.join(R, 'init.js'), encoding='utf-8').read()
assert "'audio_cadena', 'filtro_audio', 'dsp_audio'" in init, 'init.js debe cargar audio_cadena antes que los otros dos'
print('OK test_audio_plugins: cadena entre audioNode y volumen, notch automático (1 kHz sí; ruido y voz no), '
      'cortes por modo, preajustes, puerta con histéresis')
