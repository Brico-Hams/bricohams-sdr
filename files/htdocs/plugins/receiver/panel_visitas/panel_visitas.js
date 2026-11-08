/*
 * panel_visitas v1.1.0: tarjetas «TU CONEXIÓN» y «VISITAS» en la cabecera de OpenWebRX+
 * Autor: BricoHams
 * Datos: visitas.json (total, hoy, ahora, países 30 días) y /bricohams/api/mi-ip (IP enmascarada y país).
 * No guarda nada, no envía datos a terceros y no muestra identidad.
 * Ajustes opcionales (window.panel_visitas_config): json, api_ip, banderas (12), ocultar_lan (true), refresco (60 s).
 */

Plugins.panel_visitas = Plugins.panel_visitas || {};
Plugins.panel_visitas._version = '1.1.0';
Plugins.panel_visitas._author = 'BricoHams';
Plugins.panel_visitas.no_css = true;

Plugins.panel_visitas.init = function () {
    var cfg = window.panel_visitas_config || {};
    var JSON_URL = cfg.json || 'static/plugins/receiver/visitas/visitas.json';
    var API_IP = cfg.api_ip || '/bricohams/api/mi-ip';
    var MAXB = cfg.banderas || 12;
    var SIN_LAN = cfg.ocultar_lan !== false;
    var REFRESCO = Math.max(30, +cfg.refresco || 60) * 1000;

    function n(x) { return (+x || 0).toLocaleString('es-ES'); }
    function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return '&#' + c.charCodeAt(0) + ';'; }); }
    // Emoji generado solo desde dos letras validadas: seguro como HTML
    function flag(cc) {
        if (!/^[A-Za-z]{2}$/.test(cc || '')) return '🌐';
        return String.fromCodePoint.apply(null, cc.toUpperCase().split('').map(function (c) { return 0x1F1E6 + c.charCodeAt(0) - 65; }));
    }
    function pais(cc) {
        try { return new Intl.DisplayNames(['es'], { type: 'region' }).of(cc) || cc; } catch (e) { return cc; }
    }
    function navegador() {
        var ua = navigator.userAgent, m;
        if ((m = ua.match(/Edg\/(\d+)/))) return 'Edge ' + m[1];
        if ((m = ua.match(/OPR\/(\d+)/))) return 'Opera ' + m[1];
        if ((m = ua.match(/SamsungBrowser\/(\d+)/))) return 'Samsung ' + m[1];
        if ((m = ua.match(/Firefox\/(\d+)/))) return 'Firefox ' + m[1];
        if ((m = ua.match(/Chrome\/(\d+)/))) return 'Chrome ' + m[1];
        if ((m = ua.match(/Version\/(\d+).*Safari/))) return 'Safari ' + m[1];
        return 'Navegador';
    }
    function sistema() {
        var ua = navigator.userAgent, m;
        if (/Windows NT 10/.test(ua)) return 'Windows 10/11';
        if ((m = ua.match(/Windows NT ([\d.]+)/))) return 'Windows ' + m[1];
        if ((m = ua.match(/Android ([\d.]+)/))) return 'Android ' + m[1];
        if ((m = ua.match(/(iPhone|iPad).*OS (\d+)/))) return 'iOS ' + m[2];
        if (/Mac OS X/.test(ua)) return 'macOS';
        if (/CrOS/.test(ua)) return 'ChromeOS';
        if (/Linux/.test(ua)) return 'Linux';
        return 'Sistema';
    }
    var IDIOMA = navigator.language || 'es-ES';

    // Paleta oficial sobre la cabecera oscura; sin text-shadow heredado de la foto
    var css =
        '#bh-pv{display:flex;flex-wrap:wrap;gap:12px;margin:10px 0 6px;font-family:sans-serif;text-shadow:none}' +
        '#bh-pv .pv-card{background:#1C2329;color:#F6F8FA;border:1px solid #F26B1D;border-radius:8px;padding:12px 16px;' +
            'min-width:220px;line-height:1.5;text-shadow:none;box-shadow:0 2px 8px rgba(0,0,0,.35)}' +
        '#bh-pv .pv-tit{font-size:13px;font-weight:700;letter-spacing:1.5px;color:#FFA06A;text-transform:uppercase}' +
        '#bh-pv .pv-ip{font:700 17px/1.5 monospace;color:#F6F8FA}' +
        '#bh-pv .pv-big{font:700 22px/1.2 sans-serif;color:#F6F8FA;margin-left:8px;letter-spacing:0}' +
        '#bh-pv .pv-sub{font-size:13px;color:#BAC4CC}' +
        '#bh-pv .pv-line{font-size:14px}' +
        '#bh-pv .pv-grid{display:grid;grid-template-columns:repeat(4,auto);justify-content:start;gap:4px 16px;margin-top:8px;font-size:14px}' +
        '#bh-pv .pv-grid span{white-space:nowrap}' +
        '#bh-pv .pv-priv{font-size:12px;margin-top:6px}' +
        '#bh-pv .pv-priv a{color:#FFA06A}' +
        '#bh-pv .pv-priv a:focus-visible{outline:2px solid #FFC18F;outline-offset:2px}' +
        '@media (max-width:600px){#bh-pv .pv-card{min-width:0;flex:1 1 100%}#bh-pv .pv-grid{grid-template-columns:repeat(3,auto)}}';
    var st = document.createElement('style');
    st.textContent = css;
    document.head.appendChild(st);

    var $pv = $('<div id="bh-pv" aria-live="polite"></div>');
    var $con = $('<div class="pv-card" id="bh-pv-con"></div>').appendTo($pv);
    var $vis = $('<div class="pv-card" id="bh-pv-vis"></div>').appendTo($pv);

    function colocar(intentos) {
        var $d = $('.webrx-rx-photo-desc, #webrx-rx-photo-desc').first();
        if ($d.length) { if (!$pv.parent().is($d)) $d.prepend($pv); return; }
        if (intentos > 0) setTimeout(function () { colocar(intentos - 1); }, 500);
    }
    colocar(30);

    var ip = null, datos = null;

    function pintarConexion() {
        var lineas = '<div class="pv-tit">Tu conexión</div>';
        if (ip && ip.ip) {
            lineas += '<div class="pv-ip">' + esc(ip.ip) + '</div>';
            if (ip.pais) lineas += '<div class="pv-line">' + flag(ip.pais) + ' ' + esc(pais(ip.pais)) + '</div>';
        } else {
            lineas += '<div class="pv-ip">' + (ip === false ? 'no disponible' : '…') + '</div>';
        }
        lineas += '<div class="pv-line">' + esc(navegador()) + ' · ' + esc(sistema()) + '</div>';
        lineas += '<div class="pv-sub">Idioma: ' + esc(IDIOMA) + '</div>';
        $con.html(lineas);
    }

    function pintarVisitas() {
        if (!datos) { $vis.html('<div class="pv-tit">Visitas</div><div class="pv-sub">cargando…</div>'); return; }
        var lista = (datos.paises_30d || []).filter(function (p) { return !(SIN_LAN && p.cc === 'LAN'); });
        var grid = lista.slice(0, MAXB).map(function (p) {
            return '<span title="' + esc(p.pais && p.pais.length > 2 ? p.pais : pais(p.cc)) + '">' + flag(p.cc) + ' ' + n(p.n) + '</span>';
        }).join('');
        $vis.html(
            '<div class="pv-tit">Visitas<span class="pv-big">' + n(datos.total) + '</span></div>' +
            '<div class="pv-sub">' + n(datos.hoy) + ' hoy · ' + n(datos.ahora) + ' ahora · ' + n(lista.length) + ' países (30 días)</div>' +
            '<div class="pv-grid">' + grid + '</div>' +
            '<div class="pv-priv"><a href="' + esc((window.visitas_config || {}).privacidad || '/bricohams/privacidad.html') + '" target="_blank" rel="noopener">Privacidad</a></div>'
        );
    }

    function cargarIp() {
        fetch(API_IP, { cache: 'no-store', credentials: 'same-origin' })
            .then(function (r) { if (!r.ok) throw 0; return r.json(); })
            .then(function (d) { ip = (d && typeof d.ip === 'string') ? d : false; })
            .catch(function () { ip = false; })
            .then(pintarConexion);
    }
    function cargarVisitas() {
        fetch(JSON_URL + '?_=' + Date.now(), { cache: 'no-store' })
            .then(function (r) { if (!r.ok) throw 0; return r.json(); })
            .then(function (d) { datos = d || {}; })
            .catch(function () { /* se mantiene lo último */ })
            .then(pintarVisitas);
    }

    pintarConexion();
    pintarVisitas();
    cargarIp();
    cargarVisitas();
    setInterval(cargarVisitas, REFRESCO);
    return true;
};
