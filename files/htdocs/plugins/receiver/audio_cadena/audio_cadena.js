/*
 * audio_cadena: base común de los plugins de audio de BricoHams (v4.2)
 *
 * Autor: BricoHams · licencia MIT
 *
 * OpenWebRX+ reproduce el audio así (htdocs/lib/AudioEngine.js):
 *     audioNode (AudioWorklet o ScriptProcessor) → gainNode (volumen) → altavoz
 * Este plugin mete, entre los dos, las «etapas» que registren otros plugins
 * (filtro_audio, dsp_audio…), en orden y sin que se pisen:
 *     audioNode → [etapa orden 10] → [etapa orden 20] → … → gainNode → altavoz
 *
 * Todo pasa en el NAVEGADOR de cada oyente (Web Audio API):
 *   - no carga la Raspberry ni cambia lo que oyen los demás;
 *   - no toca los decodificadores (FT8, DMR, APRS…), que trabajan en el servidor;
 *   - la grabación (botón REC) sigue guardando el audio original, sin procesar.
 *
 * API para otros plugins:
 *   Plugins.audio_cadena.registrar({id, orden, activa, crear(ctx) -> {entrada, salida}})
 *       → Promise que se cumple cuando el audio arranca (tras el primer clic del oyente)
 *   Plugins.audio_cadena.activar(id, true|false)
 *   Plugins.audio_cadena.ui.{boton, ventana, deslizador, chips, interruptor}
 *   Plugins.audio_cadena.lsGet(clave, defecto) / lsSet(clave, valor)   (localStorage seguro)
 */

Plugins.audio_cadena._version = '1.0.0';
Plugins.audio_cadena._author='BricoHams';
Plugins.audio_cadena.no_css = true;

