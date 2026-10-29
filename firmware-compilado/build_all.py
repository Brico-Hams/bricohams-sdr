#!/usr/bin/env python3
"""Compila en lote firmware LoRa APRS iGate (CA2RXU) y Meshtastic con PlatformIO.

Uso:
  python build_all.py igate      --src DIR --out DIR [--jobs N] [--only env1,env2]
  python build_all.py meshtastic --src DIR --out DIR [--jobs N] [--only env1,env2]

Por cada entorno copia los binarios a OUT/<env>/, genera un "factory" fusionado
para ESP32 (flasheable en 0x0) y escribe OUT/SHA256SUMS y OUT/build_report.json.
El primer entorno se compila en solitario para que PlatformIO descargue las
toolchains sin condiciones de carrera; el resto en paralelo.
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Marcas pedidas para Meshtastic: Heltec, LilyGO (TTGO: tbeam/tlora/t-*) y Seeed Studio.
MESH_BRAND = re.compile(
    r"^(heltec|tbeam|tlora|t-|t5s3|seeed|xiao|wio|tracker-t1000)", re.I)
MESH_EXCLUDE = re.compile(r"(native|debug|sugarcube|t-energy|t-eth-elite)", re.I)

ENV_RE = re.compile(r"^\[env:([^\]]+)\]", re.M)


def pio_exe() -> str:
    here = Path(sys.executable).parent
    for name in ("pio.exe", "pio", "platformio.exe", "platformio"):
        cand = here / name
        if cand.exists():
            return str(cand)
    return shutil.which("pio") or "pio"


def list_envs(kind: str, src: Path) -> list[tuple[str, str]]:
    """Devuelve [(env, ruta_variant)]"""
    envs = []
    for ini in sorted((src / "variants").rglob("platformio.ini")):
        rel = ini.parent.relative_to(src / "variants").as_posix()
        for env in ENV_RE.findall(ini.read_text(encoding="utf-8", errors="ignore")):
            if kind == "meshtastic":
                if rel.split("/")[0] not in ("esp32", "esp32c3", "esp32c6", "esp32s3", "nrf52840"):
                    continue
                if not MESH_BRAND.search(env) or MESH_EXCLUDE.search(env):
                    continue
            envs.append((env, rel))
    return envs


def find_boot_app0() -> Path | None:
    base = Path.home() / ".platformio" / "packages"
    for p in base.glob("framework-arduinoespressif32*/tools/partitions/boot_app0.bin"):
        return p
    return None


def esptool_cmd() -> list[str]:
    base = Path.home() / ".platformio" / "packages" / "tool-esptoolpy"
    if (base / "esptool.py").exists():
        return [sys.executable, str(base / "esptool.py")]
    return [sys.executable, "-m", "esptool"]


def chip_of(build: Path) -> str:
    idf = build / "config" / "sdkconfig.json"
    text = ""
    for cand in (build / "sdkconfig.h", idf):
        if cand.exists():
            text = cand.read_text(errors="ignore")
            break
    for chip in ("esp32s3", "esp32c3", "esp32c6", "esp32s2"):
        if chip.upper() in text.upper():
            return chip
    return "esp32"


def merge_factory(build: Path, dest: Path, env: str) -> str | None:
    """Fusiona bootloader+particiones+boot_app0+app en un único .bin flasheable en 0x0."""
    boot, part, app = build / "bootloader.bin", build / "partitions.bin", build / "firmware.bin"
    if not (boot.exists() and part.exists() and app.exists()):
        return None
    chip = chip_of(build)
    boot_off = "0x0" if chip in ("esp32s3", "esp32c3", "esp32c6") else "0x1000"
    args = [*esptool_cmd(), "--chip", chip, "merge_bin", "-o",
            str(dest / f"{env}.factory.bin"), boot_off, str(boot), "0x8000", str(part)]
    ba0 = find_boot_app0()
    if ba0:
        args += ["0xe000", str(ba0)]
    args += ["0x10000", str(app)]
    r = subprocess.run(args, capture_output=True, text=True)
    return chip if r.returncode == 0 else None


def collect(kind: str, src: Path, env: str, out: Path) -> list[str]:
    build = src / ".pio" / "build" / env
    dest = out / env
    dest.mkdir(parents=True, exist_ok=True)
    files = []
    if kind == "meshtastic":
        pats = ("firmware-*.bin", "firmware-*.uf2", "firmware-*.hex", "firmware-*.zip",
                "littlefs-*.bin", "bleota*.bin")
        for pat in pats:
            for f in build.glob(pat):
                if f.name.endswith(".elf"):
                    continue
                shutil.copy2(f, dest / f.name)
                files.append(f.name)
        if not any(n.endswith(".factory.bin") for n in files):
            if merge_factory(build, dest, env):
                files.append(f"{env}.factory.bin")
    else:
        for name in ("firmware.bin", "bootloader.bin", "partitions.bin"):
            f = build / name
            if f.exists():
                shutil.copy2(f, dest / name)
                files.append(name)
        if merge_factory(build, dest, env):
            files.append(f"{env}.factory.bin")
    return files


def build_one(kind: str, src: Path, out: Path, logs: Path, env: str, rel: str) -> dict:
    t0 = time.time()
    log = logs / f"{env}.log"
    with open(log, "w", encoding="utf-8", errors="ignore") as fh:
        r = subprocess.run([pio_exe(), "run", "-e", env], cwd=src, stdout=fh,
                           stderr=subprocess.STDOUT, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    res = {"env": env, "variant": rel, "ok": r.returncode == 0,
           "seconds": round(time.time() - t0), "files": []}
    if res["ok"]:
        res["files"] = collect(kind, src, env, out)
        # Libera espacio: el árbol de objetos ya no se necesita.
        shutil.rmtree(src / ".pio" / "build" / env, ignore_errors=True)
    print(f"[{'OK ' if res['ok'] else 'ERR'}] {env} ({res['seconds']}s)", flush=True)
    return res


def write_sums(out: Path) -> None:
    lines = []
    for f in sorted(out.rglob("*")):
        if f.is_file() and f.suffix in (".bin", ".uf2", ".hex", ".zip"):
            h = hashlib.sha256(f.read_bytes()).hexdigest()
            lines.append(f"{h}  {f.relative_to(out).as_posix()}")
    (out / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=("igate", "meshtastic"))
    ap.add_argument("--src", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--only", default="")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    envs = list_envs(a.kind, a.src)
    if a.only:
        wanted = set(a.only.split(","))
        envs = [e for e in envs if e[0] in wanted]
    if a.list:
        for e, rel in envs:
            print(f"{e}\t{rel}")
        return 0

    a.out.mkdir(parents=True, exist_ok=True)
    logs = a.out / "_logs"
    logs.mkdir(exist_ok=True)
    report_path = a.out / "build_report.json"
    previous = {}
    if report_path.exists():
        previous = {r["env"]: r for r in json.loads(report_path.read_text())["results"]}
    todo = [e for e in envs if not previous.get(e[0], {}).get("ok")]
    print(f"{len(envs)} entornos, {len(todo)} pendientes", flush=True)

    results = dict(previous)
    if todo:
        first = todo.pop(0)
        results[first[0]] = build_one(a.kind, a.src, a.out, logs, *first)
        with cf.ThreadPoolExecutor(max_workers=a.jobs) as ex:
            futs = [ex.submit(build_one, a.kind, a.src, a.out, logs, *e) for e in todo]
            for fut in cf.as_completed(futs):
                r = fut.result()
                results[r["env"]] = r
                report_path.write_text(json.dumps(
                    {"kind": a.kind, "results": sorted(results.values(), key=lambda x: x["env"])},
                    indent=1))

    final = sorted((results[e] for e, _ in envs if e in results), key=lambda x: x["env"])
    report_path.write_text(json.dumps({"kind": a.kind, "results": final}, indent=1))
    write_sums(a.out)
    ok = sum(r["ok"] for r in final)
    print(f"Terminado: {ok}/{len(final)} correctos", flush=True)
    return 0 if ok == len(final) else 1


if __name__ == "__main__":
    sys.exit(main())
