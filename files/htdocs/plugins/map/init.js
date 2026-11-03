// =====================================================================
//  BricoHams · Plugins del MAPA OpenWebRX+
//  Ruta: /usr/lib/python3/dist-packages/htdocs/plugins/map/init.js
//  (la cuadrícula QTH Maidenhead ya viene integrada en OpenWebRX+)
// =====================================================================

// Plugins._enable_debug = true;

const mp_url = 'https://0xaf.github.io/openwebrxplus-plugins/map';
const BRICOHAMS_TELEGRAM = 'https://t.me/bricohams';

// Leyenda plegable (Mapa / Colores / Funciones): deja más sitio al mapa, sobre todo en el móvil
Plugins.load(mp_url + '/reduce_map_legend_sections/reduce_map_legend_sections.js');
Plugins.load('bricohams_live');

// Botón BricoHams y "volver al receptor"
(function () {
    function botones() {
        if (document.getElementById('bricohams-map')) return;
        const css = document.createElement('style');
        css.textContent =
            '#bricohams-map{position:fixed;left:12px;bottom:28px;z-index:1000;display:flex;gap:8px}' +
            '#bricohams-map a{display:flex;gap:6px;align-items:center;padding:6px 12px;border-radius:999px;' +
            'color:var(--on-accent,#23272B);font:600 13px/1 var(--bh-font-ui,system-ui,sans-serif);text-decoration:none;box-shadow:0 2px 8px rgba(0,0,0,.4)}' +
            '#bricohams-map .tg{background:var(--brand-orange,#F26B1D)}#bricohams-map a:hover{text-decoration:underline}' +
            '#bricohams-map a:focus-visible{outline:3px solid var(--focus,#F26B1D);outline-offset:3px}' +
            '#bricohams-map .rx{background:var(--surface,#F6F7F8);color:var(--text,#23272B);border:1px solid var(--border,#DCE1E5)}' +
            '@media (max-width:600px){#bricohams-map span{display:none}}';
        document.head.appendChild(css);
        const box = document.createElement('div');
        box.id = 'bricohams-map';
        box.innerHTML =
            '<a class="rx" href="./" title="Volver al receptor">📻<span>Receptor</span></a>' +
            '<a class="tg" href="' + BRICOHAMS_TELEGRAM + '" target="_blank" rel="noopener" ' +
            'title="Canal de Telegram de BricoHams">✈️<span>BricoHams</span></a>';
        document.body.appendChild(box);
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', botones);
    else botones();
})();