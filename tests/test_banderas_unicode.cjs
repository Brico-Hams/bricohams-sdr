const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const context = {
    Plugins: { banderas: {} },
    Lookup: { ccode2flag: () => '&#127466;&#127480;' }
};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,
    '../files/htdocs/plugins/receiver/banderas/banderas.js'), 'utf8'), context);
const flag = context.Plugins.banderas.bandera;
assert.equal(flag('ES'), '🇪🇸');
assert.equal(flag('es'), '🇪🇸');
for (const input of ['', '<x>', '12', null, 'ESP']) assert.equal(flag(input), '');
console.log('Flag Unicode regression: PASS');
