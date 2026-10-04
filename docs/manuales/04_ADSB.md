# 04 · ADS-B con el FlightStick de RadarBox (readsb + rbfeeder + MLAT)

## Qué deja el instalador (paso `adsb`)

| Pieza | Configuración |
|---|---|
| readsb | `/etc/default/readsb`: `RECEIVER_OPTIONS="--device-type rtlsdr --device 00001090 --gain auto --ppm 0"`. Ubicación con `readsb-set-location`. Salida Beast en `:30005` |
| tar1090 | mapa en `http://<pi>/tar1090/` |
| rbfeeder | `/etc/rbfeeder.ini`, más abajo |

```ini
[client]
network_mode = true
lat = 0.0
lon = 0.0
alt = 205          ; altura de la ANTENA sobre el nivel del mar (ADSB_ANT_ALT)
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

## Problemas típicos
- **readsb no arranca:** la serie no es 00001090 → [manual 03](03_SDR_Y_SERIES.md).
- **Pocos aviones:** prueba `ADSB_GAIN` fija (por ejemplo `43.9`) en vez de `auto`.
