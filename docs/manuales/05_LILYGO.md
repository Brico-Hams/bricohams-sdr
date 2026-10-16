# 05 · LilyGO T3 V1.6.1 de 433 MHz: nodo Meshtastic e iGate LoRa APRS

<!-- guia-visual:inicio -->
> **Ruta visual:** [Meshtastic HAT y LilyGO; puente al mapa](../GUIA_VISUAL_MODULOS.md#mesh).
> Consulta allí requisitos, ilustración, cuadro de instalación, comprobaciones y restauración.
> Los comandos de este manual se ejecutan en Bash en la Pi; revisa el backup antes de cambiarla.
<!-- guia-visual:fin -->

> **v4.5:**
> - **El iGate pasa a un RAK4631** con firmware propio ([manual 35](35_LORA_APRS_MESHTASTIC.md)). El iGate WiFi de este manual queda como alternativa.
> - El LilyGO es el **nodo Meshtastic 433** con la URL de la red (`MESH433_CHANNEL_URL`) y el nombre *SDR BricoHams 433* / SB43.
> - Nombres fijos: `sudo bricohams-dispositivos identificar`. Actualizar su firmware: `sudo bricohams-lilygo firmware`.

Los dos van por USB (hub alimentado) a la Pi. De ahí sacan la corriente y por ahí se configuran.

## 1. Grabar el firmware de Meshtastic (una vez, desde un PC con Chrome)
1. Abre https://flasher.meshtastic.org y conecta el LilyGO del **nodo Meshtastic** al PC.
2. Elige el dispositivo **LILYGO T3 V1.6.1** (TLORA_V2_1_1P6) y la última versión estable. Pulsa *Flash* con *Full erase*.
3. Pon su antena de 433 MHz y llévalo al hub de la Pi.

> El iGate **no** se graba aquí: lo compila y graba la Pi en el paso 4.

## 2. Nombres fijos (una vez)
```bash
sudo bricohams-lilygo identificar
```
1. Desenchufa los dos LilyGO.
2. Enchufa el de **Meshtastic** cuando te lo pida.
3. Enchufa el del **iGate** cuando te lo pida.

Se crea `/etc/udev/rules.d/99-bricohams-lilygo.rules`, con `/dev/lilygo-mesh` y `/dev/lilygo-igate`. Se identifican por el número de serie del chip USB o, si no tiene (CH340), por el puerto físico.

## 3. Configurar el nodo Meshtastic 433
```bash
sudo bricohams-lilygo meshtastic
```
1. Carga los **canales de la red** (`MESH_CHANNEL_URL`): SFNarrow, Murcia, Cartagena, Test y Alicante.
2. Cambia la radio a **EU_433 LONG_FAST** (el QR trae 868).
3. Pone el nombre `N0CALL BricoHams 433` / `BH43`, el rol `CLIENT` y la posición fija de tu QTH, sin GPS.

Comprueba con `meshtastic --port /dev/lilygo-mesh --info`.

## 4. Compilar y grabar el iGate LoRa APRS (CA2RXU)
```bash
sudo bricohams-lilygo igate
```
1. Instala PlatformIO.
2. Clona `richonguzman/LoRa_APRS_iGate` en `/opt/bricohams/LoRa_APRS_iGate`.
3. Genera `data/igate_conf.json` desde `bricohams.env`:
   - Indicativo **N0CALL-10**.
   - WiFi de `LILYGO_WIFI_SSID`.
   - APRS-IS `euro.aprs2.net:14580` con el código de N0CALL y filtro `m/10`.
   - Baliza solo por APRS-IS, cada 15 min.
   - **Radio:** escucha en 433,775 (SF12, BW 125, CR 4/5), **TX desactivada**, sin digipeater.
4. Graba el firmware (entorno `ttgo-lora32-v21`) y el sistema de archivos con la configuración. La primera vez tarda entre 10 y 15 min.

**Comprobaciones:**
- En la pantalla del LilyGO salen la IP y los paquetes recibidos.
- En https://aprs.fi/#!call=N0CALL-10 aparece el iGate.
- Su web es `http://<IP del iGate>/` (usuario `admin`, contraseña `IGATE_WEB_PASS`).

## Notas de RF
- El nodo Meshtastic **transmite** en 433. Separa su antena al menos 1 m de las de recepción: el receptor de RADIOAFICIONADOS escucha 433 MHz.
- La LilyGO T3S3 que hace ahora de iGate queda libre.
