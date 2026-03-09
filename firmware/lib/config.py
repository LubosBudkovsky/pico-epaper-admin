"""JSON config helpers for Pico Admin.

Configs live in /config/<name>.json.
Writes are atomic: data is written to /config/<name>.tmp then renamed.
"""

import json
import os

CONFIG_DIR = "/config"


def _cfg_path(name):
    return CONFIG_DIR + "/" + name + ".json"


def _tmp_path(name):
    return CONFIG_DIR + "/" + name + ".tmp"


def _ensure_dir():
    try:
        os.mkdir(CONFIG_DIR)
    except OSError:
        pass  # already exists


def load_config(name, defaults=None):
    """Load /config/<name>.json and merge with defaults.

    Args:
        name: config identifier (e.g., 'system' -> 'system.json')
        defaults: default values if file missing or keys absent
    """
    if defaults is None:
        defaults = {}

    path = _cfg_path(name)
    try:
        with open(path, "r") as f:
            data = json.loads(f.read())
    except OSError:
        return dict(defaults)
    except ValueError:
        print(f"Config file {path} is invalid, using defaults")
        return dict(defaults)

    if isinstance(defaults, dict) and isinstance(data, dict):
        merged = dict(defaults)
        merged.update(data)
        return merged

    return data


def save_config(cfg, name):
    """Overwrite /config/<name>.json with cfg (atomic write via temp file)."""
    _ensure_dir()
    tmp = _tmp_path(name)
    cfg_p = _cfg_path(name)

    with open(tmp, "w") as f:
        f.write(json.dumps(cfg))
    try:
        os.remove(cfg_p)
    except OSError:
        pass
    os.rename(tmp, cfg_p)


def patch_config(cfg, name):
    """Patch (merge) values into existing /config/<name>.json and save.

    Only provided keys are updated. Other keys remain untouched.

    Returns:
        The final merged configuration.
    """
    _ensure_dir()
    cfg_p = _cfg_path(name)

    try:
        with open(cfg_p, "r") as f:
            existing = json.loads(f.read())
    except OSError:
        existing = {}
    except ValueError:
        print(f"Config file {cfg_p} is invalid, recreating")
        existing = {}

    if isinstance(existing, dict) and isinstance(cfg, dict):
        merged = dict(existing)
        merged.update(cfg)
    else:
        merged = cfg

    tmp = _tmp_path(name)
    with open(tmp, "w") as f:
        f.write(json.dumps(merged))
    try:
        os.remove(cfg_p)
    except OSError:
        pass
    os.rename(tmp, cfg_p)

    return load_config(name, {})
