#!/bin/bash
# Instala o actualiza el acceso de administradores con Google (bricohams-google-auth) y la
# tarjeta «Métodos de acceso» del panel Seguridad (bricohams-mesh-admin) en una estación ya
# instalada. Copia de seguridad verificada antes de tocar nada y restauración automática si
# algo falla. No activa Google por sí solo: se elige en /settings → Seguridad (o con --configurar).
# Uso: sudo bash tools/actualizar-google-auth.sh /ruta/kit-nuevo /ruta/kit-instalado [--configurar]
set -Eeuo pipefail
umask 077
[[ $EUID -eq 0 ]] || { echo "Ejecuta con sudo." >&2; exit 1; }
NUEVO="${1:?Ruta absoluta del kit nuevo}"
KIT="${2:?Ruta absoluta del kit instalado}"
OPCION="${3:-}"
[[ "$NUEVO" = /* && "$KIT" = /* ]] || exit 1
BIN="$NUEVO/files/bin/bricohams-google-auth"
ADMIN="$NUEVO/files/bin/bricohams-mesh-admin"
KIT_ENV="$KIT/bricohams.env"
RUTAS_NGINX=/etc/nginx/snippets/bricohams-sdr-rutas.conf
SITIO_NGINX=/etc/nginx/sites-available/bricohams-sdr
UNIDAD_APLICAR=/etc/systemd/system/bricohams-google-auth-aplicar.service
OWRX_USERS="${OWRX_USERS:-/var/lib/openwebrx/users.json}"

# ---- comprobaciones previas (no cambian nada)
for f in "$BIN" "$ADMIN"; do
    python3 -c 'import ast, sys; ast.parse(open(sys.argv[1], encoding="utf-8").read())' "$f"
done
[[ -f "$KIT_ENV" ]] || { echo "No existe $KIT_ENV" >&2; exit 1; }
[[ -f "$RUTAS_NGINX" && -f "$SITIO_NGINX" ]] || { echo "No están los ficheros de nginx del kit (paso web)." >&2; exit 1; }
systemctl cat bricohams-mesh-admin >/dev/null 2>&1 || { echo "No está instalado bricohams-mesh-admin (panel de /settings)." >&2; exit 1; }
leer() { python3 - "$KIT_ENV" "$1" <<'PY'
import shlex, sys
for l in open(sys.argv[1], encoding='utf-8'):
    l = l.strip()
    if l.startswith(sys.argv[2] + '='):
        v = shlex.split(l.split('=', 1)[1], comments=True)
        print(v[0] if v else '')
PY
}
DOM=$(leer SSL_DOMAIN | tail -n1)
SSLM=$(leer SSL_MODO | tail -n1)
[[ -n "$DOM" ]] || echo "AVISO: falta SSL_DOMAIN en $KIT_ENV; Google no se podrá activar hasta ponerlo." >&2
[[ "${SSLM:-todo}" != no ]] || echo "AVISO: SSL_MODO=no; Google exige HTTPS." >&2
nginx -t >/dev/null 2>&1 || { echo "nginx ya tiene errores antes de empezar (nginx -t). No se toca nada." >&2; exit 1; }

# ---- copia de seguridad verificada
RUTAS=()
for f in "$RUTAS_NGINX" "$SITIO_NGINX" /etc/bricohams/google /etc/bricohams/google-auth.env \
         /etc/systemd/system/bricohams-google-auth.service "$UNIDAD_APLICAR" \
         /usr/local/bin/bricohams-google-auth /usr/local/bin/bricohams-mesh-admin \
         "$KIT_ENV" /etc/bricohams/bricohams.env "$KIT/files/bin/bricohams-google-auth" \
         "$KIT/files/bin/bricohams-mesh-admin" "$OWRX_USERS"; do
    [[ -e "$f" ]] && RUTAS+=("${f#/}")
done
B="/var/backups/bricohams/google-auth-$(date +%Y%m%d-%H%M%S)-$$"
install -d -m 700 "$B"
printf '%s\n' "${RUTAS[@]}" >"$B/archivos.txt"
tar --acls --xattrs -czf "$B/previo.tar.gz" -C / -T "$B/archivos.txt"
tar --compare --gzip --file "$B/previo.tar.gz" -C /
sha256sum "$B/previo.tar.gz" >"$B/previo.tar.gz.sha256"
sha256sum -c "$B/previo.tar.gz.sha256"
cat >"$B/RESTAURAR.sh" <<'EOF'
#!/bin/bash
# Deja la estación como antes del despliegue del acceso con Google.
set -Eeuo pipefail
[[ $EUID -eq 0 ]] || exit 1
B="$(cd "$(dirname "$0")" && pwd)"
sha256sum -c "$B/previo.tar.gz.sha256"
en() { grep -qx "$1" "$B/archivos.txt"; }
systemctl disable --now bricohams-google-auth 2>/dev/null || true
en etc/systemd/system/bricohams-google-auth.service || rm -f /etc/systemd/system/bricohams-google-auth.service
en etc/systemd/system/bricohams-google-auth-aplicar.service || rm -f /etc/systemd/system/bricohams-google-auth-aplicar.service
en etc/bricohams/google || rm -rf /etc/bricohams/google
en etc/bricohams/google-auth.env || rm -f /etc/bricohams/google-auth.env
en usr/local/bin/bricohams-google-auth || rm -f /usr/local/bin/bricohams-google-auth
tar --acls --xattrs -xzf "$B/previo.tar.gz" -C /
systemctl daemon-reload
if en etc/systemd/system/bricohams-google-auth.service; then systemctl enable --now bricohams-google-auth || true; fi
systemctl restart bricohams-mesh-admin || true
nginx -t && systemctl reload nginx
echo "Restaurado desde $B (nginx, panel, credenciales de Google, unidades, bricohams.env y users.json de OpenWebRX+)."
EOF
chmod 700 "$B/RESTAURAR.sh"
bash -n "$B/RESTAURAR.sh"
echo "BACKUP_VERIFICADO=$B"
echo "RESTAURACION: sudo bash $B/RESTAURAR.sh"

restaurar() {
    echo "ERROR: algo ha fallado; restaurando el estado anterior..." >&2
    bash "$B/RESTAURAR.sh" >&2 || echo "LA RESTAURACIÓN AUTOMÁTICA FALLÓ: sudo bash $B/RESTAURAR.sh" >&2
}
trap 'restaurar' ERR

# ---- instalación
install -m 755 "$BIN" /usr/local/bin/bricohams-google-auth
install -m 755 "$ADMIN" /usr/local/bin/bricohams-mesh-admin
if [[ -d "$KIT/files/bin" ]]; then
    install -m 755 "$BIN" "$KIT/files/bin/bricohams-google-auth"
    install -m 755 "$ADMIN" "$KIT/files/bin/bricohams-mesh-admin"
fi
/usr/local/bin/bricohams-google-auth instalar-aplicar --kit-env "$KIT_ENV"
systemctl daemon-reload
systemctl restart bricohams-mesh-admin
if [[ "$OPCION" = --configurar ]]; then
    echo "== Datos del cliente OAuth de Google (el secreto no se muestra ni queda en el registro)"
    /usr/local/bin/bricohams-google-auth configurar --kit-env "$KIT_ENV" || true
fi
ACTIVO=$(leer GOOGLE_AUTH | tail -n1)
if [[ "$ACTIVO" = yes ]]; then
    # mismo camino que usa el panel: preparar, servicio, nginx (con marcha atrás propia si nginx -t falla)
    systemctl start bricohams-google-auth-aplicar.service
fi
nginx -t
for _ in $(seq 1 20); do
    systemctl is-active --quiet bricohams-mesh-admin && break
    sleep 0.5
done
systemctl is-active --quiet bricohams-mesh-admin || { echo "bricohams-mesh-admin no arranca." >&2; false; }
sleep 1

# ---- comprobación: receptor abierto, panel vivo y, si Google está activo, según el modo
URL="https://${DOM:-localhost}"
RES=()
[[ -n "$DOM" ]] && RES=(--resolve "$DOM:443:127.0.0.1")
r=$(curl -sk -o /dev/null -w '%{http_code}' "${RES[@]}" "$URL/")
p=$(curl -sk -o /dev/null -w '%{http_code}' "${RES[@]}" "$URL/settings/bricohams/seguridad")
echo "Receptor /: $r · panel Seguridad sin sesión: $p"
[[ "$r" = 200 ]] || { echo "El receptor no responde 200 por HTTPS." >&2; false; }
[[ "$p" =~ ^(302|401|403)$ ]] || { echo "El panel Seguridad no responde como se espera." >&2; false; }
if [[ "$ACTIVO" = yes ]]; then
    MODO=$(leer GOOGLE_AUTH_MODO | tail -n1)
    cat /etc/bricohams/google/estado.json 2>/dev/null || true
    g=$(curl -sk -o /dev/null -w '%{http_code}' "${RES[@]}" "$URL/_bh_google/auth")
    echo "Pasarela por nginx (/_bh_google/auth sin sesión): $g · modo ${MODO:-alternativa}"
    [[ "$g" = 401 ]] || { echo "La pasarela de Google no responde por nginx." >&2; false; }
    if [[ "${MODO:-alternativa}" = alternativa ]]; then
        curl -sk "${RES[@]}" "$URL/login" | grep -q 'Entrar con Google' \
            || { echo "El botón «Entrar con Google» no aparece en /login." >&2; false; }
        echo "/login ofrece usuario local o «Entrar con Google»."
    else
        s=$(curl -sk -o /dev/null -w '%{http_code} %{redirect_url}' "${RES[@]}" "$URL/settings")
        echo "/settings: $s"
        [[ "$s" = "302 https://accounts.google.com/"* ]] || { echo "/settings no redirige a Google." >&2; false; }
    fi
fi
trap - ERR

/usr/local/bin/bricohams-google-auth comprobar --kit-env "$KIT_ENV" || true
echo "Listo. Configura el método de acceso en $URL/settings/bricohams/seguridad → «Métodos de acceso de administradores»."
echo "Emergencia (volver a solo usuarios locales): sudo bricohams-google-auth configurar --kit-env $KIT_ENV --desactivar && sudo bricohams-google-auth aplicar --kit-env $KIT_ENV"