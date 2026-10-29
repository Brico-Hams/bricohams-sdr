# Modules and how they were developed

[Versión en español](../DESARROLLO_MODULOS.md) · [Visual installation guide (ES)](../GUIA_VISUAL_MODULOS.md) ·
[Component catalogue (ES)](../COMPONENTES.md) · [Decisions / ADR (ES)](../ARQUITECTURA.md)

This document lists the modules developed for BricoHams SDR and, for each one,
explains **why it was created, how it was designed, which files make it up, how
it is installed and tested, and its current status**. The Spanish document is
the reference; ADR numbers point to [ARQUITECTURA.md](../ARQUITECTURA.md).

> **Privacy:** examples use generic values. Callsigns, coordinates, IPs, UUIDs,
> keys and passwords live only in `/etc/bricohams/bricohams.env` or in secret
> files on the Pi and are never copied into documentation.

## Module index

| # | Module | Main installer step | Status |
|---|---|---|---|
| 1 | Installer, configuration and updater | `install.sh` | integrated |
| 2 | OpenWebRX+ (native and Docker) | `openwebrx`, `configuracion` | integrated |
| 3 | owrx-clone | `--exportar`, `--importar` | integrated, publishable |
| 4 | Web plugins and in-browser audio | `plugins` | integrated |
| 5 | Bookmarks import/export and CTCSS | `configuracion`, `web` | integrated |
| 6 | RepeaterBook importer | `web` | integrated |
| 7 | Locator, area and channels | `configuracion` | integrated |
| 8 | Meshtastic 868/433 and private panel | `meshtastic`, `lilygo` | integrated |
| 9 | RAK4631 LoRa APRS iGate | `rak` | integrated |
| 10 | ADS-B, RadarBox, map and aircraft card | `adsb`, `web` | integrated |
| 11 | ADS-B feed to map.flights | `adsb` | optional; verified on one station |
| 12 | map.flights panel for OpenWebRX+ | `web` | generated, not deployed |
| 13 | Weather, sensors, Pico I/O and fans | `meteo`, `sensor`, `io`, `ventilacion` | integrated |
| 14 | Camera | `camara` | integrated |
| 15 | Satellites and FT2 | `satelites`, `ft2` | integrated; FT2 experimental |
| 16 | Web, SSL, API, visitors and chat | `web`, `visitas` | integrated |
| 17 | TAK and local map | `tak` | integrated |
| 18 | Monitoring | `monitorizacion` | optional |
| 19 | Security and blocking | `bricohams-blindaje` | integrated |
| 20 | Backups, remote backup and cleanup | `tareas`, `herramientas` | integrated |
| 21 | Hardware and generated documentation | `tools/` | integrated |

## Common development method

1. Each design decision is recorded as an ADR.
2. New variables go to `bricohams.env.example` with generic values; the file is
   read, never executed (ADR-38).
3. Each feature is an idempotent `paso_*` in `install.sh`, repeatable with `--solo`.
4. Services listen on `127.0.0.1`; administration lives under `/settings`;
   secrets use mode `600` or `LoadCredential`.
5. Tests in `tests/` use fake roots under `/tmp`: `bash tests/run_tests.sh`.
6. Every module gets a manual, a catalogue entry, a changelog entry and a visual card.
7. Deployment only with authorisation and a verified prior backup with a
   documented restore procedure.

```bash
sudo bash install.sh --solo step1,step2
sudo bricohams-check
```

## Development summary per module

1. **Installer** — started in v1.0 for Bookworm; secrets moved out of git in v2.0
   (ADR-12); Trixie support in v3.1–v3.3; `--actualizar` with per-step
   fingerprints in v4.1 (ADR-37); safe `.env` parsing (ADR-38); 29 steps today.
2. **OpenWebRX+** — one SDR per function by serial number (ADR-02), HF by direct
   sampling (ADR-03), Docker with host network in v4.3 (ADR-44).
3. **owrx-clone** — v4.2 MIT tool to export/import an OpenWebRX+ profile with
   levels, SHA-256, `--simular` and `deshacer`; two security reviews fixed path
   escapes and symlink writes; 1.1 unifies native and Docker (ADR-42, ADR-45).
4. **Web plugins and audio** — local plugins (ADR-11), browser-side audio filter
   and DSP (ADR-41), DX cluster spots on the frequency bar in v5.0.
5. **Bookmarks and CTCSS** — three-way merge in v4.1, native import/export form
   (ADR-58), tone stored in the bookmark with tone squelch (ADR-60).
6. **RepeaterBook** — API key in General Settings (ADR-59) and area importer (ADR-61).
7. **Locator** — national catalogue in the kit (ADR-43), cached downloads that never
   stop the installation (ADR-46).
8. **Meshtastic** — HAT 868 and LilyGO 433 nodes, own MQTT subscriber for the map
   (ADR-50), configuration only under `/settings` (ADR-53).
