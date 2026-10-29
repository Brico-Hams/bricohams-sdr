#!/bin/bash
# Instala ayuda integrada y soporte OAuth del backup sin cambiar credenciales.
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo 'Ejecutar con sudo.' >&2; exit 1; }
origen=$(realpath -e "${1:?Uso: actualizar-guias-modulos.sh KIT_ORIGEN KIT_INSTALADO [OTRO_KIT]}")
shift
[[ $# -gt 0 ]] || { echo 'Indica al menos un kit instalado.' >&2; exit 1; }
python=${BRICOHAMS_PYTHON:-/usr/bin/python3}
for f in files/bin/bricohams-mesh-admin files/bin/bricohams-backup-remoto \
         docs/manuales/47_CONFIGURACION_MODULOS.md tests/test_backup_oauth.py; do
    [[ -f "$origen/$f" ]] || { echo "Falta $f" >&2; exit 1; }
done
"$python" - "$origen" <<'PY'
import ast
import pathlib
import sys
root = pathlib.Path(sys.argv[1])
for name in ('bricohams-mesh-admin', 'bricohams-backup-remoto'):
    ast.parse((root / 'files/bin' / name).read_text(encoding='utf-8'), filename=name)
PY
unidades=$(systemctl list-units --type=service --state=active,activating --no-legend --plain 'bricohams-backup-remoto@*')
if grep -q 'bricohams-backup-remoto@' <<< "$unidades"; then
    echo 'Hay un trabajo de backup remoto activo. Reintentar cuando termine.' >&2
    exit 1
fi
if [[ -d /run/bricohams-backup-remoto ]]; then
    exec 9>/run/bricohams-backup-remoto/lock
    flock -n 9 || { echo 'Backup remoto ocupado.' >&2; exit 1; }
fi
umask 077
backup=$(mktemp -d /var/backups/bricohams-guias-XXXXXXXX)
declare -a fuentes destinos
fuentes=("$origen/files/bin/bricohams-mesh-admin" "$origen/files/bin/bricohams-backup-remoto")
destinos=(/usr/local/bin/bricohams-mesh-admin /usr/local/sbin/bricohams-backup-remoto)
for kit in "$@"; do
    kit=$(realpath -e "$kit")
    [[ "$kit" != / && "$kit" != "$origen" && -f "$kit/install.sh" ]] || {
        echo 'Destino no es un kit instalado distinto del origen.' >&2; exit 1;
    }
    for f in files/bin/bricohams-mesh-admin files/bin/bricohams-backup-remoto \
             docs/manuales/47_CONFIGURACION_MODULOS.md docs/manuales/46_ACCESO_GOOGLE.md \
             docs/DESARROLLO_MODULOS.md tests/test_backup_oauth.py tests/test_mesh_admin.py \
             tests/run_tests.sh CHANGELOG.md README.md VERSION tools/actualizar-guias-modulos.sh; do
        [[ -f "$origen/$f" ]] || { echo "Falta $f" >&2; exit 1; }
        fuentes+=("$origen/$f")
        destinos+=("$kit/$f")
    done
done
: > "$backup/existentes.txt"
: > "$backup/nuevos.txt"
for d in "${destinos[@]}"; do
    [[ ! -L "$d" ]] || { echo "Destino simbolico inesperado: $d" >&2; exit 1; }
    if [[ -e "$d" ]]; then
        printf '%s\n' "${d#/}" >> "$backup/existentes.txt"
    else
        printf '%s\n' "$d" >> "$backup/nuevos.txt"
    fi
done
tar -C / -czpf "$backup/estado-previo.tar.gz" -T "$backup/existentes.txt"
tar -tzf "$backup/estado-previo.tar.gz" > "$backup/contenido.txt"
tar -C / -dzf "$backup/estado-previo.tar.gz"
sha256sum "$backup/estado-previo.tar.gz" > "$backup/SHA256SUMS"
cat > "$backup/RESTAURAR.sh" <<'RESTORE'
#!/bin/bash
set -euo pipefail
[[ $EUID -eq 0 ]] || exit 1
b=$(cd -- "$(dirname -- "$0")" && pwd)
sha256sum -c "$b/SHA256SUMS"
tar -xzpf "$b/estado-previo.tar.gz" -C /
while IFS= read -r p; do
    if [[ -f "$p" && ! -L "$p" ]]; then rm -- "$p"; fi
done < "$b/nuevos.txt"
systemctl restart bricohams-mesh-admin
systemctl is-active --quiet bricohams-mesh-admin
curl --retry 10 --retry-connrefused --retry-delay 1 --retry-max-time 30 \
    --max-time 5 -fsS -o /dev/null http://127.0.0.1:8076/settings/bricohams/seguridad
echo 'RESTAURACION_COMPLETADA'
RESTORE
chmod 700 "$backup/RESTAURAR.sh"
bash -n "$backup/RESTAURAR.sh"
sha256sum -c "$backup/SHA256SUMS"
printf 'BACKUP_VERIFICADO=%s\nRESTAURAR=sudo bash %s/RESTAURAR.sh\n' "$backup" "$backup"
# Se comprueban hashes sin imprimir valores de credenciales.
secretos=(/etc/bricohams/bricohams.env /etc/bricohams/backup-remoto.json /etc/bricohams/backup-remoto.secret)
: > "$backup/secretos.sha256"
for f in "${secretos[@]}"; do
    [[ ! -f "$f" ]] || sha256sum "$f" >> "$backup/secretos.sha256"
done
cambio=0
restaurar_error() {
    r=$?
    trap - ERR
    if [[ $cambio -eq 1 ]]; then
        echo "Fallo de despliegue; restaurando $backup" >&2
        bash "$backup/RESTAURAR.sh" || echo "RESTAURACION FALLIDA: ejecutar $backup/RESTAURAR.sh" >&2
    fi
    exit "$r"
}
trap restaurar_error ERR
cambio=1
for i in "${!destinos[@]}"; do
    d=${destinos[$i]}
    modo=644
    [[ "$d" != */files/bin/* && "$d" != /usr/local/bin/* && "$d" != /usr/local/sbin/* && "$d" != *.sh ]] || modo=755
    install -D -m "$modo" "${fuentes[$i]}" "$d"
    cmp "${fuentes[$i]}" "$d"
done
[[ ! -s "$backup/secretos.sha256" ]] || sha256sum -c "$backup/secretos.sha256" > "$backup/secretos-verificados.txt"
systemctl restart bricohams-mesh-admin
systemctl is-active --quiet bricohams-mesh-admin
codigo=$(curl --retry 10 --retry-connrefused --retry-delay 1 --retry-max-time 30 \
    --max-time 5 -fsS -o /dev/null -w '%{http_code}' \
    'http://127.0.0.1:8076/settings/bricohams/seguridad?ayuda=1')
[[ "$codigo" == 302 ]] || { echo "La ayuda sin sesion debe redirigir al login, HTTP=$codigo" >&2; false; }
systemctl is-active ssh nginx openwebrx bricohams-api
curl --max-time 10 -fsS -o /dev/null -w 'HTTP %{http_code}\n' http://127.0.0.1/
trap - ERR
printf 'DESPLIEGUE_GUIAS_OK\n'
