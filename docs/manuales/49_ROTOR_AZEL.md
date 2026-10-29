# 49 · Rotor AZ/EL PortableSatLite: seguimiento automático de los pases grabados

> Fase 1. El rotor es el **PortableSatLite** del repo
> [antenaSatCommrotor](https://github.com/Brico-Hams/antenaSatCommrotor/tree/main/PortableSatLite):
> ESP32 + 2 × TMC2209 + 2 × NEMA17 de 34 mm + reductora planetaria impresa 25:1.
> Prototipo: ni el rotor ni la antena se han construido ni probado con este kit.

## 1. Qué hace
- `bricohams-rotor` (servicio en la Pi) usa **el mismo plan que `bricohams-satrec`**:
  solo sigue los pases que se van a grabar (`SATREC_MIN_EL`, exclusiones, pases omitidos).
- **2 min antes del AOS** lleva la antena al azimut de entrada con elevación 0; durante el pase
  manda az/el verdaderos (SGP4) cada 2 s por la Wi-Fi de casa (`/api/goto_true` del ESP32).
- **METEOR (137 MHz) no se sigue**: la yagi V/U no cubre esa banda; sale por la QFH fija.
- **Aparca** (`ROTOR_PARQUE_AZ/EL`, por defecto 0°/90°) fuera de pase, con racha ≥
  `ROTOR_VIENTO_MAX_KMH` (36 km/h = 10 m/s, el límite del diseño) según `meteo.json`, o si
  `meteo.json` tiene más de 3 h. Vuelve a seguir cuando la racha baja del 80 % del límite.
  Sin módulo meteo (no existe `meteo.json`) no hay aparcado por viento.

## 2. Hardware
- Motores: NEMA17 de **34 mm** (p. ej. 17HS3401) en AZ y EL; uno de 48 mm vale de repuesto o
  en EL si la antena queda desequilibrada. Corriente del TMC2209 al **50–60 %** de la nominal
  (la etapa 2 de ASA no aguanta más).
- La reductora **no se autobloquea**: sin corriente el viento gira la antena.
- RF: yagi V/U del repo → diplexor 2 m/70 cm → **un coaxial** → RTL-SDR «sat».
  LNA en el mástil con **inyector propio**; no uses el bias-tee del dongle (sobrecorriente USB).
- Deja un bucle de coaxial: el azimut va de 0 a 450°.
- El MPU6050 es opcional en una instalación fija nivelada si se fija el norte a mano (paso 3).

## 3. Puesta en marcha del ESP32 (desde su punto de acceso «SatLite-XXXX»)
1. Graba el firmware: `cd PortableSatLite/firmware && pio run -t upload && pio run -t uploadfs`
   (cambia antes `AP_PASS` en `src/config.h`).
2. Conéctate a «SatLite-XXXX» y, desde ese punto de acceso:
   - Wi-Fi de casa: `/api/wifi?ssid=…&pass=…`;
   - norte: `/api/north?deg=<azimut verdadero al que apunta el cero del rotor>` (se guarda);
   - clave para la red de casa (16+ caracteres): `/api/key?key=…`.
     **Desde la Wi-Fi de casa todas las rutas `/api/` exigen esa clave**; sin clave puesta,
     el rotor no acepta órdenes por la red de casa.
3. Pon una IP fija o nombre al ESP32 en el router.

## 4. Pi
```bash
sudo install -m 640 -o root -g openwebrx /dev/stdin /etc/bricohams/rotor.clave   # pega la clave y Ctrl-D
```
En `bricohams.env`:
```bash
ROTOR_ENABLE="yes"
ROTOR_URL="http://<ip-o-nombre-del-esp32>"
```
y repite `sudo bash install.sh --modulo satelites` (o la instalación completa).

## 5. Comprobación
```bash
systemctl status bricohams-rotor --no-pager
journalctl -u bricohams-rotor -n 20    # «aparcado, sin pase», «esperando el AOS de ISS», «siguiendo ISS»…
sudo bricohams-check | grep -i rotor
```
La clave va en el cuerpo del POST: nunca sale en la URL ni en el registro.

## 6. Límites conocidos
- Firmware compilado (PlatformIO, ESP32) pero **sin probar en placa**; motores, finales de
  carrera y RF sin montar.
- Sin lectura de los AS5600: no detecta pasos perdidos. Haz `/api/home` tras cada arranque.
- Un solo receptor de satélites: el rotor sigue el pase que graba satrec, no los demás.
- Rotor portátil: sin tapas para lluvia. Para dejarlo fuera hay que protegerlo.
