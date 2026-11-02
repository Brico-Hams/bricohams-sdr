const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const kit = path.resolve(__dirname, '..');
const read = name => fs.readFileSync(path.join(kit, name), 'utf8');
const plugin = read('files/htdocs/plugins/receiver/camara/camara.js');
for (const protocol of ['https:', 'http:']) {
    let live;
    const source = plugin.slice(plugin.indexOf('    var LIVE ='), plugin.indexOf('    var css ='));
    vm.runInNewContext(source + '\nresult(LIVE);', {
        cfg: {}, location: { protocol, hostname: 'sdr.example', port: '' },
        result: value => { live = value; }
    });
    assert.equal(live, '/camara/mastil/');
}
const install = read('install.sh');
for (const setting of ['rtspAddress: 127.0.0.1:8554', 'rtspTransports: [tcp]', 'hlsAddress: 127.0.0.1:8888', 'webrtc: no']) {
    assert.ok(install.includes(setting), setting);
}
assert.ok(read('files/htdocs/plugins/receiver/init.js').includes("BH_WEB + '/camara/mastil/'"));
assert.match(read('bricohams.env.example'), /^CAM_TUNING=""/m);
console.log('Camera HTTPS checks passed');

assert.ok(read('files/nginx/bricohams-sdr-rutas.conf').includes('proxy_redirect / /camara/;'));

const nginx = read('files/nginx/bricohams-sdr-rutas.conf');
assert.ok(nginx.includes('init[.]js|camara/camara[.]js'));
assert.ok(nginx.includes('proxy_hide_header Cache-Control;'));
assert.ok(nginx.includes('expires -1;'));
