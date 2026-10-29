/*
 * consentimiento: aviso de cookies y de contenido de terceros para OpenWebRX+ (BricoHams)
 *
 * Guarda la elección en la cookie propia «bh_consent» (necesaria, 180 días) y en localStorage.
 *   v1.terceros   = acepta cargar contenido de terceros (fotos de aviones en el mapa)
 *   v1.necesarias = solo lo imprescindible; las fotos externas quedan como enlace
 *
 * API para otros plugins:
 *   Plugins.consentimiento.estado()      -> 'terceros' | 'necesarias' | null
 *   Plugins.consentimiento.terceros()    -> true si se aceptó contenido de terceros
 *   Plugins.consentimiento.listo         -> Promise que se resuelve cuando hay elección
 *   Plugins.consentimiento.guardar(v)    -> guarda 'terceros' o 'necesarias'
 *   Plugins.consentimiento.abrir()       -> vuelve a mostrar el aviso
 *   window 'bh-consentimiento'           -> evento con detail.estado al cambiar
 *
 * Ajustes en init.js:
 *   window.consentimiento_config = { politicas: '/bricohams/politicas.html', privacidad: '/bricohams/privacidad.html', dias: 180 };
 */
Plugins.consentimiento._version = '1.0.0';
Plugins.consentimiento.no_css = true;

