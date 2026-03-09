from vendor.microdot import Microdot, Response

app = Microdot()

# Shared state populated by server.start()
state = {
    "backend": None,
    "wlan": None,
    "network_mode": "ap",  # "sta" | "ap"
    "ap_ssid": "",
    "hostname": "",
}
