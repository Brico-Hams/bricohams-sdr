#!/bin/bash
set -euo pipefail
raiz=$(cd "$(dirname "$0")/.." && pwd)
source "$raiz/files/bin/bricohams-backup-limpieza"
d=$(mktemp -d)
trap 'rm -f -- "$d"/*; rmdir -- "$d"' EXIT
limite=1700000000
antigua="$d/backup-openwebrx-2023-11-01.tar.gz"
perfil="$d/perfil-owrx-2023-11-01.owrx.tar.gz"
exacta="$d/backup-openwebrx-2023-11-02.tar.gz"
reciente="$d/backup-openwebrx-2023-11-03.tar.gz"
ajena="$d/no-es-una-copia.tar.gz"
enlace="$d/backup-openwebrx-2023-11-04.tar.gz"
touch -d "@$((limite - 1))" "$antigua" "$perfil" "$ajena"
touch -d "@$limite" "$exacta"
touch -d "@$((limite + 1))" "$reciente"
ln -s "$ajena" "$enlace"
salida=$(limpiar_copias "$d" "$limite" yes)
[[ "$salida" == *"$antigua"* && "$salida" == *"$perfil"* ]]
test -f "$antigua" && test -f "$perfil"
limpiar_copias "$d" "$limite" no
test ! -e "$antigua" && test ! -e "$perfil"
test -f "$exacta" && test -f "$reciente" && test -f "$ajena" && test -L "$enlace"
if limpiar_copias "$enlace" "$limite" no; then
    echo "ERROR: se ha aceptado un enlace como directorio" >&2
    exit 1
fi
limpiar_copias "$d/ausente" "$limite" no
if bash "$raiz/files/bin/bricohams-backup-limpieza" --invalid; then
    exit 1
fi
echo "test_backup_limpieza OK: umbral estricto, simulacion y alcance"
