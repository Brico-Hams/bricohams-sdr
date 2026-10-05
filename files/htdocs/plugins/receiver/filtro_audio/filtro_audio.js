/*
 * filtro_audio: filtro de audio para el oyente de OpenWebRX+ (v4.2)
 *
 * Autor: EA5KAO · BricoHams · licencia MIT · necesita el plugin audio_cadena
 *
 * Botón «FILTRO» en la barra superior. En la ventana:
 *   - PASO BANDA de 24 dB/octava (2 pasa-altos + 2 pasa-bajos) con modos:
 *       Voz SSB 300–2700 Hz · AM 100–4500 · CW (tono y ancho) · Digital 200–3000 · FM 50–6000 · Libre
 *   - NOTCH MANUAL: quita un pitido fijo (frecuencia y estrechez)
 *   - NOTCH AUTOMÁTICO: busca el tono más fuerte y estrecho (portadora, heterodino)
 *     y lo sigue; si desaparece 2 s, se quita solo
 *   - espectro del audio de 0 a 4 kHz con la zona que pasa
 * Solo cambia lo que oye ESTE oyente, en su navegador. No toca la Pi ni los decodificadores.
 * Ajustes guardados en el navegador (localStorage «bh_filtro_audio»).
 *
 * Opcional en init.js, antes de cargarlo:
 *   window.filtro_audio_config = { modo: 'voz', activo: false };
 */

Plugins.filtro_audio._version = '1.0.0';
Plugins.filtro_audio._author = 'EA5KAO';
Plugins.filtro_audio.no_css = true;

// ---------------------------------------------------------------------
//  lógica pura (la prueba tests/test_audio_plugins.py con node)
// ---------------------------------------------------------------------
Plugins.filtro_audio.util = (function () {
    var U = {};
    U.MODOS = {
        voz:     { nombre: 'Voz SSB', bajo: 300, alto: 2700, ayuda: 'banda lateral: corta graves y siseo' },
        am:      { nombre: 'AM',      bajo: 100, alto: 4500, ayuda: 'radiodifusión en onda media/corta' },
        cw:      { nombre: 'CW',      bajo: 0,   alto: 0,    ayuda: 'telegrafía: estrecho alrededor del tono' },
        digital: { nombre: 'Digital', bajo: 200, alto: 3000, ayuda: 'escuchar FT8, RTTY, PSK… (solo el oído)' },
        fm:      { nombre: 'FM',      bajo: 50,  alto: 6000, ayuda: 'FM estrecha: quita zumbido y siseo alto' },
        libre:   { nombre: 'Libre',   bajo: 0,   alto: 0,    ayuda: 'tú eliges los dos cortes' }
    };
    U.DEFECTO = { activo: false, modo: 'voz', bajo: 300, alto: 2700, cwTono: 700, cwAncho: 250,
                  notch: false, notchHz: 1000, notchQ: 18, auto: true };

    // cortes efectivos {bajo, alto} en Hz, dentro de lo que permite la frecuencia de muestreo
    U.cortes = function (cfg, fs) {
        var nyq = (fs || 48000) / 2, b, a, m = U.MODOS[cfg.modo] ? cfg.modo : 'voz';
        if (m === 'cw') {
            var t = Math.min(Math.max(+cfg.cwTono || 700, 300), 1500), w = Math.min(Math.max(+cfg.cwAncho || 250, 50), 1000);
            b = t - w / 2; a = t + w / 2;
        } else if (m === 'libre') { b = +cfg.bajo; a = +cfg.alto; }
        else { b = U.MODOS[m].bajo; a = U.MODOS[m].alto; }
        b = Math.min(Math.max(b || 20, 20), nyq * 0.9);
        a = Math.min(Math.max(a || nyq * 0.9, b + 50), nyq * 0.95);
        return { bajo: Math.round(b), alto: Math.round(a) };
    };

    U.mediana = function (v) {
        var s = v.slice().sort(function (x, y) { return x - y; }), n = s.length;
        return n ? (n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2) : -Infinity;
    };

    // Tono a quitar: el pico más alto entre fmin y fmax que sobresale «umbral» dB de la mediana
    // y es estrecho (menos de «anchoMax» Hz a −6 dB). Devuelve Hz (interpolación parabólica) o null.
    U.buscarTono = function (db, hzBin, fmin, fmax, umbral, anchoMax) {
        var i0 = Math.max(1, Math.ceil(fmin / hzBin)), i1 = Math.min(db.length - 2, Math.floor(fmax / hzBin));
        if (i1 <= i0) return null;
        var tramo = Array.prototype.slice.call(db, i0, i1 + 1), med = U.mediana(tramo), im = i0;
        for (var i = i0; i <= i1; i++) if (db[i] > db[im]) im = i;
        if (!(db[im] - med >= (umbral || 25))) return null;
        var lim = db[im] - 6, izq = im, der = im;
        while (izq > i0 && db[izq - 1] > lim) izq--;
        while (der < i1 && db[der + 1] > lim) der++;
        if ((der - izq + 1) * hzBin > (anchoMax || 120)) return null;
        var a = db[im - 1], b = db[im], c = db[im + 1], den = a - 2 * b + c;
        var off = den !== 0 ? 0.5 * (a - c) / den : 0;
        return (im + Math.max(-0.5, Math.min(0.5, off))) * hzBin;
    };

    // Seguimiento del notch automático: necesita 2 detecciones seguidas a ±30 Hz para moverse
    // y lo quita tras «suelta» ms sin tono. Estado: {hz, candidato, visto}. Devuelve el nuevo estado.
    U.seguir = function (est, tono, ahora, suelta) {
        est = { hz: est.hz, candidato: est.candidato, visto: est.visto };
        if (tono !== null) {
            if (est.hz !== null && Math.abs(tono - est.hz) <= 30) { est.hz = tono; est.visto = ahora; }
            else if (est.candidato !== null && Math.abs(tono - est.candidato) <= 30) { est.hz = tono; est.candidato = null; est.visto = ahora; }
            else est.candidato = tono;
        } else {
            est.candidato = null;
            if (est.hz !== null && ahora - est.visto > (suelta || 2000)) est.hz = null;
        }
        return est;
    };
    return U;
})();

