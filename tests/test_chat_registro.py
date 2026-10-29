#!/usr/bin/env python3
"""v5.0 · Registro obligatorio para el chat (plugin «identificacion»).

Sin indicativo o nombre no se puede escribir en el chat de OpenWebRX+: el campo de
mensaje queda de solo lectura, Chat.send/Chat.sendMessage no envían y piden la
identidad; con identidad, el nombre del chat queda fijado a ella. La identidad se
guarda solo en el navegador (chat_dias) y el registro en el servidor sigue siendo
voluntario. Se prueba con un arnés de Node que imita el objeto Chat de OWRX 1.2.126."""
import os
import shutil
import subprocess
import tempfile

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
PLUGIN = os.path.join(RAIZ, 'files', 'htdocs', 'plugins', 'receiver', 'identificacion', 'identificacion.js')
INIT = os.path.join(RAIZ, 'files', 'htdocs', 'plugins', 'receiver', 'init.js')


def leer(r):
    with open(r, encoding='utf-8') as f:
        return f.read()


init = leer(INIT)
instalador = leer(os.path.join(RAIZ, 'install.sh'))
configuracion = leer(os.path.join(RAIZ, 'bricohams.env.example'))
assert "chat_obligatorio: '__CHAT_REGISTRO__' !== 'no'" in init
assert "'identificacion'" in init, 'init.js debe cargar el plugin identificacion'
assert 'si "${CHAT_REGISTRO_OBLIGATORIO:-yes}" && chat_registro=yes' in instalador
assert '-e "s#__CHAT_REGISTRO__#${chat_registro}#"' in instalador
assert 'CHAT_REGISTRO_OBLIGATORIO="yes"' in configuracion

