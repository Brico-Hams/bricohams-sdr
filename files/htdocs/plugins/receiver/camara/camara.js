/*
 * camara: cámara del mástil para OpenWebRX+
 *
 * Autor: EA5KAO · BricoHams
 *
 * Botón "CAM" en la barra superior (detrás de METEO). Dos vistas:
 *   - FOTO: una foto que se renueva sola (por defecto cada 60 s). La saca
 *     bricohams-camsnap en el servidor y se sirve por el mismo puerto de
 *     OpenWebRX, así que funciona desde fuera sin abrir más puertos.
 *   - DIRECTO: vídeo WebRTC de MediaMTX (puerto 8889). Funciona en la red
 *     local o si abres/rediriges ese puerto; si no, usa la FOTO.
 *
 * Ajustes opcionales en init.js:
 *   window.camara_config = {
 *       snapshot: 'static/plugins/receiver/camara/snap/mastil.jpg',
 *       live: 'auto',        // 'auto' = mismo host, puerto 8889; o una URL completa; '' = sin directo
 *       refresh: 60,         // segundos entre fotos
 *       after: '#ea5kao-meteo-button',
 *       title: 'Cámara del mástil · Mi QTH'
 *   };
 */

Plugins.camara._version = '1.0.0';
Plugins.camara._author = 'EA5KAO';
Plugins.camara.no_css = true;

