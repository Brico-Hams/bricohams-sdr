// =====================================================================
//  BricoHams · Plugins del RECEPTOR OpenWebRX+
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

// v5.1 · las páginas /bricohams/ (privacidad, políticas, portal) las sirve nginx en el 443, no
// OpenWebRX+: si se entra directo por un puerto propio (p. ej. :8073) los enlaces van a https://<host>/
// (http:// solo con SSL_MODO=no). Por el 443 quedan relativos.
const BH_WEB = location.port ? ('__SSL_MODO__' === 'no' ? 'http://' : 'https://') + location.hostname : '';

// Botones propios de la barra superior: DX (rig_skin) · SOL · 21,3° (METEO) · CAM
window.solar_config     = { lat: __LAT__, lon: __LON__ };                   // QTH para día/noche
window.meteo_config     = { url: 'static/plugins/receiver/meteo/meteo.json' };
window.camara_config    = { live: 'auto', refresh: __CAM_SNAPSHOT_SECONDS__, title: 'Cámara del mástil · __QTH__' };
window.bricohams_config = { telegram: 'https://t.me/bricohams', boton: true };
// v4
window.satelites_config = { url: 'static/plugins/receiver/satelites/pases.json', min_el: 15 };
window.visitas_config   = { url: 'static/plugins/receiver/visitas/visitas.json', privacidad: BH_WEB + '/bricohams/privacidad.html' };
window.dvficha_config   = { api: '/bricohams/api/indicativo', segundos: 20 };
window.identificacion_config = {
    enabled: '__VISITAS_ENABLE__' === 'yes',
    endpoint: '/bricohams/api/oyentes',
    health: '/bricohams/api/salud',
    privacidad: BH_WEB + '/bricohams/privacidad.html',
    chat_obligatorio: '__CHAT_REGISTRO__' !== 'no',   // CHAT_REGISTRO_OBLIGATORIO en bricohams.env
    chat_dias: 14
};
// v5.1 · plugins de EA5HKX (gitlab.com/openwebrx-plugins). Los descarga install.sh en un commit fijo
// y comprueba su sha256; si no se pudieron verificar quedan en 'no'. Manual 41.
window.ea5hkx_config = {
    callsign_gate: '__CALLSIGN_GATE__' === 'yes',      // PLUGIN_CALLSIGN_GATE: indicativo o nombre antes de entrar
    tone_detector: '__TONE_DETECTOR__' === 'yes',      // PLUGIN_TONE_DETECTOR: panel CTCSS en el navegador
    anuncio: '__CALLSIGN_ANUNCIO__' === 'yes',          // CALLSIGN_GATE_ANUNCIO: «Chat iniciado por …» en cada visita
    titulo: '__OPERADOR__',
    telegram: window.bricohams_config.telegram,
    privacidad: BH_WEB + '/bricohams/privacidad.html'
};
// v5 · aviso de cookies, idioma ES/EN y logo BricoHams
window.consentimiento_config = { politicas: BH_WEB + '/bricohams/politicas.html', privacidad: BH_WEB + '/bricohams/privacidad.html', dias: 180 };
window.idioma_config = { defecto: 'navegador' };   // 'es', 'en' o 'navegador'
window.marca_config  = { logo: 'static/plugins/receiver/marca/bricohams-logo.png', url: BH_WEB + '/bricohams/', titulo: 'BricoHams' };
// v4.2 · audio en el navegador del oyente (botones FILTRO y DSP). Por defecto apagados:
// cada oyente los enciende y sus ajustes se guardan en su navegador.
window.filtro_audio_config = { modo: 'voz', activo: false };
window.dsp_audio_config    = { preajuste: 'voz', activo: false };
// Oyentes en tiempo real del plugin «listeners» de 0xAF: necesita un proyecto Supabase propio
// (LISTENERS_SUPABASE_URL y LISTENERS_SUPABASE_KEY en bricohams.env). Vacío = no se carga.
const LISTENERS = { url: '__LISTENERS_URL__', key: '__LISTENERS_KEY__' };
const LISTENERS_COUNTRY = '__LISTENERS_COUNTRY__';

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

    function activarPerfilEnlace() {
        const url = new URL(location.href);
        const profileKey = url.searchParams.get('bh_profile');
        const select = document.getElementById('openwebrx-sdr-profiles-listbox');
        if (!profileKey || !select || !Array.from(select.options).some(option => option.value === profileKey)) return;
        if (select.value !== profileKey) {
            select.value = profileKey;
            if (typeof window.sdr_profile_changed === 'function') window.sdr_profile_changed();
            else $(select).trigger('change');
        }
        url.searchParams.delete('bh_profile');
        history.replaceState(null, '', url.pathname + url.search + url.hash);
        $(document).off('server:profiles:after.bh_listeners_profile', activarPerfilEnlace);
    }
    if (new URL(location.href).searchParams.has('bh_profile')) {
        $(document).on('server:profiles:after.bh_listeners_profile', activarPerfilEnlace);
        setTimeout(activarPerfilEnlace, 0);
    }

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
                if (localStorage.getItem('bh_rig_default')) return;
                if (typeof UI !== 'undefined' && UI.setTheme) UI.setTheme('rig');
                localStorage.setItem('bh_rig_default', '1');
            } catch (e) { /* sin almacenamiento: no pasa nada */ }
        }, 500);
    } catch (e) { console.warn('rig_skin', e); }

    // Plugins locales de BricoHams (htdocs/plugins/receiver/<nombre>/)
    // audio_cadena va antes que filtro_audio y dsp_audio (es su base común)
    // ea5hkx_puente va antes que callsign_gate (adapta su ventana y filtra su anuncio en el chat)
    const externoActivo = { callsign_gate: window.ea5hkx_config.callsign_gate, tone_detector: window.ea5hkx_config.tone_detector };
    for (const name of ['idioma', 'marca', 'consentimiento', 'solar', 'meteo', 'camara', 'bricohams', 'banderas', 'dvficha',
                        'satelites', 'visitas', 'identificacion', 'ea5hkx_puente', 'callsign_gate',
                        'audio_cadena', 'filtro_audio', 'dsp_audio', 'tone_detector']) {
        if (externoActivo[name] === false) continue;
        try { await Plugins.load(name); } catch (e) { console.warn(name, e); }
    }

    // «listeners» (0xAF): quién escucha qué frecuencia, solo si hay Supabase configurado
    if (LISTENERS.url && LISTENERS.url.indexOf('__') !== 0 && LISTENERS.key && LISTENERS.key.indexOf('__') !== 0) {
        try {
            await Plugins.load(rp_url + '/listeners/listeners.js');
            const listeners = Plugins.listeners;
            const capture = listeners._capture;
            listeners._capture = function () {
                const presence = capture.apply(this, arguments);
                if (presence && /^[A-Z]{2}$/.test(LISTENERS_COUNTRY)) presence.country = LISTENERS_COUNTRY;
                return presence;
            };
            const validPresence = listeners._validPresence;
            listeners._validPresence = function (presence) {
                const valid = validPresence.call(this, presence);
                if (valid) valid.country = this._shortText(presence.country, 40);
                return valid;
            };
            const groups = listeners._groups;
            listeners._groups = function () {
                const receivers = groups.call(this);
                this.state.presences.forEach(function (presence) {
                    if (receivers[presence.receiver_id] && presence.country && !receivers[presence.receiver_id].country) {
                        receivers[presence.receiver_id].country = presence.country;
                    }
                });
                return receivers;
            };
            const renderReceiver = listeners._renderReceiver;
            listeners._renderReceiver = function (receiver, local) {
                const section = renderReceiver.call(this, receiver, local);
                if (receiver.country) {
                    const flag = Plugins.banderas && Plugins.banderas.bandera
                        ? Plugins.banderas.bandera(receiver.country)
                        : '';
                    section.find('.owrx-listeners__receiver-heading').append(
                        $('<span class="owrx-listeners__country"></span>')
                            .attr('title', receiver.country)
                            .text([flag, receiver.country].filter(Boolean).join(' '))
                    );
                }
                if (!local && receiver.url) {
                    const profileKeys = Object.keys(receiver.profiles).sort(function (a, b) {
                        return receiver.profiles[a].name.localeCompare(receiver.profiles[b].name);
                    });
                    section.find('.owrx-listeners__profile').each(function (index) {
                        const profile = receiver.profiles[profileKeys[index]];
                        const profileUrl = new URL(receiver.url, location.href);
                        profileUrl.searchParams.set('bh_profile', profile.key || profile.name);
                        $(this).find('.owrx-listeners__tuning').attr({ role: 'link', tabindex: '0', title: 'Abrir perfil remoto' })
                            .on('click', function () { window.open(profileUrl.href, '_blank', 'noopener,noreferrer'); })
                            .on('keydown', function (event) {
                                if (event.key === 'Enter' || event.key === ' ') {
                                    event.preventDefault();
                                    window.open(profileUrl.href, '_blank', 'noopener,noreferrer');
                                }
                            });
                        });
                }
                return section;
            };
            await Plugins.listeners.setup({ supabaseUrl: LISTENERS.url, supabaseKey: LISTENERS.key, network: 'bricohams',
                                           receiverName: '__OPERADOR__ · __QTH__', receiverUrl: location.origin });
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
