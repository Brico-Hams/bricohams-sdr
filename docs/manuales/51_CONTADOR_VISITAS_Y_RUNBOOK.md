# 51 · Contador de visitas y runbook de verificación del blindaje

Alcance: cambios solo en el repositorio. No se ha tocado ninguna infraestructura, credencial ni commit.

## 1. Contador de visitas y tarjeta «Tu conexión» (portada `/bricohams/`)

| Pieza | Fichero | Función |
|---|---|---|
| API | `files/bin/bricohams-api.py` (`ContadorVisitas`) | `GET /bricohams/api/visitas` → `{"total","hoy"}`; `POST` suma una visita (mismo origen) |
| Datos | `/var/lib/bricohams/visitas-web.sqlite` (0600) | tabla `visitas_dia(dia, n)`: solo dos números por día |
| IP interna | `/var/lib/bricohams/visitas-ip.sqlite` (0600, usuario del servicio) | tabla `visitas_ip(dia, ip, n)`: IP completa validada, borrada a los `VISITAS_IP_DIAS` (1-30, 14 por defecto) |
| Tarjeta | `GET /bricohams/api/mi-ip` | `{"ip":"203.0.x.x","identidad":"EA5ABC"}`: solo la IP del propio visitante, enmascarada (IPv4 con exactamente los dos primeros octetos; IPv6 tres primeros grupos y `x:x:x:x:x`), más la identidad que él eligió si existe (`identidad` se omite si no) y el país ISO aproximado (`pais`, de la base GeoIP local; se omite si no hay base o la IP no es pública). El banner del receptor raíz (plugin `visitas`) lo usa junto a `/bricohams/api/visitas` |
| Identidad↔IP | `/var/lib/bricohams/conexiones-ip.sqlite` (0600, `files/bin/bricohams_conexiones.py`) | tabla `conexion(ip, visto, identidad, tipo, aviso_msg, aviso_base)`: la escriben la API (registro de oyentes) y `bricohams-visitas` (nombre del chat); mismos `VISITAS_IP_DIAS` de retención y tope de 5000 filas |
| Telegram | `bricohams-visitas.py` | el aviso «🟢 Nuevo oyente» lleva `👤 identidad` si ya se conocía; si el oyente se identifica después, el aviso ya enviado se **edita** (`editMessageText`), sin mandar otra llegada |
| Portada | `files/web/index.html.tmpl` | dos tarjetas: visitas y «Tu conexión» (navegador, sistema, idioma, IP enmascarada) |
| nginx | `bricohams-sdr-rutas.conf`, `bricohams-sdr.conf.tmpl` | ubicaciones exactas `visitas` y `mi-ip` con zona `bh_visitas` (30 r/min, ráfaga 5); `X-Forwarded-For $remote_addr` (sobrescribe) y `X-Real-IP ""` |
| Privacidad | `files/web/privacidad.html` | párrafo con IP interna, retención y máscara |

Privacidad: la IP completa nunca sale por la API ni la web; no hay endpoint, exportación ni listado. Solo la lee el operador en la
estación (`sudo -u openwebrx sqlite3 …`). No se guarda agente de usuario ni identificador; no se consulta ningún servicio externo. Navegador,
sistema e idioma se calculan en el navegador y no se envían. Se cuenta una visita por pestaña (`sessionStorage`); es un contador
orientativo, no antifraude.

**Identidad.** Se reutiliza el flujo existente (`POST /bricohams/api/oyentes` con consentimiento, o el nombre del chat de OpenWebRX+); no hay registro nuevo.
El texto se normaliza (NFKC), se le quitan controles y caracteres de formato (bidi, ancho cero), se acota a 80 caracteres y se escapa en HTML para Telegram.
No aparece en `visitas.json`, `/api/visitas` ni estadísticas. Limitación: varios oyentes tras la misma IP (CGNAT/oficina) comparten identidad mientras dure la retención;
el último que se identifica prevalece. Si Telegram rechaza la edición (mensaje antiguo, red) se ignora: no se manda un aviso nuevo.

**Origen fiable de la IP.** La API solo lee `X-Forwarded-For` si el socket de la conexión está en `API_PROXIES_CONFIABLES`
(por defecto `127.0.0.1,::1`, el nginx local). Acepta un único valor IP válido (rechaza listas, texto, zonas `%`, loopback, no especificada
y multicast; las IPv4 mapeadas se normalizan). nginx sobrescribe la cabecera con `$remote_addr`, así que un `X-Forwarded-For`/`X-Real-IP`
enviado por el cliente no llega a la API. Si se pone un CDN o proxy delante de nginx, `$remote_addr` pasa a ser el del CDN: configurar
antes `set_real_ip_from` con sus rangos y `real_ip_header`, o la IP guardada será la del proxy. `bricohams-api` debe escuchar solo en 127.0.0.1.

### Despliegue (lo ejecuta el operador)
1. `bash tests/run_tests.sh` (incluye `tests/test_contador_visitas.py`).
2. `sudo bash install.sh --solo web,api` (o el paso que regenera nginx, portada y `bricohams-api`; ver `install.sh`). Escribe `VISITAS_IP_DIAS` en `api.env`.
3. `sudo nginx -t && sudo systemctl reload nginx`; `systemctl is-active bricohams-api`.

## 2. Auditoría de configuración versionada (hallazgos)

