/*
 * Registro voluntario de oyentes: guarda indicativo/nombre solo tras consentimiento.
 * Registro obligatorio para el chat: sin indicativo o nombre no se puede escribir
 * (se guarda solo en el navegador; el registro en el servidor sigue siendo voluntario).
 */
Plugins.identificacion.no_css = true;

Plugins.identificacion.init = function () {
    var cfg = window.identificacion_config || {};
    var endpoint = cfg.endpoint || '/bricohams/api/oyentes';
    var privacidad = cfg.privacidad || '/bricohams/privacidad.html';
    var consentKey = 'bh_identificacion_consent';
    var declinedKey = 'bh_identificacion_declined';
    var sessionKey = 'bh_identificacion_session';
    var spanish = (Plugins.idioma && typeof Plugins.idioma.actual === 'function')
        ? Plugins.idioma.actual() === 'es'
        : (navigator.language || '').toLowerCase().indexOf('es') === 0;
    var callPattern = /^(?:[A-Z0-9]{1,3}[0-9][A-Z0-9]{0,4}[A-Z](?:\/[A-Z0-9]{1,4})?|[A-Z0-9]{1,4}\/[A-Z0-9]{3,7})$/;
    var namePattern = /^[\p{L}][\p{L}\p{M}\s.'’-]{1,79}$/u;
    var api = Plugins.identificacion;
    var chatObligatorio = cfg.chat_obligatorio !== false;
    var chatKey = 'bh_chat_identidad';
    var chatDias = Number(cfg.chat_dias) > 0 ? Number(cfg.chat_dias) : 14;
    var DIA = 24 * 60 * 60 * 1000;
    var registroDisponible = false;
    var abierto = null;

    function esValido(value) {
        var v = String(value || '').trim();
        return callPattern.test(v.toUpperCase()) || namePattern.test(v);
    }

    function normalizar(value) {
        var v = String(value || '').trim().replace(/\s+/g, ' ');
        return callPattern.test(v.toUpperCase()) ? v.toUpperCase() : v;
    }

    function storageGet(storage, key) {
        try { return storage.getItem(key); } catch (e) { return null; }
    }

    function storageSet(storage, key, value) {
        try { storage.setItem(key, value); } catch (e) { console.warn('No se pudo guardar la preferencia de identificación', e); }
    }

    // Plugin callsign_gate de EA5HKX: su indicativo (14 días) también vale para el chat
    var gateKey = 'openwebrx_callsign';
    var gateTsKey = 'openwebrx_callsign_ts';
    var gatePattern = /^[A-Z0-9][A-Z0-9\/-]{2,14}$/;

    // Identidad del chat: la más reciente entre la del chat (chat_dias), la de callsign_gate (14 días)
    // y la del registro voluntario (180 días)
    function chatIdentidad() {
        var mejor = {nombre: '', ts: -1};
        function candidato(nombre, ts, dias, extra) {
            nombre = String(nombre || '').trim();
            ts = Number(ts) || 0;
            if (!nombre || !(esValido(nombre) || (extra && extra.test(nombre.toUpperCase())))) return;
            if (Date.now() - ts < dias * DIA && ts > mejor.ts) mejor = {nombre: normalizar(nombre), ts: ts};
        }
        try {
            var d = JSON.parse(storageGet(localStorage, chatKey) || 'null');
            if (d) candidato(d.nombre, d.ts, chatDias);
        } catch (e) { /* valor corrupto: se pide de nuevo */ }
        candidato(storageGet(localStorage, gateKey), parseInt(storageGet(localStorage, gateTsKey), 10), 14, gatePattern);
        try {
            var c = JSON.parse(storageGet(localStorage, consentKey) || 'null');
            if (c) candidato(c.identificador, c.aceptado, 180);
        } catch (e) { /* idem */ }
        return mejor.nombre;
    }

    function chatAplicar() {
        var nameInput = document.getElementById('openwebrx-chat-name');
        var msgInput = document.getElementById('openwebrx-chat-message');
        if (!nameInput || !msgInput) return false;
        var nombre = chatIdentidad();
        if (nombre && typeof Chat !== 'undefined' && Chat && typeof Chat.setNickname === 'function') Chat.setNickname(nombre);
        nameInput.value = nombre;
        nameInput.readOnly = true;
        nameInput.placeholder = spanish ? 'Indicativo' : 'Callsign';
        nameInput.title = spanish ? 'Clic para cambiar tu indicativo o nombre' : 'Click to change your callsign or name';
        msgInput.readOnly = !nombre;
        msgInput.placeholder = nombre ? (spanish ? 'Mensaje' : 'Message')
            : (spanish ? '🔒 Identifícate para usar el chat (clic aquí)' : '🔒 Identify yourself to use the chat (click here)');
        return true;
    }

    function chatGuardar(nombre) {
        nombre = normalizar(nombre);
        if (!esValido(nombre)) return '';
        storageSet(localStorage, chatKey, JSON.stringify({nombre: nombre, ts: Date.now()}));
        if (storageGet(localStorage, gateKey) !== null) {   // así callsign_gate no vuelve al nombre anterior
            storageSet(localStorage, gateKey, nombre);
            storageSet(localStorage, gateTsKey, String(Date.now()));
        }
        chatAplicar();
        return nombre;
    }

    function chatInstalar() {
        if (typeof Chat === 'undefined' || !Chat || typeof Chat.send !== 'function' || !chatAplicar()) return false;
        if (Chat._bhRegistro) return true;
        var send = Chat.send;
        var sendMessage = Chat.sendMessage;
        Chat.send = function () {
            if (!chatIdentidad()) { api.chat.abrir(); return; }
            return send.apply(this, arguments);
        };
        // Último filtro: nada sale al chat sin identidad y siempre con la identidad guardada
        Chat.sendMessage = function (text) {
            var nombre = chatIdentidad();
            if (!nombre) { api.chat.abrir(); return; }
            return sendMessage.call(this, text, nombre);
        };
        Chat._bhRegistro = true;
        var msgInput = document.getElementById('openwebrx-chat-message');
        var pedir = function () { if (!chatIdentidad()) api.chat.abrir(); };
        msgInput.addEventListener('focus', pedir);
        msgInput.addEventListener('click', pedir);
        document.getElementById('openwebrx-chat-name').addEventListener('click', function () { api.chat.abrir(true); });
        return true;
    }

    function makeDialog(modo, cambiar) {
        var chat = modo === 'chat';
        var overlay = document.createElement('div');
        overlay.className = 'bh-identificacion-overlay';
        overlay.innerHTML =
            '<section class="bh-identificacion-dialog" role="dialog" aria-modal="true" aria-labelledby="bh-identificacion-title">' +
            '<h2 id="bh-identificacion-title"></h2><p class="bh-identificacion-intro"></p>' +
            '<p class="bh-identificacion-purpose"></p><hr><label class="bh-identificacion-label" for="bh-identificacion-value"></label>' +
            '<input id="bh-identificacion-value" maxlength="80" autocomplete="nickname" />' +
            '<label class="bh-identificacion-consent"><input type="checkbox" /> <span></span></label>' +
            '<p class="bh-identificacion-error" role="alert" aria-live="polite"></p>' +
            '<button class="bh-identificacion-submit" type="button"></button>' +
            '<button class="bh-identificacion-skip" type="button"></button>' +
            '<p class="bh-identificacion-privacy"></p></section>';
        document.body.appendChild(overlay);

        var style = document.createElement('style');
        style.textContent =
            '.bh-identificacion-overlay{position:fixed;inset:0;z-index:10020;display:flex;align-items:center;justify-content:center;' +
            'padding:16px;background:rgba(0,0,0,.78);font:14px/1.55 system-ui,sans-serif;color:#eee}' +
            '.bh-identificacion-dialog{box-sizing:border-box;width:min(524px,100%);max-height:90vh;overflow:auto;padding:26px 28px;' +
            'border:1px solid #383838;border-radius:12px;background:#111;box-shadow:0 12px 44px #000}' +
            '.bh-identificacion-dialog h2{margin:0 0 8px;font-size:21px}.bh-identificacion-dialog p{color:#bbb}' +
            '.bh-identificacion-dialog hr{border:0;border-top:1px solid #333;margin:18px 0}' +
            '.bh-identificacion-dialog input:not([type=checkbox]){box-sizing:border-box;width:100%;margin:8px 0 12px;padding:12px;' +
            'border:1px solid #444;border-radius:8px;background:#1c1c1c;color:#fff;font:inherit}' +
            '.bh-identificacion-consent{display:flex;align-items:flex-start;gap:8px;margin:4px 0 12px;color:#ccc}' +
            '.bh-identificacion-consent input{margin-top:5px}.bh-identificacion-dialog button{width:100%;padding:11px;margin-top:8px;' +
            'border:0;border-radius:8px;font:600 15px system-ui,sans-serif;cursor:pointer}' +
            '.bh-identificacion-submit{background:#2868d7;color:#fff}.bh-identificacion-submit:disabled{opacity:.55;cursor:not-allowed}' +
            '.bh-identificacion-skip{background:#272727;color:#ddd}.bh-identificacion-privacy{font-size:12px}' +
            '.bh-identificacion-dialog a{color:#8ab4f8}.bh-identificacion-error{min-height:1.4em;color:#ff8a80!important}' +
            '@media(max-width:480px){.bh-identificacion-dialog{padding:20px}}';
        document.head.appendChild(style);

        var title = overlay.querySelector('h2');
        var intro = overlay.querySelector('.bh-identificacion-intro');
        var purpose = overlay.querySelector('.bh-identificacion-purpose');
        var label = overlay.querySelector('.bh-identificacion-label');
        var input = overlay.querySelector('#bh-identificacion-value');
        var checkbox = overlay.querySelector('.bh-identificacion-consent input');
        var consentText = overlay.querySelector('.bh-identificacion-consent span');
        var submit = overlay.querySelector('.bh-identificacion-submit');
        var skip = overlay.querySelector('.bh-identificacion-skip');
        var error = overlay.querySelector('.bh-identificacion-error');
        var privacy = overlay.querySelector('.bh-identificacion-privacy');

        title.textContent = chat ? (spanish ? '💬 Identifícate para el chat' : '💬 Identify yourself to chat')
            : (spanish ? '📡 Bienvenido/a al SDR' : '📡 Welcome to the SDR');
        intro.textContent = chat
            ? (spanish
                ? 'Para escribir en el chat es obligatorio indicar tu indicativo de radioaficionado o, si no tienes, tu nombre. Aparecerá junto a tus mensajes. Para escuchar no hace falta.'
                : 'To write in the chat you must enter your amateur radio callsign or, if you have none, your name. It will be shown next to your messages. Listening does not require it.')
            : (spanish
                ? '¿Tienes indicativo de radioaficionado? Introdúcelo aquí. Si no, puedes usar tu nombre o apodo, o continuar sin identificarte.'
                : 'Have an amateur radio callsign? Enter it here. Otherwise, use your name or nickname, or continue without identifying yourself.');
        purpose.textContent = chat
            ? (spanish ? 'Se guarda solo en este navegador durante ' + chatDias + ' días.'
                : 'It is stored only in this browser for ' + chatDias + ' days.')
            : (spanish
                ? 'Tu participación ayuda a conocer el uso del receptor y mejorarlo para la comunidad.'
                : 'Your participation helps us understand how the receiver is used and improve it for the community.');
        label.textContent = chat ? (spanish ? 'Indicativo o nombre (obligatorio)' : 'Callsign or name (required)')
            : (spanish ? 'Indicativo o nombre (opcional)' : 'Callsign or name (optional)');
        input.placeholder = spanish ? 'Indicativo (ej. EA5ABC) o nombre' : 'Callsign (e.g. EA5ABC) or name';
        if (!chat || cambiar) input.value = chatIdentidad();
        consentText.textContent = chat
            ? (spanish
                ? 'Además, acepto que se guarde en el registro de oyentes del receptor durante un máximo de 180 días (opcional, sin IP).'
                : 'I also agree to be stored in the receiver listener log for up to 180 days (optional, no IP address).')
            : (spanish
                ? 'Acepto guardar el identificador y la fecha de esta visita durante un máximo de 180 días. No se guardará mi IP.'
                : 'I agree to store my identifier and visit date for up to 180 days. My IP address will not be stored.');
        if (chat && !registroDisponible) checkbox.parentNode.style.display = 'none';
        submit.textContent = chat ? (spanish ? 'Entrar al chat' : 'Join the chat') : (spanish ? 'Acceder / Enter' : 'Enter');
        submit.disabled = true;
        skip.textContent = chat ? (spanish ? 'Cancelar (solo escuchar)' : 'Cancel (listen only)')
            : (spanish ? 'Continuar sin identificarme' : 'Continue without identifying');
        privacy.innerHTML = spanish ? 'Lee el <a target="_blank" rel="noopener" href=""></a>.' : 'Read the <a target="_blank" rel="noopener" href=""></a>.';
        var privacyLink = privacy.querySelector('a');
        privacyLink.href = privacidad;
        privacyLink.textContent = spanish ? 'aviso de privacidad' : 'privacy notice';

        function valid() {
            var value = input.value.trim();
            return (chat || checkbox.checked) && esValido(value);
        }

        function update() {
            submit.disabled = !valid();
            error.textContent = '';
        }
        input.addEventListener('input', update);
        input.addEventListener('keydown', function (event) {
            if (event.key === 'Enter' && !submit.disabled) submit.click();
        });
        checkbox.addEventListener('change', update);

        function close() {
            overlay.remove();
            style.remove();
            abierto = null;
            if (chat && chatIdentidad()) {
                var msg = document.getElementById('openwebrx-chat-message');
                if (msg) msg.focus();
            }
        }

        skip.addEventListener('click', function () {
            if (!chat) storageSet(localStorage, declinedKey, 'yes');
            close();
        });

        submit.addEventListener('click', async function () {
            if (!valid()) return;
            if (chat) chatGuardar(input.value);
            if (chat && !checkbox.checked) { close(); return; }
            submit.disabled = true;
            error.textContent = spanish ? 'Guardando…' : 'Saving…';
            try {
                var response = await fetch(endpoint, {
                    method: 'POST',
                    credentials: 'same-origin',
                    cache: 'no-store',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({identificador: input.value.trim(), consentimiento: true})
                });
                if (!response.ok) throw new Error('HTTP ' + response.status);
                storageSet(localStorage, consentKey, JSON.stringify({
                    identificador: input.value.trim(),
                    aceptado: Date.now()
                }));
                storageSet(sessionStorage, sessionKey, 'sent');
                if (!chat) chatGuardar(input.value);
                close();
            } catch (e) {
                console.error('No se pudo guardar el registro voluntario de oyente', e);
                if (chat) { close(); return; }   // el chat ya queda desbloqueado
                error.textContent = spanish
                    ? 'No se pudo guardar. Puedes reintentar o continuar sin identificarte.'
                    : 'The entry could not be saved. Retry or continue without identifying yourself.';
                update();
            }
        });
        abierto = overlay;
        update();
        input.focus();
        return overlay;
    }

    function enviarSesion(identificador) {
        if (storageGet(sessionStorage, sessionKey) === 'sent') return;
        fetch(endpoint, {
            method: 'POST',
            credentials: 'same-origin',
            cache: 'no-store',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({identificador: identificador, consentimiento: true})
        }).then(function (response) {
            if (!response.ok) throw new Error('HTTP ' + response.status);
            storageSet(sessionStorage, sessionKey, 'sent');
        }).catch(function (e) {
            console.error('No se pudo guardar la sesión del oyente', e);
        });
    }

    api.chat = {
        identidad: chatIdentidad, guardar: chatGuardar, valido: esValido, aplicar: chatAplicar, instalar: chatInstalar,
        abrir: function (cambiar) { if (!abierto) makeDialog('chat', cambiar); }
    };
    if (chatObligatorio) {
        var intentos = 0;
        (function esperarChat() {
            if (chatInstalar() || ++intentos > 40) return;
            setTimeout(esperarChat, 500);
        })();
    }
    var gateActivo = !!(window.ea5hkx_config && window.ea5hkx_config.callsign_gate);
    if (typeof $ === 'function') $(document).on('event:callsign_gate_accepted', function () { chatAplicar(); });

    if (cfg.enabled === false) return true;
    // Primero el aviso de cookies; así no se abren dos ventanas a la vez
    var cookiesListo = Plugins.consentimiento && Plugins.consentimiento.listo;
    Promise.resolve(cookiesListo)
        .then(function () {
            return fetch(cfg.health || '/bricohams/api/salud', {cache: 'no-store', credentials: 'same-origin'});
        })
        .then(function (response) {
            if (!response.ok) throw new Error('HTTP ' + response.status);
            return response.json();
        })
        .then(function (status) {
            if (!status || status.ok !== true) return;
            registroDisponible = true;
            var saved = storageGet(localStorage, consentKey);
            if (saved) {
                try {
                    var consent = JSON.parse(saved);
                    if (consent && typeof consent.identificador === 'string' &&
                        Date.now() - consent.aceptado < 180 * 24 * 60 * 60 * 1000) {
                        enviarSesion(consent.identificador);
                        return;
                    }
                } catch (e) {
                    console.warn('Preferencia de identificación inválida; se solicitará de nuevo');
                }
            }
            if (storageGet(localStorage, declinedKey) === 'yes') return;
            // Con callsign_gate la bienvenida espera a que se identifique (y sale ya rellena)
            if (gateActivo && !chatIdentidad() && typeof $ === 'function') {
                $(document).one('event:callsign_gate_accepted', function () {
                    setTimeout(function () { if (!abierto) makeDialog('bienvenida'); }, 400);
                });
                return;
            }
            if (!abierto) makeDialog('bienvenida');
        })
        .catch(function (e) {
            console.warn('El registro voluntario no está disponible en este receptor', e);
        });
    return true;
};
