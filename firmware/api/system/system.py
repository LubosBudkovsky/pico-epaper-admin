from api.app import app
from lib.system_status import get_status


@app.route("/api/system/status", methods=["GET"])
async def api_system_status(request):
    from api.app import state

    return get_status(state["wlan"])
