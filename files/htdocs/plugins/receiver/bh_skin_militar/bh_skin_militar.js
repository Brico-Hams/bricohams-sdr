/*
 * Military — OpenWebRX+ receiver skin in the style of a 1940s–50s field radio: analog needle meters,
 * a big tuning dial with a pointer handle, bakelite knobs, toggle switches and pilot lamps.
 * Independent plugin: needs only OpenWebRX+ 1.2.124+ (UI, Plugins, jQuery, smeter_level, tuneBySteps).
 *
 * Copyright (c) 2026 EA5KAO / BricoHams — MIT licence (see LICENSE).
 *
 * Optional calibration: window.bh_skin_militar_config = { smeter: { offset_hf, offset_vhf, iaru_vhf } }.
 */
Plugins.bh_skin_militar = Plugins.bh_skin_militar || {};

(function (P) {
    var ID = 'bh-militar', CLS = 'theme-' + ID, PANEL = 'bh-militar-panel', NS = '.bhmil';
    P._version = '1.0.0';
    P.no_css = true;
    P._timer = null;
    P._panel = null;
    P._observer = null;
    P._sig = -50;              // smoothed needle angles
    P._dial = 0;
    P._nr = false;
    P._mute = false;

    var TXT = {
        en: { label: 'Military', volume: 'Volume', squelch: 'Squelch', mode: 'Mode', tune: 'Tuning dial',
            signal: 'SIGNAL', af: 'AUDIO', nr: 'NOISE RED.', mute: 'MUTE', recv: 'RECEPTION' },
        es: { label: 'Militar', volume: 'Volumen', squelch: 'Silenciador', mode: 'Modo', tune: 'Dial de sintonía',
            signal: 'SEÑAL', af: 'AUDIO', nr: 'REDUC. RUIDO', mute: 'SILENCIO', recv: 'RECEPCIÓN' }
    };

    P._logic = {
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
        // S0 → -50°, S9 → +20°, S9+60 dB → +50°
        needleAngle: function (s, over) {
            if (s < 9) return -50 + Math.max(0, s) / 9 * 70;
            return 20 + Math.min(60, Math.max(0, over)) / 60 * 30;
        },
        knobSteps: function (deltaDeg, detentDeg) {
            var n = deltaDeg / (detentDeg || 15);
            return n < 0 ? Math.ceil(n) : Math.floor(n);
        },
        clamp: function (v, lo, hi) { return Math.min(hi, Math.max(lo, v)); },
        orDefault: function (v, d) { return (v === null || v === undefined || isNaN(v)) ? d : v; },
        t: function (key) {
            var lang = (document.documentElement.lang || '').toLowerCase().indexOf('es') === 0 ? 'es' : 'en';
            return TXT[lang][key] || TXT.en[key] || key;
        }
    };
    var L = P._logic;

    P.init = function () {
        var lb = document.getElementById('openwebrx-themes-listbox');
        if (lb && !Array.prototype.some.call(lb.options || [], function (o) { return o.value === ID; })) {
            var o = document.createElement('option');
            o.value = ID;
            o.textContent = L.t('label');
            lb.appendChild(o);
        }
        if (!P._observer) {
            var css = document.createElement('link');
            css.rel = 'stylesheet';
            css.href = P._base() + 'bh_skin_militar.css?v=' + P._version;
            document.head.appendChild(css);
            P._observer = new MutationObserver(P._sync);
            P._observer.observe(document.body, { attributes: true, attributeFilter: ['class'] });
        }
        P._sync();
        return true;
    };

    P._base = function () {
        var s = document.querySelector('script[src*="bh_skin_militar.js"]');
        return s ? s.src.replace(/[^\/]*$/, '') : 'static/plugins/receiver/bh_skin_militar/';
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
        panel.setAttribute('aria-label', L.t('label'));
        host.insertBefore(panel, host.firstChild || null);
        P._panel = panel;
        P._render(panel);
        P._timer = setInterval(function () { P._tick(); }, 200);
    };

    P._destroy = function () {
        if (P._timer !== null) clearInterval(P._timer);
        P._timer = null;
        // the MUTE switch only lives in this skin: never leave the listener muted in another theme
        if (P._mute) { try { UI.toggleMute(false); } catch (e) {} P._mute = false; }
        if (P._panel && typeof $ === 'function') $(P._panel).off(NS).find('*').off(NS);
        if (P._panel && P._panel.parentNode) P._panel.parentNode.removeChild(P._panel);
        P._panel = null;
    };

    // ------------------------------------------------------------------ panel
    function cfg() { return ((window.bh_skin_militar_config || {}).smeter) || {}; }
    function freq() { try { return UI.getFrequency(); } catch (e) { return 0; } }
    function modo() { try { return UI.getModulation() || ''; } catch (e) { return ''; } }
    function rawDb() { return (typeof smeter_level === 'number' && smeter_level > 0) ? 10 * Math.log10(smeter_level) : -200; }
    function slider(sel, v) {
        var el = document.querySelector(sel);
        if (!el) return null;
        if (v === undefined) return Number(el.value);
        el.value = v;
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        return v;
    }
    function meter(cls, label) {
        return '<div class="mil-meter ' + cls + '" aria-hidden="true"><div class="mil-face">' +
            '<div class="mil-arc"></div><div class="mil-needle"></div><div class="mil-hub"></div>' +
            '<span class="mil-mlabel">' + label + '</span></div></div>';
    }
    function knob(cls, label) {
        return '<div class="mil-kwrap"><div class="mil-knob ' + cls + '" role="slider" tabindex="0" aria-label="' + label +
            '"><span></span></div><small>' + label + '</small></div>';
    }
    function toggle(cls, label, on) {
        return '<button type="button" class="mil-toggle ' + cls + '" aria-pressed="' + !!on + '" aria-label="' + label +
            '"><span class="mil-lever"></span><small>' + label + '</small></button>';
    }
    function screws() { return '<i class="mil-screw s1"></i><i class="mil-screw s2"></i><i class="mil-screw s3"></i><i class="mil-screw s4"></i>'; }

    P._render = function (panel) {
        var t = L.t;
        panel.innerHTML = screws() +
            '<div class="mil-plate">BRICOHAMS · R-1 · ' + t('recv') + '</div>' +
            '<div class="mil-row">' +
                '<div class="mil-col">' + meter('mil-sig', t('signal')) + meter('mil-af', t('af')) + '</div>' +
                '<div class="mil-dial" role="slider" tabindex="0" aria-label="' + t('tune') + '">' +
                    '<div class="mil-scale"></div>' +
                    '<div class="mil-window"><span class="mil-freq"></span><span class="mil-mode"></span></div>' +
                    '<div class="mil-handle"></div>' +
                '</div>' +
                '<div class="mil-col mil-side">' +
                    '<div class="mil-lamps"><span class="mil-lamp mil-green" title="' + t('signal') + '"></span>' +
                    '<span class="mil-lamp mil-red" title="' + t('mute') + '"></span></div>' +
                    toggle('mil-nr', t('nr'), P._nr) + toggle('mil-mutesw', t('mute'), P._mute) +
                '</div>' +
            '</div>' +
            '<div class="mil-knobs">' + knob('mil-k-vol', t('volume')) + knob('mil-k-sql', t('squelch')) +
                knob('mil-k-mode', t('mode')) + '</div>';
        var $p = $(panel);
        P._bindKnob($p.find('.mil-dial'), 12, function (n) {
            if (typeof tuneBySteps === 'function') tuneBySteps(n);
            P._dial += n * 12;
        }, null);
        P._bindKnob($p.find('.mil-k-vol'), 12, function (n) {
            var v = L.clamp(L.orDefault(slider('#openwebrx-panel-volume'), 0) + 5 * n, 0, 150);
            slider('#openwebrx-panel-volume', v);
            try { UI.setVolume(v); } catch (e) {}
        }, 'span');
        P._bindKnob($p.find('.mil-k-sql'), 12, function (n) {
            slider('.openwebrx-squelch-slider', L.clamp(L.orDefault(slider('.openwebrx-squelch-slider'), -150) + 2 * n, -150, 0));
        }, 'span');
        P._bindKnob($p.find('.mil-k-mode'), 30, function (n) { P._nextMode(n); }, 'span');
        $p.on('click' + NS, '.mil-nr', function () {
            P._nr = !P._nr;
            try { UI.toggleNR(P._nr); } catch (e) {}
            $(this).attr('aria-pressed', P._nr);
        });
        $p.on('click' + NS, '.mil-mutesw', function () {
            P._mute = !P._mute;
            try { UI.toggleMute(P._mute); } catch (e) {}
            $(this).attr('aria-pressed', P._mute);
        });
        P._tick();
    };

    P._bindKnob = function ($el, detent, onSteps, rotSel) {
        var acc = 0, angle = 0, last = null, $rot = rotSel ? $el.find(rotSel) : null;
        function rotate(deg) { angle += deg; if ($rot) $rot.css('transform', 'rotate(' + angle + 'deg)'); }
        function feed(deg) {
            acc += deg;
            var n = L.knobSteps(acc, detent);
            if (n) { acc -= n * detent; onSteps(n); }
            rotate(deg);
        }
        function ang(e) {
            var r = $el[0].getBoundingClientRect();
            return Math.atan2(e.clientY - (r.top + r.height / 2), e.clientX - (r.left + r.width / 2)) * 180 / Math.PI;
        }
        $el.on('pointerdown' + NS, function (e) { last = ang(e); this.setPointerCapture(e.pointerId); e.preventDefault(); });
        $el.on('pointermove' + NS, function (e) {
            if (last === null) return;
            var a = ang(e), d = a - last;
            if (d > 180) d -= 360; else if (d < -180) d += 360;
            last = a;
            feed(d);
        });
        $el.on('pointerup' + NS + ' pointercancel' + NS, function () { last = null; });
        $el.on('wheel' + NS, function (e) {
            e.preventDefault();
            var dy = e.originalEvent.deltaY;
            if (dy) { onSteps(dy < 0 ? 1 : -1); rotate(dy < 0 ? detent : -detent); }
        });
        $el.on('keydown' + NS, function (e) {
            var k = { ArrowUp: 1, ArrowRight: 1, ArrowDown: -1, ArrowLeft: -1 }[e.key];
            if (k) { e.preventDefault(); onSteps(k); rotate(k * detent); }
        });
    };

    P._nextMode = function (n) {
        var $b = $('#openwebrx-panel-receiver .openwebrx-demodulator-button[data-modulation]');
        if (!$b.length) return;
        var i = $b.index($b.filter('.highlighted'));
        var j = ((i + (n || 1)) % $b.length + $b.length) % $b.length;
        $b.eq(j).trigger('click');
    };

    P._tick = function () {
        if (!P._panel) return;
        var $p = $(P._panel), f = freq();
        var u = L.sUnits(typeof smeter_level === 'number' ? smeter_level : 0, f, cfg());
        P._sig += (L.needleAngle(u.s, u.over) - P._sig) * 0.2;
        var vol = slider('#openwebrx-panel-volume') || 0;
        $p.find('.mil-sig .mil-needle').css('transform', 'rotate(' + P._sig.toFixed(1) + 'deg)');
        $p.find('.mil-af .mil-needle').css('transform', 'rotate(' + (-50 + vol / 150 * 100).toFixed(1) + 'deg)');
        $p.find('.mil-handle').css('transform', 'rotate(' + P._dial + 'deg)');
        $p.find('.mil-freq').text(f ? (f / 1e6).toFixed(4) + ' MHz' : '---');
        $p.find('.mil-mode').text(modo().toUpperCase());
        var sq = slider('.openwebrx-squelch-slider');
        $p.find('.mil-green').toggleClass('on', rawDb() > (sq === null ? -150 : sq));
        $p.find('.mil-red').toggleClass('on', P._mute);
    };
})(Plugins.bh_skin_militar);
