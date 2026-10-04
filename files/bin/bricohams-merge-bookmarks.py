#!/usr/bin/env python3
# Une los marcadores de una copia con los del kit (sin duplicar frecuencia+modo).
# Uso: bricohams-merge-bookmarks.py copia.json kit.json salida.json
import json, sys
base = json.load(open(sys.argv[1], encoding='utf-8'))
kit = json.load(open(sys.argv[2], encoding='utf-8'))
have = {(b['frequency'], b['modulation']) for b in base}
added = [b for b in kit if (b['frequency'], b['modulation']) not in have]
json.dump(base + added, open(sys.argv[3], 'w', encoding='utf-8'), indent=4, ensure_ascii=False)
print('marcadores: %d de la copia + %d nuevos del kit' % (len(base), len(added)))
