#!/bin/bash
# =====================================================================
#  BricoHams SDR · EA5KAO · Mi QTH (Región de Murcia)
#  Instalación y restauración COMPLETA desde una Raspberry Pi 5 limpia
#  con Raspberry Pi OS Lite 64 bits: Debian 13 "Trixie" (actual) o
#  Debian 12 "Bookworm" (Legacy). El instalador detecta cuál es (v3.1).
#
#  Deja preparado (detalles en docs/ARQUITECTURA.md):
#   - OpenWebRX+ con todos los receptores y perfiles:
#       🛰️ SATÉLITES  RTL-SDR del HAT HackerGadgets (R860, TCXO)
#       🟢 RADIOAFIC. Mini RTL-SDR HackerGadgets (R860, TCXO)
#       🔵 MULTIPERF. RTL-SDR Blog V3 + HF 160-6 m por muestreo directo
#       🟡 HF         SDRplay (preparado, se activa con HF_SDRPLAY=yes)
#   - ADS-B: FlightStick de RadarBox con readsb + rbfeeder + MLAT + tar1090.
#   - HAT HackerGadgets: RTC PCF85063A, GPS + PPS (gpsd + chrony) y
#     LoRa SX1262 868 como nodo Meshtastic (meshtasticd).
#   - LilyGO T3 V1.6.1 433 por USB: nodo Meshtastic EU_433 e iGate LoRa
#     APRS (CA2RXU), con nombres fijos /dev/lilygo-mesh y /dev/lilygo-igate.
#   - Sensor BME280/BMP280 por I2C: tiempo propio en la web y estación
#     WX APRS (EA5KAO-13).
#   - Cámara CSI WPI408 (OV5647 + IR) con MediaMTX y foto para la web.
#   - Plugins: rig_skin (DX cluster), solar, meteo (sensor + AEMET +
#     Open-Meteo), cámara e imagen BricoHams con Murcia; marcadores.
#   - v3: viento (RS485) y lluvia (GPIO) en la estación WX, ventiladores de
#     la caja con PWM y tacómetro (bricohams-fan), cámara CSI o IP (RTSP).
#   - v4: con el HAT no quedan GPIO: sensores y ventiladores en una Pico por USB
#     (bricohams-io); satélites con aviso de pases y Doppler; FT2 (experimental);
#     nginx + SSL, portal de servicios, privacidad; visitas por MQTT con avisos
#     por Telegram; cuenta de servicio «bricohams» y tareas en cron.
#   - v4.1: «--actualizar»: kit (git) + bricohams.env + apt + solo los pasos cambiados.
#   - v4.2: bricohams.env leído sin ejecutarse, espera de red, SSL solo en la administración
#     (SSL_MODO), plugins de audio FILTRO y DSP, perfiles de OpenWebRX+ con owrx-clone.
#   - Herramientas: bricohams-check, bricohams-sdr-serials, bricohams-lilygo,
#     bricohams-servicios, bricohams-io, bricohams-ft2, owrx-clone.
#
#  Uso:
#    sudo bash install.sh                      # todo (vale aunque falte el permiso de ejecución)
#    sudo bash install.sh                         # igual, si install.sh es ejecutable
#    sudo bash install.sh --backup copia.tar.gz   # además restaura usuarios/marcadores de una copia
#    sudo bash install.sh --solo hat,meshtastic   # solo esos pasos
#    sudo bash install.sh --lista                 # ver los pasos
#    sudo bash install.sh --actualizar            # v4.1: actualiza kit (git) + sistema (apt) y
#                                                 # repite SOLO los pasos que han cambiado
#    sudo bash install.sh --actualizar --simular  # enseña qué haría, sin cambiar nada
#       opciones de --actualizar: --sin-git  --sin-apt  --todo (repite todos los pasos)
#    sudo bash install.sh --exportar [fichero]     # v4.2: perfil de este OpenWebRX+ (owrx-clone)
#    sudo bash install.sh --importar perfil.owrx.tar.gz   # v4.2: instala y aplica un perfil
#  Se puede repetir sin miedo: cada paso deja el sistema igual.
#  Registro: /var/log/bricohams-install.log
# =====================================================================
set -Eeuo pipefail

KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES="$KIT/files"
LOG=/var/log/bricohams-install.log
HTDOCS=/usr/lib/python3/dist-packages/htdocs
OWRX_DATA=/var/lib/openwebrx
OWRX_ETC=/etc/openwebrx
ETC_BH=/etc/bricohams
BOOTCFG=/boot/firmware/config.txt
CMDLINE=/boot/firmware/cmdline.txt
PASOS=(comprobar base red arranque hat openwebrx rtlsdr sdrplay configuracion plugins meteo io sensor camara ventilacion adsb meshtastic lilygo satelites ft2 web visitas herramientas importar tareas)
BACKUP=""
SOLO=""
REINICIAR=0
ARGS=("$@")                     # para volver a lanzarse si --actualizar trae un install.sh nuevo
ACTUALIZAR=0; SIMULAR=0; TODO=0; SIN_GIT=0; SIN_APT=0; CONTINUAR=0; OWRX_CAMBIO=0
IMPORTAR=""; EXPORTAR=""; EXPORTAR_A=""      # v4.2 · perfiles de OpenWebRX+ (owrx-clone)
PERFIL_IMPORTADO=/etc/bricohams/perfil-importado
ESTADO_KIT=/var/lib/bricohams/kit-estado      # huella de cada paso aplicado (v4.1)
KIT_ANTES="${BRICOHAMS_KIT_ANTES:-}"; KIT_DESPUES=""; PLAN=()
LOCATOR_CATALOG_PATH=""; STATION_QTH_LOCATOR=""; LOCATOR_DERIVADAS=()
LOCATOR_CACHE=/var/lib/bricohams/locator    # v4.3 · AEMET y FM de la zona bajados en la Pi

c_ok=$'\e[32m'; c_ko=$'\e[31m'; c_av=$'\e[33m'; c_b=$'\e[1m'; c_0=$'\e[0m'
info()  { printf '%s==>%s %s\n' "$c_b" "$c_0" "$*"; }
bien()  { printf '  %s✔%s %s\n' "$c_ok" "$c_0" "$*"; }
aviso() { printf '  %s!%s %s\n' "$c_av" "$c_0" "$*"; }
fallo() { printf '%s✘ %s%s\n' "$c_ko" "$*" "$c_0" >&2; exit 1; }
trap 'printf "%s✘ Error en la línea %s (paso %s). Mira %s%s\n" "$c_ko" "$LINENO" "${PASO_ACTUAL:-?}" "$LOG" "$c_0" >&2' ERR

while [ $# -gt 0 ]; do
    case "$1" in
        --backup) BACKUP="$2"; shift 2 ;;
        --solo)   SOLO="$2"; shift 2 ;;
        --lista)  printf '%s\n' "${PASOS[@]}"; exit 0 ;;
        --actualizar) ACTUALIZAR=1; shift ;;
        --simular)    SIMULAR=1; shift ;;
        --todo)       TODO=1; shift ;;
        --sin-git)    SIN_GIT=1; shift ;;
        --sin-apt)    SIN_APT=1; shift ;;
        --continuar)  CONTINUAR=1; shift ;;     # interno: segunda vuelta tras bajar un install.sh nuevo
        --importar)   [ -n "${2:-}" ] || fallo "--importar necesita el fichero del perfil"
                      IMPORTAR=$(readlink -f -- "$2" || echo "$2"); shift 2 ;;
        --exportar)   EXPORTAR=1; shift
                      if [ -n "${1:-}" ] && [ "${1#-}" = "$1" ]; then EXPORTAR_A=$1; shift; fi ;;
        -h|--help) awk 'NR>2 && /^# =====/{exit} NR>2' "$0"; exit 0 ;;
        *) fallo "Opción desconocida: $1" ;;
    esac
done

{ [ "$SIMULAR" -eq 0 ] && [ "$TODO" -eq 0 ] && [ "$SIN_GIT" -eq 0 ] && [ "$SIN_APT" -eq 0 ]; } || [ "$ACTUALIZAR" -eq 1 ] \
    || fallo "--simular, --todo, --sin-git y --sin-apt van con --actualizar"
