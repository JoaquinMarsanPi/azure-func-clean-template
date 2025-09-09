import azure.functions as func
from app.business.ping import make_ping

app = func.FunctionApp()

@app.route(route="ping", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def ping(req: func.HttpRequest) -> func.HttpResponse:
    return make_ping(req)
