/*
 * bricohams: imagen de BricoHams (Mi QTH, Región de Murcia) para OpenWebRX+
 *
 * Autor: EA5KAO · BricoHams
 *
 *  - Franja carmesí (bandera de la Región de Murcia) y naranja BricoHams
 *    bajo la barra superior.
 *  - Mini bandera de Murcia junto al nombre del receptor.
 *  - Botón flotante al canal de Telegram.
 *  - v4: plan de bandas visible por defecto (la primera vez; luego manda lo que elija
 *    cada visitante) y foto superior más baja para que se vea la web.
 *
 * Ajustes opcionales en init.js:
 *   window.bricohams_config = { telegram: 'https://t.me/bricohams', boton: true };
 */

Plugins.bricohams._version = '1.1.0';
Plugins.bricohams._author = 'EA5KAO';
Plugins.bricohams.no_css = true;

Plugins.bricohams.init = function () {
    var cfg = window.bricohams_config || {};
    var TG = cfg.telegram || 'https://t.me/bricohams';
    var CR = '#A6192E', OR = '#F26B21', GOLD = '#E7B416';

    // bandera de la Región de Murcia: 4 castillos y 7 coronas (1-3-2-1)
    function flag(w) {
        var h = w * 2 / 3, s = '<svg xmlns="http://www.w3.org/2000/svg" width="' + w + '" height="' + h + '" viewBox="0 0 60 40" aria-label="Región de Murcia">' +
            '<rect width="60" height="40" rx="2" fill="' + CR + '"/>';
        [[5, 4], [16, 4], [5, 14], [16, 14]].forEach(function (p) {
            var x = p[0], y = p[1];
            s += '<path d="M' + x + ' ' + (y + 8) + 'V' + (y + 3) + 'h1.6V' + (y + 1) + 'h1.6v2h2.4V' + (y + 1) + 'h1.6v2H' + (x + 8) + 'V' + (y + 8) + 'z" fill="' + GOLD + '"/>';
        });
        var rows = [1, 3, 2, 1];
        rows.forEach(function (n, r) {
            for (var i = 0; i < n; i++) {
                var cx = 44 + (i - (n - 1) / 2) * 6.5, cy = 14 + r * 6;
                s += '<path d="M' + (cx - 2.5) + ' ' + (cy + 2.5) + 'V' + cy + 'l1.25 1.2L' + cx + ' ' + (cy - 0.6) + 'l1.25 1.8L' + (cx + 2.5) + ' ' + cy + 'V' + (cy + 2.5) + 'z" fill="' + GOLD + '"/>';
            }
        });
        return s + '</svg>';
    }

    var css =
        '.webrx-top-container{border-bottom:3px solid ' + OR + ';box-shadow:0 2px 0 0 ' + CR + '}' +
        '#bh-murcia-flag{display:inline-block;vertical-align:middle;margin-right:6px;border-radius:2px;box-shadow:0 0 0 1px rgba(0,0,0,.4)}' +
        '#bh-murcia-flag svg{display:block}' +
        '#bricohams-tg{position:fixed;right:12px;bottom:12px;z-index:9999;display:flex;gap:6px;align-items:center;' +
            'padding:6px 12px;border-radius:999px;background:' + OR + ';color:#fff;font:600 13px/1 sans-serif;' +
            'text-decoration:none;box-shadow:0 2px 8px rgba(0,0,0,.4);opacity:.9}' +
        '#bricohams-tg:hover{opacity:1;background:#229ED9}' +
        '@media (max-width:600px){#bricohams-tg span{display:none}}';
    // v4: la foto de cabecera abierta no tapa media pantalla
    css += '.openwebrx-description-container.expanded{height:210px!important;max-height:210px!important}';
    var st = document.createElement('style');
    st.textContent = css;
    document.head.appendChild(st);

    // bandera junto al nombre del receptor
    var $title = $('.webrx-rx-title').first();
    if ($title.length && !document.getElementById('bh-murcia-flag')) {
        $title.prepend($('<span id="bh-murcia-flag" title="Mi QTH · Región de Murcia"></span>').html(flag(24)));
    }

    // botón de Telegram
    if (cfg.boton !== false && !document.getElementById('bricohams-tg')) {
        var a = document.createElement('a');
        a.id = 'bricohams-tg';
        a.href = TG;
        a.target = '_blank';
        a.rel = 'noopener';
        a.title = 'Canal de Telegram de BricoHams';
        a.innerHTML =
            '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path fill="currentColor" ' +
            'd="M9.8 15.6l-.4 5.4c.6 0 .8-.2 1.1-.5l2.6-2.5 5.4 4c1 .6 1.7.3 2-.9l3.6-17c.3-1.5-.6-2.1-1.6-1.7L1.3 ' +
            '9.6C-.2 10.2-.1 11 1 11.4l5.4 1.7L18.8 5.3c.6-.4 1.1-.2.7.2z"/></svg><span>BricoHams</span>';
        document.body.appendChild(a);
    }
    // v4: plan de bandas visible por defecto (sustituye al plugin show_band_plan, ya obsoleto)
    try {
        if (typeof LS !== 'undefined' && !LS.has('ui_bandplan') && typeof UI !== 'undefined' && UI.toggleBandplan) {
            setTimeout(function () { UI.toggleBandplan(true); }, 1500);
        }
    } catch (e) { console.debug('bandplan', e); }
    return true;
};
