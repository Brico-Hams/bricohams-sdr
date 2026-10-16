/*
 * Puente entre BricoHams y los plugins de EA5HKX (gitlab.com/openwebrx-plugins).
 * - callsign_gate: pone el indicativo de esta estación y su Telegram en la ventana de bienvenida,
 *   añade el crédito a EA5HKX y el aviso de privacidad, y (si CALLSIGN_GATE_ANUNCIO=no) no deja
 *   que su mensaje automático «Chat iniciado por …» llegue al chat ni, por tanto, a Telegram.
 * - tone_detector no necesita puente: usa sus propios identificadores.
 * Los plugins de EA5HKX no se modifican: install.sh los descarga en un commit fijo y comprueba su sha256.
 */
Plugins.ea5hkx_puente.no_css = true;

Plugins.ea5hkx_puente.init = function () {
    var cfg = window.ea5hkx_config || {};
    var api = Plugins.ea5hkx_puente;
    var GATE_ID = 'owrx-callsign-gate';
    var ANUNCIO = /^\s*Chat iniciado por\s/i;
    var spanish = (Plugins.idioma && typeof Plugins.idioma.actual === 'function')
        ? Plugins.idioma.actual() === 'es'
        : (navigator.language || '').toLowerCase().indexOf('es') === 0;

    function titulo() {
        var t = String(cfg.titulo || '').trim();
        return t && t.indexOf('__') !== 0 ? t : 'BricoHams';
    }

    function canal(url) {
        var m = /t\.me\/([A-Za-z0-9_]{3,})/.exec(url || '');
        return m ? '@' + m[1] : '';
    }

    function enlace(href, texto) {
        var a = document.createElement('a');
        a.href = href;
        a.target = '_blank';
        a.rel = 'noopener';
        a.style.cssText = 'color:#8ab4f8;text-decoration:none';
        a.textContent = texto;
        return a;
    }

    function adaptar(gate) {
        if (!gate || gate.getAttribute('data-bh-puente')) return false;
        gate.setAttribute('data-bh-puente', '1');
        Array.prototype.forEach.call(gate.querySelectorAll('h2'), function (h) {
            h.textContent = h.textContent.replace(/EA5HKX/g, titulo());
        });
        var telegram = gate.querySelector('a[href*="t.me/"]');
        var parrafo = telegram && telegram.parentNode;
        if (parrafo) {
            var nombreCanal = canal(cfg.telegram);
            if (nombreCanal) {
                while (parrafo.firstChild) parrafo.removeChild(parrafo.firstChild);
                parrafo.appendChild(document.createTextNode(spanish
                    ? '💬 Comunidad y avisos en Telegram: '
                    : '💬 Community and news on Telegram: '));
                var a = enlace(cfg.telegram, nombreCanal);
                a.style.fontWeight = 'bold';
                parrafo.appendChild(a);
            } else {
                parrafo.parentNode.removeChild(parrafo);
            }
        }
        var pie = document.createElement('p');
        pie.className = 'bh-ea5hkx-pie';
        pie.style.cssText = 'margin:14px 0 0;color:#888;font-size:12px;line-height:1.5;text-align:center';
        pie.appendChild(document.createTextNode(spanish
            ? 'Se guarda solo en este navegador durante 14 días. '
            : 'Stored only in this browser for 14 days. '));
        pie.appendChild(enlace(cfg.privacidad || '/bricohams/privacidad.html', spanish ? 'Aviso de privacidad' : 'Privacy notice'));
        pie.appendChild(document.createTextNode(' · '));
        pie.appendChild(enlace('https://gitlab.com/openwebrx-plugins/callsign_gate', spanish ? 'plugin de EA5HKX' : 'plugin by EA5HKX'));
        (gate.firstElementChild || gate).appendChild(pie);
        return true;
    }

    // Sin CALLSIGN_GATE_ANUNCIO el «Chat iniciado por …» de cada visita no sale (ni al chat ni a Telegram)
    function filtrarAnuncio() {
        if (cfg.anuncio) return true;
        if (typeof Chat === 'undefined' || !Chat || typeof Chat.send !== 'function') return false;
        if (Chat._bhEa5hkx) return true;
        var send = Chat.send;
        Chat.send = function () {
            var msg = document.getElementById('openwebrx-chat-message');
            if (msg && ANUNCIO.test(msg.value)) {
                msg.value = '';
                return;
            }
            return send.apply(this, arguments);
        };
        Chat._bhEa5hkx = true;
        return true;
    }

    api.adaptar = adaptar;
    api.filtrarAnuncio = filtrarAnuncio;

    if (!cfg.callsign_gate) return true;
    if (!filtrarAnuncio()) {
        var intentos = 0;
        (function reintentar() {
            if (filtrarAnuncio() || ++intentos > 40) return;
            setTimeout(reintentar, 250);
        })();
    }
    adaptar(document.getElementById(GATE_ID));
    if (typeof MutationObserver === 'function' && document.body) {
        new MutationObserver(function (cambios) {
            cambios.forEach(function (c) {
                Array.prototype.forEach.call(c.addedNodes, function (n) {
                    if (n.nodeType === 1 && n.id === GATE_ID) adaptar(n);
                });
            });
        }).observe(document.body, {childList: true});
    }
    return true;
};
