"""Network setup — STA (client) with AP fallback.

network_setup(cfg) is the main entry point.  It attempts a client WiFi
connection when enabled and credentials are present; falls back to AP mode
otherwise.  If AP credentials are missing they are auto-generated and saved
back to network.json.
"""

import network
import os
import rp2
import utime
import ntptime
import ubinascii
from lib.log import log
from lib.blink import blink
from lib.config import save_config

_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def _get_ntptime(retries=3, retry_delay=2):
    """Sync system time via NTP. Retries on failure with a short delay.

    ntptime.settime() has a 1-second default socket timeout and is called
    immediately after DHCP completes, so the first attempt can fail if the
    DNS response is still in flight.  Retrying a couple of times is enough
    to cover that window.
    """
    for attempt in range(1, retries + 1):
        try:
            log(f"Syncing NTP time... (attempt {attempt}/{retries})")
            ntptime.settime()
            return utime.localtime()
        except Exception as e:
            log(f"NTP sync failed: {e}")
            if attempt < retries:
                utime.sleep(retry_delay)
    return None


def _gen_pass():
    """Generate a random 8-char alphanumeric password from os.urandom."""
    raw = os.urandom(16)
    return "".join(_CHARS[b % len(_CHARS)] for b in raw)[:8]


def _connect_sta(ssid, psk, country, hostname):
    """Attempt STA connection. Returns result dict on success, raises RuntimeError on failure."""
    if country:
        rp2.country(country)
    try:
        network.hostname(hostname)
        log(f"Hostname: {hostname}.local")
    except Exception as e:
        log(f"Warning: could not set hostname: {e}")

    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    utime.sleep(1)
    wlan.active(True)
    wlan.connect(ssid, psk)

    log("Connecting to WiFi...")
    max_wait = 15
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        log(f"  waiting... ({max_wait}s left)")
        utime.sleep(1)

    if wlan.status() != 3:
        wlan.active(False)
        blink(5, "fast")
        raise RuntimeError(f"WiFi connection failed (status {wlan.status()})")

    ip = wlan.ifconfig()[0]
    blink(3)
    log(f"WiFi connected — IP: {ip}")
    log(f"  reachable at: http://{hostname}.local")
    ntp_time = _get_ntptime()
    return {"wlan": wlan, "ip": ip, "ntp_time": ntp_time}


def _start_ap(ap_ssid, ap_pass, hostname):
    """Start AP mode. Returns result dict with wlan and ip."""
    try:
        network.hostname(hostname)
    except Exception:
        pass

    # Ensure STA is off before starting AP
    sta = network.WLAN(network.STA_IF)
    sta.active(False)
    utime.sleep_ms(500)

    ap = network.WLAN(network.AP_IF)
    ap.active(False)
    if ap_pass:
        # CYW43_AUTH_WPA2_AES_PSK raw bitmask — must be set before active(True)
        ap.config(ssid=ap_ssid, password=ap_pass, security=0x00400004)
    else:
        ap.config(ssid=ap_ssid, security=0)  # open network
    ap.active(True)
    utime.sleep(2)  # give the AP interface time to settle

    ip = ap.ifconfig()[0]
    blink(3)
    return {"wlan": ap, "ip": ip, "ntp_time": None}


def network_setup(cfg):
    """Set up networking from cfg dict. Returns result dict.

    Falls back to AP mode when:
      - client_enabled is False
      - client_ssid or client_pass is empty
      - STA connection attempt fails

    If AP SSID or password are missing they are auto-generated and saved back
    to network.json so they persist across reboots.

    Returns:
        {
            "wlan":     active WLAN object (STA_IF or AP_IF),
            "ip":       IP address string,
            "ntp_time": utime tuple or None,
            "mode":     "sta" | "ap",
            "ap_ssid":  AP SSID string (configured value; may be empty in STA mode),
        }
    """
    hostname = cfg.get("hostname", "") or "pico-epaper-admin"
    country = cfg.get("country", "")
    client_enabled = cfg.get("client_enabled", False)
    client_ssid = cfg.get("client_ssid", "")
    client_pass = cfg.get("client_pass", "")
    ap_ssid = cfg.get("ap_ssid", "")
    ap_pass = cfg.get("ap_pass", "")

    # ── Try STA mode ──────────────────────────────────────────────────────────
    if client_enabled and client_ssid and client_pass:
        try:
            result = _connect_sta(client_ssid, client_pass, country, hostname)
            result["mode"] = "sta"
            result["client_ssid"] = client_ssid
            return result
        except RuntimeError as e:
            log(f"Client WiFi failed: {e} — falling back to AP mode")

    # ── AP fallback ───────────────────────────────────────────────────────────
    cfg_dirty = False
    if not ap_ssid:
        ap_ssid = hostname + "-ap"
        cfg["ap_ssid"] = ap_ssid
        cfg_dirty = True
    if not ap_pass:
        ap_pass = _gen_pass()
        cfg["ap_pass"] = ap_pass
        cfg["ap_pass_is_default"] = True
        cfg_dirty = True
    if cfg_dirty:
        save_config(cfg, "network")

    result = _start_ap(ap_ssid, ap_pass, hostname)
    result["mode"] = "ap"
    result["ap_pass"] = ap_pass
    result["ap_ssid"] = ap_ssid
    return result
