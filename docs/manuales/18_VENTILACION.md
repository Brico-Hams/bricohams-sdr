# 18 · Ventilación de la caja: conexión y control

![Esquema](../esquemas/13_ventiladores.png)

**Qué hace:** dos ventiladores de 60 mm, 12 V, PWM de 4 hilos, controlados por la Raspberry según la temperatura de la CPU y la del aire de la caja (sonda DS18B20). El servicio es `bricohams-fan`.

## 1. Por qué así (ADR-23)
- **Carga térmica:** en verano en Mi QTH hay 40 °C de aire y sol directo sobre la caja. Dentro se disipan 16–24 W (Pi 5, 4 SDR, regleta, LilyGO). Sin ventilación forzada el interior pasaría de 60 °C.
- **Flujo:**
  - **entrada abajo a la izquierda** (aire fresco y sombra);
  - **salida arriba a la derecha**, donde el calor se acumula y está la Pi;
  - **las capotas**, con la boca hacia abajo, impiden que entre la lluvia.
- **PWM de 4 hilos y no 3 hilos con transistor:** el ventilador sigue con 12 V fijos y regula él mismo. A baja velocidad es silencioso, gasta poco y no mete ruido de conmutación en el bus de 12 V, cosa que sí oiría un SDR.
- **PWM por hardware en GPIO12/13** (overlay `pwm-2chan`, PWM0 del RP1 a 25 kHz):
  - no carga la CPU y no hace ruido audible;
  - si el overlay falla, el servicio pasa solo a PWM por software (`lgpio`).
- **El 2N7002:**
  - la entrada PWM del ventilador tiene pull-up interno a ~5 V; el MOSFET la tira a masa con seguridad y aísla el GPIO;
  - invierte la señal, y por eso `FAN_PWM_INVERT="yes"`;
  - **sin MOSFET:** el GPIO directo a 3,3 V funciona en casi todos los ventiladores de 4 hilos, con `FAN_PWM_INVERT="no"`.

## 2. Conexión (por cada ventilador)
| Cable del ventilador | Va a | Notas |
|---|---|---|
| Negro · GND | WAGO GND 12 V | **unido a GND de la Pi** (pin 39) |
| Amarillo · +12 V | WAGO +12 V, tras un **fusible de 1 A** | — |
| Verde · TACH | GPIO22 (pin 15) para el ventilador 1 · GPIO5 (pin 29) para el 2 | **pull-up de 10 kΩ a 3,3 V (pin 1) + 1 kΩ en serie**. El tacómetro es colector abierto: así nunca llegan 12 V a la Pi |
| Azul · PWM | drenador del 2N7002 (Q1/Q2) | fuente a GND · puerta ← 1 kΩ ← GPIO12 (pin 32) / GPIO13 (pin 33) · 100 kΩ puerta–fuente |

**DS18B20** (sonda de aire de la caja, colgada en el centro, lejos de la Pi):

| DS18B20 | Va a |
|---|---|
| VDD | 3,3 V (pin 1) |
| GND | pin 9 |
| DQ | GPIO4 (pin 7), con **4,7 kΩ** entre DQ y 3,3 V |

**Montaje en placa:** una placa perforada de 5 × 7 cm con los 2 MOSFET, las resistencias y una tira de pines Dupont. Va en un inserto de la rejilla junto a la Pi.

## 3. Configuración (`bricohams.env` → `/etc/bricohams/fan.env`)
| Variable | Defecto | Qué hace |
|---|---|---|
| `FAN_ENABLE` | yes | activa el servicio y los overlays |
| `FAN_PWM_GPIOS` | 12,13 | entrada, salida |
| `FAN_TACH_GPIOS` | 22,5 | — |
| `FAN_PWM_INVERT` | yes | con 2N7002 |
| `FAN_T_CPU_MIN` / `MAX` | 55 / 75 °C | — |
| `FAN_T_CAJA_MIN` / `MAX` | 35 / 45 °C | — |
| `FAN_DUTY_MIN` | 30 % | por debajo se paran |
| `FAN_HIST` | 3 °C | para que no arranquen y paren cada minuto |
| `FAN_DS18B20_ID` | vacío | el primero que aparezca en `/sys/bus/w1/devices/28-*` |

**La curva:**
- el ciclo es el **mayor** de los dos cálculos (CPU y caja);
- entre MIN y MAX sube en línea recta del 30 al 100 %;
- **al arrancar desde parado** da un golpe al 100 % durante 1,5 s, porque algunos ventiladores no arrancan al 30 %.

**El instalador:**
- añade `dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4` y `dtoverlay=w1-gpio,gpiopin=4` a `/boot/firmware/config.txt`;
- **hay que reiniciar** después.

## 4. Pruebas
```bash
sudo systemctl status bricohams-fan     # activo
sudo bricohams-fan --estado             # CPU, caja, ciclo y rpm de cada ventilador
sudo systemctl stop bricohams-fan
sudo bricohams-fan --forzar 100         # 30 s a tope: deben dar > 2000 rpm
sudo bricohams-fan --forzar 0           # 30 s parados: rpm 0
sudo systemctl start bricohams-fan
ls /sys/bus/w1/devices/                 # debe aparecer 28-xxxxxxxxxxxx
cat /run/bricohams/caja.json
```
**Qué ves en la web:** la tarjeta METEO de OpenWebRX muestra «📦 Caja: 38 °C · ventiladores 45 % · 1800/1750 rpm».

**Alarma:** si el ciclo es ≥ 40 % y un ventilador da < 300 rpm, aparece «⚠ ventilador parado» en la web y en `bricohams-check`.

## 5. Problemas típicos
| Síntoma | Causa | Arreglo |
|---|---|---|
| rpm siempre 0 y el ventilador gira | falta el pull-up del TACH o la masa común | revisa 10 kΩ a 3,3 V y GND del WAGO unido a la Pi |
| giran siempre al 100 % | PWM invertido al revés | cambia `FAN_PWM_INVERT` |
| `pwmchip` no aparece | falta el overlay o no se ha reiniciado | `grep pwm-2chan /boot/firmware/config.txt`; reinicia. El servicio usará PWM por software mientras tanto |
| no hay DS18B20 | falta 4,7 kΩ o el overlay w1-gpio | `dmesg \| grep w1` |
| ruido en HF al subir los ventiladores | los 12 V llevan ruido | ferrita en los cables del ventilador y condensador de 100 µF en el WAGO |
