---
layout: page
title: "OpenWebRX+ Receiver Plugin: Accessible Bookmark Search"
permalink: /receiver/accessible_bookmark_search
---

This `receiver` plugin replaces the built-in "Search Bookmarks" dialog (right-click
on the bookmark button, or the `Y` keyboard shortcut) with a fully keyboard- and
screen-reader-accessible version. The plugin patches
the existing dialog and `BookmarkBar` object in place.

## Features

* Proper `<label>`s for the search field and the results list
* Results shown in a native `<select>` dropdown instead of a table of links, so
  keyboard and screen-reader navigation come for free
* Live filtering as you type — no need to press RETURN. But just in case: RETURN does refresh the list and places focus on the results.
* Leaving the search field empty shows **all** available bookmarks right away,
  including bandplan/dial-frequency entries
* TAB from the search field into the results list opens the dropdown
* Each entry is labeled with its source: `(Personal Bookmark)`,
  `(Systemwide Bookmark)` or `(Bandplan Frequency)`, since blind user often can't see the differently colored bookmarks on the bandplan.
* Selecting an entry (RETURN, click, or leaving the list) tunes the receiver to
  that bookmark
* ESC closes both the search dialog and the "Edit Bookmark" dialog
* To prevent accidental tuning, at the top of the list is an entry to leave the tuned frequency without any changes.

## Prerequisites

* This plugin depends on the [utils](https://0xaf.github.io/openwebrxplus-plugins/receiver/utils) plugin, v0.4 or later (loaded automatically if missing).
* Also, you need to run an OpenWebRX+ version that includes the search functionality, introduced in version 1.2.118.

## Installation

Add this line to your `init.js` file:

```js
Plugins.load('https://0xaf.github.io/openwebrxplus-plugins/receiver/accessible_bookmark_search/accessible_bookmark_search.js');
```

Reload the UI; right-clicking the bookmark button (or pressing `Y`) now opens the
accessible search dialog.

## init.js

Learn how to [load plugins](/openwebrxplus-plugins/#load-plugins).

## Known issues / compatibility

* Do **not** load this plugin together with the
  [search_bookmarks](https://0xaf.github.io/openwebrxplus-plugins/receiver/search_bookmarks)
  plugin — both patch the same `BookmarkBar` methods, so only whichever loads
  last actually takes effect. This plugin detects that case and logs a console
  warning, but does not block loading.
* `showPicker()` (used to auto-expand the dropdown on TAB/RETURN) is not
  supported in every browser/version; where unsupported, the list still gets
  focus and keyboard navigation works, it just doesn't visually pop open by
  itself until you press a key to open it manually.

## Code

[Github repo](https://github.com/0xAF/openwebrxplus-plugins/tree/main/receiver/accessible_bookmark_search)
