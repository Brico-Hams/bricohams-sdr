// Kit side of the receiver skins: one-time Brico-FX default and the style selector in bricohams.js.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const code = fs.readFileSync(path.join(__dirname, '../files/htdocs/plugins/receiver/bricohams/bricohams.js'), 'utf8');

function entorno({ opciones = ['default', 'rig', 'bh-bricofx', 'bh-militar'], almacen = {}, roto = false } = {}) {
    const temas = [];
    const nodo = tag => ({ tagName: tag, children: [], attrs: {}, handlers: {}, value: '',
        appendChild(c) { this.children.push(c); return c; },
        setAttribute(k, v) { this.attrs[k] = v; },
        addEventListener(ev, fn) { this.handlers[ev] = fn; } });
    const listbox = nodo('select');
    listbox.options = opciones.map(v => ({ value: v, textContent: v }));
    const ctx = {
        Plugins: { bricohams: {} },
        window: {},
        UI: { theme: 'rig', setTheme(t) { temas.push(t); this.theme = t; } },
        localStorage: {
            getItem(k) { if (roto) throw new Error('blocked'); return k in almacen ? almacen[k] : null; },
            setItem(k, v) { if (roto) throw new Error('blocked'); almacen[k] = String(v); }
        },
        document: { getElementById: id => (id === 'openwebrx-themes-listbox' ? listbox : null), createElement: nodo },
        MutationObserver: class { observe() {} },
        console
    };
    ctx.document.body = nodo('body');
    vm.runInNewContext(code, ctx);
    return { ctx, temas, almacen, nodo };
}

// one-time default
{
    const e = entorno();
    e.ctx.Plugins.bricohams.skinPorDefecto();
    assert.deepEqual(e.temas, ['rig'], 'everyone switched to the default style (Rig) once');
    assert.equal(e.almacen.bh_skin_default, 'rig');
    e.ctx.Plugins.bricohams.skinPorDefecto();
    assert.deepEqual(e.temas, ['rig'], 'never again after the flag');
}
{
    const e = entorno({ almacen: { bh_bricofx_default: '1' } });
    e.ctx.Plugins.bricohams.skinPorDefecto();
    assert.deepEqual(e.temas, ['rig'], 'visitors moved to Brico-FX earlier also get the new default once');
}
{
    const e = entorno({ almacen: { bh_skin_default: 'rig' } });
    e.ctx.Plugins.bricohams.skinPorDefecto();
    assert.deepEqual(e.temas, [], 'a visitor who already got this default keeps their choice');
}
{
    const e = entorno({ roto: true });
    assert.doesNotThrow(() => e.ctx.Plugins.bricohams.skinPorDefecto());
    assert.deepEqual(e.temas, ['rig'], 'blocked storage still shows the default style');
}
{
    const e = entorno({ opciones: ['default', 'bh-bricofx'] });
    e.ctx.Plugins.bricohams.skinPorDefecto();
    assert.deepEqual(e.temas, [], 'nothing to do when the default style is not installed');
}
{
    const e = entorno({ almacen: { bh_skin_default: 'rig' } });
    e.ctx.window.bricohams_config = { skin_defecto: 'bh-militar' };
    e.ctx.Plugins.bricohams.skinPorDefecto();
    assert.deepEqual(e.temas, ['bh-militar'], 'changing the configured default applies it once more');
}

// style selector
{
    const e = entorno();
    const caja = e.nodo('div');
    e.ctx.Plugins.bricohams.skinSelector(caja);
    const sel = caja.children.find(c => c.tagName === 'select');
    assert.ok(sel, 'select added to the section');
    assert.equal(sel.id, 'bricohams-skin');
    assert.equal(sel.attrs['aria-label'], 'Estilo del receptor');
    assert.deepEqual(sel.children.map(o => o.value), ['bh-bricofx', 'bh-militar', 'rig', 'default']);
    assert.equal(sel.value, 'rig', 'starts on the current theme');
    sel.value = 'bh-militar';
    sel.handlers.change();
    assert.deepEqual(e.temas, ['bh-militar']);
}

console.log('Receiver skins kit regression: PASS');
