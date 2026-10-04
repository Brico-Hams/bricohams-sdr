/*
 * visitas: oyentes conectados y contador de visitas (OpenWebRX+)
 *
 * Autor: EA5KAO · BricoHams (v4)
 *
 * Muestra junto al nombre del receptor «👥 3 ahora 🇪🇸🇪🇸🇮🇹 · 1.234 visitas» y,
 * al pulsar, un resumen por países de los últimos 30 días.
 * Los datos los genera bricohams-visitas (avisos de conexión de OpenWebRX+ por
 * MQTT + GeoIP local) en static/plugins/receiver/visitas/visitas.json.
 * En la web pública solo salen países y totales: nunca IPs.
 * Incluye el enlace al aviso de privacidad (obligatorio al registrar visitas).
 */

Plugins.visitas._version = '1.0.0';
Plugins.visitas._author = 'EA5KAO';
Plugins.visitas.no_css = true;

Plugins.visitas.init = function () {
    var cfg = window.visitas_config || {};
    var URL = cfg.url || 'static/plugins/receiver/visitas/visitas.json';
    var PRIV = cfg.privacidad || '/bricohams/privacidad.html';
    function flag(cc) { return (Plugins.banderas && cc) ? Plugins.banderas.bandera(cc) : (cc || ''); }
    function n(x) { return (x || 0).toLocaleString('es-ES'); }

    $('<style>').text(
        '#bh-visitas{display:inline-block;margin-left:10px;padding:1px 8px;border-radius:999px;background:rgba(255,255,255,.08);' +
        'font:600 12px/1.6 sans-serif;color:#eee;cursor:pointer;vertical-align:middle}' +
        '#bh-visitas-pop{position:fixed;top:60px;left:12px;z-index:9998;display:none;background:rgba(20,22,26,.96);color:#eee;' +
        'border:1px solid #F26B21;border-radius:10px;padding:8px 12px;font:12px/1.5 sans-serif;max-height:60vh;overflow:auto}' +
        '#bh-visitas-pop a{color:#F26B21}'
    ).appendTo('head');
    var $b = $('<span id="bh-visitas" title="Oyentes conectados y visitas">👥 …</span>');
    var $t = $('.webrx-rx-title').first();
    if ($t.length) $t.append($b); else $('body').append($b.css({ position: 'fixed', left: 12, top: 4, zIndex: 9999 }));
    var $pop = $('<div id="bh-visitas-pop"></div>').appendTo('body');
    var datos = null;

    $b.on('click', function (e) {
        e.stopPropagation();
        if (!datos) return;
        var filas = (datos.paises_30d || []).slice(0, 25).map(function (p) {
            return '<tr><td>' + flag(p.cc) + ' ' + $('<i>').text(p.pais || p.cc).html() + '</td><td style="text-align:right">' + n(p.n) + '</td></tr>';
        }).join('');
        $pop.html('<b>👥 Oyentes · BricoHams SDR</b> <span style="float:right;cursor:pointer" onclick="$(\'#bh-visitas-pop\').hide()">✕</span><br>' +
            'Ahora: <b>' + n(datos.ahora) + '</b> · Hoy: <b>' + n(datos.hoy) + '</b> · Total: <b>' + n(datos.total) + '</b><br>' +
            '<table style="margin-top:4px">' + filas + '</table>' +
            '<div style="opacity:.7;margin-top:6px">Visitas de los últimos 30 días por país. <a href="' + PRIV + '" target="_blank">Privacidad</a></div>').toggle();
    });

    function cargar() {
        $.getJSON(URL + '?_=' + Date.now()).done(function (d) {
            datos = d || {};
            var banderas = (datos.paises_ahora || []).slice(0, 8).map(flag).join('');
            $b.html('👥 ' + n(datos.ahora) + ' ahora ' + banderas + ' · ' + n(datos.total) + ' visitas');
        }).fail(function () { $b.text('👥'); });
    }
    cargar();
    setInterval(cargar, 30 * 1000);
    return true;
};
