# 47 · Configuración guiada de módulos y credenciales

Edición 2026-10-22. La ayuda está **dentro de cada panel**, en el botón
«Configuración paso a paso y enlaces directos de los módulos». Se abre con
`?ayuda=1`, requiere la misma sesión de administrador y no publica secretos.
No instala servicios opcionales ni cambia configuraciones al abrirla.

## 1. URLs directas

Sustituye `https://TU_DOMINIO` por el origen HTTPS real, sin barra final.
Los enlaces relativos de la ayuda web utilizan automáticamente el mismo dominio.

| Configuración | URL relativa al dominio |
|---|---|
| Todos los módulos, pasos y enlaces | `/settings/bricohams/seguridad?ayuda=1#modulos` |
| Ayuda Google | `/settings/bricohams/seguridad?ayuda=1#google` |
| Método de acceso Google/local | `/settings/bricohams/seguridad#acceso` |
| Compatibilidad Entra ID | `/settings/bricohams/seguridad?ayuda=1#entra` |
| Ayuda backup y tokens | `/settings/bricohams/seguridad?ayuda=1#backup-remoto` |
| Formulario backup remoto | `/settings/bricohams/seguridad#backup-remoto` |
| Meshtastic 433/868 | `/settings/bricohams/meshtastic` |
| Mensajes Meshtastic | `/settings/bricohams/meshtastic/chat` |
| LoRa APRS RAK | `/settings/bricohams/aprs` |
| TAK | `/settings/bricohams/tak` |
| Monitorización/Grafana | `/settings/bricohams/monitorizacion` |
| map.flights | `/settings/bricohams/mapflights` |
| Satélites y agendas | `/settings/bricohams/satelites` |
| Meteorología | `/settings/bricohams/clima` |
| Configuración nativa OpenWebRX+ | `/settings` |

No todos los componentes tienen un formulario propio. Los ajustes de hardware,
instalación, red, cámara, feeds y servicios siguen gestionándose mediante el
kit/env y los asistentes documentados; no se inventan rutas web para ellos.

## 2. Google: crear ID y secreto para el acceso web

