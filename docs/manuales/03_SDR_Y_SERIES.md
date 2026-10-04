# 03 · SDR y números de serie

Los cuatro RTL-SDR (HAT, Mini, V3 y FlightStick) son iguales para el sistema. Por eso cada uno lleva grabada su serie en la EEPROM:

| SDR | Serie | Lo usa |
|---|---|---|
| RTL del HAT | 00000101 | OpenWebRX · SATÉLITES |
| Mini RTL-SDR | 00000102 | OpenWebRX · RADIOAFICIONADOS |
| RTL-SDR Blog V3 | 00000103 | OpenWebRX · MULTIPERFIL + HF |
| FlightStick | 00001090 | readsb (ADS-B) |

## Paso a paso
1. `sudo bricohams-sdr-serials` muestra lo que hay conectado y su serie.
2. `sudo bricohams-sdr-serials --grabar`:
   1. El script para OpenWebRX y readsb.
   2. **Deja conectado solo el RTL del HAT** y pulsa Intro.
   3. Enchufa el **Mini** y pulsa Intro.
   4. Enchufa el **V3** y pulsa Intro.
   5. Enchufa el **FlightStick** y pulsa Intro.
3. `sudo reboot`: las series nuevas se leen al volver a enchufar.
4. `sudo bricohams-check`: en la sección **SDR** deben salir los cuatro.

## Comprobaciones
- `rtl_test -t` lista los dispositivos con `SN: 0000010x` y `00001090`.
- En OpenWebRX, cada receptor abre sus perfiles. Si uno sale «device not found», su serie no coincide.
- HF en el V3: elige un perfil `hf40` y escucha 7,074 (FT8). Sin antena de HF por el diplexor solo se oirá ruido.
