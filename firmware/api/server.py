"""HTTP server built on Microdot.

Serves static files from /www/ with gzip and cache headers.
API routes are registered by importing their modules below.
"""

import asyncio
import os
from api.app import app, state, Response
from lib.log import log
import lib.auth as auth
import lib.mdns_responder as mdns_responder
import lib.epaper.scheduler as scheduler

# Import route modules so their @app.route decorators execute
import api.auth.auth  # noqa: F401
import api.system.system  # noqa: F401
import api.system.network  # noqa: F401
import api.epaper.clear  # noqa: F401
import api.epaper.refresh  # noqa: F401
import api.epaper.config  # noqa: F401
import api.epaper.presets  # noqa: F401
import api.context.providers  # noqa: F401
import api.context.transformers  # noqa: F401

_WWW_ROOT = "/www"
_ASSETS_MAX_AGE = 31536000  # 1 year — safe because Vite hashes filenames

Response.send_file_buffer_size = 4096


# ── auth guard ────────────────────────────────────────────────────────────────


# Routes exempt from auth — everything else under /api/ requires a valid token
_AUTH_OPEN_PATHS = {"/api/auth/login", "/api/auth/me", "/api/auth/logout"}


@app.before_request
async def check_auth(request):
    """Reject unauthenticated API requests when a password is configured.

    Only /api/auth/login, /api/auth/me, and /api/auth/logout are exempt.
    All other /api/* paths require a valid session cookie.
    Static file paths are always passed through.
    """
    if not auth.is_enabled():
        return
    path = request.path
    if path in _AUTH_OPEN_PATHS:
        return
    if not path.startswith("/api/"):
        return
    token = request.cookies.get("auth_token", "")
    if not auth.verify_token(token):
        return {"ok": False, "error": "Unauthorized"}, 401


# ── helpers ───────────────────────────────────────────────────────────────────


def _find_file(path):
    """Return (serve_path, use_gz) — prefers the .gz variant if it exists."""
    gz = _WWW_ROOT + path + ".gz"
    raw = _WWW_ROOT + path
    try:
        os.stat(gz)
        return gz, True
    except OSError:
        return raw, False


def _static_response(path):
    """Build a Microdot Response for a static path. Returns None on 404."""
    serve_path, use_gz = _find_file(path)
    try:
        os.stat(serve_path)
    except OSError:
        return None

    is_asset = path.startswith("/assets/")
    max_age = _ASSETS_MAX_AGE if is_asset else None
    resp = Response.send_file(serve_path, max_age=max_age, compressed=use_gz)
    if not is_asset:
        resp.headers["Cache-Control"] = "no-cache"
    log(f"GET {path} 200{' (gz)' if use_gz else ''}")
    return resp


@app.route("/")
async def index(request):
    resp = _static_response("/index.html")
    if resp is None:
        return Response(
            "<h1>Not Found</h1>", status_code=404, headers={"Content-Type": "text/html"}
        )
    return resp


@app.route("/<path:path>")
async def static(request, path):
    if path.startswith("api/"):
        # Don't serve API paths as static files — return JSON 404 so the
        # real response isn't a confusing HTML "Not Found" page.
        log(f"API /{path} 404")
        return {"error": "Not Found"}, 404
    resp = _static_response("/" + path)
    if resp is None:
        log(f"GET /{path} 404")
        return Response(
            "<h1>Not Found</h1>", status_code=404, headers={"Content-Type": "text/html"}
        )
    return resp


# ---------------------------------------------------------------------------
# Boot sequence
# ---------------------------------------------------------------------------

# ── boot contexts ──────────────────────────────────────────────────────────────────────────────

_BOOT_CONTEXT = {
    "CLIENT_SSID": {"provider": "system", "field": "client_ssid"},
    "IP_ADDRESS": {"provider": "system", "field": "ip_address"},
    "HOSTNAME": {"provider": "system", "field": "hostname"},
}

_BOOT_AP_CONTEXT = {
    "AP_SSID": {"provider": "system", "field": "ap_ssid"},
    "IP_ADDRESS": {"provider": "system", "field": "ip_address"},
}


async def _boot_sequence(backend):
    """Clear → show boot screen for 10 s → render active template."""
    if backend is None:
        return
    from lib.epaper.refresh import epaper_refresh

    try:
        log("boot: clearing screen")
        backend.clear_screen()
        log("boot: rendering boot screen")
        if state.get("network_mode") == "ap":
            epaper_refresh(
                backend, template_name="_boot_ap", context_override=_BOOT_AP_CONTEXT
            )
        else:
            epaper_refresh(
                backend, template_name="_boot", context_override=_BOOT_CONTEXT
            )
        await asyncio.sleep(10)
        log("boot: rendering active template")
        epaper_refresh(backend)
    except Exception as e:
        log(f"boot: sequence failed: {e}")


def start(ip, port=80, backend=None, wlan=None, hostname=None, mode="ap", ap_ssid=""):
    """Start the HTTP server and mDNS responder."""
    state["backend"] = backend
    state["wlan"] = wlan
    state["network_mode"] = mode
    state["ap_ssid"] = ap_ssid or ""
    state["hostname"] = hostname or ""
    log(f"HTTP server listening on http://{ip}:{port}/")
    loop = asyncio.get_event_loop()
    if hostname and mode == "sta":
        loop.create_task(mdns_responder.run(hostname, ip))
    loop.create_task(_boot_sequence(backend))
    scheduler.start(backend)
    app.run(host="0.0.0.0", port=port)