1. Conserva un administrador local activo y una sesión SSH de recuperación.
2. En [Google Cloud Console](https://console.cloud.google.com/) crea/elige proyecto.
3. Configura [Branding](https://console.cloud.google.com/auth/branding) y
   [Audience](https://console.cloud.google.com/auth/audience). Añade usuarios de
   prueba cuando la aplicación externa esté en pruebas.
4. En [Clients](https://console.cloud.google.com/auth/clients) crea una
   **Aplicación web**. También puedes llegar desde
   [Credenciales](https://console.cloud.google.com/apis/credentials).
5. Origen: `https://TU_DOMINIO`. Redirección:
   `https://TU_DOMINIO/_bh_google/callback`, exactamente.
6. Copia el ID de cliente y el **valor del secreto** a la tarjeta de acceso,
   no a un `.env`, Git, chat o línea de comandos. No sirven una API key ni
   el JSON de token de Drive.
7. Añade correos administradores y selecciona «Usuario local o cuenta de Google».
   Autorizar `@dominio` permite a todo ese dominio: úsalo conscientemente.
8. Guarda y aplica; prueba desde una ventana privada, conservando la sesión de
   recuperación. Comprueba también el rechazo de una cuenta no autorizada.
9. Solo tras una prueba correcta considera exigir Google.

`redirect_uri_mismatch`: dominio, HTTPS y ruta deben coincidir. Un secreto perdido
se sustituye por uno nuevo; verifica antes de revocar el anterior.
Más detalles y recuperación: [manual 46](46_ACCESO_GOOGLE.md).

## 3. Entra ID: distinguir acceso web y OneDrive

**El inicio de sesión web con Microsoft Entra ID no está implementado.**
No hay callback Entra ni validación de sus emisores en esta versión. No se puede
activar pegando credenciales Microsoft en los campos Google.

Para localizar credenciales de una aplicación Microsoft existente:

1. Abre [Entra](https://entra.microsoft.com/).
2. Identidad → Aplicaciones → Registros de aplicaciones → aplicación.
3. Información general muestra **Application (client) ID** y **Directory (tenant) ID**.
4. Certificados y secretos → Nuevo secreto de cliente → descripción y caducidad.
5. Guarda el **Valor**, no el «Id. del secreto», en un almacén seguro; el valor
   deja de mostrarse. Registra la caducidad y planifica rotación.

No registres permisos ni callbacks para un login aún no disponible.
Para backup OneDrive sí existe integración, descrita a continuación.
[Referencia oficial de registro](https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app).

## 4. Generar token Google Drive

1. En un PC de confianza con navegador instala [rclone](https://rclone.org/downloads/).
   Comprueba `rclone version` en PC y servidor para evitar incompatibilidades.
2. Crea preferentemente un cliente OAuth propio: habilita
   [Drive API](https://console.cloud.google.com/apis/library/drive.googleapis.com),
   configura Branding/Audience y crea un cliente de **Aplicación de escritorio**.
   **No es el cliente web del acceso Google.**
3. Sigue [la guía oficial](https://rclone.org/drive/#making-your-own-client-id).
   El cliente compartido se está retirando; no dependas de que funcione en todas
   las versiones/cuentas durante 2026.
4. Ejecuta `rclone config`. Crea un remoto `bhbackup`, tipo `drive`.
5. Introduce ID y secreto en los prompts interactivos, no como argumentos que
   puedan quedar en historial. Selecciona alcance de escritura adecuado para una
   carpeta dedicada y autoriza en el navegador.
6. Ejecuta `rclone config file`. Abre ese fichero **privado** con un editor local.
   De `[bhbackup]` copia el JSON completo de `token = {...}`, sin `token =`.
   No copies el JSON descargado del cliente OAuth.
7. En Backup remoto elige Google Drive; pega el token y, si creaste cliente propio,
   el mismo ID y secreto en **los campos OAuth del backup**.
8. Indica carpeta y retención. Guarda → Probar conexión → Copiar ahora →
   Verificar última copia. Habilita programación solo tras comprobarlo.

`rclone authorize "drive"` es una alternativa solo si ambos extremos usan el mismo
cliente compartido. El token generado con un cliente propio **necesita** ese cliente
para renovarse. Un cliente externo en pruebas puede tener refresh tokens de corta
duración: revisa publicación, consentimiento y requisitos de Google.

## 5. Generar token y drive_id de OneDrive

1. Ejecuta `rclone config` en el PC; crea `bhbackup`, tipo `onedrive`.
2. Normalmente deja Client ID y Client Secret vacíos para usar el cliente
   compartido, si las políticas de tu organización lo permiten.
3. Autoriza en navegador y elige el OneDrive o biblioteca SharePoint correctos.
   Solicita consentimiento al administrador si el tenant lo requiere.
4. Con `rclone config file` abre el fichero privado. De `[bhbackup]` copia:
   JSON `token`, `drive_id` y `drive_type`. No uses el tenant ID como drive_id.
5. En el panel selecciona OneDrive y pega esos valores:
   `personal`, `business` o `documentLibrary` según el asistente.
6. Si necesitas cliente propio, sigue [la guía de rclone](https://rclone.org/onedrive/#getting-your-own-client-id-and-key):
   registra aplicación, redirección de rclone y permisos delegados necesarios.
   No uses el callback Google de BricoHams. Mantén mínimos privilegios y respeta
   la política de consentimiento del tenant.
7. Introduce en PC y panel el mismo ID y **Valor** del secreto. No confundas Valor
   con Id. del secreto. Anota caducidad.
8. Guarda, prueba, copia y verifica antes de programar.

La renovación del token se conserva en `rclone.conf`; no se sobrescribe al probar
de nuevo si no cambias credenciales. `invalid_grant` exige reautorizar. Si cambias
de cliente, el panel exige un token nuevo y no conserva un secreto del cliente anterior.
Los campos ID/secreto se pueden omitir al usar el cliente compartido.

## 6. SMB, NFS y SFTP

| Protocolo | Preparación y campos | Validación |
|---|---|---|
| SMB/CIFS | Cuenta dedicada y carpeta compartida en NAS; destino `\\nas.ejemplo\copias\bricohams`, usuario o `DOMINIO\usuario`, contraseña repetida y SMB 3 preferente. No OAuth. | Guardar y probar escritura con permisos mínimos. |
| NFS | Export `nas.ejemplo:/export/copias`, IP de estación autorizada y versión. Revisa UID/GID y root-squash; no requiere token en panel. | Probar sin desactivar protecciones globales. |
| SFTP | Host, puerto, usuario, contraseña y carpeta. Esta implementación no ofrece autenticación por clave privada. | Obtener huella, comparar por canal independiente con `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` en destino, confirmar y probar. |

En todos: Guardar → Probar conexión → Copiar ahora → Verificar última copia.
Probar crea/elimina un fichero temporal; verifica fecha, estado y tamaño.
La retención borra copias antiguas: revisa antes de programar.
No actives Incluir secretos en destinos no confiables: no hay cifrado adicional
de extremo a extremo. Una verificación SHA256 no sustituye ensayar restauración.

## 7. Cada módulo restante

Secuencia común: leer manual → verificar requisitos/hardware → respaldar → guardar
solo ajustes del módulo → comprobar estado/journal → prueba funcional → restaurar
si falla. «Guardado» no demuestra conexión ni recepción correctas.

| Módulo | Paso específico | Comprobación / documentación |
|---|---|---|
| Instalador, red, arranque y hardware | Editar env mediante el flujo del kit; `install.sh --actualizar --simular` y solo pasos necesarios. | No cambiar red sin recuperación; [manual 01](01_PREPARACION.md) y [catálogo](../COMPONENTES.md). |
| OpenWebRX+ nativo/Docker | Settings: receptor y dispositivos, guardar; no compartir SDR entre procesos. | Audio y waterfall; manuales 03 y 08 del kit. |
| owrx-clone | `owrx-clone --help`; exportar antes de importar. | Restauración en instancia aislada; [herramienta](../../owrx-clone/README.md). |
| Plugins/audio | Preferencias del receptor y configuración del kit para valores persistentes. | Control visible y audio navegador; manuales 27 y 41. |
| Bookmarks, CTCSS, RepeaterBook, locator | Exportar marcadores; General Settings para clave RepeaterBook; importar una zona pequeña. Locator/catálogos por consola. | Frecuencias de salida y tonos; manuales 30–33. |
| Meshtastic | Región legal, nombres y canal por radio; guardar y leer nodos. | No publicar PSK/URL; [manual 35](35_LORA_APRS_MESHTASTIC.md). |
| Mensajes | Seleccionar red y canal; mensaje de prueba. | Recepción en otro nodo; no saturar canal. |
| RAK APRS | Indicativo, passcode, puerto y región en env; estado en panel APRS. | Registro y paquetes recibidos; manual 35. |
| ADS-B/RadarBox/AIS | Serial SDR, feeds y AIS en env. | Recepción antes de envío externo; manuales 04 y 40. |
| map.flights | Registrar estación en [portal](https://map.flights/es/stations/build), guardar ID localmente y abrir diagnóstico privado. | Mantener RadarBox; [manual 38](38_MAPFLIGHTS_PLUGIN.md). |
| Meteo/Pico I/O/ventilación | Fuente en Clima; hardware/GPIO y puertos en env. | Lecturas plausibles y ventilador; manuales 06, 07 y 09. |
| Cámara | Fuente y credenciales en flujo seguro del kit; paso camara. | Imagen sin URL pública con contraseña. |
| Satélites/agendas/grabación/FT2 | Estación, agenda, filtros y capturas en panel; FT2 experimental por su manual. | Próximo pase, captura y espacio; [manual 42](42_CLIMA_RED_SATELITES_GRABACION.md). |
| Web/HTTPS/API/idioma/logo/privacidad | Dominio, identidad y contactos en kit, aplicar web/configuracion con backup. | HTTPS y políticas; [manual 40](40_HTTPS_MAPA_LOCAL_POLITICAS.md). |
| Visitas/Telegram/chat/registro oyentes | [BotFather](https://t.me/BotFather) → /newbot; token solo en asistente/campo secreto, chat_id con herramienta del kit. | Aviso de prueba y consentimiento; manuales 24 y 39. |
| TAK | Servicios/acceso en panel, credenciales y certificados, enrolar cliente. | Posición en mapa; no publicar paquetes de enrolamiento; manual 36. |
| Monitorización/Grafana | Panel Monitorización, abrir Grafana, revisar métricas. | Exporters/bases de datos no públicos. |
| Seguridad/usuarios | Administrador local de recuperación, acceso opcional Google y restricciones progresivas. | Ventana privada autorizada y cuenta denegada; manuales 34 y 46. |
| Copias/limpieza | Destino dedicado, retención y programación tras prueba. | Copia externa y restauración aislada; preservar logs de investigaciones. |
| Hardware/diseños/laboratorio | Documentación y consola; no hay formulario web. | [Hardware y GPIO](../HARDWARE_Y_GPIO.md), [desarrollo](../DESARROLLO_MODULOS.md), manuales 43–45. |

## 8. Secretos, recuperación y alcance

- El secreto de acceso Google y el OAuth del backup son independientes.
- Contraseñas/tokens/secretos del backup: `/etc/bricohams/backup-remoto.secret`
  (0600); ID del cliente en `backup-remoto.json`. No se rellenan secretos en HTML.
- Un campo secreto vacío conserva el anterior con el mismo proveedor/cliente.
- Mantén acceso SSH y usuario local al probar identidad externa.
- No se activa Google, no se solicita consentimiento Microsoft y no se crea un
  backup externo solo por abrir esta ayuda: debes completar el flujo del proveedor.
- Para recuperar acceso: consulta [antibloqueo Google](46_ACCESO_GOOGLE.md#5-antibloqueo).
- Restauración de despliegue: copia verificada registrada antes de instalar.

## 9. Actualizar una instalación existente

Desde un kit de origen probado y distinto del instalado:

```bash
sudo bash tools/actualizar-guias-modulos.sh /ruta/al/kit-nuevo /opt/bricohams/kit
```

Se pueden añadir otros directorios de kit instalado como argumentos. El script
verifica copia con `tar --compare` y SHA256, registra `BACKUP_VERIFICADO` y
`RESTAURAR.sh`, instala solo panel/backup/documentación relacionada y reinicia
únicamente el panel. No cambia credenciales ni activa proveedores.
Ante fallo de instalación o salud intenta restaurar automáticamente y muestra
la ruta de recuperación. No ejecutar mientras hay una copia remota en curso.