[ "$ACTUALIZAR" -eq 0 ] || [ -z "$BACKUP$SOLO$IMPORTAR" ] || fallo "--actualizar no se combina con --backup, --solo ni --importar"
[ -z "$IMPORTAR" ] || [ -r "$IMPORTAR" ] || fallo "No puedo leer el perfil $IMPORTAR"
[ "$(id -u)" -eq 0 ] || fallo "Ejecútalo con sudo: sudo bash $0"
# Si el kit se copió por Windows, un móvil, un pendrive FAT o un unzip que no guarda
# permisos, los scripts pierden el bit de ejecución ("sudo: ./install.sh: command not found")
# y los ficheros de texto pueden traer finales de línea CRLF. Se reparan aquí.
arreglar_kit() {
    local f
    chmod +x "$KIT/install.sh" "$FILES"/bin/* "$KIT"/tools/*.sh "$KIT"/tests/*.sh "$KIT"/owrx-clone/owrx-clone "$KIT"/owrx-clone/instalar.sh 2>/dev/null || true
    for f in "$KIT/bricohams.env" "$KIT/install.sh" "$FILES"/bin/* "$KIT"/owrx-clone/owrx-clone "$KIT"/owrx-clone/instalar.sh; do
        if [ -f "$f" ] && grep -q $'\r' "$f"; then sed -i 's/\r$//' "$f"; fi
    done
}
arreglar_kit
# v4.2 · exportar no necesita bricohams.env: vale en cualquier OpenWebRX+ (owrx-clone)
if [ -n "$EXPORTAR" ]; then
    # v4.3 · si bricohams.env dice OWRX_BACKEND="docker", se exporta el contenedor
    EXP_DOCKER=""
    if [ -r "$KIT/bricohams.env" ]; then
        eval "$(python3 "$FILES/bin/bricohams-env.py" --shell "$KIT/bricohams.env" 2>/dev/null | grep -E '^export (OWRX_BACKEND|OWRX_DOCKER_CONTAINER)=' || true)"
        if [ "${OWRX_BACKEND:-native}" = docker ]; then EXP_DOCKER=${OWRX_DOCKER_CONTAINER:-owrx-mbe}; fi
    fi
    exec python3 "$KIT/owrx-clone/owrx-clone" ${EXP_DOCKER:+--docker "$EXP_DOCKER"} exportar ${EXPORTAR_A:+-o "$EXPORTAR_A"}
fi
[ -r "$KIT/bricohams.env" ] || fallo "Falta $KIT/bricohams.env: cp bricohams.env.example bricohams.env y rellena las claves (docs/manuales/02_INSTALACION.md)"
# v4.3 · Zona de la estación según el locator (manual 32, ADR-43). STATION_LOCATOR da las
# coordenadas si STATION_LAT/LON están vacías o a 0 (si las pones, mandan: son más precisas).
# Con LOCATOR_CATALOG (por defecto el catálogo de España del kit) se eligen los aeropuertos,
# estaciones AEMET, puertos, NAVTEX y emisoras de FM más cercanos.
coords_ok() { awk -v a="${STATION_LAT:-0}" -v b="${STATION_LON:-0}" 'BEGIN { exit !((a + 0) != 0 || (b + 0) != 0) }'; }
zona_locator() {
    local c
    # si una pasada anterior sacó las coordenadas del locator, siguen siendo «del locator»
    # (paso_meteo lo vuelve a llamar sin releer bricohams.env)
    if [ "${COORDS_DEL_LOCATOR:-0}" = 1 ]; then STATION_LAT=0; STATION_LON=0; fi
    COORDS_DEL_LOCATOR=0
    STATION_QTH_LOCATOR=""; LOCATOR_CATALOG_PATH=""; LOCATOR_DERIVADAS=()
    if [ -n "${STATION_LOCATOR:-}" ]; then
        c=$(python3 "$FILES/bin/bricohams_locator.py" "$STATION_LOCATOR") || fallo "STATION_LOCATOR=$STATION_LOCATOR no es un locator Maidenhead válido (4, 6, 8 o 10 caracteres, p. ej. IM97kx)"
        if ! coords_ok; then
            read -r STATION_LAT STATION_LON <<<"$c"; export STATION_LAT STATION_LON
            LOCATOR_DERIVADAS+=(STATION_LAT STATION_LON); COORDS_DEL_LOCATOR=1
        elif [ -z "${_ZONA_AVISADA:-}" ] && ! python3 -c 'import sys; sys.path.insert(0, sys.argv[1]); from bricohams_locator import dentro_de_celda as d; sys.exit(0 if d(sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), 5) else 1)' \
                "$FILES/bin" "$STATION_LOCATOR" "$STATION_LAT" "$STATION_LON"; then
            aviso "STATION_LAT/LON ($STATION_LAT, $STATION_LON) no caen en STATION_LOCATOR=$STATION_LOCATOR: uso las coordenadas (revisa cuál está mal)"
        fi
        STATION_QTH_LOCATOR=${STATION_LOCATOR^^}
    elif coords_ok; then
        STATION_QTH_LOCATOR=$(python3 "$FILES/bin/bricohams_locator.py" --a-locator "$STATION_LAT" "$STATION_LON") || STATION_QTH_LOCATOR=""
    fi
    if [ -n "$STATION_QTH_LOCATOR" ] && [ -z "${_ZONA_AVISADA:-}" ]; then
        python3 "$FILES/bin/bricohams_locator.py" --espana "$STATION_QTH_LOCATOR" >/dev/null \
            || aviso "El locator $STATION_QTH_LOCATOR cae fuera de España: el catálogo de zona del kit es de España (manual 32)"
    fi
    if [ -n "${LOCATOR_CATALOG:-}" ]; then
        if [ -z "$STATION_QTH_LOCATOR" ]; then
            [ -n "${_ZONA_AVISADA:-}" ] || aviso "LOCATOR_CATALOG necesita STATION_LOCATOR (o STATION_LAT/LON): sin marcadores de zona"
        else
            if [[ "$LOCATOR_CATALOG" = /* ]]; then LOCATOR_CATALOG_PATH=$LOCATOR_CATALOG
            else LOCATOR_CATALOG_PATH=$KIT/$LOCATOR_CATALOG; fi
            [ -r "$LOCATOR_CATALOG_PATH" ] || fallo "No puedo leer LOCATOR_CATALOG=$LOCATOR_CATALOG_PATH"
            if [[ ! "${LOCATOR_METEO:-yes}" =~ ^([Nn][Oo]?|0|false)$ ]]; then    # (si() aún no existe aquí)
                local estaciones
                estaciones=$(zona_selector --meteo-stations) || fallo "No pude seleccionar servicios cercanos desde LOCATOR_CATALOG"
                if [ -n "$estaciones" ]; then METEO_STATIONS=$estaciones; export METEO_STATIONS; LOCATOR_DERIVADAS+=(METEO_STATIONS); fi
            fi
        fi
    fi
    export STATION_QTH_LOCATOR
    _ZONA_AVISADA=1
}
# zona_selector ARGS… : el selector de bricohams_locator_bookmarks.py con los ajustes de bricohams.env
zona_selector() {
    local a=(--locator "$STATION_QTH_LOCATOR" --catalog "$LOCATOR_CATALOG_PATH"
             --radius-km "${LOCATOR_RADIUS_KM:-100}" --max-sites "${LOCATOR_MAX_SITES:-3}"
             --radios-max "${LOCATOR_RADIOS_MAX:-30}" --radios "${LOCATOR_RADIOS:-regional,local}")
    if coords_ok; then a+=(--lat "$STATION_LAT" --lon "$STATION_LON"); fi
    if [ -d "$LOCATOR_CACHE" ]; then a+=(--online-cache "$LOCATOR_CACHE"); fi
    python3 "$FILES/bin/bricohams_locator_bookmarks.py" "${a[@]}" "$@"
}
# v4.2 · bricohams.env se LEE, no se ejecuta: un «$» dentro de una clave
# (QRZ_PASS="abc$Clave2026") paraba el instalador con «unbound variable».
# bricohams-env.py entiende comillas dobles, simples y comentarios, y toma el «$» literal.
cargar_env() {
    local salida
    command -v python3 >/dev/null || fallo "Falta python3 (viene con Raspberry Pi OS): sudo apt install python3"
    salida=$(python3 "$FILES/bin/bricohams-env.py" --shell "$1") || fallo "$1 tiene un error de sintaxis (arriba). Revisa las comillas de esa línea."
    eval "$salida"
    COORDS_DEL_LOCATOR=0                     # recién leído: las coordenadas son las del fichero
    zona_locator
    case "${OWRX_BACKEND:-native}" in
        native) HTDOCS=/usr/lib/python3/dist-packages/htdocs; OWRX_DATA=/var/lib/openwebrx; OWRX_ETC=/etc/openwebrx ;;
        docker)
            OWRX_DOCKER_DIR=${OWRX_DOCKER_DIR:-/opt/owrx-docker}
            HTDOCS=$OWRX_DOCKER_DIR
            OWRX_DATA=$OWRX_DOCKER_DIR/var
            OWRX_ETC=$OWRX_DOCKER_DIR/etc
            ;;
        *) fallo "OWRX_BACKEND debe ser native o docker" ;;
    esac
}
owrx_control() {
    local action=$1
    if [ "${OWRX_BACKEND:-native}" = docker ]; then
        docker "$action" "${OWRX_DOCKER_CONTAINER:-owrx-mbe}" >/dev/null
    else
        systemctl "$action" openwebrx
    fi
}
# v4.3 · en Docker el paquete no crea el usuario «openwebrx» en la Pi: lo necesitan los servicios del host
usuario_openwebrx() {
    getent passwd openwebrx >/dev/null || useradd --system --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin openwebrx
}
owrx_owner() {
    if [ "${OWRX_BACKEND:-native}" = docker ]; then
        usuario_openwebrx
        # v4.3 · OpenWebRX+ corre como root DENTRO del contenedor (lee todo); en la Pi las carpetas son
        # del usuario «openwebrx» del sistema para que los servicios del host (meteo, cámara, visitas…)
        # escriban en plugins/ igual que en la instalación nativa.
        chown -R openwebrx:openwebrx "$OWRX_DATA" "$HTDOCS/plugins"
    else
        chown -R openwebrx:openwebrx "$OWRX_DATA"
    fi
}
# v4.3 · Docker: «docker compose» (plugin) o «docker-compose» (Bookworm)
docker_compose() {
    if docker compose version >/dev/null 2>&1; then docker compose "$@"
    elif command -v docker-compose >/dev/null; then docker-compose "$@"
    else fallo "Falta docker compose (sudo apt install docker-compose)"; fi
}
esperar_owrx() {   # esperar_owrx SEGUNDOS: hasta que /status.json responda en el 8073 (o el puerto publicado)
    local fin=$((SECONDS + ${1:-60})) p=8073
    [ "${OWRX_DOCKER_RED:-host}" = bridge ] && p=${OWRX_DOCKER_PORT:-8073}
    while [ "$SECONDS" -lt "$fin" ]; do
        curl -fsS -o /dev/null --max-time 3 "http://127.0.0.1:$p/status.json" && return 0
        sleep 3
    done
    return 1
}
# v4.3 · despliega (o actualiza) el contenedor de OpenWebRX+ con el docker-compose.yaml del kit
docker_preparar() {
    local dir=$OWRX_DOCKER_DIR c=${OWRX_DOCKER_CONTAINER:-owrx-mbe} yml
    if ! command -v docker >/dev/null; then
        info "Instalo Docker (paquete docker.io de Debian)"
        apt_update
        apt_i docker.io || fallo "No pude instalar docker.io"
    fi
    if ! docker compose version >/dev/null 2>&1 && ! command -v docker-compose >/dev/null; then
        apt_i docker-compose || fallo "No pude instalar docker-compose"
    fi
    systemctl enable --now docker >/dev/null 2>&1 || true
    # el paquete nativo y el contenedor no pueden convivir: los dos quieren el puerto 8073 y los SDR
    if systemctl is-enabled --quiet openwebrx 2>/dev/null || systemctl is-active --quiet openwebrx 2>/dev/null; then
        aviso "Paro y desactivo el OpenWebRX+ nativo: el de Docker usa el 8073 y los SDR. Sus datos siguen en /var/lib/openwebrx (pásalos con owrx-clone, manual 33)"
        systemctl disable --now openwebrx || true
    fi
    usuario_openwebrx
    install -d -m 755 "$dir" "$dir/etc" "$dir/var" "$dir/plugins" "$dir/plugins/receiver" "$dir/plugins/map"
    if docker inspect "$c" >/dev/null 2>&1 && [ ! -f "$dir/docker-compose.yaml" ]; then
        aviso "El contenedor '$c' ya existía (no lo creó BricoHams): lo uso tal cual, sin docker-compose.yaml del kit"
        [ "$(docker inspect --format '{{.State.Running}}' "$c")" = true ] || docker start "$c" >/dev/null
        return 0
    fi
    yml=$(mktemp)
    OWRX_DOCKER_DIR=$dir python3 "$FILES/bin/bricohams-docker-compose.py" >"$yml" || { rm -f "$yml"; fallo "Revisa OWRX_DOCKER_* en bricohams.env (arriba)"; }
    install -m 644 "$yml" "$dir/docker-compose.yaml"; rm -f "$yml"
    if si "${OWRX_DOCKER_ACTUALIZAR:-yes}"; then
        (cd "$dir" && docker_compose pull) || aviso "No pude bajar la imagen ${OWRX_DOCKER_IMAGE:-slechev/openwebrxplus-softmbe:latest}: uso la que haya"
    fi
    (cd "$dir" && docker_compose up -d --remove-orphans) || fallo "docker compose up ha fallado en $dir (docker logs $c)"
    if esperar_owrx 180; then bien "contenedor $c en marcha ($(docker inspect --format '{{.Config.Image}}' "$c"))"
    else aviso "OpenWebRX+ (Docker) aún no responde: docker logs $c"; fi
}
owrx_admin_adduser() {
    if [ "${OWRX_BACKEND:-native}" = docker ]; then
        docker exec -it "${OWRX_DOCKER_CONTAINER:-owrx-mbe}" openwebrx admin adduser "$1"
    else
        openwebrx admin adduser "$1"
    fi
}
owrx_docker_mount() {
    docker inspect --format "{{range .Mounts}}{{if eq .Destination \"$1\"}}{{.Source}}{{end}}{{end}}" \
        "${OWRX_DOCKER_CONTAINER:-owrx-mbe}"
}
# copia en /etc ya «limpia» (comillas simples): la pueden leer bash y systemd sin sorpresas
instalar_env() {   # el temporal también es 600: lleva todas las claves
    local tmp; tmp=$(umask 077; mktemp "$1.XXXXXX")
    python3 "$FILES/bin/bricohams-env.py" --normalizar "$KIT/bricohams.env" >"$tmp" || { rm -f "$tmp"; fallo "bricohams.env tiene un error (arriba)"; }
    {   # v4.3 · lo que calcula el instalador (vale lo último: bash, systemd y bricohams-env.py)
        local v
        echo "# --- calculadas por install.sh (locator y backend de OpenWebRX+): no las edites aquí"
        for v in "${LOCATOR_DERIVADAS[@]}"; do envl "$v" "${!v}"; done
        if [ -n "${STATION_QTH_LOCATOR:-}" ]; then envl STATION_QTH_LOCATOR "$STATION_QTH_LOCATOR"; fi
        envl OWRX_DATA "$OWRX_DATA"; envl OWRX_ETC "$OWRX_ETC"; envl OWRX_HTDOCS "$HTDOCS"
        if [ "${OWRX_BACKEND:-native}" = docker ]; then envl OWRX_CLONE_DOCKER "${OWRX_DOCKER_CONTAINER:-owrx-mbe}"; fi
    } >>"$tmp"
    chmod 600 "$tmp"; mv -f "$tmp" "$1"
    # v4.3 · lo que no es secreto, legible sin sudo (bricohams-locator): zona y backend
    grep -E '^(STATION_[A-Z_]*|LOCATOR_[A-Z_]*|METEO_STATIONS|OWRX_BACKEND|OWRX_DOCKER_[A-Z_]*|OWRX_DATA|OWRX_ETC|OWRX_HTDOCS|OWRX_CLONE_DOCKER)=' "$1" \
        >"$(dirname "$1")/zona.env" || true
    chmod 644 "$(dirname "$1")/zona.env"
}
# NOMBRE='valor' para los .env derivados (systemd EnvironmentFile y bash los leen igual)
sq() { local s=${1//\'/\'\\\'\'}; printf "'%s'" "$s"; }
envl() { printf '%s=%s\n' "$1" "$(sq "${2-}")"; }
# nginx_sitio MODO DOMINIO CERT KEY < plantilla: activa o borra las líneas «#@X@» de la plantilla
nginx_sitio() {
    local m=$1 dom=$2 cert=$3 key=$4 e=()
    case "$m" in
        admin) e=(-e 's/^#@ADMIN@//' -e 's/^#@HTTP@//' -e '/^#@TODO@/d' -e '/^#@SSL[<>]/d') ;;
        todo)  e=(-e 's/^#@TODO@//' -e '/^#@ADMIN@/d' -e '/^#@HTTP@/d' -e '/^#@SSL[<>]/d') ;;
        no)    e=(-e 's/^#@HTTP@//' -e '/^#@ADMIN@/d' -e '/^#@TODO@/d' -e '/^#@SSL>/,/^#@SSL</d') ;;
        *) return 1 ;;
    esac
    sed "${e[@]}" -e "s#__DOMINIO__#${dom}#g" -e "s#__CERT__#${cert}#" -e "s#__KEY__#${key}#"
}
cargar_env "$KIT/bricohams.env"
DEB=$(. /etc/os-release && echo "${VERSION_CODENAME:-}")   # bookworm | trixie: elige los repositorios
DEB_NUM=$([ "$DEB" = trixie ] && echo 13 || echo 12)
# al volver a lanzarse (--actualizar con install.sh nuevo) la salida ya va al registro
[ -n "${BRICOHAMS_LOG_ACTIVO:-}" ] || exec > >(tee -a "$LOG") 2>&1
echo; info "BricoHams SDR · $([ "$ACTUALIZAR" -eq 1 ] && echo actualización || echo instalación) $(date '+%F %T')"

apt_i() { DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "$@"; }
# apt-get update robusto (v3.2): si falla (p. ej. IPv6 sin salida a Internet, "Network is
# unreachable" con archive.raspberrypi.com), se fuerza IPv4 para apt y se reintenta.
apt_update() {
    apt-get update && return 0
    if [ ! -f /etc/apt/apt.conf.d/99bricohams-ipv4 ]; then
        aviso "apt-get update ha fallado: fuerzo IPv4 para apt (/etc/apt/apt.conf.d/99bricohams-ipv4) y reintento"
        echo 'Acquire::ForceIPv4 "true";' >/etc/apt/apt.conf.d/99bricohams-ipv4
    fi
    local i
    for i in 1 2 3; do
        apt-get update && return 0
        aviso "apt-get update: intento $i fallido; espero 10 s"; sleep 10
    done
    fallo "apt-get update sigue fallando. Prueba la red: getent ahostsv4 archive.raspberrypi.com · curl -4 -sI http://archive.raspberrypi.com/debian/dists/$DEB/Release"
}
# v4.2 · Red: espera a que haya DNS y salida antes de bajar nada. En la Pi de EA5KAO el
# paso «red» reactivaba el WiFi y el paso «openwebrx» fallaba con «Could not resolve host».
esperar_red() {
    local i
    for i in $(seq 1 24); do
        if getent hosts luarvique.github.io >/dev/null 2>&1 && getent hosts deb.debian.org >/dev/null 2>&1; then
            if [ "$i" -gt 1 ]; then bien "red disponible tras $(( (i - 1) * 5 )) s"; fi
            return 0
        fi
        [ "$i" -gt 1 ] || aviso "Esperando a la red (DNS)…"
        sleep 5
    done
    aviso "Sin DNS tras 2 minutos. Estado de la red:"
    nmcli -t -f DEVICE,STATE,CONNECTION device 2>/dev/null | sed 's/^/    /' || true
    grep -E '^nameserver' /etc/resolv.conf 2>/dev/null | sed 's/^/    /' || true
    fallo "No se resuelve luarvique.github.io ni deb.debian.org. Comprueba el WiFi/cable y repite: el instalador sigue donde se quedó"
}
# ¿El paso baja algo? (apt, curl, git, pip…): solo esos esperan a la red. «red» y «comprobar» la miran ellos.
necesita_red() {
    case "$1" in red|comprobar) return 1 ;; esac
    declare -f "paso_$1" | grep -qE 'apt_i|apt_update|apt-get|CURL|curl |wget|git (clone|pull|fetch)|pipx|pip3? install|script_remoto|clave_apt|certbot|owrx-clone'
}
# curl con reintentos (cortes de red, DNS que tarda, GitHub lento)
CURL=(curl -fsSL --retry 5 --retry-delay 3 --retry-all-errors --connect-timeout 20)
# script_remoto URL [args]: baja un instalador de terceros y lo ejecuta. Antes era
# «bash -c $(wget …)»: si la descarga fallaba, bash ejecutaba un texto vacío y
# el paso seguía como si nada (sin readsb, sin tar1090…).
script_remoto() {
    local url=$1 tmp r; shift
    tmp=$(mktemp --suffix=.sh)
    esperar_red
    "${CURL[@]}" -o "$tmp" "$url" && [ -s "$tmp" ] || { rm -f "$tmp"; echo "No pude bajar $url" >&2; return 1; }
    r=0; bash "$tmp" "$@" || r=$?
    rm -f "$tmp"; return "$r"
}
# clave_apt URL DESTINO: baja una clave de repositorio y la convierte a formato gpg binario
clave_apt() {
    local tmp; tmp=$(mktemp)
    esperar_red
    "${CURL[@]}" -o "$tmp" "$1" || { rm -f "$tmp"; fallo "No pude bajar la clave $1 (¿red?). Repite el instalador: sigue donde se quedó"; }
    [ -s "$tmp" ] || { rm -f "$tmp"; fallo "La clave $1 ha llegado vacía"; }
    gpg --yes --dearmor -o "$2" "$tmp" || { rm -f "$tmp"; fallo "La clave $1 no es una clave OpenPGP válida"; }
    rm -f "$tmp"
}
# v3.3 · Trixie: el rtl-sdr de Debian 13 (osmocom 2.0.2) es MÁS NUEVO que el fork rtl-sdr-blog
# (0.7.0~rtlsdrblog1) y los módulos SoapySDR de Trixie lo exigen. Si quedó instalado/retenido el
# fork (de una instalación anterior), apt no puede resolver dependencias: se pasa a la versión de
# Debian, que ya trae bias-tee, muestreo directo y el R820T/R860 de los cuatro SDR.
rtlsdr_debian() {
    local v
    v=$(dpkg-query -W -f='${Version}' librtlsdr0 2>/dev/null || true)
    apt-mark unhold librtlsdr0 librtlsdr-dev rtl-sdr >/dev/null 2>&1 || true
    if [ -z "$v" ] || [[ "$v" == *rtlsdrblog* ]] || dpkg-query -W -f='${Version}' rtl-sdr 2>/dev/null | grep -q rtlsdrblog; then
        aviso "rtl-sdr: cambio el fork rtl-sdr-blog (${v:-no instalado}) por el de Debian $DEB"
        DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends --allow-downgrades \
            librtlsdr0 librtlsdr-dev rtl-sdr
    fi
    dpkg-query -W -f='${Version}' librtlsdr0
}

si() { case "${1,,}" in 1|y|yes|s|si|sí|true|on) return 0 ;; *) return 1 ;; esac; }

# bloque gestionado en un fichero (entre marcadores), idempotente
bloque() {  # fichero etiqueta <contenido por stdin>
    local f=$1 tag=$2 tmp
    tmp=$(mktemp)
    touch "$f"
    awk -v b="# >>> $tag" -v e="# <<< $tag" '$0==b{s=1;next} $0==e{s=0;next} !s' "$f" >"$tmp"
    { cat "$tmp"; echo "# >>> $tag"; cat; echo "# <<< $tag"; } >"$f"
    rm -f "$tmp"
}

# =====================================================================
#  v4.1 · Actualización: sudo bash install.sh --actualizar
#  1. copia de seguridad (bricohams-backup)
#  2. kit: git pull --ff-only como el dueño de la carpeta; si llega un
#     install.sh nuevo, se vuelve a lanzar con él (--continuar)
#  3. bricohams.env: se AÑADEN las variables nuevas del .env.example con su
#     valor por defecto; las tuyas y tus claves no se tocan
#  4. sistema: apt upgrade (respeta los paquetes retenidos y tus ficheros de
#     configuración)
#  5. pasos: cada paso guarda en $ESTADO_KIT una huella de su código, de los
#     ficheros del kit que usa y de las variables de bricohams.env que lee. Solo
#     se repiten los pasos cuya huella ha cambiado (y comprobar + herramientas).
#  6. bricohams-check, aviso por Telegram y si hace falta reiniciar.
#  Si se corta a medias, se vuelve a lanzar y sigue: los pasos ya hechos tienen
#  su huella guardada.
# =====================================================================
h16() { sha256sum | cut -c1-16; }

# Ficheros del kit que usa un paso: las rutas "$FILES/…" y "$KIT/…" de su código.
ficheros_paso() {
    local ref base f
    { declare -f "paso_$1" | grep -oE '(FILES|KIT)"?/[A-Za-z0-9_./*-]+' || true; } | sort -u | while read -r ref; do
        case "$ref" in FILES*) base=$FILES ;; *) base=$KIT ;; esac
        ref=${ref#*/}
        [ "$ref" = bricohams.env ] && continue          # bricohams.env cuenta por variables, no entero
        { compgen -G "$base/$ref" || true; } | while read -r f; do
            if [ -d "$f" ]; then find "$f" -type f ! -name '*.pyc' ! -path '*/__pycache__/*'; elif [ -f "$f" ]; then echo "$f"; fi
        done
    done | sort -u
}

