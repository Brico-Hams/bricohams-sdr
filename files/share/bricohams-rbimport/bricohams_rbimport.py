# =====================================================================
#  owrx/controllers/settings/bricohams_rbimport.py  (BricoHams)
#
#  Importador de repetidores de RepeaterBook para el editor de
#  bookmarks de /settings (protegido con la contraseña de admin).
#
#  GET /settings/bookmarks/repeaterbook?pais=Spain&distrito=5
#        &bandas=2m,70cm&texto=&solo_activos=1&refrescar=0
#  -> JSON {ok, pais, total_pais, total, repetidores:[{name, frequency,
#     modulation:"nfm", ctcss?, description, scannable, existe, ...}]}
#
#  Solo propone bookmarks: el navegador los crea uno a uno con la API
#  del propio editor (POST /settings/bookmarks), que ya admite «ctcss»
#  (parche bricohams-owrx-ctcss). En la interfaz se llama «FM».
#
#  La API key se lee de la opción «repeaterbook_api_key» de General
#  Settings (parche bricohams-owrx-repeaterbook). Instalado por
#  bricohams-owrx-rbimport; no editar a mano.
# =====================================================================
import json
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from owrx.controllers import Controller
from owrx.controllers.admin import AuthorizationMixin

import logging

logger = logging.getLogger(__name__)

URL_ROW = "https://www.repeaterbook.com/api/exportROW.php"
URL_NA = "https://www.repeaterbook.com/api/export.php"
PAISES_NA = ("united states", "canada")
CACHE_SEG = 6 * 3600
TIMEOUT = 30

BANDAS = {
    "10m": (28.0, 29.7),
    "6m": (50.0, 54.0),
    "4m": (70.0, 70.5),
    "2m": (144.0, 148.0),
    "70cm": (430.0, 440.0),
    "23cm": (1240.0, 1300.0),
}

# Distrito de indicativo español (EA1..EA9) -> comunidades autónomas tal
# como las escribe RepeaterBook en «Region» (en minúsculas).
DISTRITOS_ES = {
    "1": ("galicia", "asturias", "cantabria", "castile y leon", "castilla y leon", "castile and leon"),
    "2": ("aragon", "navarre", "navarra", "bizkaia", "gipuzkoa", "araba", "pais vasco", "basque country", "la rioja"),
    "3": ("catalunya", "cataluna", "catalonia"),
    "4": ("comunidad de madrid", "madrid", "extremadura", "castile-la mancha", "castilla-la mancha"),
    "5": ("comunidad valenciana", "valencia", "murcia", "region de murcia"),
    "6": ("illes balears", "islas baleares", "balearic islands"),
    "7": ("andalusia", "andalucia"),
    "8": ("canarias", "canary islands"),
    "9": ("ceuta", "melilla"),
}

_cache = {}
_cerrojo = threading.Lock()


class RepeaterBookError(Exception):
    pass


def _texto(v):
    return "" if v is None else str(v).strip()


def _num(v):
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return None


def tono(v):
    """Subtono CTCSS válido (60-260 Hz) o None."""
    f = _num(v)
    if f is None or not (60.0 <= f <= 260.0):
        return None
    return round(f, 1)


def _version():
    try:
        from owrx.version import openwebrx_version
        return openwebrx_version
    except Exception:
        return "?"


