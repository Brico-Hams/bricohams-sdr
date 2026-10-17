const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const plugin = fs.readFileSync(path.join(__dirname, "..", "files", "meshweb", "favoritos.js"), "utf8");

async function probar() {
    const elementos = [];
    const devices = new Map();
    const conexiones = [];
    const selecciones = [];
    let id = 1;
    let radio = false;
    let errores = 0;
    let desconexiones = 0;
    const store = {
        devices,
        addDevice(n) {
            const d = { addConnection(c) { d.connection = c; } };
            devices.set(n, d);
            return d;
        },
    };
    const document = {
        createElement(tag) {
            const e = {
                tag, children: [], style: {}, dataset: {},
                setAttribute(k, v) { this[k] = v; },
                append(...hijos) { this.children.push(...hijos); },
                addEventListener(_, fn) { this.click = fn; },
                getBoundingClientRect() { return { height: 90 }; },
            };
            elementos.push(e);
            return e;
        },
        body: { prepend(e) { this.panel = e; } },
        documentElement: { style: { setProperty() {} } },
    };
    const context = {
        document, location: { host: "sdr.ejemplo.es:8443" },
        Map, Error, AbortSignal, Promise,
        ResizeObserver: class { observe() {} },
        console: { error() { errores++; } },
        ba: { getState: () => store },
        si: { getState: () => ({ addNodeDB: () => ({}) }) },
        ai: { getState: () => ({ addMessageStore: () => ({}) }) },
        lo: { getState: () => ({ setSelectedDevice(n) { selecciones.push(n); } }) },
        wN: { async create(host, tls) { conexiones.push({ host, tls }); return {}; } },
        GS: class {
            constructor() { this.events = { onDeviceStatus: { subscribe: fn => { this.estado = fn; } } }; }
            async configure() { this.isConfigured = true; this.estado(2); }
            async disconnect() { desconexiones++; this.isConfigured = false; this.estado(0); }
        },
        ct: { DeviceConfigured: 2, DeviceDisconnected: 0 },
        NN() {}, Lg: () => id++,
        fetch: async () => ({ ok: true, headers: { get: () => "application/json" }, json: async () => ({ radio }) }),
    };
    vm.runInNewContext(plugin, context);
    const botones = elementos.filter(e => e.tag === "button");
    assert.deepEqual(botones.map(b => b.dataset.bricohamsRadio), ["868", "433"]);
    await botones[0].click();
    assert.equal(conexiones[0].host, "sdr.ejemplo.es:8443/bricohams/nodos/868");
    assert.equal(conexiones[0].tls, true);
    await botones[0].click();
    assert.equal(conexiones.length, 1, "seleccionar un favorito conectado no crea duplicados");
    await botones[1].click();
    assert.equal(conexiones.length, 1, "sin USB 433 no se finge conexion");
    assert.equal(errores, 1);
    radio = true;
    await botones[1].click();
    assert.equal(conexiones[1].host, "sdr.ejemplo.es:8443/bricohams/nodos/433");
    assert.equal(devices.size, 2);
    assert.equal(selecciones.at(-1), 2);
    assert.equal(botones[1].disabled, false);
    devices.get(1).connection.isConfigured = false;
    await botones[0].click();
    assert.equal(desconexiones, 1, "cerrar el transporte anterior antes de reconectar");
    assert.equal(devices.size, 2, "reconectar no acumula dispositivos");
    assert(!plugin.includes("localStorage"), "no almacenar configuracion de canales en el navegador");
    console.log("OK favoritos: dos radios, mismo origen, seleccion sin duplicados y error USB explicito");
}
probar().catch(e => { console.error(e); process.exitCode = 1; });