# Variables de bricohams.env que lee un paso. «configuracion» las usa todas (settings.json).
vars_paso() {
    local todas
    todas=$(grep -oE '^[[:space:]]*(export[[:space:]]+)?[A-Z][A-Z0-9_]*=' "$KIT/bricohams.env" | grep -oE '[A-Z][A-Z0-9_]*' | sort -u || true)
    [ -n "$todas" ] || return 0
    if [ "$1" = configuracion ]; then echo "$todas"; return 0; fi
    # v4.3 · los pasos que escriben en las carpetas de OpenWebRX+ dependen también del backend (nativo/Docker)
    { { declare -f "paso_$1" | grep -oE '\$\{?[A-Z][A-Z0-9_]*' | tr -d '${'
        if declare -f "paso_$1" | grep -qE 'HTDOCS|OWRX_DATA|OWRX_ETC|owrx_'; then printf '%s\n' OWRX_BACKEND OWRX_DOCKER_DIR; fi
      } | sort -u | grep -Fx -f <(echo "$todas") || true; }
}

# Huella de un paso: «código ficheros variables» (16 hex cada una).
huella_paso() {
    local c fh va f v
    c=$(declare -f "paso_$1" | h16)
    fh=$(ficheros_paso "$1" | while read -r f; do printf '%s %s\n' "${f#"$KIT"/}" "$(sha256sum <"$f" | cut -c1-64)"; done | h16)
    va=$(vars_paso "$1" | while read -r v; do printf '%s=%s\n' "$v" "${!v-}"; done | h16)
    echo "$c $fh $va"
}

estado_guardar() {
    local h; h=$(huella_paso "$1")
    install -d -m 755 "$(dirname "$ESTADO_KIT")"
    { grep -v "^paso $1 " "$ESTADO_KIT" 2>/dev/null || true; echo "paso $1 $h $(date +%F)"; } >"$ESTADO_KIT.tmp"
    mv "$ESTADO_KIT.tmp" "$ESTADO_KIT"; chmod 600 "$ESTADO_KIT"
}

# Por qué hay que repetir un paso (vacío si está al día).
motivo_paso() {
    local a c f v ac af av m=""
    a=$(awk -v p="$1" '$1=="paso" && $2==p {print $3" "$4" "$5}' "$ESTADO_KIT" 2>/dev/null || true)
    [ -n "$a" ] || { echo "sin registro anterior"; return 0; }
    read -r c f v <<<"$(huella_paso "$1")"
    read -r ac af av <<<"$a"
    [ "$c" = "$ac" ] || m+="código del paso, "
    [ "$f" = "$af" ] || m+="ficheros del kit, "
    [ "$v" = "$av" ] || m+="variables de bricohams.env, "
    echo "${m%, }"
}

