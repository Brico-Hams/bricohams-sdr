---
name: ui_status
description: Status bar footer in the uikit panel
tags: [uikit, status, progressbar]
---

# ui_status

Mirrors the OpenWebRX+ status progress bars (`#openwebrx-panel-status`) into a footer strip pinned at the bottom of the uikit panel. The footer is always visible regardless of which tab is active. The original status panel is hidden (but kept in the DOM so all OWRX+ update paths continue to write to it); observer handling is wired through `Plugins.utils.observe_mutations()` for real-time sync.

## Features

- Live-mirroring of all status bars: audio buffer, audio output, audio speed, network speed, server CPU, clients, battery
- Battery bar hidden by default (mirrors original visibility state)
- Responsive layout via CSS flex-wrap: 1×6 / 2×3 / 3×2 depending on panel width — no media queries needed
- Over-threshold highlight (red fill) mirrored from original `openwebrx-progressbar--over` class
- Settings checkbox to re-enable the original `#openwebrx-panel-status` panel
- Persists "enable original panel" preference via `LS` (localStorage)

## Dependencies

- `utils >= 0.8`
- `uikit >= 0.5`

## Usage

Add to your `init.js`:

```javascript
await Plugins.load('https://0xaf.github.io/openwebrxplus-plugins/receiver/ui_status/ui_status.js');
```

Or load locally:

```javascript
await Plugins.load('/plugins/receiver/ui_status/ui_status.js');
```

## Layout

The footer strip uses `display: flex; flex-wrap: wrap` with `flex: 1 1 100px; min-width: 70px; max-width: 200px` on each bar. This drives automatic responsive wrapping:

- `>= ~480 px`: 1 row x 6 bars
- `~240-480 px`: 2 rows x 3 bars
- `~140-240 px`: 3 rows x 2 bars

## Code

[Github repo](https://github.com/0xAF/openwebrxplus-plugins/tree/main/receiver/ui_status)
