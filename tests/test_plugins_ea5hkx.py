#!/usr/bin/env python3
"""v5.1 · Plugins de EA5HKX (gitlab.com/openwebrx-plugins): callsign_gate y tone_detector.

No publican licencia, así que el kit NO lleva su código: install.sh los descarga en un commit
fijo y solo los instala si coincide el sha256. El plugin local «ea5hkx_puente» adapta la ventana
de callsign_gate a la estación (indicativo, Telegram, privacidad, crédito) y filtra su anuncio
«Chat iniciado por …»; «identificacion» acepta su indicativo como identidad del chat.
Se prueba con un arnés de Node (DOM mínimo) si hay node."""
import os
import re
import shutil
import subprocess
import tempfile

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
REC = os.path.join(RAIZ, 'files', 'htdocs', 'plugins', 'receiver')
PUENTE = os.path.join(REC, 'ea5hkx_puente', 'ea5hkx_puente.js')
IDENT = os.path.join(REC, 'identificacion', 'identificacion.js')
PINES = {
    'callsign_gate': ('dcd55b51e51a2a3b2e7fd2d20dd7821d686fcb0b',
                      'aedb2bc8e43d5da36f379f1924f00a2910e96352afeeeef9ad37dcc112e2add8'),
    'tone_detector': ('9d048ccb5532018349369c3a1a0cc8e9cd11ac10',
                      'e2acfec0b368a8c52c498f179f9376da2cf3782ed3f581b0af4ba0cfc7200c25'),
}


def leer(r):
    with open(r, encoding='utf-8') as f:
        return f.read()


init = leer(os.path.join(REC, 'init.js'))
instalador = leer(os.path.join(RAIZ, 'install.sh'))
configuracion = leer(os.path.join(RAIZ, 'bricohams.env.example'))
pruebas = leer(os.path.join(RAIZ, 'tests', 'run_tests.sh'))

# --- Sin código de terceros sin licencia dentro del kit ------------------------------
for nombre in PINES:
    assert not os.path.exists(os.path.join(REC, nombre)), nombre + ' no debe ir dentro del kit (sin licencia)'

# --- install.sh: commit fijo + sha256 ----------------------------------------------
for nombre, (commit, suma) in PINES.items():
    assert f'"{nombre} {commit} {suma}"' in instalador, nombre
assert 'https://gitlab.com/openwebrx-plugins/$nombre/-/raw/$commit/$nombre.js' in instalador
assert 'sha256sum -c --status' in instalador
assert instalador.index('plugin_ea5hkx "$p"') < instalador.index('-e "s#__CALLSIGN_GATE__#${callsign_gate}#"')
for marca in ('__CALLSIGN_GATE__', '__TONE_DETECTOR__', '__CALLSIGN_ANUNCIO__'):
    assert f'-e "s#{marca}#' in instalador and f"'{marca}' === 'yes'" in init, marca
assert 'si "${CALLSIGN_GATE_ANUNCIO:-no}" && callsign_anuncio=yes' in instalador
for var in ('PLUGIN_CALLSIGN_GATE="yes"', 'PLUGIN_TONE_DETECTOR="yes"', 'CALLSIGN_GATE_ANUNCIO="no"'):
    assert var in configuracion, var

# --- init.js: orden de carga ---------------------------------------------------------
carga = re.search(r"for \(const name of \[([^\]]+)\]\)", init).group(1)
orden = re.findall(r"'(\w+)'", carga)
assert orden.index('identificacion') < orden.index('ea5hkx_puente') < orden.index('callsign_gate') < orden.index('audio_cadena')
assert orden.index('dsp_audio') < orden.index('tone_detector')
assert 'if (externoActivo[name] === false) continue;' in init
assert 'window.ea5hkx_config' in init

# --- run_tests.sh ---------------------------------------------------------------------
assert re.search(r'receiver/\{[^}]*\bea5hkx_puente\b[^}]*\}/\*\.js', pruebas)
assert 'python3 tests/test_plugins_ea5hkx.py' in pruebas