# Añade a bricohams.env las variables del .env.example que no tiene (nunca cambia las que hay).
env_nuevas() {
    local ej="$KIT/bricohams.env.example" env="$KIT/bricohams.env" l n nuevas=()
    [ -r "$ej" ] && [ -r "$env" ] || return 0
    while IFS= read -r l; do
        [[ "$l" =~ ^([A-Z][A-Z0-9_]*)= ]] || continue
        n=${BASH_REMATCH[1]}
        grep -qE "^[[:space:]]*(export[[:space:]]+)?$n=" "$env" || nuevas+=("$l")
    done <"$ej"
    if [ ${#nuevas[@]} -eq 0 ]; then bien "bricohams.env: no faltan variables"; return 0; fi
    if [ "${1:-}" = mostrar ]; then
        aviso "bricohams.env: se añadirían ${#nuevas[@]} variables nuevas: $(printf '%s ' "${nuevas[@]%%=*}")"; return 0
    fi
    { echo; echo "# >>> añadidas por install.sh --actualizar el $(date '+%F %T'): valor por defecto del .env.example (revísalas)"
      printf '%s\n' "${nuevas[@]}"; } >>"$env"
    bien "bricohams.env: ${#nuevas[@]} variables nuevas con su valor por defecto: $(printf '%s ' "${nuevas[@]%%=*}")"
}

# git en la carpeta del kit, como su dueño (git no deja a root tocar un repositorio ajeno).
kit_g() {
    local du; du=$(stat -c %U "$KIT")
    if [ "$du" = root ]; then git -C "$KIT" "$@"; else sudo -H -u "$du" git -C "$KIT" "$@"; fi
}

kit_git() {
    local n
    if [ ! -d "$KIT/.git" ]; then
        aviso "El kit no es un clon de git: no lo puedo bajar. Copia encima el kit nuevo (tu bricohams.env no viene en él) y repite."
        return 0
    fi
    command -v git >/dev/null || { aviso "git no está instalado: me salto la descarga del kit"; return 0; }
    KIT_ANTES=$(kit_g rev-parse --short HEAD)
    if ! kit_g rev-parse --abbrev-ref '@{u}' >/dev/null 2>&1; then
        aviso "La rama del kit no sigue a ningún remoto: me salto git (git -C $KIT branch -u origin/main)"; return 0
    fi
    if [ "$SIMULAR" -eq 1 ]; then
        kit_g fetch -q || { aviso "git fetch ha fallado (¿red?)"; return 0; }
        n=$(kit_g rev-list --count 'HEAD..@{u}')
        info "kit $KIT_ANTES: $n cambios nuevos en el remoto (en --simular no se bajan)"
        kit_g log --oneline 'HEAD..@{u}' | head -20 | sed 's/^/    /'
        return 0
    fi
    kit_g pull --ff-only \
        || fallo "git pull no puede avanzar el kit. Mira «cd $KIT && git status»: si tienes cambios locales, guárdalos con «git stash»; sin red, usa --sin-git"
    KIT_DESPUES=$(kit_g rev-parse --short HEAD)
    if [ "$KIT_ANTES" = "$KIT_DESPUES" ]; then
        bien "kit: ya estaba al día ($KIT_ANTES)"; return 0
    fi
    bien "kit: $KIT_ANTES → $KIT_DESPUES"
    kit_g log --oneline "$KIT_ANTES..$KIT_DESPUES" | head -20 | sed 's/^/    /'
    if ! kit_g diff --quiet "$KIT_ANTES" "$KIT_DESPUES" -- install.sh; then
        info "Ha llegado un install.sh nuevo: sigo con él"
        arreglar_kit
        exec env BRICOHAMS_LOG_ACTIVO=1 BRICOHAMS_KIT_ANTES="$KIT_ANTES" bash "$KIT/install.sh" "${ARGS[@]}" --continuar
    fi
}

sistema_actualizar() {
    local v0 v1
    v0=$(dpkg-query -W -f='${Version}' openwebrx 2>/dev/null || true)
    apt_update
    if [ "$SIMULAR" -eq 1 ]; then
        info "Paquetes que se actualizarían:"
        apt-get -s upgrade | awk '/^Inst /{print "    " $2}' | head -40
        return 0
    fi
    if [ "$DEB" = trixie ]; then rtlsdr_debian >/dev/null; fi
    DEBIAN_FRONTEND=noninteractive apt-get -y -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold upgrade
    v1=$(dpkg-query -W -f='${Version}' openwebrx 2>/dev/null || true)
    if [ -n "$v0" ] && [ "$v0" != "$v1" ]; then
        OWRX_CAMBIO=1; bien "OpenWebRX+ $v0 → $v1 (se vuelven a aplicar plugins y FT2)"
    else
        bien "paquetes del sistema al día (OpenWebRX+ ${v1:-no instalado})"
    fi
}

plan_actualizar() {
    local p m
    local -A motivo=()
    [ -s "$ESTADO_KIT" ] || aviso "No hay huellas de una instalación anterior (estación instalada antes de la v4.1): se aplican todos los pasos, sin perder usuarios, marcadores propios ni claves."
    for p in "${PASOS[@]}"; do
        if [ "$p" = comprobar ]; then m="siempre"
        elif [ "$TODO" -eq 1 ]; then m="--todo"
        elif [ "$OWRX_CAMBIO" -eq 1 ] && { [ "$p" = plugins ] || [ "$p" = ft2 ]; }; then m="OpenWebRX+ actualizado"
        else m=$(motivo_paso "$p"); fi
        [ -z "$m" ] || motivo[$p]=$m
    done
    # si cambia algo, herramientas refresca la copia del kit en /opt/bricohams/kit
    if [ ${#motivo[@]} -gt 1 ] && [ -z "${motivo[herramientas]:-}" ]; then motivo[herramientas]="copia del kit en /opt/bricohams/kit"; fi
    PLAN=()
    for p in "${PASOS[@]}"; do
        [ -n "${motivo[$p]:-}" ] || continue
        PLAN+=("$p"); printf '    %-14s %s\n' "$p" "${motivo[$p]}"
    done
}

copia_previa() {
    local f
    if [ -x /usr/local/sbin/bricohams-backup ]; then
        f=$(/usr/local/sbin/bricohams-backup | tail -1) || fallo "La copia de seguridad ha fallado: no actualizo"
        bien "copia de seguridad: $f"
    else
        aviso "No está bricohams-backup (paso herramientas): sigo sin copia"
    fi
}

resumen_actualizacion() {
    local pasos="${PLAN[*]}"
    if [ -z "$KIT_DESPUES" ]; then
        KIT_DESPUES="sin git"
        if [ -d "$KIT/.git" ]; then KIT_DESPUES=$(kit_g rev-parse --short HEAD 2>/dev/null || echo "sin git"); fi
    fi
    echo; info "Actualización terminada"
    bien "kit: ${KIT_ANTES:-$KIT_DESPUES} → $KIT_DESPUES · pasos: ${pasos:-ninguno}"
    install -d -m 755 /var/lib/bricohams
    echo "$(date '+%F %T') kit=$KIT_DESPUES pasos=${pasos// /,}" >>/var/lib/bricohams/actualizaciones.log
    if [ ${#PLAN[@]} -gt 1 ] && command -v bricohams-check >/dev/null; then
        info "Comprobación"; bricohams-check || aviso "bricohams-check ha encontrado problemas (arriba)"
    fi
    if [ -x /usr/local/bin/bricohams-telegram ]; then
        /usr/local/bin/bricohams-telegram "🔄 Estación actualizada · kit $KIT_DESPUES · pasos: ${pasos:-ninguno}" >/dev/null 2>&1 || true
    fi
    if [ "$REINICIAR" -eq 1 ] || [ -f /var/run/reboot-required ]; then
        aviso "Hace falta reiniciar: sudo reboot"
    fi
}

# ---------------------------------------------------------------------
paso_comprobar() {
    esperar_red
    . /etc/os-release
    [ "$(uname -m)" = aarch64 ] || fallo "Hace falta Raspberry Pi OS de 64 bits (arm64)."
    case "${VERSION_CODENAME:-}" in
        bookworm|trixie) ;;
        *) fallo "Este sistema es '$PRETTY_NAME'. El kit funciona en Raspberry Pi OS Lite 64-bit Trixie (Debian 13) o Bookworm (Debian 12)." ;;
    esac
    grep -q 'Raspberry Pi 5' /proc/device-tree/model 2>/dev/null && bien "Raspberry Pi 5" || aviso "No parece una Raspberry Pi 5: los ajustes de arranque son para la Pi 5"
    if [ "${OWRX_BACKEND:-native}" = docker ]; then      # v4.3 · OpenWebRX+ viene en la imagen: no hace falta su repositorio
        bien "$PRETTY_NAME arm64 · OpenWebRX+ en Docker (${OWRX_DOCKER_IMAGE:-slechev/openwebrxplus-softmbe:latest})"
    else
        curl -fsS --max-time 15 -o /dev/null "https://luarvique.github.io/ppa/$DEB/Release" \
            || fallo "Sin Internet o sin repositorio de OpenWebRX+ para $DEB (https://luarvique.github.io/ppa/$DEB/)"
        bien "$PRETTY_NAME arm64 con Internet y repositorio de OpenWebRX+ para $DEB"
    fi
    for f in "$FILES/openwebrx/settings.json.tmpl" "$FILES/htdocs/plugins/receiver/init.js" "$FILES/branding/receiver_top_photo.png"; do
        [ -e "$f" ] || fallo "Kit incompleto: falta $f"
    done
}

paso_base() {
    apt_update
    if [ "$DEB" = trixie ]; then rtlsdr_debian >/dev/null; fi
    DEBIAN_FRONTEND=noninteractive apt-get -y full-upgrade
    apt_i git curl ca-certificates gnupg jq python3 python3-venv pipx \
        build-essential cmake pkg-config debhelper libusb-1.0-0-dev \
        i2c-tools gpsd gpsd-clients pps-tools chrony \
        ffmpeg fonts-dejavu-core rsync wget
    apt_i python3-smbus 2>/dev/null || apt_i python3-smbus2 || aviso "No pude instalar python3-smbus ni python3-smbus2 (sensor BME280)"
    apt_i rpicam-apps-lite 2>/dev/null || apt_i rpicam-apps || aviso "No pude instalar rpicam-apps (solo sirve para probar la cámara)"
    if [ -n "${HOSTNAME_NEW:-}" ] && [ "$(hostname)" != "$HOSTNAME_NEW" ]; then
        hostnamectl set-hostname "$HOSTNAME_NEW"
        sed -i "s/^127\.0\.1\.1.*/127.0.1.1\t$HOSTNAME_NEW/" /etc/hosts
        bien "nombre de equipo: $HOSTNAME_NEW"
    fi
    timedatectl set-timezone Europe/Madrid
    install -d -m 755 "$ETC_BH"
    instalar_env "$ETC_BH/bricohams.env"
    bien "paquetes base y $ETC_BH/bricohams.env"
}

paso_arranque() {
    [ -f "$BOOTCFG" ] || fallo "No encuentro $BOOTCFG"
    cp -n "$BOOTCFG" "$BOOTCFG.antes-bricohams" || true
    {
        echo "[all]"
        echo "# I2C-1 (GPIO2/3): RTC del HAT (0x51) y sensor BME280 (0x76/0x77)"
        echo "dtparam=i2c_arm=on"
        echo "dtoverlay=i2c-rtc,${HAT_RTC}"
        si "$HAT_DISABLE_PI5_RTC" && echo "dtparam=rtc=off"
        echo "# UART0 (GPIO14/15) para el GPS del HAT y PPS en GPIO${HAT_PPS_GPIO}"
        echo "dtparam=uart0=on"
        echo "dtoverlay=pps-gpio,gpiopin=${HAT_PPS_GPIO}"
        echo "# SPI para el LoRa SX1262 del HAT"
        echo "dtparam=spi=on"
        [ "$HAT_LORA_SPI" = spi1 ] && echo "dtoverlay=spi1-1cs"
        echo "# Cámara CSI del mástil"
        echo "camera_auto_detect=1"
        si "$PI5_USB_MAX_CURRENT" && echo "usb_max_current_enable=1"
        if si "${FAN_ENABLE:-no}" && [ "${IO_MODE:-pico}" = gpio ]; then
            echo "# Ventiladores de la caja: PWM por hardware en GPIO12/13 y DS18B20 (1-Wire) en GPIO${W1_GPIO:-4}"
            echo "dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4"
            echo "dtoverlay=w1-gpio,gpiopin=${W1_GPIO:-4}"
        fi
    } | bloque "$BOOTCFG" "BricoHams"
    # consola serie fuera del UART del GPS
    if command -v raspi-config >/dev/null; then
        raspi-config nonint do_serial_cons 1 || true
        raspi-config nonint do_i2c 0 || true
        raspi-config nonint do_spi 0 || true
    fi
    sed -i -E 's/ ?console=(serial0|ttyAMA0),[0-9]+//g' "$CMDLINE"
    # RTL-SDR: que el kernel no los coja como sintonizadores de TDT
    cat >/etc/modprobe.d/bricohams-rtlsdr-blacklist.conf <<'EOF'
blacklist dvb_usb_rtl28xxu
blacklist rtl2832
blacklist rtl2832_sdr
blacklist rtl2830
blacklist r820t
EOF
    echo "pps-gpio" >/etc/modules-load.d/bricohams-pps.conf
    REINICIAR=1
    bien "config.txt (RTC, UART0, PPS, SPI, cámara, USB), consola serie desactivada, TDT bloqueada"
}

paso_red() {
    # WiFi de casa (NetworkManager, Bookworm): primero la de 5 GHz, después la de 2,4 GHz.
    # Si la Pi va por cable, el WiFi queda de respaldo.
    command -v raspi-config >/dev/null && raspi-config nonint do_wifi_country "${WIFI_COUNTRY:-ES}" || true
    if ! command -v nmcli >/dev/null; then aviso "Sin NetworkManager: configura el WiFi a mano"; return; fi
    local i v ssid prio
    for i in 1 2; do
        v="WIFI_SSID_$i"; ssid=${!v:-}
        prio=$(( 30 - i * 10 ))
        [ -n "$ssid" ] || continue
        # v4.2: si ya existe se MODIFICA. Antes se borraba y se volvía a crear: si la Pi
        # estaba conectada por esa misma conexión, se quedaba sin red unos segundos y
        # el paso siguiente fallaba («Could not resolve host»).
        if nmcli -t -f NAME connection show 2>/dev/null | grep -qx "bricohams-wifi-$i"; then
            nmcli connection modify "bricohams-wifi-$i" 802-11-wireless.ssid "$ssid" \
                wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$WIFI_PASS" \
                connection.autoconnect yes connection.autoconnect-priority "$prio" >/dev/null
            bien "WiFi '$ssid' (prioridad $prio, actualizada sin desconectar)"
        else
            nmcli connection add type wifi con-name "bricohams-wifi-$i" ifname wlan0 ssid "$ssid" \
                wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$WIFI_PASS" \
                connection.autoconnect yes connection.autoconnect-priority "$prio" >/dev/null
            bien "WiFi '$ssid' (prioridad $prio)"
        fi
    done
    esperar_red
}

paso_hat() {
    # RTC: fuera fake-hwclock, la hora sale del PCF85063A
    DEBIAN_FRONTEND=noninteractive apt-get -y purge fake-hwclock 2>/dev/null || true
    # interruptores de alimentación de módulos, si el HAT los tiene
    cat >/usr/local/sbin/bricohams-hat-power <<EOF
#!/bin/bash
# Pone en alto los GPIO de alimentación de módulos del HAT (HAT_POWER_GPIOS)
for g in ${HAT_POWER_GPIOS:-}; do pinctrl set "\$g" op dh; done
exit 0
EOF
    chmod 755 /usr/local/sbin/bricohams-hat-power
    cat >/etc/systemd/system/bricohams-hat-power.service <<'EOF'
[Unit]
Description=BricoHams: alimentación de los módulos del HAT
DefaultDependencies=no
Before=gpsd.service meshtasticd.service openwebrx.service
After=local-fs.target

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/bricohams-hat-power
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
    # GPS: gpsd con el UART y el PPS
    cat >/etc/default/gpsd <<EOF
# BricoHams: GPS del HAT HackerGadgets
START_DAEMON="true"
USBAUTO="false"
DEVICES="${HAT_GPS_DEV} /dev/pps0"
GPSD_OPTIONS="-n -s ${HAT_GPS_BAUD}"
EOF
    # chrony: hora con NMEA + PPS del GPS (y NTP de Internet de respaldo)
    install -d /etc/chrony/conf.d
    cat >/etc/chrony/conf.d/bricohams-gps.conf <<'EOF'
# BricoHams: hora del GPS del HAT
refclock SHM 0 refid NMEA offset 0.2 delay 0.2 noselect
refclock PPS /dev/pps0 lock NMEA refid PPS prefer
makestep 1 3
EOF
    systemctl disable --now systemd-timesyncd 2>/dev/null || true
    systemctl daemon-reload
    systemctl enable bricohams-hat-power gpsd chrony
    systemctl restart gpsd chrony 2>/dev/null || true
    bien "RTC ${HAT_RTC}, gpsd (${HAT_GPS_DEV} @ ${HAT_GPS_BAUD}) + PPS GPIO${HAT_PPS_GPIO} en chrony"
}

paso_rtlsdr() {
    local tmp
    if [ "$DEB" = trixie ]; then
        bien "rtl-sdr $(rtlsdr_debian) de Debian (osmocom 2.x): V3, R860, bias-tee y muestreo directo; en Trixie no se compila rtl-sdr-blog"
        return
    fi
    tmp=$(mktemp -d)
    git clone --depth 1 https://github.com/rtlsdrblog/rtl-sdr-blog "$tmp/rtl-sdr-blog"
    (cd "$tmp/rtl-sdr-blog" && dpkg-buildpackage -b --no-sign -uc -us >/dev/null)
    apt-mark unhold librtlsdr0 librtlsdr-dev rtl-sdr >/dev/null 2>&1 || true
    dpkg -i "$tmp"/librtlsdr0_*.deb "$tmp"/librtlsdr-dev_*.deb "$tmp"/rtl-sdr_*.deb
    apt-mark hold librtlsdr0 librtlsdr-dev rtl-sdr
    rm -rf "$tmp"
    ldconfig
    bien "driver rtl-sdr-blog (V3, R860, bias-tee y muestreo directo) instalado y retenido"
}

paso_openwebrx() {
    # huella de --actualizar: lo que usa docker_preparar (ficheros y variables)
    : "$FILES/bin/bricohams-docker-compose.py" "${OWRX_DOCKER_IMAGE:-}${OWRX_DOCKER_RED:-}${OWRX_DOCKER_PORT:-}${OWRX_DOCKER_PRIVILEGED:-}${OWRX_DOCKER_DIR:-}${OWRX_DOCKER_CONTAINER:-}"
    if [ "${OWRX_BACKEND:-native}" = docker ]; then
        local container=${OWRX_DOCKER_CONTAINER:-owrx-mbe} mounts target source expected
        usuario_openwebrx
        if si "${OWRX_DOCKER_DESPLEGAR:-yes}"; then docker_preparar; fi
        command -v docker >/dev/null || fallo "OWRX_BACKEND=docker requiere Docker CLI"
        docker inspect "$container" >/dev/null 2>&1 || fallo "No existe el contenedor '$container'; ajusta OWRX_DOCKER_CONTAINER"
        [ "$(docker inspect --format '{{.State.Running}}' "$container")" = true ] || fallo "El contenedor '$container' debe estar en ejecución"
        mounts=$(docker inspect --format '{{range .Mounts}}{{.Destination}}{{"\n"}}{{end}}' "$container")
        for target in /etc/openwebrx /var/lib/openwebrx /usr/lib/python3/dist-packages/htdocs/plugins; do
            printf '%s\n' "$mounts" | grep -Fxq "$target" || fallo "Falta el volumen Docker persistente '$target' (Compose oficial)"
            source=$(owrx_docker_mount "$target")
            case "$target" in
                /etc/openwebrx) expected=$OWRX_ETC ;;
                /var/lib/openwebrx) expected=$OWRX_DATA ;;
                *) expected=$HTDOCS/plugins ;;
            esac
            [ "$(realpath -m "$source")" = "$(realpath -m "$expected")" ] \
                || fallo "El mount Docker de $target apunta a '$source', no a '$expected' (revisa OWRX_DOCKER_DIR)"
        done
        [ -d "$OWRX_ETC" ] && [ -d "$OWRX_DATA" ] && [ -d "$HTDOCS/plugins" ] \
            || fallo "No encuentro etc/, var/ y plugins/ bajo OWRX_DOCKER_DIR=$OWRX_DOCKER_DIR"
        bien "OpenWebRX+ Docker '$container' activo y con volúmenes persistentes"
        return 0
    fi
    # v4.3 · vuelta a nativo: el contenedor (red host, restart unless-stopped) ocuparía el 8073 y los SDR
    if command -v docker >/dev/null && docker inspect "${OWRX_DOCKER_CONTAINER:-owrx-mbe}" >/dev/null 2>&1; then
        aviso "OWRX_BACKEND=native: paro el contenedor ${OWRX_DOCKER_CONTAINER:-owrx-mbe} y le quito el arranque automático (sus datos siguen en ${OWRX_DOCKER_DIR:-/opt/owrx-docker})"
        docker update --restart=no "${OWRX_DOCKER_CONTAINER:-owrx-mbe}" >/dev/null 2>&1 || true
        docker stop "${OWRX_DOCKER_CONTAINER:-owrx-mbe}" >/dev/null 2>&1 || true
    fi
    clave_apt https://luarvique.github.io/ppa/openwebrx-plus.gpg /etc/apt/trusted.gpg.d/openwebrx-plus.gpg
    echo "deb [signed-by=/etc/apt/trusted.gpg.d/openwebrx-plus.gpg] https://luarvique.github.io/ppa/$DEB ./" >/etc/apt/sources.list.d/openwebrx-plus.list
    apt_update
    apt_i openwebrx
    apt_i soapysdr-module-sdrplay3 || aviso "No pude instalar soapysdr-module-sdrplay3"
    systemctl enable openwebrx
    bien "OpenWebRX+ $(dpkg-query -W -f='${Version}' openwebrx 2>/dev/null)"
}

paso_sdrplay() {
    if ! si "$INSTALL_SDRPLAY_API"; then aviso "API de SDRplay omitida (INSTALL_SDRPLAY_API)"; return; fi
    if [ "${OWRX_BACKEND:-native}" = docker ]; then
        aviso "OpenWebRX+ en Docker: la API de SDRplay va dentro de la imagen. Si el RSP no aparece: OWRX_DOCKER_PRIVILEGED=\"yes\" y sudo bash install.sh --solo openwebrx"
        return 0
    fi
    if [ -e /usr/local/lib/libsdrplay_api.so ] || ls /usr/local/lib/libsdrplay_api.so.* >/dev/null 2>&1; then
        bien "API de SDRplay ya instalada"
    else
        local tmp run
        tmp=$(mktemp -d); run="$tmp/$(basename "$SDRPLAY_API_URL")"
        curl -fL --retry 3 -o "$run" "$SDRPLAY_API_URL" || fallo "No pude bajar la API de SDRplay ($SDRPLAY_API_URL). Bájala de https://www.sdrplay.com/downloads/ y pon la URL en bricohams.env"
        chmod +x "$run"
        echo
        info "Instalador oficial de SDRplay: lee la licencia y acéptala para seguir."
        (cd "$tmp" && "$run") </dev/tty
        rm -rf "$tmp"
    fi
    systemctl daemon-reload
    for s in sdrplay sdrplayService; do
        systemctl list-unit-files | grep -q "^$s.service" && { systemctl enable --now "$s" || true; bien "servicio $s"; }
    done
}

paso_configuracion() {
    if [ "${OWRX_BACKEND:-native}" = docker ]; then
        :   # el contenedor sigue activo mientras se actualizan sus volúmenes bind
        usuario_openwebrx
        mkdir -p "$OWRX_DATA" "$OWRX_ETC" "$HTDOCS/plugins"
    else
        systemctl stop openwebrx 2>/dev/null || true
        install -d -o openwebrx -g openwebrx "$OWRX_DATA"
    fi
    local stamp; stamp=$(date +%Y%m%d-%H%M%S)
    [ -f "$OWRX_DATA/settings.json" ] && cp "$OWRX_DATA/settings.json" "$OWRX_DATA/settings.json.antes-$stamp"
    # settings.json desde la plantilla + bricohams.env
    install -d -m 755 "$ETC_BH"; instalar_env "$ETC_BH/bricohams.env"
    cargar_env "$KIT/bricohams.env"          # exporta todas (las lee bricohams-render-settings)
    # v4.2 · con un perfil importado (install.sh --importar) manda el perfil, no la plantilla
    if [ -f "$PERFIL_IMPORTADO" ] && ! si "${OWRX_PLANTILLA:-no}"; then
        aviso "Configuración importada de un perfil ($(grep -m1 '^PERFIL=' "$PERFIL_IMPORTADO" | cut -d= -f2-)): no regenero settings.json ni los marcadores."
        aviso "Para volver a la plantilla de BricoHams: OWRX_PLANTILLA=\"yes\" en bricohams.env y sudo bash install.sh --solo configuracion"
        if [ "${OWRX_BACKEND:-native}" = docker ]; then
            owrx_owner
            owrx_control restart
        else
            chown -R openwebrx:openwebrx "$OWRX_DATA"
            systemctl start openwebrx
        fi
        return 0
    fi
    python3 "$FILES/bin/bricohams-render-settings.py" "$FILES/openwebrx/settings.json.tmpl" "$OWRX_DATA/settings.json"
    # marcadores (v4.1): si ya hay, se conservan los que añadiste desde la web y se ponen al día los del kit
    local bm_kit=/var/lib/bricohams/bookmarks.kit.json bm_ant
    bm_ant=$bm_kit     # sin él (instalaciones de antes de la v4.1): la copia del kit anterior en /opt
    [ -s "$bm_ant" ] || bm_ant=/opt/bricohams/kit/files/openwebrx/bookmarks.json
    if [ -z "$BACKUP" ] && [ -s "$OWRX_DATA/bookmarks.json" ]; then
        cp "$OWRX_DATA/bookmarks.json" "$OWRX_DATA/bookmarks.json.antes-$stamp"
        python3 "$FILES/bin/bricohams-merge-bookmarks.py" --tres "$bm_ant" "$OWRX_DATA/bookmarks.json" \
            "$FILES/openwebrx/bookmarks.json" "$OWRX_DATA/bookmarks.json"
    else
        install -m 644 "$FILES/openwebrx/bookmarks.json" "$OWRX_DATA/bookmarks.json"
    fi
    : "$KIT/data/locator/catalogo_es.json" "$FILES/bin/bricohams_locator_bookmarks.py" "$FILES/bin/bricohams_locator.py"   # huella de --actualizar
    if [ -n "$LOCATOR_CATALOG_PATH" ]; then
        # v4.3 · marcadores de la zona del locator (aeropuertos, puertos, NAVTEX, FM regionales y locales)
        local bm_locator
        install -d -m 755 "$LOCATOR_CACHE"
        if [[ ! "${LOCATOR_ONLINE-aemet,fmdx}" =~ ^([Nn][Oo]?|0|[Ff]alse)?$ ]]; then
            AEMET_API_KEY="${AEMET_API_KEY:-}" timeout 150 python3 "$FILES/bin/bricohams_locator_online.py" refrescar \
                --cache "$LOCATOR_CACHE" --lat "$STATION_LAT" --lon "$STATION_LON" --fuentes "${LOCATOR_ONLINE-aemet,fmdx}" \
                || aviso "Sin datos de zona en línea (AEMET/FM): sigo con el catálogo del kit"
        fi
        bm_locator=$(mktemp --suffix=.json)
        zona_selector --merge-existing "$OWRX_DATA/bookmarks.json" --kit "$FILES/openwebrx/bookmarks.json" \
            --kit-zona-km "${LOCATOR_KIT_ZONA_KM:-150}" --output "$bm_locator" \
            || { rm -f "$bm_locator"; fallo "No pude generar bookmarks cercanos al locator"; }
        install -m 664 "$bm_locator" "$OWRX_DATA/bookmarks.json"
        rm -f "$bm_locator"
        zona_selector --informe | sed 's/^/    /' || true
        bien "marcadores de la zona $STATION_QTH_LOCATOR (aeropuertos, puertos, NAVTEX y FM)"
    fi
    install -D -m 644 "$FILES/openwebrx/bookmarks.json" "$bm_kit"
    install -m 664 "$FILES/branding/receiver_avatar.png" "$OWRX_DATA/receiver_avatar.png"
    install -m 664 "$FILES/branding/receiver_top_photo.png" "$OWRX_DATA/receiver_top_photo.png"
    install -d "$OWRX_ETC/openwebrx.conf.d"
    install -m 644 "$FILES"/openwebrx/conf.d/*.conf "$OWRX_ETC/openwebrx.conf.d/"
    # restaurar desde una copia (usuarios y marcadores)
    if [ -n "$BACKUP" ]; then
        [ -r "$BACKUP" ] || fallo "No puedo leer la copia $BACKUP"
        local tmp; tmp=$(mktemp -d)
        tar -xzf "$BACKUP" -C "$tmp" var/lib/openwebrx/users.json var/lib/openwebrx/bookmarks.json 2>/dev/null || true
        # v4.3 · copia de una estación en Docker: los datos van en OWRX_DOCKER_DIR/var
        local dvar=${OWRX_DOCKER_DIR:-/opt/owrx-docker}; dvar=${dvar#/}/var
        if [ ! -s "$tmp/var/lib/openwebrx/users.json" ] && tar -xzf "$BACKUP" -C "$tmp" "$dvar/users.json" "$dvar/bookmarks.json" 2>/dev/null; then :; fi
        if [ -s "$tmp/$dvar/users.json" ]; then install -d "$tmp/var/lib/openwebrx"; mv -f "$tmp/$dvar"/*.json "$tmp/var/lib/openwebrx/"; fi
        [ -s "$tmp/var/lib/openwebrx/users.json" ] && install -m 600 "$tmp/var/lib/openwebrx/users.json" "$OWRX_DATA/users.json" && bien "usuarios restaurados de la copia"
        if [ -s "$tmp/var/lib/openwebrx/bookmarks.json" ]; then
            python3 "$FILES/bin/bricohams-merge-bookmarks.py" "$tmp/var/lib/openwebrx/bookmarks.json" \
                "$FILES/openwebrx/bookmarks.json" "$OWRX_DATA/bookmarks.json"
            bien "marcadores de la copia + los nuevos del kit"
        fi
        rm -rf "$tmp"
    fi
    chown -R openwebrx:openwebrx "$OWRX_DATA"
    if [ ! -s "$OWRX_DATA/users.json" ] && [ -n "$IMPORTAR" ]; then
        aviso "Sin usuario de administración todavía: lo trae el perfil que se importa al final"
    elif [ ! -s "$OWRX_DATA/users.json" ]; then
        info "Crea la contraseña del administrador '$OWRX_ADMIN_USER' de OpenWebRX:"
        if [ "${OWRX_BACKEND:-native}" = docker ]; then
            docker exec -it "${OWRX_DOCKER_CONTAINER:-owrx-mbe}" openwebrx admin adduser "$OWRX_ADMIN_USER" </dev/tty \
                || aviso "Crea el usuario luego: docker exec -it ${OWRX_DOCKER_CONTAINER:-owrx-mbe} openwebrx admin adduser $OWRX_ADMIN_USER"
        else
            openwebrx admin adduser "$OWRX_ADMIN_USER" </dev/tty || aviso "Crea el usuario luego: sudo openwebrx admin adduser $OWRX_ADMIN_USER"
            chown openwebrx:openwebrx "$OWRX_DATA/users.json" 2>/dev/null || true
        fi
    fi
    if [ "${OWRX_BACKEND:-native}" = docker ]; then
        owrx_owner
        owrx_control restart
    else
        chown -R openwebrx:openwebrx "$OWRX_DATA"
        systemctl start openwebrx
    fi
    bien "OpenWebRX configurado: receptores, marcadores, imágenes BricoHams/Murcia"
}

paso_plugins() {
    local R="$HTDOCS/plugins/receiver"
    local listeners_country=${LISTENERS_COUNTRY:-${STATION_COUNTRY:-}}
    if [[ ! "$listeners_country" =~ ^[A-Za-z]{2}$ ]]; then
        [ -z "$listeners_country" ] || aviso "LISTENERS_COUNTRY debe ser un código ISO de dos letras; no muestro bandera en LST"
        listeners_country=""
    else
        listeners_country=${listeners_country^^}
    fi
    [ -d "$HTDOCS" ] || fallo "No existe $HTDOCS (¿OpenWebRX instalado?)"
    [ -f "$R/init.js" ] && cp "$R/init.js" "$R/init.js.antes-$(date +%Y%m%d-%H%M%S)"
    local guardar=()
    if [ -f "$PERFIL_IMPORTADO" ] && ! si "${OWRX_PLANTILLA:-no}"; then
        guardar=(--exclude 'receiver/init.js')       # v4.2: el init.js del perfil importado manda
        aviso "Perfil importado: conservo su plugins/receiver/init.js (los plugins de BricoHams quedan copiados, pero sin cargar)"
    fi
    rsync -a --exclude 'meteo/meteo.json' --exclude 'camara/snap/' --exclude 'satelites/pases.json' --exclude 'visitas/visitas.json' \
        "${guardar[@]}" "$FILES/htdocs/plugins/" "$HTDOCS/plugins/"
    sed -i -e "s/__LAT__/${STATION_LAT}/" -e "s/__LON__/${STATION_LON}/" \
        -e "s/__CAM_SNAPSHOT_SECONDS__/${CAM_SNAPSHOT_SECONDS}/" \
        -e "s#__LISTENERS_URL__#${LISTENERS_SUPABASE_URL:-}#" -e "s#__LISTENERS_KEY__#${LISTENERS_SUPABASE_KEY:-}#" \
        -e "s#__LISTENERS_COUNTRY__#${listeners_country}#" "$R/init.js"
    if [ "${OWRX_BACKEND:-native}" = docker ]; then
        mkdir -p "$R/meteo" "$R/camara/snap" "$R/satelites" "$R/visitas"
        owrx_owner
    else
        install -d -o openwebrx -g openwebrx "$R/meteo" "$R/camara/snap" "$R/satelites" "$R/visitas"
    fi
    bien "plugins: rig_skin (DX), solar, meteo, cámara, BricoHams y los de 0xAF"
}

paso_meteo() {
    install -m 755 "$FILES/bin/bricohams-meteo.py" /usr/local/bin/bricohams-meteo
    if [ -n "$LOCATOR_CATALOG_PATH" ]; then        # v4.3 · con la lista de AEMET recién bajada (paso configuracion)
        zona_locator; instalar_env "$ETC_BH/bricohams.env"
    fi
    cat >"$ETC_BH/meteo.env" <<EOF
AEMET_API_KEY=$(sq "${AEMET_API_KEY:-}")
METEO_STATIONS=$(sq "${METEO_STATIONS:-}")
STATION_LAT=${STATION_LAT}
STATION_LON=${STATION_LON}
METEO_OUT=${HTDOCS}/plugins/receiver/meteo/meteo.json
EOF
    chown root:openwebrx "$ETC_BH/meteo.env"; chmod 640 "$ETC_BH/meteo.env"
    cat >/etc/systemd/system/bricohams-meteo.service <<'EOF'
[Unit]
Description=BricoHams: tiempo de las estaciones cercanas (AEMET + Open-Meteo)
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
User=openwebrx
EnvironmentFile=/etc/bricohams/meteo.env
ExecStart=/usr/local/bin/bricohams-meteo
EOF
    cat >/etc/systemd/system/bricohams-meteo.timer <<'EOF'
[Unit]
Description=BricoHams: meteo cada 10 minutos

[Timer]
OnBootSec=90s
OnUnitActiveSec=10min
RandomizedDelaySec=30s

[Install]
WantedBy=timers.target
EOF
    systemctl daemon-reload
    systemctl enable --now bricohams-meteo.timer
    systemctl start bricohams-meteo.service || aviso "La primera lectura de meteo falló (mira: journalctl -u bricohams-meteo)"
    [ -n "$AEMET_API_KEY" ] && bien "meteo AEMET ($METEO_STATIONS) + Open-Meteo" || aviso "Sin AEMET_API_KEY: solo modelo Open-Meteo. Pide la clave gratis y vuelve a lanzar: sudo bash install.sh --solo meteo"
}

paso_camara() {
    # MediaMTX (última versión para arm64)
    if ! command -v mediamtx >/dev/null; then
        local url tmp
        url=$("${CURL[@]}" https://api.github.com/repos/bluenviron/mediamtx/releases/latest \
            | jq -r '.assets[].browser_download_url' | grep -E 'linux_arm64(v8)?\.tar\.gz$' | head -1)
        [ -n "$url" ] || fallo "No encuentro MediaMTX para arm64"
        tmp=$(mktemp -d)
        "${CURL[@]}" "$url" | tar -xz -C "$tmp"
        install -m 755 "$tmp/mediamtx" /usr/local/bin/mediamtx
        rm -rf "$tmp"
    fi
    id mediamtx >/dev/null 2>&1 || useradd -r -s /usr/sbin/nologin -G video,render mediamtx
    local cam_src
    if [ "${CAM_SOURCE:-rpi}" = rtsp ]; then
        [ -n "${CAM_RTSP_URL:-}" ] || fallo "CAM_SOURCE=rtsp pero CAM_RTSP_URL está vacío (bricohams.env)"
        # cámara IP: MediaMTX reenvía su H.264 sin recodificar (casi 0 % de CPU en la Pi)
        cam_src=$(printf '    source: %s\n    rtspTransport: tcp' "$CAM_RTSP_URL")
    else
        cam_src=$(printf '%s\n' \
            "    # Whadda/Velleman WPI408: OV5647 5 MP, 130°, 2 LED IR" \
            "    source: rpiCamera" \
            "    rpiCameraWidth: ${CAM_WIDTH}" \
            "    rpiCameraHeight: ${CAM_HEIGHT}" \
            "    rpiCameraFPS: ${CAM_FPS}" \
            "    rpiCameraHFlip: ${CAM_HFLIP}" \
            "    rpiCameraVFlip: ${CAM_VFLIP}" \
            "    # la Pi 5 no tiene codificador H.264 por hardware" \
            "    rpiCameraCodec: softwareH264" \
            "    rpiCameraBitrate: ${CAM_BITRATE}" \
            "    rpiCameraTuningFile: ${CAM_TUNING}")
    fi
    install -d /etc/mediamtx
    cat >/etc/mediamtx/mediamtx.yml <<EOF
# BricoHams: cámara CSI del mástil
logLevel: info
api: yes
apiAddress: 127.0.0.1:9997
rtsp: yes
rtspAddress: :8554
rtmp: no
srt: no
hls: yes
hlsAddress: :8888
webrtc: yes
webrtcAddress: :8889
paths:
  mastil:
${cam_src}
EOF
    chown root:mediamtx /etc/mediamtx/mediamtx.yml; chmod 640 /etc/mediamtx/mediamtx.yml   # puede llevar la clave de la cámara IP
    cat >/etc/systemd/system/mediamtx.service <<'EOF'
[Unit]
Description=MediaMTX: vídeo de la cámara del mástil
Wants=network-online.target
After=network-online.target

[Service]
User=mediamtx
Group=video
SupplementaryGroups=render
ExecStart=/usr/local/bin/mediamtx /etc/mediamtx/mediamtx.yml
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
    # foto periódica en un tmpfs dentro de la carpeta del plugin (no gasta la SD)
    local snapdir="$HTDOCS/plugins/receiver/camara/snap" uid gid
    install -d "$snapdir"
    uid=$(id -u openwebrx); gid=$(id -g openwebrx)
    sed -i "\#[[:space:]]${snapdir}[[:space:]]#d" /etc/fstab
    echo "tmpfs $snapdir tmpfs rw,nosuid,nodev,noexec,size=16m,mode=0755,uid=$uid,gid=$gid 0 0" >>/etc/fstab
    systemctl daemon-reload
    mountpoint -q "$snapdir" || mount "$snapdir"
    install -m 755 "$FILES/bin/bricohams-camsnap.py" /usr/local/bin/bricohams-camsnap
    cat >/etc/systemd/system/bricohams-camsnap.service <<EOF
[Unit]
Description=BricoHams: foto de la cámara del mástil para la web
After=mediamtx.service
Wants=mediamtx.service

[Service]
User=openwebrx
RuntimeDirectory=bricohams
Environment=CAM_SNAPSHOT_SECONDS=${CAM_SNAPSHOT_SECONDS}
Environment="CAM_LABEL=${CAM_LABEL}"
Environment=CAM_SNAPSHOT=${snapdir}/mastil.jpg
ExecStart=/usr/local/bin/bricohams-camsnap
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    systemctl enable --now mediamtx bricohams-camsnap
    bien "MediaMTX (RTSP :8554/mastil · WebRTC :8889/mastil · HLS :8888/mastil) y foto cada ${CAM_SNAPSHOT_SECONDS}s"
}

paso_sensor() {
    if ! si "$WX_ENABLE"; then aviso "Sensor WX omitido (WX_ENABLE)"; return; fi
    install -m 755 "$FILES/bin/bricohams-wx.py" /usr/local/bin/bricohams-wx
    if si "${WIND_ENABLE:-no}" || si "${RAIN_ENABLE:-no}"; then
        apt_i python3-serial python3-lgpio
        # adaptador USB-RS485 del viento con nombre fijo (CH340 1a86:7523; el LilyGO es CH9102F 1a86:55d4)
        cat >/etc/udev/rules.d/99-bricohams-rs485.rules <<EOF
SUBSYSTEM=="tty", ATTRS{idVendor}=="${RS485_VID:-1a86}", ATTRS{idProduct}=="${RS485_PID:-7523}", SYMLINK+="rs485", GROUP="dialout", MODE="0660"
EOF
        udevadm control --reload && udevadm trigger --subsystem-match=tty || true
    fi
    cat >"$ETC_BH/wx.env" <<EOF
STATION_LAT=${STATION_LAT}
STATION_LON=${STATION_LON}
STATION_ASL=${STATION_ASL}
WX_SENSOR_HEIGHT=${WX_SENSOR_HEIGHT}
WX_TEMP_OFFSET=${WX_TEMP_OFFSET}
WX_APRS=${WX_APRS}
WX_APRS_CALLSIGN=${WX_APRS_CALLSIGN}
WX_APRS_COMMENT=$(sq "${WX_APRS_COMMENT:-}")
APRS_PASSCODE=$(sq "${APRS_PASSCODE:-}")
WX_OUT=${HTDOCS}/plugins/receiver/meteo/sensor.json
WIND_ENABLE=${WIND_ENABLE:-no}
WIND_PORT=${WIND_PORT:-/dev/rs485}
WIND_BAUD=${WIND_BAUD:-4800}
WIND_ADDR_SPEED=${WIND_ADDR_SPEED:-1}
WIND_ADDR_DIR=${WIND_ADDR_DIR:-2}
WIND_DIR_MODE=${WIND_DIR_MODE:-sector8}
RAIN_ENABLE=${RAIN_ENABLE:-no}
RAIN_GPIO=${RAIN_GPIO:-17}
RAIN_MM=${RAIN_MM:-0.2794}
IO_MODE=${IO_MODE:-pico}
IO_RUN_DIR=/run/bricohams
EOF
    chown root:openwebrx "$ETC_BH/wx.env"; chmod 640 "$ETC_BH/wx.env"
    for g in dialout gpio; do getent group "$g" >/dev/null && usermod -aG "$g" openwebrx; done
    getent group i2c >/dev/null && usermod -aG i2c openwebrx
    cat >/etc/systemd/system/bricohams-wx.service <<'EOF'
[Unit]
Description=BricoHams: sensor BME280/BMP280 (tiempo propio y WX APRS)
After=network-online.target
Wants=network-online.target

[Service]
User=openwebrx
SupplementaryGroups=i2c dialout gpio
StateDirectory=bricohams
EnvironmentFile=/etc/bricohams/wx.env
ExecStart=/usr/local/bin/bricohams-wx
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    systemctl enable bricohams-wx
    if [ "${IO_MODE:-pico}" = pico ]; then
        sed -i 's/^After=network-online.target$/After=network-online.target bricohams-io.service/' /etc/systemd/system/bricohams-wx.service
        systemctl daemon-reload; systemctl restart bricohams-wx
        bien "sensor BME280 en la Pico bricohams-io, WX APRS ${WX_APRS} (${WX_APRS_CALLSIGN})"
    elif i2cdetect -y 1 2>/dev/null | grep -Eq ' (76|77) '; then
        systemctl restart bricohams-wx
        bien "sensor BME/BMP280 en I2C-1, WX APRS ${WX_APRS} (${WX_APRS_CALLSIGN})"
    else
        aviso "No veo el BME/BMP280 en I2C-1 (0x76/0x77). Conéctalo (docs/MANUAL_SENSOR_WX.md) y: sudo systemctl restart bricohams-wx"
    fi
}

paso_ventilacion() {
    if ! si "${FAN_ENABLE:-no}"; then aviso "Ventiladores omitidos (FAN_ENABLE)"; return; fi
    apt_i python3-lgpio
    install -m 755 "$FILES/bin/bricohams-fan.py" /usr/local/bin/bricohams-fan
    cat >"$ETC_BH/fan.env" <<EOF
FAN_PWM_GPIOS=${FAN_PWM_GPIOS:-12,13}
FAN_TACH_GPIOS=${FAN_TACH_GPIOS:-22,5}
FAN_PWM_INVERT=${FAN_PWM_INVERT:-yes}
FAN_T_CPU_MIN=${FAN_T_CPU_MIN:-55}
FAN_T_CPU_MAX=${FAN_T_CPU_MAX:-75}
FAN_T_CAJA_MIN=${FAN_T_CAJA_MIN:-35}
FAN_T_CAJA_MAX=${FAN_T_CAJA_MAX:-45}
FAN_DUTY_MIN=${FAN_DUTY_MIN:-30}
FAN_HIST=${FAN_HIST:-3}
FAN_DS18B20_ID=${FAN_DS18B20_ID:-}
FAN_OUT=${HTDOCS}/plugins/receiver/meteo/caja.json
IO_MODE=${IO_MODE:-pico}
IO_RUN_DIR=/run/bricohams
EOF
    cat >/etc/systemd/system/bricohams-fan.service <<'EOF'
[Unit]
Description=BricoHams: ventiladores de la caja (PWM + tacómetro)
After=multi-user.target bricohams-io.service

[Service]
EnvironmentFile=/etc/bricohams/fan.env
ExecStart=/usr/local/bin/bricohams-fan
Restart=always
RestartSec=15

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    systemctl enable bricohams-fan
    echo "d /run/bricohams 0775 openwebrx openwebrx -" >/etc/tmpfiles.d/bricohams.conf
    systemd-tmpfiles --create /etc/tmpfiles.d/bricohams.conf
    if [ "${IO_MODE:-pico}" = pico ]; then
        systemctl restart bricohams-fan
        bien "ventiladores en la Pico bricohams-io (PWM GP16/GP17, tacómetros GP18/GP19, DS18B20 GP22)"
        return
    fi
    if ls /sys/class/pwm/pwmchip* >/dev/null 2>&1; then systemctl restart bricohams-fan; fi
    REINICIAR=1
    bien "ventiladores: PWM GPIO${FAN_PWM_GPIOS:-12,13}, tacómetros GPIO${FAN_TACH_GPIOS:-22,5}, DS18B20 en GPIO${W1_GPIO:-4} (tras reiniciar)"
}

paso_adsb() {
    if ! si "$ADSB_ENABLE"; then aviso "ADS-B omitido (ADSB_ENABLE)"; return; fi
    # 1) readsb (wiedehopf) con el FlightStick, elegido por su número de serie
    if ! command -v readsb >/dev/null; then
        script_remoto https://github.com/wiedehopf/adsb-scripts/raw/master/readsb-install.sh \
            || fallo "No pude instalar readsb (wiedehopf). Repite el instalador: sigue donde se quedó"
    fi
    local biast=""
    si "$ADSB_BIAS_TEE" && biast=" --enable-biastee"
    sed -i "s|^RECEIVER_OPTIONS=.*|RECEIVER_OPTIONS=\"--device-type rtlsdr --device ${SERIAL_ADSB} --gain ${ADSB_GAIN} --ppm 0${biast}\"|" /etc/default/readsb
    if command -v readsb-set-location >/dev/null; then readsb-set-location "$STATION_LAT" "$STATION_LON" || true; fi
    # 2) mapa propio tar1090
    if si "$ADSB_TAR1090" && [ ! -d /usr/local/share/tar1090 ]; then
        script_remoto https://github.com/wiedehopf/tar1090/raw/master/install.sh || aviso "No pude instalar tar1090"
    fi
    # 3) AirNav RadarBox (rbfeeder) leyendo la salida Beast de readsb, con MLAT
    if ! command -v rbfeeder >/dev/null; then
        if [ "$DEB" = trixie ]; then
            # Trixie: repositorio de AirNav por apt (su script inst_rbfeeder.sh es para Bookworm)
            install -d -m 755 /etc/apt/keyrings
            clave_apt "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0xF2A8428D3C354953" /etc/apt/keyrings/rb24.gpg
            echo "deb [signed-by=/etc/apt/keyrings/rb24.gpg] https://apt.rb24.com/ trixie main" >/etc/apt/sources.list.d/rb24.list
            apt_update
            apt_i rbfeeder || aviso "No pude instalar rbfeeder desde apt.rb24.com (trixie)"
        else
            script_remoto http://apt.rb24.com/inst_rbfeeder.sh </dev/null || aviso "Fallo del instalador de rbfeeder"
        fi
    fi
    if ! dpkg -s mlat-client >/dev/null 2>&1; then
        if ! apt_i mlat-client 2>/dev/null; then
            # Trixie (Python 3.13) no trae mlat-client: se compila el de mutability (necesita python3-pyasyncore)
            local mt
            mt=$(mktemp -d)
            apt_i build-essential debhelper dh-python python3-dev python3-setuptools python3-pyasyncore \
                && git clone --depth 1 https://github.com/mutability/mlat-client "$mt/mlat-client" \
                && (cd "$mt/mlat-client" && dpkg-buildpackage -b --no-sign -uc -us >/dev/null) \
                && dpkg -i "$mt"/mlat-client_*.deb && apt-mark hold mlat-client >/dev/null \
                && bien "mlat-client compilado e instalado" \
                || aviso "No pude compilar mlat-client: rbfeeder funcionará sin MLAT"
            rm -rf "$mt"
        fi
    fi
    if [ -f /etc/rbfeeder.ini ]; then
        if [ -n "$RADARBOX_KEY" ]; then rbfeeder --setkey "$RADARBOX_KEY" >/dev/null 2>&1 || true; fi
        python3 "$FILES/bin/bricohams-rbfeeder-ini.py" /etc/rbfeeder.ini "$STATION_LAT" "$STATION_LON" "$ADSB_ANT_ALT"
    fi
    systemctl daemon-reload
    systemctl enable readsb rbfeeder 2>/dev/null || true
    systemctl restart readsb rbfeeder 2>/dev/null || true
    bien "ADS-B: readsb (serie ${SERIAL_ADSB}) -> rbfeeder + MLAT; tar1090 en http://<pi>/tar1090"
    aviso "Asocia la estación a tu cuenta: sudo rbfeeder --showkey y https://www.airnavradar.com/raspberry-pi/claim"
}

paso_lilygo() {
    install -m 755 "$FILES/bin/bricohams-lilygo" /usr/local/bin/bricohams-lilygo
    usermod -aG dialout openwebrx 2>/dev/null || true
    PIPX_HOME=/opt/pipx PIPX_BIN_DIR=/usr/local/bin pipx install meshtastic >/dev/null 2>&1 || true
    if [ -f /etc/udev/rules.d/99-bricohams-lilygo.rules ]; then
        bien "LilyGO ya identificados: $(ls /dev/lilygo-* 2>/dev/null | tr '\n' ' ')"
    else
        aviso "Falta identificar los LilyGO (una vez): sudo bricohams-lilygo identificar"
    fi
    aviso "Después: sudo bricohams-lilygo meshtastic  ·  sudo bricohams-lilygo igate  (docs/MANUAL_LILYGO.md)"
}

paso_meshtastic() {
    if ! dpkg -s meshtasticd >/dev/null 2>&1; then
        echo "deb http://download.opensuse.org/repositories/network:/Meshtastic:/beta/Debian_$DEB_NUM/ /" >/etc/apt/sources.list.d/network:Meshtastic:beta.list
        clave_apt "https://download.opensuse.org/repositories/network:Meshtastic:beta/Debian_$DEB_NUM/Release.key" /etc/apt/trusted.gpg.d/network_Meshtastic_beta.gpg
        apt_update
        apt_i meshtasticd
    fi
    install -d /etc/meshtasticd/config.d
    {
        echo "# BricoHams: LoRa SX1262 del HAT HackerGadgets (A VERIFICAR con su documentación)"
        echo "Lora:"
        echo "  Module: sx1262"
        echo "  DIO2_AS_RF_SWITCH: true"
        echo "  DIO3_TCXO_VOLTAGE: true"
        echo "  IRQ: ${HAT_LORA_IRQ}"
        echo "  Busy: ${HAT_LORA_BUSY}"
        echo "  Reset: ${HAT_LORA_RESET}"
        [ -n "$HAT_LORA_TXEN" ] && echo "  TXen: ${HAT_LORA_TXEN}"
        [ -n "$HAT_LORA_RXEN" ] && echo "  RXen: ${HAT_LORA_RXEN}"
        echo "  spidev: ${HAT_LORA_SPIDEV}"
        echo "# El GPS lo usa gpsd (hora + OpenWebRX); el nodo usa posición fija"
        echo "Webserver:"
        echo "  Port: 9443"
        echo "  RootPath: /usr/share/meshtasticd/web"
        echo "General:"
        echo "  MaxNodes: 200"
        echo "  MACAddressSource: eth0"
    } >/etc/meshtasticd/config.d/hackergadgets-hat.yaml
    systemctl enable meshtasticd
    systemctl restart meshtasticd || true
    # CLI de Meshtastic para dejar el nodo configurado
    PIPX_HOME=/opt/pipx PIPX_BIN_DIR=/usr/local/bin pipx install --force meshtastic >/dev/null 2>&1 || aviso "No pude instalar la CLI de meshtastic"
    if [ -e /dev/"$HAT_LORA_SPIDEV" ] && command -v meshtastic >/dev/null; then
        for _ in $(seq 1 20); do ss -ltn | grep -q ':4403 ' && break; sleep 3; done
        if ss -ltn | grep -q ':4403 '; then
            local M=(timeout 60 meshtastic --host 127.0.0.1)
            if [ -n "${MESH_CHANNEL_URL:-}" ]; then
                # canales SFNarrow, Murcia, Cartagena, Test y Alicante + radio EU_868 869,618 MHz BW 62,5 kHz SF7
                "${M[@]}" --seturl "$MESH_CHANNEL_URL" && sleep 20
            else
                "${M[@]}" --set lora.region "$MESH_REGION" && sleep 15
            fi
            # canal privado solo en el nodo 868 (índice 5, detrás de los 5 canales de la red)
            if [ -n "${MESH868_PRIVATE_PSK:-}" ]; then
                "${M[@]}" --ch-add "${MESH868_PRIVATE_NAME:-BricoHams}" && sleep 10
                "${M[@]}" --ch-index 5 --ch-set psk "base64:${MESH868_PRIVATE_PSK}" && sleep 10
                bien "canal privado ${MESH868_PRIVATE_NAME:-BricoHams} (índice 5, AES-256) en el nodo 868"
            fi
            "${M[@]}" --set-owner "$MESH_LONG_NAME" --set-owner-short "$MESH_SHORT_NAME" && sleep 10
            "${M[@]}" --setlat "$STATION_LAT" --setlon "$STATION_LON" --setalt "$STATION_ASL" && sleep 5
            "${M[@]}" --set position.gps_mode NOT_PRESENT || true
            bien "nodo Meshtastic 868: $MESH_LONG_NAME ($MESH_SHORT_NAME), canales de MESH_CHANNEL_URL, posición fija"
        else
            aviso "meshtasticd no abre el puerto 4403 (¿pines LoRa? journalctl -u meshtasticd). Configura luego con: sudo bash install.sh --solo meshtastic"
        fi
    else
        aviso "Aún no existe /dev/$HAT_LORA_SPIDEV: reinicia y lanza 'sudo bash install.sh --solo meshtastic'"
    fi
}

paso_herramientas() {
    install -m 755 "$FILES/bin/bricohams-check" /usr/local/bin/bricohams-check
    install -m 755 "$FILES/bin/bricohams-sdr-serials" /usr/local/bin/bricohams-sdr-serials
    install -m 755 "$FILES/bin/bricohams-render-settings.py" /usr/local/bin/bricohams-render-settings
    install -m 755 "$FILES/bin/bricohams-merge-bookmarks.py" /usr/local/bin/bricohams-merge-bookmarks
    install -m 755 "$FILES/bin/bricohams-lilygo" /usr/local/bin/bricohams-lilygo
    install -m 755 "$FILES/bin/bricohams-servicios" /usr/local/bin/bricohams-servicios
    install -m 755 "$FILES/bin/bricohams-telegram" /usr/local/bin/bricohams-telegram
    # v4.2 · owrx-clone: exportar/importar perfiles de OpenWebRX+ (también lo usa la copia diaria)
    install -m 755 "$KIT/owrx-clone/owrx-clone" /usr/local/bin/owrx-clone
    install -D -m 644 "$KIT/owrx-clone/owrx-clone.1" /usr/local/share/man/man1/owrx-clone.1
    # v4.3 · bricohams-locator: zona de la estación (info, refrescar, marcadores --aplicar)
    install -d /usr/local/lib/bricohams
    install -m 644 "$FILES"/bin/bricohams_locator.py "$FILES"/bin/bricohams_locator_bookmarks.py \
        "$FILES"/bin/bricohams_locator_online.py /usr/local/lib/bricohams/
    install -m 755 "$FILES/bin/bricohams-locator" /usr/local/bin/bricohams-locator
    # copia del kit en la Raspberry para restaurar sin la tarjeta original
    install -d /opt/bricohams
    rsync -a --delete --exclude 'bricohams.env' "$KIT/" /opt/bricohams/kit/
    # copia de seguridad diaria de la configuración
    cat >/usr/local/sbin/bricohams-backup <<'EOF'
#!/bin/bash
# Copia de la configuración de la estación BricoHams en /var/backups/bricohams
set -e
d=/var/backups/bricohams; mkdir -p "$d"
f="$d/backup-openwebrx-$(date +%F).tar.gz"
# v4.3 · con OpenWebRX+ en Docker, sus tres carpetas y el docker-compose.yaml
OD=$( . /etc/bricohams/bricohams.env 2>/dev/null; echo "${OWRX_DOCKER_DIR:-/opt/owrx-docker}" ); OD=${OD#/}
tar -czf "$f" --ignore-failed-read -C / \
  var/lib/openwebrx/settings.json var/lib/openwebrx/users.json var/lib/openwebrx/bookmarks.json \
  var/lib/openwebrx/receiver_avatar.png var/lib/openwebrx/receiver_top_photo.png \
  etc/openwebrx usr/lib/python3/dist-packages/htdocs/plugins \
  "$OD/docker-compose.yaml" "$OD/etc" "$OD/var" "$OD/plugins" \
  etc/bricohams etc/meshtasticd etc/mediamtx etc/default/gpsd etc/chrony/conf.d boot/firmware/config.txt \
  etc/default/readsb etc/rbfeeder.ini etc/udev/rules.d/99-bricohams-lilygo.rules etc/udev/rules.d/99-bricohams-rs485.rules \
  etc/udev/rules.d/99-bricohams-io.rules etc/nginx/sites-available/bricohams-sdr etc/letsencrypt etc/mosquitto/conf.d \
  etc/cron.d/bricohams etc/sudoers.d/bricohams var/www/bricohams var/lib/bricohams 2>/dev/null
chmod 600 "$f"
ls -1t "$d"/backup-openwebrx-*.tar.gz | tail -n +15 | xargs -r rm -f
echo "$f"
EOF
    chmod 755 /usr/local/sbin/bricohams-backup
    cat >/etc/systemd/system/bricohams-backup.service <<'EOF'
[Unit]
Description=BricoHams: copia de seguridad de la configuración

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/bricohams-backup
EOF
    cat >/etc/systemd/system/bricohams-backup.timer <<'EOF'
[Unit]
Description=BricoHams: copia diaria

[Timer]
OnCalendar=*-*-* 04:30
Persistent=true

[Install]
WantedBy=timers.target
EOF
    systemctl daemon-reload
    if [ -f /etc/cron.d/bricohams ]; then
        systemctl disable --now bricohams-backup.timer 2>/dev/null || true   # la copia la lleva el cron (paso tareas)
    else
        systemctl enable --now bricohams-backup.timer
    fi
    bien "bricohams-check, bricohams-sdr-serials, copia diaria en /var/backups/bricohams y kit en /opt/bricohams/kit"
}

# =====================================================================
#  v4 · Puente USB «bricohams-io» (Raspberry Pi Pico): con el HAT puesto no
#  quedan pines libres; BME280, DS18B20, pluviómetro y ventiladores van a la Pico.
# =====================================================================
paso_io() {
    if [ "${IO_MODE:-pico}" != pico ]; then aviso "IO_MODE=${IO_MODE}: sensores y ventiladores en los GPIO de la Pi (sin HAT)"; return; fi
    apt_i python3-serial pipx
    install -m 755 "$FILES/bin/bricohams-io.py" /usr/local/bin/bricohams-io
    PIPX_HOME=/opt/pipx PIPX_BIN_DIR=/usr/local/bin pipx install mpremote >/dev/null 2>&1 || aviso "No pude instalar mpremote (sirve para grabar el firmware de la Pico)"
    # nombre fijo para la Pico con MicroPython (2e8a:0005)
    cat >/etc/udev/rules.d/99-bricohams-io.rules <<'EOF'
SUBSYSTEM=="tty", ATTRS{idVendor}=="2e8a", ATTRS{idProduct}=="0005", SYMLINK+="bricohams-io", GROUP="dialout", MODE="0660"
EOF
    udevadm control --reload && udevadm trigger --subsystem-match=tty || true
    # /run/bricohams compartido por bricohams-io (openwebrx), bricohams-fan (root) y bricohams-wx
    echo "d /run/bricohams 0775 openwebrx openwebrx -" >/etc/tmpfiles.d/bricohams.conf
    systemd-tmpfiles --create /etc/tmpfiles.d/bricohams.conf
    cat >/etc/systemd/system/bricohams-io.service <<'EOF'
[Unit]
Description=BricoHams: puente USB con la Pico (BME280, DS18B20, pluviómetro y ventiladores)
After=multi-user.target

[Service]
User=openwebrx
SupplementaryGroups=dialout
StateDirectory=bricohams
Environment=IO_PORT=/dev/bricohams-io
Environment=IO_FIRMWARE=/opt/bricohams/kit/firmware/pico-io/main.py
ExecStart=/usr/local/bin/bricohams-io
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    systemctl enable bricohams-io
    if [ -e /dev/bricohams-io ]; then
        [ -f /opt/bricohams/kit/firmware/pico-io/main.py ] || { install -d /opt/bricohams/kit/firmware/pico-io; cp "$KIT/firmware/pico-io/main.py" /opt/bricohams/kit/firmware/pico-io/; }
        IO_FIRMWARE="$KIT/firmware/pico-io/main.py" /usr/local/bin/bricohams-io instalar /dev/bricohams-io >/dev/null 2>&1 \
            && bien "firmware bricohams-io copiado a la Pico" || aviso "No pude copiar el firmware: sudo bricohams-io instalar (manual 20)"
        systemctl restart bricohams-io
        bien "Pico bricohams-io en /dev/bricohams-io"
    else
        aviso "No veo la Pico (/dev/bricohams-io). Grábale MicroPython (BOOTSEL + UF2), conéctala a la regleta y: sudo bricohams-io instalar (manual 20)"
    fi
}

# =====================================================================
#  v4 · Satélites: pases (aviso en la web + ▶ Escuchar con Doppler) y SatDump
#  para las imágenes LRPT de los METEOR (servicio de fondo de OpenWebRX+).
# =====================================================================
paso_satelites() {
    apt_i python3-sgp4
    install -m 755 "$FILES/bin/bricohams-satpass.py" /usr/local/bin/bricohams-satpass
    install -d -o openwebrx -g openwebrx "$HTDOCS/plugins/receiver/satelites"
    cat >/etc/systemd/system/bricohams-satpass.service <<EOF
[Unit]
Description=BricoHams: próximos pases de satélites para la web
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=openwebrx
StateDirectory=bricohams
Environment=STATION_LAT=${STATION_LAT}
Environment=STATION_LON=${STATION_LON}
Environment=STATION_ASL=${STATION_ASL}
Environment=SAT_LIST=/opt/bricohams/kit/data/satelites.json
ExecStart=/usr/local/bin/bricohams-satpass
EOF
    cat >/etc/systemd/system/bricohams-satpass.timer <<'EOF'
[Unit]
Description=BricoHams: pases de satélites cada 15 min

[Timer]
OnBootSec=2min
OnUnitActiveSec=15min

[Install]
WantedBy=timers.target
EOF
    systemctl daemon-reload
    systemctl enable --now bricohams-satpass.timer
    if si "${SATDUMP_ENABLE:-yes}" && ! command -v satdump >/dev/null; then
        local url tmp
        url=$("${CURL[@]}" https://api.github.com/repos/SatDump/SatDump/releases/latest 2>/dev/null \
            | jq -r --arg d "$DEB" '[.assets[].browser_download_url | select(test("(arm64|aarch64).*\\.deb$"; "i"))] as $a
                | ([$a[] | select(test($d; "i"))] + $a)[0] // empty')
        if [ -n "$url" ]; then
            tmp=$(mktemp -d)
            if "${CURL[@]}" -o "$tmp/satdump.deb" "$url" && apt-get install -y "$tmp/satdump.deb"; then
                bien "SatDump instalado (imágenes METEOR LRPT en «Files»)"
            else
                aviso "No pude instalar SatDump ($url): las imágenes METEOR no se decodificarán"
            fi
            rm -rf "$tmp"
        else
            aviso "No encuentro un paquete SatDump arm64 para $DEB en GitHub: https://github.com/SatDump/SatDump/releases"
        fi
    fi
    bien "pases de satélites cada 15 min ($(jq -r '.satelites | length' "$KIT/data/satelites.json") satélites) · aviso y ▶ Escuchar en la web"
}

# =====================================================================
#  v4 · FT2 (experimental): decodium-rx + modo FT2 en OpenWebRX+
# =====================================================================
paso_ft2() {
    if ! si "${FT2_ENABLE:-yes}"; then aviso "FT2 omitido (FT2_ENABLE)"; return; fi
    if [ "${OWRX_BACKEND:-native}" = docker ]; then     # el parche toca el código de OpenWebRX+, que va dentro de la imagen
        aviso "FT2 no está disponible con OpenWebRX+ en Docker (el parche cambia el código del paquete): usa OWRX_BACKEND=\"native\" si lo necesitas"
        return 0
    fi
    install -m 755 "$FILES/bin/bricohams-ft2" /usr/local/bin/bricohams-ft2
    install -m 755 "$FILES/bin/bricohams-ft2-decode" /usr/local/bin/bricohams-ft2-decode
    install -m 755 "$FILES/bin/bricohams-ft2-patch.py" /usr/local/sbin/bricohams-ft2-patch
    if ! command -v decodium-rx >/dev/null; then
        info "Compilando decodium-rx (20–40 min la primera vez)…"
        /usr/local/bin/bricohams-ft2 compilar || { aviso "No pude compilar decodium-rx. Inténtalo luego: sudo bricohams-ft2 compilar && sudo bricohams-ft2 activar"; return; }
    fi
    /usr/local/bin/bricohams-ft2 activar && bien "modo FT2 en OpenWebRX+ (experimental)" \
        || aviso "No pude activar FT2 (¿cambió OpenWebRX+?). sudo bricohams-ft2 estado"
}

# =====================================================================
#  v4 · Web: nginx con SSL (Let's Encrypt o autofirmado), portal de servicios,
#  aviso de privacidad y API de los plugins (bricohams-api).
# =====================================================================
paso_web() {
    apt_i nginx certbot openssl
    install -m 755 "$FILES/bin/bricohams-api.py" /usr/local/bin/bricohams-api
    install -m 755 "$FILES/bin/bricohams-servicios" /usr/local/bin/bricohams-servicios
    local ip dom cert key modo
    ip=$(hostname -I | awk '{print $1}')
    dom=${SSL_DOMAIN:-}
    modo=${SSL_MODO:-admin}
    case "$modo" in admin|todo|no) ;; *) fallo "SSL_MODO=\"$modo\" no vale: admin, todo o no" ;; esac
    # tar1090 (lighttpd) deja el puerto 80 a nginx y solo escucha en local
    if [ -f /etc/lighttpd/lighttpd.conf ]; then
        sed -i -E 's/^server\.port\s*=.*/server.port = 8504/' /etc/lighttpd/lighttpd.conf
        grep -q '^server.bind' /etc/lighttpd/lighttpd.conf || echo 'server.bind = "127.0.0.1"' >>/etc/lighttpd/lighttpd.conf
        systemctl restart lighttpd || true
    fi
    # web estática del portal
    install -d /var/www/bricohams /var/www/letsencrypt
    sed -e "s#__OPERADOR__#${CALLSIGN:-EA5KAO}#g" -e "s#__CONTACTO__#${ADMIN_EMAIL:-t.me/bricohams}#g" \
        -e "s#__DIAS__#${VISITAS_DIAS:-90}#g" "$FILES/web/privacidad.html" >/var/www/bricohams/privacidad.html
    sed -e "s#__LAN__#${ip}#g" -e "s#__WX_CALL__#${WX_APRS_CALLSIGN:-EA5KAO-13}#g" -e "s#__RADARBOX_ID__#${RADARBOX_STATION_ID:-}#g" \
        "$FILES/web/index.html.tmpl" >/var/www/bricohams/index.html
    # certificado: primero uno autofirmado para que nginx arranque
    install -d -m 700 /etc/bricohams/ssl
    if [ "$modo" != no ] && [ ! -s /etc/bricohams/ssl/autofirmado.crt ]; then
        openssl req -x509 -newkey rsa:2048 -nodes -days 3650 -subj "/CN=${dom:-$(hostname)}" \
            -keyout /etc/bricohams/ssl/autofirmado.key -out /etc/bricohams/ssl/autofirmado.crt 2>/dev/null
    fi
    cert=/etc/bricohams/ssl/autofirmado.crt; key=/etc/bricohams/ssl/autofirmado.key
    [ -n "$dom" ] && [ -s "/etc/letsencrypt/live/$dom/fullchain.pem" ] && { cert="/etc/letsencrypt/live/$dom/fullchain.pem"; key="/etc/letsencrypt/live/$dom/privkey.pem"; }
    # v4.2 · SSL_MODO: admin = receptor por HTTP y administración por HTTPS (decisión de EA5KAO)
    escribir_nginx() {
        install -d /etc/nginx/snippets
        install -m 644 "$FILES/nginx/bricohams-sdr-rutas.conf" /etc/nginx/snippets/bricohams-sdr-rutas.conf
        nginx_sitio "$modo" "${dom:-$(hostname)}" "$1" "$2" <"$FILES/nginx/bricohams-sdr.conf.tmpl" >/etc/nginx/sites-available/bricohams-sdr
        ln -sf /etc/nginx/sites-available/bricohams-sdr /etc/nginx/sites-enabled/bricohams-sdr
        rm -f /etc/nginx/sites-enabled/default
        nginx -t || fallo "nginx no acepta la configuración (mensaje de arriba): /etc/nginx/sites-available/bricohams-sdr"
        systemctl reload-or-restart nginx
    }
    escribir_nginx "$cert" "$key"
    if [ "$modo" != no ] && [ -n "$dom" ] && [ ! -s "/etc/letsencrypt/live/$dom/fullchain.pem" ]; then
        local correo=(--register-unsafely-without-email)
        [ -n "${SSL_EMAIL:-${ADMIN_EMAIL:-}}" ] && correo=(-m "${SSL_EMAIL:-${ADMIN_EMAIL:-}}")
        if certbot certonly --webroot -w /var/www/letsencrypt -d "$dom" "${correo[@]}" --agree-tos -n >>"$LOG" 2>&1; then
            escribir_nginx "/etc/letsencrypt/live/$dom/fullchain.pem" "/etc/letsencrypt/live/$dom/privkey.pem"
            bien "certificado Let's Encrypt para $dom (se renueva solo)"
        else
            aviso "Let's Encrypt falló para $dom: ¿apunta el dominio a tu IP y está abierto el puerto 80 del router? Sigo con el autofirmado. Reintenta: sudo bash install.sh --solo web"
        fi
    fi
    install -d /etc/letsencrypt/renewal-hooks/deploy
    printf '#!/bin/sh\nsystemctl reload nginx\n' >/etc/letsencrypt/renewal-hooks/deploy/bricohams-nginx.sh
    chmod 755 /etc/letsencrypt/renewal-hooks/deploy/bricohams-nginx.sh
    { envl SSL_DOMAIN "$dom"; envl SSL_MODO "${SSL_MODO:-admin}"; envl OWRX_BACKEND "${OWRX_BACKEND:-native}"; } >/etc/bricohams/web.env
    # API de los plugins (ficha de indicativos); HamQTH principal y QRZ opcional
    {
        envl HAMQTH_USER "${HAMQTH_USER:-}"
        envl HAMQTH_PASS "${HAMQTH_PASS:-}"
        envl QRZ_USER "${QRZ_USER:-}"
        envl QRZ_PASS "${QRZ_PASS:-}"
    } >/etc/bricohams/api.env
    chown root:openwebrx /etc/bricohams/api.env; chmod 640 /etc/bricohams/api.env
    cat >/etc/systemd/system/bricohams-api.service <<'EOF'
[Unit]
Description=BricoHams: API de indicativos (HamQTH/RadioID/QRZ)
After=network-online.target

[Service]
User=openwebrx
StateDirectory=bricohams
EnvironmentFile=/etc/bricohams/api.env
ExecStart=/usr/local/bin/bricohams-api
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    systemctl enable --now bricohams-api
    systemctl restart bricohams-api
    case "$modo" in
        admin) bien "nginx: receptor http://${dom:-$ip}/ · administración https://${dom:-$ip}/settings (forzada) · portal /bricohams/" ;;
        todo)  bien "nginx: todo por https://${dom:-$ip}/ · portal /bricohams/" ;;
        no)    aviso "nginx sin SSL (SSL_MODO=no): la contraseña de /settings viaja sin cifrar. Úsalo solo en la LAN" ;;
    esac
    if [ "$modo" != no ] && [ -z "$dom" ]; then
        aviso "Sin SSL_DOMAIN: certificado autofirmado (el navegador avisará). Pon el dominio en bricohams.env y: sudo bash install.sh --solo web"
    fi
}