9. **RAK4631 iGate** — radio on the RAK, Internet through the Pi (ADR-49);
   credentials via `LoadCredential`.
10. **ADS-B** — readsb → rbfeeder → MLAT → tar1090 outside OpenWebRX+ (ADR-04),
    sanitised aircraft on the map (ADR-55), photo/route proxy with cache (ADR-69).
11. **map.flights feed** — extra Beast connector to `feed.map.flights:30004` plus a
    separate MLAT client to `mlat.map.flights:31090` (ADR-70); uses the station
    UUID, not the `mf_feed_` key; RadarBox untouched; reception confirmed by the
    provider on 2026-10-15.
12. **map.flights panel** — read-only page at `/settings/bricohams/mapflights`;
    never shows the UUID, rejects POST with 405; tests passed in isolation;
    generated, not deployed. See [MAPFLIGHTS_PLUGIN.md](MAPFLIGHTS_PLUGIN.md).
13. **Weather and sensors** — BME280 (ADR-08), fans (ADR-23), wind/rain (ADR-25),
    Pico I/O (ADR-29), RAK sensors and GPS in v5.0.
14. **Camera** — MediaMTX (ADR-09); RTSP IP camera recommended (ADR-24).
15. **Satellites and FT2** — pass prediction with one-click Doppler listening
    (ADR-31); experimental FT2 with a reversible patch (ADR-35).
16. **Web and visitors** — nginx with SSL (ADR-32), visitor stats with truncated IPs
    and Telegram (ADR-33), HTTPS for admin (ADR-40), rounded public position
    (ADR-48), APRS in the common chat (ADR-57), chat moderator (ADR-68).
17. **TAK** — isolated OpenTAKServer with Python 3.12 (ADR-54), private map layer
    (ADR-56), `/settings` panels and random credentials (ADR-62, ADR-63).
18. **Monitoring** — Prometheus, node-exporter and Grafana behind `/settings`;
    adopts manual installs (ADR-62, ADR-64).
19. **Security** — audit-first hardening with rollback (ADR-47), IP/country
    blocking with nftables (ADR-65), users and firewall from `/settings` (ADR-66),
    login alerts by Telegram (ADR-67).
20. **Backups** — daily backup (ADR-13), remote backup to SMB/NFS/SFTP/Drive/OneDrive
    with SHA-256 check, and `bricohams-backup-limpieza.timer` (daily 06:15)
    removing eligible local backups older than 120 hours.
21. **Hardware and docs** — parametric enclosure, mounts and antennas
    (ADR-15…ADR-23, ADR-30); visual guide with anonymised screenshots and a checker.

## OpenWebRX+ plugins, one by one

Every plugin lives in **its own folder** — the layout OpenWebRX+ requires
(`plugins/receiver/<name>/<name>.js`). Do not move or merge them. Loading order
and activation are set in `files/htdocs/plugins/receiver/init.js` and
`files/htdocs/plugins/map/init.js`.

```bash
sudo bash install.sh --solo plugins   # then reload the page with Ctrl+F5
```

| Plugin | Origin | Purpose |
|---|---|---|
| `idioma` | BricoHams | ES/EN switch |
| `marca` | BricoHams | Station logo |
| `consentimiento` | BricoHams | Cookie and third-party content notice |
| `solar` | BricoHams | Solar data and HF propagation |
| `meteo` | BricoHams | Nearby weather stations |
| `camara` | BricoHams | Mast camera |
| `bricohams` | BricoHams | Station look and feel |
| `banderas` | BricoHams | Country flags in digital-mode messages |
| `dvficha` | BricoHams | Operator card for DMR/YSF/NXDN/D-Star |
| `satelites` | BricoHams | Upcoming passes and one-click listening |
| `visitas` | BricoHams | Live listeners and visit counter |
| `identificacion` | BricoHams | Voluntary listener registration; required to chat |
| `ea5hkx_puente` | BricoHams | Adapter for EA5HKX plugins |
| `audio_cadena` | BricoHams | Shared audio chain (load before filters) |
| `filtro_audio` | BricoHams | FILTER button |
| `dsp_audio` | BricoHams | DSP button |
| `bricohams_live` (map) | BricoHams | Aircraft, APRS tracks, TAK layer, aircraft card |
| `layer_qth_maidenhead`, `reduce_map_legend_sections` (map) | community | Grid layer, compact legend |
| `utils`, `notify`, `colorful_spectrum`, `compact_analog_modes`, `screenshot`, `toggle_scannable`, `search_bookmarks`, `doppler` | 0xAF | Third-party receiver plugins |
| `rig_skin` | aganet | Radio front-panel theme |
| `callsign_gate`, `tone_detector` | EA5HKX | Welcome gate and tone detector |

Server-side `/settings` extensions (bookmarks I/O, CTCSS, RepeaterBook,
settings buttons and the map.flights panel) are listed in the Spanish document.
