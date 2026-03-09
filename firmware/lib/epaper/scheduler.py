"""Periodic ePaper refresh scheduler.

Two independent asyncio tasks run for the lifetime of the device:

user_refresh_task  — sleeps exactly `refresh_interval` seconds then refreshes.
                     Created/replaced via restart_user_refresh() whenever the
                     epaper config is saved, so changes take effect immediately.
                     When refresh_interval is 0 the task is not created at all.

system_refresh_loop — does a full clear + refresh to remove ghosting.
                      In STA mode (NTP available) it fires at SYSTEM_REFRESH_HOUR
                      (03:00 local time) each day.
                      In AP mode (no NTP, clock unreliable) it falls back to a
                      fixed 24-hour cycle from boot time.
"""

import asyncio
import utime
from lib.config import load_config
from lib.log import log

# Hour of day (0-23, local time) for the daily full clear+refresh.
_SYSTEM_REFRESH_HOUR = 3

# Reference to the current user refresh task so it can be cancelled on restart.
_user_task = None


async def _user_refresh_loop(backend, interval):
    """Sleep `interval` seconds, refresh, repeat."""
    log(f"scheduler: user refresh every {interval}s")
    try:
        while True:
            await asyncio.sleep(interval)
            try:
                from lib.epaper.refresh import epaper_refresh

                log("scheduler: user refresh")
                epaper_refresh(backend)
            except Exception as e:
                log(f"scheduler: user refresh error: {e}")
    except asyncio.CancelledError:
        log("scheduler: user refresh task stopped")


def restart_user_refresh(backend):
    """Cancel the existing user refresh task and start a new one.

    Reads refresh_interval from the current epaper config.  If interval is 0
    the old task is cancelled and no new task is created.

    Call this from the config POST handler whenever the config is saved.
    """
    global _user_task

    # Always cancel the current task first, regardless of the new interval.
    # This is the only place _user_task.cancel() is called — it covers both
    # "changing interval" and "setting interval back to 0".
    if _user_task is not None:
        _user_task.cancel()
        _user_task = None
        log("scheduler: user refresh task cancelled")

    cfg = load_config("epaper", {})
    interval = 0
    try:
        interval = int(cfg.get("refresh_interval", 0) or 0)
    except (ValueError, TypeError):
        interval = 0

    if interval > 0:
        # Start a new task with the updated interval.
        _user_task = asyncio.get_event_loop().create_task(
            _user_refresh_loop(backend, interval)
        )
    else:
        # interval=0: old task already cancelled above, nothing new to schedule.
        log("scheduler: user refresh disabled (interval=0)")


async def _system_refresh_loop(backend):
    """Full clear + refresh:
    - STA mode: daily at _SYSTEM_REFRESH_HOUR:00 local time (NTP available)
    - AP mode:  every 24 h from boot (clock may be wrong, no NTP)
    """
    from api.app import state

    while True:
        if state.get("network_mode") == "sta":
            # Schedule for the next 03:00 wall-clock time.
            now = utime.localtime()
            h, m, s = now[3], now[4], now[5]
            current_seconds = h * 3600 + m * 60 + s
            target_seconds = _SYSTEM_REFRESH_HOUR * 3600
            wait = target_seconds - current_seconds
            if wait <= 0:
                wait += 86400
            log(
                f"scheduler: system refresh in {wait}s (at {_SYSTEM_REFRESH_HOUR:02d}:00)"
            )
        else:
            # AP mode — NTP unavailable, use a fixed 24-hour cycle.
            wait = 86400
            log(f"scheduler: system refresh in {wait}s (AP mode — fixed 24 h cycle)")

        await asyncio.sleep(wait)

        try:
            log("scheduler: system refresh — clearing screen")
            backend.clear_screen()
            from lib.epaper.refresh import epaper_refresh

            log("scheduler: system refresh — refreshing")
            epaper_refresh(backend)
        except Exception as e:
            log(f"scheduler: system refresh error: {e}")


def start(backend):
    """Create scheduler tasks on the running event loop.

    Call this once inside server.start() before app.run().
    """
    if backend is None:
        log("scheduler: backend not available, skipping")
        return
    # Initial user refresh task based on current config
    restart_user_refresh(backend)
    # System daily refresh task (runs forever)
    asyncio.get_event_loop().create_task(_system_refresh_loop(backend))
    log("scheduler: tasks registered")
