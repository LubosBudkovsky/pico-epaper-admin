"""Gather Pico system status into a single dict."""

import gc
import os
import sys
import machine
import utime


_boot_ticks_ms = utime.ticks_ms()


def _uptime_str(ms):
    """Convert milliseconds elapsed into a human-readable relative string."""
    s = ms // 1000
    if s < 60:
        return f"{s}s"
    m = s // 60
    if m < 60:
        return f"{m}m {s % 60}s"
    h = m // 60
    if h < 24:
        return f"{h}h {m % 60}m"
    d = h // 24
    return f"{d}d {h % 24}h"


def _scale_bytes(n):
    """Return (value: int, unit: str) scaled to the most readable unit."""
    if n < 1024 * 1024:
        return n // 1024, "KB"
    return round(n / (1024 * 1024), 1), "MB"


def _mac_str(mac_bytes):
    """Format raw MAC bytes as XX:XX:XX:XX:XX:XX."""
    return ":".join("{:02X}".format(b) for b in mac_bytes)


def get_status(wlan=None):
    """Return a flat status dict. Pass the live wlan object for network details."""
    gc.collect()
    out = {}

    # ── uptime ────────────────────────────────────────────────────────────────
    elapsed_ms = utime.ticks_diff(utime.ticks_ms(), _boot_ticks_ms)
    out["uptime"] = _uptime_str(elapsed_ms)

    # ── memory ────────────────────────────────────────────────────────────────
    free_ram = gc.mem_free()
    alloc_ram = gc.mem_alloc()
    total_ram = free_ram + alloc_ram
    _, mem_unit = _scale_bytes(total_ram)
    out["memory_free"] = _scale_bytes(free_ram)[0]
    out["memory_used"] = _scale_bytes(alloc_ram)[0]
    out["memory_total"] = _scale_bytes(total_ram)[0]
    out["memory_unit"] = mem_unit
    out["memory_free_pct"] = round(free_ram * 100 / total_ram) if total_ram else 0

    # ── storage ───────────────────────────────────────────────────────────────
    try:
        st = os.statvfs("/")
        blk = st[0]
        total_b = st[2] * blk
        free_b = st[3] * blk
        used_b = total_b - free_b
        _, stor_unit = _scale_bytes(total_b)
        out["storage_free"] = _scale_bytes(free_b)[0]
        out["storage_used"] = _scale_bytes(used_b)[0]
        out["storage_total"] = _scale_bytes(total_b)[0]
        out["storage_unit"] = stor_unit
        out["storage_free_pct"] = round(free_b * 100 / total_b) if total_b else 0
    except Exception:
        pass

    # ── network ───────────────────────────────────────────────────────────────
    if wlan is not None:
        try:
            ip, subnet, gateway, dns = wlan.ifconfig()
            out["network_ip"] = ip
            out["network_subnet"] = subnet
            out["network_gateway"] = gateway
            out["network_dns"] = dns
        except Exception:
            pass
        try:
            out["network_ssid"] = wlan.config("ssid")
        except Exception:
            pass
        try:
            out["network_rssi"] = wlan.status("rssi")
        except Exception:
            pass
        try:
            out["network_mac"] = _mac_str(wlan.config("mac"))
        except Exception:
            pass

    # ── system ────────────────────────────────────────────────────────────────
    out["system_micropython"] = sys.version
    out["system_cpu_freq_mhz"] = machine.freq() // 1_000_000
    try:
        out["system_reset_cause"] = machine.reset_cause()
    except Exception:
        pass

    return out
