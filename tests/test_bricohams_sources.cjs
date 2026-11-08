const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const elements = [];
const context = {
    Plugins: { bricohams: {} },
    window: { bricohams_config: { boton: false, fuentes: '' } },
    document: {
        head: { appendChild() {} },
        body: { appendChild(element) { elements.push(element); } },
        getElementById: id => elements.find(element => element.id === id),
        createElement: () => ({ children: [], appendChild(child) { this.children.push(child); } })
    },
    $: () => ({ first: () => ({ length: 0 }) })
};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,
    '../files/htdocs/plugins/receiver/bricohams/bricohams.js'), 'utf8'), context);
context.Plugins.bricohams.init();
const button = elements.find(element => element.id === 'bricohams-gh');
assert.equal(button.href, 'https://github.com/Brico-Hams/bricohams-sdr');
assert.equal(button.children[0].textContent, 'Hazlo tú mismo');
context.Plugins.bricohams.init();
assert.equal(elements.filter(element => element.id === 'bricohams-gh').length, 1);
console.log('Source button regression: PASS');
