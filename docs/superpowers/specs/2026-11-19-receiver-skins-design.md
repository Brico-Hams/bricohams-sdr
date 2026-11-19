# Receiver skins: Brico-FX (FTX-1-inspired) and vintage military, as independent public plugins

Date: 2026-11-19 · Status: draft, pending approval by EA5KAO

## Intent

Listeners of the BricoHams SDR (OpenWebRX+ 1.2.130 on the Pi) should be able to switch the receiver's
look between four styles:

1. **Brico-FX** — FTX-1-inspired front panel (new, **default on the BricoHams SDR**): looks like a modern Yaesu FTX-1 front panel,
   **without Yaesu names or logos** (registered trademarks).
2. **Vintage military radio** (new): analog meters with **needles**, big round **wheels/knobs**,
   olive-drab / bakelite feel.
3. **Rig** (current): today's `rig_skin` (SV1DOD / HB9ISH), unchanged.
4. **Original**: stock OpenWebRX+ look.

Each new skin must be an **independent OpenWebRX+ receiver plugin** that can be published on its own
public GitHub repository and installed by any OpenWebRX+ operator, without the BricoHams kit.

Why: the station also runs a real FTX-1; the SDR should feel like the station's radio, a retro option
adds character, and publishing the skins gives something back to the OpenWebRX+ community.

## Goals

- Two standalone plugins, each self-contained (own JS + CSS, no dependency on rig_skin or on other
  BricoHams plugins):
  - `bh_skin_bricofx` → theme id `bh-bricofx`, label "Brico-FX"
  - `bh_skin_militar` → theme id `bh-militar`, label "Military"
- Each registers itself in OpenWebRX+'s own theme listbox (the same mechanism rig_skin uses:
  `<option>` in `#openwebrx-themes-listbox`, `UI.theme`, body class) so it coexists with Rig and the
  stock theme and works with any combination of installed skins.
- Each skin provides a working front panel: frequency display, tuning knob (drag/wheel/flick, step from
  the tuning-step selector), S-meter, mode buttons, volume and squelch. Military: S-meter with a
  **needle** following the real signal level, functional wheels for volume and squelch.
- Mobile (≤767 px) usable in every style.
- On the BricoHams SDR only (kit side, not in the public plugins):
  - a visible selector in the BricoHams panel section, in sync with the OpenWebRX+ theme listbox;
  - **everyone is switched to `bh-bricofx` once** (new visitors and returning ones, including those who
    had Rig, set automatically or not), marked with a localStorage flag `bh_bricofx_default`; from then
    on the visitor's own choice is kept. Rig, Military and Original stay selectable. The kit's existing
    `RIG_POR_DEFECTO` block in `init.js` is removed/replaced so the two defaults do not compete.