def descargar(pais, clave, refrescar=False):
    """Lista 'results' de RepeaterBook para un país (con caché en memoria)."""
    if not clave:
        raise RepeaterBookError("Falta la API key de RepeaterBook (Settings → General settings).")
    na = pais.strip().lower() in PAISES_NA
    url = (URL_NA if na else URL_ROW) + "?" + urllib.parse.urlencode({"country": pais})
    with _cerrojo:
        c = _cache.get(url)
        if c and not refrescar and time.time() - c[0] < CACHE_SEG:
            return c[1]
    intentos = (
        {"Authorization": "Bearer " + clave, "X-RB-App-Token": clave,
         "User-Agent": "OpenWebRX/%s (BricoHams repeater import)" % _version()},
        {"X-RB-App-Token": clave, "User-Agent": "RepeaterBook Python Client/0.6.0 (+micael@jarniac.dev)"},
    )
    ultimo = None
    for cab in intentos:
        cab = dict(cab, Accept="application/json")
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=cab), timeout=TIMEOUT) as r:
                d = json.loads(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as x:
            ultimo = "HTTP %s" % x.code
            continue
        except (urllib.error.URLError, OSError, ValueError) as x:
            ultimo = str(getattr(x, "reason", x))
            continue
        if isinstance(d, dict) and isinstance(d.get("results"), list):
            res = d["results"]
            with _cerrojo:
                _cache[url] = (time.time(), res)
            return res
        ultimo = _texto(d.get("message") if isinstance(d, dict) else "") or "respuesta inesperada"
    raise RepeaterBookError("RepeaterBook no respondió correctamente (%s)." % ultimo)


def en_distrito(r, distrito):
    if not distrito:
        return True
    distrito = str(distrito).strip()
    ind = _texto(r.get("Callsign")).upper()
    if re.match(r"^E[A-H]" + re.escape(distrito), ind):
        return True
    reg = _texto(r.get("Region")).lower()
    return bool(reg) and reg in DISTRITOS_ES.get(distrito, ())


def banda_de(f):
    for n, (lo, hi) in BANDAS.items():
        if lo <= f <= hi:
            return n
    return None


def filtrar(lista, distrito="", bandas=("2m", "70cm"), texto="", solo_activos=True):
    texto = (texto or "").strip().lower()
    bandas = set(b for b in bandas if b in BANDAS)
    out = []
    for r in lista:
        if not isinstance(r, dict):
            continue
        if _texto(r.get("FM Analog")).lower() != "yes":
            continue
        if solo_activos and _texto(r.get("Operational Status")).lower() not in ("on-air", ""):
            continue
        f = _num(r.get("Frequency"))
        if f is None:
            continue
        b = banda_de(f)
        if bandas and b not in bandas:
            continue
        if not en_distrito(r, distrito):
            continue
        if texto:
            pajar = " ".join(_texto(r.get(k)) for k in ("Callsign", "Nearest City", "Landmark", "Region", "County", "Notes")).lower()
            if texto not in pajar:
                continue
        out.append(r)
    return out


def a_bookmark(r):
    f = _num(r.get("Frequency"))
    ind = _texto(r.get("Callsign")) or "REP"
    ciudad = _texto(r.get("Nearest City"))
    nombre = (ind + " " + ciudad).strip()[:60]
    ct = tono(r.get("TSQ")) or tono(r.get("PL"))
    ent = _num(r.get("Input Freq"))
    trozos = ["RepeaterBook"]
    if ciudad:
        trozos.append(ciudad)
    if ent:
        trozos.append("entrada %.4f MHz" % ent)
    trozos.append("subtono FM %.1f Hz" % ct if ct else "sin subtono")
    for k in ("Operational Status", "Use"):
        if _texto(r.get(k)):
            trozos.append(_texto(r.get(k)))
    if _texto(r.get("Notes")):
        trozos.append(_texto(r.get("Notes"))[:120])
    b = {
        "name": nombre,
        "frequency": int(round(f * 1e6)),
        "modulation": "nfm",
        "description": " · ".join(trozos),
        "scannable": True,
    }
    if ct:
        b["ctcss"] = ct
    return b, {
        "indicativo": ind,
        "ciudad": ciudad,
        "region": _texto(r.get("Region")),
        "banda": banda_de(f),
        "entrada": ent,
        "estado": _texto(r.get("Operational Status")),
        "uso": _texto(r.get("Use")),
    }


def proponer(lista, ocupadas):
    """Bookmarks propuestos (orden por frecuencia, sin repetir frecuencia)."""
    vistos = set()
    out = []
    for r in sorted(lista, key=lambda x: _num(x.get("Frequency")) or 0):
        b, info = a_bookmark(r)
        if b["frequency"] in vistos:
            continue
        vistos.add(b["frequency"])
        b.update(info)
        b["existe"] = ocupadas.get(b["frequency"])
        out.append(b)
    return out


def _indicativos(texto):
    return set(re.findall(r"\bE[A-H][0-9][A-Z0-9]{1,4}\b", (texto or "").upper()))


def elegir_tono(nombre, candidatos, distrito=""):
    """Subtono para un bookmark entre los repetidores RB con su misma salida.

    1) el que tenga el mismo indicativo que el nombre del bookmark;
    2) si no, los del distrito indicado (o todos si no hay distrito): solo
    si todos coinciden en el mismo subtono se asigna (si no -> None)."""
    if not candidatos:
        return None, None
    ind = _indicativos(nombre)
    for r in candidatos:
        if _texto(r.get("Callsign")).upper() in ind:
            return tono(r.get("TSQ")) or tono(r.get("PL")), _texto(r.get("Callsign"))
    g = [r for r in candidatos if en_distrito(r, distrito)] if distrito else candidatos
    tonos = set(tono(r.get("TSQ")) or tono(r.get("PL")) for r in g)
    tonos.discard(None)
    if len(tonos) == 1:
        return tonos.pop(), "/".join(sorted(set(_texto(r.get("Callsign")) for r in g)))[:40]
    return None, None


def asignar_tonos(bookmarks, lista, distrito="", sobrescribir=False):
    """Pone «ctcss» a los bookmarks FM (nfm) cuya frecuencia coincide con la
    salida de un repetidor RB. Devuelve la lista de cambios. No guarda."""
    por_f = {}
    for r in lista:
        if not isinstance(r, dict) or _texto(r.get("FM Analog")).lower() != "yes":
            continue
        f = _num(r.get("Frequency"))
        if f is not None:
            por_f.setdefault(int(round(f * 1e6)), []).append(r)
    cambios = []
    for b in bookmarks:
        if b.getModulation() != "nfm":
            continue
        if getattr(b, "ctcss", 0) and not sobrescribir:
            continue
        f = b.getFrequency()
        cand = por_f.get(f) or por_f.get(int(round(f / 1000.0)) * 1000) or []
        ct, origen = elegir_tono(b.getName(), cand, distrito)
        if ct and ct != getattr(b, "ctcss", 0):
            cambios.append({"name": b.getName(), "frequency": f, "ctcss": ct, "antes": getattr(b, "ctcss", 0) or None,
                            "origen": origen})
            b.ctcss = ct
    return cambios


def _ocupadas():
    try:
        from owrx.bookmarks import Bookmarks
        return {b.getFrequency(): b.getName() for b in Bookmarks.getSharedInstance().getEditableBookmarks()}
    except Exception:
        logger.exception("bricohams rbimport: no se pudieron leer los bookmarks")
        return {}


def _config():
    try:
        from owrx.config import Config
        pm = Config.get()
        clave = pm["repeaterbook_api_key"] if "repeaterbook_api_key" in pm else ""
        return _texto(clave)
    except Exception:
        logger.exception("bricohams rbimport: no se pudo leer la configuración")
        return ""


class RepeaterBookImportController(AuthorizationMixin, Controller):
    def _json(self, d, code=200):
        self.send_response(json.dumps(d, ensure_ascii=False), code=code, content_type="application/json",
                           headers={"Cache-Control": "no-store"})

    def indexAction(self):
        q = getattr(self.request, "query", {}) or {}

        def p(k, defecto=""):
            v = q.get(k)
            return v[0] if isinstance(v, list) and v else (v if isinstance(v, str) else defecto)

        pais = p("pais", "Spain").strip() or "Spain"
        if not re.match(r"^[A-Za-z .'-]{2,40}$", pais):
            return self._json({"ok": False, "error": "País no válido."}, 400)
        distrito = p("distrito").strip()
        if distrito and not re.match(r"^[0-9]$", distrito):
            return self._json({"ok": False, "error": "Distrito no válido (0-9)."}, 400)
        bandas = [b.strip() for b in p("bandas", "2m,70cm").split(",") if b.strip()]
        texto = p("texto")[:60]
        solo_activos = p("solo_activos", "1") != "0"
        refrescar = p("refrescar", "0") == "1"
        try:
            lista = descargar(pais, _config(), refrescar)
        except RepeaterBookError as x:
            return self._json({"ok": False, "error": str(x)}, 502)
        sel = filtrar(lista, distrito, bandas, texto, solo_activos)
        rep = proponer(sel, _ocupadas())
        logger.info("bricohams rbimport: %s distrito=%s bandas=%s -> %d de %d", pais, distrito or "-",
                    ",".join(bandas), len(rep), len(lista))
        return self._json({"ok": True, "pais": pais, "total_pais": len(lista), "total": len(rep), "repetidores": rep})

    def tonosAction(self):
        """POST: asigna el subtono FM de RepeaterBook a los bookmarks
        existentes que no lo tienen (o a todos si sobrescribir=1)."""
        try:
            d = json.loads(self.get_body().decode("utf-8") or "{}")
        except Exception:
            d = {}
        pais = _texto(d.get("pais")) or "Spain"
        distrito = _texto(d.get("distrito"))
        if not re.match(r"^[A-Za-z .'-]{2,40}$", pais) or (distrito and not re.match(r"^[0-9]$", distrito)):
            return self._json({"ok": False, "error": "Parámetros no válidos."}, 400)
        try:
            lista = descargar(pais, _config(), bool(d.get("refrescar")))
        except RepeaterBookError as x:
            return self._json({"ok": False, "error": str(x)}, 502)
        from owrx.bookmarks import Bookmarks
        bm = Bookmarks.getSharedInstance()
        cambios = asignar_tonos(bm.getEditableBookmarks(), lista, distrito, bool(d.get("sobrescribir")))
        if cambios:
            bm.store()
        logger.info("bricohams rbimport: subtonos asignados a %d bookmarks", len(cambios))
        return self._json({"ok": True, "total": len(cambios), "cambios": cambios})
