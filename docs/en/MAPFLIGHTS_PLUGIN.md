# map.flights module for OpenWebRX+

**Language / Idioma:** English · [Español](../manuales/38_MAPFLIGHTS_PLUGIN.md)

## Scope and current status

This module is integrated into the kit. **It has not been deployed.**
The commands below are instructions for a future installation, not actions
performed by opening this document.

The module has two independent parts: the aircraft map requests map.flights
details for locally detected aircraft, and `/settings` retains the private
Beast/MLAT feed diagnostic panel at `/settings/bricohams/mapflights`.
It does not require a second OpenWebRX+ instance or another receiver.

Enable flight details at **General Settings → map.flights → Use map.flights for
aircraft details**. The optional **map.flights API key** password field in the
same section holds a private beta key (requested at
`https://map.flights/developers`); the server sends it in the `x-api-key`
header and retries anonymously if it is rejected. Empty means anonymous access
with lower limits. The key never reaches the browser. The browser calls only
the local API; the server looks up the aircraft ICAO when its detail card is
opened and caches responses for six hours. map.flights is the primary provider;
adsbdb and Planespotters remain fallbacks for missing fields. Disabling the
setting uses only those existing fallbacks.

The map displays **Powered by MAP.FLIGHTS**, its official icon and a link to
`https://map.flights`. Photo credit is retained when supplied by the API.
The current panel interface is in Spanish; this document is its English guide,
not an English interface translation.

## Data flow

```text
Dedicated 1090 MHz receiver
          |
        readsb ----> rbfeeder ----> RadarBox (existing feed retained)
          |
          +-------> feed.map.flights:30004 (tagged Beast, private station UUID)
          |
          +-------> separate mlat-client ----> mlat.map.flights:31090
          |                                  (same UUID; no result reinjection)
          +-------> local aircraft map

OpenWebRX+ /settings ----> authenticated, read-only administration panel
```

These are default destinations; the existing installer supports configured
host/port values. Sending occurs on the server, not in the browser.
See the [Spanish ADS-B procedure](../manuales/04_ADSB.md) for the underlying feed.

For aircraft details, the local map keeps readsb positions and the server
queries `https://map.flights/api/v1/aircraft/{hex}`. Only the selected aircraft
ICAO is sent; receiver coordinates are not sent. Detail lookup is independent
of the outgoing Beast/MLAT feed and its private UUID.

## Requirements

- An existing supported BricoHams/OpenWebRX+ installation, with its web
  administration service and HTTPS reverse proxy.
- Working readsb reception from a dedicated ADS-B receiver.
- Existing RadarBox configuration preserved if already feeding RadarBox.
- A map.flights station UUID to enable the additional feed.
- A verified backup and a documented restoration procedure before applying
  any installation or configuration change.

Run commands in **Bash on the Raspberry Pi**, from the kit directory containing
`install.sh`, not in PowerShell on your PC.

## Install the panel (future deployment only)

1. Back up all affected files, configuration and data. Verify the backup,
   record its location and prepare a restoration procedure.
   See the [maintenance manual in Spanish](../manuales/09_MANTENIMIENTO.md).
   **Stop if backup creation or verification fails.**
2. Review the kit configuration, SSL settings and existing web services.
3. If deployment is authorized, apply the web step:

```bash
sudo bash install.sh --solo web
sudo nginx -t
systemctl status bricohams-mesh-admin nginx --no-pager
```

The `web` step also configures other web components: it is **not** an isolated
button-only installer. It does not automatically execute the ADS-B step.

Open `/settings` over HTTPS and sign in as an OpenWebRX+ administrator. Enable
**General Settings → map.flights → Use map.flights for aircraft details**.
The feed diagnostic panel remains available at `/settings/bricohams/mapflights`.
The API and feed UUID are independent; the UUID is not published and no account
iframe is embedded.

## Enable feeding (separate from panel installation)

1. Check local reception and confirm RadarBox is receiving data.
2. With a verified backup, edit the kit's `bricohams.env` in a private editor:
   set `MAPFLIGHTS_FEED="yes"`, enter your station's own `MAPFLIGHTS_UUID` and
   choose `MAPFLIGHTS_MLAT` according to whether you want MLAT participation.
3. Preserve `RADARBOX_KEY`, the receiver serial and the actual station position.
   Do not put private values in shared command lines or screenshots.
4. Apply and check:

```bash
sudo bash install.sh --solo adsb
sudo bricohams-check
```

The ADS-B step briefly restarts readsb/rbfeeder. It retains the RadarBox feed.
Installing or viewing the panel alone does not modify an existing feed.

### UUID, API keys and attribution

The Beast integration uses the **station UUID**, shared with its separate MLAT
client. The `mf_feed_` feed key is not used by this method.
No adsb.lol, adsb.fi or aircraft-database API key is required for this outgoing feed.

The public aircraft-detail endpoint needs no credentials. The server keeps the
required photo credit and the map displays the official MAP.FLIGHTS attribution.
Do not use the feed UUID or an `mf_feed_` key as an API credential.

## Verify and troubleshoot

| Panel indication | What it establishes | What it does not establish |
|---|---|---|
| Feeding requested | Saved `MAPFLIGHTS_FEED` setting | Connector actually applied |
| Valid UUID | Hexadecimal format | Ownership or account acceptance |
| readsb active | Local process state | Useful RF reception or positions |
| rbfeeder active | RadarBox process state | Data accepted by the RadarBox portal |
| MLAT active | Separate client process state | Completed handshake or accepted participation |

```bash
systemctl status readsb rbfeeder --no-pager
# Only expected when map.flights MLAT is enabled:
systemctl status bricohams-mapflights-mlat --no-pager
```

Confirm positions in **both provider portals**. Check the MLAT journal locally
for its handshake; it may contain the private UUID and station location, so
anonymize it before sharing.

Without an administrator session, the panel redirects to login. It rejects
POST changes. If configuration cannot be read, it displays an error: check
permissions and the service rather than making private files publicly readable.

## Disable or restore

To stop only map.flights feeding, first verify your backup, set
`MAPFLIGHTS_FEED="no"` in the kit configuration, then repeat `--solo adsb`.
RadarBox is retained. The panel can remain installed to show the disabled state.

To restore an earlier panel version, restore the affected files from the
verified backup and restart the administration service according to your
recorded procedure. Re-running the installer is not a general rollback.
Do not extract an unknown archive over `/`.

## Implementation and tests

| Surface | Source |
|---|---|
| Administration backend and page registration | [bricohams-mesh-admin](../../files/bin/bricohams-mesh-admin) |
| Idempotent settings button and existing apt hook | [bricohams-owrx-botones](../../files/bin/bricohams-owrx-botones) |
| Existing nginx panel proxy; no new public port | [bricohams-sdr-rutas.conf](../../files/nginx/bricohams-sdr-rutas.conf) |
| Beast connector helper | [bricohams-mapflights.py](../../files/bin/bricohams-mapflights.py) |
| Web/ADS-B installation steps | [install.sh](../../install.sh) |
| Session, read-only access, hidden UUID, POST rejection and HEAD tests | [test_mesh_admin.py](../../tests/test_mesh_admin.py) |
| Connector and preservation of other destinations | [test_mapflights.py](../../tests/test_mapflights.py) |

Tests use simulated services and temporary files; they do not require real
credentials or send aircraft data to providers. Passing these tests is not
proof of a live deployment or remote reception.
