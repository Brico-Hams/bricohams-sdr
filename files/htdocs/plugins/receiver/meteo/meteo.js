/*
 * meteo: tiempo en vivo de las estaciones cercanas para OpenWebRX+
 *
 * Autor: BricoHams
 *
 * Botón "METEO" en la barra superior (detrás de SOL). La ventana muestra
 * las estaciones AEMET más cercanas al QTH (temperatura, humedad, viento,
 * racha, presión, lluvia, máx/mín y la curva de 24 h) y la previsión de
 * 3 días de Open-Meteo. El botón enseña la temperatura de la estación
 * más cercana.
 *
 * Los datos los prepara en el servidor bricohams-meteo.py (cada 10 min)
 * en static/plugins/receiver/meteo/meteo.json: así no hay problemas de
 * CORS y la clave de AEMET no sale nunca al navegador.
 *
 * Ajustes opcionales en init.js:
 *   window.meteo_config = { url: 'static/plugins/receiver/meteo/meteo.json', after: '#bh-solar-button' };
 */

Plugins.meteo._version = '1.0.0';
Plugins.meteo._author='BricoHams';
Plugins.meteo.no_css = true;

Plugins.meteo.init = function () {
    var cfg = window.meteo_config || {};
    var DATA_URL = cfg.url || 'static/plugins/receiver/meteo/meteo.json';
    var SENSOR_URL = cfg.sensor === undefined ? 'static/plugins/receiver/meteo/sensor.json' : cfg.sensor;
    var CAJA_URL = cfg.caja === undefined ? 'static/plugins/receiver/meteo/caja.json' : cfg.caja;
    var AFTER = cfg.after || '#bh-solar-button';

    var css =
        '#bh-meteo-button{position:relative}' +
        '#bh-meteo-button svg{width:18px;height:18px}' +
        '#bh-meteo{position:fixed;top:90px;left:460px;z-index:1002;width:440px;max-width:calc(100vw - 16px);' +
            'display:none;flex-direction:column;padding:8px;border-radius:8px;color:#cfd4d9;font:12px roboto-mono,monospace;' +
            'background:linear-gradient(#2a2e33,#17191d);box-shadow:inset 0 1px 0 rgba(255,255,255,.07),0 0 0 1px #060708,0 6px 18px rgba(0,0,0,.65)}' +
        '#bh-meteo.open{display:flex}' +
        '#bh-meteo .mt-hdr{display:flex;align-items:center;gap:6px;padding:0 2px 6px;cursor:move;user-select:none;touch-action:none}' +
        '#bh-meteo .mt-title{flex:1;color:#93a0ab;letter-spacing:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}' +
        '#bh-meteo .mt-time{color:#6b7782;font-size:11px}' +
        '#bh-meteo .mt-btn{cursor:pointer;color:#93a0ab;padding:0 4px;font-size:15px;line-height:1}' +
        '#bh-meteo .mt-btn:hover{color:#fff}' +
        '#bh-meteo .mt-lcd{overflow:auto;min-height:0;border-radius:5px;padding:8px;background:#0b0f12;box-shadow:inset 0 2px 8px rgba(0,0,0,.9),inset 0 0 2px #000}' +
        '#bh-meteo .mt-st{background:#10161b;border-radius:4px;padding:8px;box-shadow:0 0 0 1px #1d242b;margin-bottom:6px}' +
        '#bh-meteo .mt-st.near{box-shadow:0 0 0 1px #A6192E}' +
        '#bh-meteo .mt-top{display:flex;justify-content:space-between;gap:8px;align-items:baseline}' +
        '#bh-meteo .mt-name{color:#e8edf1;font-weight:bold;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}' +
        '#bh-meteo .mt-sub{color:#6b7782;font-size:10px;white-space:nowrap}' +
        '#bh-meteo .mt-body{display:flex;gap:10px;align-items:center;margin-top:4px}' +
        '#bh-meteo .mt-temp{font-size:28px;color:#fff;min-width:92px}' +
        '#bh-meteo .mt-temp small{font-size:11px;color:#93a0ab;display:block}' +
        '#bh-meteo .mt-kv{display:grid;grid-template-columns:auto auto;gap:1px 10px;font-size:11px;flex:1}' +
        '#bh-meteo .mt-kv span:nth-child(odd){color:#6b7782}' +
        '#bh-meteo .mt-arrow{display:inline-block;transition:transform .3s}' +
        '#bh-meteo canvas{width:100%;height:46px;display:block;margin-top:4px}' +
        '#bh-meteo .mt-h{color:#93a0ab;letter-spacing:1px;margin:8px 0 4px;font-size:11px}' +
        '#bh-meteo .mt-days{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}' +
        '#bh-meteo .mt-day{background:#10161b;border-radius:4px;padding:6px;text-align:center;box-shadow:0 0 0 1px #1d242b}' +
        '#bh-meteo .mt-day b{font-size:20px;display:block}' +
        '#bh-meteo .mt-note{color:#6b7782;font-size:10px;margin-top:6px;line-height:1.4}' +
        '#bh-meteo a{color:#64b5f6}' +
        '@media (max-width:600px){#bh-meteo{left:8px!important;top:60px!important}}';
    var st = document.createElement('style');
    st.textContent = css;
    document.head.appendChild(st);

    function esc(s) { return String(s === undefined || s === null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
    function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
    function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* sin almacenamiento */ } }
    function num(v, d) { return (typeof v === 'number' && isFinite(v)) ? v.toFixed(d === undefined ? 1 : d) : '—'; }
    function fmtTime(iso) {
        if (!iso) return '';
        var d = new Date(iso);
        if (isNaN(d)) return '';
        return d.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Madrid' });
    }
    function compass(deg) {
        if (typeof deg !== 'number') return '';
        return ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSO', 'SO', 'OSO', 'O', 'ONO', 'NO', 'NNO'][Math.round(deg / 22.5) % 16];
    }
    function tempColor(t) {
        if (typeof t !== 'number') return '#fff';
        return t >= 35 ? '#f44336' : t >= 28 ? '#ff9800' : t >= 20 ? '#ffc107' : t >= 10 ? '#8bc34a' : t >= 0 ? '#64b5f6' : '#b39ddb';
    }
    // códigos WMO de Open-Meteo
    function wmo(code) {
        var m = {
            0: ['☀️', 'Despejado'], 1: ['🌤️', 'Casi despejado'], 2: ['⛅', 'Nubes y claros'], 3: ['☁️', 'Cubierto'],
            45: ['🌫️', 'Niebla'], 48: ['🌫️', 'Niebla con escarcha'],
            51: ['🌦️', 'Llovizna débil'], 53: ['🌦️', 'Llovizna'], 55: ['🌧️', 'Llovizna intensa'],
            61: ['🌦️', 'Lluvia débil'], 63: ['🌧️', 'Lluvia'], 65: ['🌧️', 'Lluvia fuerte'],
            66: ['🌧️', 'Lluvia helada'], 67: ['🌧️', 'Lluvia helada fuerte'],
            71: ['🌨️', 'Nieve débil'], 73: ['🌨️', 'Nieve'], 75: ['❄️', 'Nieve fuerte'], 77: ['🌨️', 'Granos de nieve'],
            80: ['🌦️', 'Chubascos'], 81: ['🌧️', 'Chubascos fuertes'], 82: ['⛈️', 'Chubascos muy fuertes'],
            85: ['🌨️', 'Chubascos de nieve'], 86: ['❄️', 'Chubascos de nieve fuertes'],
            95: ['⛈️', 'Tormenta'], 96: ['⛈️', 'Tormenta con granizo'], 99: ['⛈️', 'Tormenta con granizo fuerte']
        };
        return m[code] || ['🌡️', ''];
    }

    var THERMO = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">' +
        '<path d="M10 14.5V5a2 2 0 1 1 4 0v9.5a4 4 0 1 1-4 0z"/><path d="M12 9v7"/><path d="M17 6h3M17 9h2M17 12h3"/></svg>';
    var $btn = $('<div class="button" id="bh-meteo-button" title="Tiempo en vivo de las estaciones cercanas">' +
        THERMO + '<br><span class="mt-label">METEO</span></div>');

    function placeButton(tries) {
        var $after = $(AFTER);
        if (!$after.length) $after = $('#owrx-rig-dx-button');
        if ($after.length) { $after.after($btn); return; }
        if (tries > 0) { setTimeout(function () { placeButton(tries - 1); }, 500); return; }
        var $bar = $('.openwebrx-main-buttons').first();
        var $status = $bar.children('.button').filter(function () { return /Estado|Status/.test($(this).text()); }).first();
        if ($status.length) $status.after($btn); else $bar.append($btn);
    }
    placeButton(20);

    var $win = $('<div id="bh-meteo" role="dialog" aria-label="Tiempo en vivo">' +
        '<div class="mt-hdr"><span class="mt-title">🌡 METEO · VEGA DEL SEGURA</span>' +
        '<span class="mt-time"></span><span class="mt-btn mt-reload" title="Actualizar">⟳</span>' +
        '<span class="mt-btn mt-close" title="Cerrar">×</span></div>' +
        '<div class="mt-lcd"><div class="mt-note">Cargando…</div></div></div>');
    $('body').append($win);
    var $lcd = $win.find('.mt-lcd');
    var data = null, sensor = null, caja = null, open = false;

    function fitHeight() {
        var top = $win[0].getBoundingClientRect().top;
        $win.css('max-height', Math.max(160, window.innerHeight - top - 10) + 'px');
    }
    $(window).on('resize', function () { if (open) fitHeight(); });

    (function () {
        var p = (lsGet('bh_meteo_pos') || '').split(',');
        if (p.length === 2 && window.innerWidth > 600) {
            $win.css({ left: Math.max(0, Math.min(+p[0], window.innerWidth - 120)) + 'px',
                       top: Math.max(0, Math.min(+p[1], window.innerHeight - 60)) + 'px' });
        }
        var drag = null;
        $win.find('.mt-hdr').on('pointerdown', function (e) {
            if ($(e.target).hasClass('mt-btn')) return;
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
            lsSet('bh_meteo_pos', parseInt($win.css('left')) + ',' + parseInt($win.css('top')));
        });
    })();

    function toggle(on) {
        open = on;
        $win.toggleClass('open', on);
        $btn.toggleClass('highlighted', on);
        lsSet('bh_meteo_open', on ? '1' : '0');
        if (on) { fitHeight(); render(); load(); }
    }
    Plugins.meteo._toggle = toggle;
    $btn.on('click', function () { toggle(!open); });
    $win.find('.mt-close').on('click', function () { toggle(false); });
    $win.find('.mt-reload').on('click', load);

    function fresco(s) { return s && s.updated && (Date.now() - Date.parse(s.updated)) < 15 * 60 * 1000; }

    function loadSensor() {
        if (!SENSOR_URL) return Promise.resolve();
        return fetch(SENSOR_URL + (SENSOR_URL.indexOf('?') < 0 ? '?' : '&') + 't=' + Date.now(), { cache: 'no-store' })
            .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
            .then(function (d) { sensor = d; })
            .catch(function () { sensor = null; })
            .then(function () {
                if (!CAJA_URL) return;
                return fetch(CAJA_URL + '?t=' + Date.now(), { cache: 'no-store' })
                    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
                    .then(function (d) { caja = d; })
                    .catch(function () { caja = null; });
            });
    }

    function load() {
        loadSensor().then(function () { updateButton(); render(); });
        return fetch(DATA_URL + (DATA_URL.indexOf('?') < 0 ? '?' : '&') + 't=' + Date.now(), { cache: 'no-store' })
            .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
            .then(function (d) { data = d; updateButton(); render(); })
            .catch(function () {
                if (open && !data && !sensor) $lcd.html('<div class="mt-note">No hay datos todavía. Comprueba en el servidor: <code>systemctl status bricohams-meteo.timer</code></div>');
            });
    }

    function nearest() {
        if (!data || !data.stations) return null;
        var ok = data.stations.filter(function (s) { return typeof s.ta === 'number'; });
        ok.sort(function (a, b) { return (a.dist_km || 999) - (b.dist_km || 999); });
        return ok[0] || null;
    }

    function updateButton() {
        var n = nearest();
        var t = fresco(sensor) ? sensor.ta : n ? n.ta : (data && data.model && data.model.current ? data.model.current.temperature_2m : null);
        if (fresco(sensor)) {
            $btn.attr('title', sensor.name + ': ' + num(sensor.ta) + ' °C' + (typeof sensor.hr === 'number' ? ', ' + num(sensor.hr, 0) + ' % HR' : '') + ', ' + num(sensor.pres_nmar) + ' hPa');
        }
        $btn.find('.mt-label').text(typeof t === 'number' ? t.toFixed(1) + '°' : 'METEO')
            .css('color', typeof t === 'number' ? tempColor(t) : '');
        if (n && !fresco(sensor)) $btn.attr('title', n.name + ': ' + num(n.ta) + ' °C, ' + num(n.hr, 0) + ' % HR, viento ' + num(n.vv_kmh, 0) + ' km/h ' + compass(n.dv) + ' (' + fmtTime(n.time) + ')');
    }

    function spark(cv, hist) {
        var pts = (hist || []).filter(function (h) { return typeof h.ta === 'number'; });
        var dpr = window.devicePixelRatio || 1, W = cv.clientWidth || 380, H = cv.clientHeight || 46;
        cv.width = W * dpr; cv.height = H * dpr;
        var x = cv.getContext('2d');
        x.scale(dpr, dpr);
        if (pts.length < 2) return;
        var t0 = Date.parse(pts[0].t), t1 = Date.parse(pts[pts.length - 1].t);
        var v = pts.map(function (p) { return p.ta; });
        var lo = Math.floor(Math.min.apply(null, v)) - 1, hi = Math.ceil(Math.max.apply(null, v)) + 1;
        function X(t) { return 2 + (Date.parse(t) - t0) / Math.max(1, t1 - t0) * (W - 34); }
        function Y(val) { return H - 4 - (val - lo) / (hi - lo) * (H - 8); }
        var g = x.createLinearGradient(0, 0, 0, H);
        g.addColorStop(0, 'rgba(242,107,33,.35)'); g.addColorStop(1, 'rgba(242,107,33,0)');
        x.beginPath(); x.moveTo(X(pts[0].t), H);
        pts.forEach(function (p) { x.lineTo(X(p.t), Y(p.ta)); });
        x.lineTo(X(pts[pts.length - 1].t), H); x.closePath(); x.fillStyle = g; x.fill();
        x.beginPath();
        pts.forEach(function (p, i) { if (i) x.lineTo(X(p.t), Y(p.ta)); else x.moveTo(X(p.t), Y(p.ta)); });
        x.strokeStyle = '#F26B21'; x.lineWidth = 1.5; x.stroke();
        x.fillStyle = '#6b7782'; x.font = '10px roboto-mono, monospace';
        x.fillText(hi + '°', W - 28, 10); x.fillText(lo + '°', W - 28, H - 2);
    }

    function render() {
        if (!open || (!data && !sensor)) return;
        data = data || { stations: [] };
        $win.find('.mt-time').text(data.updated ? fmtTime(data.updated) : '');
        var h = '';
        if (sensor) {
            var ok = fresco(sensor);
            h += '<div class="mt-st near" style="box-shadow:0 0 0 1px #F26B21">' +
                '<div class="mt-top"><span class="mt-name">🏠 ' + esc(sensor.name) + '</span>' +
                '<span class="mt-sub">' + esc(sensor.chip || '') + (sensor.aprs ? ' · APRS ' + esc(sensor.aprs) : '') + ' · ' + fmtTime(sensor.updated) + '</span></div>';
            if (!ok) h += '<div class="mt-note" style="color:#ff9800">Sin datos recientes del sensor (systemctl status bricohams-wx)</div>';
            h += '<div class="mt-body"><div class="mt-temp" style="color:' + tempColor(sensor.ta) + '">' + num(sensor.ta) + '°' +
                '<small>' + (typeof sensor.dew === 'number' ? 'rocío ' + num(sensor.dew) + '°' : '&nbsp;') + '</small></div><div class="mt-kv">' +
                (typeof sensor.hr === 'number' ? '<span>Humedad</span><span>' + num(sensor.hr, 0) + ' %</span>' : '') +
                '<span>Presión (mar)</span><span>' + num(sensor.pres_nmar, 1) + ' hPa</span>' +
                '<span>Presión (QTH)</span><span>' + num(sensor.pres, 1) + ' hPa</span>' +
                (sensor.viento ? '<span>Viento</span><span>' + num(sensor.viento.vel_ms * 3.6, 0) + ' km/h ' + compass(sensor.viento.dir) +
                    ' · racha ' + num(sensor.viento.racha_ms * 3.6, 0) + '</span>' : '') +
                (sensor.lluvia ? '<span>Lluvia</span><span>' + num(sensor.lluvia['1h'], 1) + ' mm/h · hoy ' + num(sensor.lluvia.hoy, 1) + ' mm</span>' : '') +
                '</div></div><canvas data-sensor="1"></canvas>' +
                (caja && typeof caja.ciclo === 'number' ? '<div class="mt-note">📦 Caja: ' + (typeof caja.t_caja === 'number' ? num(caja.t_caja) + ' °C' : '—') +
                    ' · CPU ' + num(caja.t_cpu, 0) + ' °C · ventiladores ' + caja.ciclo + ' %' + (caja.alarma ? ' · <b style="color:#ff5252">ventilador ' + esc(caja.alarma) + ' parado</b>' : '') + '</div>' : '') +
                '</div>';
        }
        var n = nearest();
        (data.stations || []).forEach(function (s, i) {
            var has = typeof s.ta === 'number';
            h += '<div class="mt-st' + (n && s.id === n.id ? ' near' : '') + '">' +
                '<div class="mt-top"><span class="mt-name">' + esc(s.name) + '</span>' +
                '<span class="mt-sub">' + (s.dist_km !== undefined ? num(s.dist_km, 1) + ' km · ' : '') + esc(s.source || '') +
                (s.time ? ' · ' + fmtTime(s.time) : '') + '</span></div>';
            if (!has) {
                h += '<div class="mt-note">' + esc(s.error || 'Sin datos') + '</div></div>';
                return;
            }
            h += '<div class="mt-body"><div class="mt-temp" style="color:' + tempColor(s.ta) + '">' + num(s.ta) + '°' +
                '<small>máx ' + num(s.tamax) + ' · mín ' + num(s.tamin) + '</small></div>' +
                '<div class="mt-kv">' +
                '<span>Humedad</span><span>' + num(s.hr, 0) + ' %</span>' +
                '<span>Viento</span><span>' + (typeof s.dv === 'number' ? '<span class="mt-arrow" style="transform:rotate(' + (s.dv + 180) + 'deg)">↑</span> ' + compass(s.dv) + ' ' : '') + num(s.vv_kmh, 0) + ' km/h</span>' +
                '<span>Racha</span><span>' + num(s.vmax_kmh, 0) + ' km/h</span>' +
                '<span>Presión</span><span>' + num(s.pres_nmar !== undefined && s.pres_nmar !== null ? s.pres_nmar : s.pres, 1) + ' hPa</span>' +
                '<span>Lluvia</span><span>' + num(s.prec_1h, 1) + ' mm/h · ' + num(s.prec_24h, 1) + ' mm/24 h</span>' +
                '</div></div><canvas data-i="' + i + '"></canvas></div>';
        });
        var m = data.model;
        if (m && m.current) {
            var c = m.current, w = wmo(c.weather_code);
            h += '<div class="mt-h">AHORA EN EL QTH (modelo) · ' + w[0] + ' ' + esc(w[1]) + '</div>' +
                '<div class="mt-note" style="margin-top:0;color:#cfd4d9">' + num(c.temperature_2m) + ' °C (sensación ' + num(c.apparent_temperature) + ' °C) · ' +
                num(c.relative_humidity_2m, 0) + ' % · viento ' + num(c.wind_speed_10m, 0) + ' km/h ' + compass(c.wind_direction_10m) +
                ' (racha ' + num(c.wind_gusts_10m, 0) + ') · nubes ' + num(c.cloud_cover, 0) + ' %</div>';
        }
        if (m && m.daily && m.daily.length) {
            h += '<div class="mt-h">PREVISIÓN</div><div class="mt-days">';
            m.daily.slice(0, 3).forEach(function (d) {
                var w = wmo(d.weather_code);
                var dd = new Date(d.date + 'T12:00:00');
                h += '<div class="mt-day"><div>' + esc(dd.toLocaleDateString('es-ES', { weekday: 'short', day: 'numeric' })) + '</div>' +
                    '<b title="' + esc(w[1]) + '">' + w[0] + '</b>' +
                    '<span style="color:#ff9800">' + num(d.tmax, 0) + '°</span> / <span style="color:#64b5f6">' + num(d.tmin, 0) + '°</span>' +
                    '<div class="mt-note" style="margin-top:2px">💧 ' + num(d.precip_prob, 0) + ' %</div></div>';
            });
            h += '</div>';
        }
        h += '<div class="mt-note">' + (sensor ? 'Sensor propio ' + esc(sensor.chip || '') + ' en el mástil. ' : '') + 'Observación: <a href="https://www.aemet.es/es/eltiempo/observacion/ultimosdatos?k=mur" target="_blank" rel="noopener">AEMET OpenData</a>. ' +
            'Modelo y previsión: <a href="https://open-meteo.com/" target="_blank" rel="noopener">Open-Meteo</a>. Se actualiza cada 10 min.</div>' +
            '<div class="mt-note">🌦️ <a href="/bricohams/clima.html" target="_blank" rel="noopener">Clima en red</a>: estaciones WX cercanas por APRS, balizas WSPR y pases de satélite grabados.</div>';
        if (data.errors && data.errors.length) h += '<div class="mt-note">Avisos: ' + esc(data.errors.join(' · ')) + '</div>';
        $lcd.html(h);
        $lcd.find('canvas').each(function () {
            if ($(this).data('sensor')) spark(this, sensor.history);
            else spark(this, data.stations[+$(this).data('i')].history);
        });
    }

    load();
    setInterval(load, 5 * 60 * 1000);
    if (lsGet('bh_meteo_open') === '1') setTimeout(function () { toggle(true); }, 1500);
    return true;
};
