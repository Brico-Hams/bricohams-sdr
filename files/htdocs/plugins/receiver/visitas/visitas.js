/*
 * visitas: oyentes conectados y contador de visitas (OpenWebRX+)
 *
 * Autor: BricoHams (v4)
 *
 * Muestra junto al nombre del receptor «👥 3 ahora 🇪🇸🇪🇸🇮🇹 · 1.234 visitas» y,
 * al pulsar, un resumen por países de los últimos 30 días.
 * Los datos los genera bricohams-visitas (avisos de conexión de OpenWebRX+ por
 * MQTT + GeoIP local) en static/plugins/receiver/visitas/visitas.json.
 * En la web pública solo salen países y totales: nunca IPs.
 * Incluye el enlace al aviso de privacidad (obligatorio al registrar visitas).
 */

Plugins.visitas._version = '1.2.0';
Plugins.visitas._author='BricoHams';
Plugins.visitas.no_css = true;

Plugins.visitas.init = function () {
    var cfg = window.visitas_config || {};
    var URL = cfg.url || 'static/plugins/receiver/visitas/visitas.json';
    var PRIV = cfg.privacidad || '/bricohams/privacidad.html';
    var API_V = cfg.api_visitas || '/bricohams/api/visitas';
    var API_IP = cfg.api_mi_ip || '/bricohams/api/mi-ip';
    // Misma clave que la portada: una visita por pestaña, sin contarla dos veces al pasar de una a otra
    var CLAVE = 'bh_visita';
    var contar = (window.identificacion_config || {}).enabled !== false;
    function flag(cc) { return (Plugins.banderas && cc) ? Plugins.banderas.bandera(cc) : (cc || ''); }
    function n(x) { return (x || 0).toLocaleString('es-ES'); }
    function nombrePais(cc) {
        try { return new Intl.DisplayNames(['es'], { type: 'region' }).of(cc) || cc; } catch (e) { return cc; }
    }

    $('<style>').text(
        '#bh-visitas{display:inline-block;margin-left:10px;padding:1px 8px;border-radius:999px;background:var(--surface,#1C2329);border:1px solid var(--border,#38434C);' +
        'font:600 12px/1.6 var(--bh-font-ui,system-ui,sans-serif);color:var(--text,#F6F8FA);cursor:pointer;vertical-align:middle}' +
        '#bh-visitas:focus-visible,#bh-banner-info a:focus-visible{outline:2px solid var(--focus,#FFC18F);outline-offset:2px}' +
        '#bh-banner-info{display:block;margin-top:2px;font:12px/1.5 var(--bh-font-ui,system-ui,sans-serif);color:var(--text-muted,#BAC4CC)}' +
        '#bh-banner-info b{color:var(--text,#F6F8FA);font-weight:600}#bh-banner-info .bh-sep{margin:0 6px;color:var(--brand-orange,#F26B1D)}' +
        '#bh-visitas-pop{position:fixed;top:60px;left:12px;z-index:9998;display:none;background:var(--surface,#1C2329);color:var(--text,#F6F8FA);' +
        'border:1px solid var(--brand-orange,#F26B1D);border-radius:12px;padding:8px 12px;font:12px/1.5 var(--bh-font-ui,system-ui,sans-serif);max-height:60vh;overflow:auto}' +
        '#bh-visitas-pop a{color:var(--link,#FFA06A)}'
    ).appendTo('head');
    var $b = $('<span id="bh-visitas" role="button" tabindex="0" title="Oyentes conectados y visitas">👥 …</span>');
    var $info = $('<span id="bh-banner-info" aria-live="polite"></span>');
    var $pop = $('<div id="bh-visitas-pop"></div>').appendTo('body');

    // El banner real de OpenWebRX+ (título + descripción con la presentación del proyecto) puede tardar o
    // reconstruirse según el tema: se reintenta y, sin él, la píldora queda fija en pantalla.
    function colocar(intentos) {
        var $t = $('.webrx-rx-title').first();
        if ($t.length) {
            if (!$b.parent().is($t)) $t.append($b);
            var $d = $('.webrx-rx-desc').first();
            if ($d.length) { if (!$info.prev().is($d)) $d.after($info); }
            else if (!$info.parent().is($t.parent())) $t.after($info);
            return;
        }
        if (intentos > 0) { setTimeout(function () { colocar(intentos - 1); }, 500); return; }
        $('body').append($b.css({ position: 'fixed', left: 12, top: 4, zIndex: 9999 }));
        $('body').append($info.css({ position: 'fixed', left: 12, top: 28, zIndex: 9999 }));
    }
    colocar(20);
    var datos = null, total = null, propia = null;

    function pintarResumen() {
        var resumen = datos || {};
        var filas = (resumen.paises_30d || []).slice(0, 25).map(function (p) {
            return '<tr><td>' + flag(p.cc) + ' ' + $('<i>').text(p.pais || p.cc).html() + '</td><td style="text-align:right">' + n(p.n) + '</td></tr>';
        }).join('');
        $pop.html('<b>👥 Oyentes · BricoHams SDR</b> <span style="float:right;cursor:pointer" onclick="$(\'#bh-visitas-pop\').hide()">✕</span><br>' +
            'Ahora: <b>' + n(resumen.ahora) + '</b> · Hoy: <b>' + n(resumen.hoy) + '</b> · Total: <b>' + n(typeof resumen.total === 'number' ? resumen.total : total) + '</b><br>' +
            '<table style="margin-top:4px">' + filas + '</table>' +
            '<div style="opacity:.8;margin-top:6px">Visitas de los últimos 30 días por país. <a href="' + PRIV + '" target="_blank">Privacidad</a></div>');
        $pop.append($('<div>').append($info.contents().clone()));
    }
    function abrirResumen() {
        pintarResumen();
        $pop.toggle();
        $b.attr('aria-expanded', $pop.is(':visible') ? 'true' : 'false');
    }
    $b.on('click', function (e) { e.stopPropagation(); abrirResumen(); })
      .on('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); abrirResumen(); } });

    function parte(etiqueta, valor) {
        return $('<span>').append(document.createTextNode(etiqueta + ' '), $('<b>').text(valor));
    }
    function pintarInfo() {
        // «Visitas» = conexiones al receptor (visitas.json, histórico); el contador de la portada es otro, y se muestra aparte
        var t = datos && typeof datos.total === 'number' ? datos.total : total;
        var partes = [parte('👥 Visitas', t === null || t === undefined ? 'no disponible' : n(t))];
        if (total) partes.push(parte('🏠 Portal', n(total)));
        if (propia && propia.ip) {
            partes.push(parte('🌐 Tu IP', propia.ip));
            if (propia.pais) partes.push(parte(flag(propia.pais) + ' País', nombrePais(propia.pais) + ' (' + propia.pais + ')'));
            else partes.push(parte('🌐 País', 'no disponible'));
        } else if (propia === false) {
            partes.push(parte('🌐 Tu IP', 'no disponible'));
        }
        // Solo la identidad registrada en este navegador: la API no la deduce de la IP (puede compartirse)
        var id = '';
        try { id = Plugins.identificacion && Plugins.identificacion.chat && Plugins.identificacion.chat.identidad(); } catch (e) { id = ''; }
        if (typeof id === 'string' && id && id !== '?' && id !== 'Anonymous') partes.push(parte('👤', id));
        $info.empty();
        partes.forEach(function (p, i) {
            if (i) $info.append('<span class="bh-sep" aria-hidden="true">·</span>');
            $info.append(p);
        });
        if ($pop.is(':visible')) pintarResumen();
    }

    function visitaApi() {
        var contada = false;
        try { contada = sessionStorage.getItem(CLAVE) === '1'; } catch (e) { /* sin almacenamiento */ }
        if (Plugins.visitas._contando) return;
        Plugins.visitas._contando = true;
        var post = contar && !contada;
        fetch(API_V, { method: post ? 'POST' : 'GET', headers: { 'Content-Type': 'application/json' }, body: post ? '{}' : undefined,
                       cache: 'no-store', credentials: 'same-origin' })
            .then(function (r) { if (!r.ok) throw 0; return r.json(); })
            .then(function (d) {
                if (post) { try { sessionStorage.setItem(CLAVE, '1'); } catch (e) { /* idem */ } }
                total = typeof d.total === 'number' ? d.total : null;
            })
            .catch(function () { /* se usa el total de visitas.json */ })
            .then(function () { Plugins.visitas._contando = false; pintarInfo(); });
    }

    function cargarIp() {
        fetch(API_IP, { cache: 'no-store', credentials: 'same-origin' })
            .then(function (r) { if (!r.ok) throw 0; return r.json(); })
            .then(function (d) { propia = (d && typeof d.ip === 'string') ? d : false; })
            .catch(function () { propia = false; })
            .then(pintarInfo);
    }

    function cargar() {
        $.getJSON(URL + '?_=' + Date.now()).done(function (d) {
            datos = d || {};
            var banderas = (datos.paises_ahora || []).slice(0, 8).map(flag).join('');
            $b.html('👥 ' + n(datos.ahora) + ' ahora ' + banderas + ' · ' + n(datos.total) + ' visitas');
            pintarInfo();
        }).fail(function () { $b.text('👥'); });
    }
    visitaApi();
    cargarIp();
    cargar();
    $(document).on('bh:identidad', function () { setTimeout(cargarIp, 1500); });
    setInterval(cargar, 30 * 1000);
    setInterval(cargarIp, 60 * 1000);
    return true;
};
