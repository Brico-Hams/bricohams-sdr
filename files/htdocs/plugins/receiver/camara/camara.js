/*
 * camara: cámara del mástil para OpenWebRX+
 *
 * Autor: BricoHams
 *
 * Botón "CAM" en el panel de plugins de OpenWebRX+ (Plugins.addButton) y ventana nativa (Plugins.addWindow). Dos vistas:
 *   - FOTO: una foto que se renueva sola (por defecto cada 60 s). La saca
 *     bricohams-camsnap en el servidor y se sirve por el mismo puerto de
 *     OpenWebRX, así que funciona desde fuera sin abrir más puertos.
 *   - DIRECTO: vídeo HLS de MediaMTX por HTTPS (puerto 443). Funciona en la red
 *     local y desde Internet por el mismo HTTPS; si falla, usa FOTO.
 *
 * Ajustes opcionales en init.js:
 *   window.camara_config = {
 *       snapshot: 'static/plugins/receiver/camara/snap/mastil.jpg',
 *       live: 'auto',        // 'auto' = /camara/mastil/ en el mismo origen; o una URL completa; '' = sin directo
 *       refresh: 60,         // segundos entre fotos
 *       after: '#bh-meteo-button',
 *       title: 'Cámara del mástil · Mi QTH'
 *   };
 */

Plugins.camara._version = '1.0.0';
Plugins.camara._author='BricoHams';
Plugins.camara.no_css = true;