- Brico-FX screen (EA5KAO's request): inside the TFT-like screen, a **mini spectrum/waterfall** of the
  receiver (reusing OpenWebRX+'s data, not a second decoder), and **selectable views** via a DISP-like
  button and the soft-key bar (at least: frequency + meter, scope/waterfall, digital-mode view). When a
  digital mode is selected (FT8, FT4, WSPR, JS8, RTTY, packet…), the screen shows the digital view: the
  decoded messages OpenWebRX+ already produces, plus the mini waterfall. Knobs: VFO (tuning), AF/SQL
  (volume, squelch) and FUNC (cycles functions such as step / NR / filter width), all working.
- Rig-only extras (DX cluster window, PROP/SAT screens, spot ribbon, VFO line) stay in Rig; Brico-FX and
  Military do not reimplement them (Claude's call; EA5KAO did not ask for them in the new skins).

## Non-goals

- No transmit, no CAT control.
- No pixel-exact replica of the FTX-1.
- No changes to rig_skin; it stays the upstream plugin.

## Anti-goals (failure even if it works)

- Any Yaesu trademark, logo or product photo in the UI or in the public repos.
- Code copied from rig_skin (or any other third-party plugin) into the public skins: they must be
  original work so they can carry their own licence.
- Breaking Rig or the stock theme, or skins fighting each other over the DOM when several are installed.
- Heavy assets (no images > ~50 KB, no extra web fonts).
- Invented FTX-1 visual "facts": colours and layout come from the photo EA5KAO provided (below).

## Constraints

- OpenWebRX+ plugin API (1.2.124+): plugins load via `init.js` (`Plugins.load`), optional
  `Plugins.<name>.no_css`; native helpers `Plugins.addButton/addWindow/addSection`.
- Theme switching must clean up: when the user picks another theme, the skin removes its body class,
  its DOM and its event handlers, so switching back and forth leaves no leftovers.
- Plugin JS/CSS on the BricoHams SDR is served with `Cache-Control: no-cache` (nginx).
- BricoHams colour manual v1.1 applies to BricoHams chrome (the kit selector); the skins use their own
  palettes, text must meet WCAG 2.2 AA.
- Deploys to `/usr/lib/python3/dist-packages/htdocs/plugins/receiver/` need sudo on the Pi.

## Approaches considered

- A. Overlay CSS on top of rig_skin: rejected — depends on rig_skin, cannot be published standalone.
- B. Fork rig_skin into an own engine (first pick by EA5KAO): replaced after EA5KAO asked for
  independent skins publishable individually — a fork carries rig_skin's code and licence and is one
  big plugin, not separate skins.
- **C. Independent, original plugins, one per skin — chosen.** Each skin is written from scratch
  against the OpenWebRX+ plugin API; a shared look is not required. Trade-off: some duplicated
  widget code (knob, meter) between the two skins, accepted so each repo stands alone.

## Decided

- Development lives in the kit repo under `files/htdocs/plugins/receiver/bh_skin_bricofx/` and
  `.../bh_skin_militar/`, each with its own `README.md`, `LICENSE` (MIT, author EA5KAO / BricoHams)
  and screenshot, laid out so the folder can be copied as-is to its own public repo.
- **Publishing the public repos is a separate step that needs EA5KAO's explicit go-ahead.**
- Kit side: `init.js` loads both skins; the selector and the "default to bh-bricofx" rule live in the
  kit's `bricohams.js` (not in the public plugins).

## Builder's calls (made by Claude, EA5KAO can correct)

- **S-meter calibration**: each skin reads its own optional global config
  (`window.bh_skin_bricofx_config.smeter`, `window.bh_skin_militar_config.smeter`, same shape as
  `rig_skin_config.smeter`: `offset_hf`, `offset_vhf`, `iaru_vhf`); without it, the meter shows the
  uncalibrated level. The kit's `init.js` fills both with the station's existing rig_skin values.
- **Waterfall/spectrum**: the skins do not register waterfall themes nor change `wf_theme`; they only
  style the panel around it (avoids clashing with `colorful_spectrum`).
- **Language**: each skin carries its labels in English and Spanish and picks by
  `document.documentElement.lang` (fallback English); the kit's `idioma` button keeps working because it
  sets that attribute.

## Pending source (do not invent)

## Visual references (photos from EA5KAO, 2026-11-19; observed, not invented)

**Brico-FX** — EA5KAO's own FTX-1 (photo `images/7.jpg` of the session, not to be published):
- Matte black body with rounded corners; wide colour screen on the left two thirds, controls on the right.
- Screen: light blue/white status strip on top with small icons and an orange-on-black tag ("ANT TUNE");
  big light-blue/cyan italic frequency digits ("145.525.000"); white outlined mode box ("FM").
- Meter top-left: white scale `S 1 3 5 7 9`, cyan `+20 +40 +60 dB`, second scale `PO 10 50 100 150 W`,
  a red needle-like bar, and a `VOL` row with a red level line.
- Lower screen: two dark panes (left one larger, right one a list with a grey title strip) and a
  soft-key bar at the bottom with white labels on dark blue (e.g. ALL · SEARCH · ENTER ID · CATEGORY ·
  DISCONNECT · LOG).
- Right side: large knurled black VFO knob with a smooth spun-metal centre and a **blue LED arc** on
  both sides; rounded black keys with white labels: QMB, CLAR, DISP, BACK; small BUSY/TX SUB MAIN lamps.
- Knobs: FUNC (top right), MAIN AF/RF/SQL (bottom right), SUB DIAL (top left), SUB AF/RF/SQL (bottom
  left); red-labelled power/LOCK key; small blue LED.
- Top edge row of thin keys: S-DX, PMG (PW), MAG (BAND), N/W (MODE), SPLIT, V/M (MW), M-V (MT).
- The red maker name and model text on the top bezel are trademarks: **omit**, use "BRICO-FX" / BricoHams.

**Military** — inspiration image `images/8.png` (stock photo, inspiration only, not to be copied or
published):
- Grey-green / olive steel panels with screws, small engraved label plates.
- Two round analog meters with white dials and black needles top-left; another on a separate side unit.
- Large central round dial: cream/olive scale ring and a bar-shaped pointer handle across it.
- Black bakelite knobs (round, ribbed), toggle switches, small red and green indicator lamps, cable
  connectors along the bottom edge.

## Left to the builder

- Internal structure of each plugin, canvas vs SVG for knobs/needles.
- Which OpenWebRX+ globals to read for frequency, mode, step and signal level (the same public
  globals rig_skin reads, e.g. `smeter_level`), verified against OpenWebRX+ 1.2.130.
- Tests: a Node check per plugin (registers its theme, cleans up on switch, kit default selection),
  existing tests green, and a real-browser check on the live SDR (desktop and 375 px).
- Deploy script (backup, install, `init.js` update, rollback) following the `desplegar-*.sh` pattern.

## Change 2026-11-19

EA5KAO asked for **Rig** as the default style for everyone instead of Brico-FX. The kit default is now
`bricohams_config.skin_defecto` (`rig` if unset), applied once per browser and remembered in
`localStorage.bh_skin_default`; changing the configured default applies the new one once more. Brico-FX,
Military and Original stay selectable.
