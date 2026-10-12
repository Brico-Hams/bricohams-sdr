#!/bin/bash
# =====================================================================
#  tools/git_sanear.sh · BricoHams SDR (v5.1, manual 38)
#
#  Diagnostica (y con --reparar arregla) por qué la carpeta del kit no se
#  sincroniza con GitHub. Pensado para Git Bash en Windows y para Linux.
#
#  Lo que mira:
#   1. Copias de conflicto que deja un cliente de sincronización en la nube
#      DENTRO de .git («(# Name clash … #)», «(# Edit conflict … #)»,
#      «conflicted copy», «sync-conflict»). Rompen las referencias: git avisa
#      «ignoring ref with broken name» y la rama sale como [gone].
#   2. Referencias rotas (ficheros de ref vacíos o con 0000…) y ficheros .lock
#      viejos que bloquean commit/pull.
#   3. Si la rama remota existe y cuántos commits vamos por delante/detrás.
#   4. Que bricohams.env NO está en el índice y que .gitignore existe.
#   5. Ficheros de más de 50 MB en el índice (GitHub rechaza >100 MB).
#   6. Si la carpeta está dentro de OneDrive/Proton Drive/Dropbox/Google Drive/iCloud.
#
#  Con --reparar: mueve las copias de conflicto y los .lock viejos a
#  .git/_conflictos_<fecha>/ (no borra nada), quita refs rotas, hace
#  «git fetch --prune» y, si el remoto solo va por delante, avisa del pull.
#  Nunca hace push ni toca credenciales.
#
#  Uso:  bash tools/git_sanear.sh            (solo diagnóstico)
#        bash tools/git_sanear.sh --reparar
# =====================================================================
set -u
REPARAR=no
[ "${1:-}" = "--reparar" ] && REPARAR=yes
cd "$(git rev-parse --show-toplevel 2>/dev/null || dirname "$0")/" || exit 1
[ -d .git ] || { echo "✘ No es la raíz de un repositorio git"; exit 1; }
export GIT_OPTIONAL_LOCKS=0
GITDIR=.git
FECHA=$(date +%Y%m%d-%H%M%S)
APARTE="$GITDIR/_conflictos_$FECHA"
problemas=0
ok()   { echo "  ✔ $*"; }
mal()  { echo "  ✘ $*"; problemas=$((problemas + 1)); }
info() { echo "  · $*"; }
apartar() {   # mueve dentro de .git/_conflictos_<fecha>/ conservando la ruta
    local f="$1" destino
    destino="$APARTE/${f#"$GITDIR"/}"
    mkdir -p "$(dirname "$destino")" && mv -n "$f" "$destino" && info "apartado: $f"
}

echo "== 1. Copias de conflicto de la nube dentro de .git"
mapfile -t CONFL < <(find "$GITDIR" -path "$GITDIR/_conflictos_*" -prune -o \
    \( -name '*Name clash*' -o -name '*Edit conflict*' -o -name '*conflicted copy*' -o -name '*sync-conflict*' \
       -o -name '*(1)' -o -name '* (1).*' \) -print 2>/dev/null)
if [ "${#CONFL[@]}" -eq 0 ]; then ok "ninguna"; else
    mal "${#CONFL[@]} copias de conflicto (las crea el cliente de sincronización, no git)"
    for f in "${CONFL[@]}"; do info "$f"; done
    if [ "$REPARAR" = yes ]; then for f in "${CONFL[@]}"; do apartar "$f"; done; fi
fi

echo "== 2. Referencias rotas y bloqueos"
rotas=0
while IFS= read -r f; do
    c=$(head -c 200 "$f" 2>/dev/null)
    if [ -z "$c" ] || [[ "$c" =~ ^0{40} ]]; then
        mal "ref rota: $f"; rotas=$((rotas + 1))
        [ "$REPARAR" = yes ] && apartar "$f"
    fi
done < <(find "$GITDIR/refs" -type f 2>/dev/null)
[ "$rotas" -eq 0 ] && ok "refs bien"
mapfile -t LOCKS < <(find "$GITDIR" -path "$GITDIR/_conflictos_*" -prune -o -name '*.lock' -mmin +10 -print 2>/dev/null)
if [ "${#LOCKS[@]}" -eq 0 ]; then ok "sin .lock viejos"; else
    mal "${#LOCKS[@]} ficheros .lock de más de 10 min (git se cortó a medias)"
    if [ "$REPARAR" = yes ]; then for f in "${LOCKS[@]}"; do apartar "$f"; done; fi
fi
if [ "$REPARAR" = yes ]; then
    git symbolic-ref refs/remotes/origin/HEAD >/dev/null 2>&1 || true
    git fsck --no-dangling --connectivity-only >/dev/null 2>&1 && ok "fsck sin errores" || mal "git fsck da errores: git fsck --no-dangling"
