# 38 · Módulo map.flights para OpenWebRX+

<!-- guia-visual:inicio -->
> **Ruta visual:** [ADS-B local, RadarBox y map.flights simultáneos](../GUIA_VISUAL_MODULOS.md#adsb).
> Consulta allí requisitos, ilustración, cuadro de instalación, comprobaciones y restauración.
> Los comandos de este manual se ejecutan en Bash en la Pi; revisa el backup antes de cambiarla.
<!-- guia-visual:fin -->

**Idioma / Language:** Español · [English](../en/MAPFLIGHTS_PLUGIN.md)

**Estado:** módulo integrado en el kit, **sin desplegar**. Los comandos de este
manual describen una instalación futura, no acciones realizadas.
La interfaz actual del panel está en español; la guía inglesa no cambia su idioma.

## Alcance

El módulo tiene dos partes independientes: en el mapa de OpenWebRX+ consulta
map.flights para completar las fichas de los aviones locales, y en `/settings`
mantiene el panel privado de diagnóstico del feed Beast/MLAT descrito en el
[manual 04](04_ADSB.md). No requiere una segunda instancia de OpenWebRX+ ni
otro receptor.

El detalle de vuelos se habilita en **General Settings → map.flights** con
**Use map.flights for aircraft details**. En la misma sección está el campo
**map.flights API key** (tipo contraseña, opcional): vacío usa el acceso
anónimo de map.flights, con límites más bajos; con la clave de la beta privada
(se pide en `https://map.flights/developers`), el servidor la envía en la
cabecera `x-api-key`. Si map.flights la rechaza, se repite la consulta en modo
anónimo.
El navegador solo llama a la API local; el servidor consulta map.flights por
el ICAO del avión al abrir su ficha y conserva la caché local de seis horas.
map.flights es el proveedor principal; adsbdb y Planespotters quedan como
respaldo cuando falten campos. Si se desactiva el selector, se usan únicamente
los respaldos existentes.

El mapa muestra **Powered by MAP.FLIGHTS**, el icono oficial y un enlace a
`https://map.flights`. Se conserva además el crédito de la foto cuando la
respuesta identifica a su fotógrafo.

**Fotos (v5.0).** map.flights devuelve sus propias fotos con ruta relativa
(`/photos/ext_…_640.webp`), con autor, origen (`source`, p. ej. `wikimedia`) y
licencia. La API las completa a `https://map.flights/photos/…` y compone el
crédito «© autor · Wikimedia Commons · CC BY 2.0»; antes se descartaban por no
empezar por `https://` y la ficha caía a la foto de Planespotters, que salía con
su crédito aunque los datos fueran de map.flights. Si la foto no indica el
origen, se deduce del dominio (Planespotters). Prueba: `test_mapflights_api.py`.

## Flujo

![Un receptor, RadarBox y map.flights simultáneos](../esquemas/27_adsb_destinos.svg)

La integración de datos de vuelo sigue en el servidor:

- readsb → RadarBox mediante rbfeeder, conservando su configuración.
- readsb → map.flights con Beast etiquetado y UUID privado.
- mlat-client separado → MLAT map.flights, mismo UUID, sin reinyectar resultados.
- OpenWebRX+ → API local → endpoint oficial de detalle por ICAO de map.flights.
- El mapa OpenWebRX+ pinta las posiciones de readsb local; no reemplaza la
  capa de seguimiento local por el mapa global del proveedor.

## Instalar el panel

En una estación existente, **antes de aplicar** guarda y verifica una copia
de los archivos/configuración/datos afectados y documenta cómo restaurarla
([manual 09](09_MANTENIMIENTO.md)). Si falla, no continúes.
Desde la carpeta del kit en Bash de la Raspberry:

```bash
sudo bash install.sh --solo web
sudo nginx -t
systemctl status bricohams-mesh-admin nginx --no-pager
```

El paso web también configura otros componentes web: no es una instalación
aislada del módulo. Revisa SSL y configuración antes de repetirlo.
Abre `/settings` por HTTPS, inicia sesión como administrador y activa
**General Settings → map.flights → Use map.flights for aircraft details**.
Si tienes API key de map.flights, pégala en **map.flights API key** y pulsa
**Apply and save**; se guarda en `settings.json` de OpenWebRX+ (solo
administrador) y nunca se envía al navegador ni aparece en los registros.
El botón de diagnóstico del feed sigue bajo `/settings/bricohams/mapflights`.
La API y el UUID del feed son independientes; no se publica el UUID ni se
incrusta un iframe de la cuenta map.flights.

## Activar el feed (separado de instalar el panel)

1. Comprueba recepción local y que RadarBox siga recibiendo.
2. Con backup verificado, edita el `bricohams.env` del kit en un editor privado:
   `MAPFLIGHTS_FEED="yes"`, `MAPFLIGHTS_UUID` propio y `MAPFLIGHTS_MLAT`
   según la participación deseada. No uses la clave `mf_feed_`.
3. Conserva `RADARBOX_KEY`, serie del receptor y posición real.

```bash
sudo bash install.sh --solo adsb
sudo bricohams-check
```

El paso ADS-B reinicia brevemente readsb/rbfeeder. Instalar el panel no ejecuta
este paso ni modifica por sí solo un feed existente.

## Verificar y diagnosticar

### UUID, claves y atribución

El envío Beast usa el UUID de la estación, compartido con su cliente MLAT.
No utiliza la clave `mf_feed_` ni requiere una API key de adsb.lol, adsb.fi o
las bases de datos de aeronaves para enviar este feed.

El endpoint público de detalle consultado es
`https://map.flights/api/v1/aircraft/{hex}`. Funciona sin credenciales
(acceso anónimo con límites bajos) y, si se rellena **map.flights API key**,
con la clave en la cabecera `x-api-key` (nunca en la URL). Solo el
servidor envía el ICAO del avión seleccionado; la posición del receptor no se
envía. Se mantiene la atribución fotográfica devuelta por la API. No uses el
UUID del feed ni una clave `mf_feed_` como si fueran credenciales de esta API.

### Interpretar los estados

| Indicación | Qué prueba | Qué no prueba |
|---|---|---|
| Envío solicitado | Valor guardado de MAPFLIGHTS_FEED | Que el conector se haya aplicado |
| Selector General Settings activo | Se permite consultar los detalles a map.flights | Que map.flights tenga datos para todos los ICAO |
| UUID válido | Formato hexadecimal | Que pertenezca a tu cuenta |
| readsb activo | Proceso local | Recepción RF útil o posiciones |
| rbfeeder activo | Proceso de RadarBox | Recepción confirmada por su portal |
| MLAT activo | Proceso independiente | Handshake o participación aceptada |

Confirma el feed en **ambos portales** y consulta localmente el journal de MLAT
para el handshake. No publiques ese journal sin anonimizar: puede contener UUID
y ubicación. La consulta de fichas es independiente de esos servicios de envío.

Sin sesión, el panel redirige al login. No acepta cambios por POST.
Si la configuración no se puede leer, muestra un error; revisa permisos y
el servicio, no hagas públicos los archivos para resolverlo.

## Desactivar o restaurar

Para retirar solo el envío a map.flights, con copia verificada cambia
`MAPFLIGHTS_FEED="no"` en el kit y repite `--solo adsb`. Se conserva RadarBox.
El panel puede seguir instalado para documentar el estado desactivado.
Para volver a una versión anterior del panel, restaura los archivos afectados
desde la copia verificada y reinicia el servicio administrativo según el
procedimiento de tu backup. No extraigas archivos desconocidos sobre `/`.

## Implementación y pruebas

- Backend de fichas: `files/bin/bricohams-api.py`; proveedor primario map.flights
  y respaldos adsbdb/Planespotters con caché.
- Selector de General Settings: `files/bin/bricohams-owrx-mapflights`, parche
  idempotente/reversible reaplicado por apt.
- Mapa y atribución: `files/htdocs/plugins/map/bricohams_live/bricohams_live.js`.
- Panel de feed: `files/bin/bricohams-mesh-admin`, página registrada en `PAGINAS`.
- Botón: `files/bin/bricohams-owrx-botones`; idempotente y reaplicado por el
  gancho apt existente.
- Proxy: prefijo autenticado de paneles en nginx, sin nuevo puerto público.
- Feed: `files/bin/bricohams-mapflights.py` y paso `adsb`.
- Pruebas: `tests/test_mapflights_api.py` (mapeo de respuesta oficial, selector,
  fallback y atribución), `tests/test_avion.py`, `tests/test_mesh_admin.py`
  (sesión, lectura, UUID oculto, POST rechazado y HEAD) y `tests/test_mapflights.py`
  (conector y conservación de otros destinos). No requieren credenciales reales
  ni envío de datos.
