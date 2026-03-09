import gc
from lib.config import load_config
from lib.network_connect import network_setup
from lib.epaper.epd_backend import EPDBackend
from api import server
from lib.log import log

net_cfg = load_config("network")
epaper_cfg = load_config("epaper")

net = network_setup(net_cfg)

log(f"\n--- Device ready ---")
log(f"Mode       : {net['mode']}")
if net["mode"] == "sta":
    log(f"SSID       : {net['client_ssid']}")
    log(f"NTP Time   : {net['ntp_time']}")
else:
    log(f"AP SSID    : {net['ap_ssid']}")
    log(f"AP Pass    : {net['ap_pass']}")
log(f"IP Address : {net['ip']}")
log(f"--------------------\n")

driver_name = epaper_cfg.get("driver", "Pico-ePaper-7.5-B.mod")
hostname = net_cfg.get("hostname", "pico-epaper-admin") or "pico-epaper-admin"
del net_cfg
del epaper_cfg
gc.collect()

try:
    backend = EPDBackend(driver_name)
except Exception as e:
    log(f"ePaper error: {e}")
    backend = None
finally:
    gc.collect()

ip = net["ip"]
wlan = net["wlan"]
mode = net["mode"]
ap_ssid = net.get("ap_ssid") or ""
del net
gc.collect()

server.start(
    ip, backend=backend, wlan=wlan, hostname=hostname, mode=mode, ap_ssid=ap_ssid
)