| Prio | Hallazgo | Estado |
|---|---|---|
| P1 | `bricohams-api.service` sin sandbox (corre como `openwebrx` con toda la FS) | Corregido: `NoNewPrivileges`, `ProtectSystem=strict`, `ProtectHome`, `PrivateTmp`, `ProtectKernel*`, `RestrictAddressFamilies`, sin capacidades |
| P1 | HSTS solo con `SSL_MODO=todo`; en `admin` el receptor público va por HTTP | Decisión del operador; documentado |
| P2 | Sin `Content-Security-Policy` en nginx (la portada usa script en línea) | Pendiente: añadir CSP con hash/nonce tras probar OpenWebRX+ |
| P2 | `GET /bricohams/api/*` (indicativo, avión) sin `limit_req` | Pendiente: zona propia para no agotar cuotas HamQTH/QRZ |
| P2 | `proxy_read_timeout 1d` en `/` sin `limit_conn` | Pendiente: `limit_conn` por IP en websockets |
| P3 | Puerto 8073 de OpenWebRX+ accesible si el router lo abre | Verificar cierre (manual 34) |

## 3. Runbook de verificación (solo lectura, por prioridad)

**P0 · antes de nada:** copia de `/etc/nginx/`, `/etc/systemd/system/bricohams-api.service` y `/var/lib/bricohams/`.

**P1**
1. `sudo nginx -t` → `syntax is ok`.
2. `systemctl is-active bricohams-api nginx fail2ban`; `systemd-analyze security bricohams-api` (puntuación inferior a la anterior).
3. `curl -s http://127.0.0.1:8075/bricohams/api/salud` → `{"ok": true}`.
4. `curl -s https://DOMINIO/bricohams/api/visitas` → solo `total` y `hoy`.
5. `curl -s -X POST -H 'Origin: https://otro.example' -H 'Content-Type: application/json' -d '{}' https://DOMINIO/bricohams/api/visitas` → 403.
6. `sudo bricohams-blindaje` (modo auditoría) sin fallos; SSH solo con clave; `ss -ltnp` sin 8073/8075/9443 en interfaces públicas.

**P2**
7. Ráfaga de 50 POST → aparecen 429 (`bh_visitas`).
8. `sqlite3 /var/lib/bricohams/visitas-web.sqlite '.schema'` → solo `dia`, `n`; permisos 600. `sqlite3 /var/lib/bricohams/visitas-ip.sqlite '.schema'` → solo `dia`, `ip`, `n`; permisos 600; `SELECT MIN(dia) FROM visitas_ip` no anterior a hoy − `VISITAS_IP_DIAS`.
9. Portada a 320 px y 1280 px, modo oscuro, navegación con teclado, lector de pantalla (valores anunciados).
10. IP propia enmascarada: `curl -s https://DOMINIO/bricohams/api/mi-ip` → `{"ip":"82.160.x.x"}` con tu IP (o `a:b:c:x:x:x:x:x`); con `-H 'X-Forwarded-For: 1.2.3.4'` sigue mostrando la tuya (nginx sobrescribe). `curl -s http://127.0.0.1:8075/bricohams/api/mi-ip` sin cabecera → 404; con `-H 'X-Forwarded-For: 1.2.3.4'` desde el propio servidor sí responde (el socket local es de confianza), por eso la API nunca debe exponerse fuera de 127.0.0.1.
10b. Identidad: `ls -l /var/lib/bricohams/conexiones-ip.sqlite` → `-rw-------`; `sqlite3 … 'SELECT MIN(visto) FROM conexion'` no anterior a hoy − `VISITAS_IP_DIAS`; registrar un indicativo de prueba desde el navegador y comprobar que el aviso de Telegram se edita (un solo «Nuevo oyente») y que la tarjeta muestra la identidad tras recargar.
11. `curl -s https://DOMINIO/bricohams/api/visitas https://DOMINIO/bricohams/api/mi-ip | grep -E '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+'` → ninguna IP completa.
12. Borrado a petición (derecho de supresión): `sudo -u openwebrx sqlite3 /var/lib/bricohams/visitas-ip.sqlite "DELETE FROM visitas_ip WHERE ip='A.B.C.D'"` y `sudo -u openwebrx sqlite3 /var/lib/bricohams/conexiones-ip.sqlite "DELETE FROM conexion WHERE ip='A.B.C.D'"`.

## 4. Rollback (por orden de impacto mínimo)

1. **Sandbox del servicio** (si `bricohams-api` no arranca): `sudo systemctl edit --full bricohams-api` y quitar las líneas añadidas, o reinstalar la unidad anterior desde la copia; `daemon-reload && restart`.
2. **Contador**: restaurar `/etc/nginx/snippets/bricohams-sdr-rutas.conf` y `/etc/nginx/sites-available/bricohams-sdr` de la copia, `nginx -t && reload`. Las tarjetas muestran «No disponible» sin romper la portada.
3. **Portada**: restaurar `/var/www/bricohams/index.html` y `privacidad.html` de la copia, o `git revert` de los cambios en el repo (sin push automático).
4. **Datos**: `visitas-web.sqlite`, `visitas-ip.sqlite` y `conexiones-ip.sqlite` pueden borrarse sin efectos colaterales (el contador vuelve a 0 / se pierde solo el registro interno de IP e identidad; los avisos siguen sin identidad).
5. **IP propia**: quitar la fila «Tu IP» de la portada y la ubicación `mi-ip` de nginx; el contador sigue funcionando. Para dejar de guardar IP: `API_PROXIES_CONFIABLES=` vacío en `api.env` (la API ignora entonces `X-Forwarded-For`) y reiniciar.
