/*
 * banderas: bandera del país en los mensajes FT8 / FT4 / FT2 / WSPR / JT65… de OpenWebRX+
 *
 * Autor: BricoHams (v4)
 *
 * El servidor de OpenWebRX+ ya calcula el país de cada indicativo (campos
 * «ccode» y «country» del mensaje). Este plugin pone la bandera delante del
 * mensaje y el nombre del país en el título. Si el mensaje no trae «ccode»,
 * usa Lookup.call2ccode() del propio OpenWebRX+.
 * Además apunta en la consola el mensaje FT2 si existe el modo (decodificador
 * FT2 de BricoHams).
 */

Plugins.banderas._version = '1.0.0';
Plugins.banderas._author='BricoHams';
Plugins.banderas.no_css = true;

Plugins.banderas.bandera = function (cc) {
    if (!cc || cc.length !== 2) return '';
    if (typeof Lookup !== 'undefined' && Lookup.ccode2flag) return Lookup.ccode2flag(cc);
    var A = 0x1F1E6, c = cc.toUpperCase();
    return String.fromCodePoint(A + c.charCodeAt(0) - 65, A + c.charCodeAt(1) - 65);
};

Plugins.banderas.init = function () {
    if (typeof WsjtMessagePanel === 'undefined') { console.warn('banderas: no hay WsjtMessagePanel'); return false; }
    var P = WsjtMessagePanel.prototype;
    if (P._bh_banderas) return true;
    P._bh_banderas = true;

    // FT2 (decodificador de BricoHams): que el panel acepte también esos mensajes
    var supports = P.supportsMessage;
    P.supportsMessage = function (m) {
        if (m && m.mode === 'FT2') return true;
        return supports.apply(this, arguments);
    };

    var push = P.pushMessage;
    P.pushMessage = function (msg) {
        var esFt2 = msg && msg.mode === 'FT2';
        if (esFt2 && this.qsoModes && this.qsoModes.indexOf('FT2') < 0) this.qsoModes.push('FT2');
        var r = push.apply(this, arguments);
        try {
            var cc = msg.ccode;
            if (!cc && msg.callsign && typeof Lookup !== 'undefined' && Lookup.call2ccode) cc = Lookup.call2ccode(msg.callsign);
            if (cc) {
                var $td = $(this.el).find('tbody tr:last td.message');
                if ($td.length && !$td.data('bh')) {
                    $td.data('bh', 1).prepend($('<span class="bh-flag"></span>')
                        .attr('title', msg.country || cc).text(Plugins.banderas.bandera(cc) + ' '));
                }
            }
        } catch (e) { console.debug('banderas', e); }
        return r;
    };
    return true;
};
