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
#   - Herramientas: bricohams-check, bricohams-sdr-serials, bricohams-lilygo.
#
#  Uso:
#    sudo bash install.sh                      # todo (vale aunque falte el permiso de ejecución)
#    sudo bash install.sh                         # igual, si install.sh es ejecutable
#    sudo bash install.sh --backup copia.tar.gz   # además restaura usuarios/marcadores de una copia
#    sudo bash install.sh --solo hat,meshtastic   # solo esos pasos
#    sudo bash install.sh --lista                 # ver los pasos
#  Se puede repetir sin miedo: cada paso deja el sistema igual.
#  Registro: /var/log/bricohams-install.log
# =====================================================================
set -Eeuo pipefail

KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES="$KIT/files"
LOG=/var/log/bricohams-install.log
HTDOCS=/usr/lib/python3/dist-packages/htdocs
OWRX_DATA=/var/lib/openwebrx
ETC_BH=/etc/bricohams
BOOTCFG=/boot/firmware/config.txt
CMDLINE=/boot/firmware/cmdline.txt
PASOS=(comprobar base red arranque hat openwebrx rtlsdr sdrplay configuracion plugins meteo sensor camara ventilacion adsb meshtastic lilygo herramientas)
BACKUP=""
SOLO=""
REINICIAR=0

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
        -h|--help) sed -n '2,38p' "$0"; exit 0 ;;
        *) fallo "Opción desconocida: $1" ;;
    esac
done