# =====================================================================
#  v4 · Visitas: MQTT local + bricohams-visitas (GeoIP local, Telegram)
# =====================================================================
paso_visitas() {
    if ! si "${VISITAS_ENABLE:-yes}"; then aviso "Visitas omitidas (VISITAS_ENABLE)"; return; fi
    apt_i mosquitto python3-paho-mqtt python3-maxminddb
    cat >/etc/mosquitto/conf.d/bricohams.conf <<'EOF'
# BricoHams: MQTT solo para la propia Pi (avisos de OpenWebRX+ a bricohams-visitas)
listener 1883 127.0.0.1
allow_anonymous true
EOF
    systemctl enable mosquitto && systemctl restart mosquitto
    install -m 755 "$FILES/bin/bricohams-visitas.py" /usr/local/bin/bricohams-visitas
    install -m 755 "$FILES/bin/bricohams-telegram" /usr/local/bin/bricohams-telegram
    install -d -o openwebrx -g openwebrx "$HTDOCS/plugins/receiver/visitas"
    {
        envl TELEGRAM_TOKEN "${TELEGRAM_TOKEN:-}"
        envl TELEGRAM_CHAT_ID "${TELEGRAM_CHAT_ID:-}"
        echo "VISITAS_DIAS=${VISITAS_DIAS:-90}"
        echo "VISITAS_CHAT=${VISITAS_CHAT:-yes}"
        echo "VISITAS_AVISAR_LAN=${VISITAS_AVISAR_LAN:-no}"
        echo "VISITAS_AVISAR_DESCONEXION=${VISITAS_AVISAR_DESCONEXION:-no}"
        echo "VISITAS_OUT=$HTDOCS/plugins/receiver/visitas/visitas.json"
    } >/etc/bricohams/visitas.env
    chown root:openwebrx /etc/bricohams/visitas.env; chmod 640 /etc/bricohams/visitas.env
    { envl TELEGRAM_TOKEN "${TELEGRAM_TOKEN:-}"; envl TELEGRAM_CHAT_ID "${TELEGRAM_CHAT_ID:-}"; } >/etc/bricohams/telegram.env
    chmod 600 /etc/bricohams/telegram.env
    cat >/etc/systemd/system/bricohams-visitas.service <<'EOF'
[Unit]
Description=BricoHams: oyentes conectados, estadísticas y avisos por Telegram
After=mosquitto.service openwebrx.service
Wants=mosquitto.service

[Service]
User=openwebrx
StateDirectory=bricohams
EnvironmentFile=/etc/bricohams/visitas.env
ExecStart=/usr/local/bin/bricohams-visitas
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    [ -s /var/lib/bricohams/dbip-city-lite.mmdb ] || sudo -u openwebrx env STATE_DIRECTORY=/var/lib/bricohams /usr/local/bin/bricohams-visitas --geoip \
        || aviso "Sin base GeoIP todavía (se reintenta cada mes): las visitas saldrán sin país"
    systemctl enable --now bricohams-visitas
    systemctl restart bricohams-visitas
    owrx_control restart           # para que lea mqtt_enabled
    [ -n "${TELEGRAM_TOKEN:-}" ] && bien "visitas con avisos por Telegram" || aviso "Sin TELEGRAM_TOKEN/TELEGRAM_CHAT_ID: las visitas se cuentan pero no se avisan (manual 24)"
}

