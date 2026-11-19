// Regression checks for the independent receiver skins (pure helpers + theme lifecycle).
// The DOM rendering itself is verified in a real browser on the live SDR.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const DIR = path.join(__dirname, '../files/htdocs/plugins/receiver');
const src = n => fs.readFileSync(path.join(DIR, n, n + '.js'), 'utf8');

function entorno() {
    const opciones = [], observadores = [], timers = new Set();
    const clases = new Set();
    const nodo = tag => ({ tagName: tag, children: [], style: {}, dataset: {}, attrs: {},
        appendChild(c) { this.children.push(c); c.parentNode = this; return c; },
        insertBefore(c) { return this.appendChild(c); },
        removeChild(c) { this.children = this.children.filter(x => x !== c); c.parentNode = null; },
        setAttribute(k, v) { this.attrs[k] = v; }, addEventListener() {}, removeEventListener() {} });
    const listbox = nodo('select');
    listbox.options = opciones;
    listbox.appendChild = function (o) { opciones.push(o); return o; };
    const receptor = nodo('div');
    const body = nodo('body');
    body.classList = { contains: c => clases.has(c), add: c => clases.add(c), remove: c => clases.delete(c) };
    const ids = { 'openwebrx-themes-listbox': listbox, 'openwebrx-panel-receiver': receptor };
    const ctx = {
        Plugins: {},
        window: {},
        document: {
            documentElement: { lang: 'es' },
            head: nodo('head'), body,
            getElementById: id => ids[id] || null,
            createElement: nodo,
            querySelector: () => null
        },
        MutationObserver: class { constructor(cb) { this.cb = cb; observadores.push(this); } observe() {} disconnect() {} },
        setInterval: () => { const t = {}; timers.add(t); return t; },
        clearInterval: t => timers.delete(t),
        console
    };
    ctx.window.document = ctx.document;
    const disparar = () => observadores.forEach(o => o.cb([]));
    return { ctx, opciones, clases, timers, receptor, disparar };
}

function cargar(nombre, e) {
    vm.runInNewContext(src(nombre), e.ctx);
    const P = e.ctx.Plugins[nombre];
    P._render = () => {};      // rendering needs a real DOM; checked in the browser
    P._tick = () => {};
    return P;
}

// ---- Brico-FX: theme registration ----
{
    const e = entorno();
    const P = cargar('bh_skin_bricofx', e);
    P.init();
    P.init();
    assert.deepEqual(e.opciones.map(o => o.value), ['bh-bricofx'], 'option registered exactly once');
    assert.equal(e.opciones[0].textContent, 'Brico-FX');
}

// ---- Brico-FX: lifecycle ----
{
    const e = entorno();
    const P = cargar('bh_skin_bricofx', e);
    P.init();
    e.clases.add('theme-bh-bricofx');
    e.disparar(); e.disparar();
    assert.equal(e.receptor.children.length, 1, 'panel built once');
    assert.equal(e.timers.size, 1, 'one refresh timer');
    e.clases.delete('theme-bh-bricofx');
    e.disparar();
    assert.equal(e.receptor.children.length, 0, 'panel removed');
    assert.equal(P._timer, null);
    assert.equal(e.timers.size, 0, 'timer stopped');
}

// ---- Brico-FX: saved theme already active at init ----
{
    const e = entorno();
    e.clases.add('theme-bh-bricofx');
    const P = cargar('bh_skin_bricofx', e);
    P.init();
    assert.equal(e.receptor.children.length, 1, 'built when the saved theme is already active');
}

// ---- Brico-FX: pure helpers ----
{
    const e = entorno();
    const L = cargar('bh_skin_bricofx', e)._logic;
    const nivel = dbm => Math.pow(10, dbm / 10);   // offset 0 → dBm = 10·log10(level)
    assert.deepEqual({ ...L.sUnits(0, 7e6, {}) }, { s: 0, over: 0, dbm: null });
    assert.deepEqual({ ...L.sUnits(NaN, 7e6, {}) }, { s: 0, over: 0, dbm: null });
    assert.deepEqual({ ...L.sUnits(undefined, 7e6, {}) }, { s: 0, over: 0, dbm: null });
    let r = L.sUnits(nivel(-73), 7e6, { offset_hf: 0 });
    assert.equal(r.s, 9); assert.equal(r.over, 0);
    r = L.sUnits(nivel(-61), 7e6, { offset_hf: 0 });
    assert.equal(r.s, 9); assert.equal(r.over, 12);
    assert.equal(L.sUnits(nivel(-79), 7e6, { offset_hf: 0 }).s, 8);
    assert.equal(L.sUnits(nivel(-93), 145e6, { offset_vhf: 0, iaru_vhf: true }).s, 9);
    assert.equal(L.sUnits(nivel(-200), 7e6, {}).s, 0, 'never below S0');
    assert.equal(L.isDigital('FT8'), true);
    assert.equal(L.isDigital('nfm'), false);
    assert.equal(L.isDigital(''), false);
    assert.equal(L.isDigital(undefined), false);
    assert.equal(L.t('volume'), 'Volumen');
}

