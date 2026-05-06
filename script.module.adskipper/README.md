# script.module.adskipper

> **v2.0.0** — MPEG-DASH ad-skipping library for Kodi addons.

Detects and skips advertisement periods in MPEG-DASH streams by parsing the MPD manifest, tracking playback position, and issuing a `seekTime()` call to jump past each ad slot. Designed around SOLID principles with full dependency injection, so every component can be replaced or tested in isolation — **no running Kodi instance required for unit tests**.

---

## Table of contents

1. [Module structure](#module-structure)
2. [Installation](#installation)
3. [Quick start](#quick-start)
4. [Configuration reference](#configuration-reference)
5. [Custom components](#custom-components)
6. [Full manual wiring](#full-manual-wiring)
7. [Running tests](#running-tests)
8. [SOLID design notes](#solid-design-notes)
9. [Changelog](#changelog)

---

## Module structure

```
script.module.adskipper/
├── addon.xml
└── lib/
    └── adskipper/
        ├── _compat.py   → xbmc/xbmcgui stubs (enables tests outside Kodi)
        ├── period.py    → Period              (immutable domain model)
        ├── fetcher.py   → HttpManifestFetcher (HTTP transport)
        ├── parser.py    → MpdParser           (XML → Period[])
        ├── loader.py    → ManifestLoader      (fetch + parse + in-memory cache)
        ├── detector.py  → DurationAdDetector, CompositeAdDetector
        ├── notifier.py  → KodiNotifier, SilentNotifier
        ├── seeker.py    → KodiSeeker
        ├── monitor.py   → PlaybackMonitor     (daemon-thread polling loop)
        ├── skipper.py   → AdSkipper           (orchestrator)
        └── __init__.py  → start_ad_skipper()  (one-liner factory)
```

### Data flow

```
stream URL
  └─▶ ManifestLoader
        ├─▶ HttpManifestFetcher.fetch()   # urllib GET → raw XML
        └─▶ MpdParser.parse()            # XML → list[Period]

PlaybackMonitor (daemon thread)
  └─▶ xbmc.Player().getTime()  every 200 ms
        └─▶ AdSkipper.on_position(pos)
              ├─▶ AdDetector.is_ad(period)   # duration heuristic
              ├─▶ Seeker.seek_to(period.end) # xbmc.Player().seekTime()
              └─▶ Notifier.notify(...)       # xbmcgui toast
```

---

## Installation

Copy `script.module.adskipper/` into your Kodi `addons/` directory and declare the dependency in your addon's `addon.xml`:

```xml
<import addon="script.module.adskipper" version="2.0.0"/>
```

---

## Quick start

### One-liner

```python
from adskipper import start_ad_skipper

skipper, thread = start_ad_skipper(
    stream_url,
    label="Pluto TV",
    extra_headers={
        "Origin":  "https://pluto.tv",
        "Referer": "https://pluto.tv/",
    },
)

# when playback ends:
skipper.stop()
thread.join(timeout=2)
xbmc.log(f"Skipped {skipper.skip_count} ad(s)")
```

`start_ad_skipper` returns **`(AdSkipper, threading.Thread)`**. The thread is a daemon — it will not prevent the Python process from exiting — but calling `skipper.stop()` before `thread.join()` is always the clean shutdown path.

---

## Configuration reference

| Parameter | Type | Default | Description |
|---|---|---|---|
| `stream_url` | `str` | — | MPEG-DASH `.mpd` manifest URL |
| `label` | `str` | `"AdSkipper"` | Name shown in skip notifications |
| `min_duration` | `float` | `15.0` | Minimum ad length in seconds (inclusive) |
| `max_duration` | `float` | `45.0` | Maximum ad length in seconds (inclusive) |
| `extra_headers` | `dict` | `None` | Additional HTTP headers for the manifest request |
| `notify` | `bool` | `True` | Set `False` to suppress all UI notifications |
| `notify_threshold` | `int` | `3` | Stop showing notifications after this many skips |
| `seek_offset` | `float` | `0.5` | Extra seconds added past the ad end before seeking |
| `timeout` | `int` | `10` | HTTP timeout in seconds for the manifest fetch |

---

## Custom components

Every component satisfies a structural protocol — no inheritance needed.

### Custom ad detector

```python
from adskipper.detector import CompositeAdDetector, DurationAdDetector
from adskipper.period   import Period

class IdPrefixAdDetector:
    """Flag any period whose id starts with 'ad-'."""
    def is_ad(self, period: Period) -> bool:
        return period.id.startswith("ad-")

# Combine strategies with AND or OR logic:
detector = CompositeAdDetector(
    [DurationAdDetector(15, 45), IdPrefixAdDetector()],
    require_all=False,   # OR: either condition is enough
)
```

### Custom notifier

```python
from adskipper.period import Period

class LogNotifier:
    """Write skip events to xbmc.log instead of showing a toast."""
    def notify(self, period: Period, skip_count: int) -> None:
        import xbmc
        xbmc.log(f"[MyAddon] skipped ad #{skip_count} ({period.duration:.0f}s)")
```

### Custom seeker (e.g. with retry)

```python
import xbmc

class RetrySeeker:
    def seek_to(self, position: float) -> None:
        for attempt in range(3):
            try:
                xbmc.Player().seekTime(position)
                return
            except Exception:
                pass
```

---

## Full manual wiring

```python
import threading

from adskipper.fetcher  import HttpManifestFetcher
from adskipper.parser   import MpdParser
from adskipper.loader   import ManifestLoader
from adskipper.detector import DurationAdDetector
from adskipper.notifier import SilentNotifier
from adskipper.seeker   import KodiSeeker
from adskipper.monitor  import PlaybackMonitor
from adskipper.skipper  import AdSkipper

loader = ManifestLoader(
    url     = stream_url,
    fetcher = HttpManifestFetcher(
        headers = {"Origin": "https://pluto.tv"},
        timeout = 15,
    ),
)

skipper = AdSkipper(
    periods   = loader.get_periods(),
    detector  = DurationAdDetector(min_duration=15, max_duration=45),
    seeker    = KodiSeeker(offset=0.5),
    notifier  = SilentNotifier(),
    lookahead = 2.0,   # seconds before period start that triggers the skip
)

monitor = PlaybackMonitor(on_position=skipper.on_position)
thread  = threading.Thread(target=monitor.start, daemon=True)
thread.start()

# clean shutdown:
monitor.stop()
thread.join(timeout=2)
```

## Changelog

### v2.0.0

- **Fix:** `PlaybackMonitor` now uses `threading.Event` instead of a bare `bool` flag — eliminates the race condition between the main thread and the polling daemon.
- **Fix:** `KodiSeeker` and `PlaybackMonitor` create a fresh `xbmc.Player()` on every seek / poll call instead of holding a stale instance from `__init__`.
- **Fix:** `MpdParser` now respects the `Period@start` attribute (DASH §4.3.2.2). Previously only sequential duration accumulation was used, which produced incorrect timecodes on SSAI-stitched streams (e.g. Pluto TV).
- **Fix:** `start_ad_skipper` monkey-patch now correctly calls the original `stop()` when one exists on the skipper before it is shadowed.
- **New:** `adskipper._compat` — minimal `xbmc`/`xbmcgui` stubs so the library can be imported and tested entirely outside Kodi.
- **New:** Full unit-test suite (100 tests, zero Kodi dependency).
- **Config:** `addon.xml` version aligned to `2.0.0`.
