"""Context transformer routes.

Routes:
    GET /api/context/transformers  — list available transformers (name + title)
"""

from api.app import app
from lib.transformers import list_transformers


@app.route("/api/context/transformers", methods=["GET"])
async def get_transformers(request):
    """Return available data transformers (name + title)."""
    data = [{"name": t.name, "title": t.title} for t in list_transformers()]
    return {"ok": True, "data": data}
