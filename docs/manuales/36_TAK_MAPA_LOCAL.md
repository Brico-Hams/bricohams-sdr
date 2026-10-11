# TAK local, mapa ADS-B/APRS y CHAT

## Estacion desplegada

Servidor OpenWebRX+: `192.168.1.105`, Debian 13 ARM64.

- Mapa publico Leaflet: <http://192.168.1.105/map>.
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

Se comprobo un fallo real: readsb buscaba la serie USB `00001090`, que no
estaba conectada. Con autorizacion del operador se selecciono `00000401`;
OpenWebRX+ mantiene `00000001`. No se cambia la EEPROM del receptor.

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

El acceso de red TAK se limita a `192.168.1.0/24`. La CA local no es
confiable para un navegador nuevo hasta importarla voluntariamente:
no se debe desactivar la verificacion TLS como solucion.

Las cuentas se conservan en `/etc/bricohams/tak-access.txt` (root, modo 600).
El usuario administrador es `ea5kao`; el usuario cliente es `ea5kao-tak`.
Las claves no estan en este manual ni en el repositorio. Consultarlas solo
en una terminal administrativa local:

```bash
sudo cat /etc/bricohams/tak-access.txt
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