# =====================================================================
#  v4 · Tareas automáticas: cuenta de servicio «bricohams» + cron
#  (sin contraseñas guardadas: sudoers solo le deja ejecutar bricohams-tarea)
# =====================================================================
# =====================================================================
#  v4.2 · Importar un perfil de OpenWebRX+ (sudo bash install.sh --importar perfil.owrx.tar.gz)
#  Lo aplica owrx-clone (copia previa, sumas SHA-256, deshacer). Después el instalador
#  respeta lo importado: «configuracion» no regenera settings.json y «plugins» no pisa init.js.
# =====================================================================
paso_importar() {
    if [ -z "$IMPORTAR" ]; then
        if [ -f "$PERFIL_IMPORTADO" ]; then bien "perfil importado antes: $(grep -m1 '^PERFIL=' "$PERFIL_IMPORTADO" | cut -d= -f2-)"
        else bien "sin perfil que importar (sudo bash install.sh --importar FICHERO)"; fi
        return 0
    fi
    local oc=${OWRX_CLONE_BIN:-/usr/local/bin/owrx-clone} niveles=${IMPORTAR_NIVELES:-config,etc,web,paquetes}
    [ -n "${OWRX_CLONE_BIN:-}" ] || install -m 755 "$KIT/owrx-clone/owrx-clone" "$oc"
    local dk=()                     # v4.3 · en Docker, owrx-clone escribe en los volúmenes del contenedor
    if [ "${OWRX_BACKEND:-native}" = docker ]; then dk=(--docker "${OWRX_DOCKER_CONTAINER:-owrx-mbe}"); fi
    "$oc" "${dk[@]}" importar "$IMPORTAR" --si --niveles "$niveles" \
        || fallo "owrx-clone no ha podido importar $IMPORTAR (mensaje de arriba). Para volver atrás: sudo owrx-clone deshacer"
    # lo que BricoHams necesita de settings.json: el informe MQTT de las visitas
    if si "${VISITAS_ENABLE:-yes}" && [ -s "$OWRX_DATA/settings.json" ]; then
        python3 "$FILES/bin/bricohams-mqtt-settings.py" "$OWRX_DATA/settings.json"
        if [ "${OWRX_BACKEND:-native}" = docker ]; then owrx_owner; else chown openwebrx:openwebrx "$OWRX_DATA/settings.json"; fi
        owrx_control restart
    fi
    # un perfil público (o --sin-usuarios) no trae administrador: se crea aquí
    if [ ! -s "$OWRX_DATA/users.json" ] || [ "$(wc -c <"$OWRX_DATA/users.json")" -lt 5 ]; then
        info "El perfil no trae usuario de administración: crea la contraseña de '${OWRX_ADMIN_USER:-admin}':"
        if [ "${OWRX_BACKEND:-native}" = docker ]; then
            docker exec -it "${OWRX_DOCKER_CONTAINER:-owrx-mbe}" openwebrx admin adduser "${OWRX_ADMIN_USER:-admin}" </dev/tty \
                || aviso "Créalo luego dentro del contenedor ${OWRX_DOCKER_CONTAINER:-owrx-mbe}"
            owrx_owner
        else
            openwebrx admin adduser "${OWRX_ADMIN_USER:-admin}" </dev/tty || aviso "Créalo luego: sudo openwebrx admin adduser ${OWRX_ADMIN_USER:-admin}"
            chown openwebrx:openwebrx "$OWRX_DATA/users.json" 2>/dev/null || true
        fi
    fi
    install -d -m 755 /etc/bricohams
    { envl PERFIL "$IMPORTAR"; envl FECHA "$(date '+%F %T')"; envl NIVELES "$niveles"; } >"$PERFIL_IMPORTADO"
    bien "perfil $(basename "$IMPORTAR") importado (niveles: $niveles). Deshacer: sudo owrx-clone deshacer"
}

