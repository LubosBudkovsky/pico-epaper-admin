from api.app import app
from lib.log import log


@app.route("/api/epaper/clear", methods=["POST"])
async def api_epaper_clear(request):
    from api.app import state

    backend = state["backend"]

    if backend is None:
        return {"error": "E-paper backend not initialized"}, 500

    try:
        log("API: /api/epaper/clear")
        backend.clear_screen()
        return {"status": "ok"}
    except Exception as e:
        log(f"API: /api/epaper/clear error: {e}")
        return {"error": str(e)}, 500
