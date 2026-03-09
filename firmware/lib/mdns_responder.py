"""Minimal mDNS A-record responder for MicroPython.

Responds to mDNS queries for <hostname>.local with an A record
pointing at our IP address, making the device reachable via .local
on the local network without a DNS server.

Usage (run as an asyncio task alongside Microdot):
    import asyncio
    import lib.mdns_responder as mdns
    asyncio.get_event_loop().create_task(mdns.run("pico-epaper-admin", "192.168.1.x"))
"""

import asyncio
import socket
import struct
from lib.log import log

_MDNS_ADDR = "224.0.0.251"
_MDNS_PORT = 5353
_TTL = 3600  # 1 hour — Pico IP is stable so staleness isn't a concern

# Numeric fallback in case MicroPython doesn't expose the named constant
_IPPROTO_IP = getattr(socket, "IPPROTO_IP", 0)


def _inet_aton(ip_str):
    return bytes(int(x) for x in ip_str.split("."))


def _pack_name(name):
    """Encode a dotted name into DNS label wire format."""
    result = b""
    for part in name.split("."):
        b = part.encode()
        result += bytes([len(b)]) + b
    return result + b"\x00"


def _build_response(hostname, ip_str):
    """Build a minimal mDNS A-record response packet."""
    ip_bytes = _inet_aton(ip_str)
    name = _pack_name(hostname + ".local")
    # Header: ID=0, QR+AA, 0 questions, 1 answer RR
    header = struct.pack("!HHHHHH", 0, 0x8400, 0, 1, 0, 0)
    # A record: name | type A (1) | class IN + cache-flush (0x8001) | TTL | rdlen=4 | IP
    rr = name + struct.pack("!HHIH", 1, 0x8001, _TTL, 4) + ip_bytes
    return header + rr


async def _announce_loop(hostname, ip):
    """Send mDNS A-record announcements: 3-burst at startup, then once per hour.

    Used when port 5353 is already held by lwIP. macOS queries for a cache
    refresh at ~80% of TTL (48 min for a 1h TTL), so we re-announce every
    55 minutes to keep the record alive indefinitely on always-on devices.
    One ~60-byte UDP packet per hour is negligible on an always-on WiFi radio.
    """
    response = _build_response(hostname, ip)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # IP_MULTICAST_TTL=255 required for multicast link-local traffic
        sock.setsockopt(_IPPROTO_IP, getattr(socket, "IP_MULTICAST_TTL", 10), 255)
    except Exception:
        pass

    def _send():
        try:
            sock.sendto(response, (_MDNS_ADDR, _MDNS_PORT))
        except Exception as e:
            log(f"mDNS: announce failed: {e}")

    log(f"mDNS: announcing {hostname}.local (burst + hourly refresh, TTL={_TTL}s)")
    # 3-burst at startup so macOS caches the record within seconds of boot
    for delay in (0, 1, 2):
        await asyncio.sleep(delay)
        _send()

    # Refresh every 55 minutes — well within the 1-hour TTL
    while True:
        await asyncio.sleep(55 * 60)
        _send()


async def run(hostname, ip):
    """Async mDNS A-record responder — run as an asyncio task.

    lwIP on the Pico always holds port 5353, so we use unsolicited announcer
    mode exclusively. See _announce_loop for the burst + refresh strategy.
    """
    await _announce_loop(hostname, ip)
