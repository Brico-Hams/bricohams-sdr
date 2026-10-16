# 40 · Solo HTTPS, mapa local (ADS-B/AIS), políticas, cookies, idioma y logo

<!-- guia-visual:inicio -->
> **Ruta visual:** [Portal, HTTPS, API y paneles administrativos](../GUIA_VISUAL_MODULOS.md#web).
> Consulta allí requisitos, ilustración, cuadro de instalación, comprobaciones y restauración.
> Los comandos de este manual se ejecutan en Bash en la Pi; revisa el backup antes de cambiarla.
<!-- guia-visual:fin -->

## Qué cambia en v5.0

| Antes | Ahora |
|---|---|
| `SSL_MODO="admin"`: receptor por HTTP, administración por HTTPS | `SSL_MODO="todo"` (defecto): **todo por 443**; el 80 solo redirige a HTTPS y sirve Let's Encrypt; HSTS activo |
| OpenWebRX+ escuchaba en `0.0.0.0:8073` (LAN o Internet) | **8073 decomisionado**: solo `127.0.0.1` (`OWRX_SOLO_LOCAL="yes"`); se entra por nginx |
| tar1090 por lighttpd en 8504 | tar1090 servido por nginx con la configuración oficial (`/etc/nginx/snippets/bricohams-tar1090.conf`) |
| Módulo «WEB» con webs externas (AstroRadio ADS-B/AIS, meteo) | Eliminado. **Aviones y barcos salen de la recepción propia** y se ven en `/map` |
| Logo de OpenWebRX+ en receptor, `/map` y `/settings` | Logo **BricoHams** en todas las páginas |

## 1. Solo HTTPS y 8073 cerrado

- `bricohams.env`:
  ```bash
  SSL_MODO="todo"          # admin · todo (defecto) · no
  OWRX_SOLO_LOCAL="yes"    # OpenWebRX+ solo en 127.0.0.1:8073
  BLINDAJE_8073="cerrado"  # publico · lan · cerrado
  ```
- `install.sh --solo configuracion` escribe `/etc/openwebrx/openwebrx.conf.d/22-solo-local.conf`
  (`[web] bind_address = 127.0.0.1`). En Docker con red `bridge` se publica `127.0.0.1:PUERTO:8073`.
- `install.sh --solo web` genera el sitio nginx en modo `todo` (80 → 301 HTTPS, salvo
  `/.well-known/acme-challenge/`; cabecera `Strict-Transport-Security`).
- `bricohams-blindaje` con `cerrado` no abre el 8073 ni en la LAN y avisa si OpenWebRX+
  sigue escuchando fuera de `127.0.0.1`.
- **Router:** abre 443 (y 80 para la redirección y la renovación del certificado). Cierra el 8073.

Comprobar:

```bash
ss -Hltn 'sport = :8073'                 # solo 127.0.0.1:8073
curl -sI http://127.0.0.1/ | head -3     # 301 → https://
curl -skI https://127.0.0.1/ | grep -i strict-transport
```

## 2. Mapa en vivo con recepción propia

El plugin de mapa `bricohams_live.js` añade capas a `/map` de OpenWebRX+:

- **ADS-B local**: readsb/tar1090 de la estación (`/bricohams/api/aviones`), con ficha
  map.flights (foto solo con consentimiento de terceros).
- **AIS local** (nuevo): AIS-catcher con un SDR propio en 162 MHz. La capa
  «AIS local (AIS-catcher)» solo aparece si `/bricohams/api/barcos` responde 200; con
  `AIS_ENABLE="no"` responde 404 y el mapa deja de consultarla.

Activar AIS (requiere un **tercer SDR** con antena VHF marina, distinto del de ADS-B):

```bash
AIS_ENABLE="yes"
AIS_SDR_SERIAL="00000162"   # número de serie del RTL-SDR de AIS (rtl_test lo muestra)
sudo bash install.sh --solo ais,web
```

- Servicio `bricohams-ais` (usuario dinámico, grupo `plugdev`): AIS-catcher con
  `-N 8100 IP_BIND 127.0.0.1`. El servicio `ais-catcher` del instalador oficial se desactiva
  (su puerto de control 8118 escucha en toda la red).
- La API valida cada barco (MMSI numérico de hasta 9 dígitos, coordenadas válidas, última señal ≤ `AIS_MAX_EDAD`, 900 s).
- El portal enlaza `/map` («Aviones (ADS-B) y barcos (AIS) de recepción propia»).

## 3. Políticas, cookies y consentimiento

- Página `/bricohams/politicas.html`: seguridad (solo HTTPS, HSTS, 8073 interno),
  tabla de datos tratados, proveedores (OpenStreetMap, GitHub, map.flights) y sección
  «Aviones y barcos en el mapa». `/bricohams/privacidad.html` enlaza con ella.
- Banner de cookies (`plugins/receiver/consentimiento`): cookie propia `bh_consent`
  (`v1.necesarias` o `v1.terceros`, 180 días). Sin «terceros» no se cargan las fotos de
  aviones de servidores externos; el resto del receptor funciona igual.

## 4. Idioma y logo

- `plugins/receiver/idioma`: botón ES/EN en la cabecera; guarda `bh_idioma` en
  `localStorage` (por defecto, el idioma del navegador).
- Logo BricoHams (`plugins/receiver/marca/bricohams-logo.png`) en todas las páginas:
  - **nginx** (`bricohams-sdr-rutas.conf`, `location /`): `sub_filter` cambia el enlace y el
    SVG `webrx-top-logo` de la cabecera de OpenWebRX+ por el logo BricoHams, enlazado a
    `/bricohams/`. Pide la respuesta sin comprimir (`Accept-Encoding ""`) para poder
    sustituirla. Cubre receptor, `/map`, `/settings` y el resto de páginas.
  - **plugins** (`marca.js` en el receptor y `marca()` en `bricohams_live.js` para el mapa):
    hacen lo mismo en el navegador si nginx no lo ha hecho; con el logo ya cambiado
    (`bh-marca-logo`) no hacen nada.

## 5. Pruebas

```bash
python3 tests/test_politicas_mapa_local.py   # sin AstroRadio, políticas, 443, AIS, logo
python3 tests/test_instalador_docker.py      # bridge en 127.0.0.1
python3 tests/test_ssl_admin.py              # SSL_MODO="todo" por defecto
python3 tests/test_mesh_admin.py             # nginx solo cambia el logo
```

## 6. Volver atrás

- Receptor de nuevo en la LAN: `OWRX_SOLO_LOCAL="no"`, `BLINDAJE_8073="lan"` y
  `sudo bash install.sh --solo configuracion,web`.
- Receptor por HTTP: `SSL_MODO="admin"` y `sudo bash install.sh --solo web`. HSTS queda
  recordado en los navegadores hasta 180 días.
- Restaurar desde la copia hecha antes del despliegue (ver manual 09).
