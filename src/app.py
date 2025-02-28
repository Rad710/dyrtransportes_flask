from app_config import app

from api.auth import *
from api.route import *
from api.product import *
from api.driver import *
from api.shipment_payroll import *
from api.shipment import *

from decorators.token_required import token_required


@app.route("/api/hello-world")
def hello_world():
    return "Hello, World!"


@app.route("/api/protected/hello-world")
@token_required
def protected_hello_world():
    return "Protected Hello, World!"


if __name__ == "__main__":
    # flask --app app/app.py run --host 0.0.0.0 --port 8081 --debug
    app.run(host="0.0.0.0", debug=False, port=8080)