ARNES = r'''
const fs = require('fs');
const puente = fs.readFileSync(process.argv[2], 'utf8');
const ident = fs.readFileSync(process.argv[3], 'utf8');
const fallos = [];
function comprobar(c, m) { if (!c) fallos.push('FALLO: ' + m); }

class Nodo {
    constructor(tag, texto) {
        this.tagName = tag ? tag.toUpperCase() : null; this.nodeType = tag ? 1 : 3;
        this.hijos = []; this.attrs = {}; this.style = {}; this._texto = texto || ''; this.parentNode = null;
    }
    appendChild(n) { if (n.parentNode) n.parentNode.removeChild(n); n.parentNode = this; this.hijos.push(n); return n; }
    removeChild(n) { this.hijos = this.hijos.filter(h => h !== n); n.parentNode = null; return n; }
    get firstChild() { return this.hijos[0] || null; }
    get firstElementChild() { return this.hijos.find(h => h.nodeType === 1) || null; }
    get textContent() { return this.nodeType === 3 ? this._texto : this.hijos.map(h => h.textContent).join(''); }
    set textContent(v) { if (this.nodeType === 3) { this._texto = v; return; } this.hijos = []; this.appendChild(new Nodo(null, v)); }
    get href() { return this.attrs.href; }
    set href(v) { this.attrs.href = v; }
    setAttribute(k, v) { this.attrs[k] = String(v); }
    getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; }
    todos() { return this.hijos.filter(h => h.nodeType === 1).flatMap(h => [h, ...h.todos()]); }
    querySelectorAll(sel) { if (sel === 'h2') return this.todos().filter(n => n.tagName === 'H2'); throw new Error(sel); }
    querySelector(sel) {
        if (sel === 'a[href*="t.me/"]') return this.todos().find(n => n.tagName === 'A' && (n.attrs.href || '').includes('t.me/')) || null;
        throw new Error(sel);
    }
}
function el(tag, hijos, attrs) { const n = new Nodo(tag); (hijos || []).forEach(h => n.appendChild(typeof h === 'string' ? new Nodo(null, h) : h)); Object.assign(n.attrs, attrs || {}); return n; }
function ventanaGate() {
    // Estructura de la ventana de callsign_gate (commit fijado)
    return el('div', [el('div', [
        el('div', [el('h2', ['📡 ¡Bienvenido al SDR de EA5HKX!'])]),
        el('div', [el('h2', ['📡 Welcome to EA5HKX SDR!'])]),
        el('input'), el('button', ['Acceder / Enter']),
        el('p', ['💬 … Telegram ', el('a', ['@ea5hkxSDR'], { href: 'https://t.me/ea5hkxSDR' }), ' — síguelo …'])
    ])], { id: 'owrx-callsign-gate' });
}
function almacen() {
    const d = {};
    return { getItem: k => (k in d ? d[k] : null), setItem: (k, v) => { d[k] = String(v); }, removeItem: k => { delete d[k]; } };
}

function cargarPuente(cfg, gate, chat, mensaje) {
    const Plugins = { ea5hkx_puente: {} };
    const document = {
        body: null,
        createElement: t => new Nodo(t), createTextNode: t => new Nodo(null, t),
        getElementById: id => (id === 'owrx-callsign-gate' ? gate : id === 'openwebrx-chat-message' ? mensaje : null)
    };
    const f = new Function('Plugins', 'window', 'document', 'navigator', 'Chat', 'MutationObserver',
        puente + '\nreturn Plugins.ea5hkx_puente.init();');
    const ok = f(Plugins, { ea5hkx_config: cfg }, document, { language: 'es-ES' }, chat, undefined);
    return { ok, api: Plugins.ea5hkx_puente };
}

// 1 · la ventana pasa a ser de la estación, con su Telegram, privacidad y crédito
let gate = ventanaGate();
let chat = { enviados: [], send() { this.enviados.push(mensaje.value); mensaje.value = ''; } };
let mensaje = { value: '' };
let r = cargarPuente({ callsign_gate: true, anuncio: false, titulo: 'EA1ZZZ', telegram: 'https://t.me/bricohams',
                       privacidad: '/bricohams/privacidad.html' }, gate, chat, mensaje);
comprobar(r.ok === true, 'init devuelve true');
const texto = gate.textContent;
comprobar(!/EA5HKX SDR|SDR de EA5HKX/.test(texto) && /SDR de EA1ZZZ/.test(texto) && /EA1ZZZ SDR/.test(texto), 'títulos: ' + texto);
const enlaces = gate.todos().filter(n => n.tagName === 'A');
comprobar(enlaces.some(a => a.href === 'https://t.me/bricohams' && a.textContent === '@bricohams'), 'Telegram propio');
comprobar(!enlaces.some(a => /ea5hkxSDR/.test(a.href)), 'sin el Telegram de EA5HKX');
comprobar(enlaces.some(a => a.href === '/bricohams/privacidad.html'), 'aviso de privacidad');
comprobar(enlaces.some(a => a.href === 'https://gitlab.com/openwebrx-plugins/callsign_gate' && /EA5HKX/.test(a.textContent)), 'crédito a EA5HKX');
comprobar(r.api.adaptar(gate) === false, 'adaptar es idempotente');

// 2 · el anuncio automático no sale; los mensajes normales sí
mensaje.value = 'Chat iniciado por EA5ABC'; chat.send();
comprobar(chat.enviados.length === 0 && mensaje.value === '', 'anuncio filtrado');
mensaje.value = 'hola'; chat.send();
comprobar(chat.enviados.length === 1 && chat.enviados[0] === 'hola', 'mensaje normal enviado');

// 3 · con anuncio=yes no se toca Chat; sin Telegram desaparece el párrafo; título sin sustituir → BricoHams
gate = ventanaGate();
chat = { send() {} }; const original = chat.send;
r = cargarPuente({ callsign_gate: true, anuncio: true, titulo: '__OPERADOR__', telegram: '' }, gate, chat, mensaje);
comprobar(chat.send === original, 'anuncio=yes no envuelve Chat.send');
comprobar(/SDR de BricoHams/.test(gate.textContent), 'título por defecto BricoHams');
comprobar(!gate.todos().some(n => n.tagName === 'A' && /t\.me/.test(n.href || '')), 'sin Telegram no queda enlace');

// 4 · callsign_gate desactivado: el puente no hace nada
gate = ventanaGate(); chat = { send() {} }; const orig2 = chat.send;
r = cargarPuente({ callsign_gate: false }, gate, chat, mensaje);
comprobar(chat.send === orig2 && gate.getAttribute('data-bh-puente') === null, 'desactivado no toca nada');

// 5 · identificacion acepta el indicativo de callsign_gate y lo mantiene sincronizado
function cargarIdent(previo) {
    const ls = almacen(), nombre = { value: '', addEventListener() {} }, msg = { value: '', addEventListener() {} };
    ls.setItem('bh_identificacion_declined', 'yes');
    previo(ls);
    const Plugins = { identificacion: {} };
    const document = { getElementById: id => ({ 'openwebrx-chat-name': nombre, 'openwebrx-chat-message': msg })[id] || null };
    const f = new Function('Plugins', 'window', 'localStorage', 'sessionStorage', 'navigator', 'document', 'fetch', 'Chat',
        ident + '\nPlugins.identificacion.init(); return Plugins.identificacion.chat;');
    const api = f(Plugins, { identificacion_config: { enabled: false, chat_obligatorio: false }, ea5hkx_config: { callsign_gate: true } }, ls, almacen(),
        { language: 'es-ES' }, document, async () => ({ ok: false }), undefined);
    return { api, ls, msg };
}
let c = cargarIdent(ls => { ls.setItem('openwebrx_callsign', 'EA5ABC'); ls.setItem('openwebrx_callsign_ts', String(Date.now())); });
comprobar(c.api.identidad() === 'EA5ABC', 'identidad desde callsign_gate');
c = cargarIdent(ls => { ls.setItem('openwebrx_callsign', 'EA5ABC'); ls.setItem('openwebrx_callsign_ts', String(Date.now() - 15 * 864e5)); });
comprobar(c.api.identidad() === '', 'callsign_gate caducado (14 días) no vale');
c = cargarIdent(ls => { ls.setItem('openwebrx_callsign', '123'); ls.setItem('openwebrx_callsign_ts', String(Date.now())); });
comprobar(c.api.identidad() === '123', 'vale lo que acepta callsign_gate aunque no sea indicativo ITU');
c = cargarIdent(ls => {
    ls.setItem('bh_chat_identidad', JSON.stringify({ nombre: 'EA5OLD', ts: Date.now() - 864e5 }));
    ls.setItem('openwebrx_callsign', 'EA5NEW'); ls.setItem('openwebrx_callsign_ts', String(Date.now()));
});
comprobar(c.api.identidad() === 'EA5NEW', 'gana la identidad más reciente');
c.api.guardar('ea5cmb');
comprobar(c.ls.getItem('openwebrx_callsign') === 'EA5CMB' && c.api.identidad() === 'EA5CMB', 'cambiar identidad actualiza callsign_gate');
c = cargarIdent(() => {});
c.api.guardar('EA5XYZ');
comprobar(c.ls.getItem('openwebrx_callsign') === null, 'sin callsign_gate en uso no se crea su clave');

if (fallos.length) { console.error(fallos.join('\n')); process.exit(1); }
console.log('arnés ea5hkx OK');
'''

if shutil.which('node'):
    subprocess.run(['node', '--check', PUENTE], check=True)
    d = tempfile.mkdtemp()
    try:
        arnes = os.path.join(d, 'arnes.js')
        with open(arnes, 'w', encoding='utf-8') as f:
            f.write(ARNES)
        r = subprocess.run(['node', arnes, PUENTE, IDENT], capture_output=True, text=True, encoding='utf-8')
        assert r.returncode == 0, 'plugins ea5hkx: ' + r.stdout + r.stderr
    finally:
        shutil.rmtree(d)
print('OK test_plugins_ea5hkx')
