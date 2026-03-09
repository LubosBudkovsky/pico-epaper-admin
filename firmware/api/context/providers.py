"""Context provider routes.

Routes:
    GET    /api/context/providers              — list all providers (+ system)
    POST   /api/context/providers              — create or update a provider
    DELETE /api/context/providers/<name>       — delete a provider
"""

from api.app import app
from lib.config import load_config, save_config
from lib.system_context import get_system_provider
from lib.log import log
from lib.utils import normalize_name

# ── GET /api/context/providers ────────────────────────────────────────────────


@app.route("/api/context/providers", methods=["GET"])
async def get_providers(request):
    """Return all configured providers, with the system provider appended."""
    exclude_system = request.args.get("exclude_system", "false").lower() == "true"
    configured = load_config("context_providers", []) or []
    providers = [p for p in configured if isinstance(p, dict)]
    if not exclude_system:
        providers.append(get_system_provider())
    return {"ok": True, "data": providers}


# ── POST /api/context/providers ───────────────────────────────────────────────


@app.route("/api/context/providers", methods=["POST"])
async def post_provider(request):
    """Create or update a configured provider."""
    try:
        incoming = request.json
        if not isinstance(incoming, dict):
            return {"ok": False, "error": "Request body must be a JSON object"}, 400

        incoming_name = incoming.get("name")
        if not incoming_name:
            return {
                "ok": False,
                "error": "Provider object must include a 'name' field",
            }, 400
        if incoming_name == "system":
            return {"ok": False, "error": "Provider name 'system' is reserved"}, 400

        providers = load_config("context_providers", []) or []

        # Find existing provider index
        existing_idx = None
        for i, p in enumerate(providers):
            if isinstance(p, dict) and p.get("name") == incoming_name:
                existing_idx = i
                break
        is_existing = existing_idx is not None

        # Build merged provider data
        provider_data = dict(providers[existing_idx]) if is_existing else {}
        for k, v in incoming.items():
            if v is not None:
                provider_data[k] = v

        # Process fields — normalize names for new fields
        original_fields = (
            providers[existing_idx].get("fields", []) if is_existing else []
        )
        original_field_names = {
            f.get("name") for f in original_fields if isinstance(f, dict)
        }
        seen_field_names = set(original_field_names)
        new_fields = []

        for f in provider_data.get("fields", []):
            if not isinstance(f, dict):
                continue
            fname = f.get("name")
            ftitle = f.get("title", "")
            is_new_field = (not is_existing) or (fname not in original_field_names)

            if is_new_field:
                if not ftitle:
                    return {
                        "ok": False,
                        "error": "New field must include a 'title'",
                    }, 400
                gen = normalize_name(ftitle)
                if not gen:
                    return {
                        "ok": False,
                        "error": "Could not generate field name from title",
                    }, 400
                if gen in seen_field_names:
                    return {
                        "ok": False,
                        "error": "Field name '{}' already exists".format(gen),
                    }, 400
                f = dict(f)
                f["name"] = gen
                seen_field_names.add(gen)
            else:
                # Existing field: keep its name as-is
                if fname in seen_field_names and fname not in original_field_names:
                    return {
                        "ok": False,
                        "error": "Field name '{}' already exists".format(fname),
                    }, 400
                seen_field_names.add(fname)

            new_fields.append(f)

        provider_data["fields"] = new_fields

        if not is_existing:
            title = provider_data.get("title", "")
            if not title:
                return {
                    "ok": False,
                    "error": "New provider must include a 'title'",
                }, 400
            gen_name = normalize_name(title)
            if not gen_name:
                return {
                    "ok": False,
                    "error": "Could not generate provider name from title",
                }, 400
            if gen_name == "system":
                return {"ok": False, "error": "Provider name 'system' is reserved"}, 400
            if any(
                isinstance(p, dict) and p.get("name") == gen_name for p in providers
            ):
                return {
                    "ok": False,
                    "error": "Provider '{}' already exists".format(gen_name),
                }, 400
            provider_data["name"] = gen_name
            providers.append(provider_data)
            saved = provider_data
        else:
            provider_data["name"] = incoming_name
            providers[existing_idx] = provider_data
            saved = provider_data

        save_config(providers, "context_providers")
        log("context: saved provider '{}'".format(saved.get("name")))
        return {"ok": True, "data": saved}

    except Exception as e:
        log("context: post_provider error: {}".format(e))
        return {"ok": False, "error": "Failed to save provider: {}".format(e)}, 500


# ── DELETE /api/context/providers/<name> ──────────────────────────────────────


@app.route("/api/context/providers/<name>", methods=["DELETE"])
async def delete_provider(request, name):
    """Delete a configured provider by name."""
    if name == "system":
        return {"ok": False, "error": "Provider 'system' cannot be deleted"}, 400

    providers = load_config("context_providers", []) or []
    for i, pdata in enumerate(providers):
        if isinstance(pdata, dict) and pdata.get("name") == name:
            deleted = providers.pop(i)
            save_config(providers, "context_providers")
            log("context: deleted provider '{}'".format(name))
            return {"ok": True, "data": deleted}

    return {"ok": False, "error": "Provider not found"}, 404