(function (P) {
    // -----------------------------------------------------------------
    //  lógica pura (sin DOM ni Web Audio: la prueba tests/test_audio_plugins.py)
    // -----------------------------------------------------------------
    P.limitar = function (v, min, max) { v = +v; if (isNaN(v)) v = min; return Math.min(max, Math.max(min, v)); };
    P.db = function (v) { return 20 * Math.log10(Math.max(Math.abs(v), 1e-9)); };
    P.lineal = function (db) { return Math.pow(10, db / 20); };

    // Vuelve a cablear: fuente → etapas activas (por «orden») → destino. Devuelve los id en orden
    // (y en ruta.primero, el nodo al que queda conectada la fuente).
    // De la fuente solo se quita NUESTRA conexión («antes»): otros plugins también cuelgan de ella
    // (p. ej. el osciloscopio de rig_skin) y un disconnect() sin argumento los dejaría sin señal.
    P.conectar = function (fuente, etapas, destino, antes) {
        try { fuente.disconnect(antes || destino); } catch (e) { /* no estaba conectada */ }
        etapas.forEach(function (e) { try { if (e.salida) e.salida.disconnect(); } catch (x) { /* idem */ } });
        var prev = fuente, ruta = [], primero = null;
        etapas.filter(function (e) { return e.activa && e.entrada && e.salida; })
              .sort(function (a, b) { return a.orden - b.orden; })
              .forEach(function (e) { prev.connect(e.entrada); if (!primero) primero = e.entrada; prev = e.salida; ruta.push(e.id); });
        prev.connect(destino);
        ruta.primero = primero || destino;
        return ruta;
    };

    P.lsGet = function (k, defecto) {
        try { var v = window.localStorage.getItem(k); return v === null ? defecto : JSON.parse(v); }
        catch (e) { return defecto; }
    };
    P.lsSet = function (k, v) { try { window.localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* modo privado */ } };

    // -----------------------------------------------------------------
    //  motor
    // -----------------------------------------------------------------
    var etapas = [], ae = null, ctx = null, esperando = false, conectadoA = null;
    P.etapas = etapas;
    P.contexto = function () { return ctx; };

    function crearEtapa(e) {
        if (e.entrada || !ctx) return;
        try {
            var n = e.crear(ctx);
            e.entrada = n.entrada; e.salida = n.salida; e.nodos = n;
        } catch (x) { console.warn('audio_cadena: no pude crear la etapa ' + e.id, x); }
        if (e._listo) e._listo(e);
    }

    P.reconectar = function () {
        if (!ae || !ae.audioNode || !ae.gainNode) return [];
        try { var r = P.conectar(ae.audioNode, etapas, ae.gainNode, conectadoA); conectadoA = r.primero; return r; }
        catch (x) { console.warn('audio_cadena: error al conectar; vuelvo al audio directo', x);
                    try { if (conectadoA) ae.audioNode.disconnect(conectadoA); } catch (y) { /* no estaba */ }
                    try { ae.audioNode.connect(ae.gainNode); conectadoA = ae.gainNode; } catch (y) { /* nada más que hacer */ }
                    return []; }
    };

    P.registrar = function (def) {
        var e = { id: def.id, orden: def.orden || 50, activa: def.activa !== false, crear: def.crear };
        etapas.push(e);
        var p = new Promise(function (resolve) { e._listo = resolve; });
        if (ctx) { crearEtapa(e); P.reconectar(); } else esperarMotor();
        return p;
    };

    P.activar = function (id, on) {
        etapas.forEach(function (e) { if (e.id === id) e.activa = !!on; });
        return P.reconectar();
    };

    function esperarMotor() {
        if (esperando) return;
        esperando = true;
        (function mirar() {
            var a = window.audioEngine;
            if (!a || typeof a.onStart !== 'function') { setTimeout(mirar, 500); return; }
            ae = a;
            ae.onStart(function () {
                ctx = ae.audioContext;
                etapas.forEach(crearEtapa);
                P.reconectar();
            });
        })();
    }

    // -----------------------------------------------------------------
    //  interfaz común: botón del panel de plugins, ventana nativa y controles
    // -----------------------------------------------------------------
    var CSS =
        '.bha-btn{position:relative}.bha-btn svg{width:18px;height:18px}' +
        '.bha-btn .bha-dot{position:absolute;top:2px;right:8px;width:7px;height:7px;border-radius:50%;background:var(--text-muted,#BAC4CC)}' +
        '.bha-btn.on .bha-dot{background:var(--brand-orange,#F26B1D);box-shadow:0 0 0 2px rgba(242,107,29,.35)}' +
        '.bha-win{display:flex;flex-direction:column;min-width:min(320px,calc(100vw - 48px));color:var(--text,#F6F8FA);font:12px var(--bh-font-ui,system-ui,sans-serif)}' +
        '.bha-sec{margin:4px 0;padding:6px;border-radius:8px;background:var(--bg,#111518)}' +
        '.bha-sec h4{margin:0 0 4px;font-size:11px;color:var(--text-muted,#BAC4CC);font-weight:normal;letter-spacing:.5px}' +
        '.bha-row{display:flex;align-items:center;gap:6px;margin:3px 0}.bha-row label{width:92px;color:var(--text-muted,#BAC4CC)}' +
        '.bha-row input[type=range]{flex:1;accent-color:var(--brand-orange,#F26B1D)}.bha-row output{width:62px;text-align:right}' +
        '.bha-chips{display:flex;flex-wrap:wrap;gap:4px}' +
        '.bha-chip{padding:2px 7px;border-radius:10px;background:var(--bg,#111518);cursor:pointer;border:1px solid var(--border,#38434C)}' +
        '.bha-chip.on{background:var(--brand-orange,#F26B1D);color:var(--on-accent,#23272B);border-color:var(--brand-orange,#F26B1D)}' +
        '.bha-sw{display:inline-flex;align-items:center;gap:6px;cursor:pointer}' +
        '.bha-sw i{width:30px;height:16px;border-radius:8px;background:var(--border,#38434C);position:relative;display:inline-block}' +
        '.bha-sw i:after{content:"";position:absolute;top:2px;left:2px;width:12px;height:12px;border-radius:50%;background:var(--text-muted,#BAC4CC);transition:left .15s}' +
        '.bha-sw.on i{background:var(--brand-orange,#F26B1D)}.bha-sw.on i:after{left:16px;background:var(--brand-ink,#23272B)}' +
        '.bha-nota{color:var(--text-muted,#BAC4CC);font-size:10.5px;margin-top:4px}' +
        '.bha-espera{color:var(--warn,#FFC857);font-size:11px}' +
        '.bha-win :focus-visible{outline:3px solid var(--focus,#FFC18F);outline-offset:3px}';

    var cssPuesto = false;
    function ponerCss() {
        if (cssPuesto) return;
        cssPuesto = true;
        $('<style id="bha-css">').text(CSS).appendTo('head');
    }

    P.ui = {};

    // botón del panel de plugins de OpenWebRX+ (Plugins.addButton); sin él, en la barra superior (detrás de los de BricoHams)
    P.ui.boton = function (id, texto, svg, titulo, alPulsar) {
        ponerCss();
        var nativo = typeof Plugins.addButton === 'function'
            ? Plugins.addButton(id.replace(/^bh-/, '').replace(/-button$/, ''), texto, alPulsar) : null;
        if (nativo) return $(nativo).addClass('bha-btn').attr('title', titulo).append('<span class="bha-dot"></span>');
        var $b = $('<div class="button bha-btn" id="' + id + '" title="' + titulo + '">' + svg + '<br>' + texto + '<span class="bha-dot"></span></div>');
        $b.on('click', alPulsar);
        (function colocar(intentos) {
            var $tras = $('#bh-dsp-button, #bh-filtro-button, #bh-cam-button, #bh-meteo-button, #bh-solar-button, #owrx-rig-dx-button').not($b).last();
            if ($tras.length) { $tras.after($b); return; }
            if (intentos > 0) { setTimeout(function () { colocar(intentos - 1); }, 500); return; }
            $('.openwebrx-main-buttons').first().append($b);
        })(10);
        return $b;
    };

    // ventana nativa (Plugins.addWindow); sin ella, un bloque suelto en pos0. Devuelve {$win, $cuerpo, abrir(bool), abierta()}
    P.ui.ventana = function (id, titulo, pos0) {
        ponerCss();
        var nid = id.replace(/^bh-/, '');
        var html = '<div class="bha-win" id="' + id + '" role="region" aria-label="' + titulo + '"><div class="bha-cuerpo"></div></div>';
        var nativa = typeof Plugins.addWindow === 'function' && typeof Plugins.toggleWindow === 'function';
        var host = nativa ? Plugins.addWindow(nid, titulo, html) : null;
        if (!host) {
            nativa = false;
            host = $('<div class="openwebrx-plugin-body"></div>').html(html)
                .css({ display: 'none', position: 'absolute', top: (pos0 ? pos0[1] : 110) + 'px', left: (pos0 ? pos0[0] : 460) + 'px', zIndex: 1002 }).appendTo('body')[0];
        }
        var $w = $(host).find('#' + id);
        var api = {
            $win: $w, $cuerpo: $w.find('.bha-cuerpo'),
            abrir: function (on) {
                if (nativa) Plugins.toggleWindow(nid, !!on); else $(host).toggle(!!on);
                if (api.alCambiar) api.alCambiar(!!on);
            },
            abierta: function () { return $(host).is(':visible'); }
        };
        $(host).find('.openwebrx-plugin-close').on('click touchend', function () {
            setTimeout(function () { if (api.alCambiar) api.alCambiar(false); }, 0);
        });
        return api;
    };

    // deslizador con etiqueta y valor; devuelve {$el, poner(v), habilitar(bool)}
    P.ui.deslizador = function (etiqueta, min, max, paso, valor, formato, alMover) {
        var $r = $('<div class="bha-row"><label>' + etiqueta + '</label><input type="range"><output></output></div>');
        var $i = $r.find('input').attr({ min: min, max: max, step: paso }).val(valor), $o = $r.find('output');
        function mostrar() { $o.text(formato(+$i.val())); }
        $i.on('input', function () { mostrar(); alMover(+$i.val()); });
        mostrar();
        return { $el: $r, poner: function (v) { $i.val(v); mostrar(); }, habilitar: function (on) { $i.prop('disabled', !on); $r.css('opacity', on ? 1 : 0.45); } };
    };

    // grupo de botones de opción; devuelve {$el, poner(clave)}
    P.ui.chips = function (opciones, actual, alElegir) {
        var $c = $('<div class="bha-chips"></div>');
        opciones.forEach(function (o) {
            $('<span class="bha-chip" data-k="' + o[0] + '" title="' + (o[2] || '') + '">' + o[1] + '</span>').appendTo($c);
        });
        function poner(k) { $c.children().removeClass('on').filter('[data-k="' + k + '"]').addClass('on'); }
        $c.on('click', '.bha-chip', function () { var k = $(this).data('k'); poner(k); alElegir(String(k)); });
        poner(actual);
        return { $el: $c, poner: poner };
    };

    // interruptor on/off; devuelve {$el, poner(bool)}
    P.ui.interruptor = function (texto, valor, alCambiar) {
        var $s = $('<span class="bha-sw"><i></i>' + texto + '</span>');
        function poner(v) { $s.toggleClass('on', !!v); }
        $s.on('click', function () { var v = !$s.hasClass('on'); poner(v); alCambiar(v); });
        poner(valor);
        return { $el: $s, poner: poner };
    };
})(Plugins.audio_cadena);

Plugins.audio_cadena.init = function () { return true; };
