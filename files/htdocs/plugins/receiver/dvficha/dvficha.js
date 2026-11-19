/*
 * dvficha: ficha del operador en voz digital (DMR, YSF, NXDN, D-Star) para OpenWebRX+
 *
 * Autor: BricoHams (v4)
 *
 * Cuando llega una trama de voz con indicativo muestra, junto al panel de
 * voz digital, una ficha (ventana nativa de OpenWebRX+, Plugins.addWindow) con:
 *   bandera · indicativo (enlace a QRZ) · nombre · ciudad y país · foto
 * Datos:
 *   1. DMR/NXDN: OpenWebRX+ ya consulta RadioID por el número DMR («additional»).
 *   2. Para YSF/D-Star (y para completar DMR) pregunta al servicio bricohams-api
 *      (/bricohams/api/indicativo?call=…): HamQTH es la fuente principal y RadioID
 *      y QRZ XML son complementarias si faltan datos.
 *      Si la web se abre sin nginx (puerto 8073) solo sale lo que dé OpenWebRX+.
 * Ajustes: window.dvficha_config = { api: '/bricohams/api/indicativo', segundos: 20 };
 */

Plugins.dvficha._version = '1.0.0';
Plugins.dvficha._author='BricoHams';
Plugins.dvficha.no_css = true;

Plugins.dvficha.init = function () {
    var cfg = window.dvficha_config || {};
    var API = cfg.api || '/bricohams/api/indicativo';
    var SEG = cfg.segundos || 20;
    var cache = {}, ocultar = null, actual = '';

    $('<style>').text(
        '#bh-dvficha{min-width:230px;max-width:320px;color:var(--text,#F6F8FA);font:13px/1.35 var(--bh-font-ui,system-ui,sans-serif)}' +
        '#bh-dvficha .f{display:flex;gap:10px;align-items:center}' +
        '#bh-dvficha img{width:64px;height:64px;object-fit:cover;border-radius:6px;background:var(--border,#38434C)}' +
        '#bh-dvficha .c{font:700 17px/1.1 monospace;color:var(--text,#F6F8FA)}#bh-dvficha .c a{color:var(--text,#F6F8FA);text-decoration:none}' +
        '#bh-dvficha .m{color:var(--text-muted,#BAC4CC);font-size:12px}#bh-dvficha .modo{float:right;font-size:11px;color:var(--link,#FFA06A)}'
    ).appendTo('head');

    // ventana nativa (Plugins.addWindow) que se abre sola con cada trama y se cierra a los SEG segundos;
    // sin ella, un bloque suelto
    var nativa = typeof Plugins.addWindow === 'function' && typeof Plugins.toggleWindow === 'function';
    var ventana = nativa ? Plugins.addWindow('dvficha', '📻 FICHA DEL OPERADOR', '<div id="bh-dvficha"></div>') : null;
    if (!ventana) {
        nativa = false;
        ventana = $('<div class="openwebrx-plugin-body"><div id="bh-dvficha"></div></div>')
            .css({ display: 'none', position: 'absolute', left: '12px', bottom: '64px', zIndex: 1002 }).appendTo('body')[0];
    }
    var $f = $(ventana).find('#bh-dvficha');
    function abrir(on) { if (nativa) Plugins.toggleWindow('dvficha', on); else $(ventana).toggle(on); }

    function bandera(cc) { return (Plugins.banderas && cc) ? Plugins.banderas.bandera(cc) : ''; }
    function ccDe(call) {
        try { return (typeof Lookup !== 'undefined' && Lookup.call2ccode) ? Lookup.call2ccode(call) : ''; } catch (e) { return ''; }
    }
    function esc(t) { return $('<i>').text(t || '').html(); }

    function pintar(modo, d) {
        var call = d.call;
        var qrz = 'https://www.qrz.com/db/' + encodeURIComponent(call);
        var linea2 = [d.nombre].filter(Boolean).join(' ');
        var linea3 = [d.ciudad, d.region, d.pais].filter(Boolean).join(', ');
        $f.html('<span class="modo">' + esc(modo) + '</span><div class="f">' +
            (d.foto ? '<img src="' + esc(d.foto) + '" alt="" referrerpolicy="no-referrer">' : '') +
            '<div><div class="c">' + bandera(d.ccode || ccDe(call)) + ' <a href="' + qrz + '" target="_blank" rel="noopener">' + esc(call) + '</a></div>' +
            (linea2 ? '<div>' + esc(linea2) + '</div>' : '') +
            (linea3 ? '<div class="m">' + esc(linea3) + '</div>' : '') +
            (d.dmrid ? '<div class="m">DMR ID ' + esc(String(d.dmrid)) + '</div>' : '') +
            '</div></div>');
        abrir(true);
        clearTimeout(ocultar);
        ocultar = setTimeout(function () { abrir(false); actual = ''; }, SEG * 1000);
    }

    function mostrar(modo, call, extra) {
        if (!call) return;
        call = String(call).toUpperCase().replace(/[^A-Z0-9\/]/g, '');
        if (!/[A-Z]/.test(call) || !/[0-9]/.test(call)) return;
        var base = $.extend({ call: call }, extra || {});
        clearTimeout(ocultar);
        ocultar = setTimeout(function () { abrir(false); actual = ''; }, SEG * 1000);
        if (actual === call) return;
        actual = call;
        if (cache[call]) { pintar(modo, $.extend({}, base, cache[call])); return; }
        pintar(modo, base);
        $.getJSON(API, { call: call }).done(function (d) {
            cache[call] = d || {};
            if (actual === call) pintar(modo, $.extend({}, base, cache[call]));
        }).fail(function () { cache[call] = {}; });
    }

    function envolver(clase, modo, sacar) {
        if (typeof window[clase] === 'undefined' || !window[clase].prototype || window[clase].prototype._bh_dv) return;
        var P = window[clase].prototype, orig = P.update;
        P._bh_dv = true;
        P.update = function (data) {
            var r = orig.apply(this, arguments);
            try { var x = sacar(data || {}); if (x) mostrar(modo, x.call, x.extra); } catch (e) { console.debug('dvficha', e); }
            return r;
        };
    }

    envolver('DmrMetaSlot', 'DMR', function (d) {
        if (d.sync !== 'voice') return null;
        var a = d.additional || {};
        var call = a.callsign || d.talkeralias || '';
        return call ? { call: call, extra: { nombre: [a.fname, a.surname].filter(Boolean).join(' '), ciudad: a.city,
            region: a.state, pais: a.country, dmrid: d.source } } : null;
    });
    envolver('NxdnMetaPanel', 'NXDN', function (d) {
        var a = d.additional || {};
        return a.callsign ? { call: a.callsign, extra: { nombre: a.fname, ciudad: a.city, pais: a.country } } : null;
    });
    envolver('YsfMetaPanel', 'YSF', function (d) { return d.source ? { call: d.source } : null; });
    envolver('DStarMetaPanel', 'D-Star', function (d) { return d.ourcall ? { call: String(d.ourcall).split(/[ \/]/)[0] } : null; });
    return true;
};
