"""Authentication helpers.

Provides simple token-based auth for the HTTP API.

If ``hash`` in config/auth.json is absent or empty, auth is disabled and
every request is allowed through.  When enabled, in-memory session tokens are
issued on login.  Tokens are intentionally lost on reboot — users log in again.

Password storage
~~~~~~~~~~~~~~~~
Passwords are never stored in plaintext.  ``set_password`` generates a random
16-byte salt, computes SHA-256(salt + password), and persists both as hex
strings in config/auth.json under the keys ``hash`` and ``salt``.

Login rate limiting
~~~~~~~~~~~~~~~~~~~
After *_MAX_ATTEMPTS* consecutive failures the login endpoint is locked for
*_LOCKOUT_SECS* seconds.  The counters are in-memory and reset on reboot.
"""

import hashlib
import os
import time
import ubinascii
from lib.config import load_config, save_config

_tokens = set()

# ── rate-limit state ──────────────────────────────────────────────────────────

_MAX_ATTEMPTS = 5
_LOCKOUT_SECS = 30
_login_attempts = 0
_login_locked_until = 0.0


# ── internal helpers ──────────────────────────────────────────────────────────


def _hash_password(pw, salt_hex):
    """Return SHA-256(salt_bytes + pw_bytes) as a hex string."""
    salt = ubinascii.unhexlify(salt_hex)
    return ubinascii.hexlify(hashlib.sha256(salt + pw.encode()).digest()).decode()


# ── public API ────────────────────────────────────────────────────────────────


def is_enabled():
    """Return True when a hashed password exists in config/auth.json."""
    try:
        return bool(load_config("auth").get("hash", ""))
    except Exception:
        return False


def check_password(pw):
    """Return True when *pw* matches the stored hash."""
    try:
        cfg = load_config("auth")
        stored_hash = cfg.get("hash", "")
        salt = cfg.get("salt", "")
        if not stored_hash or not salt:
            return False
        return _hash_password(pw, salt) == stored_hash
    except Exception:
        return False


def set_password(pw):
    """Hash *pw* and persist to config/auth.json.  Empty string disables auth."""
    if not pw:
        save_config({"hash": "", "salt": ""}, "auth")
        return
    salt_hex = ubinascii.hexlify(os.urandom(16)).decode()
    save_config({"hash": _hash_password(pw, salt_hex), "salt": salt_hex}, "auth")


def is_login_allowed():
    """Return True when the login endpoint is not currently locked out."""
    return time.time() >= _login_locked_until


def record_login_failure():
    """Increment the failure counter; lock for *_LOCKOUT_SECS* after *_MAX_ATTEMPTS*."""
    global _login_attempts, _login_locked_until
    _login_attempts += 1
    if _login_attempts >= _MAX_ATTEMPTS:
        _login_locked_until = time.time() + _LOCKOUT_SECS
        _login_attempts = 0


def record_login_success():
    """Reset the rate-limit counters after a successful login."""
    global _login_attempts, _login_locked_until
    _login_attempts = 0
    _login_locked_until = 0.0


def generate_token():
    """Mint a new random token, add it to the active set, and return it."""
    token = ubinascii.hexlify(os.urandom(16)).decode()
    _tokens.add(token)
    return token


def verify_token(t):
    """Return True when *t* is in the active token set."""
    return t in _tokens


def revoke_token(t=None):
    """Remove *t* from the active set.  If t is None, revoke all tokens."""
    global _tokens
    if t is None:
        _tokens = set()
    else:
        _tokens.discard(t)