paso_tareas() {
    apt_i cron at
    install -m 755 "$FILES/bin/bricohams-tarea" /usr/local/sbin/bricohams-tarea
    install -m 755 "$FILES/bin/bricohams-telegram" /usr/local/bin/bricohams-telegram
    id bricohams >/dev/null 2>&1 || useradd --system --home-dir /var/lib/bricohams-svc --create-home --shell /usr/sbin/nologin \
        --comment "BricoHams cuenta de servicio" bricohams
    usermod -aG adm bricohams 2>/dev/null || true
    cat >/etc/sudoers.d/bricohams <<'EOF'
# BricoHams: la cuenta de servicio solo puede lanzar las tareas fijas de mantenimiento, sin contraseña
bricohams ALL=(root) NOPASSWD: /usr/local/sbin/bricohams-tarea
EOF
    chmod 440 /etc/sudoers.d/bricohams
    visudo -cf /etc/sudoers.d/bricohams >/dev/null || { rm -f /etc/sudoers.d/bricohams; fallo "sudoers de bricohams no válido"; }
    local T=/usr/local/sbin/bricohams-tarea
    cat >/etc/cron.d/bricohams <<EOF
# BricoHams SDR · tareas automáticas (las genera install.sh, paso «tareas»; horas en $(cat /etc/timezone 2>/dev/null || echo local))
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
MAILTO=""
${CRON_COPIA:-30 4 * * *}       bricohams  sudo -n $T copia
${CRON_ACTUALIZAR:-30 3 * * 1}       bricohams  sudo -n $T actualizar
${CRON_REINICIO:-0 5 * * 1}        bricohams  sudo -n $T reinicio
${CRON_SALUD:-*/30 * * * *}      bricohams  sudo -n $T salud
${CRON_RESUMEN:-0 21 * * *}        bricohams  sudo -n $T resumen
${CRON_GEOIP:-15 3 2 * *}        bricohams  sudo -n $T geoip
EOF
    if [ -n "${DUCKDNS_DOMAIN:-}" ] && [ -n "${DUCKDNS_TOKEN:-}" ]; then
        { envl DUCKDNS_DOMAIN "$DUCKDNS_DOMAIN"; envl DUCKDNS_TOKEN "$DUCKDNS_TOKEN"; } >/etc/bricohams/duckdns.env
        chown root:bricohams /etc/bricohams/duckdns.env; chmod 640 /etc/bricohams/duckdns.env
        echo '*/5 * * * *     bricohams  . /etc/bricohams/duckdns.env && curl -fsS -m 20 "https://www.duckdns.org/update?domains=${DUCKDNS_DOMAIN}&token=${DUCKDNS_TOKEN}&ip=" >/dev/null' >>/etc/cron.d/bricohams
    fi
    chmod 644 /etc/cron.d/bricohams
    systemctl disable --now bricohams-backup.timer 2>/dev/null || true     # la copia diaria la lleva ahora el cron
    touch /var/log/bricohams-tareas.log
    bien "cuenta de servicio «bricohams» + /etc/cron.d/bricohams (copia, actualización, reinicio, salud, resumen, GeoIP)"
}

