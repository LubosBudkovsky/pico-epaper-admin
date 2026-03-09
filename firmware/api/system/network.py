"""Network config API routes.

Routes:
    GET   /api/system/wifiap  — return network config (client_pass and ap_pass excluded)
    PATCH /api/system/wifiap  — update network config; device reboots to apply changes
"""

import asyncio
import machine
from api.app import app
from lib.config import load_config, save_config
from lib.log import log

_DEFAULTS = {
    "client_enabled": False,
    "client_ssid": "",
    "client_pass": "",
    "country": "",
    "ap_ssid": "",
    "ap_pass": "",
    "ap_pass_is_default": False,
    "hostname": "pico-epaper-admin",
}

_ALLOWED_PATCH_KEYS = {
    "client_enabled",
    "client_ssid",
    "client_pass",
    "ap_ssid",
    "ap_pass",
    "country",
    "hostname",
}

# Keys that require a reboot to take effect.
# Changes to AP-only keys (ap_ssid, ap_pass) while client mode is active are
# saved silently — the AP is not running so no reconnect is needed.
_REBOOT_KEYS = {"client_enabled", "client_ssid", "client_pass", "hostname", "country"}
_AP_ONLY_KEYS = {"ap_ssid", "ap_pass"}


@app.route("/api/system/wifiap")
async def get_network_config(request):
    cfg = load_config("network", _DEFAULTS)
    ap_pass_is_default = bool(cfg.get("ap_pass_is_default", False))
    data = {
        "client_enabled": cfg.get("client_enabled", False),
        "client_ssid": cfg.get("client_ssid", ""),
        "country": cfg.get("country", ""),
        "ap_ssid": cfg.get("ap_ssid", ""),
        "ap_pass_is_default": ap_pass_is_default,
        "hostname": cfg.get("hostname", ""),
    }
    # Only expose the AP password when it was auto-generated — user must note it
    # down before they can change it. Once they set a custom password it is
    # never returned by the API.
    if ap_pass_is_default:
        data["ap_pass"] = cfg.get("ap_pass", "")
    return {"ok": True, "data": data}


@app.route("/api/system/wifiap", methods=["PATCH"])
async def patch_network_config(request):
    body = request.json
    if not isinstance(body, dict):
        return {"ok": False, "error": "Bad request"}, 400

    cfg = load_config("network", _DEFAULTS)

    currently_in_client = bool(cfg.get("client_enabled", False))
    patched_keys = {k for k in body if k in _ALLOWED_PATCH_KEYS}

    # Merge patch into a copy so we can validate the resulting state
    merged = dict(cfg)
    for key, val in body.items():
        if key in _ALLOWED_PATCH_KEYS:
            merged[key] = val

    # Reject if client mode would be enabled without valid credentials
    if merged.get("client_enabled"):
        if not merged.get("client_ssid") or not merged.get("client_pass"):
            return {
                "ok": False,
                "error": "client_ssid and client_pass are required when client mode is enabled",
            }, 400

    for key, val in body.items():
        if key not in _ALLOWED_PATCH_KEYS:
            continue
        # Empty ap_pass in the body means "keep existing" — but if there is no
        # existing password either, that would leave the AP open; reject it.
        if key == "ap_pass" and not val:
            if not cfg.get("ap_pass"):
                return {"ok": False, "error": "ap_pass is required"}, 400
            continue
        cfg[key] = val

    # If the caller explicitly set a new AP password it is no longer the default
    if body.get("ap_pass"):
        cfg["ap_pass_is_default"] = False

    save_config(cfg, "network")

    # Skip reboot when client mode is active and only the inactive AP config changed
    only_ap_changes = bool(patched_keys) and patched_keys.issubset(_AP_ONLY_KEYS)
    needs_reboot = not (currently_in_client and only_ap_changes)

    if needs_reboot:
        log("Network config updated — rebooting in 3 s")

        async def _reboot():
            await asyncio.sleep(3)
            machine.reset()

        asyncio.get_event_loop().create_task(_reboot())
    else:
        log("Network config updated (AP-only change while in client mode — no reboot)")

    return {"ok": True, "reboot": needs_reboot}
