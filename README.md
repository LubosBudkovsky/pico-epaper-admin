# pico-epaper-admin

Firmware and web admin interface for a **Raspberry Pi Pico 2 W** with ePaper display.

The device serves a React SPA from its own HTTP server. Through the UI you configure which template is displayed on the ePaper screen, wire template variables to data providers (built-in system values, custom text, or any external HTTP JSON endpoint) and set a refresh interval for automatic updates.

The device can operate in **WiFi client mode** (connects to an existing network) or **AP mode** (broadcasts its own access point). Both modes and all network credentials are configurable through the admin UI.

---

## Table of contents

1. [Installation](#installation)
2. [Hardware](#hardware)
3. [Repository layout](#repository-layout)
4. [Architecture overview](#architecture-overview)
5. [Firmware](#firmware)
   - [Boot sequence](#boot-sequence)
   - [HTTP server & API routes](#http-server--api-routes)
   - [ePaper rendering pipeline](#epaper-rendering-pipeline)
   - [Template system](#template-system)
   - [Layout presets](#layout-presets)
   - [Context providers & transformers](#context-providers--transformers)
   - [Scheduler](#scheduler)
   - [Authentication](#authentication)
   - [Config files](#config-files)
6. [Development workflow](#development-workflow)
   - [Add a new template](#add-a-new-template)
   - [Frontend](#frontend)
   - [First-time setup](#first-time-setup)
   - [Editing the frontend](#editing-the-frontend)
   - [Building and deploying the frontend](#building-and-deploying-the-frontend)
   - [Font generation](#font-generation)
   - [Icon generation](#icon-generation)
7. [Third-party licenses](#third-party-licenses)

---

## Installation

### 1. Flash MicroPython

Download the latest **MicroPython firmware for Pico 2 W** from https://micropython.org/download/RPI_PICO2_W/ and flash it following the instructions on that page (hold BOOTSEL while plugging in, copy the `.uf2` file to the drive that appears).

### 2. Clone the repository

```sh
git clone https://github.com/LubosBudkovsky/pico-epaper-admin.git
cd pico-epaper-admin
```

### 3. Network setup

The device defaults to **AP mode** — on first boot it creates its own WiFi access point so you can reach the admin UI without any prior configuration.

**Option A — configure via the admin UI (recommended)**

Skip this step. Power on the device, connect to the AP it broadcasts (see [First boot](#6-first-boot)), then go to **Network Settings** in the admin UI to enter your home WiFi credentials.

**Option B — configure by editing `network.json` directly**

Edit `firmware/config/network.json` before copying the firmware to the device:

```json
{
  "client_enabled": false,
  "client_ssid": "",
  "client_pass": "",
  "country": "",
  "ap_ssid": "pico-epaper-ap",
  "ap_pass": "",
  "ap_pass_is_default": false,
  "hostname": "pico-epaper-admin"
}
```

| Key | Description |
|-----|-------------|
| `client_enabled` | Set to `true` to connect to an existing WiFi network on boot |
| `client_ssid` | Your WiFi network name |
| `client_pass` | Your WiFi password |
| `country` | Two-letter ISO 3166-1 country code (`US`, `GB`, `DE`, `CZ` …). Sets the WiFi regulatory domain |
| `ap_ssid` | Name of the access point the device broadcasts when not in client mode |
| `ap_pass` | Access point password. Leave empty to have it **auto-generated** (see below) |
| `ap_pass_is_default` | Managed automatically — do not set manually |
| `hostname` | mDNS hostname — device reachable at `http://<hostname>.local` in client mode |

> **Auto-generated AP password:** If `ap_pass` is empty when the device first boots into AP mode, a random 8-character alphanumeric password is generated, saved back to `network.json` (with `ap_pass_is_default: true`), and **printed to the serial output**. Connect a serial monitor to read it. Once you set a custom password through the admin UI, the auto-generated one is replaced and never returned by the API again.

> **After changing the AP password:** If you update `ap_pass` without also changing `ap_ssid`, your device may reconnect using the cached (old) password and fail silently. To avoid this, **forget the AP network on your phone or laptop** before reconnecting after a password change.

### 4. ePaper driver

The `driver` value in `firmware/config/epaper.json` is the bare filename (no `.py`) of a driver file inside `firmware/vendor/`. The included `Pico-ePaper-7.5-B.mod.py` works for the Waveshare 7.5" ePaper B panel.

For a different panel, download the matching MicroPython driver from
https://github.com/waveshareteam/Pico_ePaper_Code/tree/main/python,
place it under `firmware/vendor/`, and set `driver` to its filename.

> **Memory note:** Many Waveshare drivers allocate two pixel buffers (black + red/yellow), each 48 KB. On the Pico this can cause heap exhaustion under load. If you run into `MemoryError` crashes, open the driver file and comment out the second buffer allocation (the one typically named `buffer_red`). See `firmware/vendor/Pico-ePaper-7.5-B.mod.py` for an example of this modification.

### 5. Copy firmware to the device

Three options, from most to least friction:

**Thonny** (easiest for first-time setup): open Thonny, go to *View → Files*, navigate to `firmware/` on the left panel, select all files and folders, right-click → *Upload to /*. No additional tools required.

**MicroPico** (best for ongoing development in VS Code): install the [MicroPico](https://marketplace.visualstudio.com/items?itemName=paulober.pico-w-go) extension. Open the `firmware/` folder (it contains `.micropico` as the sync root marker). Use *MicroPico: Upload project to Pico* from the command palette. Subsequent edits can be synced automatically on save.

> **MicroPico `.gz` sync issue:** MicroPico sometimes silently skips `.gz` files when uploading the project, leaving the old (or missing) compressed assets on the device. After syncing, verify the files are actually present in `firmware/www/assets/` on the Pico using the MicroPico file explorer or via the REPL:
> If the `.gz` files are absent, copy them manually using Thonny (*Upload to /*) or `mpremote`:
> ```sh
> mpremote fs cp firmware/www/assets/index-*.js.gz :www/assets/
> mpremote fs cp firmware/www/assets/index-*.css.gz :www/assets/
> ```

**mpremote** (command line):

```sh
python3 -m venv .venv && source .venv/bin/activate
pip install mpremote
mpremote fs cp -r firmware/. :
```

### 6. First boot

Disconnect and reconnect the USB cable (or power-cycle the device). Watch the serial output.

**AP mode (default):** The device broadcasts a WiFi access point. The SSID and IP are shown on the ePaper display and printed to serial. If no AP password was pre-configured, a random one is generated and printed to serial — note it down. Connect your phone or laptop to that AP, then open `http://192.168.4.1` in a browser.

**Client mode** (if you pre-configured `client_enabled: true` with valid credentials): The device connects to your WiFi, prints its IP address, and is reachable at `http://pico-epaper-admin.local`.

---

## Hardware

The driver is loaded dynamically at boot via the `driver` key in `config/epaper.json` (e.g. `Pico-ePaper-7.5-B.mod`). The value is the bare filename (no `.py` extension) of a driver file inside `vendor/`. Because driver filenames may contain hyphens and dots, the file is loaded via `exec()` rather than `import`, so any valid filename works. Swapping to a different panel only requires dropping in a new driver file and updating that one config value.

**Driver source:** Official Waveshare MicroPython drivers are available at
https://github.com/waveshareteam/Pico_ePaper_Code/tree/main/python

**Buffer modification:** The official `Pico-ePaper-7.5-B.py` driver allocates two 48 KB buffers at init — `buffer_black` and `buffer_red`. The Pico 2 W has ~264 KB of RAM and MicroPython leaves roughly 200 KB of heap free; with two driver buffers plus the firmware's own rendering buffer, heap exhaustion can occur during HTTP request handling. The included `Pico-ePaper-7.5-B.mod.py` is a copy of the official driver with `buffer_red` commented out (the red channel goes unused — all-white bytes are sent for it). This frees 48 KB permanently. If you use a different panel, check whether its driver allocates a second buffer and apply the same modification if needed.

---

## Repository layout

```
pico-epaper-admin/
├── app/                    # React frontend (Vite 7 + React 19 + Mantine 8)
├── assets/
│   ├── fonts/              # Source TTF files + font generation README
│   └── icons/              # Bootstrap Icons SVG source + icon generation README
├── firmware/               # MicroPython code (deploy this to the Pico)
│   ├── main.py             # Entry point
│   ├── api/                # Microdot HTTP server + route modules
│   ├── lib/                # Core libraries
│   │   └── epaper/         # Rendering pipeline
│   ├── assets/
│   │   ├── fonts/          # Generated font .py modules (font_to_py output)
│   │   └── icons/          # Generated icon .py modules (gen_icons.py output)
│   ├── config/             # Runtime JSON config (persisted on device)
│   ├── templates/epaper/   # Layout template JSON files
│   ├── vendor/             # Third-party MicroPython libs (Microdot, Writer, driver)
│   └── www/                # Built React app (output of build-app.sh, served by Microdot)
└── tools/
    ├── build-app.sh        # Build React app → firmware/www/
    ├── build-icons.sh      # Generate icon font modules from icons-config.json
    ├── icons-config.json   # Icon names per size
    └── lib/
        └── gen_icons.py    # Bootstrap Icons SVG → font_to_py icon modules
```

---

## Architecture overview

```
┌────────────────────────────────────────────────────────┐
│                   Pico 2 W (MicroPython)                │
│                                                         │
│  main.py                                                │
│    └─ network_setup(cfg)  ← config/network.json         │
│         STA mode: connects to client WiFi               │
│         AP mode:  broadcasts access point (default)     │
│    └─ EPDBackend(driver)  ← config/epaper.json          │
│    └─ server.start()                                    │
│         │                                               │
│         ├─ asyncio task: mdns_responder (STA only)      │
│         ├─ asyncio task: _boot_sequence                 │
│         ├─ scheduler.start()                            │
│         │     ├─ asyncio task: _user_refresh_loop       │
│         │     └─ asyncio task: _system_refresh_loop     │
│         └─ Microdot app.run()  (blocks, drives loop)    │
│               ├─ GET/POST /api/epaper/*                 │
│               ├─ GET/POST /api/context/*                │
│               ├─ GET/POST /api/system/*                 │
│               └─ GET /*  → serves firmware/www/ (SPA)  │
└────────────────────────────────────────────────────────┘
         ↑ HTTP (port 80)
         ↑ mDNS: pico-epaper-admin.local  (client/STA mode only)
┌────────────────────────────────────────────────────────┐
│           Browser → React SPA (from firmware/www/)      │
│           dev: npm run dev  (Vite proxy → device IP)    │
└────────────────────────────────────────────────────────┘
```

All concurrent work (mDNS, boot sequence, scheduler, HTTP serving) runs as **asyncio tasks** inside a single event loop driven by `app.run()`.

---

## Firmware

### Boot sequence

`main.py` → `server.start()` schedules `_boot_sequence(backend)` as an asyncio task before `app.run()`:

1. `backend.clear_screen()` — full white to remove any previous image
2. `epaper_refresh(backend, template_name="_boot", context_override=...)` — renders `templates/epaper/_boot.json` showing the device hostname and IP address (resolved from the built-in `system` provider)
3. `asyncio.sleep(10)` — boot screen stays visible for 10 seconds
4. `epaper_refresh(backend)` — renders the active preset from `config/epaper.json`

The boot screen template lives at `firmware/templates/epaper/_boot.json` and `firmware/templates/epaper/_boot_ap.json` respectively. Templates prefixed with `_` are system-managed.

---

### HTTP server & API routes

**Entry point:** `firmware/api/server.py` — imports route modules so their `@app.route` decorators register, then calls `app.run()`.

**Shared state** (`firmware/api/app.py`): `state["backend"]` (EPDBackend) and `state["wlan"]` (WLAN object) are stored at startup and accessed by route handlers as needed.

**Static file serving:** All files under `firmware/www/` are served with gzip support (Vite's compression plugin pre-gzips everything). Assets under `/assets/` get a 1-year `Cache-Control` (safe because Vite hashes filenames). All other paths get `no-cache`. Unknown paths fall through to `index.html` for SPA routing.

**API routes:**

| Method | Path | Module | Description |
|--------|------|--------|-------------|
| GET | `/api/epaper/config` | `api/epaper/config.py` | Get device-level ePaper config (rotation, padding, refresh interval, active preset name) |
| POST | `/api/epaper/config` | `api/epaper/config.py` | Save device config, restart scheduler, trigger background refresh |
| GET | `/api/epaper/templates` | `api/epaper/config.py` | List all templates from `templates/epaper/` excluding system ones (`_` prefix) |
| GET | `/api/epaper/presets` | `api/epaper/presets.py` | List all layout presets |
| POST | `/api/epaper/presets` | `api/epaper/presets.py` | Create or update a layout preset (identified by `name`) |
| DELETE | `/api/epaper/presets/<name>` | `api/epaper/presets.py` | Delete a layout preset |
| POST | `/api/epaper/refresh` | `api/epaper/refresh.py` | Trigger immediate refresh |
| POST | `/api/epaper/clear` | `api/epaper/clear.py` | Clear display to white |
| GET | `/api/context/providers` | `api/context/providers.py` | List all providers (includes built-in system provider) |
| POST | `/api/context/providers` | `api/context/providers.py` | Create/update provider |
| DELETE | `/api/context/providers/<name>` | `api/context/providers.py` | Delete provider |
| GET | `/api/context/transformers` | `api/context/transformers.py` | List available transformers |
| GET | `/api/system/status` | `api/system/system.py` | System info (IP, uptime, memory, etc.) |
| GET | `/api/system/wifiap` | `api/system/network.py` | Network config (client SSID, AP settings — passwords excluded except auto-generated AP pass) |
| PATCH | `/api/system/wifiap` | `api/system/network.py` | Update network config; reboots to apply changes (AP-only edits while in client mode save silently without reboot) |
| GET | `/api/auth/me` | `api/auth/auth.py` | Current auth state — `{protected, authed}` |
| POST | `/api/auth/login` | `api/auth/auth.py` | Verify password, set session cookie |
| POST | `/api/auth/logout` | `api/auth/auth.py` | Revoke session, clear cookie |
| GET | `/api/auth/config` | `api/auth/auth.py` | Return whether auth is enabled |
| POST | `/api/auth/config` | `api/auth/auth.py` | Enable/disable auth or change password (always revokes current session) |

---

### ePaper rendering pipeline

```
epaper_refresh(backend, template_name?, context_override?)
    └─ _load_template(name)            load JSON from templates/epaper/
    └─ _resolve_variables(vars, ctx)   fetch + transform context values
    └─ Renderer(backend).render(final)
         └─ inject_layout_context_data()  substitute {{VAR}} placeholders
         └─ for each element:
               parse_el() / pos_from_el()  resolve position (top/bottom/left/right)
               backend.draw_text()
               backend.draw_icon()
               backend.draw_line() / draw_rect()
         └─ backend.display_image()    rotate buffer → push to hardware
```

**Key modules:**

| File | Purpose |
|------|---------|
| `lib/epaper/epd_backend.py` | Drawing backend — wraps the EPD driver, manages framebuf, handles rotation, loads font/icon modules, exposes `draw_text`, `draw_icon`, `draw_line`, `draw_rect`, `display_image`, `clear_screen` |
| `lib/epaper/renderer.py` | Translates a layout dict into backend drawing calls |
| `lib/epaper/render_utils.py` | Element parsing, position math (`top`/`bottom` from canvas edge), `{{VAR}}` substitution |
| `lib/epaper/refresh.py` | Orchestrates load → resolve → render; thin `_busy` mutex prevents concurrent refreshes |
| `lib/epaper/scheduler.py` | asyncio tasks for periodic refresh (see [Scheduler](#scheduler)) |

**Memory:** `EPDBackend` manages a 48 KB draw buffer (`_draw_buf`) with tight lifecycle control to minimise heap pressure: it is allocated at the start of `init_canvas()` (beginning of a render cycle, after font caches are cleared) and freed immediately after `epd.sleep()` in `display_image()`. This means the buffer is **not** resident on the heap while the HTTP server is handling requests — only the driver's own `buffer_black` (48 KB) remains pinned between refreshes. The server and a display cycle never run concurrently (asyncio single-threaded), so this is safe.

**Fonts:** Custom fonts are loaded lazily by name from `assets/fonts/`. The `_FONT_MAP` in `epd_backend.py` maps logical names (`SANS_REGULAR`, `SANS_BOLD`, `SERIF_BOLD`, …) to `(module_prefix, size)`. Peter Hinch's [Writer](https://github.com/peterhinch/micropython-font-to-py) is used for rendering. If a font module is missing the built-in 8×8 framebuf font is used as fallback. Vertical alignment uses `font_mod.baseline()` for precise ink-box positioning.

**Icons:** Icons are stored as font modules (same format as text fonts, generated via `tools/lib/gen_icons.py`). An icon name like `"cloud-rain"` maps to the corresponding glyph in the icon font module.

---

### Template system

Templates live in `firmware/templates/epaper/` as JSON files.

```jsonc
{
  "name": "my_template",
  "title": "Human-readable title",
  "layout": {
    "elements": [
      // text element
      { "type": "text", "text": "{{VAR_NAME}}", "font": "SANS_BOLD", "size": 26,
        "left": 0, "bottom": 100 },
      // icon element
      { "type": "icon", "icon": "{{ICON_VAR}}", "size": 28, "left": 0, "bottom": 50 },
      // horizontal line
      { "type": "line", "left": 0, "right": 0, "bottom": 200 },
      // rectangle
      { "type": "rect", "left": 0, "top": 0, "right": 0, "bottom": 50, "fill": 0 }
    ],
    "variables": [
      { "name": "VAR_NAME", "title": "Variable label shown in admin UI" }
    ]
  }
}
```

**Positioning model:** All coordinates are relative to the canvas edge and expressed in pixels. Exactly one horizontal anchor (`left` or `right`) and one vertical anchor (`top` or `bottom`) must be specified per element. `bottom: 0` = bottom edge of canvas; `top: 0` = top edge.

**Element types:**

| Type | Supported keys | Notes |
|------|---------------|-------|
| `text` | `text`, `font`, `size`, `fill`, `wrap`, position | `font`: logical name (`SANS_REGULAR`, `SANS_BOLD`, `SERIF_BOLD`, etc.), default `SANS_REGULAR`; `size`: px, default 24; `fill`: `0` black / `1` white, default black; `wrap: true` enables word wrap |
| `icon` | `icon`, `size`, `fill`, position | `icon`: Bootstrap Icons name or `{{VAR}}`; `size`: px, default 24; `fill`: `0` black / `1` white, default black |
| `line` | `stroke_width`, `fill`, position | Horizontal rule drawn between the two resolved anchor points; `stroke_width` default 1 |
| `rect` | `width`, `height`, `stroke_width`, `fill`, `radius`, position | `fill: 0` = filled black, `fill: 1` = filled white, omit `fill` for outline only; `radius` for rounded corners (default 0) |

**Position keys** (all elements): `left`, `right`, `top`, `bottom` (pixels from that edge) — or `x`/`y` for absolute coords, `x1`/`y1`/`x2`/`y2` for box elements. Values can be integers or percentage strings (`"50%"`).

**Variables** declared in the template's `variables` array are shown in the admin UI for context binding. At render time `{{VAR_NAME}}` placeholders in `text` and `icon` fields are substituted with resolved values.

---

### Layout presets

A **layout preset** bundles a template name and its context variable bindings into a named, reusable unit. Multiple presets can be stored; exactly one is active at any time.

**Device config vs. layout preset — split rationale:** Hardware settings (rotation, padding, refresh interval) apply to the physical display regardless of what is shown. Each preset stores `name`, `title`, `template`, and `context`.

**Storage:**
- `config/epaper.json` — device-level settings + `layout_preset` key (name of the active preset)
- `config/epaper_presets.json` — list of preset objects

**Preset object schema:**

```jsonc
{
  "name": "my_preset",          // machine identifier, used as key
  "title": "My Preset",         // human-readable label shown in the UI
  "template": "weather_vertical", // template filename (no .json)
  "context": {
    "CURRENT_TEMP": { "provider": "weather", "field": "temp" },
    "CURRENT_ICON": { "provider": "weather", "field": "icon", "transformer": "owm_icon" }
  }
}
```

**Switching the active preset:** POST to `/api/epaper/config` with `{"layout_preset": "my_preset"}`. The scheduler and manual refresh both always read `layout_preset` from `epaper.json` first, then look up the matching preset in `epaper_presets.json` to resolve the template and context.

**`first_setup` preset:** A built-in preset (`name: "first_setup"`) is included in `config/epaper_presets.json` and points to the `firmware/templates/epaper/first_setup.json` template. It serves as a sensible default and a starting point for the initial device configuration.

---

### Context providers & transformers

The context system maps template variable names to data sources. Configuration is persisted in `config/context_providers.json`.

**Provider types:**

| Provider | How it works |
|----------|-------------|
| `system` | Built-in, always available. Resolved by `lib/system_context.py` at render time using `utime` and the live WLAN object. See field list below. |
| `custom_text` | The field value IS the literal string. No fetch. |
| user-defined | Any name. Configured with an HTTP endpoint URL. At refresh time `urequests.get(endpoint)` is called, the JSON response is path-extracted using a dot-separated path (e.g. `daily.[0].weather.[0].icon`). Result is cached per-refresh across variables sharing the same provider. |

**Built-in `system` provider fields:**

| Field | Value |
|-------|-------|
| `current_time` | Current time as `HH:MM` |
| `current_day_of_week` | Full weekday name (`Monday`, `Tuesday` …) |
| `current_month_name` | Full month name (`January`, `February` …) |
| `hostname` | Device hostname (from `config/network.json`) |
| `ip_address` | Current IP address (client IP in STA mode, AP gateway in AP mode) |
| `ssid` | **Active** network SSID — client network name in STA mode, AP name in AP mode |
| `client_ssid` | Configured client WiFi network name (empty when not in STA mode) |
| `ap_ssid` | Configured access point name (always set once the AP has been configured) |

**Transformers** (`lib/transformers.py`) are optional post-processing functions applied to an extracted value before substitution. Each has a machine `name` used in config and a `resolve(value)` method.

Built-in transformers include OWM icon codes → icon names (`01d` → `sun`, `10n` → `cloud-rain`, etc.), Unix timestamp → formatted time, Unix timestamp → weekday name, and similar weather-data helpers.

**Context binding in config** (`config/epaper.json` → `context` key):

```jsonc
{
  "context": {
    "CURRENT_TEMP": { "provider": "my_weather_api", "field": "temp" },
    "CURRENT_ICON": { "provider": "my_weather_api", "field": "icon",
                      "transformer": "owm_icon" },
    "HOSTNAME": { "provider": "system", "field": "hostname" }
  }
}
```

---

### Scheduler

`lib/epaper/scheduler.py` runs two independent asyncio tasks:

**`_user_refresh_loop`** — sleeps `refresh_interval` seconds (from `config/epaper.json`) then calls `epaper_refresh()`. When `refresh_interval` is 0 this task is not created. The task is cancelled and restarted (via `restart_user_refresh()`) every time the ePaper config is saved, so changes take effect immediately without a reboot.

**`_system_refresh_loop`** — performs a full `clear_screen()` + `epaper_refresh()` once per day to remove ePaper ghosting. The scheduling strategy depends on the network mode:
- **STA mode** (WiFi client, NTP available): fires at **03:00 local time** each day.
- **AP mode** (no NTP, clock may be wrong): falls back to a fixed **24-hour cycle** from boot time.

Both tasks are started by `scheduler.start(backend)` in `server.py` before `app.run()`.

---

### Authentication

Authentication is **disabled by default** — a fresh device with empty `hash`/`salt` fields in `config/auth.json` is fully open. Enable it through the **Security** page in the admin UI.

**Mechanism:** In-memory session tokens are issued on successful login. Each token is generated with `os.urandom(16)` (available on Pico W MicroPython), hex-encoded, and kept in a module-level `set` in `lib/auth.py`. Tokens are sent to the browser as an `HttpOnly; SameSite=Strict` cookie (`auth_token`). Because tokens live only in RAM they are lost on device reboot — users log in again after a power cycle.

**Password storage:** Passwords are never stored in plaintext. `set_password()` generates a random 16-byte salt via `os.urandom(16)`, computes `SHA-256(salt + password)`, and persists both as hex strings in `config/auth.json` under the keys `hash` and `salt`. `check_password()` re-derives the hash from the stored salt and compares — the plaintext is never written anywhere.

**Login rate limiting:** After 5 consecutive failed login attempts the login endpoint is locked for 30 seconds. The counters are in-memory and reset on reboot. A locked endpoint returns `{"ok": false, "error": "Too many attempts. Try again shortly."}` (HTTP 200, same as a wrong password, so the browser can display it as an inline form error).

**Route protection** (`api/server.py`): A `@app.before_request` hook inspects every incoming request before it reaches a route handler:
- If `auth.is_enabled()` returns `False` → all requests pass through.
- The paths `/api/auth/login`, `/api/auth/me`, and `/api/auth/logout` are always exempt (needed to reach the login page and check state).
- Non-API paths (static files) are exempt.
- All other `/api/*` paths require a valid `auth_token` cookie — returns `{"ok": false, "error": "Unauthorized"}, 401` otherwise.

> Note: `POST /api/auth/config` (enable/disable/change password) **is** protected. A logged-in session is required to change auth settings.

**Wrong-password response:** `/api/auth/login` returns **HTTP 200** with `{"ok": false, "error": "Invalid password"}` on a wrong password, not 401. This allows the browser client to display an inline form error. HTTP 401 is reserved exclusively for "missing or expired session token on a protected route".

**Enabling auth:**

Navigate to **Security** (button in the app header) → toggle on → enter and confirm a password → Save. The current session is revoked and you are redirected to the login page.

**Disabling auth:** Toggle the switch off in **Security** → Save. The session is revoked and you are redirected to `/` (which is now open to everyone).

**Changing the password:** With the switch already on, enter a new password in the Security form → Save. Behaves the same as enabling — session revoked, redirect to `/login`.

**Frontend auth flow:**

`AuthProvider` (`app/src/modules/AuthProvider.tsx`) polls `/api/auth/me` on mount and surfaces one of four states:

| State | Meaning |
|------|--------|
| `loading` | Waiting for `/api/auth/me` response |
| `open` | No password configured — all routes accessible |
| `authed` | Password configured, valid session cookie present |
| `guest` | Password configured, no valid session |

`RequireAuth` (`app/src/modules/RequireAuth.tsx`) wraps the entire Layout route tree. When the state is `guest` it redirects to `/login?next=<current-path>` so the user is returned to where they were after logging in. When `open` or `authed` it renders children immediately.

The **Sign out** button in the app header is only visible in `authed` state.

---

### Config files

All config is stored as JSON in `firmware/config/`. Write access is via `lib/config.py` (`load_config` / `save_config`).

**`config/network.json`** — network and connectivity settings, editable via the **Network Settings** page in the admin UI or directly before first flash. See [Network setup](#3-network-setup) for a description of each key.

**`config/epaper.json`** — device-level display settings and ePaper driver, managed by the admin UI:

```jsonc
{
  "driver": "Pico-ePaper-7.5-B.mod", // bare filename, no .py
  "rotation": 0,           // 0 | 90 | 180 | 270
  "refresh_interval": 0,   // seconds; 0 = disabled
  "padding_top": 0,
  "padding_right": 0,
  "padding_bottom": 0,
  "padding_left": 0,
  "layout_preset": "first_setup"  // name of the active layout preset
}
```

**`config/epaper_presets.json`** — list of layout presets (template + context bindings), managed by the admin UI. See [Layout presets](#layout-presets) for the object schema.

**`config/auth.json`** — authentication config:

```json
{ "hash": "", "salt": "" }
```

Empty strings (the default) mean authentication is disabled. Never edit this file manually to set a password — `hash` and `salt` are managed by `lib/auth.py` and must be set through the UI or `POST /api/auth/config`. See [Authentication](#authentication).

**`config/context_providers.json`** — list of user-defined provider objects:

```jsonc
[
  {
    "name": "my_weather_api",
    "title": "My Weather API",
    "endpoint": "http://example-weather-app/weather?apikey=12345",
    "fields": [
      { "name": "temp", "title": "Temperature", "path": "current.temp" },
      { "name": "icon", "title": "Icon", "path": "current.weather.[0].icon",
        "transformer": "owm_icon" }
    ]
  }
]
```

---

## Development workflow

### Add a new template

1. Create `firmware/templates/epaper/my_template.json` following the schema in [Template system](#template-system)
2. Declare all variable names in the `variables` array
3. Make sure every font size and icon name/size used in the template has been generated — see [Font generation](#font-generation) and [Icon generation](#icon-generation)
4. Sync to Pico
5. The template appears in the admin UI's template dropdown automatically

### Frontend

**Stack:** Vite 7 · React 19 · TypeScript · Mantine 8 · React Router 7

**App routes:**

| Path | Component | Purpose |
|------|-----------|---------|
| `/` | `Home.tsx` | Dashboard / status |
| `/epaper/settings` | `EpaperSettings.tsx` | Device config (rotation, padding, refresh interval) + layout preset management (template, context bindings) |
| `/epaper/context` | `ContextProviders.tsx` | Manage external data providers |
| `/network/settings` | `NetworkSettings.tsx` | WiFi client credentials, country code, AP name and password |
| `/auth/settings` | `AuthSettings.tsx` | Enable/disable password protection, change password |
| `/login` | `Login.tsx` | Login form — shown only when auth is enabled and session is absent |

**Types:** `app/src/types/epaper.ts` and `app/src/types/context.ts` define the TypeScript interfaces that mirror the firmware API payloads.

**Build output:** `npm run build` (via `tools/build-app.sh`) produces gzipped static files in `app/dist/`. The Vite compression plugin deletes the uncompressed originals so only `.gz` files land in `dist/`. Microdot's static handler detects `.gz` variants automatically and sets `Content-Encoding: gzip`.

---

#### First-time setup

```sh
# Frontend dependencies
cd app && npm install
```

---

#### Editing the frontend

The Vite dev server proxies `/api/*` requests to the live device, so you can iterate on the UI without rebuilding and redeploying on every change.

```sh
cd app
cp .env.example .env    # set VITE_DEVICE_IP to your Pico's IP
npm run dev             # http://localhost:5173 — /api/* proxied to device
```

---

#### Building and deploying the frontend

```sh
./tools/build-app.sh
# then sync firmware/ to Pico via MicroPico (or mpremote)
```

`build-app.sh` runs `npm run build`, wipes `firmware/www/`, and copies `app/dist/` into it.

---

### Font generation

Run from the project root. Requires `.venv` with `micropython-font-to-py`.

```sh
# Python venv for font/icon generation tools
python3 -m venv .venv && source .venv/bin/activate
pip install micropython-font-to-py
```

The `-l 176` flag extends the charset up to U+00B0 (`°`). Without it only ASCII 32–126 is included and `°` renders as `?`.

```console
.venv/bin/font_to_py -l 176 assets/fonts/Roboto-Regular.ttf 22 firmware/assets/fonts/roboto_regular_22.py
.venv/bin/font_to_py -l 176 assets/fonts/Roboto-Regular.ttf 24 firmware/assets/fonts/roboto_regular_24.py
.venv/bin/font_to_py -l 176 assets/fonts/Roboto-Regular.ttf 26 firmware/assets/fonts/roboto_regular_26.py
.venv/bin/font_to_py -l 176 assets/fonts/Roboto-Bold.ttf 22 firmware/assets/fonts/roboto_bold_22.py
.venv/bin/font_to_py -l 176 assets/fonts/Roboto-Bold.ttf 26 firmware/assets/fonts/roboto_bold_26.py
.venv/bin/font_to_py -l 176 assets/fonts/Roboto-Bold.ttf 38 firmware/assets/fonts/roboto_bold_38.py
.venv/bin/font_to_py -l 176 assets/fonts/Merriweather_48pt-ExtraBold.ttf 48 firmware/assets/fonts/merriweather_bold_48.py
```

Naming convention: `{font_base}_{size}.py` — must match `_FONT_MAP` in `epd_backend.py`.

> **Only generated sizes are usable in templates.** If you specify `"size": 32` in a template element but `roboto_regular_32.py` (or `roboto_bold_32.py`, etc.) does not exist in `firmware/assets/fonts/`, the backend falls back to the built-in 8×8 bitmap font. Generate every size you intend to use before deploying.

| Logical name | File prefix |
|---|---|
| `SANS_REGULAR` | `roboto_regular_{size}.py` ← default font |
| `SANS_BOLD` | `roboto_bold_{size}.py` |
| `SERIF_REGULAR` | `merriweather_regular_{size}.py` |
| `SERIF_BOLD` | `merriweather_bold_{size}.py` |

---

### Icon generation

Run from the project root. Requires `.venv` with `micropython-font-to-py`.

```sh
# Python venv for font/icon generation tools
python3 -m venv .venv && source .venv/bin/activate
pip install micropython-font-to-py
```

Edit `tools/icons-config.json` to manage which icons are included at each size:

```json
{
  "28": ["sun", "moon", "cloud-rain", "sunrise", "sunset"],
  "48": ["sun", "moon", "cloud-rain"],
  "96": ["quote"]
}
```

Then regenerate:

```console
./tools/build-icons.sh
```

> **Only generated icons and sizes are usable in templates.** Make sure every icon name and size combination you use in templates is listed in `tools/icons-config.json` and the modules have been regenerated.

This calls `tools/lib/gen_icons.py`, which writes the output directly into `firmware/assets/icons/` — a `bootstrap_icons_{size}.py` font module per size and a single `icons_map.py` containing the union of all icons across all sizes. No separate copy step is needed; the next full firmware sync to the Pico picks them up automatically.

Icons are sourced from **Bootstrap Icons** in `assets/icons/bootstrap-icons.ttf` / `bootstrap-icons-map.json`. Icon names in templates (`"icon": "cloud-rain"`) must match the Bootstrap Icons name.

---

## Third-party licenses

Full license texts and copyright notices for all bundled third-party components are in [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

| Component | Files | License |
|---|---|---|
| [microdot](https://github.com/miguelgrinberg/microdot) | `firmware/vendor/microdot.py` | MIT |
| [micropython-font-to-py](https://github.com/peterhinch/micropython-font-to-py) | `firmware/vendor/writer.py` | MIT |
| [Waveshare Pico ePaper driver](https://github.com/waveshareteam/Pico_ePaper_Code) | `firmware/vendor/Pico-ePaper-7.5-B.mod.py` | MIT |
| [Roboto](https://github.com/googlefonts/roboto-classic) | `assets/fonts/Roboto-*.ttf`, `firmware/assets/fonts/roboto_*.py` | SIL OFL 1.1 |
| [Merriweather](https://github.com/SorkinType/Merriweather) | `assets/fonts/Merriweather_*.ttf`, `firmware/assets/fonts/merriweather_*.py` | SIL OFL 1.1 |
| [Bootstrap Icons](https://github.com/twbs/icons) | `assets/icons/bootstrap-icons.*`, `firmware/assets/icons/bootstrap_icons_*.py` | MIT |
