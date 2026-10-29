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
Plugins.marca._version = '1.0.0';
Plugins.marca.no_css = true;

Plugins.marca.init = function () {
    var cfg = window.marca_config || {};
    var LOGO = cfg.logo || 'static/plugins/receiver/marca/bricohams-logo.png';
    var URL_PORTAL = cfg.url || '/bricohams/';
    var TITULO = cfg.titulo || 'BricoHams';

    var st = document.createElement('style');
    st.textContent = 'img.bh-marca-logo{height:52px;width:auto;max-width:190px;object-fit:contain;padding:0;border-radius:6px;vertical-align:middle}' +
        '@media (max-width:600px){img.bh-marca-logo{height:36px}}' +
        // Etiquetas de frecuencia: fondo amarillo/cian/verde de OpenWebRX+ con el texto claro de los
        // temas (Rig Skin) no se leían; texto oscuro y sin sombra en todas.
        '#openwebrx-bookmarks-container .bookmark,#openwebrx-bookmarks-container .bookmark .bookmark-content' +
        '{color:#111 !important;text-shadow:none !important;font-weight:600}';
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