Plugins.consentimiento.init = function () {
    var cfg = window.consentimiento_config || {};
    var POLITICAS = cfg.politicas || '/bricohams/politicas.html';
    var PRIVACIDAD = cfg.privacidad || '/bricohams/privacidad.html';
    var DIAS = Math.max(1, Math.min(365, +cfg.dias || 180));
    var NOMBRE = 'bh_consent';
    var VERSION = 'v1';
    var VALIDOS = ['terceros', 'necesarias'];
    var self = Plugins.consentimiento;
    var estado = null;
    var resolver;
    var banner = null;

    self.listo = new Promise(function (resolve) { resolver = resolve; });

    function es() {
        if (Plugins.idioma && typeof Plugins.idioma.actual === 'function') return Plugins.idioma.actual() === 'es';
        return (navigator.language || '').toLowerCase().indexOf('es') === 0;
    }

    function leerCookie() {
        var partes = document.cookie ? document.cookie.split(';') : [];
        for (var i = 0; i < partes.length; i++) {
            var p = partes[i].trim();
            if (p.indexOf(NOMBRE + '=') === 0) {
                try { return decodeURIComponent(p.substring(NOMBRE.length + 1)); } catch (e) { return null; }
            }
        }
        return null;
    }

    function interpretar(valor) {
        if (!valor) return null;
        var p = String(valor).split('.');
        return (p.length === 2 && p[0] === VERSION && VALIDOS.indexOf(p[1]) >= 0) ? p[1] : null;
    }

    // La cookie manda: si caducó, se vuelve a preguntar aunque quede copia en localStorage
    function leer() {
        var v = interpretar(leerCookie());
        if (!v) { try { localStorage.removeItem(NOMBRE); } catch (e) { /* sin almacenamiento */ } }
        return v;
    }

    function cerrar() {
        if (banner) { banner.remove(); banner = null; }
    }

    function guardar(valor) {
        if (VALIDOS.indexOf(valor) < 0) return;
        var dato = VERSION + '.' + valor;
        document.cookie = NOMBRE + '=' + encodeURIComponent(dato) + '; Path=/; Max-Age=' + (DIAS * 86400) +
            '; SameSite=Lax' + (location.protocol === 'https:' ? '; Secure' : '');
        try { localStorage.setItem(NOMBRE, dato); } catch (e) { /* sin almacenamiento: queda la cookie */ }
        estado = valor;
        cerrar();
        resolver(valor);
        try { window.dispatchEvent(new CustomEvent('bh-consentimiento', { detail: { estado: valor } })); } catch (e) { /* navegador antiguo */ }
    }

    function abrir() {
        cerrar();
        var spanish = es();
        banner = document.createElement('section');
        banner.id = 'bh-consentimiento';
        banner.setAttribute('role', 'dialog');
        banner.setAttribute('aria-live', 'polite');
        banner.setAttribute('aria-label', spanish ? 'Cookies y privacidad' : 'Cookies and privacy');
        banner.innerHTML =
            '<style>#bh-consentimiento{position:fixed;left:50%;bottom:16px;transform:translateX(-50%);z-index:10030;box-sizing:border-box;' +
            'width:min(680px,calc(100vw - 24px));padding:16px 18px;border:1px solid #383838;border-radius:10px;background:#111;color:#ddd;' +
            'font:14px/1.5 system-ui,sans-serif;box-shadow:0 10px 40px #000}' +
            '#bh-consentimiento h2{margin:0 0 6px;font-size:17px;color:#fff}#bh-consentimiento p{margin:0 0 10px;color:#bbb}' +
            '#bh-consentimiento a{color:#8ab4f8}#bh-consentimiento .bh-c-btns{display:flex;flex-wrap:wrap;gap:8px}' +
            '#bh-consentimiento button{flex:1 1 180px;padding:10px;border:0;border-radius:7px;font:600 14px system-ui,sans-serif;cursor:pointer}' +
            '#bh-consentimiento .bh-c-si{background:#2868d7;color:#fff}#bh-consentimiento .bh-c-no{background:#272727;color:#ddd}</style>' +
            '<h2></h2><p class="bh-c-txt"></p><p class="bh-c-links"><a target="_blank" rel="noopener"></a> · <a target="_blank" rel="noopener"></a></p>' +
            '<div class="bh-c-btns"><button type="button" class="bh-c-si"></button><button type="button" class="bh-c-no"></button></div>';
        banner.querySelector('h2').textContent = spanish ? '🍪 Cookies y privacidad' : '🍪 Cookies and privacy';
        banner.querySelector('.bh-c-txt').textContent = spanish
            ? 'Este receptor usa solo cookies propias necesarias (tu elección y la sesión del operador) y almacenamiento local para tus preferencias. ' +
              'Aviones (ADS-B) y barcos (AIS) del mapa salen de la recepción local de esta estación. ' +
              'Si aceptas todo, la ficha de cada avión cargará su foto desde servicios externos (map.flights, Planespotters), que reciben tu IP.'
            : 'This receiver only uses necessary first-party cookies (your choice and the operator session) and local storage for your preferences. ' +
              'Aircraft (ADS-B) and ships (AIS) on the map come from this station\'s own local reception. ' +
              'If you accept all, each aircraft card will load its photo from external services (map.flights, Planespotters), which receive your IP.';
        var enlaces = banner.querySelectorAll('.bh-c-links a');
        enlaces[0].href = POLITICAS;
        enlaces[0].textContent = spanish ? 'Políticas de seguridad, datos y cookies' : 'Security, data and cookie policies';
        enlaces[1].href = PRIVACIDAD;
        enlaces[1].textContent = spanish ? 'Aviso de privacidad' : 'Privacy notice';
        var si = banner.querySelector('.bh-c-si');
        var no = banner.querySelector('.bh-c-no');
        si.textContent = spanish ? 'Aceptar todo' : 'Accept all';
        no.textContent = spanish ? 'Solo necesarias' : 'Necessary only';
        si.addEventListener('click', function () { guardar('terceros'); });
        no.addEventListener('click', function () { guardar('necesarias'); });
        document.body.appendChild(banner);
        si.focus();
    }

    self.estado = function () { return estado; };
    self.terceros = function () { return estado === 'terceros'; };
    self.guardar = guardar;
    self.abrir = abrir;

    estado = leer();
    if (estado) resolver(estado);
    if (!estado || location.hash === '#cookies') abrir();
    window.addEventListener('bh-idioma', function () { if (banner) abrir(); });
    return true;
};
