/*
 * dsp_audio: procesado de audio para el oyente de OpenWebRX+ (v4.2)
 *
 * Autor: EA5KAO · BricoHams · licencia MIT · necesita el plugin audio_cadena
 *
 * Botón «DSP» en la barra superior. En la ventana:
 *   - ECUALIZADOR de 3 bandas: graves (250 Hz), medios (1,2 kHz), agudos (3 kHz), ±12 dB
 *   - PUERTA DE RUIDO: baja el soplido entre frases (umbral en dBFS, 30 dB de atenuación)
 *   - AGC / COMPRESOR: iguala estaciones flojas y fuertes (suave, medio, fuerte) con ganancia de compensación
 *   - LIMITADOR final a −1 dBFS: nunca satura el altavoz
 *   - medidores de nivel de entrada y de reducción del compresor
 *   - preajustes: Plano · Voz clara (SSB) · AM radiodifusión · FM estrecha · DX débil
 * Va DESPUÉS de filtro_audio (orden 20). Solo cambia lo que oye ESTE oyente, en su navegador.
 * Ajustes guardados en el navegador (localStorage «bh_dsp_audio»).
 *
 * Opcional en init.js, antes de cargarlo:
 *   window.dsp_audio_config = { preajuste: 'voz', activo: false };
 */

Plugins.dsp_audio._version = '1.0.0';
Plugins.dsp_audio._author = 'EA5KAO';
Plugins.dsp_audio.no_css = true;

// ---------------------------------------------------------------------
//  lógica pura (la prueba tests/test_audio_plugins.py con node)
// ---------------------------------------------------------------------
Plugins.dsp_audio.util = (function () {
    var U = {};
    U.AGC = {
        no:     null,
        suave:  { umbral: -24, ratio: 3,  ataque: 0.010, suelta: 0.25, compensa: 4 },
        medio:  { umbral: -32, ratio: 6,  ataque: 0.005, suelta: 0.30, compensa: 8 },
        fuerte: { umbral: -42, ratio: 12, ataque: 0.003, suelta: 0.40, compensa: 13 }
    };
    U.PREAJUSTES = {
        plano: { nombre: 'Plano',          graves: 0,  medios: 0, agudos: 0,  puerta: false, umbral: -55, agc: 'no' },
        voz:   { nombre: 'Voz clara',      graves: -6, medios: 3, agudos: 4,  puerta: true,  umbral: -55, agc: 'medio' },
        am:    { nombre: 'AM radio',       graves: 3,  medios: 0, agudos: 2,  puerta: false, umbral: -60, agc: 'suave' },
        fm:    { nombre: 'FM estrecha',    graves: -3, medios: 1, agudos: 2,  puerta: true,  umbral: -50, agc: 'suave' },
        dx:    { nombre: 'DX débil',       graves: -8, medios: 5, agudos: 3,  puerta: false, umbral: -60, agc: 'fuerte' }
    };
    U.DEFECTO = $extend({ activo: false, preajuste: 'voz' }, U.PREAJUSTES.voz);
    delete U.DEFECTO.nombre;

    function $extend(a, b) { for (var k in b) if (Object.prototype.hasOwnProperty.call(b, k)) a[k] = b[k]; return a; }
    U.aplicarPreajuste = function (cfg, k) {
        var p = U.PREAJUSTES[k];
        if (!p) return cfg;
        var r = $extend({}, cfg);
        ['graves', 'medios', 'agudos', 'puerta', 'umbral', 'agc'].forEach(function (c) { r[c] = p[c]; });
        r.preajuste = k;
        return r;
    };

    // nivel RMS en dBFS de un bloque de muestras
    U.rmsDb = function (m) {
        var s = 0;
        for (var i = 0; i < m.length; i++) s += m[i] * m[i];
        return 10 * Math.log10(Math.max(s / Math.max(m.length, 1), 1e-12));
    };

    // Puerta con histéresis de 3 dB y «hold»: se abre por encima del umbral y se cierra cuando
    // lleva «hold» ms por debajo de (umbral − 3). Estado {abierta, ultima}. Devuelve el nuevo estado.
    U.puerta = function (est, nivelDb, umbral, ahora, hold) {
        var r = { abierta: est.abierta, ultima: est.ultima };
        if (nivelDb >= umbral) { r.abierta = true; r.ultima = ahora; }
        else if (nivelDb >= umbral - 3 && r.abierta) r.ultima = ahora;
        else if (r.abierta && ahora - r.ultima > (hold || 300)) r.abierta = false;
        return r;
    };
    return U;
})();

