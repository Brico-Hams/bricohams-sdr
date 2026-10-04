---
layout: page
title: "OpenWebRX+ Receiver Plugin: Utils (utility)"
permalink: /receiver/utils
---

This `utility` plugin will give a function wrapping method and will send some events.  
This plugin is a dependency for almost all plugins.

## Features

- Function interception via `wrap_func()`
- Initialization hook via `on_ready()`
- DOM mutation helper via `observe_mutations()`
- Observer cleanup helper via `disconnect_observers()`

## Load

Add this lines in your `init.js` file (await ensures it finishes before dependents):

```js
await Plugins.load('https://0xaf.github.io/openwebrxplus-plugins/receiver/utils/utils.js');
// load the rest of your plugins here
```

## init.js

Learn how to [load plugins](/openwebrxplus-plugins/#load-plugins).

## API

### `Plugins.utils.wrap_func(name, before_cb, after_cb, obj)`

Wrap a function and intercept calls before and/or after execution.

### `Plugins.utils.on_ready(callback)`

Run `callback` once OpenWebRX+ has completed initialization.

### `Plugins.utils.observe_mutations(targets, options, callback, run_now)`

Create one or more `MutationObserver` instances with a shared callback.

- `targets`: single node, array, `NodeList`, or `HTMLCollection`
- `options`: standard `MutationObserver.observe()` options
- `callback(mutationsList, observer, target)`: called on mutation batches
- `run_now`: if `true`, callback is called once immediately per valid target

Returns an array of handles: `{ observer, target, disconnect }`.

Example:

```js
var handles = Plugins.utils.observe_mutations(
  [tabEl, rootEl],
  { attributes: true, attributeFilter: ['class'] },
  function () {
    refreshVisibility();
  },
  true
);
```

### `Plugins.utils.disconnect_observers(handles)`

Disconnect handles returned by `observe_mutations()`.

- Accepts a single handle or an array of handles.
- Returns the number of disconnected observers.

```js
Plugins.utils.disconnect_observers(handles);
```

## Code

Code is in the [Github repo](https://github.com/0xAF/openwebrxplus-plugins/tree/main/receiver/utils).
