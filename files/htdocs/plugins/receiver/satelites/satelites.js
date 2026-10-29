/*
 * satelites: aviso de próximos pases y «▶ Escuchar» con un clic (OpenWebRX+)
 *
 * Autor: BricoHams (v4)
 *
 *  - Franja bajo la cabecera: «🛰️ SO-50 en 12 min · máx 54° · 11 min · 436,795 FM  [▶ Escuchar]»
 *    y, durante el pase, «🔴 EN DIRECTO: ISS 32°».
 *  - Botón «PASES» en la barra superior con los pases de las próximas 24 h.
 *  - ▶ Escuchar: cambia al receptor/perfil de satélites que toca, sintoniza la
 *    bajada en su modo y arranca el seguimiento Doppler del plugin «doppler»
 *    con los mismos elementos orbitales. Para los METEOR (imágenes LRPT) las
 *    imágenes las decodifica el servicio de fondo y aparecen en «Files».
 *  Datos: static/plugins/receiver/satelites/pases.json (bricohams-satpass, cada 15 min).
 *  Ajustes: window.satelites_config = { url: '…/pases.json', franja: true, min_el: 15 };
 */

Plugins.satelites._version = '1.0.0';
Plugins.satelites._author = 'BricoHams';
Plugins.satelites.no_css = true;

