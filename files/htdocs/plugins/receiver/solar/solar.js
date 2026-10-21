/*
 * solar: radiación solar y propagación HF para OpenWebRX+
 *
 * Autor: BricoHams
 *
 * Añade un botón "SOL" en la barra superior, junto al de DX cluster
 * (rig_skin). Abre una ventana flotante con datos en vivo de NOAA SWPC:
 *   - Flujo solar (SFI), rayos X (clase de fulguración), protones,
 *     índices Kp/A, viento solar y escalas NOAA R/S/G (+ previsión).
 *   - Gráficas de 6 h de rayos X (GOES) y protones >=10 MeV.
 *   - Estimación de bandas HF día/noche en el QTH, mapa de absorción
 *     D-RAP y mapa de MUF de KC2G.
 *   - Imágenes del Sol (SDO) y el panel de HamQSL.
 * El punto del botón toma el color de la escala NOAA más alta.
 *
 * Ajustes opcionales en init.js (antes de cargar el plugin):
 *   window.solar_config = { lat: 42.23, lon: -8.71, after: '#owrx-rig-dx-button' };
 */

Plugins.solar._version = '1.0.0';
Plugins.solar._author='BricoHams';
Plugins.solar.no_css = true;

Plugins.solar.init = function () {
    var cfg = window.solar_config || {};
    var LAT = (typeof cfg.lat === 'number') ? cfg.lat : 0;
    var LON = (typeof cfg.lon === 'number') ? cfg.lon : 0;
    var AFTER = cfg.after || '#owrx-rig-dx-button';

    var SW = 'https://services.swpc.noaa.gov';
    var URL = {
        sfi:    SW + '/products/summary/10cm-flux.json',
        kp:     SW + '/products/noaa-planetary-k-index.json',
        flare:  SW + '/json/goes/primary/xray-flares-latest.json',
        xray:   SW + '/json/goes/primary/xrays-6-hour.json',
        proton: SW + '/json/goes/primary/integral-protons-6-hour.json',
        wind:   SW + '/products/summary/solar-wind-speed.json',
        mag:    SW + '/products/summary/solar-wind-mag-field.json',
        scales: SW + '/products/noaa-scales.json'
    };
    var IMG = {
        drap:   SW + '/images/animations/d-rap/global/latest.png',
        muf:    'https://prop.kc2g.com/renders/current/mufd-normal-now.svg',
        sdo193: 'https://sdo.gsfc.nasa.gov/assets/img/latest/latest_512_0193.jpg',
        sdohmi: 'https://sdo.gsfc.nasa.gov/assets/img/latest/latest_512_HMIIC.jpg',
        hamqsl: 'https://www.hamqsl.com/solar101vhf.php'
    };

    // ---------------------------------------------------------------
    //  estilos (un solo archivo: no hace falta solar.css)
    // ---------------------------------------------------------------
    var css =
        '#bh-solar-button{position:relative}' +
        '#bh-solar-button svg{width:18px;height:18px}' +
        '#bh-solar-button .sol-dot{position:absolute;top:2px;right:8px;width:7px;height:7px;border-radius:50%;background:#555;box-shadow:0 0 4px rgba(0,0,0,.8)}' +
        '#bh-solar{position:fixed;top:90px;left:420px;z-index:1002;width:430px;max-width:calc(100vw - 16px);max-height:calc(100vh - 20px);' +
            'display:none;flex-direction:column;padding:8px;border-radius:8px;color:#cfd4d9;font:12px roboto-mono,monospace;' +
            'background:linear-gradient(#2a2e33,#17191d);box-shadow:inset 0 1px 0 rgba(255,255,255,.07),0 0 0 1px #060708,0 6px 18px rgba(0,0,0,.65)}' +
        '#bh-solar.open{display:flex}' +
        '#bh-solar .sol-hdr{display:flex;align-items:center;gap:6px;padding:0 2px 6px;cursor:move;user-select:none;touch-action:none}' +
        '#bh-solar .sol-title{flex:1;color:#93a0ab;letter-spacing:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}' +
        '#bh-solar .sol-time{color:#6b7782;font-size:11px}' +
        '#bh-solar .sol-btn{cursor:pointer;color:#93a0ab;padding:0 4px;font-size:15px;line-height:1}' +
        '#bh-solar .sol-btn:hover{color:#fff}' +
        '#bh-solar .sol-tabs{display:flex;gap:4px;margin-bottom:6px;flex-wrap:wrap}' +
        '#bh-solar .sol-chip{cursor:pointer;padding:2px 7px;border-radius:3px;background:#10161b;color:#93a0ab;box-shadow:0 0 0 1px #1d242b;font-size:11px}' +
        '#bh-solar .sol-chip.on{color:#0f0;box-shadow:0 0 0 1px #2e7d32}' +
        '#bh-solar .sol-lcd{overflow:auto;min-height:0;border-radius:5px;padding:8px;background:#0b0f12;box-shadow:inset 0 2px 8px rgba(0,0,0,.9),inset 0 0 2px #000}' +
        '#bh-solar .sol-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}' +
        '#bh-solar .sol-tile{background:#10161b;border-radius:4px;padding:6px;box-shadow:0 0 0 1px #1d242b;min-width:0}' +
        '#bh-solar .sol-k{color:#6b7782;font-size:10px;letter-spacing:1px;text-transform:uppercase}' +
        '#bh-solar .sol-v{font-size:19px;color:#e8edf1;margin:2px 0 1px;white-space:nowrap}' +
        '#bh-solar .sol-s{font-size:10px;color:#93a0ab;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}' +
        '#bh-solar .sol-row{display:flex;justify-content:space-between;gap:8px;padding:3px 0;border-bottom:1px solid #161d23}' +
        '#bh-solar .sol-h{color:#93a0ab;letter-spacing:1px;margin:8px 0 4px;font-size:11px}' +
        '#bh-solar canvas{width:100%;height:150px;display:block;background:#0b0f12}' +
        '#bh-solar img{max-width:100%;display:block;margin:0 auto 6px;border-radius:3px}' +
        '#bh-solar table{width:100%;border-collapse:collapse}' +
        '#bh-solar td,#bh-solar th{padding:3px 4px;text-align:center;border-bottom:1px solid #161d23}' +
        '#bh-solar th{color:#6b7782;font-weight:normal;font-size:10px;letter-spacing:1px}' +
        '#bh-solar td:first-child{text-align:left}' +
        '#bh-solar .c-good{color:#4caf50}#bh-solar .c-fair{color:#ffc107}#bh-solar .c-poor{color:#f44336}' +
        '#bh-solar .sol-note{color:#6b7782;font-size:10px;margin-top:6px;line-height:1.4}' +
        '#bh-solar a{color:#64b5f6}' +
        '@media (max-width:600px){#bh-solar{left:8px!important;top:60px!important}#bh-solar .sol-grid{grid-template-columns:repeat(2,1fr)}}';
    var st = document.createElement('style');
    st.textContent = css;
    document.head.appendChild(st);

    // ---------------------------------------------------------------
    //  utilidades
    // ---------------------------------------------------------------
    function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
    function getJSON(u) {
        return fetch(u, { cache: 'no-store' }).then(function (r) {
            if (!r.ok) throw new Error(r.status);
            return r.json();
        });
    }
    function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
    function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* sin almacenamiento */ } }
    function hhmm(d) { return ('0' + d.getUTCHours()).slice(-2) + ':' + ('0' + d.getUTCMinutes()).slice(-2); }

    // clase de fulguración a partir del flujo 0.1-0.8 nm (W/m2)
    function xclass(f) {
        if (!(f > 0)) return '—';
        var L = ['A', 'B', 'C', 'M', 'X'], e = Math.floor(Math.log10(f)) + 8;
        if (e < 0) return 'A' + (f / 1e-8).toFixed(1);
        if (e > 4) return 'X' + (f / 1e-4).toFixed(1);
        return L[e] + (f / Math.pow(10, e - 8)).toFixed(1);
    }
    function xcolor(c) {
        switch ((c || '')[0]) {
            case 'X': return '#f44336';
            case 'M': return '#ff9800';
            case 'C': return '#ffc107';
            default: return '#4caf50';
        }
    }
    function scaleColor(n) { n = +n || 0; return ['#4caf50', '#ffeb3b', '#ffc107', '#ff9800', '#f44336', '#b71c1c'][Math.min(n, 5)]; }
    function kpColor(k) { return k >= 7 ? '#f44336' : k >= 5 ? '#ff9800' : k >= 4 ? '#ffc107' : '#4caf50'; }
    function sScale(p) { return p >= 1e5 ? 5 : p >= 1e4 ? 4 : p >= 1e3 ? 3 : p >= 100 ? 2 : p >= 10 ? 1 : 0; }

    // elevación del Sol en el QTH (grados)
    function sunElevation(date, lat, lon) {
        var rad = Math.PI / 180;
        var d = (date.getTime() / 86400000) - 10957.5;            // días desde J2000
        var g = (357.529 + 0.98560028 * d) * rad;
        var q = 280.459 + 0.98564736 * d;
        var L = (q + 1.915 * Math.sin(g) + 0.020 * Math.sin(2 * g)) * rad;
        var e = (23.439 - 0.00000036 * d) * rad;
        var dec = Math.asin(Math.sin(e) * Math.sin(L));
        var ra = Math.atan2(Math.cos(e) * Math.sin(L), Math.cos(L));
        var gmst = (18.697374558 + 24.06570982441908 * d) % 24;
        var ha = ((gmst * 15 + lon) * rad) - ra;
        return Math.asin(Math.sin(lat * rad) * Math.sin(dec) + Math.cos(lat * rad) * Math.cos(dec) * Math.cos(ha)) / rad;
    }

    // estimación de bandas a partir de SFI, Kp y escala R (aproximada)
    function bandCond(group, night, sfi, k, r) {
        if (!night && r >= 3) return 'poor';                    // apagón de radio por rayos X
        var c;
        switch (group) {
            case 0: // 160-80-40
                c = night ? (k <= 2 ? 'good' : k <= 4 ? 'fair' : 'poor') : (k <= 4 ? 'fair' : 'poor'); break;   // de día manda la absorción de la capa D
            case 1: // 30-20
                c = night ? (sfi >= 120 && k <= 3 ? 'good' : sfi >= 90 && k <= 5 ? 'fair' : 'poor')
                          : (sfi >= 90 && k <= 3 ? 'good' : sfi >= 70 && k <= 5 ? 'fair' : 'poor'); break;
            case 2: // 17-15
                c = night ? (sfi >= 150 && k <= 2 ? 'fair' : 'poor')
                          : (sfi >= 120 && k <= 3 ? 'good' : sfi >= 90 && k <= 4 ? 'fair' : 'poor'); break;
            case 3: // 12-10
                c = night ? 'poor' : (sfi >= 150 && k <= 3 ? 'good' : sfi >= 110 && k <= 4 ? 'fair' : 'poor'); break;
        }
        if (!night && r === 2 && c === 'good') c = 'fair';
        return c;
    }
    var COND_TXT = { good: 'Buena', fair: 'Regular', poor: 'Mala' };

    // ---------------------------------------------------------------
    //  botón en la barra superior
    // ---------------------------------------------------------------
    var SUN_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">' +
        '<circle cx="12" cy="12" r="4.2"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8"/></svg>';
    var $btn = $('<div class="button" id="bh-solar-button" title="Radiación solar y propagación (NOAA SWPC)">' +
        SUN_SVG + '<br>SOL<span class="sol-dot"></span></div>');

    function placeButton(tries) {
        var $after = $(AFTER);
        if ($after.length) { $after.after($btn); return; }
        if (tries > 0) { setTimeout(function () { placeButton(tries - 1); }, 500); return; }
        // sin rig_skin: detrás de "Estado" o al final de la barra
        var $bar = $('.openwebrx-main-buttons').first();
        var $status = $bar.children('.button').filter(function () { return /Estado|Status/.test($(this).text()); }).first();
        if ($status.length) $status.after($btn); else $bar.append($btn);
    }
    placeButton(20);

    // ---------------------------------------------------------------
    //  ventana
    // ---------------------------------------------------------------
    var $win = $('<div id="bh-solar" role="dialog" aria-label="Radiación solar">' +
        '<div class="sol-hdr"><span class="sol-title">☀ SOL · RADIACIÓN Y PROPAGACIÓN</span>' +
        '<span class="sol-time"></span><span class="sol-btn sol-reload" title="Actualizar">⟳</span>' +
        '<span class="sol-btn sol-close" title="Cerrar">×</span></div>' +
        '<div class="sol-tabs">' +
        '<span class="sol-chip on" data-tab="datos">DATOS</span>' +
        '<span class="sol-chip" data-tab="graf">RAYOS X · PROTONES</span>' +
        '<span class="sol-chip" data-tab="bandas">BANDAS HF</span>' +
        '<span class="sol-chip" data-tab="img">IMÁGENES</span></div>' +
        '<div class="sol-lcd"></div></div>');
    $('body').append($win);
    var $lcd = $win.find('.sol-lcd');

    var tab = lsGet('bh_solar_tab') || 'datos';
    var data = {}, loadedAt = 0, timer = null, open = false;

    function setTab(t) {
        tab = t;
        lsSet('bh_solar_tab', t);
        $win.find('.sol-chip').removeClass('on').filter('[data-tab="' + t + '"]').addClass('on');
        render();
    }
    $win.on('click', '.sol-chip', function () { setTab($(this).data('tab')); });
    $win.find('.sol-close').on('click', function () { toggle(false); });
    $win.find('.sol-reload').on('click', function () { load(true); });
    $btn.on('click', function () { toggle(!open); });

    // posición guardada y arrastre por la cabecera
    (function () {
        var p = (lsGet('bh_solar_pos') || '').split(',');
        if (p.length === 2 && window.innerWidth > 600) {
            $win.css({ left: Math.max(0, Math.min(+p[0], window.innerWidth - 120)) + 'px',
                       top: Math.max(0, Math.min(+p[1], window.innerHeight - 60)) + 'px' });
        }
        var drag = null;
        $win.find('.sol-hdr').on('pointerdown', function (e) {
            if ($(e.target).hasClass('sol-btn')) return;
            var o = $win[0].getBoundingClientRect();
            drag = { dx: e.clientX - o.left, dy: e.clientY - o.top };
            this.setPointerCapture(e.pointerId);
        }).on('pointermove', function (e) {
            if (!drag) return;
            $win.css({ left: Math.max(0, e.clientX - drag.dx) + 'px', top: Math.max(0, e.clientY - drag.dy) + 'px' });
            fitHeight();
        }).on('pointerup pointercancel', function () {
            if (!drag) return;
            drag = null;
            lsSet('bh_solar_pos', parseInt($win.css('left')) + ',' + parseInt($win.css('top')));
        });
    })();

    // que la ventana nunca se salga por abajo de la pantalla
    function fitHeight() {
        var top = $win[0].getBoundingClientRect().top;
        $win.css('max-height', Math.max(160, window.innerHeight - top - 10) + 'px');
    }
    $(window).on('resize', function () { if (open) fitHeight(); });

    function toggle(on) {
        open = on;
        $win.toggleClass('open', on);
        if (on) fitHeight();
        $btn.toggleClass('highlighted', on);
        lsSet('bh_solar_open', on ? '1' : '0');
        if (on) {
            if (Date.now() - loadedAt > 5 * 60 * 1000) load(true); else render();
            if (!timer) timer = setInterval(function () { load(true); }, 5 * 60 * 1000);
        } else if (timer) {
            clearInterval(timer);
            timer = null;
        }
    }

    // ---------------------------------------------------------------
    //  datos
    // ---------------------------------------------------------------
    function load(full) {
        var keys = full ? Object.keys(URL) : ['scales', 'flare', 'kp'];
        if (full && open) $win.find('.sol-time').text('cargando…');
        return Promise.all(keys.map(function (k) {
            return getJSON(URL[k]).then(function (d) { data[k] = d; }).catch(function () { /* se marca como sin datos */ });
        })).then(function () {
            if (full) loadedAt = Date.now();
            updateDot();
            if (open) {
                $win.find('.sol-time').text(hhmm(new Date()) + ' UTC');
                render();
            }
        });
    }

    function current() {
        var o = {};
        var s = data.scales && data.scales['0'];
        o.R = s ? +s.R.Scale : null; o.S = s ? +s.S.Scale : null; o.G = s ? +s.G.Scale : null;
        if (data.sfi && data.sfi[0]) o.sfi = +data.sfi[0].flux;
        if (data.kp && data.kp.length) {
            var last = data.kp[data.kp.length - 1];
            if (Array.isArray(last)) { o.kp = +last[1]; o.a = +last[2]; o.kpTime = last[0]; }
            else { o.kp = +last.Kp; o.a = +last.a_running; o.kpTime = last.time_tag; }
        }
        if (data.flare && data.flare[0]) o.flare = data.flare[0];
        if (data.xray) {
            var xl = data.xray.filter(function (r) { return r.energy === '0.1-0.8nm'; });
            if (xl.length) {
                o.xNow = xl[xl.length - 1].flux;
                o.xMax = Math.max.apply(null, xl.map(function (r) { return r.flux || 0; }));
            }
        }
        if (data.proton) {
            var p = data.proton.filter(function (r) { return r.energy === '>=10 MeV'; });
            if (p.length) o.p10 = p[p.length - 1].flux;
        }
        if (data.wind && data.wind[0]) o.wind = +data.wind[0].proton_speed;
        if (data.mag && data.mag[0]) { o.bt = +data.mag[0].bt; o.bz = +data.mag[0].bz_gsm; }
        return o;
    }

    function updateDot() {
        var c = current();
        var worst = Math.max(c.R || 0, c.S || 0, c.G || 0);
        $btn.find('.sol-dot').css('background', (c.R === null || c.R === undefined) ? '#555' : scaleColor(worst));
        $btn.attr('title', 'Radiación solar y propagación · NOAA R' + (c.R || 0) + ' S' + (c.S || 0) + ' G' + (c.G || 0) +
            (c.flare ? ' · rayos X ' + c.flare.current_class : ''));
    }

    // ---------------------------------------------------------------
    //  pestañas
    // ---------------------------------------------------------------
    function tile(k, v, s, color) {
        return '<div class="sol-tile"><div class="sol-k">' + k + '</div>' +
            '<div class="sol-v"' + (color ? ' style="color:' + color + '"' : '') + '>' + v + '</div>' +
            '<div class="sol-s">' + (s || '&nbsp;') + '</div></div>';
    }
    var ND = '<span style="color:#6b7782">s/d</span>';

    function renderDatos() {
        var c = current();
        var xNow = c.flare ? c.flare.current_class : xclass(c.xNow);
        var h = '<div class="sol-grid">';
        h += tile('Flujo solar', c.sfi ? Math.round(c.sfi) : ND, 'SFI 10,7 cm (sfu)');
        h += tile('Rayos X', xNow || ND, c.xMax ? 'máx 6 h ' + xclass(c.xMax) : 'GOES 0,1-0,8 nm', xcolor(xNow));
        h += tile('Protones', (c.p10 !== undefined) ? (c.p10 < 10 ? c.p10.toFixed(2) : Math.round(c.p10)) : ND,
            '≥10 MeV (pfu) · S' + sScale(c.p10 || 0), scaleColor(sScale(c.p10 || 0)));
        h += tile('Índice Kp', (c.kp !== undefined) ? c.kp.toFixed(1) : ND, (c.a !== undefined) ? 'A = ' + c.a : 'planetario', kpColor(c.kp || 0));
        h += tile('Viento solar', c.wind ? Math.round(c.wind) : ND, 'km/s', c.wind >= 600 ? '#ff9800' : null);
        h += tile('Bz / Bt', (c.bz !== undefined) ? c.bz + ' / ' + c.bt : ND, 'nT (GSM)', c.bz <= -10 ? '#f44336' : c.bz < 0 ? '#ffc107' : null);
        h += '</div>';

        // escalas NOAA hoy y previsión
        var sc = data.scales;
        h += '<div class="sol-h">ESCALAS NOAA</div>';
        if (sc && sc['0']) {
            var lab = { R: 'R · apagones de radio (rayos X)', S: 'S · tormenta de radiación (protones)', G: 'G · tormenta geomagnética' };
            ['R', 'S', 'G'].forEach(function (k) {
                var n = +sc['0'][k].Scale || 0;
                h += '<div class="sol-row"><span>' + lab[k] + '</span><b style="color:' + scaleColor(n) + '">' + k + n + '</b></div>';
            });
            var f = sc['1'];
            if (f) {
                h += '<div class="sol-note">Previsión ' + esc(f.DateStamp) + ': ' +
                    'R1-R2 ' + (f.R.MinorProb || 0) + ' % · R3+ ' + (f.R.MajorProb || 0) + ' % · ' +
                    'S1+ ' + (f.S.Prob || 0) + ' % · G' + (+f.G.Scale || 0) + '</div>';
            }
        } else {
            h += '<div class="sol-note">Sin datos de NOAA.</div>';
        }
        if (c.flare && c.flare.max_class) {
            h += '<div class="sol-note">Último evento de rayos X: inicio ' + esc(c.flare.begin_class || '') + ' ' +
                esc((c.flare.begin_time || '').slice(11, 16)) + ' UTC, máximo ' + esc(c.flare.max_class) + ' ' +
                esc((c.flare.max_time || '').slice(11, 16)) + ' UTC.</div>';
        }
        h += '<div class="sol-note">Fuente: <a href="https://www.swpc.noaa.gov/" target="_blank" rel="noopener">NOAA SWPC</a>. Se actualiza cada 5 min con la ventana abierta.</div>';
        $lcd.html(h);
    }

    function renderGraf() {
        $lcd.html('<div class="sol-h" style="margin-top:0">RAYOS X GOES · 6 h (W/m², escala log)</div><canvas class="cx"></canvas>' +
            '<div class="sol-h">PROTONES ≥10 MeV · 6 h (pfu, escala log)</div><canvas class="cp"></canvas>' +
            '<div class="sol-note">Rayos X: línea continua 0,1-0,8 nm (clase de fulguración), discontinua 0,05-0,4 nm. ' +
            'Una fulguración M o X en la cara diurna absorbe la HF baja (apagón R). Protones ≥10 pfu = tormenta S1 (absorción polar).</div>');
        if (!data.xray || !data.proton) { load(true); return; }
        var xl = data.xray.filter(function (r) { return r.energy === '0.1-0.8nm'; });
        var xs = data.xray.filter(function (r) { return r.energy === '0.05-0.4nm'; });
        chart($lcd.find('canvas.cx')[0], [{ pts: xl, color: '#ffc107' }, { pts: xs, color: '#64b5f6', dash: true }], -9, -3,
            [[-8, 'A'], [-7, 'B'], [-6, 'C'], [-5, 'M'], [-4, 'X']]);
        var p10 = data.proton.filter(function (r) { return r.energy === '>=10 MeV'; });
        var p100 = data.proton.filter(function (r) { return r.energy === '>=100 MeV'; });
        chart($lcd.find('canvas.cp')[0], [{ pts: p10, color: '#ef5350' }, { pts: p100, color: '#ab47bc', dash: true }], -2, 4,
            [[1, 'S1'], [2, 'S2'], [3, 'S3'], [4, 'S4']]);
    }

    function chart(cv, series, lo, hi, marks) {
        var dpr = window.devicePixelRatio || 1, W = cv.clientWidth || 400, H = cv.clientHeight || 150;
        cv.width = W * dpr; cv.height = H * dpr;
        var x = cv.getContext('2d');
        x.scale(dpr, dpr);
        var padL = 26, padR = 6, padT = 6, padB = 16, w = W - padL - padR, h = H - padT - padB;
        var all = [];
        series.forEach(function (s) { s.pts.forEach(function (p) { all.push(Date.parse(p.time_tag)); }); });
        if (!all.length) { x.fillStyle = '#6b7782'; x.fillText('sin datos', padL + 8, padT + 16); return; }
        var t0 = Math.min.apply(null, all), t1 = Math.max.apply(null, all);
        function X(t) { return padL + (t - t0) / Math.max(1, t1 - t0) * w; }
        function Y(v) { var l = Math.log10(Math.max(v, Math.pow(10, lo))); return padT + h - (Math.min(l, hi) - lo) / (hi - lo) * h; }
        x.font = '10px roboto-mono, monospace';
        x.textBaseline = 'middle';
        marks.forEach(function (m) {
            var y = Y(Math.pow(10, m[0]));
            x.strokeStyle = '#1d262e'; x.lineWidth = 1; x.beginPath(); x.moveTo(padL, y); x.lineTo(W - padR, y); x.stroke();
            x.fillStyle = '#6b7782'; x.fillText(m[1], 4, y);
        });
        // horas
        x.textBaseline = 'alphabetic';
        for (var t = Math.ceil(t0 / 3600000) * 3600000; t <= t1; t += 3600000) {
            var xx = X(t);
            x.strokeStyle = '#141b21'; x.beginPath(); x.moveTo(xx, padT); x.lineTo(xx, padT + h); x.stroke();
            x.fillStyle = '#6b7782'; x.fillText(hhmm(new Date(t)).slice(0, 2) + 'h', xx - 8, H - 3);
        }
        series.forEach(function (s) {
            x.strokeStyle = s.color; x.lineWidth = 1.4; x.setLineDash(s.dash ? [4, 3] : []);
            x.beginPath();
            var started = false;
            s.pts.forEach(function (p) {
                if (!(p.flux > 0)) return;
                var px = X(Date.parse(p.time_tag)), py = Y(p.flux);
                if (!started) { x.moveTo(px, py); started = true; } else x.lineTo(px, py);
            });
            x.stroke();
        });
        x.setLineDash([]);
    }

    function renderBandas() {
        var c = current();
        var now = new Date();
        var el = sunElevation(now, LAT, LON);
        var night = el < -6;
        var groups = [['160-80-40 m', 0], ['30-20 m', 1], ['17-15 m', 2], ['12-10 m', 3]];
        var h = '<div class="sol-row"><span>Sol en el QTH (' + LAT.toFixed(2) + ', ' + LON.toFixed(2) + ')</span><b>' +
            el.toFixed(0) + '° · ' + (el > 0 ? 'día' : el > -6 ? 'crepúsculo' : 'noche') + '</b></div>';
        if (c.sfi === undefined || c.kp === undefined) {
            h += '<div class="sol-note">Faltan SFI o Kp para la estimación.</div>';
        } else {
            h += '<table><tr><th>BANDA</th><th>DÍA</th><th>NOCHE</th></tr>';
            groups.forEach(function (g) {
                var d = bandCond(g[1], false, c.sfi, c.kp, c.R || 0), n = bandCond(g[1], true, c.sfi, c.kp, c.R || 0);
                var bold = function (cond, isNow) { return '<td class="c-' + cond + '">' + (isNow ? '<b>▸ ' : '') + COND_TXT[cond] + (isNow ? '</b>' : '') + '</td>'; };
                h += '<tr><td>' + g[0] + '</td>' + bold(d, !night) + bold(n, night) + '</tr>';
            });
            h += '<tr><td>6 m</td><td colspan="2" style="color:#93a0ab">Esporádica E / TEP: mira el DX cluster</td></tr></table>';
            h += '<div class="sol-note">Estimación a partir de SFI ' + Math.round(c.sfi) + ', Kp ' + c.kp.toFixed(1) +
                ' y R' + (c.R || 0) + '. Orientativa: lo que manda es lo que se oye en la cascada.</div>';
        }
        h += '<div class="sol-h">ABSORCIÓN HF (D-RAP)</div>' +
            '<a href="https://www.swpc.noaa.gov/products/d-region-absorption-predictions-d-rap" target="_blank" rel="noopener">' +
            '<img loading="lazy" alt="Mapa D-RAP de absorción" src="' + IMG.drap + '?t=' + Math.floor(Date.now() / 300000) + '"></a>' +
            '<div class="sol-h">MUF EN VIVO (KC2G)</div>' +
            '<a href="https://prop.kc2g.com/" target="_blank" rel="noopener">' +
            '<img loading="lazy" alt="Mapa de MUF" style="background:#fff" src="' + IMG.muf + '?t=' + Math.floor(Date.now() / 900000) + '"></a>';
        $lcd.html(h);
    }

    function renderImg() {
        var t = Math.floor(Date.now() / 900000);
        $lcd.html(
            '<div class="sol-h" style="margin-top:0">SOL AHORA · SDO AIA 193 Å (corona)</div>' +
            '<a href="https://sdo.gsfc.nasa.gov/data/" target="_blank" rel="noopener"><img loading="lazy" alt="Sol en 193 Å" src="' + IMG.sdo193 + '?t=' + t + '"></a>' +
            '<div class="sol-h">MANCHAS SOLARES · SDO HMI</div>' +
            '<img loading="lazy" alt="Manchas solares" src="' + IMG.sdohmi + '?t=' + t + '">' +
            '<div class="sol-h">HAMQSL</div>' +
            '<a href="https://www.hamqsl.com/solar.html" target="_blank" rel="noopener"><img loading="lazy" alt="Panel solar HamQSL" src="' + IMG.hamqsl + '?t=' + t + '"></a>');
    }

    function render() {
        if (!open) return;
        if (tab === 'graf') renderGraf();
        else if (tab === 'bandas') renderBandas();
        else if (tab === 'img') renderImg();
        else renderDatos();
    }

    // punto de color del botón: datos ligeros cada 15 min
    load(false);
    setInterval(function () { if (!open) load(false); }, 15 * 60 * 1000);

    // reabrir si el visitante la dejó abierta
    $win.find('.sol-chip').removeClass('on').filter('[data-tab="' + tab + '"]').addClass('on');
    if (lsGet('bh_solar_open') === '1') setTimeout(function () { toggle(true); }, 1500);

    return true;
};