// ---------------------------------------------------------------------
//  plugin
// ---------------------------------------------------------------------
Plugins.filtro_audio.init = async function () {
    if (!Plugins.audio_cadena || !Plugins.audio_cadena.registrar) await Plugins.load('audio_cadena');
    var C = Plugins.audio_cadena, U = Plugins.filtro_audio.util;
    if (!C || !C.registrar) { console.error('filtro_audio: falta el plugin audio_cadena'); return false; }

    var CLAVE = 'bh_filtro_audio';
    var cfg = $.extend({}, U.DEFECTO, window.filtro_audio_config || {}, C.lsGet(CLAVE, {}));
    function guardar() { C.lsSet(CLAVE, cfg); }

    var n = null, auto = { hz: null, candidato: null, visto: 0 }, temporizador = null, cableado = null;

    // ---- nodos ----------------------------------------------------------
    C.registrar({
        id: 'filtro_audio', orden: 10, activa: cfg.activo,
        crear: function (ctx) {
            // En Web Audio la Q de lowpass/highpass va en dB: −3,01 dB = 0,7071 lineal = Butterworth (sin pico en el corte)
            var mk = function (tipo) { var f = ctx.createBiquadFilter(); f.type = tipo; f.Q.value = (tipo === 'highpass' || tipo === 'lowpass') ? -3.0103 : 0.7071; return f; };
            var x = { hp1: mk('highpass'), hp2: mk('highpass'), lp1: mk('lowpass'), lp2: mk('lowpass'),
                      notch: mk('allpass'), autoNotch: mk('allpass'), an: ctx.createAnalyser(), fs: ctx.sampleRate };
            x.an.fftSize = 4096; x.an.smoothingTimeConstant = 0.5;
            x.hp1.connect(x.hp2); x.hp2.connect(x.lp1); x.lp1.connect(x.lp2);
            x.lp2.connect(x.notch); x.notch.connect(x.autoNotch);
            x.lp2.connect(x.an);                              // el analizador mira antes de los notch
            x.entrada = x.hp1; x.salida = x.autoNotch;
            return x;
        }
    }).then(function (e) { n = e.nodos; aplicar(); });

    function aplicar() {
        $btn.toggleClass('on', !!cfg.activo);
        pintarEstado();
        if (!n) return;
        var t = C.contexto().currentTime, c = U.cortes(cfg, n.fs);
        [n.hp1, n.hp2].forEach(function (f) { f.frequency.setTargetAtTime(c.bajo, t, 0.02); });
        [n.lp1, n.lp2].forEach(function (f) { f.frequency.setTargetAtTime(c.alto, t, 0.02); });
        n.notch.type = cfg.notch ? 'notch' : 'allpass';
        n.notch.frequency.setTargetAtTime(+cfg.notchHz, t, 0.02);
        n.notch.Q.value = +cfg.notchQ;
        if (!cfg.auto) { auto.hz = null; n.autoNotch.type = 'allpass'; }
        if (cableado !== !!cfg.activo) { cableado = !!cfg.activo; C.activar('filtro_audio', cableado); }   // recablear solo al encender/apagar
        vigilar();
    }

    // notch automático + dibujo del espectro (solo con el filtro activo)
    function vigilar() {
        var hace = cfg.activo && n && (cfg.auto || ventana.abierta());
        if (hace && !temporizador) temporizador = setInterval(paso, 200);
        if (!hace && temporizador) { clearInterval(temporizador); temporizador = null; }
    }
    var buf = null;
    function paso() {
        if (!n) return;
        if (!buf || buf.length !== n.an.frequencyBinCount) buf = new Float32Array(n.an.frequencyBinCount);
        n.an.getFloatFrequencyData(buf);
        var hzBin = n.fs / n.an.fftSize, c = U.cortes(cfg, n.fs);
        if (cfg.auto) {
            var tono = U.buscarTono(buf, hzBin, Math.max(150, c.bajo), Math.min(4000, c.alto), 25, 120);
            auto = U.seguir(auto, tono, Date.now(), 2000);
            if (auto.hz !== null) { n.autoNotch.type = 'notch'; n.autoNotch.Q.value = 25; n.autoNotch.frequency.setTargetAtTime(auto.hz, C.contexto().currentTime, 0.01); }
            else n.autoNotch.type = 'allpass';
            $estadoAuto.text(auto.hz !== null ? 'quitando ' + Math.round(auto.hz) + ' Hz' : 'sin pitidos');
        }
        if (ventana.abierta()) dibujar(buf, hzBin, c);
    }

    // ---- interfaz -------------------------------------------------------
    var SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">' +
        '<path d="M2 18h4l3-12h6l3 12h4"/><path d="M12 3v3" opacity=".5"/></svg>';
    var ventana = C.ui.ventana('ea5kao-filtro', '🎚 FILTRO DE AUDIO', [460, 110]);
    var $btn = C.ui.boton('ea5kao-filtro-button', 'FILTRO', SVG, 'Filtro de audio: paso banda y notch (solo en tu navegador)',
                          function () { ventana.abrir(!ventana.abierta()); });
    ventana.alCambiar = function () { vigilar(); };
    var $c = ventana.$cuerpo;

    var $esperando = $('<div class="bha-espera">El audio aún no ha empezado: pulsa en la página para oírlo.</div>');
    var sw = C.ui.interruptor('Filtro activo', cfg.activo, function (v) { cfg.activo = v; guardar(); aplicar(); });
    $('<div class="bha-sec"></div>').append(sw.$el, $esperando).appendTo($c);

    var $sec1 = $('<div class="bha-sec"><h4>PASO BANDA</h4></div>').appendTo($c);
    var chips = C.ui.chips(Object.keys(U.MODOS).map(function (k) { return [k, U.MODOS[k].nombre, U.MODOS[k].ayuda]; }), cfg.modo,
                           function (k) { cfg.modo = k; guardar(); controles(); aplicar(); });
    var hz = function (v) { return v + ' Hz'; };
    var sBajo = C.ui.deslizador('Corte bajo', 20, 1500, 10, cfg.bajo, hz, function (v) { cfg.bajo = v; guardar(); aplicar(); });
    var sAlto = C.ui.deslizador('Corte alto', 1000, 8000, 50, cfg.alto, hz, function (v) { cfg.alto = v; guardar(); aplicar(); });
    var sTono = C.ui.deslizador('Tono CW', 300, 1500, 10, cfg.cwTono, hz, function (v) { cfg.cwTono = v; guardar(); aplicar(); });
    var sAncho = C.ui.deslizador('Ancho CW', 50, 1000, 10, cfg.cwAncho, hz, function (v) { cfg.cwAncho = v; guardar(); aplicar(); });
    var $cortes = $('<div class="bha-nota"></div>');
    $sec1.append(chips.$el, sBajo.$el, sAlto.$el, sTono.$el, sAncho.$el, $cortes);

    var $sec2 = $('<div class="bha-sec"><h4>NOTCH (QUITAR PITIDOS)</h4></div>').appendTo($c);
    var swAuto = C.ui.interruptor('Automático', cfg.auto, function (v) { cfg.auto = v; guardar(); aplicar(); });
    var $estadoAuto = $('<span class="bha-nota" style="margin-left:8px"></span>');
    var swN = C.ui.interruptor('Manual', cfg.notch, function (v) { cfg.notch = v; guardar(); controles(); aplicar(); });
    var sN = C.ui.deslizador('Frecuencia', 100, 4000, 5, cfg.notchHz, hz, function (v) { cfg.notchHz = v; guardar(); aplicar(); });
    var sQ = C.ui.deslizador('Estrechez', 3, 40, 1, cfg.notchQ, function (v) { return 'Q ' + v; }, function (v) { cfg.notchQ = v; guardar(); aplicar(); });
    $sec2.append($('<div class="bha-row"></div>').append(swAuto.$el, $estadoAuto), $('<div class="bha-row"></div>').append(swN.$el), sN.$el, sQ.$el);

    var $cv = $('<canvas width="320" height="70" style="width:100%;height:70px;background:#0b0d10;border-radius:4px"></canvas>');
    $('<div class="bha-sec"><h4>ESPECTRO DEL AUDIO 0–4 kHz</h4></div>').append($cv,
        '<div class="bha-nota">Solo cambia lo que oyes tú. La grabación (REC) y los decodificadores usan el audio original.</div>').appendTo($c);

    function controles() {
        var libre = cfg.modo === 'libre', cw = cfg.modo === 'cw';
        sBajo.$el.toggle(libre); sAlto.$el.toggle(libre); sTono.$el.toggle(cw); sAncho.$el.toggle(cw);
        sN.habilitar(cfg.notch); sQ.habilitar(cfg.notch);
        pintarEstado();
    }
    function pintarEstado() {
        var c = U.cortes(cfg, n ? n.fs : 48000);
        $cortes.text('Pasa de ' + c.bajo + ' a ' + c.alto + ' Hz');
        $esperando.toggle(!n);
    }
    function dibujar(db, hzBin, c) {
        var g = $cv[0].getContext('2d'), W = $cv[0].width, H = $cv[0].height, fmax = 4000;
        g.clearRect(0, 0, W, H);
        g.fillStyle = 'rgba(242,107,33,.15)';
        g.fillRect(c.bajo / fmax * W, 0, (Math.min(c.alto, fmax) - c.bajo) / fmax * W, H);
        g.strokeStyle = '#39d353'; g.beginPath();
        for (var x = 0; x < W; x++) {
            var v = db[Math.min(db.length - 1, Math.round(x / W * fmax / hzBin))];
            var y = H - (Math.max(-110, Math.min(-20, v)) + 110) / 90 * H;
            if (x) g.lineTo(x, y); else g.moveTo(x, y);
        }
        g.stroke();
        [[cfg.notch && cfg.notchHz, '#ffb74d'], [auto.hz, '#ff5252']].forEach(function (m) {
            if (!m[0]) return;
            g.strokeStyle = m[1]; g.beginPath(); g.moveTo(m[0] / fmax * W, 0); g.lineTo(m[0] / fmax * W, H); g.stroke();
        });
    }
    controles();
    aplicar();
    return true;
};
