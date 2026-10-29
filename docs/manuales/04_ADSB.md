# 04 · ADS-B con el FlightStick de RadarBox (readsb + rbfeeder + MLAT)

<!-- guia-visual:inicio -->
> **Ruta visual:** [ADS-B local, RadarBox y map.flights simultáneos](../GUIA_VISUAL_MODULOS.md#adsb).
> Consulta allí requisitos, ilustración, cuadro de instalación, comprobaciones y restauración.
> Los comandos de este manual se ejecutan en Bash en la Pi; revisa el backup antes de cambiarla.
<!-- guia-visual:fin -->

## Qué deja el instalador (paso `adsb`)

| Pieza | Configuración |
|---|---|
| readsb | `/etc/default/readsb`: `RECEIVER_OPTIONS="--device-type rtlsdr --device 00001090 --gain auto --ppm 0"`. Ubicación con `readsb-set-location`. Salida Beast en `:30005` |
| tar1090 | mapa en `http://<pi>/tar1090/` |
| rbfeeder | `/etc/rbfeeder.ini`, más abajo |

```ini
[client]
network_mode = true
# El instalador rellena lat/lon desde STATION_LAT/STATION_LON.
alt = tu_altitud    ; altura de la ANTENA sobre el nivel del mar (ADSB_ANT_ALT)
key = …            ; se conserva la que haya

[network]
mode = beast
external_host = 127.0.0.1
external_port = 30005

[mlat]
autostart_mlat = true
```

## Paso a paso
1. Conecta la antena de 1090 al FlightStick y el FlightStick al hub.
2. `sudo bash install.sh --solo adsb`. El instalador ya lo hace la primera vez.
3. **Clave de RadarBox:**
   - Si ya tenías estación, pon su clave en `RADARBOX_KEY`, o lanza `sudo rbfeeder --setkey CLAVE` y después `sudo systemctl restart rbfeeder`.
   - Si es nueva: `sudo rbfeeder --showkey` y asóciala en https://www.airnavradar.com/raspberry-pi/claim
4. Comprueba:
   - `sudo bricohams-check`, sección ADS-B.
   - `sudo systemctl status rbfeeder`.
   - `tail /var/log/rbfeeder.log` (debe salir *Connected*).
5. **MLAT:** pon en `ADSB_ANT_ALT` la altura real de la antena (la del terreno más la del mástil). Necesita la hora del GPS sincronizada; compruébalo con `chronyc sources`, donde el PPS debe salir con `*`.

## Foto y datos del vuelo en el mapa (v5.0)
- Pulsa un avión en el mapa de OpenWebRX+ y el globo muestra:
  - la foto del modelo (planespotters.net, con el crédito del fotógrafo);
  - el tipo, la matrícula y el operador;
  - el origen y el destino del vuelo (adsbdb.com, según el indicativo).
- La ficha sale en el globo **nativo** de OpenWebRX+ (`AircraftMarker`): el plugin `bricohams_live` envuelve `getInfoHTML` y añade un bloque `bh-ficha` que se rellena al abrirse.
- Los datos los pide la Pi mediante el proxy `GET /bricohams/api/avion?hex=<icao>&cs=<indicativo>` (`bricohams-api`):
  - fuentes: adsbdb.com (tipo, matrícula, operador y ruta) y planespotters.net (foto);
  - valida el hex (6 caracteres hexadecimales) y el indicativo; con un valor inválido responde 400;
  - caché en memoria de 6 h; las respuestas vacías o fallidas se guardan solo 10 min.
  - Si el proxy falla, el navegador consulta directamente adsbdb y planespotters.
- Si no hay foto o el avión no está en la base (militares, privados), se ve solo lo que manda readsb.
- Tras actualizar, recarga el mapa con **Ctrl+F5** para que el navegador tome el JS nuevo.
- Prueba: `python tests/test_avion.py`. Desde la Pi: `curl -s 'http://127.0.0.1:8075/bricohams/api/avion?hex=3c6444'`.

### No aparece ningún avión
El globo solo se rellena si readsb ve aviones. Comprueba:
```bash
python3 -c 'import json;print(len(json.load(open("/run/readsb/aircraft.json"))["aircraft"]))'
python3 -c 'import json;l=json.load(open("/run/readsb/stats.json"))["last1min"]["local"];print(l["accepted"],l["signal"],l["noise"])'
```
Si `signal` ≈ `noise` y `accepted` apenas pasa de unas decenas por minuto, el problema es de RF: la antena, el LNA, el cable o el dongle. Revisa también que la serie de `--device` en `/etc/default/readsb` sea la del dongle conectado a la antena de 1090 MHz.

## Problemas típicos
- **readsb no arranca:** la serie no es 00001090 → [manual 03](03_SDR_Y_SERIES.md).
- **Pocos aviones:** prueba `ADSB_GAIN` fija (por ejemplo `43.9`) en vez de `auto`.

### logrotate falla por el registro de MLAT (v5.0)

El paquete `mlat-client` puede instalar `/etc/logrotate.d/mlat-client` sin `missingok`.
Si `/var/log/mlat-client.log` todavía no existe, falla `logrotate.service`; no implica por sí solo que readsb o rbfeeder hayan dejado de recibir.

El paso `adsb` del instalador añade `missingok` y `notifempty` a esa regla cuando existe y aún no contiene `missingok`.
Así se admite la ausencia del registro y no se rota si está vacío. La corrección no crea un registro ficticio.
En instalaciones existentes, revisar la regla y seguir el flujo de actualización con **backup verificado y restauración preparada**
antes de repetir `sudo bash install.sh --solo adsb`: ese paso también reconfigura el servicio ADS-B.

Comprobaciones sin forzar una rotación:

```bash
sudo journalctl -u logrotate.service -n 30 --no-pager
sudo grep -nE 'daily|missingok|notifempty' /etc/logrotate.d/mlat-client
sudo logrotate --debug /etc/logrotate.conf
```

Si la regla no existe, no hay nada que corregir en ese fichero. Si contiene `missingok` pero no `notifempty`,
el instalador actual no añade la segunda directiva: revisar esa configuración por separado.

## Enviar también a map.flights (v5.1)

[map.flights](https://map.flights) es un destino **adicional**: RadarBox sigue recibiendo exactamente lo mismo.
Sin `MAPFLIGHTS_FEED="yes"` no cambia nada.

**Validación de referencia (15-10-2026):** en la estación principal se confirmó la recepción simultánea en
RadarBox y map.flights, el handshake MLAT y la conservación de la configuración de RadarBox.
En una instalación nueva de este kit hay que registrar su propia estación y aplicar la configuración;
crear la estación en la web no activa el envío.

### Cómo funciona
| Pieza | Qué hace |
|---|---|
| readsb | Añade a `NET_OPTIONS` de `/etc/default/readsb` el conector `--net-connector=feed.map.flights,30004,beast_reduce_plus_out,uuid=<UUID>`. Solo ese protocolo lleva la etiqueta `uuid` |
| `bricohams-mapflights-mlat` | Un `mlat-client` propio: lee Beast de `127.0.0.1:30005`, va a `mlat.map.flights:31090` con `--user <UUID>`. Sus resultados **no** se reinyectan en readsb (como el MLAT de RadarBox, ADR-55). Corre con `DynamicUser` |
| `/etc/bricohams/mapflights.env` | UUID, servidor MLAT y posición de la antena. `root`, modo 600 |
| rbfeeder | **No se toca**: sigue con su MLAT de RadarBox |

El ayudante `files/bin/bricohams-mapflights.py` edita `/etc/default/readsb` de forma idempotente: solo cambia el
conector de map.flights y conserva el resto de opciones y de conectores.

### UUID y clave de feed
- **UUID de la estación** (etiqueta beast, `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`): es lo único que usa este método.
  No es una contraseña (viaja en claro por TCP), pero map.flights pide **no publicarlo**. Si se filtra, se cambia en su web.
  Va solo en el `bricohams.env` real de la estación, nunca en `bricohams.env.example` ni en el repositorio.
- **Clave de feed `mf_feed_…`**: es del cliente alternativo `mapflights-feeder` (envía `aircraft.json` por HTTPS).
  **No hace falta** con este método. map.flights solo la enseña una vez: guárdala en un gestor de contraseñas y
  no la pongas en el kit, en scripts ni en la línea de órdenes.

### Procedimiento
1. **Alta:** en map.flights entra en *Mis estaciones*, crea la estación con la misma posición que `STATION_LAT`/`STATION_LON`
   y copia el **UUID**.
2. **Copia de seguridad verificada** (antes de tocar nada):
   ```bash
   f=$(sudo /usr/local/sbin/bricohams-backup | tail -1) && echo "$f"   # /var/backups/bricohams/backup-openwebrx-AAAA-MM-DD.tar.gz
   sudo tar -tzf "$f" | grep -E 'etc/default/readsb|etc/rbfeeder.ini|etc/bricohams/'
   ```
   Si el `tar -tzf` falla o no lista `etc/default/readsb`, **para aquí**. Apunta la ruta del fichero.
3. **Configuración**, en el `bricohams.env` de la estación (no en el ejemplo):
   ```bash
   MAPFLIGHTS_FEED="yes"
   MAPFLIGHTS_UUID="<UUID de Mis estaciones>"
   MAPFLIGHTS_MLAT="yes"
   ```
   Revisa que `ADSB_ANT_ALT` sea la altura real de la antena: map.flights la usa para MLAT. Es altura sobre el nivel
   del mar (como en RadarBox); mlat-client espera la del elipsoide, que en la Península es ~50 m mayor. Para afinar MLAT
   puedes sumar esa diferencia, pero afecta también a `rbfeeder.ini`.
4. **Aplicar:** `sudo bash install.sh --solo adsb`. Debe salir
   `map.flights: readsb -> feed.map.flights:30004 (beast_reduce_plus_out) + MLAT; RadarBox sin cambios`.
   Con un UUID no válido avisa y no envía nada a map.flights.
5. **Comprobar:**
   ```bash
   sudo bricohams-check                                   # sección ADS-B: RadarBox y map.flights
   ss -tnp | grep -E ':30004 |:31090 '                     # conexiones a feed.map.flights y mlat.map.flights
   systemctl status bricohams-mapflights-mlat --no-pager
   journalctl -u bricohams-mapflights-mlat -n 30 --no-pager
   sudo systemctl status rbfeeder --no-pager               # RadarBox sigue igual
   ```
   En map.flights, la estación pasa a *en línea* en unos minutos; el MLAT tarda más en sincronizar.
   Si el registro de MLAT dice *already connected*, hay otro cliente con el mismo UUID: deja uno solo.

### Si la web sigue mostrando cero
- El servicio de este kit se llama `bricohams-mapflights-mlat`; `mapflights-mlat` es el del instalador oficial.
  No arranques los dos con la misma identidad.
- `journalctl -u readsb --no-pager` debe mostrar la conexión a `feed.map.flights`; en el MLAT debe aparecer
  `Handshake complete` y la entrada conectada a `127.0.0.1:30005`.
- Un servicio activo no demuestra que envíe: comprueba la conexión y los contadores TCP con
  `sudo ss -tinp dst feed.map.flights`, y los paquetes de RadarBox con `journalctl -u rbfeeder -n 20 --no-pager`.
- El estado web puede tardar unos minutos; los resúmenes medidos pueden actualizarse al día siguiente.
  Participar en MLAT no garantiza resultados inmediatos: hacen falta otras estaciones que reciban los mismos aviones.
- Guía oficial: [montar y conectar un receptor](https://map.flights/es/stations/build).

### Fotos e información de los vuelos en el mapa local
En `/map` de OpenWebRX+, activa **ADS-B local (readsb)** y pulsa un icono **✈**: la foto, modelo, matrícula,
operador y ruta aparecen en su ventana, no de forma permanente sobre el mapa. Si falta la actualización,
recarga con **Ctrl+F5**. Esta ficha no corresponde a tar1090 ni a la web de map.flights.

El 15-10-2026 se comprobó una foto realmente cargada y la ruta de un vuelo en la estación principal.
La API `/bricohams/api/avion?hex=<ICAO>&cs=<INDICATIVO>` obtiene datos mediante `bricohams-api`.
Si un avión no tiene información pública o el proveedor no responde, puede no haber foto o ruta.
Si el contador dice «0 con posicion», no hay posiciones recientes para dibujar; no implica un fallo de las fotos.

### Desactivar o volver atrás
- **Desactivar:** `MAPFLIGHTS_FEED="no"` y `sudo bash install.sh --solo adsb`. Quita el conector de readsb, para y borra
  `bricohams-mapflights-mlat` y `/etc/bricohams/mapflights.env`. RadarBox no se toca.
- **Restaurar la copia** del paso 2 si algo queda mal:
  ```bash
  sudo systemctl disable --now bricohams-mapflights-mlat 2>/dev/null
  sudo tar -xzf <ruta-de-la-copia> -C / etc/default/readsb etc/rbfeeder.ini
  sudo rm -f /etc/systemd/system/bricohams-mapflights-mlat.service /etc/bricohams/mapflights.env
  sudo systemctl daemon-reload && sudo systemctl restart readsb rbfeeder
  ```

Prueba del repositorio: `python tests/test_mapflights.py`.
