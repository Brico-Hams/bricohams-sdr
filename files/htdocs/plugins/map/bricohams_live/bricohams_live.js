(function () {
    'use strict';
    const TTL = 2 * 60 * 60 * 1000;
    const MAX_STATIONS = 512;
    const MAX_POINTS = 1000;
    const tracks = new Map();
    const aircraft = new Map();
    const ships = new Map();
    let aprsLayer, aircraftLayer, status;
    let aisLayer = null, aisStatus = '';
    let takLayer;
    const takMarkers = new Map();

    function position(lat, lon) {
        return Number.isFinite(lat) && Number.isFinite(lon) &&
            lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180;
    }

    function prune(now) {
        tracks.forEach(function (t, id) {
            t.points = t.points.filter(p => now - p.time <= TTL);
            if (!t.points.length) {
                aprsLayer.removeLayer(t.line);
                aprsLayer.removeLayer(t.marker);
                tracks.delete(id);
            } else {
                t.line.setLatLngs(t.points.map(p => p.pos));
            }
        });
    }

    function updates(items) {
        const now = Date.now();
        prune(now);
        items.forEach(function (u) {
            const p = u.location;
            const ts = u.lastseen;
            if ((u.mode !== 'APRS' && u.mode !== 'AIS') || !p || p.type !== 'latlon' ||
                !position(p.lat, p.lon) || typeof u.callsign !== 'string' ||
                !Number.isFinite(ts) || ts > now + 5000 || now - ts > TTL) return;
            const id = u.mode + ':' + u.callsign;
            let t = tracks.get(id);
            if (!t) {
                if (tracks.size >= MAX_STATIONS) {
                    const oldest = tracks.keys().next().value;
                    const old = tracks.get(oldest);
                    aprsLayer.removeLayer(old.line);
                    aprsLayer.removeLayer(old.marker);
                    tracks.delete(oldest);
                }
                const markerLabel = document.createElement('span');
                markerLabel.textContent = u.callsign + ' (' + u.mode + ')';
                const lineLabel = document.createElement('span');
                lineLabel.textContent = markerLabel.textContent;
                const color = u.mode === 'AIS' ? '#1769aa' : '#e87524';
                const marker = u.mode === 'AIS'
                    ? L.marker([p.lat, p.lon], {
                        icon: L.divIcon({className: 'bricohams-ais-target', html: '&#128674;', iconSize: [22, 22]})
                    })
                    : L.circleMarker([p.lat, p.lon], {
                        color: color, fillColor: color, fillOpacity: 0.9, radius: 6, weight: 2
                    });
                marker.bindTooltip(markerLabel).addTo(aprsLayer);
                t = {points: [], marker: marker,
                    line: L.polyline([], {color: color, weight: 3}).bindTooltip(lineLabel)};
                t.line.addTo(aprsLayer);
                tracks.set(id, t);
            }
            const prev = t.points[t.points.length - 1];
            if (prev && ts <= prev.time) return;
            t.marker.setLatLng([p.lat, p.lon]);
            if (prev && prev.pos[0] === p.lat && prev.pos[1] === p.lon) {
                prev.time = ts;
                return;
            }
            t.points.push({pos: [p.lat, p.lon], time: ts});
            if (t.points.length > MAX_POINTS) t.points.shift();
            t.line.setLatLngs(t.points.map(x => x.pos));
        });
    }

    // Foto y datos del vuelo: adsbdb.com (modelo, matrícula, ruta) y planespotters.net (foto).
    // Se consultan desde el navegador al abrir la ficha y se guardan en memoria.
    const fichas = new Map();
    const MAX_FICHAS = 300;

    function urlSegura(u) {
        try {
            const x = new URL(u);
            return x.protocol === 'https:' ? x.href : '';
        } catch (e) {
            return '';
        }
    }

    function fichaAvion(hex, flight) {
        const icao = String(hex || '').toLowerCase();
        if (!/^[0-9a-f]{6}$/.test(icao)) return Promise.resolve(null);
        const cs = /^[A-Z0-9]{3,8}$/.test(flight || '') ? flight : '';
        const clave = icao + '|' + cs;
        if (fichas.has(clave)) return fichas.get(clave);
        if (fichas.size >= MAX_FICHAS) fichas.delete(fichas.keys().next().value);
        const promesa = (async function () {
            const respuesta = await fetch('bricohams/api/avion?hex=' + icao + (cs ? '&cs=' + cs : ''),
                {credentials: 'same-origin', cache: 'force-cache'});
            if (!respuesta.ok) throw new Error('HTTP ' + respuesta.status);
            const ficha = await respuesta.json();
            if (!ficha || typeof ficha !== 'object' || Array.isArray(ficha)) return null;
            const coord = function (x) {
                return Array.isArray(x) && x.length === 2 && x.every(Number.isFinite) ? x : null;
            };
            ficha.foto = urlSegura(ficha.foto || '');
            ficha.enlace = urlSegura(ficha.enlace || '');
            ficha.pOrigen = coord(ficha.pOrigen);
            ficha.pDestino = coord(ficha.pDestino);
            ficha.ruta = [ficha.origen, ficha.destino].filter(Boolean).join(' → ');
            return Object.keys(ficha).length ? ficha : null;
        })().catch(function (e) {
            console.warn('BricoHams ficha avión:', e);
            fichas.delete(clave);
            return null;
        });
        fichas.set(clave, promesa);
        return promesa;
    }

    // Las fotos vienen de servidores externos: solo se cargan si el oyente aceptó
    // contenido de terceros en el aviso de cookies del receptor (cookie bh_consent).
    function tercerosAceptados() {
        return /(?:^|;\s*)bh_consent=v1\.terceros(?:;|$)/.test(document.cookie);
    }

    // Pinta foto, crédito y datos del vuelo dentro de cualquier contenedor.
    function pintarFicha(caja, ficha, alCambiar) {
        caja.textContent = '';
        if (!ficha) {
            caja.textContent = 'Sin foto ni datos públicos del vuelo';
            return;
        }
        if (ficha.foto && !tercerosAceptados()) {
            const aviso = document.createElement('div');
            aviso.style.cssText = 'font-size:11px;color:#555;margin:6px 0';
            aviso.append(document.createTextNode('Foto externa no cargada (solo cookies necesarias). '));
            const ver = document.createElement('a');
            ver.href = ficha.enlace || ficha.foto;
            ver.target = '_blank';
            ver.rel = 'noopener noreferrer';
            ver.textContent = 'Ver foto';
            aviso.append(ver);
            caja.append(aviso);
        } else if (ficha.foto) {
            const img = document.createElement('img');
            img.src = ficha.foto;
            img.alt = ficha.modelo || 'Foto del avión';
            img.referrerPolicy = 'no-referrer';
            img.style.cssText = 'display:block;width:100%;max-width:260px;margin:6px 0 2px;border-radius:4px';
            img.addEventListener('load', alCambiar);
            img.addEventListener('error', function () { img.remove(); alCambiar(); });
            if (ficha.enlace) {
                const a = document.createElement('a');
                a.href = ficha.enlace;
                a.target = '_blank';
                a.rel = 'noopener noreferrer';
                a.append(img);
                caja.append(a);
            } else {
                caja.append(img);
            }
            const cr = document.createElement('div');
            if (ficha.fuente === 'MAP.FLIGHTS') {
                const referencia = document.createElement('a');
                referencia.href = 'https://map.flights';
                referencia.target = '_blank';
                referencia.rel = 'noopener noreferrer';
                referencia.textContent = 'MAP.FLIGHTS';
                cr.append(referencia);
                if (ficha.credito) cr.append(document.createTextNode(' · ' + ficha.credito));
            } else {
                cr.textContent = ficha.credito || '';
            }
            cr.style.cssText = 'font-size:10px;color:#666';
            caja.append(cr);
        }
        const datos = document.createElement('div');
        datos.style.whiteSpace = 'pre-line';
        datos.textContent = [
            ficha.modelo && 'Modelo: ' + ficha.modelo,
            ficha.matricula && 'Matrícula: ' + ficha.matricula,
            ficha.operador && 'Operador: ' + ficha.operador,
            ficha.aerolinea && 'Aerolínea: ' + ficha.aerolinea,
            ficha.origen && 'Origen: ' + ficha.origen,
            ficha.destino && 'Destino: ' + ficha.destino
        ].filter(Boolean).join('\n');
        caja.append(datos);
        alCambiar();
    }

    async function mostrarAvion(marker, hex, flight) {
        const caja = marker.bhExtra;
        if (!caja || caja.dataset.hex === hex + '|' + flight) return;
        caja.dataset.hex = hex + '|' + flight;
        caja.textContent = 'Buscando foto y datos del vuelo...';
        const ficha = await fichaAvion(hex, flight);
        if (caja.dataset.hex !== hex + '|' + flight) return;
        pintarFicha(caja, ficha, function () { if (marker.getPopup()) marker.getPopup().update(); });
        dibujarRuta(marker, ficha);
    }

    // Ficha en la ventana NATIVA de los aviones de OpenWebRX+ (AircraftMarker),
    // que es la que se abre al pulsar los aviones del mapa.
    const fichasPintadas = new Map();

    function refrescarVentana() {
        try {
            if (typeof infoWindow !== 'undefined' && infoWindow && infoWindow.update) infoWindow.update();
        } catch (e) { /* mapa de Google: se ajusta solo */ }
    }

    function rellenarNativas() {
        document.querySelectorAll('.bh-ficha:not([data-bh-ok])').forEach(function (caja) {
            caja.setAttribute('data-bh-ok', '1');
            const hex = caja.getAttribute('data-icao') || '';
            const cs = caja.getAttribute('data-cs') || '';
            const clave = hex + '|' + cs;
            if (fichasPintadas.has(clave)) {
                pintarFicha(caja, fichasPintadas.get(clave), refrescarVentana);
                return;
            }
            fichaAvion(hex, cs).then(function (ficha) {
                fichasPintadas.set(clave, ficha);
                if (caja.isConnected) pintarFicha(caja, ficha, refrescarVentana);
            });
        });
    }

    function engancharNativo() {
        if (typeof AircraftMarker === 'undefined' || !AircraftMarker.prototype ||
            typeof AircraftMarker.prototype.getInfoHTML !== 'function') {
            setTimeout(engancharNativo, 500);
            return;
        }
        if (AircraftMarker.prototype.bhFicha) return;
        const original = AircraftMarker.prototype.getInfoHTML;
        AircraftMarker.prototype.getInfoHTML = function (name) {
            const html = original.apply(this, arguments);
            let hex = String(this.icao || '').replace(/^~/, '');
            if (!/^[0-9A-F]{6}$/i.test(hex) && /^[0-9A-F]{6}$/i.test(String(name || ''))) hex = String(name);
            if (!/^[0-9A-F]{6}$/i.test(hex)) return html;
            const cs = String(this.flight || '').trim().toUpperCase().replace(/[^A-Z0-9]/g, '');
            setTimeout(rellenarNativas, 0);
            return html + '<div class="bh-ficha" data-icao="' + hex.toLowerCase() + '" data-cs="' + cs +
                '" style="max-width:270px">Buscando foto y datos del vuelo...</div>';
        };
        AircraftMarker.prototype.bhFicha = true;
        // La ventana se reescribe en cada actualización del avión: se vuelve a rellenar.
        new MutationObserver(rellenarNativas).observe(document.body, {childList: true, subtree: true});
    }
    engancharNativo();

    // Línea discontinua origen → avión → destino mientras la ficha está abierta.
    function borrarRuta(marker) {
        if (marker.bhRuta) {
            aircraftLayer.removeLayer(marker.bhRuta);
            marker.bhRuta = null;
        }
    }

    function dibujarRuta(marker, ficha) {
        borrarRuta(marker);
        if (!ficha || !marker.isPopupOpen || !marker.isPopupOpen()) return;
        const aqui = marker.getLatLng();
        const tramos = [];
        if (ficha.pOrigen) tramos.push([ficha.pOrigen, [aqui.lat, aqui.lng]]);
        if (ficha.pDestino) tramos.push([[aqui.lat, aqui.lng], ficha.pDestino]);
        if (!tramos.length) return;
        marker.bhRuta = L.polyline(tramos, {color: '#1f6fd1', weight: 2, dashArray: '6 6', interactive: false})
            .addTo(aircraftLayer);
    }

    async function poll() {
        if (document.hidden) return;
        try {
            const response = await fetch('bricohams/api/aviones', {cache: 'no-store'});
            if (!response.ok) throw new Error('HTTP ' + response.status);
            const data = await response.json();
            if (!Array.isArray(data.aircraft)) throw new Error('Respuesta ADS-B no valida');
            const seen = new Set();
            data.aircraft.forEach(function (a) {
                if (!position(a.lat, a.lon) || typeof a.hex !== 'string' ||
                    !Number.isFinite(a.timestamp) || Date.now() - a.timestamp > 75000) return;
                seen.add(a.hex);
                let marker = aircraft.get(a.hex);
                const flight = typeof a.flight === 'string' ? a.flight.trim() : '';
                const helicopter = a.category === 'A7';
                const iconHtml = helicopter ? '&#128641;' : '&#9992;';
                const iconClass = helicopter ? 'bricohams-helicopter' : 'bricohams-aircraft';
                const label = document.createElement('span');
                label.textContent = (flight || a.hex) + ' (' + a.hex + ')' +
                    (helicopter ? ' · Helicóptero' : '');
                if (!marker) {
                    marker = L.marker([a.lat, a.lon], {
                        icon: L.divIcon({className: iconClass, html: iconHtml, iconSize: [24, 24]})
                    }).addTo(aircraftLayer);
                } else if (marker.bhHelicopter !== helicopter) {
                    marker.setIcon(L.divIcon({
                        className: iconClass, html: iconHtml, iconSize: [24, 24]
                    }));
                }
                aircraft.set(a.hex, marker);
                marker.bhHelicopter = helicopter;
                marker.setLatLng([a.lat, a.lon]);
                if (marker.bhRuta) fichaAvion(marker.bhHex, marker.bhFlight).then(function (f) { dibujarRuta(marker, f); });
                marker.unbindTooltip().bindTooltip(label);
                if (!marker.bhPopup) {
                    marker.bhPopup = document.createElement('div');
                    marker.bhPopup.style.cssText = 'min-width:220px;max-width:260px';
                    marker.bhTexto = document.createElement('div');
                    marker.bhTexto.style.whiteSpace = 'pre-line';
                    marker.bhExtra = document.createElement('div');
                    marker.bhPopup.append(marker.bhTexto, marker.bhExtra);
                    marker.bindPopup(marker.bhPopup);
                    marker.on('popupopen', function () {
                        mostrarAvion(marker, marker.bhHex, marker.bhFlight);
                        fichaAvion(marker.bhHex, marker.bhFlight).then(function (f) { dibujarRuta(marker, f); });
                    });
                    marker.on('popupclose', function () { borrarRuta(marker); });
                }
                marker.bhHex = a.hex;
                marker.bhFlight = flight;
                marker.bhTexto.textContent = label.textContent + '\nAltitud: ' +
                    (a.alt_baro === 'ground' ? 'en tierra' : (a.alt_baro == null ? '?' : a.alt_baro + ' ft')) +
                    '\nVelocidad: ' + (a.gs == null ? '?' : a.gs + ' kt') +
                    '\nRumbo: ' + (a.track == null ? '?' : a.track + ' grados') +
                    '\nPosicion: ' + new Date(a.timestamp).toLocaleTimeString();
            });
            aircraft.forEach(function (marker, id) {
                if (!seen.has(id)) {
                    borrarRuta(marker);
                    aircraftLayer.removeLayer(marker);
                    aircraft.delete(id);
                }
            });
            status.textContent = 'ADS-B local: ' + seen.size + ' con posicion' + (aisStatus ? ' · ' + aisStatus : '');
        } catch (e) {
            aircraftLayer.clearLayers();
            aircraft.clear();
            status.textContent = 'ADS-B local no disponible' + (aisStatus ? ' · ' + aisStatus : '');
            console.error('BricoHams ADS-B:', e);
        }
    }

    function clearTak() {
        takMarkers.clear();
        if (takLayer) {
            map.removeLayer(takLayer);
            layerControl.removeLayer(takLayer);
            takLayer = null;
        }
    }

    async function pollTak() {
        if (location.protocol !== 'https:' || document.hidden) return;
        try {
            const response = await fetch('/settings/bricohams/tak/posiciones', {cache: 'no-store'});
            if (response.status === 401 || response.status === 403) {
                clearTak();
                return;
            }
            if (!response.ok) throw new Error('HTTP ' + response.status);
            const data = await response.json();
            if (!Array.isArray(data.nodes)) throw new Error('Respuesta TAK no valida');
            if (!takLayer) {
                takLayer = L.layerGroup().addTo(map);
                layerControl.addOverlay(takLayer, 'TAK privado (administrador)');
            }
            const seen = new Set();
            data.nodes.forEach(function (n) {
                if (!position(n.lat, n.lon) || typeof n.uid !== 'string') return;
                seen.add(n.uid);
                let marker = takMarkers.get(n.uid);
                if (!marker) {
                    marker = L.circleMarker([n.lat, n.lon], {color: '#802db0', radius: 7}).addTo(takLayer);
                    takMarkers.set(n.uid, marker);
                }
                marker.setLatLng([n.lat, n.lon]);
                const label = document.createElement('span');
                label.textContent = String(n.callsign || n.uid);
                marker.unbindTooltip().bindTooltip(label);
            });
            takMarkers.forEach(function (marker, uid) {
                if (!seen.has(uid)) {
                    takLayer.removeLayer(marker);
                    takMarkers.delete(uid);
                }
            });
        } catch (e) {
            clearTak();
            console.error('BricoHams TAK privado:', e);
        }
    }

    // AIS local: barcos que recibe AIS-catcher en esta estación (no hay fuente externa).
    // La capa aparece solo si la API responde: sin AIS instalado (404) deja de preguntar.
    function textoBarco(b) {
        const nombre = b.shipname || ('MMSI ' + b.mmsi);
        return nombre + ' (MMSI ' + b.mmsi + ')' +
            (b.callsign ? '\nIndicativo: ' + b.callsign : '') +
            (b.destination ? '\nDestino: ' + b.destination : '') +
            '\nVelocidad: ' + (b.speed == null ? '?' : b.speed + ' kn') +
            '\nRumbo: ' + (b.cog == null ? '?' : b.cog + ' grados') +
            '\nÚltima señal: hace ' + Math.round(b.edad) + ' s';
    }

    async function pollAis() {
        if (document.hidden) return true;
        try {
            const response = await fetch('bricohams/api/barcos', {cache: 'no-store'});
            if (response.status === 404) return false;
            if (!response.ok) throw new Error('HTTP ' + response.status);
            const data = await response.json();
            if (!Array.isArray(data.ships)) throw new Error('Respuesta AIS no valida');
            if (!aisLayer) {
                aisLayer = L.layerGroup().addTo(map);
                layerControl.addOverlay(aisLayer, 'AIS local (AIS-catcher)');
            }
            const seen = new Set();
            data.ships.forEach(function (b) {
                if (!position(b.lat, b.lon) || !Number.isInteger(b.mmsi)) return;
                seen.add(b.mmsi);
                let marker = ships.get(b.mmsi);
                if (!marker) {
                    marker = L.marker([b.lat, b.lon], {
                        icon: L.divIcon({className: 'bricohams-ship', html: '&#9973;', iconSize: [22, 22]})
                    }).addTo(aisLayer);
                    marker.bhTexto = document.createElement('div');
                    marker.bhTexto.style.cssText = 'white-space:pre-line;min-width:200px';
                    marker.bindPopup(marker.bhTexto);
                    ships.set(b.mmsi, marker);
                }
                marker.setLatLng([b.lat, b.lon]);
                const label = document.createElement('span');
                label.textContent = b.shipname || ('MMSI ' + b.mmsi);
                marker.unbindTooltip().bindTooltip(label);
                marker.bhTexto.textContent = textoBarco(b);
            });
            ships.forEach(function (marker, id) {
                if (!seen.has(id)) {
                    aisLayer.removeLayer(marker);
                    ships.delete(id);
                }
            });
            aisStatus = 'AIS local: ' + seen.size + ' barcos';
        } catch (e) {
            if (aisLayer) aisLayer.clearLayers();
            ships.clear();
            aisStatus = aisLayer ? 'AIS local no disponible' : '';
            console.error('BricoHams AIS:', e);
        }
        return true;
    }

    // Logo de BricoHams en la cabecera del mapa (nginx ya lo cambia; esto cubre el acceso sin nginx)
    function marca() {
        const original = document.querySelector('.webrx-top-logo:not(.bh-marca-logo)');
        if (!original || original.closest('svg[style*="display:none"]')) return;
        const img = document.createElement('img');
        img.className = 'webrx-top-logo bh-marca-logo';
        img.src = 'static/plugins/receiver/marca/bricohams-logo.png';
        img.alt = img.title = 'BricoHams';
        img.style.cssText = 'height:52px;width:auto;max-width:190px;object-fit:contain;padding:0;border-radius:6px;vertical-align:middle';
        img.addEventListener('error', function () { img.replaceWith(original); });
        const enlace = original.closest('a');
        if (enlace) {
            enlace.href = '/bricohams/';
            enlace.removeAttribute('target');
            enlace.title = 'BricoHams';
        }
        original.replaceWith(img);
    }
    marca();

    function start() {
        if (typeof map !== 'undefined' && map && typeof map.addLayer !== 'function') return;
        if (typeof map === 'undefined' || !map || typeof L === 'undefined' ||
            typeof layerControl === 'undefined' || !layerControl || typeof MapManager === 'undefined') {
            setTimeout(start, 500);
            return;
        }
        aprsLayer = L.layerGroup().addTo(map);
        aircraftLayer = L.layerGroup().addTo(map);
        layerControl.addOverlay(aircraftLayer, 'ADS-B local (readsb)');
        layerControl.addOverlay(aprsLayer, 'Posiciones y trayectorias APRS/AIS (2 h)');
        const control = L.control({position: 'bottomright'});
        control.onAdd = function () {
            status = L.DomUtil.create('div', 'leaflet-control bricohams-live-status');
            status.style.cssText = 'background:white;color:#222;padding:5px 8px;font:12px sans-serif';
            status.textContent = 'Conectando ADS-B local...';
            return status;
        };
        control.addTo(map);
        const atribucion = L.control({position: 'bottomleft'});
        atribucion.onAdd = function () {
            const caja = L.DomUtil.create('div', 'leaflet-control bricohams-mapflights-credit');
            caja.style.cssText = 'background:rgba(255,255,255,.94);padding:5px 8px;border-radius:3px;font:12px sans-serif;display:flex;align-items:center;gap:5px';
            const enlace = document.createElement('a');
            enlace.href = 'https://map.flights';
            enlace.target = '_blank';
            enlace.rel = 'noopener noreferrer';
            enlace.style.cssText = 'display:flex;align-items:center;gap:5px;color:#0f172a;text-decoration:none;font-weight:600';
            const logo = document.createElement('img');
            logo.src = 'https://map.flights/favicon.svg';
            logo.alt = 'map.flights';
            logo.referrerPolicy = 'no-referrer';
            logo.style.cssText = 'width:18px;height:18px';
            enlace.append(logo, document.createTextNode('Powered by MAP.FLIGHTS'));
            caja.append(enlace);
            L.DomEvent.disableClickPropagation(caja);
            return caja;
        };
        atribucion.addTo(map);
        const original = MapManager.prototype.processUpdates;
        MapManager.prototype.processUpdates = function (items) {
            const result = original.apply(this, arguments);
            updates(items);
            return result;
        };
        if (mapManager && mapManager.mman) {
            updates(Object.keys(mapManager.mman.markers).map(function (id) {
                const m = mapManager.mman.markers[id];
                const p = m.mode === 'APRS' || m.mode === 'AIS' ? m.getPos() : [];
                return {callsign: id, mode: m.mode, lastseen: m.lastseen,
                    location: {type: 'latlon', lat: p[0], lon: p[1]}};
            }));
        }
        async function tick() {
            prune(Date.now());
            await poll();
            setTimeout(tick, 2000);
        }
        tick();
        async function takTick() {
            await pollTak();
            setTimeout(takTick, 10000);
        }
        takTick();
        async function aisTick() {
            if (await pollAis() !== false) setTimeout(aisTick, 15000);
        }
        aisTick();
    }
    start();
})();
