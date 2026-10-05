// =====================================================================
//  EA5KAO · BricoHams · Plugins del RECEPTOR OpenWebRX+
//  Ruta: /usr/lib/python3/dist-packages/htdocs/plugins/receiver/init.js
//  Lo instala bricohams-install. Tras cambiarlo basta con recargar la web (Ctrl+F5).
// =====================================================================

// Plugins._enable_debug = true;   // descomenta para depurar en la consola del navegador

const rp_url  = 'https://0xaf.github.io/openwebrxplus-plugins/receiver';
const rig_url = 'https://aganet.github.io/openwebrxplus-rig-skin/receiver/rig_skin/rig_skin.js';

// ---------------------------------------------------------------------
//  Ajustes
// ---------------------------------------------------------------------
const RIG_POR_DEFECTO = true;                         // tema "Rig" la primera vez que alguien entra

// S-meter del Rig Skin (ajústalo comparando con una señal conocida)
window.rig_skin_config = {
    smeter: { offset_hf: 7, offset_vhf: -50, iaru_vhf: true }
};

// Botones propios de la barra superior: DX (rig_skin) · SOL · 21,3° (METEO) · CAM
window.solar_config     = { lat: __LAT__, lon: __LON__ };                   // QTH para día/noche
window.meteo_config     = { url: 'static/plugins/receiver/meteo/meteo.json' };
window.camara_config    = { live: 'auto', refresh: __CAM_SNAPSHOT_SECONDS__, title: 'Cámara del mástil · Mi QTH' };
window.bricohams_config = { telegram: 'https://t.me/bricohams', boton: true };
// v4
window.satelites_config = { url: 'static/plugins/receiver/satelites/pases.json', min_el: 15 };
window.visitas_config   = { url: 'static/plugins/receiver/visitas/visitas.json', privacidad: '/bricohams/privacidad.html' };
window.dvficha_config   = { api: '/bricohams/api/indicativo', segundos: 20 };
// v4.2 · audio en el navegador del oyente (botones FILTRO y DSP). Por defecto apagados:
// cada oyente los enciende y sus ajustes se guardan en su navegador.
window.filtro_audio_config = { modo: 'voz', activo: false };
window.dsp_audio_config    = { preajuste: 'voz', activo: false };
// Oyentes en tiempo real del plugin «listeners» de 0xAF: necesita un proyecto Supabase propio
// (LISTENERS_SUPABASE_URL y LISTENERS_SUPABASE_KEY en bricohams.env). Vacío = no se carga.
const LISTENERS = { url: '__LISTENERS_URL__', key: '__LISTENERS_KEY__' };

// Pasos del plugin tune_precise (Hz)
Plugins.tune_precise_steps = [25000, 12500, 6250, 1000, 100];

// Plugins que se cargan para todo el mundo (0xAF)
const PluginsToLoad = [
    'colorful_spectrum',     // espectro en color
    'compact_analog_modes',  // botones de modos compactos
    'screenshot',            // captura de la cascada
    'toggle_scannable',      // clic derecho en un marcador = entra/sale del scanner
    'search_bookmarks',      // buscador de marcadores
    'doppler',               // seguimiento Doppler de satélites (ISS, SO-50…)
];

// Plugins que cada visitante puede activar él mismo (botón del puzle)
const PluginsOpcionales = [
    'tune_precise', 'thumbtune', 'accessible_bookmark_search', 'screen_reader',
    'sort_profiles', 'freq_scanner', 'smeter',
];

// ---------------------------------------------------------------------
//  Carga (el orden importa)
// ---------------------------------------------------------------------
(async () => {
    await Plugins.load(rp_url + '/utils/utils.js');
    await new Promise(resolve => Plugins.utils.on_ready(resolve));   // esperar a que el receptor esté listo

    // Plugins integrados de OpenWebRX+ (no se cargan con Plugins.load)
    const builtin = (name) => { try { if (typeof window[name] !== 'undefined') window[name].init(); } catch (e) { console.warn(name, e); } };
    builtin('MapPlugin');   // mapa en ventana flotante dentro del receptor (1.2.124+)
    builtin('KeyPlugin');   // campo "magic key" en Ajustes (1.2.125+)
    // SunPlugin (solo la imagen de HamQSL) queda sustituido por el plugin local "solar"

    await Plugins.load(rp_url + '/notify/notify.js');

    for (const name of PluginsToLoad) {
        try { await Plugins.load(`${rp_url}/${name}/${name}.js`); } catch (e) { console.warn(name, e); }
    }

    // Rig Skin (aganet): tema Rig, DX cluster, pantallas PROP y SAT
    try {
        await Plugins.load(rig_url);
        if (RIG_POR_DEFECTO) setTimeout(function () {
            try {
                if (localStorage.getItem('ea5kao_rig_default')) return;
                if (typeof UI !== 'undefined' && UI.setTheme) UI.setTheme('rig');
                localStorage.setItem('ea5kao_rig_default', '1');
            } catch (e) { /* sin almacenamiento: no pasa nada */ }
        }, 500);
    } catch (e) { console.warn('rig_skin', e); }

    // Plugins locales de EA5KAO (htdocs/plugins/receiver/<nombre>/)
    // audio_cadena va antes que filtro_audio y dsp_audio (es su base común)
    for (const name of ['solar', 'meteo', 'camara', 'bricohams', 'banderas', 'dvficha', 'satelites', 'visitas',
                        'audio_cadena', 'filtro_audio', 'dsp_audio']) {
        try { await Plugins.load(name); } catch (e) { console.warn(name, e); }
    }

    // «listeners» (0xAF): quién escucha qué frecuencia, solo si hay Supabase configurado
    if (LISTENERS.url && LISTENERS.url.indexOf('__') !== 0 && LISTENERS.key && LISTENERS.key.indexOf('__') !== 0) {
        try {
            await Plugins.load(rp_url + '/listeners/listeners.js');
            await Plugins.listeners.setup({ supabaseUrl: LISTENERS.url, supabaseKey: LISTENERS.key, network: 'bricohams',
                                           receiverName: 'EA5KAO · Mi QTH', receiverUrl: location.origin });
        } catch (e) { console.warn('listeners', e); }
    }

    // Ventana de plugins para el visitante (debe ir la última)
    try {
        await Plugins.load(rp_url + '/plugin_loader/plugin_loader.js');
        await Plugins.plugin_loader.setup({
            allowed: PluginsOpcionales,
            allow_all: false,
            allow_experimental: false,
            allow_thirdparty: false,
        });
    } catch (e) { console.warn('plugin_loader', e); }
})();
