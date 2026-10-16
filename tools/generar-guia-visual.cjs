const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const root = path.resolve(__dirname, '..');
// rama openwebrxplus-generico: un solo kit, en la raíz del repositorio
const kits = ['.'];
const manualsFor = kit => fs.readdirSync(path.join(root, kit, 'docs', 'manuales')).filter(f => /^\d+.*\.md$/.test(f)).sort();
const modules = [
  {
    id: 'sistema', title: 'Sistema base, red, arranque y HAT',
    steps: 'comprobar,base,red,arranque,hat,banner', manuals: [1, 2], diagram: '01_arquitectura',
    purpose: 'Preparar Raspberry Pi OS, conectividad, buses y reloj/GPS del HAT. El banner resume el estado al entrar por SSH.',
    before: 'Pi 5 con Raspberry Pi OS Lite arm64 Bookworm o Trixie, fuente adecuada, Ethernet de rescate y hardware apagado durante el cableado. Revisa HOSTNAME_NEW, WIFI_*, HAT_* y coordenadas propias.',
    after: 'La Pi conserva acceso SSH, fecha correcta y dispositivos previstos. Los cambios de arranque pueden requerir reinicio: no lo hagas hasta revisar el registro y disponer de acceso local.',
    check: 'uname -m\ncat /etc/os-release\nip -brief address\ntimedatectl\nsystemctl status gpsd chrony bricohams-hat-power --no-pager',
    trouble: 'Sin red: usa consola local o Ethernet y revisa NetworkManager antes de repetir red. Sin GPS/RTC: comprueba pines y alimentación con la Pi apagada. No cambies cableado energizado.',
  },
  {
    id: 'receptor', title: 'OpenWebRX+, RTL-SDR y SDRplay',
    steps: 'openwebrx,rtlsdr,sdrplay,configuracion', manuals: [3, 8, 33], diagram: '01_arquitectura',
    purpose: 'Instalar el receptor web, drivers y perfiles de radio. El backend puede ser nativo o Docker; los demás módulos siguen en el host.',
    before: 'Completa sistema base. Revisa SERIAL_*, OWRX_BACKEND y los permisos USB. El FlightStick ADS-B no debe estar asignado también a OpenWebRX+. SDRplay requiere hardware y API compatibles; no actives HF_SDRPLAY sin ellos.',
    after: 'El receptor abre, permite seleccionar el SDR correcto y reproduce audio. En Docker usa el nombre configurado en OWRX_DOCKER_CONTAINER: no se espera openwebrx.service.',
    check: 'lsusb\nsystemctl status openwebrx --no-pager\n# Solo para backend Docker, en vez del servicio nativo:\ndocker ps --format "table {{.Names}}\\t{{.Status}}"',
    trouble: 'USB ocupado: verifica series y procesos antes de reiniciar. Sin audio: revisa volumen, modo y permisos del navegador (manual 30). No grabes series EEPROM a ciegas; manual 03.',
  },
  {
    id: 'plugins', title: 'Plugins, registro de oyentes, CTCSS y RepeaterBook',
    steps: 'plugins,web', manuals: [27, 30, 39, 41], diagram: '20_audio_navegador',
    purpose: 'Añadir controles de audio/DSP, fichas de indicativos, registro voluntario de oyentes, identificación obligatoria (callsign_gate de EA5HKX), detector CTCSS (servidor y navegador), marcadores, importación/exportación y repetidores por zona. Son extensiones del receptor, no servicios de radio independientes.',
    before: 'OpenWebRX+ y configuración funcionales. Para paneles administrativos completa también web. Guarda bookmarks antes de importar; la clave de RepeaterBook se introduce en General Settings, no en una captura.',
    after: 'Los controles del receptor aparecen tras recargar. En /settings están las herramientas de bookmarks y repetidores. Guarda frecuencia de salida del repetidor y subtono; el SDR no transmite.',
    check: 'systemctl status openwebrx --no-pager\n# Docker: consulta el contenedor configurado, como en la ficha receptor.',
    trouble: 'Si no aparecen controles, recarga sin caché y revisa la consola del navegador. Si faltan fichas, revisa API y proveedor externo. Si el instalador avisa de que no pudo verificar un plugin de EA5HKX, queda desactivado: revisa el acceso a gitlab.com (manual 41). No publiques logs completos de autenticación.',
  },
  {
    id: 'zona', title: 'Locator, canales y marcadores de la zona',
    steps: 'configuracion,meteo', helpers: ['zona_locator'], manuals: [32], diagram: '22_zona_locator',
    purpose: 'Derivar ubicación, emisoras, aeropuertos, NAVTEX y estaciones meteorológicas a partir del locator o coordenadas.',
    before: 'Usa tu STATION_LOCATOR y catálogo adecuado. Las coordenadas explícitas tienen prioridad. LOCATOR_ONLINE necesita Internet y AEMET necesita su clave. Revisa datos antes de emitir APRS.',
    after: 'Los marcadores corresponden a tu región y METEO_STATIONS refleja la selección configurada. No se garantiza cobertura mundial del catálogo español.',
    check: 'systemctl status bricohams-meteo.timer --no-pager\njournalctl -u bricohams-meteo.service -n 30 --no-pager',
    trouble: 'Zona equivocada: revisa coordenadas explícitas, locator, radio y catálogo. Sin datos online: comprueba DNS y credenciales sin copiarlas a un informe público.',
  },
  {
    id: 'mesh', title: 'Meshtastic HAT y LilyGO; puente al mapa',
    steps: 'meshtastic,lilygo', manuals: [5, 35], diagram: '25_lora_owrx',
    purpose: 'Configurar nodos 868/433 MHz, MQTT interno y posiciones/mensajes en OpenWebRX+. El firmware y frecuencia de cada radio deben coincidir con el hardware.',
    before: 'Completa HAT, receptor y web. Identifica cada USB; conecta antena apropiada antes de transmitir. Revisa región regulatoria, canales y PSK en privado. No compartas QR de canales privados.',
    after: 'Los nodos aparecen en el panel administrativo y sus mensajes/posiciones llegan al mapa cuando se reciben. Sin tráfico RF no hay datos nuevos que mostrar.',
    check: 'systemctl status meshtasticd mosquitto bricohams-mesh-owrx --no-pager\njournalctl -u bricohams-mesh-owrx -n 30 --no-pager',
    trouble: 'Sin radio: revisa pines, banda y firmware. Sin mapa: revisa MQTT y que el nodo emita posición. Grabar firmware es un procedimiento separado del instalador; sigue manual 05.',
  },
  {
    id: 'rak', title: 'RAK4631, APRS y GPS',
    steps: 'rak', manuals: [6, 35], diagram: '25_lora_owrx',
    purpose: 'Integrar el RAK por USB, posiciones, chat APRS y sensores disponibles. RF y APRS-IS no equivalen al chat de Meshtastic.',
    before: 'Identifica el puerto del RAK, carga el firmware indicado y usa indicativo/passcode propios. Comprueba RAK_TX y bandas; mantener recepción no autoriza transmisión.',
    after: 'El servicio recibe tramas y el mapa presenta posiciones válidas. Una trayectoria necesita al menos dos posiciones distintas recibidas desde la apertura del mapa.',
    check: 'systemctl status bricohams-rak-aprs --no-pager\njournalctl -u bricohams-rak-aprs -n 30 --no-pager',
    trouble: 'Sin GPS: espera cielo abierto y revisa antena/firmware. Sin tramas: revisa dispositivo USB y permisos. No actives transmisión como forma de diagnosticar recepción.',
  },
  {
    id: 'adsb', title: 'ADS-B local, RadarBox y map.flights simultáneos',
    steps: 'adsb,ais', helpers: ['mapflights'], manuals: [4, 14, 36, 38, 40], diagram: '10_adsb_gp',
    purpose: 'readsb decodifica un receptor 1090 MHz y distribuye sus datos a RadarBox y, opcionalmente, map.flights. Con un SDR propio de 162 MHz, AIS-catcher añade barcos locales al mapa (AIS_ENABLE). El mapa local y el envío externo son verificaciones distintas.',
    before: 'Receptor/antena 1090 MHz y serie correcta; ADSB_ENABLE=yes. Para añadir map.flights usa MAPFLIGHTS_FEED=yes y el UUID propio en MAPFLIGHTS_UUID. Conserva RADARBOX_KEY; no uses mf_feed_ como UUID. Protege configuración y logs.',
    after: 'readsb y rbfeeder activos; si habilitas MLAT de map.flights, su servicio conecta con su servidor. Confirma recepción en ambos portales, no solo un proceso activo. Reiniciar readsb puede interrumpir brevemente el flujo, sin sustituir RadarBox.',
    check: 'systemctl status readsb rbfeeder --no-pager\n# Solo con AIS_ENABLE=yes:\nsystemctl status bricohams-ais --no-pager\n# Solo si habilitaste MAPFLIGHTS_MLAT:\nsystemctl status bricohams-mapflights-mlat --no-pager\nss -tn | grep -E ":(30004|31090)\\b"\n# Revisar localmente; el journal puede contener el UUID:\njournalctl -u bricohams-mapflights-mlat -n 20 --no-pager',
    trouble: 'Sin posiciones: comprueba antena, serie y recepción local antes de culpar al feed. Sin MLAT: mismo UUID para Beast y MLAT; destino mlat.map.flights:31090. Una conexión TCP no prueba aceptación de datos. Fotos: activa ADS-B local y pulsa un avión; dependen de datos externos.',
  },
  {
    id: 'wx', title: 'Meteorología, BME280, viento/lluvia y Pico IO',
    steps: 'meteo,io,sensor,ventilacion', manuals: [6, 18, 19, 20, 22], diagram: '03_cableado_bme280',
    purpose: 'Obtener meteo externa y sensores locales, publicar WX y regular ventiladores. Pico IO separa entradas/pulsos/PWM de la Pi; son fuentes distintas, no lecturas intercambiables.',
    before: 'Cableado sin tensión, pines/voltajes comprobados. Elige IO_MODE y fuente de sensores. Un bus RS485 tiene un solo maestro: no actives simultáneamente Pi y LilyGO WX como maestros. Firmware Pico y LoRa se graban según sus manuales.',
    after: 'Lecturas con unidades plausibles, timestamps actuales y ventilación funcionando. Para APRS valida indicativo y coordenadas reales antes de habilitar publicación.',
    check: 'systemctl status bricohams-meteo.timer bricohams-wx bricohams-fan --no-pager\n# Solo si usas Pico IO:\nsudo bricohams-io estado\nsudo bricohams-fan --estado',
    trouble: 'Sin sensor: revisa dirección I2C, USB, alimentación y modo elegido. Errores lgpio: revisa directorio de trabajo del servicio según manual 06. No fuerces ventilación apagada con electrónica caliente.',
  },
  {
    id: 'camara', title: 'Cámara y MediaMTX',
    steps: 'camara', manuals: [7], diagram: '01_arquitectura',
    purpose: 'Publicar vídeo y capturas de la cámara mediante MediaMTX y la integración web.',
    before: 'Conecta CSI con la Pi apagada. Revisa CAM_SOURCE y modelo soportado, orientación y privacidad del encuadre; no expongas interiores, personas ni credenciales.',
    after: 'Imagen actual en el módulo web y servicios sin reinicios repetidos. RTSP/WebRTC y captura fija tienen rutas/puertos diferentes; manual 07.',
    check: 'systemctl status mediamtx bricohams-camsnap --no-pager\njournalctl -u mediamtx -u bricohams-camsnap -n 30 --no-pager',
    trouble: 'Sin imagen: cable CSI, fuente elegida y detección de cámara. Imagen fija pero sin vídeo: comprueba red y puertos WebRTC sin abrir la API de MediaMTX a Internet.',
  },
  {
    id: 'satelites', title: 'Satélites, Doppler y FT2 experimental',
    steps: 'satelites,ft2', manuals: [26, 28], diagram: '01_arquitectura',
    purpose: 'Calcular pases y facilitar escucha con Doppler; FT2 es integración experimental, no una garantía de decodificación ni función de transmisión.',
    before: 'Hora y ubicación correctas, receptor de satélites disponible y antena adecuada. Consulta limitaciones de FT2 antes de habilitarlo.',
    after: 'Lista de pases coherente y selección de escucha cuando hay receptor disponible. Las efemérides requieren actualización; que no haya pase visible puede ser normal.',
    check: 'systemctl status bricohams-satpass.timer --no-pager\njournalctl -u bricohams-satpass.service -n 30 --no-pager\nsudo bricohams-ft2 estado',
    trouble: 'Pases incorrectos: revisa hora, ubicación y datos orbitales. No recibir un satélite fuera del horizonte no es fallo de instalación.',
  },
  {
    id: 'web', title: 'Portal, HTTPS, API y paneles administrativos',
    steps: 'web', manuals: [23, 27, 40], diagram: '18_red_servicios',
    purpose: 'Publicar receptor y servicios solo por HTTPS (443) mediante nginx, con el 8073 limitado a la propia Pi; políticas, cookies, idioma y logo BricoHams; enriquecer fichas y proteger /settings con la sesión del administrador.',
    before: 'Receptor instalado, SSL_MODO elegido, DNS/dominio propios si usas ACME. Configura claves de proveedores en privado. Conserva acceso SSH antes de cambiar proxy o certificados.',
    after: 'Portal accesible; /settings pide sesión válida. API y servicios internos no quedan públicos directamente. Certificado autofirmado necesita aceptación consciente del navegador.',
    check: 'sudo nginx -t\nsystemctl status nginx bricohams-api bricohams-mesh-admin --no-pager',
    trouble: '502: comprueba el servicio de destino y el journal de nginx. Login en bucle: revisa HTTPS, sesión y reloj. No elimines auth_request para resolver un problema de acceso.',
  },
  {
    id: 'visitas', title: 'Oyentes, Telegram y avisos',
    steps: 'visitas,tareas', manuals: [24, 25], diagram: '18_red_servicios',
    purpose: 'Recoger estadísticas de oyentes y programar avisos/moderación cuando están habilitados.',
    before: 'OpenWebRX+ y MQTT funcionales. Tokens y chat IDs se introducen en configuración privada. Revisa retención y avisos de privacidad antes de publicar estadísticas.',
    after: 'El panel muestra estado y las tareas están programadas. Telegram solo funciona con bot, permisos y chat configurados; no es obligatorio para usar el receptor.',
    check: 'systemctl status bricohams-visitas --no-pager\nsudo -u openwebrx bricohams-visitas --estado',
    trouble: 'Sin avisos: revisa permisos del bot, conectividad y calendario. No pegues URLs de Telegram con token en incidencias ni capturas.',
  },
  {
    id: 'tak', title: 'TAK local y capas privadas',
    steps: 'tak,web', manuals: [36], diagram: '18_red_servicios',
    purpose: 'Instalar OpenTAKServer opcional y acceso administrativo; integrar posiciones privadas en el mapa Leaflet.',
    before: 'TAK=yes, Pi arm64, capacidad de almacenamiento y copia de datos/certificados previos. Configura clientes mediante el panel; no compartas tak-access.txt ni certificados privados.',
    after: 'El panel está disponible con sesión administrativa; la capa TAK solo aparece por HTTPS y no se publica por MQTT.',
    check: 'sudo bricohams-check\n# Ver unidades TAK instaladas, sin asumir un nombre de paquete:\nsystemctl list-units --all --no-pager | grep -i tak',
    trouble: 'Sin capa: revisa HTTPS y sesión vigente. No confundir el mapa público ADS-B/APRS con autorización para ver TAK. Revisa errores del instalador externo antes de dar la instalación por buena.',
  },
  {
    id: 'monitorizacion', title: 'Prometheus, exporters y Grafana',
    steps: 'monitorizacion,web', manuals: [23, 36], diagram: '18_red_servicios',
    purpose: 'Recoger métricas locales y presentar paneles privados; puede adoptar instalaciones manuales existentes.',
    before: 'MONITORIZACION=yes; verifica espacio y copias de configuraciones/datos existentes. Completa web para el acceso autenticado a Grafana.',
    after: 'Grafana accesible bajo /settings/bricohams/grafana/ con sesión administrativa. Prometheus/exporters escuchan localmente. No todos los equipos usan el mismo nombre de unidad del exporter.',
    check: 'systemctl status prometheus grafana-server --no-pager\nsystemctl list-units --all --no-pager | grep -E "node.exporter|openwebrx.exporter"\nss -ltn | grep -E ":(3000|9090|9100)\\b"',
    trouble: 'Panel vacío: comprueba targets y exporter. Fallo de autenticación: revisa proxy/sesión, no abras 3000/9090 a Internet.',
  },
  {
    id: 'seguridad', title: 'Blindaje, bloqueo y copias remotas',
    steps: 'herramientas,web', manuals: [9, 34], diagram: '24_blindaje',
    purpose: 'Instalar herramientas de cortafuegos/bloqueo y copias remotas administradas desde los paneles privados.',
    before: 'Acceso de rescate, backup verificado y conocimiento de tu red. Para SFTP compara huella del servidor antes de confirmar; secretos solo en ficheros protegidos.',
    after: 'Paneles privados y configuración de copias remotas comprobada. Instalar herramientas no equivale a configurar un destino remoto ni a probar su restauración.',
    check: 'sudo bricohams-check\nsudo bricohams-backup-remoto estado\nsystemctl status bricohams-bloqueo-arranque --no-pager',
    trouble: 'Acceso bloqueado: usa consola local y revisa reglas, sin desactivar toda protección indiscriminadamente. Backup remoto fallido: revisa huella/permisos/espacio, no ocultes el error.',
  },
  {
    id: 'mantenimiento', title: 'Tareas, backups, limpieza, actualización y clonado',
    steps: 'herramientas,importar,tareas', manuals: [9, 25, 29, 31], diagram: '19_actualizar',
    purpose: 'Programar mantenimiento, guardar configuración/perfiles, migrar OpenWebRX+ y retirar copias locales antiguas.',
    before: 'Revisa calendario, espacio y destino externo. Importar requiere un perfil existente y validado: --solo importar no aporta un fichero. Actualizar, importar y restaurar son operaciones distintas.',
    after: 'Temporizadores/cron previstos y copias verificables. La limpieza diaria a las 06:15 borra archivos elegibles con más de 120 h por mtime; no garantiza una copia mínima ni toca subdirectorios/restauraciones de despliegue.',
    command: 'sudo bash install.sh --solo herramientas,tareas\n# Importar SOLO un perfil propio, existente y verificado (manual 31):\n# sudo bash install.sh --importar /ruta/perfil.owrx.tar.gz\n# Inspeccionar una actualizacion sin aplicarla:\nsudo bash install.sh --actualizar --simular',
    check: 'sudo bricohams-backup-limpieza --dry-run\nsystemctl list-timers bricohams-backup-limpieza.timer --all\njournalctl -u bricohams-backup-limpieza.service -n 20 --no-pager',
    trouble: 'Antes de limpiar guarda fuera del alcance los archivos que quieras conservar. No hay papelera; parar el timer no recupera archivos. Para deshacer importación usa owrx-clone deshacer según manual 31, no para revertir todo el sistema.',
  },
  {
    id: 'hardware', title: 'Caja, antenas, filtros, alimentación y anclajes',
    steps: '', manuals: [10, 11, 12, 13, 14, 15, 16, 17, 21], diagram: '07_caja_distribucion',
    purpose: 'Construcción mecánica y cadena RF. No existe un paso install.sh que monte o certifique el hardware.',
    before: 'Lee materiales, dimensiones y comprobaciones de cada manual. Desconecta alimentación antes de cablear. Trabajos de red eléctrica y altura requieren personal cualificado, medios de protección y normativa local.',
    after: 'Cableado y fijaciones revisados, puesta a tierra/protección según diseño, estanqueidad y alimentación comprobadas; antenas verificadas con instrumentación antes de izarlas.',
    check: '# No hay comando que sustituya inspeccion electrica, RF o mecanica.\n# Despues del montaje y encendido seguro, si las herramientas estan instaladas:\nsudo bricohams-check',
    trouble: 'No alimentes un LNA o bias-tee sin verificar tensión/corriente y sentido de conexión. No trabajes con 230 V ni en el mástil energizado. Una ilustración no es un plano eléctrico certificado.',
  },
];

