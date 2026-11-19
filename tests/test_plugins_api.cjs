const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const DIR = path.join(__dirname, '../files/htdocs/plugins/receiver');
const src = n => fs.readFileSync(path.join(DIR, n, n + '.js'), 'utf8');

// 1) bricohams: se ejecuta contra una API nativa mínima falsa
const botones = [], secciones = [], aperturas = [], fijos = [], body = [];
const nodo = () => ({ children: [], style: {}, classList: { contains: () => false },
    appendChild(c) { this.children.push(c); return c; }, addEventListener() {},
    setAttribute(k, v) { this[k] = v; } });
const context = {
    Plugins: {
        bricohams: {},
        addButton(id, titulo, handler) { const b = nodo(); botones.push({ id, titulo, handler }); return b; },
        addSection(id, titulo) { secciones.push({ id, titulo }); return nodo(); },
        addWindow() { throw new Error('bricohams no abre ventanas'); }
    },
    window: {
        bricohams_config: { telegram: 'https://t.me/bricohams' },
        BricoHamsTheme: { get: () => 'system', set() {} },
        open: (...a) => aperturas.push(a)
    },
    document: {
        head: { appendChild() {} },
        body: { appendChild(e) { body.push(e); } },
        getElementById: () => null,
        createElement: nodo
    },
    $: () => ({ first: () => ({ length: 0 }) })
};
vm.runInNewContext(src('bricohams'), context);
context.Plugins.bricohams.init();
assert.deepEqual(botones.map(b => b.id), ['bricohams-tg', 'bricohams-gh']);
assert.deepEqual(secciones.map(s => s.id), ['bricohams']);
assert.equal(body.length, 0, 'con API nativa no queda nada suelto en body');
botones[0].handler();
botones[1].handler();
assert.deepEqual(aperturas.map(a => [a[0], a[1], a[2]]),
    [['https://t.me/bricohams', '_blank', 'noopener'], ['https://github.com/Brico-Hams/bricohams-sdr', '_blank', 'noopener']]);

// 2) resto de plugins migrados: usan addButton / addWindow con los ids esperados
const esperado = {
    solar: ["Plugins.addButton('solar'", "Plugins.addWindow(id", "crearVentana('solar'"],
    meteo: ["Plugins.addButton('meteo'", "Plugins.addWindow(id", "crearVentana('meteo'"],
    camara: ["Plugins.addButton('camara'", "Plugins.addWindow('camara'"],
    dvficha: ["Plugins.addWindow('dvficha'"],
    visitas: ["Plugins.addWindow('visitas'"]
};
for (const [n, frags] of Object.entries(esperado)) {
    const s = src(n);
    for (const frag of frags) assert.ok(s.includes(frag), n + ' debe contener ' + frag);
}
const cadena = src('audio_cadena');
assert.ok(cadena.includes('Plugins.addButton(') && cadena.includes('Plugins.addWindow(nid'), 'audio_cadena usa la API nativa');
assert.ok(src('filtro_audio').includes("C.ui.ventana('bh-filtro'") && src('filtro_audio').includes("C.ui.boton('bh-filtro-button'"));
assert.ok(src('dsp_audio').includes("C.ui.ventana('bh-dsp'") && src('dsp_audio').includes("C.ui.boton('bh-dsp-button'"));

// 3) ningún lanzador propio con position:fixed (el aviso de identificacion y la píldora de visitas quedan fuera)
for (const n of ['solar', 'meteo', 'camara', 'dvficha', 'bricohams', 'audio_cadena', 'filtro_audio', 'dsp_audio']) {
    assert.ok(!/position:\s*fixed/.test(src(n)), n + ' no debe usar position:fixed');
}
console.log('Native plugins API regression: PASS');
