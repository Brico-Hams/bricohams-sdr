# 46 · Acceso de administradores: usuarios locales y Google (v5.5)

**Edición 2026-10-19.** Complementa el [manual 34](34_BLINDAJE_SEGURIDAD.md) (panel Seguridad).
Decisión de diseño: ADR-71 en [ARQUITECTURA](../ARQUITECTURA.md).

Los administradores de `/settings`, de los paneles BricoHams (`/settings/bricohams/…`) y de la web
de Meshtastic pueden entrar de dos maneras:

- **Usuario local**: los usuarios de la base de datos de OpenWebRX+ (`users.json`), que se gestionan
  en `/settings` → Seguridad → «Usuarios de la web». Todos tienen rol de administrador.
- **Cuenta de Google**: inicio de sesión OpenID Connect con Google. Solo entran los correos (o el
  `@dominio` de Google Workspace) de la lista de administradores.

El receptor público (`/`) no cambia: sigue abierto sin sesión.

## 0. Dónde se configura (resumen)

| Qué | Dónde |
|---|---|
| Método de acceso, cliente de Google, correos y horas de sesión | Web: `https://TU_DOMINIO/settings/bricohams/seguridad` → tarjeta **«Métodos de acceso de administradores»** (ancla `#acceso`). Se guarda en `bricohams.env` (claves `GOOGLE_*`). |
| Secreto del cliente | Solo en el servidor: `/etc/bricohams/google/client_secret` (0600). Se pega en el panel o en `configurar`; nunca vuelve al navegador. |
| Usuarios locales (base de datos de OpenWebRX+) | Misma página → tarjeta «Usuarios de la web». |
| Cliente OAuth (ID, secreto, URI de redirección) | [Google Cloud Console → Credenciales](https://console.cloud.google.com/apis/credentials) (apartado 3). |
| Consola | `bricohams-google-auth configurar\|aplicar\|comprobar --kit-env …` (apartado 4). |
| Registros | `journalctl -u bricohams-google-auth` y `journalctl -u bricohams-google-auth-aplicar`. |

Estas referencias también están en el propio módulo y en la web:

- **Panel Seguridad**: la tarjeta incluye los desplegables «Cómo crear el cliente de Google» (con
  enlace a la consola) y «Dónde se configura cada cosa». La tarjeta de usuarios enlaza a `#acceso`.
- **`/login`**: bajo el botón «Entrar con Google» hay una nota que indica dónde se configura.
- **Páginas de error de la pasarela** («Cuenta sin permiso», «Acceso cancelado»…): enlace para entrar
  con el usuario local y referencia al panel y a este manual.
- **`bricohams-google-auth --help`** y **`… comprobar`**: muestran la misma guía en la consola.

## 1. Modos

| Modo (panel) | `GOOGLE_AUTH` / `GOOGLE_AUTH_MODO` | Cómo se entra |
|---|---|---|
| Solo usuarios locales | `no` | Usuario y contraseña de OpenWebRX+, como siempre. |
| **Usuario local o cuenta de Google** (recomendado) | `yes` / `alternativa` | En `/login` aparece el formulario de siempre y debajo el botón **«Entrar con Google»**. Cualquiera de los dos vale. |
| Cuenta de Google y además usuario local | `yes` / `doble` | Primero Google, después el usuario local (dos factores). |
| Solo cuenta de Google | `yes` / `solo_google` | `/login` lleva directamente a Google. |

En «alternativa» y «solo Google», tras validar la cuenta de Google la pasarela abre la sesión de
OpenWebRX+ con la cuenta de servicio `bricohams-google`. Su clave es aleatoria, se guarda solo en el
servidor (`/etc/bricohams/google/owrx_password`, 0600) y nadie la teclea. En la tabla de usuarios
aparece como «Google (cuenta de servicio)» y no se puede editar ni borrar desde el panel.

## 2. Requisitos

- Un dominio con HTTPS (`SSL_DOMAIN` y `SSL_MODO` distinto de `no`): Google no admite una IP como
  dirección de vuelta.
- Una cuenta de Google para crear el cliente OAuth (no hace falta facturación).

## 3. Crear el cliente OAuth en Google Cloud (paso a paso)

1. Entra en <https://console.cloud.google.com/> y crea un proyecto (por ejemplo, «BricoHams SDR»).
2. **APIs y servicios → Pantalla de consentimiento de OAuth**: tipo **Externo**, nombre de la
   aplicación, tu correo de asistencia y ámbitos `openid` y `email`. Mientras esté «en pruebas»,
   añade tus correos como usuarios de prueba.
3. **Credenciales → Crear credenciales → ID de cliente de OAuth → Aplicación web.**
4. **Orígenes de JavaScript autorizados:** `https://TU_DOMINIO`
5. **URI de redirección autorizados:** `https://TU_DOMINIO/_bh_google/callback` (exactamente así).
6. Pulsa *Crear* y copia el **ID de cliente** (`…apps.googleusercontent.com`) y el **secreto**
   (`GOCSPX-…`). El secreto no se pega en el chat, en correos ni en Git.

## 4. Activarlo desde el panel Seguridad

1. Entra con tu usuario local en `https://TU_DOMINIO/settings/bricohams/seguridad`.
2. Tarjeta **«Métodos de acceso de administradores»**:
   - marca «Usuario local o cuenta de Google»;
   - pega el ID de cliente y el secreto;
   - escribe los correos de Google administradores (o `@midominio.es`) separados por comas;
   - deja las horas de sesión (8 por defecto; de 0,25 a 168).
3. Pulsa **Guardar y aplicar**. El panel valida los datos, guarda el secreto en
   `/etc/bricohams/google/client_secret` (0600, root) y lanza `bricohams-google-auth-aplicar.service`,
   que prepara la pasarela, adapta nginx, ejecuta `nginx -t` y recarga. Si `nginx -t` falla, deja
   los ficheros como estaban. El resultado se ve en la línea **Estado** de la tarjeta (recarga la página).
4. Cierra la sesión y comprueba que `/login` muestra «Entrar con Google». Pruébalo.
5. Opcional: cuando hayas entrado con Google al menos una vez, ya puedes elegir «doble» o «solo Google».

El secreto nunca vuelve al navegador. Si dejas el campo vacío, se conserva el que hay guardado.

### Desde la consola (alternativa al panel)

```bash
sudo bricohams-google-auth configurar --kit-env /opt/bricohams/kit/bricohams.env   # pide ID, secreto (oculto) y correos
sudo bricohams-google-auth aplicar --kit-env /opt/bricohams/kit/bricohams.env
sudo bricohams-google-auth comprobar --kit-env /opt/bricohams/kit/bricohams.env
```

## 5. Antibloqueo

El panel rechaza los cambios que te dejarían fuera:

- «Solo locales» y «doble» exigen al menos un usuario local activo (sin contar la cuenta de servicio).
- Para pasar a «doble» o «solo Google» desde un modo sin Google, la petición tiene que llevar ya una
  sesión de Google válida. Por eso primero se activa «Usuario local o Google» y se entra con Google.
- Si la pasarela no arranca al aplicar, se vuelve sola a «solo usuarios locales» y lo indica en *Estado*.

### Acceso de emergencia (te has quedado fuera)

Por SSH o con teclado en la Pi:

```bash
sudo bricohams-google-auth configurar --kit-env /opt/bricohams/kit/bricohams.env --desactivar
sudo bricohams-google-auth aplicar --kit-env /opt/bricohams/kit/bricohams.env
```

Así se vuelve a «solo usuarios locales». Si tampoco recuerdas la contraseña local:
`sudo openwebrx admin resetpassword USUARIO` (o con `docker exec` en la versión Docker).

## 6. Cómo funciona

- `bricohams-google-auth` (`DynamicUser`, `127.0.0.1:8077`) publica `/_bh_google/login`,
  `/callback`, `/auth`, `/entrar` y `/salir`. Usa *Authorization Code* con PKCE, `state` y `nonce`,
  valida el `id_token` (recibido directamente de Google por TLS verificado, OpenID Connect Core §3.1.3.7:
  emisor, audiencia, fechas, `nonce` y `email_verified`) y crea una cookie `bh-google` firmada con HMAC (`HttpOnly`, `Secure`,
  `SameSite=Lax`).
- nginx: los cambios van entre `# bricohams-google:inicio` y `# bricohams-google:fin`, o en líneas
  marcadas con `# bricohams-google`. `bricohams-google-auth nginx --quitar` devuelve el fichero original.
  - «alternativa»: solo añade `/_bh_google/` y el botón en `/login` (`sub_filter` sobre `</form>`).
  - «doble» y «solo Google»: añade además `auth_request` en `/login`, `/settings` y los paneles.
- El panel se ejecuta con `ProtectSystem=strict` y no puede escribir en nginx ni en systemd: por eso
  delega en la unidad *oneshot* `bricohams-google-auth-aplicar.service`.

## 7. Despliegue en una estación ya instalada

`tools/actualizar-google-auth.sh` (o `scripts-despliegue/Desplegar-GoogleAuth.ps1` desde Windows):
copia de seguridad verificada (`BACKUP_VERIFICADO=…` y `RESTAURAR.sh`), instalación de la pasarela y
del panel, unidad de aplicar, `nginx -t` y comprobaciones. Si algo falla, restaura solo. **No activa
Google**: se elige después en el panel.

Antes de la copia, el `.ps1` ofrece liberar espacio con `tools/limpiar-copias-despliegue.sh`:
muestra el espacio libre y la lista de copias de **despliegue** antiguas (`/var/backups/bricohams/<tipo>-FECHA-PID/`
y `/var/backups/bricohams-<tipo>-FECHA[.tar.gz]`), conserva la más reciente de cada tipo y solo borra si se
escribe `BORRAR`. Nunca toca las copias diarias (`backup-openwebrx-*`, `perfil-owrx-*`, con su propia
retención de cinco días), las de deshacer (`bricohams-blindaje/`, `owrx-clone/`) ni los enlaces simbólicos.
Para ver qué borraría sin borrar nada: `sudo bash tools/limpiar-copias-despliegue.sh --lista`.

## 8. Problemas

| Síntoma | Causa y solución |
|---|---|
| Google dice `redirect_uri_mismatch` | La URI registrada no es exactamente `https://TU_DOMINIO/_bh_google/callback`. |
| «Cuenta sin permiso» | El correo no está en la lista de administradores, o la cuenta no tiene el correo verificado. |
| «Acceso cancelado» al volver de Google | Cancelaste en Google, o la pantalla de consentimiento está «en pruebas» y tu correo no es usuario de prueba. |
| No aparece «Entrar con Google» | Mira *Estado* en la tarjeta y `journalctl -u bricohams-google-auth-aplicar -n 30`. |
| *Estado* en rojo: «nginx -t falló» | Los ficheros se han restaurado; `sudo nginx -t` muestra el error. |
| El panel no deja elegir «doble» o «solo Google» | Primero entra con Google en el modo «Usuario local o Google». |

Pruebas: `tests/test_google_auth.py` (pasarela, modos, nginx, `aplicar`) y `tests/test_mesh_admin.py`
(tarjeta, validación y antibloqueo).