[ "$(id -u)" -eq 0 ] || fallo "Ejecútalo con sudo: sudo bash $0"
# Si el kit se copió por Windows, un móvil, un pendrive FAT o un unzip que no guarda
# permisos, los scripts pierden el bit de ejecución ("sudo: ./install.sh: command not found")
# y los ficheros de texto pueden traer finales de línea CRLF. Se reparan aquí.
chmod +x "$KIT/install.sh" "$FILES"/bin/* "$KIT"/tools/*.sh "$KIT"/tests/*.sh 2>/dev/null || true
for f in "$KIT/bricohams.env" "$KIT/install.sh" "$FILES"/bin/*; do
    [ -f "$f" ] && grep -q $'\r' "$f" && sed -i 's/\r$//' "$f"
done
[ -r "$KIT/bricohams.env" ] || fallo "Falta $KIT/bricohams.env: cp bricohams.env.example bricohams.env y rellena las claves (docs/manuales/02_INSTALACION.md)"
# shellcheck source=bricohams.env
. "$KIT/bricohams.env"
DEB=$(. /etc/os-release && echo "${VERSION_CODENAME:-}")   # bookworm | trixie: elige los repositorios
DEB_NUM=$([ "$DEB" = trixie ] && echo 13 || echo 12)
exec > >(tee -a "$LOG") 2>&1
echo; info "BricoHams SDR · instalación $(date '+%F %T')"

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

# ---------------------------------------------------------------------
paso_comprobar() {
    . /etc/os-release
    [ "$(uname -m)" = aarch64 ] || fallo "Hace falta Raspberry Pi OS de 64 bits (arm64)."
    case "${VERSION_CODENAME:-}" in
        bookworm|trixie) ;;
        *) fallo "Este sistema es '$PRETTY_NAME'. El kit funciona en Raspberry Pi OS Lite 64-bit Trixie (Debian 13) o Bookworm (Debian 12)." ;;
    esac
    grep -q 'Raspberry Pi 5' /proc/device-tree/model 2>/dev/null && bien "Raspberry Pi 5" || aviso "No parece una Raspberry Pi 5: los ajustes de arranque son para la Pi 5"
    curl -fsS --max-time 15 -o /dev/null "https://luarvique.github.io/ppa/$DEB/Release" \
        || fallo "Sin Internet o sin repositorio de OpenWebRX+ para $DEB (https://luarvique.github.io/ppa/$DEB/)"
    bien "$PRETTY_NAME arm64 con Internet y repositorio de OpenWebRX+ para $DEB"
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
    install -m 600 "$KIT/bricohams.env" "$ETC_BH/bricohams.env"
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
        if si "${FAN_ENABLE:-no}"; then
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
        nmcli connection delete "bricohams-wifi-$i" >/dev/null 2>&1 || true
        nmcli connection add type wifi con-name "bricohams-wifi-$i" ifname wlan0 ssid "$ssid" \
            wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$WIFI_PASS" \
            connection.autoconnect yes connection.autoconnect-priority "$prio" >/dev/null
        bien "WiFi '$ssid' (prioridad $prio)"
    done
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
    curl -fsSL https://luarvique.github.io/ppa/openwebrx-plus.gpg | gpg --yes --dearmor -o /etc/apt/trusted.gpg.d/openwebrx-plus.gpg
    echo "deb [signed-by=/etc/apt/trusted.gpg.d/openwebrx-plus.gpg] https://luarvique.github.io/ppa/$DEB ./" >/etc/apt/sources.list.d/openwebrx-plus.list
    apt_update
    apt_i openwebrx
    apt_i soapysdr-module-sdrplay3 || aviso "No pude instalar soapysdr-module-sdrplay3"
    systemctl enable openwebrx
    bien "OpenWebRX+ $(dpkg-query -W -f='${Version}' openwebrx 2>/dev/null)"
}

paso_sdrplay() {
    if ! si "$INSTALL_SDRPLAY_API"; then aviso "API de SDRplay omitida (INSTALL_SDRPLAY_API)"; return; fi
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
    systemctl stop openwebrx 2>/dev/null || true
    install -d -o openwebrx -g openwebrx "$OWRX_DATA"
    local stamp; stamp=$(date +%Y%m%d-%H%M%S)
    [ -f "$OWRX_DATA/settings.json" ] && cp "$OWRX_DATA/settings.json" "$OWRX_DATA/settings.json.antes-$stamp"
    # settings.json desde la plantilla + bricohams.env
    install -d -m 755 "$ETC_BH"; install -m 600 "$KIT/bricohams.env" "$ETC_BH/bricohams.env"
    set -a; . "$KIT/bricohams.env"; set +a
    python3 "$FILES/bin/bricohams-render-settings.py" "$FILES/openwebrx/settings.json.tmpl" "$OWRX_DATA/settings.json"
    install -m 644 "$FILES/openwebrx/bookmarks.json" "$OWRX_DATA/bookmarks.json"
    install -m 664 "$FILES/branding/receiver_avatar.png" "$OWRX_DATA/receiver_avatar.png"
    install -m 664 "$FILES/branding/receiver_top_photo.png" "$OWRX_DATA/receiver_top_photo.png"
    install -d /etc/openwebrx/openwebrx.conf.d
    install -m 644 "$FILES"/openwebrx/conf.d/*.conf /etc/openwebrx/openwebrx.conf.d/
    # restaurar desde una copia (usuarios y marcadores)
    if [ -n "$BACKUP" ]; then
        [ -r "$BACKUP" ] || fallo "No puedo leer la copia $BACKUP"
        local tmp; tmp=$(mktemp -d)
        tar -xzf "$BACKUP" -C "$tmp" var/lib/openwebrx/users.json var/lib/openwebrx/bookmarks.json 2>/dev/null || true
        [ -s "$tmp/var/lib/openwebrx/users.json" ] && install -m 600 "$tmp/var/lib/openwebrx/users.json" "$OWRX_DATA/users.json" && bien "usuarios restaurados de la copia"
        if [ -s "$tmp/var/lib/openwebrx/bookmarks.json" ]; then
            python3 "$FILES/bin/bricohams-merge-bookmarks.py" "$tmp/var/lib/openwebrx/bookmarks.json" \
                "$FILES/openwebrx/bookmarks.json" "$OWRX_DATA/bookmarks.json"
            bien "marcadores de la copia + los nuevos del kit"
        fi
        rm -rf "$tmp"
    fi
    chown -R openwebrx:openwebrx "$OWRX_DATA"
    if [ ! -s "$OWRX_DATA/users.json" ]; then
        info "Crea la contraseña del administrador '$OWRX_ADMIN_USER' de OpenWebRX:"
        openwebrx admin adduser "$OWRX_ADMIN_USER" </dev/tty || aviso "Crea el usuario luego: sudo openwebrx admin adduser $OWRX_ADMIN_USER"
        chown openwebrx:openwebrx "$OWRX_DATA/users.json" 2>/dev/null || true
    fi
    systemctl start openwebrx
    bien "OpenWebRX configurado: receptores, marcadores, imágenes BricoHams/Murcia"
}

paso_plugins() {
    local R="$HTDOCS/plugins/receiver"
    [ -d "$HTDOCS" ] || fallo "No existe $HTDOCS (¿OpenWebRX instalado?)"
    [ -f "$R/init.js" ] && cp "$R/init.js" "$R/init.js.antes-$(date +%Y%m%d-%H%M%S)"
    rsync -a --exclude 'meteo/meteo.json' --exclude 'camara/snap/' "$FILES/htdocs/plugins/" "$HTDOCS/plugins/"
    sed -i -e "s/__LAT__/${STATION_LAT}/" -e "s/__LON__/${STATION_LON}/" \
        -e "s/__CAM_SNAPSHOT_SECONDS__/${CAM_SNAPSHOT_SECONDS}/" "$R/init.js"
    install -d -o openwebrx -g openwebrx "$R/meteo" "$R/camara/snap"
    bien "plugins: rig_skin (DX), solar, meteo, cámara, BricoHams y los de 0xAF"
}

paso_meteo() {
    install -m 755 "$FILES/bin/bricohams-meteo.py" /usr/local/bin/bricohams-meteo
    cat >"$ETC_BH/meteo.env" <<EOF
AEMET_API_KEY=${AEMET_API_KEY}
METEO_STATIONS=${METEO_STATIONS}
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
        url=$(curl -fsSL https://api.github.com/repos/bluenviron/mediamtx/releases/latest \
            | jq -r '.assets[].browser_download_url' | grep -E 'linux_arm64(v8)?\.tar\.gz$' | head -1)
        [ -n "$url" ] || fallo "No encuentro MediaMTX para arm64"
        tmp=$(mktemp -d)
        curl -fsSL "$url" | tar -xz -C "$tmp"
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
WX_APRS_COMMENT=${WX_APRS_COMMENT}
APRS_PASSCODE=${APRS_PASSCODE}
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
    if i2cdetect -y 1 2>/dev/null | grep -Eq ' (76|77) '; then
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
EOF
    cat >/etc/systemd/system/bricohams-fan.service <<'EOF'
[Unit]
Description=BricoHams: ventiladores de la caja (PWM + tacómetro)
After=multi-user.target

[Service]
EnvironmentFile=/etc/bricohams/fan.env
RuntimeDirectory=bricohams
RuntimeDirectoryPreserve=yes
ExecStart=/usr/local/bin/bricohams-fan
Restart=always
RestartSec=15

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    systemctl enable bricohams-fan
    if ls /sys/class/pwm/pwmchip* >/dev/null 2>&1; then systemctl restart bricohams-fan; fi
    REINICIAR=1
    bien "ventiladores: PWM GPIO${FAN_PWM_GPIOS:-12,13}, tacómetros GPIO${FAN_TACH_GPIOS:-22,5}, DS18B20 en GPIO${W1_GPIO:-4} (tras reiniciar)"
}

paso_adsb() {
    if ! si "$ADSB_ENABLE"; then aviso "ADS-B omitido (ADSB_ENABLE)"; return; fi
    # 1) readsb (wiedehopf) con el FlightStick, elegido por su número de serie
    if ! command -v readsb >/dev/null; then
        bash -c "$(wget -nv -O - https://github.com/wiedehopf/adsb-scripts/raw/master/readsb-install.sh)"
    fi
    local biast=""
    si "$ADSB_BIAS_TEE" && biast=" --enable-biastee"
    sed -i "s|^RECEIVER_OPTIONS=.*|RECEIVER_OPTIONS=\"--device-type rtlsdr --device ${SERIAL_ADSB} --gain ${ADSB_GAIN} --ppm 0${biast}\"|" /etc/default/readsb
    if command -v readsb-set-location >/dev/null; then readsb-set-location "$STATION_LAT" "$STATION_LON" || true; fi
    # 2) mapa propio tar1090
    if si "$ADSB_TAR1090" && [ ! -d /usr/local/share/tar1090 ]; then
        bash -c "$(wget -nv -O - https://github.com/wiedehopf/tar1090/raw/master/install.sh)" || aviso "No pude instalar tar1090"
    fi
    # 3) AirNav RadarBox (rbfeeder) leyendo la salida Beast de readsb, con MLAT
    if ! command -v rbfeeder >/dev/null; then
        if [ "$DEB" = trixie ]; then
            # Trixie: repositorio de AirNav por apt (su script inst_rbfeeder.sh es para Bookworm)
            install -d -m 755 /etc/apt/keyrings
            curl -fsSL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0xF2A8428D3C354953" | gpg --yes --dearmor -o /etc/apt/keyrings/rb24.gpg
            echo "deb [signed-by=/etc/apt/keyrings/rb24.gpg] https://apt.rb24.com/ trixie main" >/etc/apt/sources.list.d/rb24.list
            apt_update
            apt_i rbfeeder || aviso "No pude instalar rbfeeder desde apt.rb24.com (trixie)"
        else
            bash -c "$(wget -O - http://apt.rb24.com/inst_rbfeeder.sh)" </dev/null || aviso "Fallo del instalador de rbfeeder"
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
        curl -fsSL "https://download.opensuse.org/repositories/network:Meshtastic:beta/Debian_$DEB_NUM/Release.key" | gpg --yes --dearmor -o /etc/apt/trusted.gpg.d/network_Meshtastic_beta.gpg
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
tar -czf "$f" --ignore-failed-read -C / \
  var/lib/openwebrx/settings.json var/lib/openwebrx/users.json var/lib/openwebrx/bookmarks.json \
  var/lib/openwebrx/receiver_avatar.png var/lib/openwebrx/receiver_top_photo.png \
  etc/openwebrx usr/lib/python3/dist-packages/htdocs/plugins \
  etc/bricohams etc/meshtasticd etc/mediamtx etc/default/gpsd etc/chrony/conf.d boot/firmware/config.txt \
  etc/default/readsb etc/rbfeeder.ini etc/udev/rules.d/99-bricohams-lilygo.rules etc/udev/rules.d/99-bricohams-rs485.rules var/lib/bricohams 2>/dev/null
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
    systemctl enable --now bricohams-backup.timer
    bien "bricohams-check, bricohams-sdr-serials, copia diaria en /var/backups/bricohams y kit en /opt/bricohams/kit"
}

# ---------------------------------------------------------------------
for PASO_ACTUAL in "${PASOS[@]}"; do
    if [ -n "$SOLO" ] && [[ ",$SOLO," != *",$PASO_ACTUAL,"* ]]; then continue; fi
    echo; info "Paso: $PASO_ACTUAL"
    "paso_$PASO_ACTUAL"
done

echo
info "Terminado."
cat <<EOF

  Siguientes pasos:
   1. Graba las series de los 4 RTL-SDR (una vez):  sudo bricohams-sdr-serials --grabar
   2. Identifica los LilyGO (una vez):              sudo bricohams-lilygo identificar
   3. Reinicia:                                     sudo reboot
   4. Configura los LilyGO:                         sudo bricohams-lilygo meshtastic && sudo bricohams-lilygo igate
   5. Comprueba todo:                               sudo bricohams-check

  Web:        http://$(hostname -I 2>/dev/null | awk '{print $1}'):8073   (admin: /settings)
  Meshtastic: https://$(hostname -I 2>/dev/null | awk '{print $1}'):9443
  Cámara:     http://$(hostname -I 2>/dev/null | awk '{print $1}'):8889/mastil/
  Aviones:    http://$(hostname -I 2>/dev/null | awk '{print $1}')/tar1090/
EOF
[ "$REINICIAR" -eq 1 ] && aviso "Hay cambios de arranque (config.txt): hace falta reiniciar."
exit 0
