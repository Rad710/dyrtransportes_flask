"""Shared test setup.

The application creates its engine and its session while it is imported, from
the DB_* environment variables, so those are set here before anything from the
app is imported. Tests always run against their own database, never against the
development one.
"""

import os
import uuid

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import pytest

from helpers import TEST_API_KEY
from helpers import http_date

TEST_DB_NAME = os.getenv("TEST_DB_NAME", "dyrtransportes_test")

# load_dotenv() does not override variables that already exist, so setting them
# here keeps a local .env from pointing the tests at the development database
os.environ.setdefault("DB_USERNAME", "root")
os.environ.setdefault("DB_PASSWORD", "root")
os.environ.setdefault("DB_HOST", "127.0.0.1")
os.environ.setdefault("DB_PORT", "3306")
os.environ["DB_NAME"] = TEST_DB_NAME
os.environ["API_KEY"] = TEST_API_KEY
os.environ["DEBUG"] = ""  # no SQL logging while testing


def _create_test_database() -> Optional[str]:
    """Create the test database. Returns the error when MySQL is unreachable."""
    try:
        import MySQLdb

        connection = MySQLdb.connect(
            host=os.environ["DB_HOST"],
            port=int(os.environ["DB_PORT"]),
            user=os.environ["DB_USERNAME"],
            passwd=os.environ["DB_PASSWORD"],
        )
        connection.cursor().execute(f"CREATE DATABASE IF NOT EXISTS `{TEST_DB_NAME}`")
        connection.close()
        return None
    except Exception as e:  # pylint: disable=broad-exception-caught
        return str(e)


DATABASE_ERROR = _create_test_database()


def pytest_collection_modifyitems(config, items):
    """Skip the tests that need MySQL when there is no server to run them on."""
    if DATABASE_ERROR is None:
        return

    skip_db = pytest.mark.skip(
        reason=(
            f"MySQL is not reachable ({DATABASE_ERROR}). Start it with: "
            "docker compose -f deploy/docker-compose.test.yml up -d"
        )
    )
    for item in items:
        if "db" in item.keywords:
            item.add_marker(skip_db)


@pytest.fixture(scope="session")
def flask_app():
    """The real application, with every blueprint registered."""
    import app as app_module  # imported late, it connects to the database

    app_module.app.config.update(TESTING=True)
    return app_module.app


@pytest.fixture
def database_session(flask_app):  # pylint: disable=unused-argument
    """The session of the app, rolled back so it sees the latest commits.

    MySQL runs in REPEATABLE READ, without this the test would keep the
    snapshot it had before the request under test committed.
    """
    from app_config import db_session

    db_session.rollback()
    return db_session


@pytest.fixture(autouse=True)
def clean_database(request):
    """Leave every test with empty tables, so tests do not see each other."""
    if "db" not in request.keywords or DATABASE_ERROR is not None:
        yield
        return

    request.getfixturevalue("flask_app")

    from sqlalchemy import text
    from app_config import db_session
    from models.base import Base

    engine = db_session.get_bind()

    # The app keeps its own session, an open transaction there would block the
    # TRUNCATE on a metadata lock, so it is returned to the pool first
    db_session.rollback()
    db_session.remove()

    with engine.begin() as connection:
        connection.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for table in Base.metadata.sorted_tables:
            connection.execute(text(f"TRUNCATE TABLE `{table.name}`"))
        connection.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

    yield

    db_session.rollback()
    db_session.remove()


@pytest.fixture
def client(flask_app):
    return flask_app.test_client()


@pytest.fixture
def credentials() -> Dict[str, str]:
    return {
        "name": "Tester",
        "email": f"test-{uuid.uuid4().hex[:8]}@dyrtransportes.com",
        "password": "Test1234!",
    }


@pytest.fixture
def auth(client, credentials) -> Dict[str, str]:
    """Headers of a signed up and logged in user."""
    client.post("/api/auth/sign-up", data=credentials)
    response = client.post(
        "/api/auth/log-in",
        data={"email": credentials["email"], "password": credentials["password"]},
    )
    assert response.status_code == 200, response.get_json()

    return {
        "Authorization": f"Bearer {response.get_json()['token']}",
        "Accept-Language": "es-ES,es",
    }


