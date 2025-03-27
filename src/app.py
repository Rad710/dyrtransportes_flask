from flask import send_from_directory

from app_config import app

from decorators.token_required import token_required

from api.auth import *
from api.route import *
from api.product import *
from api.driver import *
from api.shipment_payroll import *
from api.shipment import *
from api.user_profile import *
from api.driver_payroll import *
from api.shipment_expense import *
from api.dinatran import *
from api.statistics import *


@app.route("/api/hello-world")
def hello_world():
    return "Hello, World!"


@app.route("/api/protected/hello-world")
@token_required
def protected_hello_world():
    return "Protected Hello, World!"


# Serve static assets directly
@app.route("/assets/<path:path>")
def serve_assets(path: str):
    return send_from_directory("static/assets", path)


# Catch-all route to serve index.html for any non-API routes
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path: str):
    # If path starts with /api/, let Flask continue to the next route handler
    if path.startswith("api/"):
        return app.dispatch_request()

    # Otherwise serve the index.html file for client-side routing
    return send_from_directory("static", "index.html")


if __name__ == "__main__":
    # flask --app app/app.py run --host 0.0.0.0 --port 8081 --debug
    app.run(host="0.0.0.0", debug=False, port=8080)
