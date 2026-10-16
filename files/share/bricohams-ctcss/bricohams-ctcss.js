/*
 * bricohams-ctcss.js · squelch por subtono CTCSS («Subtono FM») en la
 * página principal de OpenWebRX+.
 *
 * - Al sintonizar un bookmark FM con subtono (campo "ctcss", editado solo
 *   en /settings/bookmarks) se pide al servidor el squelch CTCSS de ese
 *   tono: el audio solo se abre cuando el repetidor transmite su subtono.
 * - Al cambiar de modo o alejarse más de 3 kHz de la frecuencia del
 *   bookmark, el subtono se desactiva.
 * - Selector «Subtono FM» bajo el squelch (solo visible en FM): control
 *   de escucha de la sesión actual; no guarda ninguna configuración.
 *
 * Instalado por bricohams-owrx-ctcss (líneas marcadas #@BH-CTCSS@).
 */
(function () {
    'use strict';

    var TONOS = [67.0, 69.3, 71.9, 74.4, 77.0, 79.7, 82.5, 85.4, 88.5, 91.5, 94.8, 97.4, 100.0, 103.5,
        107.2, 110.9, 114.8, 118.8, 123.0, 127.3, 131.8, 136.5, 141.3, 146.2, 150.0, 151.4, 156.7,
        159.8, 162.2, 165.5, 167.9, 171.3, 173.8, 177.3, 179.9, 183.5, 186.2, 189.9, 192.8, 196.6,
        199.5, 203.5, 206.5, 210.7, 218.1, 225.7, 229.1, 233.6, 241.8, 250.3, 254.1];

    var tono = 0;          // tono activo (Hz), 0 = sin subtono
    var tonoFreq = 0;      // frecuencia a la que se asoció el tono
    var enBookmark = false;

    function demod() {
        try { return UI.getDemodulator(); } catch (e) { return null; }
    }

    function modulacion(d) {
        try { return d && d.get_modulation ? d.get_modulation() : null; } catch (e) { return null; }
    }

    function frecuenciaActual(d) {
        try {
            if (d && typeof center_freq !== 'undefined') return center_freq + d.offset_frequency;
        } catch (e) { /* nada */ }
        try { return UI.getFrequency(); } catch (e) { return 0; }
    }

    function actualizarSelector() {
        var d = demod();
        var linea = document.getElementById('bh-ctcss-line');
        if (!linea) return;
        var fm = !!(d && d.get_modulation && d.get_modulation() === 'nfm');
        linea.style.display = fm ? '' : 'none';
        var sel = document.getElementById('bh-ctcss-select');
        if (sel) {
            var v = String(tono || 0);
            if (!sel.querySelector('option[value="' + v + '"]')) {
                var o = document.createElement('option');
                o.value = v;
                o.textContent = Number(v).toFixed(1) + ' Hz';
                sel.appendChild(o);
            }
            sel.value = v;
        }
    }

    function sincronizar(d) {
        if (!d) return;
        var deseado = (d.get_modulation && d.get_modulation() === 'nfm') ? tono : 0;
        // Un demodulador nuevo no conoce el estado del servidor: enviar siempre la primera vez
        if (d._bhCtcss === undefined || deseado !== d._bhCtcss) {
            d._bhCtcss = deseado;
            try { d.send({ctcss: deseado}); } catch (e) { /* nada */ }
        }
    }

    function instalar() {
        // Demodulator.set(): tras enviar la configuración, mandar el subtono
        if (typeof Demodulator !== 'undefined' && Demodulator.prototype.set && !Demodulator.prototype._bhCtcssSet) {
            var setOriginal = Demodulator.prototype.set;
            Demodulator.prototype._bhCtcssSet = true;
            Demodulator.prototype.set = function () {
                var r = setOriginal.apply(this, arguments);
                try {
                    if (this.started) {
                        if (tono && !enBookmark && Math.abs(frecuenciaActual(this) - tonoFreq) > 3000) {
                            tono = 0;
                        }
                        sincronizar(this);
                        actualizarSelector();
                    }
                } catch (e) { /* nada */ }
                return r;
            };
        }

        // Cambiar de modo a mano anula el subtono. OpenWebRX+ vuelve a llamar a setMode con el
        // mismo modo al actualizar el #freq=…,mod=… de la URL (hashchange, asíncrono tras
        // sintonizar un bookmark): eso no es un cambio de modo y no debe borrar el subtono.
        if (typeof DemodulatorPanel !== 'undefined' && DemodulatorPanel.prototype.setMode && !DemodulatorPanel.prototype._bhCtcss) {
            var setModeOriginal = DemodulatorPanel.prototype.setMode;
            DemodulatorPanel.prototype._bhCtcss = true;
            DemodulatorPanel.prototype.setMode = function () {
                var antes = modulacion(demod());
                var r = setModeOriginal.apply(this, arguments);
                try {
                    if (!enBookmark && modulacion(demod()) !== antes) tono = 0;
                    sincronizar(demod());
                    actualizarSelector();
                } catch (e) { /* nada */ }
                return r;
            };
        }

        // Sintonizar un bookmark: activar su subtono
        if (typeof UI !== 'undefined' && UI.tuneBookmark && !UI._bhCtcss) {
            var tuneOriginal = UI.tuneBookmark;
            UI._bhCtcss = true;
            UI.tuneBookmark = function (b) {
                var r;
                enBookmark = true;
                try {
                    tono = (b && b.modulation === 'nfm' && Number(b.ctcss)) || 0;
                    tonoFreq = (b && b.frequency) || 0;
                    r = tuneOriginal.apply(this, arguments);
                } finally {
                    enBookmark = false;
                }
                try {
                    var d = demod();
                    if (d) d.set();
                    sincronizar(d);
                    actualizarSelector();
                    if (tono && UI.showBubble) UI.showBubble('Subtono FM ' + tono.toFixed(1) + ' Hz');
                } catch (e) { /* nada */ }
                return r;
            };
        }
    }

    function crearSelector() {
        if (document.getElementById('bh-ctcss-line')) return;
        var slider = document.querySelector('.openwebrx-squelch-slider');
        var lineaSquelch = slider ? slider.closest('.openwebrx-panel-line') : null;
        if (!lineaSquelch) return;
        var linea = document.createElement('div');
        linea.className = 'openwebrx-panel-line';
        linea.id = 'bh-ctcss-line';
        linea.style.display = 'none';
        linea.title = 'Subtono CTCSS: el audio FM solo se abre cuando la señal lleva este tono (solo esta sesión)';
        var html = '<span style="margin-right:6px;white-space:nowrap">Subtono FM</span>' +
            '<select id="bh-ctcss-select" class="openwebrx-panel-select" style="flex:1">' +
            '<option value="0">Ninguno</option>';
        TONOS.forEach(function (t) { html += '<option value="' + t + '">' + t.toFixed(1) + ' Hz</option>'; });
        html += '</select>';
        linea.innerHTML = html;
        linea.style.alignItems = 'center';
        lineaSquelch.parentNode.insertBefore(linea, lineaSquelch.nextSibling);
        document.getElementById('bh-ctcss-select').addEventListener('change', function () {
            var d = demod();
            tono = Number(this.value) || 0;
            tonoFreq = frecuenciaActual(d);
            sincronizar(d);
        });
        actualizarSelector();
    }

    try { instalar(); } catch (e) { if (window.console) console.warn('bricohams-ctcss', e); }

    function alCargar() {
        try { instalar(); crearSelector(); } catch (e) { if (window.console) console.warn('bricohams-ctcss', e); }
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', alCargar);
    } else {
        alCargar();
    }
})();