const manualExtra = {
  1: 'sistema', 2: 'sistema', 3: 'receptor', 4: 'adsb', 5: 'mesh', 6: 'wx',
  7: 'camara', 8: 'receptor', 9: 'mantenimiento', 18: 'wx', 19: 'wx', 20: 'wx',
  22: 'wx', 23: 'web', 24: 'visitas', 25: 'mantenimiento', 26: 'satelites',
  27: 'plugins', 28: 'satelites', 29: 'mantenimiento', 30: 'plugins',
  31: 'mantenimiento', 32: 'zona', 33: 'receptor', 34: 'seguridad', 35: 'mesh',
  36: 'adsb', 37: 'sistema', 38: 'adsb', 39: 'plugins', 40: 'web',
};
const block = text => `\n\`\`\`bash\n${text}\n\`\`\`\n`;
const unique = values => [...new Set(values)].sort();
const write = (p, content, check) => {
  if (check) assert.equal(fs.readFileSync(p, 'utf8'), content, `Desactualizado: ${p}`);
  else fs.writeFileSync(p, content, 'utf8');
};

function build(kit, check) {
  const dir = path.join(root, kit);
  const installer = fs.readFileSync(path.join(dir, 'install.sh'), 'utf8').replace(/\r/g, '');
  const steps = installer.match(/^PASOS=\(([^)]+)\)/m)[1].split(/\s+/);
  const documented = new Set(modules.flatMap(m => m.steps.split(',')).filter(Boolean));
  for (const step of steps) assert(documented.has(step), `Paso sin documentar: ${step}`);
  for (const step of documented) assert(steps.includes(step), `Paso inexistente: ${step}`);
  const starts = [...installer.matchAll(/^(\w+)\(\) \{\n/gm)];
  const functions = new Map(starts.map((m, i) => {
    const region = installer.slice(m.index + m[0].length, starts[i + 1]?.index ?? installer.length);
    const endings = [...region.matchAll(/^}$/gm)];
    assert(endings.length, `Cierre de funcion ausente: ${m[1]}`);
    return [m[1], region.slice(0, endings.at(-1).index)];
  }));
  for (const step of steps) assert(functions.has(`paso_${step}`), `No se pudo leer paso: ${step}`);
  for (const m of modules) for (const helper of m.helpers || []) assert(functions.has(helper), `Ayudante ausente: ${helper}`);
  assert(functions.get('paso_meshtastic').includes('MESH868_PRIVATE_PSK'), 'Extraccion incompleta de meshtastic');
  assert(functions.get('mapflights').includes('MAPFLIGHTS_UUID'), 'Extraccion incompleta de mapflights');
  assert(functions.get('paso_tareas').includes('CRON_COPIA'), 'Extraccion incompleta de tareas');
  const env = fs.readFileSync(path.join(dir, 'bricohams.env.example'), 'utf8');
  const keys = [...env.matchAll(/^([A-Z][A-Z0-9_]*)=/gm)].map(m => m[1]);
  const manuals = manualsFor(kit);
  const manualLink = n => {
    const f = manuals.find(f => Number(f.slice(0, 2)) === n);
    assert(f, `Manual ${n} ausente`);
    return `[${f.replace(/\.md$/, '')}](manuales/${f})`;
  };
  const diagram = m => {
    const files = fs.readdirSync(path.join(dir, 'docs', 'esquemas'));
    const f = files.find(f => f === `${m.diagram}.svg`) || files.find(f => f === `${m.diagram}.png`);
    assert(f, `Ilustracion ausente: ${m.diagram}`);
    return `esquemas/${f}`;
  };
  let doc = `# Guía visual de instalación y módulos

Guía de entrada para personas sin experiencia con este kit. **No ejecutes todos los
cuadros seguidos**: elige el módulo y comprueba su hardware y sus dependencias.
Los comandos son para la terminal **Bash de la Raspberry**, no PowerShell del PC.
Se ejecutan desde la carpeta del kit que contiene install.sh.

Esta guía complementa, no sustituye, los ${manuals.length} manuales: conserva allí los detalles
de cableado, firmware, formularios y restauración. Cada ficha enlaza su procedimiento.
Los diagramas son ilustraciones de diseño; las dos capturas son recortes reales
de la interfaz. No se presentan maquetas ni salidas inventadas como pruebas.

## 1. Elegir el recorrido

| Situación | Recorrido |
|---|---|
| Tarjeta nueva | Preparación → configuración privada → instalación completa → pruebas |
| Añadir un módulo | Backup y restauración previstos → editar configuración → paso del módulo → verificar |
| Actualizar | Manual 29: simulación → backup verificado → actualización → pruebas |
| Migrar a otra Pi | Manual 31: exportar perfil, verificar, importar; revisar series y hardware del destino |
| Solo consultar | No ejecutar instalador; consultar estado y manual del módulo |

![Ilustración del ciclo seguro de instalación](esquemas/26_procedimiento_seguro.svg)

### Preparar la configuración sin sobrescribir la existente

1. Sigue ${manualLink(1)} para grabar el sistema y obtener el repositorio.
2. Entra en la carpeta del kit **en la Pi**. Si ya existe bricohams.env, edítalo:
   no lo sustituyas por la plantilla.
3. Usa indicativo, ubicación y dispositivos propios; N0CALL y coordenadas de
   muestra no son una configuración apta para transmitir.
${block('pwd\\nls install.sh bricohams.env.example\\n# SOLO si todavia no existe bricohams.env:\\ncp -n bricohams.env.example bricohams.env\\nchmod 600 bricohams.env\\nnano bricohams.env\\nsudo bash install.sh --lista'.replace(/\\n/g, '\n'))}
La plantilla explica las variables. El instalador lee el bricohams.env del kit y
lo copia a /etc/bricohams; no mezcles versiones distintas del fichero. Las claves
se introducen en el editor o panel privado, nunca en comandos compartidos.

### Backup, comprobación y restauración antes de cambiar una estación

En una instalación existente crea una copia externa/imagen de tarjeta y conserva
las configuraciones y datos de todos los servicios afectados. La copia habitual
de configuración **no es una imagen completa**: revisa también volúmenes Docker,
bases de datos TAK/Grafana y archivos externos al kit si los vas a modificar.
Documenta destino, fecha, alcance y procedimiento de restauración. Detalles:
${manualLink(9)} y ${manualLink(31)}.

| Acción | Comando o procedimiento |
|---|---|
| Crear copia habitual, si la herramienta ya está instalada | \`sudo bricohams-backup\` |
| Comprobar integridad del archivo elegido | Cuadro siguiente; usa la ruta real, no el ejemplo |
| Probar restauración | En tarjeta/equipo de repuesto; manual 09 (configuración) o 31 (perfil) |
| Si no hay herramienta previa | Imagen externa y copia de archivos/datos afectados; no instalar encima para obtener el primer backup |
| Si falla copia o comprobación | **Detenerse: no instalar ni desplegar** |

${block('# Sustituye la ruta por TU archivo ya creado; no imprime su contenido.\\ncopia=/ruta/backup.tar.gz\\nsudo gzip -t "$copia" && sudo tar -tzf "$copia" >/dev/null && sudo sha256sum "$copia"'.replace(/\\n/g, '\n'))}
Registra el SHA-256 fuera del destino y compáralo tras transferir la copia.
gzip/tar comprueban legibilidad, no que el alcance esté completo ni que una
aplicación pueda restaurarse: prueba la restauración y detén los servicios que
necesiten una copia consistente. No publiques archivos que contengan usuarios,
tokens, certificados o coordenadas. No extraigas un tar desconocido sobre /.

### Instalar, comprobar y volver atrás

${block('# Instalacion COMPLETA: solo tras revisar todos los perifericos y opciones.\\nsudo bash install.sh\\n# Despues, si se instalo el paso herramientas:\\nsudo bricohams-check'.replace(/\\n/g, '\n'))}
Para añadir un módulo utiliza su cuadro de instalación. **--solo no resuelve
automáticamente dependencias omitidas**. En una Pi limpia sigue primero el manual 02.
Un servicio omitido por una opción desactivada no es un éxito funcional.
Si falla algo, conserva el registro, corrige la causa y repite solo lo necesario.
Deshacer cambios exige el backup correspondiente, la configuración anterior y
el procedimiento del módulo; repetir el instalador no revierte versiones de paquetes.

## 2. Capturas reales anonimizadas: cómo usar el mapa

Abre /map desde el portal del receptor. Los archivos publicados excluyen por recorte
la barra del navegador, cabecera, indicativo, localidad, coordenadas, nodos,
aviones y teselas del mapa; no se ocultan datos mediante un rectángulo reversible.
No muestran credenciales ni QR. La captura no prueba recepción RF ni conexión
a proveedores: para eso están las comprobaciones de la ficha ADS-B.

![Captura real recortada: activar ADS-B local y trayectorias APRS](capturas/mapa-capas.png)

1. Marca **ADS-B local (readsb)** para ver aviones de tu receptor.
2. Pulsa un avión para abrir su ficha. Fotos, matrícula/modelo y ruta requieren
   datos del proveedor; pueden faltar sin que falle la recepción.
3. Las trayectorias APRS se acumulan desde la apertura: dos posiciones distintas
   como mínimo, hasta dos horas; al recargar se pierde ese historial.

![Captura real recortada: selector cartográfico y capas adicionales](capturas/mapa-herramientas.png)

4. Elige cartografía en **Map**. OpenWeatherMap necesita su clave configurada;
   una capa marcada no asegura que el proveedor esté respondiendo.
5. No confundas la capa de aviones locales con el portal RadarBox/map.flights.
   El envío simultáneo se configura y comprueba como sigue:

![Ilustración del envío paralelo ADS-B y MLAT independiente](esquemas/27_adsb_destinos.svg)

El MLAT de map.flights no reinyecta resultados en readsb. No elimines el feed ni
la configuración de RadarBox para añadir el segundo destino.

## 3. Índice de módulos y cobertura del instalador

| Módulo | Pasos reales de install.sh | Ficha |
|---|---|---|
`;
  for (const m of modules) doc += `| ${m.title} | ${m.steps ? m.steps.split(',').map(s => `\`${s}\``).join(', ') : 'Montaje manual, sin paso software'} | [Abrir](#${m.id}) |\n`;
  doc += `\nLos **${steps.length} pasos** del instalador quedan cubiertos. Los submódulos de
bookmarks/CTCSS, RepeaterBook, locator, Docker, DSP y seguridad tienen además
referencia técnica en [COMPONENTES](COMPONENTES.md). Para puertos, archivos de
configuración y pruebas de regresión consulta ese catálogo; para decisiones,
[ARQUITECTURA](ARQUITECTURA.md). No abras todos los puertos del catálogo al exterior.
\n## 4. Fichas de módulos\n`;
  for (const m of modules) {
    const source = [...m.steps.split(',').filter(Boolean).map(s => `paso_${s}`), ...(m.helpers || [])]
      .map(s => functions.get(s)).join('\n');
    const usedKeys = keys.filter(k => new RegExp(`\\$\\{?${k}\\b`).test(source));
    const helperNames = unique([...source.matchAll(/\$FILES\/bin\/([a-zA-Z0-9_.-]+)/g)].map(x => x[1]))
      .filter(f => fs.existsSync(path.join(dir, 'files', 'bin', f)));
    doc += `\n<a id="${m.id}"></a>\n\n### ${m.title}\n\n**Qué hace.** ${m.purpose}\n\n**Antes de empezar.** ${m.before}\n\n![Ilustración de referencia: ${m.title}](${diagram(m)})\n\n**Instalar o aplicar cambios (con backup verificado).**\n`;
    doc += m.steps ? block(m.command || `sudo bash install.sh --solo ${m.steps}`) : '\nNo hay script de instalación para este montaje. Sigue los manuales enlazados.\n';
    doc += `\n**Configuración.** [Plantilla comentada](../bricohams.env.example).
Variables referenciadas por estos pasos y sus ayudantes indicados (inventario estático, sin
valores privados; las herramientas llamadas pueden leer otras variables):\n\n`;
    doc += usedKeys.length ? usedKeys.map(k => `\`${k}\``).join(', ') + '.\n' : 'Consulta los requisitos de la ficha y el manual; no hay variables directas adicionales identificadas.\n';
    doc += `\n**Scripts y código.** ${m.steps ? '[Instalador](../install.sh)' : 'Manuales de montaje'}`;
    if (m.helpers) doc += ` (incluye ${m.helpers.map(h => `\`${h}\``).join(', ')})`;
    if (helperNames.length) doc += '; ' + helperNames.map(f => `[${f}](../files/bin/${f})`).join(', ');
    doc += `.\n\n**Comprobar (solo los servicios/opciones habilitados).**\n${block(m.check)}\n**Resultado esperado.** ${m.after}\n\n**Si no funciona.** ${m.trouble}\n\n**Restauración.** Guarda el estado previo indicado al principio y sigue el manual
