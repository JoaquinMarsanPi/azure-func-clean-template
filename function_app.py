# en function_app.py
import json, azure.functions as func
from db.repository.client import get_client
from app.core.config import settings

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.function_name(name="db_health")
@app.route(route="db/health", methods=["GET"])
def db_health(_: func.HttpRequest) -> func.HttpResponse:
    cli = get_client()
    if not cli.is_configured:
        return func.HttpResponse(json.dumps({"ok": False, "msg": "COSMOS no configurado"}), mimetype="application/json")
    try:
        # ping barato
        list(cli.db().list_containers())
        return func.HttpResponse(json.dumps({"ok": True, "db": settings.COSMOS_DB}), mimetype="application/json")
    except Exception as ex:
        return func.HttpResponse(json.dumps({"ok": False, "error": str(ex)}), status_code=500, mimetype="application/json")
