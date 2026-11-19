# Receiver skins (Brico-FX and Military) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Two independent, publishable OpenWebRX+ receiver skins (Brico-FX, FTX-1-inspired; Military,
vintage field radio) plus the kit wiring that makes Brico-FX the default on the BricoHams SDR.

**Architecture:** Each skin is a self-contained receiver plugin (`<name>/<name>.js` + `<name>.css`) that
adds an `<option>` to `#openwebrx-themes-listbox`, watches `body` for its class `theme-<id>` (set by
OpenWebRX+'s own `UI.setTheme`) with a `MutationObserver`, builds its front panel when the class appears
and removes all of it when it disappears. Pure helpers live on `Plugins.<name>._logic` so they can be
tested in Node; the DOM is verified in a real browser on the live SDR.

**Tech Stack:** plain ES2017 JavaScript + jQuery (already on the page), CSS, canvas 2D; Node `vm` tests
(pattern of `tests/test_plugins_api.cjs`); Python tests for kit files (pattern of `tests/test_audio_plugins.py`).

**Spec:** `docs/superpowers/specs/2026-11-19-receiver-skins-design.md`

## Global Constraints

- Plugin ids / theme ids / labels: `bh_skin_bricofx` → `bh-bricofx` → "Brico-FX"; `bh_skin_militar` → `bh-militar` → "Military" (ES "Militar").
- No Yaesu name, logo or photo anywhere (code, CSS, README, screenshots). The front label is "BRICO-FX".
- Original code only: nothing copied from `rig_skin` or other plugins. Each skin folder carries `LICENSE` (MIT, "EA5KAO / BricoHams") and `README.md`.
- Each skin depends only on OpenWebRX+ 1.2.124+ globals (`UI`, `LS`, `Plugins`, `$`, `smeter_level`, `tuneBySteps`), never on rig_skin or other BricoHams plugins.
- Labels in English and Spanish, chosen by `document.documentElement.lang` starting with `es`, fallback English.
- S-meter calibration from optional `window.<plugin>_config.smeter` = `{ offset_hf, offset_vhf, iaru_vhf }` (same meaning as `rig_skin_config.smeter`); without it, show the raw level.
- No waterfall theme registration, no change to `wf_theme`.
- No images > 50 KB, no new web fonts; text contrast WCAG 2.2 AA; every control keyboard-reachable with `aria-label`.
- Usable at 375 px width.
- Kit: everyone switched to `bh-bricofx` once, flag `localStorage.bh_bricofx_default = '1'`; afterwards the visitor's choice is kept. Remove `RIG_POR_DEFECTO` from `init.js`.

## Review Focus

1. Switching themes back and forth many times → no duplicated panels, timers or handlers (one panel, one interval at most).
2. `localStorage` unavailable (private mode / blocked) → skins and kit default still work, no exception (every LS access in try/catch).
3. `smeter_level` 0 or undefined (no audio yet / no signal) → meter at minimum, needle at rest, no `NaN`/`-Infinity` drawn.
4. Digital mode selected but its message panel absent or empty → digital view shows an empty list, not an error.
5. Two skins installed together, or a saved theme whose plugin is no longer loaded → only one skin panel visible; OpenWebRX+ falls back without errors.

---

### Task 1: Brico-FX core — theme registration, lifecycle, pure helpers

**Files:**
- Create: `files/htdocs/plugins/receiver/bh_skin_bricofx/bh_skin_bricofx.js`
- Create: `files/htdocs/plugins/receiver/bh_skin_bricofx/bh_skin_bricofx.css` (empty scaffold, `body.theme-bh-bricofx` scope)
- Test: `tests/test_skins.cjs`

**Interfaces:**
- Produces on `Plugins.bh_skin_bricofx`:
  - `init()` → registers option `bh-bricofx` / label in listbox (once), starts the body-class observer, builds the panel if the class is already present (saved theme).
  - `_build()` / `_destroy()` → create / remove `#bh-bricofx-panel`, start / stop the single refresh interval (`this._timer`), unbind namespaced events `.bhfx`.
  - `_logic.sUnits(level, freqHz, cfg) -> { s: 0..9, over: dB >= 0, dbm: number|null }`. `dbm = 10*log10(level) + offset` (offset `offset_vhf` if `freqHz >= 30e6` else `offset_hf`, default 0); S9 = −73 dBm HF, −93 dBm VHF when `iaru_vhf`, 6 dB per S-unit; `level <= 0` or not finite → `{ s: 0, over: 0, dbm: null }`.
  - `_logic.isDigital(mode: string) -> boolean` true for `ft8 ft4 wspr jt65 jt9 fst4 fst4w q65 msk144 js8 rtty packet ais pocsag bpsk31 bpsk63 sstv fax hfdl dsc` (case-insensitive).
  - `_logic.t(key) -> string` label lookup ES/EN.
- Consumes: OpenWebRX+ `UI.setTheme` (sets `theme-<id>` on body), `#openwebrx-themes-listbox`.

- [ ] **Step 1: Write the failing test** in `tests/test_skins.cjs` (vm + minimal fakes, like `test_plugins_api.cjs`):
  - after `init()`, the fake listbox received exactly one option with value `bh-bricofx`; calling `init()` again adds none.
  - `sUnits(0, 7e6, {})` → `{ s: 0, over: 0, dbm: null }`; `sUnits(NaN, 7e6, {})` same.
  - with `cfg = { offset_hf: 0 }` and level such that dbm = −73 at 7 MHz → `s === 9 && over === 0`; dbm −61 → `s === 9 && over === 12`; dbm −79 → `s === 8`.
  - with `cfg = { offset_vhf: 0, iaru_vhf: true }`, dbm −93 at 145 MHz → `s === 9`.
  - `isDigital('FT8') === true`, `isDigital('nfm') === false`, `isDigital('') === false`.
  - lifecycle: firing the observer callback with the class added twice builds once; removed → `_timer === null` and no panel.
- [ ] **Step 2: Run** `node tests/test_skins.cjs` → FAIL (file missing).
- [ ] **Step 3: Implement** the core and helpers in `bh_skin_bricofx.js` (set `Plugins.bh_skin_bricofx.no_css = true` and load the CSS itself with a `?v=<version>` link, version `'1.0.0'`).
- [ ] **Step 4: Run** `node tests/test_skins.cjs` → PASS; `node tests/test_plugins_api.cjs` → PASS.
- [ ] **Step 5: Commit** `feat(skins): Brico-FX core, theme registration and helpers`.

### Task 2: Brico-FX front panel and controls

**Files:**
- Modify: `files/htdocs/plugins/receiver/bh_skin_bricofx/bh_skin_bricofx.js`, `.css`
- Test: `tests/test_skins.cjs`

**Interfaces:**
- Consumes: Task 1 `_build/_destroy/_logic`.
- Produces: `_logic.knobSteps(deltaAngleDeg: number, detentDeg = 15) -> integer` (sign kept, truncates toward zero); `_logic.clamp(v, lo, hi)`.

Panel layout (from the spec's visual references; inserted before `#openwebrx-panel-receiver`'s content, which is hidden while the skin is active and restored on destroy):
- Body matte black, rounded. Top edge row of thin keys: `S-DX`, `MODE`, `BAND`, `SPLIT`, `V/M`, `M-V` — only `MODE` (cycles `.openwebrx-demodulator-button` modes) and `V/M` (QMB recall) act; the rest are inert labels with `aria-disabled="true"`.
- Screen: status strip (light blue/white) with "BRICO-FX" and the mode box (white outline); frequency in light-blue/cyan italic digits from `UI.getFrequency()`, refreshed by the interval (250 ms); meter with `S 1 3 5 7 9` white and `+20 +40 +60 dB` cyan scale and a red bar from `sUnits(smeter_level, freq, cfg)`; `VOL` row with a red line proportional to volume.
- Soft-key bar (white on dark blue) — content per view (Task 3).
- Right: VFO knob (knurled black ring, spun-metal centre, blue LED arcs both sides); drag (pointer events, rotation → `knobSteps` → `tuneBySteps(n)`), mouse wheel (±1 step per notch), keyboard (Arrow keys ±1 step when focused). Keys `QMB` (short press: recall stored freq; long press ≥ 600 ms: store current freq in LS `bh_bricofx_qmb`), `CLAR` (toggle fine tuning: while on, each knob step is passed as one tuneBySteps step but the step selector is temporarily set to the smallest option, restored when off), `DISP` (next view), `BACK` (main view).
- Knobs: `AF/SQL` (drag/wheel: volume 0–150 via `UI.setVolume` and `#openwebrx-panel-volume`; with Shift or after a click on its `SQL` label: squelch −150..0 by setting `.openwebrx-squelch-slider` value and dispatching `input` and `change`), `FUNC` (cycles NR on/off via `UI.toggleNR`, then filter width presets via the demodulator bandpass, documented in README).
- Lamps `BUSY` (green when `sUnits().dbm` above squelch) and blue LED.
- ≤767 px: knob column below the screen, keys wrap.

- [ ] **Step 1: Failing tests:** `knobSteps(44) === 2`, `knobSteps(-16) === -1`, `knobSteps(14) === 0`, `knobSteps(30, 10) === 3`; `clamp(200, 0, 150) === 150`.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** helpers, markup, CSS and bindings (all events namespaced `.bhfx`, removed in `_destroy`).
- [ ] **Step 4: Run** tests → PASS. Manual check in the browser pane against the live SDR is in Task 6.
- [ ] **Step 5: Commit** `feat(skins): Brico-FX front panel, knobs and keys`.

### Task 3: Brico-FX screen views — scope/waterfall and digital

**Files:**
- Modify: `bh_skin_bricofx.js`, `.css`; Test: `tests/test_skins.cjs`

**Interfaces:**
- Produces: `_logic.VIEWS = ['main', 'scope', 'digital']`; `_logic.nextView(cur) -> string` (cycles); `_logic.viewFor(mode, chosen) -> string` (returns `'digital'` when `isDigital(mode)` and the user has not chosen a view since the mode change, else `chosen`).

- `main`: frequency + meter large; soft keys `MODE · STEP · NR · FILTER · DISP`.
- `scope`: mini waterfall inside the screen: a `<canvas>` that, on each interval tick, `drawImage`s the visible OpenWebRX+ waterfall canvases under `#webrx-canvas-container` scaled to its size, plus the spectrum `#openwebrx-spectrum-canvas` above when present; clicking a point tunes there via `UI.setFrequency` computed from the canvas x and the visible range (use OpenWebRX+'s own scale data the way the main waterfall click does — implementer reads `openwebrx.js` for the conversion it uses). Soft keys `ZOOM− · ZOOM+ · CENTER · BACK` (zoom calls the existing zoom buttons).
- `digital`: mini waterfall (smaller) + the last 8 lines of the active decoder panel (`#openwebrx-panel-wsjt-message`, `-js8-`, `-packet-`, `-pocsag-`, `-skimmer-`, `-hfdl-`, `-dsc-`, `-sstv-`, `-fax-` — whichever is visible), read as text, newest first; empty list when none. Soft keys `ALL · SEARCH · CLEAR · LOG · BACK` (`SEARCH` filters lines by a typed callsign; `CLEAR` empties the view only; `LOG` opens the original panel).
- Mode change to a digital mode switches to `digital` automatically (per `viewFor`).

- [ ] **Step 1: Failing tests:** `nextView('main') === 'scope'`, `nextView('digital') === 'main'`; `viewFor('ft8', null) === 'digital'`; `viewFor('usb', 'scope') === 'scope'`; `viewFor('ft8', 'main') === 'main'` when the user picked after the change (pass `chosen` non-null).
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement.** **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat(skins): Brico-FX scope and digital views`.

### Task 4: Military skin

**Files:**
- Create: `files/htdocs/plugins/receiver/bh_skin_militar/bh_skin_militar.js`, `.css`
- Test: `tests/test_skins.cjs`

**Interfaces:**
- Same lifecycle shape as Task 1 (`init/_build/_destroy`, panel `#bh-militar-panel`, events `.bhmil`, single `_timer`), own copies of `sUnits`, `knobSteps`, `clamp`, `t` on `Plugins.bh_skin_militar._logic` (duplicated on purpose: each repo stands alone).
- Produces: `_logic.needleAngle(s, over) -> degrees` mapping S0 → −50°, S9 → +20°, S9+60 → +50°, linear in between, clamped.

Look (spec's references): olive/grey-green steel panel with screws and engraved plates; two round meters with white dials and black needles — left "SIGNAL" (needle from `needleAngle`, smoothed 0.2 per tick), right "AF" (volume 0–150 mapped −50°..+50°); large central round dial, cream/olive scale ring with the frequency engraved around, bar-shaped pointer handle that rotates as the tuning wheel (drag/wheel/keys → `tuneBySteps`); black ribbed bakelite knobs `VOLUME`, `SQUELCH`, `MODE` (cycles modes); toggle switches `NR` and `MUTE` (`UI.toggleNR`, `UI.toggleMute`); lamps green (signal above squelch) and red (muted). ≤767 px: meters above the dial, knobs in a row.

- [ ] **Step 1: Failing tests:** option `bh-militar` registered once; `needleAngle(0,0) === -50`, `needleAngle(9,0) === 20`, `needleAngle(9,60) === 50`, `needleAngle(9,200) === 50`; lifecycle build-once / destroy-clears as in Task 1; with both skins initialised, adding `theme-bh-militar` builds only `#bh-militar-panel`.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement.** **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat(skins): Military receiver skin`.

### Task 5: Kit wiring — load, calibrate, selector, one-time default

**Files:**
- Modify: `files/htdocs/plugins/receiver/init.js` (remove `RIG_POR_DEFECTO` block and constant; add `window.bh_skin_bricofx_config` and `window.bh_skin_militar_config` with the current `rig_skin_config.smeter` values; load `bh_skin_bricofx` and `bh_skin_militar` with the other receiver plugins, after rig_skin)
- Modify: `files/htdocs/plugins/receiver/bricohams/bricohams.js` (selector + default)
- Test: `tests/test_skins_kit.py` (new), `tests/test_plugins_api.cjs` (extend)

**Interfaces:**
- Consumes: theme ids from Tasks 1 and 4; OpenWebRX+ `UI.setTheme`, `#openwebrx-themes-listbox`.
- Produces in `bricohams.js`: a labelled `<select id="bricohams-skin" aria-label="Estilo del receptor">` inside the `bricohams` section with options mirroring the listbox (Brico-FX, Military, Rig, Original=`default`), synced both ways (`change` → `UI.setTheme`; listbox `change` → select value); `aplicarSkinPorDefecto()` runs once after plugins load: if `localStorage.bh_bricofx_default !== '1'` and option `bh-bricofx` exists → `UI.setTheme('bh-bricofx')` and set the flag; all LS access in try/catch.

- [ ] **Step 1: Failing tests:** Python: `init.js` contains `'bh_skin_bricofx'` and `'bh_skin_militar'` loads, `bh_skin_bricofx_config` with `offset_hf: 7, offset_vhf: -50, iaru_vhf: true`, and no `RIG_POR_DEFECTO`/`bh_rig_default`. Node: fake env where flag unset → `setTheme('bh-bricofx')` called once and flag set; flag set → not called; `localStorage` throwing → no exception and `setTheme` still called once; selector `change` to `rig` → `UI.setTheme('rig')`.
- [ ] **Step 2: Run** `python tests/test_skins_kit.py` and `node tests/test_plugins_api.cjs` → FAIL.
- [ ] **Step 3: Implement.** **Step 4: Run** both + `node tests/test_skins.cjs` → PASS (run the Python test on the Pi if Windows encoding/symlink issues appear, as with the other kit tests).
- [ ] **Step 5: Commit** `feat(skins): load skins, Brico-FX by default once, style selector`.

### Task 6: Package, deploy and verify live

**Files:**
- Create in each skin folder: `README.md` (what it is, install lines for `init.js`, config, controls, licence, "inspired by a modern HF/VHF/UHF transceiver" wording without brand), `LICENSE` (MIT, EA5KAO / BricoHams, 2026), `screenshot.png` (< 50 KB, taken from the live SDR, no brand marks).
- Create (scratchpad, not repo): `desplegar-skins.sh` (backup of `init.js`, `bricohams.js` and the two new folders to `/var/backups/bricohams/skins-<fecha>`, install with `install -m 644 -o root -g root`, rollback on error, ends with `SKINS-OK`).

- [ ] **Step 1:** Check satellite passes (`grabaciones.json`) — no OpenWebRX restart is needed; only static files change.
- [ ] **Step 2:** Deploy via the script in a terminal tab (user types sudo password).
- [ ] **Step 3:** Browser pane on `http://192.168.254.105/`, fresh profile state (clear `bh_bricofx_default`, `ui_theme`): Brico-FX appears; tune with knob/wheel/keys; volume and squelch change the real sliders; meter moves; DISP cycles views; select FT8 → digital view shows decodes and the mini waterfall; switch Brico-FX → Military → Rig → Original → Brico-FX five times: one panel, no console errors; reload keeps the last choice; repeat at 375 px.
- [ ] **Step 4:** Screenshots for the READMEs; commit `docs(skins): READMEs, licences and screenshots`.
- [ ] **Step 5:** Report to EA5KAO; publishing the two public repos waits for his explicit go-ahead.
