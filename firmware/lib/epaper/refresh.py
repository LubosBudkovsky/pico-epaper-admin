"""ePaper refresh service for Pico Admin.

Loads the active template, resolves context variables and renders to the display.
Supported providers: custom_text, system, and any configured external provider
(fetched via urequests from its endpoint URL).
"""

import gc
import json
from lib.config import load_config
from lib.epaper.renderer import Renderer
from lib.log import log

_TEMPLATES_DIR = "/templates/epaper"

# Simple mutex flag — MicroPython has no asyncio.Lock
_busy = False


def _inject_context(layout, context):
    """Replace {{KEY}} tokens throughout the layout dict with resolved context values."""
    if not context:
        return layout

    def _sub(s):
        if "{{" not in s:
            return s
        for key, val in context.items():
            token = "{{" + key + "}}"
            if token in s:
                s = s.replace(token, str(val))
        return s

    def _walk(obj):
        if isinstance(obj, dict):
            for k in obj:
                v = obj[k]
                if isinstance(v, str):
                    obj[k] = _sub(v)
                elif isinstance(v, (dict, list)):
                    _walk(v)
        elif isinstance(obj, list):
            for i in range(len(obj)):
                item = obj[i]
                if isinstance(item, str):
                    obj[i] = _sub(item)
                elif isinstance(item, (dict, list)):
                    _walk(item)

    _walk(layout)
    return layout


def _get_active_preset():
    """Return the active layout preset dict from epaper_presets.json.

    Reads the preset name from epaper.json (key: layout_preset), then finds
    the matching entry in epaper_presets.json.  Falls back to the first preset
    if not found.  Returns {} when no presets are configured.
    """
    preset_name = load_config("epaper", {}).get("layout_preset", "default")
    presets = load_config("epaper_presets", []) or []
    for p in presets:
        if isinstance(p, dict) and p.get("name") == preset_name:
            return p
    return presets[0] if presets else {}


def _load_template(name):
    """Load /templates/epaper/<name>.json. Returns dict or None."""
    path = _TEMPLATES_DIR + "/" + name + ".json"
    try:
        with open(path, "r") as f:
            return json.loads(f.read())
    except OSError:
        log(f"refresh: template file not found: {path}")
        return None
    except ValueError:
        log(f"refresh: template JSON invalid: {path}")
        return None


def _extract_by_path(data, path):
    """Extract a value from a nested dict/list using a dot-separated path.

    Array indices are expressed as '[N]' segments, e.g. 'weather.[0].icon'.
    Returns empty string when any step is missing.
    """
    if not path:
        return ""
    cur = data
    for part in path.split("."):
        if part.startswith("[") and part.endswith("]"):
            try:
                idx = int(part[1:-1])
                if isinstance(cur, (list, tuple)) and 0 <= idx < len(cur):
                    cur = cur[idx]
                    continue
            except ValueError:
                pass
            return ""
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
            continue
        return ""
    return cur


def _fetch_provider_json(url, retries=3, retry_delay_ms=3000):
    """Fetch JSON from an external URL. Returns dict or list on success, {} on failure.

    Retries up to `retries` times with `retry_delay_ms` milliseconds between
    attempts.  The inter-retry delay uses asyncio.sleep() so the event loop
    keeps running (CYW43 network driver needs to be polled — utime.sleep()
    would freeze it, causing the WiFi link to go stale on subsequent fetches).

    r.close() is called in a finally block so the socket and SSL context are
    always released — even when r.json() raises.  Without this, each failed
    HTTPS request leaks an mbedTLS context (~10-20 KB); after 2-3 leaks
    subsequent connections fail with [Errno 12] ENOMEM.
    """
    import urequests
    import asyncio

    for attempt in range(1, retries + 1):
        r = None
        try:
            r = urequests.get(url, timeout=10)
            data = r.json()
            return data
        except Exception as e:
            log(f"refresh: HTTP fetch failed (attempt {attempt}/{retries}, {url}): {e}")
            if attempt < retries:
                # Yield to the event loop so the CYW43 driver stays healthy
                try:
                    asyncio.get_event_loop().run_until_complete(
                        asyncio.sleep_ms(retry_delay_ms)
                    )
                except Exception:
                    pass
        finally:
            if r is not None:
                try:
                    r.close()
                except Exception:
                    pass
            gc.collect()  # free SSL context + response buffer immediately

    return {}