del módulo. Un estado \`inactive\` en un periférico desactivado es esperable;
\`failed\` exige revisar el journal. No borres configuraciones para hacer que pase
una prueba. Para cambios de hardware vuelve a intervenir sin tensión.\n\n**Procedimiento detallado:** ${m.manuals.map(manualLink).join(' · ')}.\n`;
  }
  doc += `\n## 5. Matriz de todos los manuales

Cada enlace conduce al procedimiento completo con su cuadro de orientación.
Los manuales mecánicos no se convierten artificialmente en módulos instalables.
El manual 37 explica cambios históricos, no añade un paso de instalación.

| Manual | Recorrido visual |
|---|---|
`;
  for (const f of manuals) {
    const n = Number(f.slice(0, 2));
    const m = modules.find(m => m.id === (manualExtra[n] || 'hardware'));
    doc += `| [${f.replace(/\.md$/, '')}](manuales/${f}) | [${m.title}](#${m.id}) |\n`;
    const p = path.join(dir, 'docs', 'manuales', f);
    const text = fs.readFileSync(p, 'utf8').replace(/\r/g, '');
    const nav = `\n<!-- guia-visual:inicio -->\n> **Ruta visual:** [${m.title}](../GUIA_VISUAL_MODULOS.md#${m.id}).\n> Consulta allí requisitos, ilustración, cuadro de instalación, comprobaciones y restauración.\n> Los comandos de este manual se ejecutan en Bash en la Pi; revisa el backup antes de cambiarla.\n<!-- guia-visual:fin -->\n`;
    const without = text.replace(/\n<!-- guia-visual:inicio -->[\s\S]*?<!-- guia-visual:fin -->\n/, '');
    const headingEnd = without.indexOf('\n');
    write(p, without.slice(0, headingEnd + 1) + nav + without.slice(headingEnd + 1), check);
  }
  doc += `\n## 6. Mantener la guía y publicar capturas

Generada con \`node tools/generar-guia-visual.cjs\` desde la raíz del repositorio.
Verificar sin escribir: \`node tools/generar-guia-visual.cjs --check\`.
El generador exige cobertura de todos los pasos y existencia de los diagramas,
manuales, capturas y enlaces locales. No ejecuta ningún comando en la Pi.

Para nuevas capturas: usar cuenta/datos de demostración o recorte sin información
personal **antes de guardar**, revisar visualmente al tamaño original, retirar
metadatos y excluir IP/dominio privado, indicativo, ubicación, UUID, tokens,
claves, canales/QR y usuarios. No publicar fotos de terceros sin derechos.
Los módulos sin captura real disponible usan una ilustración identificada,
no una interfaz ficticia. Las capturas actuales documentan controles del mapa,
no todos los formularios de administración ni estados de servicios.
`;
  write(path.join(dir, 'docs', 'GUIA_VISUAL_MODULOS.md'), doc, check);
}

