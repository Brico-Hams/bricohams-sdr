# 25 · Tareas automáticas: copias, actualizaciones, reinicios y avisos

<!-- guia-visual:inicio -->
> **Ruta visual:** [Tareas, backups, limpieza, actualización y clonado](../GUIA_VISUAL_MODULOS.md#mantenimiento).
> Consulta allí requisitos, ilustración, cuadro de instalación, comprobaciones y restauración.
> Los comandos de este manual se ejecutan en Bash en la Pi; revisa el backup antes de cambiarla.
<!-- guia-visual:fin -->

**Qué hace:** la Pi se mantiene sola con un **cron** (`/etc/cron.d/bricohams`) que ejecuta una **cuenta de servicio** llamada `bricohams`.

## 1. Por qué una cuenta de servicio y no «credenciales embebidas» (ADR-34)
**El problema:** actualizar paquetes, hacer copias o reiniciar exige ser root. La idea de guardar una contraseña de sudo en un script es peligrosa: cualquiera que lea el script o la copia de seguridad la tendría.

**Cómo está resuelto:**
- **La cuenta:** `bricohams` es una cuenta de sistema **sin contraseña y sin shell** (`/usr/sbin/nologin`). Nadie puede entrar con ella.
- **Lo que puede hacer:** `/etc/sudoers.d/bricohams` solo le deja ejecutar **un programa**, sin pedir clave:
  ```
  bricohams ALL=(root) NOPASSWD: /usr/local/sbin/bricohams-tarea
  ```
- **Actualizar el kit** (git + pasos cambiados) **no** está en el cron: se hace a mano con `sudo bash install.sh --actualizar` ([manual 29](29_ACTUALIZAR.md), ADR-37). El verbo `actualizar` del cron solo toca paquetes.
- **El programa:** `bricohams-tarea` solo acepta **verbos fijos**: `actualizar`, `copia`, `reinicio`, `salud`, `geoip`, `resumen` y `satpass`. No admite comandos arbitrarios.
- **Resultado:** el cron funciona sin pedir sudo y **no hay ninguna contraseña guardada** en ningún sitio.

## 2. Calendario (se cambia en `bricohams.env`)
| Variable | Por defecto | Tarea |
|---|---|---|
| `CRON_COPIA` | `30 4 * * *` (cada día, 04:30) | copia en `/var/backups/bricohams` y perfil de OpenWebRX+ con owrx-clone; retención local de cinco días; aviso solo si falla |
| `CRON_ACTUALIZAR` | `30 3 * * 1` (lunes, 03:30) | `apt update` + `upgrade`, sin preguntas y respetando lo retenido; aviso al terminar |
| `CRON_REINICIO` | `0 5 * * 1` (lunes, 05:00) | reinicio preventivo; **se aplaza 20 min si hay un pase de satélite** |
| `CRON_SALUD` | `*/30 * * * *` | `bricohams-check`; avisa por Telegram si aparece un fallo y cuando se arregla (sin repetir) |
| `CRON_RESUMEN` | `0 21 * * *` | resumen de visitas del día |
| `CRON_GEOIP` | `15 3 2 * *` | base GeoIP del mes |
| (DuckDNS) | `*/5 * * * *` | actualiza la IP si `DUCKDNS_DOMAIN`/`TOKEN` están puestos |

Después de cambiar el calendario: `sudo bash install.sh --solo tareas`.

La limpieza local es independiente del cron: `bricohams-backup-limpieza.timer` se instala con el paso
`herramientas` y se ejecuta diariamente a las **06:15**. Borra copias de configuración y perfiles de más de
120 horas; no toca copias remotas ni carpetas de despliegues. Simulación, registro y desactivación:
[manual 09](09_MANTENIMIENTO.md#limpieza-automática-de-copias-locales).

## 3. Lanzar una tarea a mano
```bash
sudo /usr/local/sbin/bricohams-tarea copia
sudo /usr/local/sbin/bricohams-tarea actualizar
sudo -u bricohams sudo -n /usr/local/sbin/bricohams-tarea salud   # como lo hace el cron
cat /etc/cron.d/bricohams
tail -f /var/log/bricohams-tareas.log
```

## 4. Notas
- **El driver rtl-sdr no se toca:**
  - en Bookworm está retenido con `apt-mark hold`;
  - en Trixie se usa el de Debian, y las actualizaciones lo mantienen coherente.
- **Si una actualización pide reiniciar** (`/var/run/reboot-required`), lo hace el reinicio preventivo del lunes.
- **La copia incluye:**
  - la configuración de OpenWebRX+;
  - `/etc/bricohams`, que contiene claves: guarda las copias en sitio seguro;
  - nginx, Let's Encrypt y mosquitto;
  - cron y sudoers;
  - el portal y `/var/lib/bricohams` (visitas, lluvia e históricos).