// ---------------------------------------------------------------------
//  plugin
// ---------------------------------------------------------------------
Plugins.dsp_audio.init = async function () {
    if (!Plugins.audio_cadena || !Plugins.audio_cadena.registrar) await Plugins.load('audio_cadena');
    var C = Plugins.audio_cadena, U = Plugins.dsp_audio.util;
    if (!C || !C.registrar) { console.error('dsp_audio: falta el plugin audio_cadena'); return false; }

    var CLAVE = 'bh_dsp_audio';
    var cfg = $.extend({}, U.DEFECTO, window.dsp_audio_config || {}, C.lsGet(CLAVE, {}));
    if (window.dsp_audio_config && window.dsp_audio_config.preajuste && !C.lsGet(CLAVE, null)) cfg = U.aplicarPreajuste(cfg, cfg.preajuste);
    function guardar() { C.lsSet(CLAVE, cfg); }

    var n = null, temporizador = null, gate = { abierta: true, ultima: 0 }, cableado = null, buf = null;

    C.registrar({
        id: 'dsp_audio', orden: 20, activa: cfg.activo,
        crear: function (ctx) {
            var bq = function (tipo, f, q) { var x = ctx.createBiquadFilter(); x.type = tipo; x.frequency.value = f; if (q) x.Q.value = q; return x; };
            var x = { graves: bq('lowshelf', 250), medios: bq('peaking', 1200, 0.9), agudos: bq('highshelf', 3000),
                      an: ctx.createAnalyser(), puerta: ctx.createGain(), comp: ctx.createDynamicsCompressor(),
                      compensa: ctx.createGain(), lim: ctx.createDynamicsCompressor() };
            x.an.fftSize = 1024;
            x.lim.threshold.value = -1; x.lim.knee.value = 0; x.lim.ratio.value = 20; x.lim.attack.value = 0.001; x.lim.release.value = 0.1;
            x.graves.connect(x.medios); x.medios.connect(x.agudos); x.agudos.connect(x.puerta);
            x.agudos.connect(x.an);                    // el medidor y la puerta miran antes de la puerta
            x.puerta.connect(x.comp); x.comp.connect(x.compensa); x.compensa.connect(x.lim);
            x.entrada = x.graves; x.salida = x.lim;
            return x;
        }
    }).then(function (e) { n = e.nodos; aplicar(); });

    function aplicar() {
        $btn.toggleClass('on', !!cfg.activo);
        $esperando.toggle(!n);
        if (!n) return;
        var t = C.contexto().currentTime;
        n.graves.gain.setTargetAtTime(+cfg.graves, t, 0.03);
        n.medios.gain.setTargetAtTime(+cfg.medios, t, 0.03);
        n.agudos.gain.setTargetAtTime(+cfg.agudos, t, 0.03);
        var a = U.AGC[cfg.agc];
        if (a) {
            n.comp.threshold.value = a.umbral; n.comp.ratio.value = a.ratio; n.comp.knee.value = 8;
            n.comp.attack.value = a.ataque; n.comp.release.value = a.suelta;
            n.compensa.gain.setTargetAtTime(C.lineal(a.compensa), t, 0.05);
        } else {
            n.comp.threshold.value = 0; n.comp.ratio.value = 1;
            n.compensa.gain.setTargetAtTime(1, t, 0.05);
        }
        if (!cfg.puerta) { gate.abierta = true; n.puerta.gain.setTargetAtTime(1, t, 0.01); }
        if (cableado !== !!cfg.activo) { cableado = !!cfg.activo; C.activar('dsp_audio', cableado); }
        vigilar();
    }

    function vigilar() {
        var hace = cfg.activo && n && (cfg.puerta || ventana.abierta());
        if (hace && !temporizador) temporizador = setInterval(paso, 50);
        if (!hace && temporizador) { clearInterval(temporizador); temporizador = null; }
    }
    function paso() {
        if (!n) return;
        if (!buf || buf.length !== n.an.fftSize) buf = new Float32Array(n.an.fftSize);
        n.an.getFloatTimeDomainData(buf);
        var nivel = U.rmsDb(buf), t = C.contexto().currentTime;
        if (cfg.puerta) {
            var antes = gate.abierta;
            gate = U.puerta(gate, nivel, +cfg.umbral, Date.now(), 300);
            if (gate.abierta !== antes) n.puerta.gain.setTargetAtTime(gate.abierta ? 1 : C.lineal(-30), t, gate.abierta ? 0.005 : 0.12);
        }
        if (ventana.abierta()) {
            $nivel.css('width', C.limitar((nivel + 80) / 80 * 100, 0, 100) + '%');
            $nivelTxt.text(Math.round(nivel) + ' dBFS' + (cfg.puerta ? (gate.abierta ? ' · puerta abierta' : ' · puerta cerrada') : ''));
            var red = typeof n.comp.reduction === 'number' ? n.comp.reduction : (n.comp.reduction && n.comp.reduction.value) || 0;
            $red.css('width', C.limitar(-red / 20 * 100, 0, 100) + '%');
            $redTxt.text(U.AGC[cfg.agc] ? Math.round(-red) + ' dB de compresión' : 'AGC apagado');
        }
    }

    // ---- interfaz -------------------------------------------------------
    var SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">' +
        '<path d="M5 4v16M12 4v16M19 4v16"/><rect x="3" y="13" width="4" height="3" rx="1"/><rect x="10" y="7" width="4" height="3" rx="1"/><rect x="17" y="11" width="4" height="3" rx="1"/></svg>';
    var ventana = C.ui.ventana('ea5kao-dsp', '🎛 DSP DE AUDIO', [820, 110]);
    var $btn = C.ui.boton('ea5kao-dsp-button', 'DSP', SVG, 'Ecualizador, puerta de ruido y AGC (solo en tu navegador)',
                          function () { ventana.abrir(!ventana.abierta()); });
    ventana.alCambiar = function () { vigilar(); };
    var $c = ventana.$cuerpo;

    var $esperando = $('<div class="bha-espera">El audio aún no ha empezado: pulsa en la página para oírlo.</div>');
    var sw = C.ui.interruptor('DSP activo', cfg.activo, function (v) { cfg.activo = v; guardar(); aplicar(); });
    var chips = C.ui.chips(Object.keys(U.PREAJUSTES).map(function (k) { return [k, U.PREAJUSTES[k].nombre]; }), cfg.preajuste,
                           function (k) { cfg = U.aplicarPreajuste(cfg, k); guardar(); refrescar(); aplicar(); });
    $('<div class="bha-sec"></div>').append(sw.$el, $esperando, $('<div style="margin-top:6px"></div>').append(chips.$el)).appendTo($c);

    var dbf = function (v) { return (v > 0 ? '+' : '') + v + ' dB'; };
    var manual = function () { cfg.preajuste = ''; chips.poner(''); guardar(); aplicar(); };
    var sG = C.ui.deslizador('Graves 250', -12, 12, 1, cfg.graves, dbf, function (v) { cfg.graves = v; manual(); });
    var sM = C.ui.deslizador('Medios 1k2', -12, 12, 1, cfg.medios, dbf, function (v) { cfg.medios = v; manual(); });
    var sA = C.ui.deslizador('Agudos 3k', -12, 12, 1, cfg.agudos, dbf, function (v) { cfg.agudos = v; manual(); });
    $('<div class="bha-sec"><h4>ECUALIZADOR</h4></div>').append(sG.$el, sM.$el, sA.$el).appendTo($c);

    var swP = C.ui.interruptor('Puerta de ruido', cfg.puerta, function (v) { cfg.puerta = v; manual(); sU.habilitar(v); });
    var sU = C.ui.deslizador('Umbral', -80, -20, 1, cfg.umbral, function (v) { return v + ' dBFS'; }, function (v) { cfg.umbral = v; manual(); });
    var agc = C.ui.chips([['no', 'Sin AGC'], ['suave', 'Suave'], ['medio', 'Medio'], ['fuerte', 'Fuerte']], cfg.agc,
                         function (k) { cfg.agc = k; manual(); });
    $('<div class="bha-sec"><h4>PUERTA DE RUIDO Y AGC</h4></div>').append($('<div class="bha-row"></div>').append(swP.$el), sU.$el,
        $('<div class="bha-row"><label>AGC</label></div>').append(agc.$el)).appendTo($c);

    var barra = function () { return $('<div style="flex:1;height:8px;background:#0b0d10;border-radius:4px;overflow:hidden"><div style="height:100%;width:0;background:#39d353"></div></div>'); };
    var $bN = barra(), $bR = barra();
    var $nivel = $bN.children(), $red = $bR.children().css('background', '#f26b21');
    var $nivelTxt = $('<div class="bha-nota"></div>'), $redTxt = $('<div class="bha-nota"></div>');
    $('<div class="bha-sec"><h4>MEDIDORES</h4></div>').append($('<div class="bha-row"><label>Entrada</label></div>').append($bN), $nivelTxt,
        $('<div class="bha-row"><label>Compresión</label></div>').append($bR), $redTxt,
        '<div class="bha-nota">Solo cambia lo que oyes tú. La grabación (REC) y los decodificadores usan el audio original.</div>').appendTo($c);

    function refrescar() {
        sG.poner(cfg.graves); sM.poner(cfg.medios); sA.poner(cfg.agudos);
        swP.poner(cfg.puerta); sU.poner(cfg.umbral); sU.habilitar(cfg.puerta); agc.poner(cfg.agc); chips.poner(cfg.preajuste);
    }
    refrescar();
    aplicar();
    return true;
};
