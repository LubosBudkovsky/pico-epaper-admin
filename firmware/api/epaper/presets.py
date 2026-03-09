"""ePaper preset routes.

Routes:
    GET    /api/epaper/presets          — list all presets
    POST   /api/epaper/presets          — create or update a preset
    DELETE /api/epaper/presets/<name>   — delete a preset (not 'default')
"""

from api.app import app
from lib.config import load_config, save_config
from lib.log import log
from lib.utils import normalize_name

_PRESET_DEFAULTS = {
    "template": "",
    "context": {},
}


def _sanitize_preset(body, existing=None):
    """Validate and coerce a submitted preset dict. Returns a cleaned dict."""
    out = dict(existing or _PRESET_DEFAULTS)

    if "template" in body:
        out["template"] = str(body["template"])

    if "context" in body and isinstance(body["context"], dict):
        ctx = {}
        for var_name, binding in body["context"].items():
            if (
                isinstance(binding, dict)
                and "provider" in binding
                and "field" in binding
            ):
                ctx[str(var_name)] = {
                    "provider": str(binding["provider"]),
                    "field": str(binding["field"]),
                }
        out["context"] = ctx

    return out


# ── GET /api/epaper/presets ───────────────────────────────────────────────────


@app.route("/api/epaper/presets", methods=["GET"])
async def get_presets(request):
    """Return all configured presets."""
    log("API: GET /api/epaper/presets")
    presets = load_config("epaper_presets", []) or []
    return {"ok": True, "data": presets}


# ── POST /api/epaper/presets ──────────────────────────────────────────────────


@app.route("/api/epaper/presets", methods=["POST"])
async def post_preset(request):
    """Create or update a preset."""
    log("API: POST /api/epaper/presets")
    try:
        body = request.json
        if not isinstance(body, dict):
            return {"ok": False, "error": "Request body must be a JSON object"}, 400
    except Exception:
        return {"ok": False, "error": "Failed to parse request body"}, 400

    incoming_name = body.get("name")
    presets = load_config("epaper_presets", []) or []

    # Find existing preset index by name
    existing_idx = None
    for i, p in enumerate(presets):
        if isinstance(p, dict) and p.get("name") == incoming_name:
            existing_idx = i
            break
    is_existing = existing_idx is not None

    if is_existing:
        existing = presets[existing_idx]
        preset_data = _sanitize_preset(body, existing)
        preset_data["name"] = incoming_name
        preset_data["title"] = str(body.get("title", existing.get("title", "")))
        presets[existing_idx] = preset_data
        saved = preset_data
    else:
        # New preset — generate name from title
        title = body.get("title", "")
        if not title:
            return {"ok": False, "error": "New preset must include a 'title'"}, 400
        gen_name = normalize_name(title)
        if not gen_name:
            return {
                "ok": False,
                "error": "Could not generate preset name from title",
            }, 400
        if any(isinstance(p, dict) and p.get("name") == gen_name for p in presets):
            return {
                "ok": False,
                "error": "Preset '{}' already exists".format(gen_name),
            }, 400
        preset_data = _sanitize_preset(body)
        preset_data["name"] = gen_name
        preset_data["title"] = str(title)
        presets.append(preset_data)
        saved = preset_data

    save_config(presets, "epaper_presets")
    log("epaper: saved preset '{}'".format(saved.get("name")))
    return {"ok": True, "data": saved}


# ── DELETE /api/epaper/presets/<name> ─────────────────────────────────────────


@app.route("/api/epaper/presets/<name>", methods=["DELETE"])
async def delete_preset(request, name):
    """Delete a preset by name. The 'default' preset cannot be deleted."""
    if name == "default":
        return {"ok": False, "error": "Preset 'default' cannot be deleted"}, 400

    presets = load_config("epaper_presets", []) or []
    for i, p in enumerate(presets):
        if isinstance(p, dict) and p.get("name") == name:
            deleted = presets.pop(i)
            save_config(presets, "epaper_presets")
            log("epaper: deleted preset '{}'".format(name))
            return {"ok": True, "data": deleted}

    return {"ok": False, "error": "Preset not found"}, 404