fi

echo "== 3. Remoto"
URL=$(git remote get-url origin 2>/dev/null || true)
if [ -z "$URL" ]; then mal "no hay remoto origin"; else
    echo "$URL" | grep -q '@' && mal "la URL del remoto lleva usuario/token: git remote set-url origin https://github.com/<cuenta>/<repo>.git"
    info "origin = $(echo "$URL" | sed -E 's#://[^@/]+@#://***@#')"
    RAMA=$(git symbolic-ref --short HEAD 2>/dev/null || echo main)
    if [ "$REPARAR" = yes ]; then
        GIT_TERMINAL_PROMPT=0 git fetch --prune origin 2>&1 | sed 's/^/    /' || true
    fi
    if REMOTO=$(GIT_TERMINAL_PROMPT=0 git ls-remote origin "refs/heads/$RAMA" 2>/dev/null | cut -f1) && [ -n "$REMOTO" ]; then
        ok "la rama $RAMA existe en GitHub (${REMOTO:0:7})"
        if git cat-file -e "$REMOTO" 2>/dev/null; then
            delante=$(git rev-list --count "$REMOTO..HEAD"); detras=$(git rev-list --count "HEAD..$REMOTO")
            info "vas $delante por delante y $detras por detrás"
            [ "$detras" -gt 0 ] && [ "$delante" -gt 0 ] && mal "ramas divergentes: git pull --rebase origin $RAMA (o merge) antes del push"
            [ "$detras" -gt 0 ] && [ "$delante" -eq 0 ] && info "solo falta traer: git pull --ff-only"
            [ "$detras" -gt 0 ] && git diff --name-status HEAD "$REMOTO" | grep -q $'^D\t.gitignore$' && \
                mal "el remoto BORRA .gitignore (commit hecho en la web): al traerlo, recupéralo antes de cualquier git add"
        else
            info "no tengo el commit remoto: git fetch origin"
        fi
    else
        mal "no puedo leer la rama $RAMA en GitHub (¿sin red, repo privado sin credenciales o rama borrada?)"
    fi
    git branch -vv 2>/dev/null | grep -q '\[origin/[^]]*: gone\]' && \
        info "git dice [gone]: falta refs/remotes/origin/$RAMA en local (se arregla con el fetch de --reparar)"
fi

echo "== 4. Claves fuera del git"
[ -f .gitignore ] && ok ".gitignore presente" || mal "falta .gitignore (bricohams.env podría subirse): git checkout HEAD~1 -- .gitignore"
if git ls-files --error-unmatch bricohams.env >/dev/null 2>&1; then
    mal "bricohams.env ESTÁ en el índice: git rm --cached bricohams.env y cambia sus claves (ya han salido)"
else ok "bricohams.env no está en el git"; fi
git check-ignore -q bricohams.env && ok "bricohams.env ignorado" || mal "bricohams.env no está en .gitignore"

echo "== 5. Ficheros grandes en el índice"
grandes=$(git ls-files -z | xargs -0 -I{} sh -c 'f="{}"; [ -f "$f" ] && s=$(wc -c <"$f") && [ "$s" -gt 52428800 ] && echo "$s $f"' 2>/dev/null)
if [ -z "$grandes" ]; then ok "ninguno de más de 50 MB"; else mal "ficheros enormes (GitHub corta en 100 MB):"; echo "$grandes" | sed 's/^/    /'; fi
sin=$(git status --porcelain --ignored=no 2>/dev/null | awk '$1=="??"{print $2}' | head -20)
[ -n "$sin" ] && info "sin seguimiento: $(echo "$sin" | tr '\n' ' ')"

echo "== 6. ¿Carpeta sincronizada con la nube?"
RUTA=$(pwd -W 2>/dev/null || pwd)
if echo "$RUTA" | grep -qiE 'onedrive|proton ?drive|dropbox|google ?drive|icloud|nextcloud|pcloud|mega'; then
    mal "el repo está en una carpeta de la nube ($RUTA): sácalo o excluye .git de la sincronización"
elif [ "${#CONFL[@]}" -gt 0 ]; then
    mal "hay copias de conflicto: aunque la ruta no lo diga, algo sincroniza esta carpeta (p. ej. Documentos en la nube)"
else ok "no lo parece"; fi

echo
if [ "$problemas" -eq 0 ]; then echo "✔ Todo bien: git push debería funcionar."; else
    echo "✘ $problemas problemas.$([ "$REPARAR" = no ] && echo ' Para arreglar lo automático: bash tools/git_sanear.sh --reparar')"
fi
[ "$REPARAR" = yes ] && [ -d "$APARTE" ] && echo "Lo apartado está en $APARTE (bórralo cuando todo vaya bien)."
exit $((problemas > 0))