Plugins.camara.init = function () {
    var cfg = window.camara_config || {};
    var SNAP = cfg.snapshot || 'static/plugins/receiver/camara/snap/mastil.jpg';
    var REFRESH = Math.max(10, +cfg.refresh || 60);
    var AFTER = cfg.after || '#ea5kao-meteo-button';
    var TITLE = cfg.title || 'CÁMARA DEL MÁSTIL';
    var LIVE = (cfg.live === undefined || cfg.live === 'auto')
        ? location.protocol + '//' + location.hostname + ':8889/mastil/'
        : cfg.live;

    var css =
        '#ea5kao-cam-button svg{width:18px;height:18px}' +
        '#ea5kao-cam{position:fixed;top:90px;left:500px;z-index:1002;width:520px;max-width:calc(100vw - 16px);' +
            'display:none;flex-direction:column;padding:8px;border-radius:8px;color:#cfd4d9;font:12px roboto-mono,monospace;' +
            'background:linear-gradient(#2a2e33,#17191d);box-shadow:inset 0 1px 0 rgba(255,255,255,.07),0 0 0 1px #060708,0 6px 18px rgba(0,0,0,.65);resize:horizontal;overflow:hidden}' +
        '#ea5kao-cam.open{display:flex}' +
        '#ea5kao-cam .cm-hdr{display:flex;align-items:center;gap:6px;padding:0 2px 6px;cursor:move;user-select:none;touch-action:none}' +
        '#ea5kao-cam .cm-title{flex:1;color:#93a0ab;letter-spacing:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}' +
        '#ea5kao-cam .cm-btn{cursor:pointer;color:#93a0ab;padding:0 4px;font-size:15px;line-height:1}' +
        '#ea5kao-cam .cm-btn:hover{color:#fff}' +
        '#ea5kao-cam .cm-tabs{display:flex;gap:4px;margin-bottom:6px}' +
        '#ea5kao-cam .cm-chip{cursor:pointer;padding:2px 7px;border-radius:3px;background:#10161b;color:#93a0ab;box-shadow:0 0 0 1px #1d242b;font-size:11px}' +
        '#ea5kao-cam .cm-chip.on{color:#0f0;box-shadow:0 0 0 1px #2e7d32}' +
        '#ea5kao-cam .cm-view{position:relative;background:#000;border-radius:5px;overflow:hidden;aspect-ratio:16/9}' +
        '#ea5kao-cam img,#ea5kao-cam iframe{width:100%;height:100%;border:0;display:block;object-fit:contain}' +
        '#ea5kao-cam .cm-note{color:#6b7782;font-size:10px;margin-top:6px}' +
        '#ea5kao-cam .cm-rec{position:absolute;top:8px;left:8px;background:rgba(0,0,0,.55);padding:2px 6px;border-radius:3px;font-size:10px;color:#fff}' +
        '#ea5kao-cam .cm-rec:before{content:"";display:inline-block;width:7px;height:7px;border-radius:50%;background:#ff3b30;margin-right:5px;vertical-align:middle}' +
        '@media (max-width:600px){#ea5kao-cam{left:8px!important;top:60px!important}}';
    var st = document.createElement('style');
    st.textContent = css;
    document.head.appendChild(st);

    function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
    function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* sin almacenamiento */ } }

    var CAM_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round">' +
        '<rect x="2.5" y="7" width="13" height="10" rx="2"/><path d="M15.5 10.5l6-3.5v10l-6-3.5z"/><circle cx="6" cy="10" r="1" fill="currentColor"/></svg>';
    var $btn = $('<div class="button" id="ea5kao-cam-button" title="Cámara del mástil">' + CAM_SVG + '<br>CAM</div>');

    function placeButton(tries) {
        var $after = $(AFTER);
        if (!$after.length) $after = $('#ea5kao-solar-button, #owrx-rig-dx-button').last();
        if ($after.length) { $after.after($btn); return; }
        if (tries > 0) { setTimeout(function () { placeButton(tries - 1); }, 500); return; }
        var $bar = $('.openwebrx-main-buttons').first();
        var $status = $bar.children('.button').filter(function () { return /Estado|Status/.test($(this).text()); }).first();
        if ($status.length) $status.after($btn); else $bar.append($btn);
    }
    placeButton(24);

    var $win = $('<div id="ea5kao-cam" role="dialog" aria-label="Cámara del mástil">' +
        '<div class="cm-hdr"><span class="cm-title">📷 ' + $('<i>').text(TITLE).html() + '</span>' +
        '<span class="cm-btn cm-close" title="Cerrar">×</span></div>' +
        '<div class="cm-tabs"><span class="cm-chip" data-v="foto">FOTO</span>' +
        (LIVE ? '<span class="cm-chip" data-v="directo">DIRECTO</span>' : '') +
        '<a class="cm-chip" target="_blank" rel="noopener" style="margin-left:auto;text-decoration:none">ABRIR ⤢</a></div>' +
        '<div class="cm-view"></div><div class="cm-note"></div></div>');
    $('body').append($win);
    var $view = $win.find('.cm-view'), $note = $win.find('.cm-note'), $open = $win.find('a.cm-chip');
    var view = lsGet('ea5kao_cam_view') || 'foto';
    if (!LIVE) view = 'foto';
    var open = false, timer = null;

    function snapUrl() { return SNAP + (SNAP.indexOf('?') < 0 ? '?' : '&') + 't=' + Date.now(); }

    function show() {
        clearInterval(timer); timer = null;
        $win.find('.cm-chip[data-v]').removeClass('on').filter('[data-v="' + view + '"]').addClass('on');
        if (view === 'directo') {
            $view.html('<iframe allow="autoplay; fullscreen" allowfullscreen src="' + LIVE + '"></iframe>');
            $note.text('Vídeo en directo (WebRTC). Si no carga, el puerto 8889 no es accesible desde aquí: usa FOTO.');
            $open.attr('href', LIVE);
        } else {
            var $img = $('<img alt="Vista desde el mástil">').attr('src', snapUrl());
            $img.on('error', function () { $note.text('Todavía no hay foto. En el servidor: systemctl status bricohams-camsnap'); });
            $img.on('load', function () { $note.text('Foto actualizada a las ' + new Date().toLocaleTimeString('es-ES') + ' · se renueva cada ' + REFRESH + ' s'); });
            $view.html('<span class="cm-rec">EA5KAO · MÁSTIL</span>').prepend($img);
            $open.attr('href', SNAP);
            timer = setInterval(function () { if (open) $img.attr('src', snapUrl()); }, REFRESH * 1000);
        }
    }

    function toggle(on) {
        open = on;
        $win.toggleClass('open', on);
        $btn.toggleClass('highlighted', on);
        lsSet('ea5kao_cam_open', on ? '1' : '0');
        if (on) show(); else { clearInterval(timer); timer = null; $view.empty(); }
    }
    Plugins.camara._toggle = toggle;
    $btn.on('click', function () { toggle(!open); });
    $win.find('.cm-close').on('click', function () { toggle(false); });
    $win.on('click', '.cm-chip[data-v]', function () { view = $(this).data('v'); lsSet('ea5kao_cam_view', view); show(); });

    (function () {
        var p = (lsGet('ea5kao_cam_pos') || '').split(',');
        if (p.length === 2 && window.innerWidth > 600) {
            $win.css({ left: Math.max(0, Math.min(+p[0], window.innerWidth - 120)) + 'px',
                       top: Math.max(0, Math.min(+p[1], window.innerHeight - 60)) + 'px' });
        }
        var drag = null;
        $win.find('.cm-hdr').on('pointerdown', function (e) {
            if ($(e.target).hasClass('cm-btn')) return;
            var o = $win[0].getBoundingClientRect();
            drag = { dx: e.clientX - o.left, dy: e.clientY - o.top };
            this.setPointerCapture(e.pointerId);
        }).on('pointermove', function (e) {
            if (!drag) return;
            $win.css({ left: Math.max(0, e.clientX - drag.dx) + 'px', top: Math.max(0, e.clientY - drag.dy) + 'px' });
        }).on('pointerup pointercancel', function () {
            if (!drag) return;
            drag = null;
            lsSet('ea5kao_cam_pos', parseInt($win.css('left')) + ',' + parseInt($win.css('top')));
        });
    })();

    if (lsGet('ea5kao_cam_open') === '1') setTimeout(function () { toggle(true); }, 1500);
    return true;
};