ARNES = r'''
const fs = require('fs');
const codigo = fs.readFileSync(process.argv[2], 'utf8');
const fallos = [];
function comprobar(c, m) { if (!c) fallos.push('FALLO: ' + m); }

function almacen() {
    const d = {};
    return { getItem: k => (k in d ? d[k] : null), setItem: (k, v) => { d[k] = String(v); }, removeItem: k => { delete d[k]; } };
}
function campo(id) {
    const ev = {};
    return { id, value: '', readOnly: false, placeholder: '', title: '',
             addEventListener: (t, f) => { (ev[t] = ev[t] || []).push(f); }, disparar: t => (ev[t] || []).forEach(f => f()) };
}

async function escenario(cfg, conChat, previo) {
    const nombre = campo('openwebrx-chat-name'), mensaje = campo('openwebrx-chat-message');
    const enviados = [];
    const ctx = {
        localStorage: almacen(), sessionStorage: almacen(), navigator: { language: 'es-ES' },
        document: { getElementById: id => ({ 'openwebrx-chat-name': nombre, 'openwebrx-chat-message': mensaje })[id] || null },
        fetch: async () => ({ ok: true, json: async () => ({ ok: true }) }),
        Chat: undefined
    };
    ctx.localStorage.setItem('bh_identificacion_declined', 'yes');   // sin ventana de bienvenida
    if (previo) previo(ctx);
    const Chat = {
        nickname: '',
        setNickname(n) { if (this.nickname !== n) { this.nickname = n; nombre.value = n; } },
        sendMessage(text, nick = '') { enviados.push({ name: nick, text }); },
        send() {
            this.setNickname(nombre.value.trim());
            const msg = mensaje.value.trim();
            if (msg.length > 0) this.sendMessage(msg, this.nickname);
            mensaje.value = '';
        }
    };
    if (conChat) ctx.Chat = Chat;
    const Plugins = { identificacion: {} };
    const window = { identificacion_config: cfg };
    // Chat se resuelve en cada llamada para poder aparecer más tarde
    const tieneChat = () => ctx.Chat;
    const envoltorio = new Function('Plugins', 'window', 'localStorage', 'sessionStorage', 'navigator', 'document', 'fetch',
        'getChat', 'setTimeout', 'Object.defineProperty(globalThis, "Chat", { get: getChat, configurable: true });' +
        codigo + '\nreturn Plugins.identificacion.init();');
    envoltorio(Plugins, window, ctx.localStorage, ctx.sessionStorage, ctx.navigator, ctx.document, ctx.fetch,
               tieneChat, setTimeout);
    const abiertos = [];
    if (Plugins.identificacion.chat) Plugins.identificacion.chat.abrir = c => abiertos.push(c || false);
    await new Promise(r => setTimeout(r, 20));
    return { ctx, Chat, nombre, mensaje, enviados, abiertos, api: Plugins.identificacion.chat, ponerChat: () => { ctx.Chat = Chat; } };
}

(async () => {
    // 1 · sin identidad el chat está bloqueado
    let e = await escenario({ enabled: true }, true);
    comprobar(e.mensaje.readOnly === true, 'sin identidad el mensaje es de solo lectura');
    comprobar(e.mensaje.placeholder.indexOf('🔒') === 0, 'aviso 🔒 en el campo de mensaje');
    comprobar(e.nombre.readOnly === true, 'el nombre del chat no se edita a mano');
    e.mensaje.value = 'hola';
    e.Chat.send();
    comprobar(e.enviados.length === 0, 'Chat.send no envía sin identidad');
    comprobar(e.abiertos.length === 1, 'Chat.send pide la identidad');
    e.Chat.sendMessage('directo', 'X');
    comprobar(e.enviados.length === 0, 'Chat.sendMessage directo tampoco envía');
    e.mensaje.disparar('focus');
    comprobar(e.abiertos.length === 3, 'al entrar en el mensaje se pide la identidad');

    // 2 · identidad válida: se normaliza, desbloquea y se fuerza el nombre
    comprobar(e.api.guardar('<script>') === '', 'identificador inválido rechazado');
    comprobar(e.api.guardar('  ea5abc ') === 'EA5ABC', 'indicativo en mayúsculas');
    comprobar(e.nombre.value === 'EA5ABC' && e.Chat.nickname === 'EA5ABC', 'nombre del chat fijado');
    comprobar(e.mensaje.readOnly === false, 'mensaje desbloqueado');
    e.mensaje.value = 'hola';
    e.nombre.value = 'OTRO';
    e.Chat.send();
    comprobar(e.enviados.length === 1 && e.enviados[0].name === 'EA5ABC' && e.enviados[0].text === 'hola',
              'se envía con la identidad guardada: ' + JSON.stringify(e.enviados));
    e.Chat.sendMessage('directo', 'SUPLANTADO');
    comprobar(e.enviados[1].name === 'EA5ABC', 'no se puede suplantar el nombre');
    e.nombre.disparar('click');
    comprobar(e.abiertos[e.abiertos.length - 1] === true, 'clic en el nombre abre «cambiar identidad»');
    comprobar(e.api.guardar('José Pérez') === 'José Pérez', 'también vale un nombre');

    // 3 · caducidad de la identidad del chat (14 días por defecto)
    e = await escenario({ enabled: true }, true, ctx => ctx.localStorage.setItem('bh_chat_identidad',
        JSON.stringify({ nombre: 'EA5OLD', ts: Date.now() - 15 * 864e5 })));
    comprobar(e.api.identidad() === '' && e.mensaje.readOnly === true, 'identidad caducada vuelve a bloquear');
    e = await escenario({ enabled: true, chat_dias: 30 }, true, ctx => ctx.localStorage.setItem('bh_chat_identidad',
        JSON.stringify({ nombre: 'EA5OLD', ts: Date.now() - 15 * 864e5 })));
    comprobar(e.api.identidad() === 'EA5OLD', 'chat_dias configurable');

    // 4 · quien ya se registró voluntariamente puede usar el chat
    e = await escenario({ enabled: true }, true, ctx => ctx.localStorage.setItem('bh_identificacion_consent',
        JSON.stringify({ identificador: 'ea5reg', aceptado: Date.now() })));
    comprobar(e.api.identidad() === 'EA5REG' && e.mensaje.readOnly === false, 'registro voluntario identifica en el chat');

    // 5 · funciona aunque el registro de oyentes esté apagado
    e = await escenario({ enabled: false }, true);
    e.mensaje.value = 'x'; e.Chat.send();
    comprobar(e.enviados.length === 0 && e.abiertos.length === 1, 'bloqueo activo con VISITAS_ENABLE=no');

    // 6 · se puede desactivar
    e = await escenario({ enabled: true, chat_obligatorio: false }, true);
    e.mensaje.value = 'libre'; e.Chat.send();
    comprobar(e.enviados.length === 1 && e.mensaje.readOnly === false, 'chat_obligatorio=false no toca el chat');

    // 7 · Chat aparece más tarde (se reintenta cada 500 ms)
    e = await escenario({ enabled: true }, false);
    e.ponerChat();
    await new Promise(r => setTimeout(r, 650));
    e.mensaje.value = 'tarde'; e.Chat.send();
    comprobar(e.enviados.length === 0 && e.mensaje.readOnly === true, 'se instala cuando aparece Chat');

    if (fallos.length) { console.error(fallos.join('\n')); process.exit(1); }
    console.log('arnés chat OK');
})().catch(err => { console.error(err); process.exit(1); });
'''

if shutil.which('node'):
    subprocess.run(['node', '--check', PLUGIN], check=True)
    d = tempfile.mkdtemp()
    try:
        arnes = os.path.join(d, 'arnes.js')
        with open(arnes, 'w', encoding='utf-8') as f:
            f.write(ARNES)
        r = subprocess.run(['node', arnes, PLUGIN], capture_output=True, text=True, encoding='utf-8')
        assert r.returncode == 0, 'registro chat: ' + r.stdout + r.stderr
    finally:
        shutil.rmtree(d)
print('OK test_chat_registro')
