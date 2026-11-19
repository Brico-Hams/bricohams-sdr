/*
 * Brico-FX — OpenWebRX+ receiver skin inspired by a modern HF/VHF/UHF all-mode transceiver.
 * Independent plugin: needs only OpenWebRX+ 1.2.124+ (UI, LS, Plugins, jQuery, smeter_level, tuneBySteps).
 *
 * Copyright (c) 2026 EA5KAO / BricoHams — MIT licence (see LICENSE).
 *
 * Adds "Brico-FX" to the theme selector. While that theme is active a front panel (screen, meter,
 * VFO knob, keys and knobs) replaces the receiver panel; picking another theme removes it completely.
 * Optional calibration: window.bh_skin_bricofx_config = { smeter: { offset_hf, offset_vhf, iaru_vhf } }.
 */
Plugins.bh_skin_bricofx = Plugins.bh_skin_bricofx || {};

(function (P) {
    var ID = 'bh-bricofx', CLS = 'theme-' + ID, PANEL = 'bh-bricofx-panel';
    P._version = '1.0.0';
    P.no_css = true;          // the stylesheet is loaded below with ?v= so new releases are not cached
    P._timer = null;
    P._panel = null;
    P._observer = null;

    var TXT = {
        en: { volume: 'Volume', squelch: 'Squelch', tune: 'Tuning knob', func: 'Function knob',
            store: 'Hold to store, tap to recall', fine: 'Fine tuning', disp: 'Next view', back: 'Main view',
            mode: 'Next mode', empty: 'No decoded messages yet', search: 'Callsign filter' },
        es: { volume: 'Volumen', squelch: 'Silenciador', tune: 'Mando de sintonía', func: 'Mando de funciones',
            store: 'Mantén para guardar, pulsa para recuperar', fine: 'Sintonía fina', disp: 'Siguiente vista',
            back: 'Vista principal', mode: 'Siguiente modo', empty: 'Aún no hay mensajes decodificados',
            search: 'Filtrar por indicativo' }
    };
    var DIGITAL = ['ft8', 'ft4', 'wspr', 'jt65', 'jt9', 'fst4', 'fst4w', 'q65', 'msk144', 'js8', 'rtty',
        'packet', 'ais', 'pocsag', 'bpsk31', 'bpsk63', 'sstv', 'fax', 'hfdl', 'dsc'];

    P._logic = {
        // S-units from OpenWebRX+'s linear smeter_level; S9 = -73 dBm (HF) or -93 dBm (VHF, IARU), 6 dB/S
        sUnits: function (level, freqHz, cfg) {
            if (typeof level !== 'number' || !isFinite(level) || level <= 0) return { s: 0, over: 0, dbm: null };
            cfg = cfg || {};
            var vhf = freqHz >= 30e6;
            var off = (vhf ? cfg.offset_vhf : cfg.offset_hf) || 0;
            var dbm = 10 * Math.log10(level) + off;
            var s9 = vhf && cfg.iaru_vhf ? -93 : -73;
            if (dbm >= s9) return { s: 9, over: Math.max(0, Math.round(dbm - s9)), dbm: dbm };
            return { s: Math.max(0, Math.round(9 + (dbm - s9) / 6)), over: 0, dbm: dbm };
        },
        isDigital: function (mode) {
            return typeof mode === 'string' && DIGITAL.indexOf(mode.toLowerCase()) >= 0;
        },
        t: function (key) {
            var lang = (document.documentElement.lang || '').toLowerCase().indexOf('es') === 0 ? 'es' : 'en';
            return TXT[lang][key] || TXT.en[key] || key;
        }
    };

    P.init = function () {
        var lb = document.getElementById('openwebrx-themes-listbox');
        if (lb && !Array.prototype.some.call(lb.options || [], function (o) { return o.value === ID; })) {
            var o = document.createElement('option');
            o.value = ID;
            o.textContent = 'Brico-FX';
            lb.appendChild(o);
        }
        if (!P._observer) {
            var css = document.createElement('link');
            css.rel = 'stylesheet';
            css.href = P._base() + 'bh_skin_bricofx.css?v=' + P._version;
            document.head.appendChild(css);
            P._observer = new MutationObserver(P._sync);
            P._observer.observe(document.body, { attributes: true, attributeFilter: ['class'] });
        }
        P._sync();
        return true;
    };

    P._base = function () {
        var s = document.querySelector('script[src*="bh_skin_bricofx.js"]');
        return s ? s.src.replace(/[^\/]*$/, '') : 'static/plugins/receiver/bh_skin_bricofx/';
    };

    P._sync = function () {
        var on = document.body.classList.contains(CLS);
        if (on && !P._panel) P._build();
        else if (!on && P._panel) P._destroy();
    };

    P._build = function () {
        var host = document.getElementById('openwebrx-panel-receiver');
        if (!host) return;
        var panel = document.createElement('div');
        panel.id = PANEL;
        panel.setAttribute('role', 'group');
        panel.setAttribute('aria-label', 'Brico-FX');
        host.insertBefore(panel, host.firstChild || null);
        P._panel = panel;
        P._render(panel);
        P._timer = setInterval(function () { P._tick(); }, 250);
    };

    P._destroy = function () {
        if (P._timer !== null) clearInterval(P._timer);
        P._timer = null;
        if (P._unbind) P._unbind();
        if (P._panel && P._panel.parentNode) P._panel.parentNode.removeChild(P._panel);
        P._panel = null;
    };

    // filled in by the panel code below
    P._render = function () {};
    P._tick = function () {};
})(Plugins.bh_skin_bricofx);
