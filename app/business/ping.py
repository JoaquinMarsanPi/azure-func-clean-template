import json
import azure.functions as func

def make_ping(req: func.HttpRequest) -> func.HttpResponse:
    name = req.params.get("name", "world")
    return func.HttpResponse(
        json.dumps({"ok": True, "message": "pong", "who": name}),
        mimetype="application/json",
        status_code=200
    )
