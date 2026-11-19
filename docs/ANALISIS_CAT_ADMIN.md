# Análisis: control CAT de los equipos solo para el administrador

Estado: **análisis, sin implementar**. Fecha: 2026-11-19. Equipo revisado: SDR del .105 con OpenWebRX+ 1.2.130.

## Qué se quiere

Que el administrador de la estación, y solo él, pueda controlar por CAT los transceptores desde la web del SDR (frecuencia y modo, y que radio y receptor se sigan mutuamente), al estilo de herramientas como «SDR SYNC» (la de EA1HG que sincroniza una radio por COM con un WebSDR u OpenWebRX). Los oyentes públicos no deben poder tocar ninguna radio.

## Lo que ya trae OpenWebRX+ 1.2.130 (comprobado en el equipo)

- `owrx/rigcontrol.py`: lanza `rigctl` de Hamlib (`rigctl -m <rig_model> -r <rig_device>`) y hace que la radio siga la frecuencia y el modo sintonizados.
- Opciones: `rig_enabled`, `rig_tx_enabled`, `rig_model`, `rig_device` (por defecto `127.0.0.1:4533`, es decir, un `rigctld`) y `rig_address`. En el Pi están instalados `/usr/bin/rigctl` y `/usr/bin/rigctld`.
- `htdocs/lib/Plugins.js` trae un `RigPlugin` con un botón «TRANSMIT». Al pulsarlo envía `{"type": "txcontrol"}` por el websocket del receptor.
- `owrx/connection.py` acepta `txcontrol` de **cualquier** cliente conectado y no comprueba si es administrador. El único freno es la opción global `rig_tx_enabled`.
- `owrx/dsp.py` crea un `RigControl` **por cada oyente** (cada uno con su DSP). Con varios oyentes, la radio seguiría al último que mueva el dial.

**Conclusión:** el control nativo **no sirve** en un SDR público multiusuario. Cualquier visitante movería la radio, y con `rig_tx_enabled` podría transmitir con el indicativo de la estación. Por eso ya se decidió no instalar el botón PTT (ver `docs/OWRX_PLUGINS.md`). Hay que mantener `rig_enabled=False` y `rig_tx_enabled=False`.

## Opciones

### A. Panel CAT en `/settings/bricohams/` (en el servidor, solo administrador) — recomendada

- Se reutiliza `bricohams-mesh-admin` (127.0.0.1:8076), que ya comprueba la sesión de administrador de OpenWebRX+ (`/settings/bricohams/auth`) y ya sirve otros paneles exclusivos del admin. Nginx ya lo publica solo bajo `/settings/bricohams/`.
- Un `rigctld` local por equipo, escuchando solo en `127.0.0.1`. El panel habla con él por TCP con órdenes de Hamlib (`f`/`F` frecuencia, `m`/`M` modo).
- Funciones:
  1. Ver y fijar la frecuencia y el modo de cada radio.
  2. «Radio → SDR»: abrir el receptor en la frecuencia de la radio con un enlace `#freq=…,mod=…`, como ya hace la web.
  3. «SDR → radio»: pasar a la radio la frecuencia que el admin tiene sintonizada en su pestaña.
- **Sin TX** en la primera versión: el panel no ofrece PTT ni ninguna orden que transmita (`T`). Si algún día se quiere transmitir, sería una decisión aparte, con su propia confirmación y su registro, porque es transmisión remota con el indicativo EA5KAO.
- Ventajas: no toca OpenWebRX+, los oyentes no ven nada y aprovecha la autenticación y el registro que ya existen.
- Requisitos: las radios conectadas por USB/CAT al Pi y el modelo de Hamlib de cada una.

### B. Sincronización en el PC o el móvil del administrador (fuera del servidor)

- Como «SDR SYNC»: la radio se conecta al PC o al móvil del administrador y un programa sincroniza la radio con la pestaña del receptor web.
- RadiCodex (la APK de BricoHams) ya tiene CAT. Podría añadir «seguir al SDR» leyendo la frecuencia del receptor web y moviendo la radio que tiene conectada.
- Ventajas: el servidor no gana ninguna capacidad nueva, así que no hay riesgo de que un oyente toque nada. Desventajas: solo funciona con el equipo del admin delante de la radio, no en remoto.

### C. Activar el `RigControl` nativo de OpenWebRX+

Descartada por lo explicado arriba: no tiene control de acceso, lleva un control por oyente y PTT para todos.

## Seguridad (para A)

- Todo pasa por la sesión de administrador (cookie `owrx-session` comprobada por `bricohams-mesh-admin`). Sin sesión: 401 y redirección al login.
- `rigctld` solo en `127.0.0.1`, nunca expuesto en el router ni en el cortafuegos.
- Lista blanca de órdenes (solo leer y fijar frecuencia y modo), con la frecuencia validada y limitada a las bandas de cada radio.
- Registro de cada cambio (usuario, hora y orden) y aviso opcional por Telegram, como ya se hace con los inicios de sesión.
- Nota: hoy `/login` y `/settings` se pueden abrir desde Internet; la opción de OpenWebRX+ «restringir a la red local» no surte efecto detrás de nginx. Antes de añadir un panel CAT conviene decidir si el administrador solo entra desde la LAN o la VPN.

## Equipos elegidos (2026-11-19): Yaesu FTX-1 y QRP Labs QMX+

| Equipo | Soporte en Hamlib | En el Pi (Hamlib 4.6.2 de Debian trixie) |
|---|---|---|
| Yaesu FTX-1 | Modelo **1051**, incluido en Hamlib **4.7.2** (`rigs/yaesu/ftx1/`; su readme indica serie a 38400 8N1, admite 4800-115200, y firmware probado de noviembre de 2025) | **No está**: hay que instalar Hamlib ≥ 4.7.2 (compilado o de backports) antes de poder usarlo |
| QRP Labs QMX+ | Modelo **2057 «QMX»** (estado *Beta*) | Disponible. Hay que comprobar con el equipo real que el QMX+ responde igual que el QMX |

Comprobado con `rigctl -l` en el Pi y en el repositorio oficial de Hamlib (tag 4.7.2). Ninguno de los dos está conectado al Pi por ahora.

## Pendiente de datos (no inventar)

- Cómo se conecta cada equipo al Pi (USB-CAT, puerto y velocidad configurada en la radio) y si comparten la antena o los receptores con el SDR.
- Si la radio de cada equipo se usará también desde RadiCodex: habría que evitar que dos programas abran el mismo puerto (con un `rigctld` compartido se evita).
