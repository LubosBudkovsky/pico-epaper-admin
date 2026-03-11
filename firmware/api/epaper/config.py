"""ePaper device config and templates API routes.

Routes:
    GET  /api/epaper/config     — return device config (rotation, padding, refresh_interval, invert_colors, layout_preset)
    POST /api/epaper/config     — save device config, triggers refresh + scheduler
    GET  /api/epaper/templates  — list available templates from /templates/epaper/
"""

import gc
import json
import os
import asyncio
from api.app import app, state
from lib.config import load_config, save_config
from lib.log import log

_TEMPLATES_DIR = "/templates/epaper"
_CONFIG_DEFAULTS = {
    "layout_preset": "default",
    "refresh_interval": 0,
    "rotation": 0,
    "invert_colors": False,
    "padding_top": 0,
    "padding_right": 0,
    "padding_bottom": 0,
    "padding_left": 0,
}
_CONFIG_INT_KEYS = (
    "refresh_interval",
    "rotation",
    "padding_top",
    "padding_right",
    "padding_bottom",
    "padding_left",
)


def _load_template(name):
    """Load a single template by name. Returns dict or None."""
    path = _TEMPLATES_DIR + "/" + name + ".json"
    try:
        with open(path, "r") as f:
            return json.loads(f.read())
    except (OSError, ValueError):
        return None


def _list_templates():
    """Return all valid template dicts from /templates/epaper/ (excluding _* files)."""
    templates = []
    try:
        entries = os.listdir(_TEMPLATES_DIR)
    except OSError:
        return templates
    for fname in entries:
        if not fname.startswith("_") and fname.endswith(".json"):
            name = fname[:-5]  # strip .json
            tpl = _load_template(name)
            if tpl is not None:
                templates.append(tpl)
    templates.sort(key=lambda t: t.get("name", ""))
    return templates


# ── GET /api/epaper/config ────────────────────────────────────────────────────


@app.route("/api/epaper/config", methods=["GET"])
async def get_epaper_config(request):
    """Return the device configuration."""
    log("API: GET /api/epaper/config")
    config = load_config("epaper", _CONFIG_DEFAULTS)
    return {"ok": True, "data": config}


# ── POST /api/epaper/config ───────────────────────────────────────────────────


@app.route("/api/epaper/config", methods=["POST"])
async def post_epaper_config(request):
    """Save device config (rotation, padding, refresh_interval, layout_preset).

    Triggers scheduler restart and screen refresh.
    """
    log("API: POST /api/epaper/config")
    try:
        body = request.json
        if not isinstance(body, dict):
            return {"ok": False, "error": "Invalid JSON body"}, 400
    except Exception:
        return {"ok": False, "error": "Failed to parse request body"}, 400

    existing = load_config("epaper", _CONFIG_DEFAULTS)

    # Update layout_preset if provided, verifying it exists
    if "layout_preset" in body:
        preset_name = str(body["layout_preset"])
        presets = load_config("epaper_presets", []) or []
        if not any(
            isinstance(p, dict) and p.get("name") == preset_name for p in presets
        ):
            return {
                "ok": False,
                "error": "Preset '{}' not found".format(preset_name),
            }, 404
        existing["layout_preset"] = preset_name

    # Update integer device config fields
    for key in _CONFIG_INT_KEYS:
        if key in body:
            try:
                existing[key] = int(body[key])
            except (ValueError, TypeError):
                pass

    # Update boolean fields
    if "invert_colors" in body:
        existing["invert_colors"] = bool(body["invert_colors"])

    save_config(existing, "epaper")
    log(
        "API: device config saved (layout_preset='{}')".format(
            existing.get("layout_preset")
        )
    )
    config = existing

    # Restart user refresh task with the new preset's interval
    from lib.epaper.scheduler import restart_user_refresh

    restart_user_refresh(state["backend"])

    # Refresh the screen in the background
    async def _bg_refresh():
        from lib.epaper.refresh import epaper_refresh

        epaper_refresh(state["backend"])

    asyncio.create_task(_bg_refresh())

    return {"ok": True, "data": config}


# ── GET /api/epaper/templates ─────────────────────────────────────────────────


@app.route("/api/epaper/templates", methods=["GET"])
async def get_epaper_templates(request):
    """Return all available ePaper templates."""
    log("API: GET /api/epaper/templates")
    gc.collect()  # compact heap before json.dumps(all templates) in Response()
    templates = _list_templates()
    return {"ok": True, "data": templates}