Plugins.camara.init = function () {
    var cfg = window.camara_config || {};
    var SNAP = cfg.snapshot || 'static/plugins/receiver/camara/snap/mastil.jpg';
    var REFRESH = Math.max(10, +cfg.refresh || 60);
    var AFTER = cfg.after || '#bh-meteo-button';
    var TITLE = cfg.title || 'CÁMARA DEL MÁSTIL';
    var LIVE = (cfg.live === undefined || cfg.live === 'auto')
        ? '/camara/mastil/'
        : cfg.live;

    var css =
        '#bh-cam-button svg{width:18px;height:18px}' +
        '#bh-cam{display:flex;flex-direction:column;width:min(520px,calc(100vw - 48px));color:var(--text,#F6F8FA);font:12px var(--bh-font-ui,system-ui,sans-serif)}' +
        '#bh-cam .cm-tabs{display:flex;gap:4px;margin-bottom:6px}' +
        '#bh-cam .cm-chip{cursor:pointer;padding:2px 7px;border-radius:6px;background:var(--bg,#111518);color:var(--text-muted,#BAC4CC);box-shadow:0 0 0 1px var(--border,#38434C);font-size:11px}' +
        '#bh-cam .cm-chip.on{background:var(--brand-orange,#F26B1D);color:var(--on-accent,#23272B);box-shadow:none}' +
        '#bh-cam .cm-view{position:relative;background:var(--brand-ink,#23272B);border-radius:8px;overflow:hidden;aspect-ratio:16/9}' +
        '#bh-cam img,#bh-cam iframe{width:100%;height:100%;border:0;display:block;object-fit:contain}' +
        '#bh-cam .cm-note{color:var(--text-muted,#BAC4CC);font-size:10px;margin-top:6px}' +
        '#bh-cam .cm-rec{position:absolute;top:8px;left:8px;background:var(--brand-ink,#23272B);padding:2px 6px;border-radius:4px;font-size:10px;color:#F6F8FA}' +
        '#bh-cam .cm-rec:before{content:"";display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--err,#FF8A80);margin-right:5px;vertical-align:middle}' +
        '#bh-cam :focus-visible{outline:3px solid var(--focus,#FFC18F);outline-offset:3px}';
    var st = document.createElement('style');
    st.textContent = css;
    document.head.appendChild(st);

    function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
    function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* sin almacenamiento */ } }

    var CAM_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round">' +
        '<rect x="2.5" y="7" width="13" height="10" rx="2"/><path d="M15.5 10.5l6-3.5v10l-6-3.5z"/><circle cx="6" cy="10" r="1" fill="currentColor"/></svg>';
    var TITLE_BTN = 'Cámara del mástil';
    var $btn;

    // botón nativo del panel de plugins; si no existe, el de la barra superior de antes
    var nativeBtn = typeof Plugins.addButton === 'function'
        ? Plugins.addButton('camara', 'CAM', function () { toggle(!abierta()); }) : null;
    if (nativeBtn) {
        $btn = $(nativeBtn).attr('title', TITLE_BTN);
    } else {
        $btn = $('<div class="button" id="bh-cam-button" title="' + TITLE_BTN + '">' + CAM_SVG + '<br>CAM</div>');
        $btn.on('click', function () { toggle(!abierta()); });
        (function placeButton(tries) {
            var $after = $(AFTER);
            if (!$after.length) $after = $('#bh-solar-button, #owrx-rig-dx-button').last();
            if ($after.length) { $after.after($btn); return; }
            if (tries > 0) { setTimeout(function () { placeButton(tries - 1); }, 500); return; }
            var $bar = $('.openwebrx-main-buttons').first();
            var $status = $bar.children('.button').filter(function () { return /Estado|Status/.test($(this).text()); }).first();
            if ($status.length) $status.after($btn); else $bar.append($btn);
        })(24);
    }

    // ventana nativa (Plugins.addWindow); sin ella, un bloque suelto
    var HTML = '<div id="bh-cam" role="region" aria-label="Cámara del mástil">' +
        '<div class="cm-tabs"><span class="cm-chip" data-v="foto">FOTO</span>' +
        (LIVE ? '<span class="cm-chip" data-v="directo">DIRECTO</span>' : '') +
        '<a class="cm-chip" target="_blank" rel="noopener" style="margin-left:auto;text-decoration:none">ABRIR ⤢</a></div>' +
        '<div class="cm-view"></div><div class="cm-note"></div></div>';
    var nativa = typeof Plugins.addWindow === 'function' && typeof Plugins.toggleWindow === 'function';
    var host = nativa ? Plugins.addWindow('camara', '📷 ' + $('<i>').text(TITLE).html(), HTML) : null;
    if (!host) {
        nativa = false;
        host = $('<div class="openwebrx-plugin-body"></div>').html(HTML)
            .css({ display: 'none', position: 'absolute', top: '90px', left: '12px', zIndex: 1002 }).appendTo('body')[0];
    }
    var $win = $(host).find('#bh-cam');
    function abierta() { return $(host).is(':visible'); }
    var $view = $win.find('.cm-view'), $note = $win.find('.cm-note'), $open = $win.find('a.cm-chip');
    var view = lsGet('bh_cam_view') || 'foto';
    if (!LIVE) view = 'foto';
    var open = false, timer = null;

    function snapUrl() { return SNAP + (SNAP.indexOf('?') < 0 ? '?' : '&') + 't=' + Date.now(); }

    function show() {
        clearInterval(timer); timer = null;
        $win.find('.cm-chip[data-v]').removeClass('on').filter('[data-v="' + view + '"]').addClass('on');
        if (view === 'directo') {
            $view.html('<iframe allow="autoplay; fullscreen" allowfullscreen src="' + LIVE + '"></iframe>');
            $note.text('Vídeo en directo (HLS). Si no carga, usa FOTO.');
            $open.attr('href', LIVE);
        } else {
            var $img = $('<img alt="Vista desde el mástil">').attr('src', snapUrl());
            $img.on('error', function () { $note.text('Todavía no hay foto. En el servidor: systemctl status bricohams-camsnap'); });
            $img.on('load', function () { $note.text('Foto actualizada a las ' + new Date().toLocaleTimeString('es-ES') + ' · se renueva cada ' + REFRESH + ' s'); });
            $view.html('<span class="cm-rec">MÁSTIL</span>').prepend($img);
            $open.attr('href', SNAP);
            timer = setInterval(function () { if (open) $img.attr('src', snapUrl()); }, REFRESH * 1000);
        }
    }

    function toggle(on) {
        open = on;
        if (nativa) Plugins.toggleWindow('camara', on); else $(host).toggle(on);
        $btn.toggleClass('highlighted', on);
        lsSet('bh_cam_open', on ? '1' : '0');
        if (on) show(); else { clearInterval(timer); timer = null; $view.empty(); }
    }
    Plugins.camara._toggle = toggle;
    $(host).find('.openwebrx-plugin-close').on('click touchend', function () { toggle(false); });
    $win.on('click', '.cm-chip[data-v]', function () { view = $(this).data('v'); lsSet('bh_cam_view', view); show(); });

    if (lsGet('bh_cam_open') === '1') setTimeout(function () { toggle(true); }, 1500);
    return true;
};
