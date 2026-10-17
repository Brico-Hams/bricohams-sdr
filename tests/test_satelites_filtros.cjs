const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const nodos = new Map();
class Nodo {
    constructor() { this.contenido = ''; this.error = ''; }
    appendTo() { return this; }
    text(valor) { this.contenido = String(valor).replaceAll('&', '&amp;').replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;').replaceAll('"', '&quot;'); return this; }
    html(valor) { if (valor === undefined) return this.contenido; this.contenido = valor; return this; }
    hide() { return this; }
    toggle() { return this; }
    toggleClass() { return this; }
    css() { return this; }
    on(evento, selector, callback) { this.enviar = callback; return this; }
    find() { return { text: valor => { this.error = valor; } }; }
}
const $ = selector => {
    if (typeof selector === 'object') return selector;
    if (selector.startsWith('<')) {
        const nodo = new Nodo();
        if (selector.includes('id="bh-sat-lista"')) nodos.set('lista', nodo);
        return nodo;
    }
    throw Error('Selector inesperado: ' + selector);
};
const ahora = Date.now() / 1000;
const pases = [
    { nombre: 'FO-29', hz: 435850000 }, { nombre: 'Replicator-2', hz: 400500000 },
    { nombre: 'ISS', hz: 145800000 }, { nombre: 'SAKHACUBE-CHOLBON', hz: 437350000 }
].map(p => ({ ...p, aos: ahora + 3600, los: ahora + 4200, max_el: 50, duracion_s: 600, modo: 'nfm' }));
$.getJSON = () => ({ done: callback => callback({ pases }) });
const Plugins = { satelites: {} };
const contexto = { $, Plugins, window: {}, setInterval() {}, setTimeout() {}, Date, console };
vm.runInNewContext(fs.readFileSync(path.join(__dirname, '..', 'files', 'htdocs', 'plugins',
    'receiver', 'satelites', 'satelites.js'), 'utf8'), contexto);
assert.equal(Plugins.satelites.init(), true);
Plugins.satelites.lista();
const lista = nodos.get('lista');
function filtrar(banda, desde = '', hasta = '') {
    const formulario = { find(selector) { return { val: () => ({ '[name=banda]': banda,
        '[name=desde]': desde, '[name=hasta]': hasta })[selector] }; } };
    lista.enviar.call(formulario, { preventDefault() {} });
    return lista.contenido;
}
assert(lista.contenido.includes('FO-29') && lista.contenido.includes('Replicator-2'));
let html = filtrar('400');
assert(html.includes('Replicator-2') && !html.includes('FO-29') && !html.includes('SAKHACUBE'));
assert(html.includes('escuchar(1)'), 'conserva el indice original para sintonizar el satelite correcto');
html = filtrar('70cm');
assert(html.includes('FO-29') && html.includes('SAKHACUBE') && !html.includes('Replicator-2'));
html = filtrar('', '145,800', '145.800');
assert(html.includes('ISS') && !html.includes('FO-29'));
const previo = lista.contenido;
filtrar('', 'nan', '400');
assert(lista.error.includes('no v\u00e1lidas') && lista.contenido === previo);
filtrar('', '436', '400');
assert(lista.error.includes('no v\u00e1lidas') && lista.contenido === previo);
html = filtrar('', '436', '437,350');
assert(html.includes('SAKHACUBE') && !html.includes('FO-29'));
console.log('OK: filtros PASES por banda, rango, frecuencia exacta, validacion e indice de sintonizacion.');
