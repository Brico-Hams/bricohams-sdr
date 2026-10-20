#!/bin/bash
# Libera espacio borrando las copias de seguridad ANTIGUAS que dejan los despliegues, y conserva la
# más reciente de cada tipo. Solo borra si se escribe BORRAR en la terminal: antes muestra la lista
# exacta, el tamaño de cada copia y el espacio libre.
#
# Qué se considera copia de despliegue (nombre con fecha AAAAMMDD-HHMMSS):
#   /var/backups/bricohams/<tipo>-AAAAMMDD-HHMMSS[-PID]       (google-auth, archivo-files, mesh-dual…)
#   /var/backups/bricohams-<tipo>-AAAAMMDD-HHMMSS[.tar.gz[.sha256]]  (pretelegram, preblindaje, mapa…)
# No se tocan nunca:
#   las copias diarias (backup-openwebrx-AAAA-MM-DD.tar.gz, perfil-owrx-*.owrx.tar.gz), que ya tienen
#   su propia retención de cinco días; las de «deshacer» (/var/backups/bricohams-blindaje/,
#   /var/backups/owrx-clone/); ni ningún enlace simbólico.
# Uso: sudo bash tools/limpiar-copias-despliegue.sh [--lista]
#   --lista  solo muestra lo que se borraría (no pregunta ni borra)
set -Eeuo pipefail
umask 077
RAIZ="${BACKUPS_RAIZ:-/var/backups}"
SOLO_LISTA=0
[[ "${1:-}" == --lista ]] && SOLO_LISTA=1
[[ $EUID -eq 0 || -n "${BACKUPS_RAIZ:-}" ]] || { echo "Ejecuta con sudo." >&2; exit 1; }
[[ -d "$RAIZ" ]] || { echo "No existe $RAIZ: nada que limpiar."; exit 0; }

# «tipo<TAB>marca<TAB>ruta» de cada copia de despliegue; la marca (AAAAMMDDHHMMSS) ordena por fecha
candidatas() {
    local f n
    for f in "$RAIZ"/bricohams/* "$RAIZ"/bricohams-*; do
        [[ -e "$f" && ! -L "$f" ]] || continue
        n=${f##*/}
        if [[ "$n" =~ ^([a-z0-9][a-z0-9-]*[a-z0-9])-([0-9]{8})-([0-9]{6})(-[0-9]+)?(\.tar\.gz(\.sha256)?)?$ ]]; then
            [[ "${f%/*}" == "$RAIZ" ]] || [[ -d "$f" ]] || continue
            printf '%s\t%s%s\t%s\n' "${f%/*}/${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}" "${BASH_REMATCH[3]}" "$f"
        fi
    done
}

mapfile -t TODAS < <(candidatas | sort -t $'\t' -k1,1 -k2,2r)
BORRAR=()
CONSERVAR=()
declare -A ULTIMA=()
for l in "${TODAS[@]}"; do
    IFS=$'\t' read -r tipo marca ruta <<<"$l"
    # la .tar.gz y su .sha256 comparten marca: las dos se conservan o se borran juntas
    if [[ -z "${ULTIMA[$tipo]:-}" || "${ULTIMA[$tipo]}" == "$marca" ]]; then
        ULTIMA[$tipo]=$marca
        CONSERVAR+=("$ruta")
    else
        BORRAR+=("$ruta")
    fi
done

echo "Espacio libre en $RAIZ:"
df -h "$RAIZ" | tail -n 1
echo "Se conservan (la más reciente de cada tipo): ${#CONSERVAR[@]}"
for r in "${CONSERVAR[@]}"; do echo "  = $r"; done
if [[ ${#BORRAR[@]} -eq 0 ]]; then
    echo "No hay copias de despliegue antiguas que borrar."
    exit 0
fi
echo "Se BORRARÍAN (copias de despliegue antiguas): ${#BORRAR[@]}"
du -sch "${BORRAR[@]}" | sed 's/^/  - /'
[[ $SOLO_LISTA -eq 1 ]] && exit 0

if ! { exec 3<>/dev/tty; } 2>/dev/null; then
    echo "Sin terminal interactiva: no se borra nada."
    exit 0
fi
printf 'Escribe BORRAR para eliminarlas definitivamente (cualquier otra cosa: no se borra nada): ' >&3
read -r resp <&3 || resp=''
exec 3>&-
if [[ "$resp" != BORRAR ]]; then
    echo "No se ha borrado nada."
    exit 0
fi
for r in "${BORRAR[@]}"; do
    rm -rf --one-file-system -- "$r"
    echo "borrada: $r"
done
echo "Espacio libre ahora:"
df -h "$RAIZ" | tail -n 1