const check = process.argv.includes('--check');
for (const kit of kits) build(kit, check);
for (const kit of kits) {
  const dir = path.join(root, kit, 'docs');
  const files = ['GUIA_VISUAL_MODULOS.md', ...manualsFor(kit).map(f => path.join('manuales', f))];
  for (const file of files) {
    const text = fs.readFileSync(path.join(dir, file), 'utf8');
    assert.equal((text.match(/^```/gm) || []).length % 2, 0, `Cuadro sin cerrar: ${file}`);
    const linksToCheck = file === 'GUIA_VISUAL_MODULOS.md' ? text :
      text.match(/<!-- guia-visual:inicio -->[\s\S]*?<!-- guia-visual:fin -->/)[0];
    for (const match of linksToCheck.matchAll(/!?\[[^\]]*\]\(([^)]+)\)/g)) {
      const target = match[1].split('#')[0];
      if (target && !/^[a-z]+:/i.test(target)) {
        const absolute = path.resolve(dir, path.dirname(file), target);
        assert(fs.existsSync(absolute), `Enlace roto: ${target}`);
        const anchor = match[1].split('#')[1];
        if (anchor) assert(fs.readFileSync(absolute, 'utf8').includes(`<a id="${anchor}"></a>`), `Ancla rota: ${anchor}`);
      }
    }
    if (file !== 'GUIA_VISUAL_MODULOS.md') continue;
    for (const m of modules) assert(text.includes(`<a id="${m.id}"></a>`));
    assert(!/mf_feed_[a-z0-9]{6}|[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}|192\.168\.254\.105|EA5[K]AO|Lorq[u]/i.test(text), 'Dato privado en guia');
  }
  for (const name of ['mapa-capas.png', 'mapa-herramientas.png']) {
    const png = fs.readFileSync(path.join(dir, 'capturas', name));
    assert.equal(png.subarray(1, 4).toString(), 'PNG');
    let offset = 8;
    while (offset < png.length) {
      const size = png.readUInt32BE(offset);
      const type = png.toString('ascii', offset + 4, offset + 8);
      assert(!['tEXt', 'zTXt', 'iTXt', 'eXIf'].includes(type), `Metadatos en ${name}`);
      offset += size + 12;
    }
    assert.equal(offset, png.length, `PNG truncado: ${name}`);
    assert.equal(png.readUInt32BE(16), 254);
    assert.equal(png.readUInt32BE(20), name === 'mapa-capas.png' ? 41 : 140);
  }
}
console.log(`${check ? 'Verificadas' : 'Generadas'} guias, cobertura de pasos, cuadros y enlaces del kit.`);