Plugins.satelites.init = function () {
    var cfg = window.satelites_config || {};
    var URL = cfg.url || 'static/plugins/receiver/satelites/pases.json';
    var MIN_EL = cfg.min_el || 15;
    var pases = [];
    var S = Plugins.satelites;

    $('<style>').text(
        '#bh-sat-franja{position:fixed;top:0;left:50%;transform:translateX(-50%);z-index:9997;display:none;gap:8px;align-items:center;' +
        'background:rgba(20,22,26,.92);color:#eee;border:1px solid #2e7d32;border-top:0;border-radius:0 0 10px 10px;padding:4px 12px;' +
        'font:13px/1.3 sans-serif;box-shadow:0 2px 10px rgba(0,0,0,.5);white-space:nowrap}' +
        '#bh-sat-franja.vivo{border-color:#e53935}#bh-sat-franja button,#bh-sat-lista button{background:#2e7d32;color:#fff;border:0;border-radius:6px;' +
        'padding:2px 8px;cursor:pointer;font-weight:600}#bh-sat-franja .x{background:none;color:#aaa;padding:0 2px}' +
        '#bh-sat-lista{position:fixed;top:60px;right:12px;z-index:9998;display:none;max-height:70vh;overflow:auto;background:rgba(20,22,26,.96);' +
        'color:#eee;border:1px solid #2e7d32;border-radius:10px;padding:8px;font:12px/1.4 sans-serif}' +
        '#bh-sat-lista table{border-collapse:collapse}#bh-sat-lista td,#bh-sat-lista th{padding:2px 6px;text-align:left}' +
        '#bh-sat-lista tr.vivo{color:#ff8a80}#bh-sat-lista th{color:#9ccc65}'
    ).appendTo('head');
    var $franja = $('<div id="bh-sat-franja"></div>').appendTo('body');
    var $lista = $('<div id="bh-sat-lista"></div>').appendTo('body');
    var cerrada = false;
    var filtro = { banda: '', desde: '', hasta: '' };
    function filtrar(p) {
        var limites = { '': [0, 1e11], '2m': [144e6, 148e6], '70cm': [430e6, 440e6],
            '137': [137e6, 138e6], '400': [400e6, 401e6] }[filtro.banda];
        var desde = filtro.desde ? Number(filtro.desde.replace(',', '.')) * 1e6 : 0;
        var hasta = filtro.hasta ? Number(filtro.hasta.replace(',', '.')) * 1e6 : 1e11;
        return p.hz >= Math.max(limites[0], desde) && p.hz <= Math.min(limites[1], hasta);
    }
    $lista.on('submit', 'form', function (evento) {
        evento.preventDefault();
        var desde = $(this).find('[name=desde]').val().trim();
        var hasta = $(this).find('[name=hasta]').val().trim();
        if ([desde, hasta].some(function (v) {
            return v && (!/^[0-9]+([.,][0-9]{1,6})?$/.test(v) || Number(v.replace(',', '.')) <= 0 ||
                Number(v.replace(',', '.')) > 100000);
        }) || (desde && hasta && Number(desde.replace(',', '.')) > Number(hasta.replace(',', '.')))) {
            $lista.find('[role=alert]').text('Frecuencias no válidas: MHz positivos, desde menor o igual que hasta.');
            return;
        }
        filtro = { banda: $(this).find('[name=banda]').val(), desde: desde, hasta: hasta };
        pintarLista();
    });

    function mhz(hz) { return (hz / 1e6).toFixed(3).replace('.', ','); }
    function hora(t) { var d = new Date(t * 1000); return ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2); }
    function esc(t) { return $('<i>').text(t || '').html(); }

    S.escuchar = function (i) {
        var p = pases[i];
        if (!p) return;
        try { if (Plugins.doppler && Plugins.doppler.intervalId) Plugins.doppler.stop_tracker(); } catch (e) {}
        var $lb = $('#openwebrx-sdr-profiles-listbox');
        var sintonizar = function () {
            try {
                UI.setFrequency(p.hz, false);
                UI.setModulation(p.modo);
                if (Plugins.doppler && Plugins.doppler.start_tracker && p.omm) {
                    setTimeout(function () { Plugins.doppler.start_tracker(p.omm); }, 600);
                }
                if (UI.showBubble) UI.showBubble('🛰️ ' + p.nombre + ' · ' + mhz(p.hz) + ' MHz · Doppler activado');
            } catch (e) { console.warn('satelites', e); }
        };
        if ($lb.length && $lb.val() !== p.perfil && $lb.find('option[value="' + p.perfil + '"]').length) {
            $lb.val(p.perfil);
            if (typeof sdr_profile_changed === 'function') sdr_profile_changed(); else $lb.trigger('change');
            var antes = window.center_freq, n = 0;
            var espera = setInterval(function () {      // esperar a que llegue el perfil nuevo
                n++;
                if ((window.center_freq !== antes && Math.abs(window.center_freq - p.hz) < 3e6) || n > 40) {
                    clearInterval(espera);
                    setTimeout(sintonizar, 400);
                }
            }, 250);
        } else {
            sintonizar();
        }
    };

    function pintarFranja() {
        if (cerrada) return;
        var ahora = Date.now() / 1000;
        var vivo = pases.findIndex(function (p) { return p.aos <= ahora && ahora <= p.los && p.max_el >= MIN_EL; });
        var prox = pases.findIndex(function (p) { return p.aos > ahora && p.max_el >= MIN_EL; });
        var i = vivo >= 0 ? vivo : prox;
        if (i < 0) { $franja.hide(); return; }
        var p = pases[i];
        var txt = vivo >= 0
            ? '🔴 EN DIRECTO: <b>' + esc(p.nombre) + '</b> · hasta las ' + hora(p.los) + ' · máx ' + p.max_el + '°'
            : '🛰️ <b>' + esc(p.nombre) + '</b> en ' + Math.max(1, Math.round((p.aos - ahora) / 60)) + ' min (' + hora(p.aos) + ') · máx ' +
              p.max_el + '° · ' + Math.round(p.duracion_s / 60) + ' min';
        $franja.toggleClass('vivo', vivo >= 0).css('display', 'flex').html(
            '<span>' + txt + ' · ' + mhz(p.hz) + ' ' + p.modo.toUpperCase() + '</span>' +
            '<button title="' + esc(p.nota) + '" onclick="Plugins.satelites.escuchar(' + i + ')">▶ Escuchar</button>' +
            '<button class="x" title="Ocultar" onclick="$(\'#bh-sat-franja\').hide();Plugins.satelites._cerrar()">✕</button>');
    }
    S._cerrar = function () { cerrada = true; setTimeout(function () { cerrada = false; }, 30 * 60 * 1000); };

    function pintarLista() {
        var ahora = Date.now() / 1000;
        var filas = pases.filter(function (p) { return p.los > ahora && filtrar(p); }).slice(0, 100).map(function (p) {
            var i = pases.indexOf(p);
            return '<tr class="' + (p.aos <= ahora ? 'vivo' : '') + '"><td>' + hora(p.aos) + '</td><td>' + esc(p.nombre) + '</td><td>' + p.max_el +
                '°</td><td>' + Math.round(p.duracion_s / 60) + ' min</td><td>' + mhz(p.hz) + ' ' + p.modo.toUpperCase() + '</td><td>' +
                (p.az_aos != null ? p.az_aos + '°→' + (p.az_los != null ? p.az_los : '?') + '°' : '') +
                '</td><td><button onclick="Plugins.satelites.escuchar(' + i + ')">▶</button></td></tr>';
        }).join('');
        $lista.html('<b>🛰️ Próximos pases (24 h)</b> <span style="float:right;cursor:pointer" onclick="$(\'#bh-sat-lista\').hide()">✕</span>' +
            '<form><label>Banda <select name="banda">' +
            [['', 'Todas'], ['2m', '2 m'], ['70cm', '70 cm'], ['137', '137 MHz'], ['400', '400 MHz']].map(function (v) {
                return '<option value="' + v[0] + '"' + (filtro.banda === v[0] ? ' selected' : '') + '>' + v[1] + '</option>';
            }).join('') + '</select></label> <label>Desde MHz <input name="desde" size="9" inputmode="decimal" value="' +
            esc(filtro.desde) + '"></label> <label>Hasta MHz <input name="hasta" size="9" inputmode="decimal" value="' +
            esc(filtro.hasta) + '"></label> <button>Filtrar</button></form><div role="alert"></div>' +
            '<div>Solo filtra esta lista, no las capturas ni los avisos. Para frecuencia exacta: desde = hasta.</div>' +
            '<table><tr><th>Hora</th><th>Satélite</th><th>Máx</th><th>Dura</th><th>Bajada</th><th>Az</th><th></th></tr>' +
            (filas || '<tr><td colspan="7">Sin pases con estos filtros o sin datos (bricohams-satpass)</td></tr>') + '</table>' +
            '<div style="opacity:.7;margin-top:4px">▶ cambia de perfil, sintoniza y activa el Doppler. Imágenes METEOR: menú «Files».</div>');
    }
    S.lista = function () {
        pintarLista();
        $lista.toggle();
    };

    function cargar() {
        $.getJSON(URL + '?_=' + Date.now()).done(function (d) {
            pases = (d && d.pases) || [];
            pintarFranja();
        });
    }
    if (typeof Plugins.addButton === 'function') {
        try { Plugins.addButton('satelites', 'PASES', function () { S.lista(); }); } catch (e) { console.debug(e); }
    }
    cargar();
    setInterval(cargar, 5 * 60 * 1000);
    setInterval(pintarFranja, 30 * 1000);
    return true;
};
