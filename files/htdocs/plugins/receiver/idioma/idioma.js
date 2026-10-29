/*
 * idioma: botón ES/EN para la interfaz de OpenWebRX+ (BricoHams)
 *
 * OpenWebRX+ viene en inglés y no trae traducciones. Este plugin cambia en el navegador
 * los textos de la interfaz (barra superior, panel del receptor, chat y diálogos) entre
 * español e inglés, sin tocar los ficheros del paquete. La elección se guarda en
 * localStorage («bh_idioma»). Por defecto se usa el idioma del navegador.
 *
 * API para otros plugins:
 *   Plugins.idioma.actual()        -> 'es' | 'en'
 *   Plugins.idioma.t(es, en)       -> el texto del idioma activo
 *   Plugins.idioma.cambiar('en')   -> cambia el idioma
 *   window 'bh-idioma'             -> evento con detail.idioma al cambiar
 *
 * Textos propios bilingües (descripción del receptor, avisos…): marca cada versión con
 * data-lang="es" o data-lang="en"; solo se muestra la del idioma activo.
 */
Plugins.idioma._version = '1.1.0';
Plugins.idioma.no_css = true;

Plugins.idioma.init = function () {
    var cfg = window.idioma_config || {};
    var CLAVE = 'bh_idioma';
    var ES = {
        'Help': 'Ayuda', 'Status': 'Estado', 'Receiver': 'Receptor', 'Map': 'Mapa', 'Files': 'Archivos', 'Settings': 'Ajustes',
        'Tune down': 'Bajar frecuencia', 'Tune up': 'Subir frecuencia', 'Add bookmark...': 'Añadir marcador...',
        'Mute on/off': 'Silencio sí/no', 'Volume': 'Volumen', 'Tuning step': 'Paso de sintonía',
        'Name': 'Nombre', 'Message': 'Mensaje', 'Send': 'Enviar', 'OpenWebRX+ message log': 'Registro de mensajes de OpenWebRX+',
        'Modes': 'Modos', 'Controls': 'Controles', 'Display': 'Pantalla',
        'Auto-set squelch level (right-click for scanner)': 'Ajuste automático del silenciador (clic derecho: escáner)',
        'Noise reduction on/off': 'Reducción de ruido sí/no', 'Noise reduction level': 'Nivel de reducción de ruido',
        'Record audio': 'Grabar audio', 'Zoom in one step': 'Acercar un paso', 'Zoom out one step': 'Alejar un paso',
        'Zoom in totally': 'Acercar al máximo', 'Zoom out totally': 'Alejar al máximo',
        'Auto-adjust waterfall colors (right-click for continuous)': 'Ajuste automático de colores de la cascada (clic derecho: continuo)',
        'Set waterfall colors to default': 'Colores de la cascada por defecto',
        'Waterfall maximum level': 'Nivel máximo de la cascada', 'Waterfall minimum level': 'Nivel mínimo de la cascada',
        'Waterfall theme': 'Tema de la cascada', 'Reset waterfall theme': 'Restablecer tema de la cascada',
        'Theme': 'Tema', 'Reset theme': 'Restablecer tema', 'Opacity': 'Opacidad', 'Toggle opacity bump': 'Alternar opacidad extra',
        'Toggle spectrum display': 'Mostrar/ocultar espectro', 'Show band plan ribbon': 'Mostrar plan de bandas',
        'Show pointer frequency': 'Mostrar frecuencia del puntero', 'Hold mouse wheel down to tune': 'Mantener la rueda pulsada para sintonizar',
        'Draw white frame around panels': 'Marco blanco alrededor de los paneles',
        'Edit Bookmark': 'Editar marcador', 'Name:': 'Nombre:', 'Frequency:': 'Frecuencia:', 'Modulation:': 'Modulación:',
        'Underlying:': 'Modo base:', 'Description:': 'Descripción:', 'Scannable': 'Escaneable', 'Cancel': 'Cancelar',
        'Start OpenWebRX+': 'Iniciar OpenWebRX+', 'Error Message:': 'Mensaje de error:', 'Default': 'Predeterminado',
        'Timeslot 1': 'Intervalo 1', 'Timeslot 2': 'Intervalo 2',
        'Clients': 'Clientes', 'Server CPU': 'CPU del servidor', 'Audio stream': 'Flujo de audio',
        'Waterfall stream': 'Flujo de la cascada', 'Network usage': 'Uso de red', 'Audio buffer': 'Búfer de audio',
        'Audio output': 'Salida de audio'
    };
    var EN = {};
    Object.keys(ES).forEach(function (k) { EN[ES[k]] = k; });
    var ATRIBUTOS = ['title', 'placeholder', 'aria-label', 'alt'];
    // Contenido de usuarios y ventanas propias: no se traduce
    var EXCLUIR = '#openwebrx-messages, #openwebrx-chat-messages, .openwebrx-chat-message, .openwebrx-message, ' +
        '#bh-consentimiento, .bh-identificacion-overlay, script, style, textarea';

    function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
    function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* sin almacenamiento */ } }

    var guardado = lsGet(CLAVE);
    var lang = (guardado === 'es' || guardado === 'en') ? guardado
        : (cfg.defecto === 'es' || cfg.defecto === 'en') ? cfg.defecto
        : ((navigator.language || '').toLowerCase().indexOf('es') === 0 ? 'es' : 'en');

    function traducir(texto) {
        var m = /^([\s\u00a0\u25b2-\u25bf]*)([\s\S]*?)(\s*)$/.exec(texto);
        if (!m || !m[2]) return null;
        var r = (lang === 'es' ? ES : EN)[m[2]];
        return (r && r !== m[2]) ? m[1] + r + m[3] : null;
    }

    function excluido(el) {
        return !el || (el.closest && el.closest(EXCLUIR));
    }

    function procesarElemento(el) {
        if (excluido(el)) return;
        for (var i = 0; i < ATRIBUTOS.length; i++) {
            var v = el.getAttribute && el.getAttribute(ATRIBUTOS[i]);
            if (v) {
                var r = traducir(v);
                if (r !== null) el.setAttribute(ATRIBUTOS[i], r);
            }
        }
    }

    function bilingue(raiz) {
        if (!raiz || raiz.nodeType !== 1) return;
        var els = [].slice.call(raiz.querySelectorAll('[data-lang]'));
        if (raiz.hasAttribute('data-lang')) els.push(raiz);
        els.forEach(function (el) { el.style.display = el.getAttribute('data-lang') === lang ? '' : 'none'; });
    }

    function procesar(raiz) {
        if (!raiz) return;
        bilingue(raiz);
        if (raiz.nodeType === 3) {
            if (!excluido(raiz.parentElement)) {
                var r = traducir(raiz.nodeValue);
                if (r !== null) raiz.nodeValue = r;
            }
            return;
        }
        if (raiz.nodeType !== 1 || excluido(raiz)) return;
        procesarElemento(raiz);
        var els = raiz.querySelectorAll('[title], [placeholder], [aria-label], [alt]');
        for (var i = 0; i < els.length; i++) procesarElemento(els[i]);
        var walker = document.createTreeWalker(raiz, NodeFilter.SHOW_TEXT, null);
        var nodos = [];
        while (walker.nextNode()) nodos.push(walker.currentNode);
        nodos.forEach(function (n) {
            if (excluido(n.parentElement)) return;
            var t = traducir(n.nodeValue);
            if (t !== null) n.nodeValue = t;
        });
    }

    var pendientes = [];
    var programado = false;
    function encolar(nodo) {
        pendientes.push(nodo);
        if (programado) return;
        programado = true;
        setTimeout(function () {
            programado = false;
            var lista = pendientes;
            pendientes = [];
            lista.forEach(procesar);
        }, 60);
    }

    var $btn = $('<div class="button" id="bh-idioma-button"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" ' +
        'style="width:18px;height:18px"><path d="M4 5h9M8.5 3v2M11 5c-.8 4-3.4 7-6.5 8.5M6.5 8.5c1.2 2 3 3.5 5 4.3"/>' +
        '<path d="M13 21l4-10 4 10M14.4 17.5h5.2"/></svg><br><span class="bh-idioma-txt"></span></div>');

    function pintarBoton() {
        $btn.find('.bh-idioma-txt').text(lang === 'es' ? 'ES' : 'EN');
        $btn.attr('title', lang === 'es' ? 'Idioma: español · cambiar a inglés' : 'Language: English · switch to Spanish');
    }

    function cambiar(nuevo) {
        if (nuevo !== 'es' && nuevo !== 'en') return;
        lang = nuevo;
        lsSet(CLAVE, lang);
        document.documentElement.setAttribute('lang', lang);
        pintarBoton();
        procesar(document.body);
        try { window.dispatchEvent(new CustomEvent('bh-idioma', { detail: { idioma: lang } })); } catch (e) { /* navegador antiguo */ }
    }

    Plugins.idioma.actual = function () { return lang; };
    Plugins.idioma.t = function (es, en) { return lang === 'es' ? es : en; };
    Plugins.idioma.cambiar = cambiar;

    function colocar(intentos) {
        var $bar = $('.openwebrx-main-buttons').first();
        if (!$bar.length && intentos > 0) { setTimeout(function () { colocar(intentos - 1); }, 500); return; }
        var $ajustes = $bar.find('a.button[href$="settings"]').last();
        if ($ajustes.length) $ajustes.after($btn); else $bar.append($btn);
    }

    pintarBoton();
    colocar(24);
    $btn.on('click', function () { cambiar(lang === 'es' ? 'en' : 'es'); });
    document.documentElement.setAttribute('lang', lang);
    procesar(document.body);
    new MutationObserver(function (cambios) {
        cambios.forEach(function (c) {
            if (c.type === 'attributes') encolar(c.target);
            else for (var i = 0; i < c.addedNodes.length; i++) encolar(c.addedNodes[i]);
        });
    }).observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ATRIBUTOS });
    return true;
};