// ---- Brico-FX: knob helpers ----
{
    const L = cargar('bh_skin_bricofx', entorno())._logic;
    assert.equal(L.knobSteps(44), 2);
    assert.equal(L.knobSteps(-16), -1);
    assert.equal(L.knobSteps(14), 0);
    assert.equal(L.knobSteps(30, 10), 3);
    assert.equal(L.clamp(200, 0, 150), 150);
    assert.equal(L.clamp(-5, 0, 150), 0);
    assert.equal(L.clamp(70, 0, 150), 70);
    assert.equal(L.fmtFreq(145525000), '145.525.000');
    assert.equal(L.fmtFreq(7074000), '7.074.000');
    assert.equal(L.fmtFreq(0), '---.---.---');
    assert.equal(L.meterPct({ s: 0, over: 0 }), 0);
    assert.equal(L.meterPct({ s: 9, over: 0 }), 60);
    assert.equal(L.meterPct({ s: 9, over: 60 }), 100);
    assert.equal(L.meterPct({ s: 9, over: 90 }), 100);
}

// ---- Brico-FX: screen views ----
{
    const L = cargar('bh_skin_bricofx', entorno())._logic;
    assert.deepEqual([...L.VIEWS], ['main', 'scope', 'digital']);
    assert.equal(L.nextView('main'), 'scope');
    assert.equal(L.nextView('scope'), 'digital');
    assert.equal(L.nextView('digital'), 'main');
    assert.equal(L.nextView('bogus'), 'main');
    assert.equal(L.viewFor('ft8', null), 'digital', 'digital mode opens the digital view');
    assert.equal(L.viewFor('usb', 'scope'), 'scope');
    assert.equal(L.viewFor('ft8', 'main'), 'main', 'a view picked after the mode change wins');
    assert.equal(L.viewFor('usb', null), 'main');
    assert.equal(L.scopeFreq(50, 100, { start: 7000000, end: 7200000 }), 7100000);
    assert.equal(L.scopeFreq(0, 0, { start: 1, end: 2 }), null, 'zero-width canvas gives no frequency');
    assert.deepEqual([...L.lastLines(['a', 'b', 'c'], 2)], ['c', 'b'], 'newest first');
    assert.deepEqual([...L.lastLines([], 8)], []);
    assert.deepEqual([...L.lastLines(['EA5KAO x', 'EB3Y y'], 8, 'ea5')], ['EA5KAO x'], 'case-insensitive filter');
}

// ---- Military: registration, lifecycle, needle ----
{
    const e = entorno();
    const P = cargar('bh_skin_militar', e);
    P.init(); P.init();
    assert.deepEqual(e.opciones.map(o => o.value), ['bh-militar']);
    e.clases.add('theme-bh-militar');
    e.disparar(); e.disparar();
    assert.equal(e.receptor.children.length, 1);
    assert.equal(e.timers.size, 1);
    e.clases.delete('theme-bh-militar');
    e.disparar();
    assert.equal(e.receptor.children.length, 0);
    assert.equal(P._timer, null);
    const L = P._logic;
    assert.equal(L.needleAngle(0, 0), -50);
    assert.equal(L.needleAngle(9, 0), 20);
    assert.equal(L.needleAngle(9, 60), 50);
    assert.equal(L.needleAngle(9, 200), 50);
    assert.equal(L.needleAngle(-3, 0), -50);
    assert.deepEqual({ ...L.sUnits(0, 7e6, {}) }, { s: 0, over: 0, dbm: null });
    assert.equal(L.knobSteps(44), 2);
    assert.equal(L.t('volume'), 'Volumen');
}

// ---- both skins installed: only the active one builds ----
{
    const e = entorno();
    const fx = cargar('bh_skin_bricofx', e), mil = cargar('bh_skin_militar', e);
    fx.init(); mil.init();
    assert.deepEqual(e.opciones.map(o => o.value), ['bh-bricofx', 'bh-militar']);
    e.clases.add('theme-bh-militar');
    e.disparar();
    assert.equal(e.receptor.children.length, 1);
    assert.equal(e.receptor.children[0].id, 'bh-militar-panel');
    assert.equal(fx._panel, null);
}

console.log('Receiver skins regression: PASS');
