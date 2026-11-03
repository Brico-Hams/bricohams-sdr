/*
 * marca: logo de BricoHams en la cabecera de OpenWebRX+
 *
 * Sustituye en el navegador el logo de OpenWebRX+ (arriba a la izquierda) por el de
 * BricoHams y lo enlaza al portal de la estación. No modifica los ficheros del paquete:
 * al actualizar OpenWebRX+ el cambio se mantiene y, si se quita el plugin, vuelve el original.
 *
 * Ajustes en init.js:
 *   window.marca_config = { logo: 'static/plugins/receiver/marca/bricohams-logo.png', url: '/bricohams/', titulo: 'BricoHams' };
 */
Plugins.marca._version = '1.1.0';
Plugins.marca.no_css = true;

// Official BricoHams colour manual v1.1: light tokens by default, dark via prefers-color-scheme,
// and an explicit data-theme="light"|"dark" on <html> (stored in localStorage as bh_theme).
(function () {
    var KEY = 'bh_theme';
    var DARK = '--bg:#111518;--surface:#1C2329;--text:#F6F8FA;--text-muted:#BAC4CC;--border:#38434C;--link:#FFA06A;--focus:#FFC18F;' +
        '--ok:#7BD88F;--warn:#FFC857;--err:#FF8A80;';
    var TOKENS =
        ':root{color-scheme:light;--brand-ink:#23272B;--brand-orange:#F26B1D;--on-accent:#23272B;' +
        '--bg:#FFFFFF;--surface:#F6F7F8;--text:#23272B;--text-muted:#59636B;--border:#DCE1E5;--link:#AA410B;--focus:#F26B1D;' +
        '--ok:#1B5E20;--warn:#7A4F00;--err:#B3261E;' +
        '--bh-font-ui:Inter,system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;' +
        '--bh-font-head:Montserrat,Inter,system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}' +
        '@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;' + DARK + '}}' +
        ':root[data-theme="dark"]{color-scheme:dark;' + DARK + '}' +
        '[id^="bh-"]:focus-visible,[id^="bricohams-"]:focus-visible,[class^="bha-"]:focus-visible,' +
        '[id^="bh-"] :focus-visible,[id^="bricohams-"] :focus-visible{outline:3px solid var(--focus);outline-offset:3px}';

    function get() {
        try { var t = localStorage.getItem(KEY); return t === 'light' || t === 'dark' ? t : 'system'; } catch (e) { return 'system'; }
    }
    function set(t) {
        var root = document.documentElement;
        if (t === 'light' || t === 'dark') root.setAttribute('data-theme', t); else root.removeAttribute('data-theme');
        try { if (t === 'light' || t === 'dark') localStorage.setItem(KEY, t); else localStorage.removeItem(KEY); } catch (e) { /* sin almacenamiento */ }
    }
    set(get());
    if (!document.getElementById('bh-brand-tokens')) {
        var s = document.createElement('style');
        s.id = 'bh-brand-tokens';
        s.textContent = TOKENS;
        document.head.appendChild(s);
    }
    window.BricoHamsTheme = { get: get, set: set };
})();

Plugins.marca.init = function () {
    var cfg = window.marca_config || {};
    var LOGO = cfg.logo || 'static/plugins/receiver/marca/bricohams-logo.png';
    var URL_PORTAL = cfg.url || '/bricohams/';
    var TITULO = cfg.titulo || 'BricoHams';

    var st = document.createElement('style');
    // The original PNG is never filtered; it sits on a white plate because the OpenWebRX+ header is dark.
    st.textContent = 'img.bh-marca-logo{height:40px;width:auto;max-width:180px;object-fit:contain;padding:5px 8px;border-radius:10px;' +
        'background:#FFFFFF;box-sizing:content-box;vertical-align:middle}' +
        '@media (max-width:600px){img.bh-marca-logo{height:28px}}' +
        // Etiquetas de frecuencia: fondo amarillo/cian/verde de OpenWebRX+ con el texto claro de los
        // temas (Rig Skin) no se leían; texto grafito y sin sombra en todas.
        '#openwebrx-bookmarks-container .bookmark,#openwebrx-bookmarks-container .bookmark .bookmark-content' +
        '{color:var(--on-accent,#23272B) !important;text-shadow:none !important;font-weight:600}';
    document.head.appendChild(st);

    function cambiar(intentos) {
        var original = document.querySelector('.webrx-top-logo:not(.bh-marca-logo)');
        if (!original) {
            if (intentos > 0) setTimeout(function () { cambiar(intentos - 1); }, 500);
            return;
        }
        var img = document.createElement('img');
        img.className = 'webrx-top-logo bh-marca-logo';
        img.src = LOGO;
        img.alt = TITULO;
        img.title = TITULO;
        // Si la imagen no está, se deja el logo original
        img.addEventListener('error', function () { img.replaceWith(original); });
        var enlace = original.closest('a');
        if (enlace) {
            enlace.href = URL_PORTAL;
            enlace.removeAttribute('target');
            enlace.title = TITULO;
        }
        original.replaceWith(img);
    }
    cambiar(20);
    return true;
};