# ---------------------------------------------------------------------
if [ "$ACTUALIZAR" -eq 1 ]; then
    if [ "$SIN_GIT" -eq 0 ] && [ "$CONTINUAR" -eq 0 ]; then info "Kit"; kit_git; fi
    arreglar_kit
    if [ "$SIMULAR" -eq 1 ]; then env_nuevas mostrar; else env_nuevas; fi
    cargar_env "$KIT/bricohams.env"
    if [ "$SIMULAR" -eq 0 ]; then info "Copia de seguridad"; copia_previa; fi
    if [ "$SIN_APT" -eq 0 ]; then info "Sistema"; sistema_actualizar; fi
    info "Pasos que hay que repetir"
    plan_actualizar
    if [ "$SIMULAR" -eq 1 ]; then echo; info "Simulación: no se ha cambiado nada."; exit 0; fi
    if [ ${#PLAN[@]} -le 1 ]; then
        bien "Los pasos de la estación ya estaban al día"; PLAN=(); resumen_actualizacion; exit 0
    fi
    SOLO=$(IFS=,; echo "${PLAN[*]}")
fi

for PASO_ACTUAL in "${PASOS[@]}"; do
    if [ -n "$SOLO" ] && [[ ",$SOLO," != *",$PASO_ACTUAL,"* ]]; then continue; fi
    echo; info "Paso: $PASO_ACTUAL"
    if necesita_red "$PASO_ACTUAL"; then esperar_red; fi   # v4.2: no empezar sin red un paso que baja cosas
    "paso_$PASO_ACTUAL"
    estado_guardar "$PASO_ACTUAL"          # huella del paso para --actualizar
done

if [ "$ACTUALIZAR" -eq 1 ]; then resumen_actualizacion; exit 0; fi

echo
info "Terminado."
cat <<EOF

  Siguientes pasos:
   1. Graba las series de los 4 RTL-SDR (una vez):  sudo bricohams-sdr-serials --grabar
   2. Identifica los LilyGO (una vez):              sudo bricohams-lilygo identificar
   3. Reinicia:                                     sudo reboot
   4. Configura los LilyGO:                         sudo bricohams-lilygo meshtastic && sudo bricohams-lilygo igate
   5. Comprueba todo:                               sudo bricohams-check

  Servicios:  bricohams-servicios        (lista con estado y direcciones)
  Web:        http://${SSL_DOMAIN:-$(hostname -I 2>/dev/null | awk '{print $1}')}/   · admin https://${SSL_DOMAIN:-$(hostname -I 2>/dev/null | awk '{print $1}')}/settings (SSL_MODO=${SSL_MODO:-admin})
  Meshtastic: https://$(hostname -I 2>/dev/null | awk '{print $1}'):9443
  Cámara:     http://$(hostname -I 2>/dev/null | awk '{print $1}'):8889/mastil/
  Aviones:    http://${SSL_DOMAIN:-$(hostname -I 2>/dev/null | awk '{print $1}')}/tar1090/
  Pico IO:    sudo bricohams-io estado      FT2: sudo bricohams-ft2 estado
EOF
[ "$REINICIAR" -eq 1 ] && aviso "Hay cambios de arranque (config.txt): hace falta reiniciar."
exit 0
