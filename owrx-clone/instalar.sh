#!/bin/bash
# =====================================================================
#  Instala owrx-clone en este equipo (o lo quita con --quitar)
#    sudo ./instalar.sh            → /usr/local/bin/owrx-clone + man owrx-clone
#    sudo ./instalar.sh --quitar
#  Necesita python3 (y openssl solo para perfiles cifrados).
# =====================================================================
set -euo pipefail
cd "$(dirname "$0")"
[ "$(id -u)" -eq 0 ] || { echo "Ejecútalo con sudo: sudo ./instalar.sh"; exit 1; }
if [ "${1:-}" = --quitar ]; then
    rm -f /usr/local/bin/owrx-clone /usr/local/share/man/man1/owrx-clone.1
    echo "owrx-clone quitado (las copias de /var/backups/owrx-clone se quedan)"
    exit 0
fi
command -v python3 >/dev/null || { echo "Falta python3: sudo apt install python3"; exit 1; }
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)' || { echo "Hace falta Python 3.7 o posterior"; exit 1; }
command -v openssl >/dev/null || echo "Aviso: sin openssl no podrás usar --cifrar (sudo apt install openssl)"
install -m 755 owrx-clone /usr/local/bin/owrx-clone
install -d /usr/local/share/man/man1
install -m 644 owrx-clone.1 /usr/local/share/man/man1/owrx-clone.1
command -v mandb >/dev/null && mandb -q 2>/dev/null || true
echo "Instalado: $(owrx-clone --version) · ayuda: owrx-clone ayuda · man owrx-clone"
