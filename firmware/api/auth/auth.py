"""Auth API routes.

POST /api/auth/login        — verify password, set session cookie
GET  /api/auth/me           — return protection status and current auth state
POST /api/auth/logout       — revoke token, clear cookie
GET  /api/auth/config       — return whether auth is enabled
POST /api/auth/config       — enable/disable auth or change password
"""

import json
import lib.auth as auth
from api.app import app, Response


@app.route("/api/auth/login", methods=["POST"])
async def login(request):
    data = request.json
    if not data or not isinstance(data.get("password"), str):
        return {"ok": False, "error": "Bad request"}, 400

    # Rate limiting — lock after _MAX_ATTEMPTS consecutive failures
    if not auth.is_login_allowed():
        return {"ok": False, "error": "Too many attempts. Try again shortly."}

    if not auth.check_password(data["password"]):
        auth.record_login_failure()
        # Return 200 so the browser client can handle it gracefully.
        # 401 is reserved for missing/expired session tokens on other routes.
        return {"ok": False, "error": "Invalid password"}

    auth.record_login_success()
    token = auth.generate_token()
    resp = Response(
        json.dumps({"ok": True}),
        headers={"Content-Type": "application/json"},
    )
    resp.set_cookie("auth_token", token, path="/", http_only=True)
    # Microdot does not expose a samesite parameter — append it manually.
    resp.headers["Set-Cookie"][-1] += "; SameSite=Strict"
    return resp


@app.route("/api/auth/me")
async def me(request):
    if not auth.is_enabled():
        return {"ok": True, "data": {"protected": False}}
    token = request.cookies.get("auth_token", "")
    if auth.verify_token(token):
        return {"ok": True, "data": {"protected": True, "authed": True}}
    return {"ok": True, "data": {"protected": True, "authed": False}}


@app.route("/api/auth/logout", methods=["POST"])
async def logout(request):
    token = request.cookies.get("auth_token", "")
    auth.revoke_token(token)
    resp = Response(
        json.dumps({"ok": True}),
        headers={"Content-Type": "application/json"},
    )
    resp.delete_cookie("auth_token", path="/")
    return resp


@app.route("/api/auth/config")
async def get_auth_config(request):
    return {"ok": True, "data": {"enabled": auth.is_enabled()}}


@app.route("/api/auth/config", methods=["POST"])
async def post_auth_config(request):
    data = request.json
    if not isinstance(data, dict):
        return {"ok": False, "error": "Bad request"}, 400

    enabled = bool(data.get("enabled", False))
    if enabled:
        pw = data.get("password", "")
        if not pw or not isinstance(pw, str):
            return {"ok": False, "error": "Password is required"}, 400
        auth.set_password(pw)
    else:
        auth.set_password("")

    # Revoke all sessions — user must re-authenticate (or log in fresh)
    auth.revoke_token()
    resp = Response(
        json.dumps({"ok": True}),
        headers={"Content-Type": "application/json"},
    )
    resp.delete_cookie("auth_token", path="/")
    return resp