def _resolve_variables(variables, saved_context):
    """Resolve template variables to their final string values.

    Provider types:
        custom_text       — field IS the literal value
        system            — resolved from lib.system_context
        <configured name> — fetched from provider endpoint, path-extracted,
                            optionally transformed

    Returns a dict mapping variable name -> resolved string value.
    """
    parsed_context = {}
    _provider_cache = {}

    configured_providers = load_config("context_providers", []) or []
    _configured_by_name = {
        p.get("name"): p for p in configured_providers if isinstance(p, dict)
    }

    for var in variables:
        var_name = var.get("name") if isinstance(var, dict) else var
        value = ""

        ctx = saved_context.get(var_name)
        if isinstance(ctx, dict):
            provider_name = ctx.get("provider", "")
            field = ctx.get("field", "")

            if provider_name == "custom_text":
                value = str(field)

            elif provider_name == "system":
                if "system" not in _provider_cache:
                    from lib.system_context import resolve_system_provider
                    from api.app import state

                    net_cfg = load_config("network", {})
                    _provider_cache["system"] = resolve_system_provider(
                        wlan=state.get("wlan"),
                        hostname=state.get("hostname") or net_cfg.get("hostname", ""),
                        mode=state.get("network_mode", "ap"),
                        ap_ssid=state.get("ap_ssid", ""),
                        client_ssid=net_cfg.get("client_ssid", ""),
                    )
                value = str(_provider_cache["system"].get(field, ""))

            elif provider_name in _configured_by_name:
                prov = _configured_by_name[provider_name]
                endpoint = prov.get("endpoint")
                if endpoint:
                    if provider_name not in _provider_cache:
                        _provider_cache[provider_name] = _fetch_provider_json(endpoint)
                    resp = _provider_cache.get(provider_name)
                    if resp is None:
                        resp = {}

                    # Find field config to get path and optional transformer
                    field_cfg = None
                    for f in prov.get("fields", []):
                        if isinstance(f, dict) and f.get("name") == field:
                            field_cfg = f
                            break

                    path = field_cfg.get("path", "") if field_cfg else ""
                    if path:
                        value = _extract_by_path(resp, path)
                    elif isinstance(resp, dict):
                        value = resp.get(field, "")
                    else:
                        log(
                            f"refresh: no path for var '{var_name}' but response is not a dict"
                        )

                    # Apply transformer if configured
                    transformer_name = (
                        field_cfg.get("transformer") if field_cfg else None
                    )
                    if transformer_name:
                        from lib.transformers import get_transformer

                        t = get_transformer(transformer_name)
                        if t is not None:
                            try:
                                value = t.resolve(value)
                            except Exception as te:
                                log(
                                    f"refresh: transformer '{transformer_name}' failed: {te}"
                                )
                                value = ""
                        else:
                            log(f"refresh: unknown transformer '{transformer_name}'")
            else:
                log(
                    f"refresh: unknown provider '{provider_name}' for var '{var_name}', skipping"
                )

        parsed_context[var_name] = str(value) if value != "" else ""
    return parsed_context


def epaper_refresh(backend, template_name=None, context_override=None):
    """Core ePaper refresh flow.

    Args:
        backend:          EPDBackend instance (may be None if hardware init failed)
        template_name:    Override the template from config. When None the
                          template persisted in epaper.json is used.
        context_override: When provided, used as ``saved_context`` dict instead
                          of the ``context`` key from epaper config.  Follows the
                          same format: ``{VAR_NAME: {"provider": ..., "field": ...}}``.
                          Useful for system-driven renders (e.g. boot screen) where
                          no user context has been persisted yet.

    Returns:
        dict with 'ok' bool, plus 'message' or 'error' key.
    """
    global _busy

    def _err(msg):
        log(f"refresh error: {msg}")
        return {"ok": False, "error": msg}

    if backend is None:
        return _err("ePaper backend not initialized")

    if _busy:
        return _err("ePaper is busy")

    # Evict all cached font/icon modules before loading the new template.
    # Each font module holds 15-30 KB of glyph bitmaps; without eviction,
    # switching between templates with different font sets gradually exhausts
    # the heap.  After clearing, only fonts the current template actually
    # uses will be re-imported on demand.
    from lib.epaper.epd_backend import clear_font_cache, clear_icon_cache

    clear_font_cache()
    clear_icon_cache()
    gc.collect()  # free any previous refresh's allocations before we start
    _busy = True
    try:
        # Load the active layout preset (template + context)
        preset = _get_active_preset()
        if not preset:
            return _err("No active preset configured")

        # Load template — param overrides the preset value
        if not template_name:
            template_name = preset.get("template", "")
        if not template_name:
            return _err("No template configured in active preset")

        template = _load_template(template_name)
        if template is None:
            return _err(f"Template '{template_name}' not found")

        layout = template.get("layout", {})
        variables = layout.get("variables", [])
        del template  # free outer dict (name/title strings); layout ref kept alive
        gc.collect()

        if not layout:
            return _err(f"Template '{template_name}' has no layout")

        # Device config — padding and rotation come from epaper.json (global, not per-preset)
        epaper_cfg = load_config("epaper", {})
        device_config = {
            "padding_top": epaper_cfg.get("padding_top", 0),
            "padding_right": epaper_cfg.get("padding_right", 0),
            "padding_bottom": epaper_cfg.get("padding_bottom", 0),
            "padding_left": epaper_cfg.get("padding_left", 0),
            "rotation": epaper_cfg.get("rotation", 0),
            "invert_colors": epaper_cfg.get("invert_colors", False),
        }
        del epaper_cfg
        gc.collect()

        # Resolve context variables
        if context_override is not None:
            saved_context = context_override
        else:
            saved_context = preset.get("context", {}) or {}
        del preset

        parsed_context = _resolve_variables(variables, saved_context)
        del variables
        del saved_context

        gc.collect()

        # Inject resolved context values into layout (replaces {{KEY}} tokens)
        layout = _inject_context(layout, parsed_context)
        del parsed_context
        gc.collect()

        final = {
            "layout": layout,
            "device_config": device_config,
        }

        log(f"refresh: rendering template '{template_name}'")
        Renderer(backend).render(final)
        del final

        # Free font/icon modules immediately — they're not needed until the
        # next refresh
        clear_font_cache()
        clear_icon_cache()
        gc.collect()

        log("refresh: done")
        return {"ok": True, "message": f"Rendered template '{template_name}'"}

    except Exception as e:
        return _err(f"Render failed: {e}")

    finally:
        _busy = False
