# 23 · Web con SSL, portal de servicios y cómo entrar a cada uno

<!-- guia-visual:inicio -->
> **Ruta visual:** [Portal, HTTPS, API y paneles administrativos](../GUIA_VISUAL_MODULOS.md#web).
> Consulta allí requisitos, ilustración, cuadro de instalación, comprobaciones y restauración.
> Los comandos de este manual se ejecutan en Bash en la Pi; revisa el backup antes de cambiarla.
<!-- guia-visual:fin -->

![Servicios](../esquemas/18_red_servicios.png)

**Qué hace:** **nginx** va delante de OpenWebRX+ con un certificado de **Let's Encrypt** que se renueva solo.

> **v5.0 · todo por 443 y 8073 decomisionado** ([manual 40](40_HTTPS_MAPA_LOCAL_POLITICAS.md)): `SSL_MODO="todo"` pasa a ser el defecto (el 80 solo redirige a HTTPS y sirve Let's Encrypt, con HSTS) y OpenWebRX+ escucha solo en `127.0.0.1:8073` (`OWRX_SOLO_LOCAL="yes"`). El modo `admin` de abajo sigue disponible si lo pones a mano.

> **v4.2 · decisión de N0CALL: el certificado SSL es solo para la administración** (`SSL_MODO="admin"`, por defecto):
> - el **receptor público** se sirve por **HTTP** (`http://<tu dominio>/`), como siempre;
> - **`/login`, `/settings`** y el resto de páginas de administración se **fuerzan a HTTPS**: la contraseña nunca viaja sin cifrar;
> - la cookie de sesión del administrador sale con `Secure`, así el navegador no la manda nunca por el HTTP público;
> - sin HSTS (si no, el navegador ya no volvería a HTTP).
>
> | `SSL_MODO` | Receptor | Administración | Router |
> |---|---|---|---|
> | `admin` | HTTP | **HTTPS forzado** | 80 y 443 |
> | `todo` (defecto desde v5.0) | HTTPS (HTTP redirige, con HSTS) | HTTPS | 80 y 443 |
> | `no` | HTTP | HTTP (¡contraseña sin cifrar! solo LAN) | 80 |
>
> Cambiarlo: edita `SSL_MODO` en `bricohams.env` y `sudo bash install.sh --solo web`.

- **Desde casa:** `https://<IP>/` (desde v5.0 el 8073 solo responde en la propia Pi).

## 1. Qué necesitas
1. **Un dominio** que apunte a la IP de tu casa. Vale cualquiera de estos:
   - **uno propio** (por ejemplo `sdr.bricohams.es`), con un registro A hacia tu IP pública;
   - **DuckDNS, gratis:**
     1. Entra en https://www.duckdns.org con tu cuenta y crea por ejemplo `bricohams-sdr`.
     2. Copia el *token*.
     3. En `bricohams.env`, pon `DUCKDNS_DOMAIN="bricohams-sdr"` y `DUCKDNS_TOKEN="…"`. La Pi actualiza la IP cada 5 min.
2. **En el router:** reenvía los puertos **80 y 443 TCP** a la IP de la Pi (con `SSL_MODO="no"`, solo el 80). **No abras el 8073, el 4403 ni el 9443.** Lo ideal es darle a la Pi una IP fija en el DHCP del router.
3. **En `bricohams.env`:**
   ```
   SSL_DOMAIN="bricohams-sdr.duckdns.org"    # o tu dominio
   SSL_EMAIL="tu@correo"                      # avisos de caducidad
   SSL_MODO="todo"                            # todo (defecto) · admin · no
   ```
4. **Aplica los cambios:**
   ```bash
   sudo bash install.sh --solo web,tareas
   ```

- **Qué hace el paso `web`:**
  - instala nginx y certbot;
  - sirve el mapa de aviones tar1090 desde nginx (configuración oficial; si no está, proxy al 8504 local);
  - crea el portal `/bricohams/` y la página de privacidad;
  - arranca con un certificado autofirmado y pide el de Let's Encrypt.
- **Si Let's Encrypt falla** (el dominio aún no apunta o el puerto 80 está cerrado), se queda con el autofirmado y te avisa. Repite el paso cuando esté listo.

## 2. Direcciones
| Servicio | Desde Internet | Desde casa |
|---|---|---|
| Receptor OpenWebRX+ | `https://DOMINIO/` | `https://IP/` |
| Portal con todos los servicios | `http://DOMINIO/bricohams/` | `http://IP/bricohams/` |
| Mapa de aviones tar1090 | `http://DOMINIO/tar1090/` | igual |
| Cámara del mástil (HLS) | `http://DOMINIO/camara/mastil/` | `http://IP:8888/mastil/` |
| Aviso de privacidad | `http://DOMINIO/bricohams/privacidad.html` | — |
| API de los plugins | `http://DOMINIO/bricohams/api/salud` | — |
| Meshtastic 433 / 868 (configuración) | **solo con sesión de admin:** `https://DOMINIO/settings/bricohams/meshtastic` (botón «Meshtastic 433 / 868» en Ajustes) | igual |
| Meshtastic API del nodo 868 | no expuesto | `IP:4403` (TCP, sin clave: solo LAN) |
| RTSP de la cámara | no expuesto | `rtsp://IP:8554/mastil` |
| Admin de OpenWebRX+ | **`https://DOMINIO/settings`** (si entras por http, te lleva a https) | igual |

Con `SSL_MODO="todo"` todo lo de arriba va por `https://`. El HTTPS también sirve el receptor: quien prefiera `https://DOMINIO/` puede usarlo.

**Para ver todo de un vistazo:**
```bash
bricohams-servicios      # estado y direcciones de cada servicio (no necesita sudo)
```

## 3. Seguridad
- **nginx:**
  - pasa la IP real del oyente a OpenWebRX+ (`X-Forwarded-For`), así funcionan los baneos del admin y las estadísticas;
  - añade cabeceras básicas (y HSTS solo con `SSL_MODO="todo"`);
  - solo admite TLS 1.2 y 1.3;
  - fuerza a HTTPS estas rutas de OpenWebRX+ (las que piden usuario): `/login`, `/logout`, `/pwchange`, `/settings…`, `/imageupload`, `/clients`, `/services`, `/ban`, `/unban`, `/broadcast`, `/files/delete`;
  - marca la cookie `owrx-session` como `Secure; HttpOnly; SameSite=Lax`.
- **Ficheros:** `/etc/nginx/sites-available/bricohams-sdr` (lo genera el paso `web` desde `files/nginx/bricohams-sdr.conf.tmpl` según `SSL_MODO`) y `/etc/nginx/snippets/bricohams-sdr-rutas.conf` (las rutas comunes a HTTP y HTTPS).
- **Comprobación:** `bricohams-check` prueba que `http://…/settings` redirige a HTTPS.
- **Lo que solo escucha en `127.0.0.1`:** API, MQTT, tar1090 y HLS. Desde fuera solo se llega a ellos a través de nginx.
- **Renovación:** la hace el temporizador `certbot.timer`. Después recarga nginx (`/etc/letsencrypt/renewal-hooks/deploy/bricohams-nginx.sh`). `bricohams-check` avisa si quedan menos de 14 días.

## 4. Problemas típicos
| Síntoma | Arreglo |
|---|---|
| El navegador avisa de «no seguro» | certificado autofirmado: pon `SSL_DOMAIN` y repite `--solo web` |
| Let's Encrypt «Timeout during connect» | el puerto 80 no llega a la Pi: revisa el reenvío del router y el firewall |
| La web carga pero la cascada no se mueve | nginx sin websockets: `sudo nginx -t`; el bloque `location /` debe tener `Upgrade` |
| tar1090 da 502 | `systemctl status lighttpd`; tiene que escuchar en 127.0.0.1:8504 |
| `/settings` no pide HTTPS | `SSL_MODO` vale `no`, o falta repetir `sudo bash install.sh --solo web` |
| Tras entrar en `/settings`, en el receptor no salgo como admin | es lo esperado en `admin`: la sesión vive solo en HTTPS. Abre el receptor por `https://DOMINIO/` si la necesitas allí |
| `nginx no acepta la configuración` | el paso para con el mensaje de `nginx -t`. Desde la v4.2 ya no se usa `http2 on;` (no existe en el nginx 1.22 de Bookworm) |
