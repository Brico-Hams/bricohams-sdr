# TAK local, mapa ADS-B/APRS y CHAT

<!-- guia-visual:inicio -->
> **Ruta visual:** [ADS-B local, RadarBox y map.flights simultáneos](../GUIA_VISUAL_MODULOS.md#adsb).
> Consulta allí requisitos, ilustración, cuadro de instalación, comprobaciones y restauración.
> Los comandos de este manual se ejecutan en Bash en la Pi; revisa el backup antes de cambiarla.
<!-- guia-visual:fin -->

## Ejemplo de estación

Servidor OpenWebRX+: Raspberry Pi con Debian ARM64. Sustituye los marcadores
por los valores de tu instalación.

- Mapa publico Leaflet: `http://<IP-DE-LA-PI>/map`.
- ADS-B local: lectura de `/run/readsb/aircraft.json`, cada dos segundos.
- APRS: posiciones recibidas por OpenWebRX+, RF del RAK y APRS-IS del RAK.
- Trayectorias APRS: hasta dos horas **desde la apertura del mapa**,
  1.000 puntos por equipo y 512 equipos. No son un archivo historico:
  desaparecen al recargar/cerrar el mapa. Una sola posicion no permite
  dibujar un recorrido; se necesita recibir una segunda posicion distinta.
- TAK: capa privada solamente en el mapa por **HTTPS**, con sesion
  administrativa de OpenWebRX+ vigente. No se publica por MQTT.
- CHAT comun: mensajes APRS recibidos por RF/APRS-IS. No habilita transmision
  desde el navegador, ni ACK automatico, ni modifica `RAK_TX`.

Las capas nuevas requieren Leaflet, el mapa predeterminado del kit; no se
incorporan al mapa alternativo Google. No se anaden controles de configuracion
a la pagina publica.

## ADS-B, RadarBox y MLAT

readsb puede buscar un identificador USB distinto del conectado. Comprueba los
identificadores disponibles en tu equipo y configura el que corresponda;
OpenWebRX+ mantiene su propia configuración. No se cambia la EEPROM del receptor.

Se conservaron el fichero `/etc/rbfeeder.ini`, los puertos de readsb y los
parametros de MLAT:

```text
readsb:30005 -> rbfeeder (Beast)
rbfeeder:32457 -> mlat-client
mlat-client -> mlat1.rb24.com:40900
mlat-client -> 127.0.0.1:32004 (resultado Beast de RadarBox)
```

El mapa lee las posiciones que contiene readsb; no extrae ni promete
posiciones calculadas por MLAT que no lleguen a ese fichero. No se
reinyectan resultados MLAT en readsb para evitar posibles bucles de alimentacion.
La continuidad de RadarBox se verifico con conexiones TCP establecidas y
su configuracion intacta. Un proceso MLAT activo no garantiza por si solo
resultados de multilateracion: depende de suficientes estaciones correlacionadas.

El endpoint publico `/bricohams/api/aviones` publica solo identificador,
indicativo de vuelo, posicion, hora, altitud, velocidad y rumbo. No sirve
estadisticas, configuracion ni coordenadas del receptor. Devuelve 503 si
readsb no actualiza el fichero en 15 segundos; descarta posiciones de mas
de 60 segundos. Al perder la fuente, el mapa elimina los aviones anteriores
y muestra un aviso, en vez de presentar datos antiguos como actuales.

```bash
systemctl is-active readsb rbfeeder
pgrep -a mlat-client
curl -f http://127.0.0.1:8075/bricohams/api/aviones
sudo journalctl -u readsb -n 30 --no-pager
```

## APRS recibido y CHAT

`OWRX_MAPA_LORA=yes` permite publicar las posiciones LoRa y las posiciones
recibidas en la conexion APRS-IS existente. Se conserva el filtro
`RAK_APRSIS_FILTRO=m/10`: **no representa todos los equipos del mundo**,
sino los paquetes RF recibidos y el conjunto que entrega ese filtro.
El parser de la pasarela maneja posiciones sin comprimir, comprimidas,
con timestamp y objetos; no implementa todas las variantes APRS, como Mic-E.
Los formatos que decodifica directamente OpenWebRX+ siguen usando su parser.

`RAK_OWRX_CHAT=yes` publica texto al topico local `aprs/CLIENT` con
`state=ChatMessage`, remitente y destinatario. Se activa la suscripcion
`mqtt_chat` en OpenWebRX+. Se excluyen acuses `ack/rej` y metadatos
`PARM/UNIT/EQNS/BITS`, y se deduplican mensajes RF/IS durante cinco minutos,
con un maximo de 1.024 entradas. El chat nativo escapa nombre y texto como
HTML; la capa de mapa usa `textContent` para etiquetas recibidas.

Las posiciones de otros equipos se muestran como las reportan, sin aplicarles
el redondeo de privacidad de nuestra estacion. El redondeo del GPS propio
del RAK permanece intacto. No se altera el passcode APRS.

## OpenTAKServer local

Se eligio OpenTAKServer 1.7.13 y UI 1.7.5, sin Docker y sin sustituir nginx
ni OpenWebRX+. El instalador adaptado es `tools/instalar_tak.sh`:

```bash
sudo bash tools/instalar_tak.sh
```

No se ejecuto el instalador upstream que elimina los sitios nginx.
Se aislo Python 3.12.15 para evitar el fallo gevent/fork observado con
Python 3.13. PostgreSQL usa autenticacion Unix peer; RabbitMQ se limita
a local; los servicios llevan usuario dedicado y limites de recursos.

| Puerto | Uso |
|---|---|
| 8445 HTTPS | Interfaz TAK y administracion propia de TAK |
| 8089 mTLS | Clientes ATAK/iTAK/WinTAK |
| 8446 HTTPS | Enrollment |
| 8447 mTLS | Marti/API |
| 8081 loopback | Backend interno |
| 8443 | Se conserva para Meshtastic, no se reasigna a TAK |

El acceso de red TAK se limita a `<SUBRED-LAN-CONFIGURADA>`. La CA local no es
confiable para un navegador nuevo hasta importarla voluntariamente:
no se debe desactivar la verificacion TLS como solucion.

### Credenciales TAK (no hay clave por defecto)

`tools/instalar_tak.sh` crea **dos** cuentas en OpenTAKServer:

| Cuenta | Variable `.env` | Valor por defecto | Rol |
|---|---|---|---|
| Administrador | `TAK_ADMIN_USER` | `admin` | `administrator` |
| Cliente ATAK/iTAK | `TAK_USER` | `tak` | `user` |

(Los nombres de usuario si tienen valor por defecto y pueden cambiarse en el
entorno al instalar, p.ej. `TAK_ADMIN_USER=ea5xxx TAK_USER=ea5xxx_tak`.)

> **Importante:** OpenTAKServer solo acepta nombres de usuario con letras,
> numeros, `_` y `.`. Un **guion** (`ea5xxx-tak`) hace que el login devuelva
> HTTP 400 aunque la clave sea correcta. `instalar_tak.sh` rechaza esos nombres.
> Si heredas una cuenta con guion, crea una nueva con `_` (no se puede renombrar
> en la BD: la tabla `certificates` referencia el nombre) y desactiva la antigua.

### Reset completo de claves

Para regenerar todas las claves (p.ej. si se han filtrado):

1. Copia de seguridad de `/etc/bricohams/tak-access.txt`.
2. Para cada usuario: nueva clave aleatoria, `hash_password`, `active=True`,
   `confirmed_at` y nuevo `fs_uniquifier` (cierra las sesiones abiertas).
3. Reescribe el fichero (root, 600) y comprueba `POST /api/login` → 200.

Desde el panel (`/settings` → Servidor TAK → Credenciales) se hace lo mismo
cuenta a cuenta con «Cambiar clave». Tras el reset, actualiza los clientes
ATAK/iTAK con la nueva clave.

**Las claves NO tienen valor por defecto**: se generan aleatoriamente en la
instalacion (`secrets.token_urlsafe(24)`, ~32 caracteres) y solo se guardan en
`/etc/bricohams/tak-access.txt` (root, modo 600), una linea `usuario: clave`
por cuenta; la primera linea es el administrador. No estan en este manual ni
en el repositorio.

**Consultarlas** (requiere sesion de administrador de OpenWebRX+):

1. `https://<ip>/settings` → **Servidor TAK** → tarjeta **Credenciales TAK**.
   Por defecto muestra usuarios, rol y claves enmascaradas (`••••`).
2. Pulsar **Mostrar credenciales** (POST con token CSRF): la respuesta,
   marcada `Cache-Control: no-store`, muestra las claves en claro.
3. Alternativa en terminal local: `sudo cat /etc/bricohams/tak-access.txt`.

**Cambiarlas** desde la misma tarjeta: elegir usuario, escribir una clave
nueva (12–128 caracteres ASCII visibles, sin espacios) o marcar *Generar
aleatoria*, y pulsar **Cambiar clave**. El panel:

- solo admite usuarios presentes en `tak-access.txt` (lista blanca);
- ejecuta `runuser -u opentakserver` con el Python de OpenTAKServer y pasa la
  clave por **stdin** (nunca en la linea de comandos ni en el log);
- si OpenTAKServer confirma el cambio, reescribe `tak-access.txt` de forma
  atomica (modo 600); si el usuario no existe (codigo 3) no toca el fichero.

El servicio `bricohams-mesh-admin` corre con `ProtectSystem=strict`; para que
OpenTAKServer pueda escribir su log y BD durante el cambio, la unidad incluye
`ReadWritePaths=-/var/lib/bricohams-tak` (el `-` lo hace opcional si TAK no
esta instalado). `instalar_tak.sh` ejecuta `systemctl try-restart
bricohams-mesh-admin` al terminar para que el montaje tome efecto.

Comprobar servicios:

```bash
systemctl is-active bricohams-tak bricohams-tak-cot bricohams-tak-ssl
```

La CA publica esta en `/etc/bricohams/tak-tls/ca.pem`. Para incorporar un
cliente, descargar su paquete de datos desde la interfaz autenticada TAK;
no compartir la clave privada de la CA ni los paquetes personales.

La capa privada consulta `/settings/bricohams/tak/posiciones`, validando
la sesion OpenWebRX+ en **cada peticion**, sin cache positiva de autenticacion.
Consulta PostgreSQL local bajo la identidad `opentakserver`, con transaccion
de solo lectura y timeout. Devuelve solo la ultima posicion de cada dispositivo
cuya informacion CoT no haya caducado. Los no administradores reciben 401
y el navegador elimina la capa al perder acceso; los errores reales dan 503.
En HTTP no se intenta consultar la capa privada, porque la cookie administrativa
usa HTTPS. Refresco privado: diez segundos.

El cortafuegos TAK no sustituye el blindaje general. Si se vuelve a aplicar
un cortafuegos global de denegacion, su lista LAN debe incluir
`8089 8445 8446 8447`, ademas de los puertos existentes de Meshtastic/camara.
El instalador TAK incorpora esos puertos en `BLINDAJE_PUERTOS_LAN` de esta
estacion, sin cambiar los valores por defecto de los kits que no instalan TAK.

## Monitorizacion: Prometheus, node-exporter y Grafana

Se activa con `MONITORIZACION="yes"` en el `.env` y lo aplica el paso
`monitorizacion` de `install.sh`:

```bash
sudo bash install.sh --solo monitorizacion,web
```

Que hace, en orden:

1. **Paquetes.** Si `prometheus`, `prometheus-node-exporter` o `grafana`
   no existen, los instala por apt (Grafana desde su repositorio oficial).
   Si ya hay una **instalacion manual** (binarios en `/usr/local/bin`,
   unidades propias `prometheus.service` / `node_exporter.service`), la
   **adopta**: no reinstala ni borra nada.
2. **Solo loopback.** Crea *drop-ins* `/etc/systemd/system/<unidad>.service.d/bricohams.conf`
   que sustituyen el `ExecStart=` para escuchar en `127.0.0.1:9090`
   (Prometheus) y `127.0.0.1:9100` (node-exporter). Nunca `0.0.0.0`.
3. **prometheus.yml fusionado.** Garantiza los trabajos `prometheus`
   (127.0.0.1:9090) y `node` (127.0.0.1:9100) y **conserva** cualquier
   trabajo extra que el operador hubiera anadido a mano (por ejemplo un
   `openwebrx_exporter` propio). Si existe la unidad `openwebrx_exporter`,
   un drop-in con `IPAddressDeny=any` / `IPAddressAllow=localhost` le
   impide hablar con nadie que no sea la propia Pi. La
   fusion es idempotente: ejecutarla dos veces no cambia el fichero.
   Copia previa en `prometheus.yml.bak-manual` la primera vez.
4. **grafana.ini.** Fija `http_addr = 127.0.0.1`, `http_port = 3000`,
   `root_url = %(protocol)s://%(domain)s/settings/bricohams/grafana/` y
   `serve_from_sub_path = true`. Permisos `640` (root:grafana).
5. **Contrasena de admin**, por prioridad:
   `GRAFANA_ADMIN_PASS` del `.env` > la guardada en
   `/etc/bricohams/grafana-access.txt` > una aleatoria nueva (16-20
   caracteres alfanumericos). Se aplica con
   `grafana cli admin reset-admin-password` (por stdin cuando la version
   lo admite) y se guarda en `grafana-access.txt` (root, `600`).
   Para mantener una clave concreta (p. ej. la de una instalacion manual
   previa) basta con ponerla en `GRAFANA_ADMIN_PASS`. El `grafana.ini`
   original se guarda una vez como `grafana.ini.bak-manual`. Grafana
   permite ademas consulta anonima con rol *Viewer*, pero solo es alcanzable
   tras el login de `/settings`.
6. **Panel y nginx.** Importa el panel `files/grafana/bricohams.json`
   (fuente de datos Prometheus) y activa en nginx las lineas `#@GF@` de
   `bricohams-sdr-rutas.conf`: `/settings/bricohams/grafana/` pasa antes
   por `auth_request` (sesion de administrador de OpenWebRX+) y solo
   entonces se reenvia a `127.0.0.1:3000`. Con `MONITORIZACION="no"`
   esas lineas quedan comentadas y Grafana no es accesible.

Rotar la contrasena:

```bash
sudoedit /etc/bricohams/bricohams.env     # GRAFANA_ADMIN_PASS="nueva-clave"
sudo bash install.sh --solo monitorizacion
```

Comprobar:

```bash
systemctl status prometheus node_exporter grafana-server   # o prometheus-node-exporter
ss -ltnp | grep -E ':(3000|9090|9100) '                    # todo en 127.0.0.1
curl -s 127.0.0.1:9090/api/v1/targets | grep -o '"health":"[a-z]*"'
```

Acceso: `/settings` > boton **Monitorizacion** > **Abrir Grafana**.
Nada de esto aparece en la pagina publica.

Prueba: `tests/test_monitorizacion.py` (fusion del YAML, prioridad de la
contrasena, drop-ins en loopback y orden `auth_request` en nginx).

## Despliegue y verificacion

Para actualizar estos componentes nativos desde el kit, sin reinstalar
RadarBox ni modificar MLAT:

```bash
sudo bash tools/activar_mapa_local.sh 00000401
```

El argumento es la serie elegida por el operador; si se omite, se lee
`SERIAL_ADSB` del kit. Se conservan copias root-only bajo
`/var/backups/bricohams-mapa-FECHA`. Se actualizan el kit y su copia de ENV,
los plugins y binarios; se reinician los servicios necesarios, incluyendo
OpenWebRX+, lo que interrumpe brevemente las sesiones de escucha.

Si el navegador conserva el plugin anterior, recargar con **Ctrl+F5**.

Pruebas Linux:

```bash
python3 tests/test_live_map.py
python3 tests/test_api.py
python3 tests/test_rak_aprs.py
python3 tests/test_mesh_admin.py
```

El test RAK usa puertos/firmware simulados: los mensajes de DFU que imprime
son una prueba del manejo de errores, no un nuevo flasheo del RAK real.
Se verificaron aviones reales en readsb y su marcador en Leaflet,
trayectorias/deduplicacion/orden temporal con posiciones sinteticas solo
en el navegador, y continuidad de RadarBox/MLAT. No se emitieron paquetes
de prueba por RF ni hacia APRS-IS.
Se comprobo tambien la recepcion de un mensaje de prueba por MQTT en el
chat publico, una unica vez, y el escape de HTML en el navegador.
TAK rechazo la conexion CoT sin certificado y acepto un cliente con
certificado valido; su evento `PRUEBA-TAK-LOCAL` llego a PostgreSQL y a la
consulta privada. La posicion de prueba caduca al cabo de 60 segundos.
El plugin desplegado se ejercito ademas en un contexto de prueba del navegador:
se verificaron los limites exactos de 1.000 puntos y 512 equipos, las etiquetas
sin HTML ejecutable y la eliminacion de la capa TAK al recibir 401.

Para copias TAK, conservar PostgreSQL (`pg_dump bricohams_tak`), datos/config/CA
en `/var/lib/bricohams-tak`, certificados nginx y configuraciones de servicios.
Guardar esas copias cifradas: incluyen claves privadas y credenciales.
