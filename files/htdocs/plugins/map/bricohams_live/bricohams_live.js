(function () {
    'use strict';
    const TTL = 2 * 60 * 60 * 1000;
    const MAX_STATIONS = 512;
    const MAX_POINTS = 1000;
    const tracks = new Map();
    const aircraft = new Map();
    let aprsLayer, aircraftLayer, status;
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
            if (u.mode !== 'APRS' || !p || p.type !== 'latlon' ||
                !position(p.lat, p.lon) || typeof u.callsign !== 'string' ||
                !Number.isFinite(ts) || ts > now + 5000 || now - ts > TTL) return;
            let t = tracks.get(u.callsign);
            if (!t) {
                if (tracks.size >= MAX_STATIONS) {
                    const oldest = tracks.keys().next().value;
                    aprsLayer.removeLayer(tracks.get(oldest).line);
                    tracks.delete(oldest);
                }
                const label = document.createElement('span');
                label.textContent = u.callsign + ' - trayectoria APRS';
                t = {points: [], line: L.polyline([], {color: '#e87524', weight: 3}).bindTooltip(label)};
                t.line.addTo(aprsLayer);
                tracks.set(u.callsign, t);
            }
            const prev = t.points[t.points.length - 1];
            if (prev && ts <= prev.time) return;
            if (prev && prev.pos[0] === p.lat && prev.pos[1] === p.lon) {
                prev.time = ts;
                return;
            }
            t.points.push({pos: [p.lat, p.lon], time: ts});
            if (t.points.length > MAX_POINTS) t.points.shift();
            t.line.setLatLngs(t.points.map(x => x.pos));
        });
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
                if (!marker) {
                    marker = L.marker([a.lat, a.lon], {
                        icon: L.divIcon({className: 'bricohams-aircraft', html: '&#9992;', iconSize: [24, 24]})
                    }).addTo(aircraftLayer);
                    aircraft.set(a.hex, marker);
                }
                marker.setLatLng([a.lat, a.lon]);
                const label = document.createElement('span');
                label.textContent = (a.flight || a.hex) + ' (' + a.hex + ')';
                marker.unbindTooltip().bindTooltip(label);
                const popup = document.createElement('div');
                popup.textContent = label.textContent + '\nAltitud: ' +
                    (a.alt_baro === 'ground' ? 'en tierra' : (a.alt_baro == null ? '?' : a.alt_baro + ' ft')) +
                    '\nVelocidad: ' + (a.gs == null ? '?' : a.gs + ' kt') +
                    '\nRumbo: ' + (a.track == null ? '?' : a.track + ' grados') +
                    '\nPosicion: ' + new Date(a.timestamp).toLocaleTimeString();
                popup.style.whiteSpace = 'pre-line';
                marker.unbindPopup().bindPopup(popup);
            });
            aircraft.forEach(function (marker, id) {
                if (!seen.has(id)) {
                    aircraftLayer.removeLayer(marker);
                    aircraft.delete(id);
                }
            });
            status.textContent = 'ADS-B local: ' + seen.size + ' con posicion';
        } catch (e) {
            aircraftLayer.clearLayers();
            aircraft.clear();
            status.textContent = 'ADS-B local no disponible';
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
        layerControl.addOverlay(aprsLayer, 'Trayectorias APRS (2 h desde apertura)');
        const control = L.control({position: 'bottomright'});
        control.onAdd = function () {
            status = L.DomUtil.create('div', 'leaflet-control bricohams-live-status');
            status.style.cssText = 'background:white;color:#222;padding:5px 8px;font:12px sans-serif';
            status.textContent = 'Conectando ADS-B local...';
            return status;
        };
        control.addTo(map);
        const original = MapManager.prototype.processUpdates;
        MapManager.prototype.processUpdates = function (items) {
            const result = original.apply(this, arguments);
            updates(items);
            return result;
        };
        if (mapManager && mapManager.mman) {
            updates(Object.keys(mapManager.mman.markers).map(function (id) {
                const m = mapManager.mman.markers[id];
                const p = m.mode === 'APRS' ? m.getPos() : [];
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
    }
    start();
})();
