from api.app import app, state
from lib.epaper.refresh import epaper_refresh
from lib.log import log


@app.route("/api/epaper/refresh", methods=["POST"])
async def api_epaper_refresh(request):
    log("API: /api/epaper/refresh")
    result = epaper_refresh(state["backend"])
    status = 200 if result.get("ok") else 500
    return result, status
