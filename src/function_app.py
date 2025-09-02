import azure.functions as func
from functions.ping import make_ping  # <- importa desde el submódulo "functions"

app = func.FunctionApp()

@app.route(route="ping", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def ping(req: func.HttpRequest) -> func.HttpResponse:
    return make_ping(req)
