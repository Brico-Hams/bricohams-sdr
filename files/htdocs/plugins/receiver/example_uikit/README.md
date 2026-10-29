---
layout: page
title: "OpenWebRX+ Receiver Plugin: UIKit Example (for devs)"
permalink: /receiver/example_uikit
---

This `receiver` plugin is an interactive demo for plugin developers.
It showcases every feature of the **uikit** plugin (v0.6+) with working,
copy-paste-ready code.

**There is no point in enabling this plugin for end users.**

## What it demonstrates

- **Panel tab** with buttons for each feature
- **Docked panel resizing** — drag the panel's inner edge or use the demo panel controls
- **Settings tab** added to the UIKit settings modal
- **Modals** — basic, close-left, no title bar, floating (no backdrop), resizable, custom border, lifecycle hooks
- **Dialogs** — `info()` and `question()` with Promise-based flow
- **Toasts** — all four types, with title, persistent (no timeout), dismiss all
- **Loading overlay** — on panel tab and on modal content

## Load

Add to your `init.js` after `uikit`:

```js
await Plugins.load('https://0xaf.github.io/openwebrxplus-plugins/receiver/uikit/uikit.js');
await Plugins.load('https://0xaf.github.io/openwebrxplus-plugins/receiver/example_uikit/example_uikit.js');
```

Note: `example_uikit` will auto-load uikit if it's not already loaded, so the first line is optional.

## Dependencies

- `uikit` >= 0.6

## Code

Code is in the [Github repo](https://github.com/0xAF/openwebrxplus-plugins/tree/main/receiver/example_uikit).
