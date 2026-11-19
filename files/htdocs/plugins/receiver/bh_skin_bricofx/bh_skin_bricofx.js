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
        // whole detents turned (sign kept, truncated toward zero)
        knobSteps: function (deltaDeg, detentDeg) {
            var n = deltaDeg / (detentDeg || 15);
            return n < 0 ? Math.ceil(n) : Math.floor(n);
        },
        clamp: function (v, lo, hi) { return Math.min(hi, Math.max(lo, v)); },
        orDefault: function (v, d) { return (v === null || v === undefined || isNaN(v)) ? d : v; },
        // QMB: long press (≥ 600 ms) or Shift stores, a tap / Enter recalls
        qmbAction: function (heldMs, shift) { return (shift || heldMs >= 600) ? 'store' : 'recall'; },
        fmtFreq: function (hz) {
            if (!hz || !isFinite(hz)) return '---.---.---';
            var s = String(Math.round(hz));
            return s.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
        },
        // bar position: S0..S9 fill 0..60 %, S9+0..60 dB fill 60..100 %
        meterPct: function (u) {
            var p = u.s < 9 ? u.s / 9 * 60 : 60 + Math.min(60, u.over) / 60 * 40;
            return Math.round(p);
        },
        VIEWS: ['main', 'scope', 'digital'],
        nextView: function (cur) {
            var v = P._logic.VIEWS, i = v.indexOf(cur);
            return i < 0 ? 'main' : v[(i + 1) % v.length];
        },
        // a view the user picked after the last mode change wins; otherwise digital modes open the digital view
        viewFor: function (mode, chosen) {
            if (chosen) return chosen;
            return P._logic.isDigital(mode) ? 'digital' : 'main';
        },
        scopeFreq: function (x, width, range) {
            if (!width || !range) return null;
            return Math.round(range.start + x / width * (range.end - range.start));
        },
        lastLines: function (lines, n, filter) {
            var f = (filter || '').toLowerCase();
            var sel = f ? lines.filter(function (l) { return l.toLowerCase().indexOf(f) >= 0; }) : lines.slice();
            return sel.slice(-n).reverse();
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
        host.scrollTop = 0;            // the front panel is the first thing seen
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

    // ------------------------------------------------------------------ panel
    var L = P._logic, NS = '.bhfx';
    P._fn = 'step';            // FUNC knob target: step | nr | filter
    P._af = 'af';              // AF/SQL knob target: af | sql
    P._fine = null;            // saved tuning step while CLAR (fine tuning) is on

    function cfg() { return ((window.bh_skin_bricofx_config || {}).smeter) || {}; }
    function ls(k, v) {
        try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; }
    }
    function freq() { try { return UI.getFrequency(); } catch (e) { return 0; } }
    function modo() { try { return UI.getModulation() || ''; } catch (e) { return ''; } }
    function rawDb() { return (typeof smeter_level === 'number' && smeter_level > 0) ? 10 * Math.log10(smeter_level) : -200; }
    function tune(n) { if (n && typeof tuneBySteps === 'function') tuneBySteps(n); }
    function slider(sel, v) {
        var el = document.querySelector(sel);
        if (!el) return null;
        if (v === undefined) return Number(el.value);
        el.value = v;
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        return v;
    }
    function key(label, cls, title, extra) {
        return '<button type="button" class="fx-key ' + (cls || '') + '" aria-label="' + title + '" title="' + title + '"' +
            (extra || '') + '>' + label + '</button>';
    }
    function knob(cls, title) {
        return '<div class="fx-knob ' + cls + '" role="slider" tabindex="0" aria-label="' + title + '"><span></span></div>';
    }

    P._render = function (panel) {
        var t = L.t;
        panel.innerHTML =
            '<div class="fx-top">' +
                key('S-DX', 'fx-thin', 'S-DX', ' aria-disabled="true"') + key('MODE', 'fx-thin fx-mode', t('mode')) +
                key('BAND', 'fx-thin', 'BAND', ' aria-disabled="true"') + key('SPLIT', 'fx-thin', 'SPLIT', ' aria-disabled="true"') +
                key('V/M', 'fx-thin fx-vm', t('store')) + key('M-V', 'fx-thin', 'M-V', ' aria-disabled="true"') +
            '</div>' +
            '<div class="fx-body">' +
                '<div class="fx-left">' + knob('fx-k-func', t('func')) +
                    '<span class="fx-led" aria-hidden="true"></span>' +
                    '<button type="button" class="fx-key fx-af" aria-pressed="true">AF</button>' +
                    '<button type="button" class="fx-key fx-sql" aria-pressed="false">SQL</button>' +
                    knob('fx-k-af', t('volume')) + '</div>' +
                '<div class="fx-screen">' +
                    '<div class="fx-status"><b>BRICO-FX</b><span class="fx-fn"></span><span class="fx-modebox"></span></div>' +
                    '<div class="fx-meter" aria-hidden="true">' +
                        '<div class="fx-scale"><i>S</i>1 3 5 7 9 <em>+20 +40 +60dB</em></div>' +
                        '<div class="fx-bar"><span></span></div>' +
                        '<div class="fx-vol">VOL <span></span></div>' +
                    '</div>' +
                    '<div class="fx-freq" aria-live="off"></div>' +
                    '<div class="fx-view" data-view="main"></div>' +
                    '<div class="fx-soft" role="toolbar"></div>' +
                '</div>' +
                '<div class="fx-right">' +
                    '<div class="fx-lamps"><span class="fx-busy">BUSY</span></div>' +
                    key('QMB', 'fx-qmb', t('store')) + key('CLAR', 'fx-clar', t('fine'), ' aria-pressed="false"') +
                    '<div class="fx-vfo" role="slider" tabindex="0" aria-label="' + t('tune') + '"><div class="fx-vfo-ring"><div class="fx-vfo-cap"></div></div></div>' +
                    key('DISP', 'fx-disp', t('disp')) + key('BACK', 'fx-back', t('back')) +
                '</div>' +
            '</div>';
        var $p = $(panel);
        P._bindKnob($p.find('.fx-vfo'), 15, function (n) { tune(n); }, '.fx-vfo-ring');
        P._bindKnob($p.find('.fx-k-af'), 12, function (n) {
            if (P._af === 'sql') slider('.openwebrx-squelch-slider', L.clamp(L.orDefault(slider('.openwebrx-squelch-slider'), -150) + 2 * n, -150, 0));
            else {
                var v = L.clamp(L.orDefault(slider('#openwebrx-panel-volume'), 0) + 5 * n, 0, 150);
                slider('#openwebrx-panel-volume', v);
                try { UI.setVolume(v); } catch (e) {}
            }
        });
        // FUNC turns only; its target (STEP / NR / FILTER) is chosen with the soft keys
        P._bindKnob($p.find('.fx-k-func'), 20, P._funcTurn);
        $p.on('click' + NS, '.fx-af, .fx-sql', function () {
            P._af = $(this).hasClass('fx-sql') ? 'sql' : 'af';
            $p.find('.fx-af').attr('aria-pressed', P._af === 'af');
            $p.find('.fx-sql').attr('aria-pressed', P._af === 'sql');
        });
        $p.on('click' + NS, '.fx-mode', P._nextMode);
        $p.on('click' + NS, '.fx-vm', function () { var f = Number(ls('bh_bricofx_qmb')); if (f > 0) UI.setFrequency(f, false); });
        var t0 = 0;
        $p.on('pointerdown' + NS, '.fx-qmb', function () { t0 = Date.now(); });
        $p.on('pointerleave' + NS + ' pointercancel' + NS, '.fx-qmb', function () { t0 = 0; });
        $p.on('click' + NS, '.fx-qmb', function (e) {
            var held = t0 ? Date.now() - t0 : 0;
            t0 = 0;
            if (L.qmbAction(held, e.shiftKey) === 'store') ls('bh_bricofx_qmb', String(freq()));
            else { var f = Number(ls('bh_bricofx_qmb')); if (f > 0) UI.setFrequency(f, false); }
        });
        $p.on('click' + NS, '.fx-clar', P._toggleFine);
        if (P._renderViews) P._renderViews($p);
        P._tick();
    };

    // drag (rotation), wheel and arrow keys → whole detents
    P._bindKnob = function ($el, detent, onSteps, rotSel) {
        var acc = 0, angle = 0, last = null, $rot = rotSel ? $el.find(rotSel) : $el.find('span');
        function rotate(deg) { angle += deg; $rot.css('transform', 'rotate(' + angle + 'deg)'); }
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

    P._funcTurn = function (n) {
        if (P._fn === 'step') {
            var lb = document.getElementById('openwebrx-tuning-step-listbox');
            if (!lb) return;
            lb.selectedIndex = L.clamp(lb.selectedIndex + n, 0, lb.options.length - 1);
            lb.dispatchEvent(new Event('change', { bubbles: true }));
        } else if (P._fn === 'nr') {
            try { UI.toggleNR(); } catch (e) {}
        } else {
            var d = UI.getDemodulator && UI.getDemodulator();
            var bp = d && d.getBandpass();
            if (!bp || bp.low_cut === null || bp.high_cut === null) return;
            var f = 1 + 0.1 * n;      // ±10 % width per detent around the passband centre
            var c = (bp.low_cut + bp.high_cut) / 2, w = (bp.high_cut - bp.low_cut) / 2 * f;
            if (w < 50) return;
            d.setBandpass({ low_cut: Math.round(c - w), high_cut: Math.round(c + w) });
        }
    };

    P._nextMode = function () {
        var $b = $('#openwebrx-panel-receiver .openwebrx-demodulator-button[data-modulation]:visible');
        if (!$b.length) $b = $('#openwebrx-panel-receiver .openwebrx-demodulator-button[data-modulation]');
        if (!$b.length) return;
        var i = $b.index($b.filter('.highlighted'));
        $b.eq((i + 1) % $b.length).trigger('click');
    };

    P._toggleFine = function () {
        var lb = document.getElementById('openwebrx-tuning-step-listbox');
        if (!lb || !lb.options.length) return;
        if (P._fine === null) { P._fine = lb.selectedIndex; lb.selectedIndex = 0; }
        else { lb.selectedIndex = P._fine; P._fine = null; }
        lb.dispatchEvent(new Event('change', { bubbles: true }));
        $(P._panel).find('.fx-clar').attr('aria-pressed', P._fine !== null);
    };

    P._unbind = function () {
        if (P._fine !== null) P._toggleFine();
        if (P._panel && typeof $ === 'function') $(P._panel).off(NS).find('*').off(NS);
    };

    // ------------------------------------------------------------------ screen views
    P._view = 'main';
    P._chosen = null;          // view picked by the user since the last mode change
    P._lastMode = null;
    P._filter = '';
    P._clearAt = 0;            // CLEAR hides the lines decoded before this count
    var DECODERS = ['wsjt', 'js8', 'packet', 'pocsag', 'skimmer', 'hfdl', 'dsc', 'sstv', 'fax'];
    var SOFT = {
        main: [['MODE', 'mode'], ['STEP', 'fn-step'], ['NR', 'fn-nr'], ['FILTER', 'fn-filter'], ['DISP', 'disp']],
        scope: [['ZOOM−', 'zout'], ['ZOOM+', 'zin'], ['FULL', 'full'], ['BACK', 'back']],
        digital: [['ALL', 'all'], ['SEARCH', 'search'], ['CLEAR', 'clear'], ['LOG', 'log'], ['BACK', 'back']]
    };

    P._renderViews = function ($p) {
        $p.on('click' + NS, '.fx-disp', function () { P._show(L.nextView(P._view), true); });
        $p.on('click' + NS, '.fx-back', function () { P._show('main', true); });
        $p.on('click' + NS, '.fx-soft button', function () { P._soft($(this).data('act')); });
        $p.on('click' + NS, '.fx-scope', function (e) {
            var r = this.getBoundingClientRect();
            var range = typeof get_visible_freq_range === 'function' ? get_visible_freq_range() : null;
            var f = L.scopeFreq(e.clientX - r.left, r.width, range);
            if (f) UI.setFrequency(f);
        });
        P._show(P._view, false);
    };

    P._show = function (view, byUser) {
        if (byUser) P._chosen = view;
        P._view = view;
        if (!P._panel) return;
        var $p = $(P._panel), $v = $p.find('.fx-view').attr('data-view', view).empty();
        if (view !== 'main') $v.append('<canvas class="fx-scope" aria-label="Waterfall" role="img"></canvas>');
        if (view === 'digital') $v.append('<ol class="fx-msgs" aria-live="polite"></ol>');
        $p.find('.fx-soft').html(SOFT[view].map(function (k) {
            var on = k[1] === 'fn-' + P._fn;
            return '<button type="button" data-act="' + k[1] + '" aria-pressed="' + on + '">' + k[0] + '</button>';
        }).join(''));
    };

    P._soft = function (act) {
        if (act === 'mode') P._nextMode();
        else if (act === 'disp') P._show(L.nextView(P._view), true);
        else if (act === 'back') P._show('main', true);
        else if (act.indexOf('fn-') === 0) { P._fn = act.slice(3); P._show(P._view, false); }
        else if (act === 'zin' && typeof zoomInOneStep === 'function') zoomInOneStep();
        else if (act === 'zout' && typeof zoomOutOneStep === 'function') zoomOutOneStep();
        else if (act === 'full' && typeof zoomOutTotal === 'function') zoomOutTotal();
        else if (act === 'all') { P._filter = ''; P._clearAt = 0; }
        else if (act === 'search') { var q = window.prompt(L.t('search'), P._filter); if (q !== null) P._filter = q.trim(); }
        else if (act === 'clear') P._clearAt = P._decoded().length;
        else if (act === 'log') { var el = P._decoderPanel(); if (el) el.scrollIntoView({ block: 'nearest' }); }
    };

    P._decoderPanel = function () {
        for (var i = 0; i < DECODERS.length; i++) {
            var el = document.getElementById('openwebrx-panel-' + DECODERS[i] + '-message');
            if (el && el.offsetParent !== null) return el;
        }
        return null;
    };

    P._decoded = function () {
        var el = P._decoderPanel();
        if (!el) return [];
        var rows = el.querySelectorAll('tbody tr');
        if (!rows.length) rows = el.lastElementChild ? el.lastElementChild.children : [];
        return Array.prototype.map.call(rows, function (r) { return r.textContent.replace(/\s+/g, ' ').trim(); })
            .filter(Boolean);
    };

    // copies what OpenWebRX+ already draws (spectrum + waterfall) into the small screen canvas
    P._drawScope = function (cv) {
        var w = cv.clientWidth, h = cv.clientHeight;
        if (!w || !h) return;
        if (cv.width !== w) cv.width = w;
        if (cv.height !== h) cv.height = h;
        var ctx = cv.getContext('2d');
        ctx.fillStyle = '#000';
        ctx.fillRect(0, 0, w, h);
        var spec = document.getElementById('openwebrx-spectrum-canvas');
        var top = 0;
        if (spec && spec.width && spec.offsetParent !== null) {
            top = Math.round(h * 0.3);
            ctx.drawImage(spec, 0, 0, w, top);
        }
        var box = document.getElementById('webrx-canvas-container');
        if (!box) return;
        var br = box.getBoundingClientRect();
        if (!br.width || !br.height) return;
        var sx = w / br.width, sy = (h - top) / br.height;
        box.querySelectorAll('canvas').forEach(function (c) {
            var r = c.getBoundingClientRect();
            if (!c.width || r.bottom < br.top || r.top > br.bottom) return;
            ctx.drawImage(c, (r.left - br.left) * sx, top + (r.top - br.top) * sy, r.width * sx, r.height * sy);
        });
    };

    // the message list is an aria-live region: rebuild it only when its content changes
    P._lastMsgs = null;
    P._msgsChanged = function (html) {
        if (html === P._lastMsgs) return false;
        P._lastMsgs = html;
        return true;
    };

    P._tickViews = function ($p) {
        var m = modo();
        if (m !== P._lastMode) { P._lastMode = m; P._chosen = null; P._clearAt = 0; }
        var v = L.viewFor(m, P._chosen);
        if (v !== P._view) P._show(v, false);
        var cv = $p.find('.fx-scope')[0];
        if (cv) P._drawScope(cv);
        var $ol = $p.find('.fx-msgs');
        if ($ol.length) {
            var lines = P._decoded().slice(P._clearAt);
            var out = L.lastLines(lines, 8, P._filter);
            var html = out.length ? out.map(function (l) { return '<li>' + $('<i>').text(l).html() + '</li>'; }).join('')
                : '<li class="fx-empty">' + L.t('empty') + '</li>';
            if (P._msgsChanged(html) || !$ol.children().length) $ol.html(html);
        }
    };

    P._tick = function () {
        if (!P._panel) return;
        var $p = $(P._panel), f = freq(), u = L.sUnits(typeof smeter_level === 'number' ? smeter_level : 0, f, cfg());
        $p.find('.fx-freq').text(L.fmtFreq(f));
        $p.find('.fx-modebox').text(modo().toUpperCase());
        $p.find('.fx-fn').text({ step: 'STEP', nr: 'NR', filter: 'FILTER' }[P._fn]);
        $p.find('.fx-bar span').css('width', L.meterPct(u) + '%');
        $p.find('.fx-vol span').css('width', Math.round((slider('#openwebrx-panel-volume') || 0) / 150 * 100) + '%');
        var sq = slider('.openwebrx-squelch-slider');
        $p.find('.fx-busy').toggleClass('on', rawDb() > (sq === null ? -150 : sq));
        if (P._tickViews) P._tickViews($p);
    };
})(Plugins.bh_skin_bricofx);