class ApiFactory:
    """Creates records through the API, the way the frontend does."""

    def __init__(self, client, headers: Dict[str, str]):
        self.client = client
        self.headers = headers

    def post(self, path: str, payload: Any) -> Dict[str, Any]:
        response = self.client.post(path, json=payload, headers=self.headers)
        assert response.status_code in (200, 201), (path, response.get_json())
        return response.get_json()

    def driver(self, **overrides) -> int:
        payload = {
            "driver_id": "1234567",
            "driver_name": "JUAN",
            "driver_surname": "PEREZ",
            "truck_plate": "ABC123",
            "trailer_plate": "TRA123",
            **overrides,
        }
        return self.post("/api/driver", payload)["driver_code"]

    def route(self, **overrides) -> int:
        payload = {
            "origin": "PUERTO CAACUPEMI",
            "destination": "CAMPO NUEVE",
            "price": "120.75",
            "payroll_price": "55.50",
            **overrides,
        }
        return self.post("/api/route", payload)["route_code"]

    def product(self, **overrides) -> int:
        payload = {"product_name": "SOJA", **overrides}
        return self.post("/api/product", payload)["product_code"]

    def shipment_payroll(self, **overrides) -> int:
        payload = {"payroll_timestamp": http_date(31), **overrides}
        return self.post("/api/shipment-payroll", payload)["payroll_code"]

    def driver_payroll(self, driver_code: int, **overrides) -> int:
        payload = {
            "driver_code": driver_code,
            "payroll_timestamp": http_date(31),
            **overrides,
        }
        return self.post("/api/driver-payroll", payload)["payroll_code"]

    def shipment(
        self,
        driver_code: int,
        product_code: int,
        route_code: int,
        shipment_payroll_code: int,
        driver_payroll_code: int,
        **overrides,
    ) -> int:
        payload = {
            "shipment_date": http_date(1),
            "driver_code": driver_code,
            "driver_name": "JUAN PEREZ",
            "truck_plate": "ABC123",
            "trailer_plate": "TRA123",
            "product_code": product_code,
            "product_name": "SOJA",
            "route_code": route_code,
            "origin": "PUERTO CAACUPEMI",
            "destination": "CAMPO NUEVE",
            "dispatch_code": "REM-1000",
            "receipt_code": "REC-2000",
            "origin_weight": "30000",
            "destination_weight": "29950",
            "price": "120.75",
            "payroll_price": "55.50",
            "shipment_payroll_code": shipment_payroll_code,
            "driver_payroll_code": driver_payroll_code,
            **overrides,
        }
        return self.post("/api/shipment", payload)["shipment_code"]

    def shipment_expense(self, driver_payroll_code: int, **overrides) -> int:
        payload = {
            "expense_date": http_date(1),
            "reason": "GASOIL",
            "amount": "100000",
            "receipt": "B-1",
            "driver_payroll_code": driver_payroll_code,
            **overrides,
        }
        return self.post("/api/shipment-expense", payload)["expense_code"]


@pytest.fixture
def api(client, auth) -> ApiFactory:
    return ApiFactory(client, auth)


@pytest.fixture
def full_payroll(api) -> Dict[str, int]:
    """A payroll with one shipment and one expense, the base of the exports."""
    driver_code = api.driver()
    product_code = api.product()
    route_code = api.route()
    shipment_payroll_code = api.shipment_payroll()
    driver_payroll_code = api.driver_payroll(driver_code)
    shipment_code = api.shipment(
        driver_code,
        product_code,
        route_code,
        shipment_payroll_code,
        driver_payroll_code,
    )
    expense_code = api.shipment_expense(driver_payroll_code)

    return {
        "driver_code": driver_code,
        "product_code": product_code,
        "route_code": route_code,
        "shipment_payroll_code": shipment_payroll_code,
        "driver_payroll_code": driver_payroll_code,
        "shipment_code": shipment_code,
        "expense_code": expense_code,
    }


def codes(payload: List[Dict[str, Any]], key: str) -> List[int]:
    """Codes of a list response, to assert on what a listing returned."""
    return [item[key] for item in payload]
