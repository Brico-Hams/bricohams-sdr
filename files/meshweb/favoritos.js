/* Adapter for the SHA-256-pinned Meshtastic Web 2.6.7 module.
 * Runs in that module's scope; never stores channel settings or keys. */
(() => {
    const favoritos = new Map();
    const panel = document.createElement("section");
    panel.id = "bricohams-favoritos";
    panel.setAttribute("aria-label", "Conexiones favoritas");
    panel.style.cssText = "padding:10px 16px;background:#172033;color:#f1f5f9;border-bottom:1px solid #64748b";
    const titulo = document.createElement("strong");
    titulo.textContent = "Conexiones favoritas";
    panel.append(titulo);
    const aviso = document.createElement("span");
    aviso.setAttribute("role", "status");
    aviso.style.cssText = "display:block;font-size:13px;margin-top:4px";
    aviso.textContent = "Selecciona una radio. Los canales se leen del nodo; recargar no elimina estos favoritos.";
    const error = (red, causa) => {
        aviso.textContent = `Nodo ${red}: ${causa}`;
    };
    for (const red of ["868", "433"]) {
        const boton = document.createElement("button");
        boton.type = "button";
        boton.textContent = `Nodo ${red} MHz`;
        boton.dataset.bricohamsRadio = red;
        boton.style.cssText = "margin:4px 8px;padding:6px 12px;background:#27354e;color:#fff;border:1px solid #94a3b8;border-radius:6px;cursor:pointer";
        let ocupado = false;
        let actual;
        const liberar = () => { ocupado = false; boton.disabled = false; };
        boton.addEventListener("click", async () => {
            if (ocupado) return;
            const anterior = favoritos.get(red);
            const existente = anterior && ba.getState().devices.get(anterior);
            if (existente?.connection?.isConfigured) {
                lo.getState().setSelectedDevice(anterior);
                aviso.textContent = `Nodo ${red} seleccionado.`;
                return;
            }
            ocupado = true;
            actual = undefined;
            boton.disabled = true;
            aviso.textContent = `Conectando al nodo ${red}...`;
            let conexion;
            try {
                if (existente?.connection) await existente.connection.disconnect();
                const base = `${location.host}/bricohams/nodos/${red}`;
                if (red === "433") {
                    const respuesta = await fetch(`https://${base}/api/v1/estado`, {
                        cache: "no-store", signal: AbortSignal.timeout(5000),
                    });
                    if (!respuesta.ok || !respuesta.headers.get("Content-Type")?.includes("application/json")) {
                        throw new Error("puente 433 no disponible; revisa el servicio y la sesion administrativa");
                    }
                    if (!(await respuesta.json()).radio) throw new Error("USB 433 desconectado");
                }
                const transporte = await wN.create(base, true);
                const id = anterior || Lg();
                const dispositivo = ba.getState().addDevice(id);
                const nodos = si.getState().addNodeDB(id);
                const mensajes = ai.getState().addMessageStore(id);
                conexion = new GS(transporte, id);
                actual = conexion;
                conexion.events.onDeviceStatus.subscribe((estado) => {
                    if (actual !== conexion) return;
                    if (estado === ct.DeviceConfigured) {
                        liberar();
                        aviso.textContent = `Nodo ${red} conectado; canales descargados del nodo.`;
                    } else if (estado === ct.DeviceDisconnected) {
                        liberar();
                        error(red, "sin conexion. Comprueba la sesion y el servicio antes de volver a conectar.");
                    }
                });
                dispositivo.addConnection(conexion);
                NN(dispositivo, conexion, mensajes, nodos);
                favoritos.set(red, id);
                lo.getState().setSelectedDevice(id);
                Promise.resolve(conexion.configure()).catch((causa) => {
                    if (actual !== conexion) return;
                    liberar();
                    console.error(`BricoHams: configuracion ${red}`, causa);
                    error(red, "no se pudo descargar la configuracion del nodo");
                });
            } catch (causa) {
                liberar();
                if (conexion) await conexion.disconnect();
                console.error(`BricoHams: conexion ${red}`, causa);
                error(red, causa instanceof Error ? causa.message : "error de conexion");
            } finally {
                if (!conexion || conexion.isConfigured) liberar();
            }
        });
        panel.append(boton);
    }
    panel.append(aviso);
    const estilo = document.createElement("style");
    estilo.textContent = "#root > .h-screen{height:calc(100dvh - var(--bh-favoritos-height,90px))}";
    panel.append(estilo);
    document.body.prepend(panel);
    const ajustar = () => document.documentElement.style.setProperty("--bh-favoritos-height", `${panel.getBoundingClientRect().height}px`);
    new ResizeObserver(ajustar).observe(panel);
    ajustar();
})();
