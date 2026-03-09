"""System context provider for MicroPython.

Provides runtime system values (time, IP, hostname, network SSIDs) for
template rendering.
"""

import utime

SYSTEM_CONTEXT_PROVIDER = {
    "name": "system",
    "title": "System",
    "fields": [
        {"name": "current_month_name", "title": "Month"},
        {"name": "current_day_of_week", "title": "Day"},
        {"name": "current_time", "title": "Time"},
        {"name": "hostname", "title": "Hostname"},
        {"name": "ip_address", "title": "IP Address"},
        {"name": "ssid", "title": "Active Network (SSID)"},
        {"name": "client_ssid", "title": "WiFi Client Network (SSID)"},
        {"name": "ap_ssid", "title": "Access Point Network (SSID)"},
    ],
}

_WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
_MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


def get_system_provider():
    """Return the system provider schema dict."""
    return SYSTEM_CONTEXT_PROVIDER


def resolve_system_provider(
    wlan=None, hostname=None, mode="ap", ap_ssid="", client_ssid=""
):
    """Resolve runtime values for the system provider.

    Args:
        wlan:        live WLAN object (STA_IF or AP_IF)
        hostname:    device hostname string
        mode:        "sta" | "ap" — current network mode
        ap_ssid:     configured AP SSID (used when mode=="ap")
        client_ssid: configured client SSID (used as fallback in STA mode)

    Returns a dict of field name -> resolved string value.
    """
    t = utime.localtime()
    ip = ""
    active_ssid = ""

    if wlan is not None:
        try:
            ip = wlan.ifconfig()[0]
        except Exception:
            pass
        if mode == "sta":
            try:
                active_ssid = wlan.config("ssid")
                client_ssid = active_ssid  # prefer live value
            except Exception:
                active_ssid = client_ssid
        else:
            active_ssid = ap_ssid
    else:
        active_ssid = ap_ssid if mode == "ap" else client_ssid

    return {
        "current_month_name": _MONTHS[t[1] - 1],
        "current_day_of_week": _WEEKDAYS[t[6]],
        "current_time": "{:02d}:{:02d}".format(t[3], t[4]),
        "hostname": hostname or "",
        "ip_address": ip,
        "ssid": active_ssid,
        "client_ssid": client_ssid,
        "ap_ssid": ap_ssid,
    }
