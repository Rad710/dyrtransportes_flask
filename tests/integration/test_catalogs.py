"""CRUD, soft delete, audit trail and user scoping of drivers, routes and products.

The three modules follow the same pattern, so they are covered together.
"""

import pytest

pytestmark = pytest.mark.db


# --------------------------------------------------------------------- drivers


def test_create_and_read_a_driver(client, auth, api):
    driver_code = api.driver(driver_name="MARIA")

    response = client.get(f"/api/driver/{driver_code}", headers=auth)

    assert response.status_code == 200
    assert response.get_json()["driver_name"] == "MARIA"


def test_a_driver_needs_a_name(client, auth):
    response = client.post(
        "/api/driver",
        json={"driver_id": "1", "driver_name": "", "truck_plate": "ABC123"},
        headers=auth,
    )

    assert response.status_code >= 400


def test_list_drivers_returns_what_was_created(client, auth, api):
    api.driver(driver_name="UNO")
    api.driver(driver_name="DOS", driver_id="7654321")

    payload = client.get("/api/drivers", headers=auth).get_json()

    assert sorted(driver["driver_name"] for driver in payload) == ["DOS", "UNO"]


def test_update_a_driver(client, auth, api):
    driver_code = api.driver()

    response = client.put(
        f"/api/driver/{driver_code}",
        json={
            "driver_id": "1234567",
            "driver_name": "JUAN CARLOS",
            "driver_surname": "PEREZ",
            "truck_plate": "XYZ999",
            "trailer_plate": "TRA123",
        },
        headers=auth,
    )

    assert response.status_code == 200
    updated = client.get(f"/api/driver/{driver_code}", headers=auth).get_json()
    assert updated["driver_name"] == "JUAN CARLOS"
    assert updated["truck_plate"] == "XYZ999"


def test_updating_a_driver_writes_an_audit_row(client, auth, api, database_session):
    """Needs the audit triggers of src/migrations/not-applied to be installed."""
    from sqlalchemy import select
    from models.driver import DriverAudit
    from helpers import audit_triggers_installed

    if not audit_triggers_installed(database_session):
        pytest.skip("audit triggers not installed, the audit trail is not populated")

    driver_code = api.driver(driver_name="ANTES")
    client.put(
        f"/api/driver/{driver_code}",
        json={
            "driver_id": "1234567",
            "driver_name": "DESPUES",
            "driver_surname": "PEREZ",
            "truck_plate": "ABC123",
            "trailer_plate": "TRA123",
        },
        headers=auth,
    )

    audits = database_session.scalars(
        select(DriverAudit).where(DriverAudit.driver_code == driver_code)
    ).all()

    assert [audit.driver_name for audit in audits] == ["ANTES"]


def test_deleting_a_driver_is_a_soft_delete(client, auth, api, database_session):
    from sqlalchemy import select
    from models.driver import Driver

    driver_code = api.driver()
    response = client.delete(f"/api/driver/{driver_code}", headers=auth)

    assert response.status_code == 200
    row = database_session.scalar(
        select(Driver).where(Driver.driver_code == driver_code)
    )
    assert row is not None, "the record must stay in the table"
    assert row.deleted is True


def test_a_deleted_driver_stays_in_the_listing_flagged_as_deleted(client, auth, api):
    """Drivers are listed even when deleted, the UI offers to restore them.

    Routes and products behave the other way around, see the tests below.
    """
    driver_code = api.driver()
    client.delete(f"/api/driver/{driver_code}", headers=auth)

    payload = client.get("/api/drivers", headers=auth).get_json()

    listed = {driver["driver_code"]: driver for driver in payload}
    assert listed[driver_code]["deleted"] is True


def test_a_deleted_driver_can_be_restored(client, auth, api):
    driver_code = api.driver()
    client.delete(f"/api/driver/{driver_code}", headers=auth)

    response = client.patch(f"/api/driver/{driver_code}/restore", headers=auth)

    assert response.status_code == 200
    payload = client.get("/api/drivers", headers=auth).get_json()
    assert driver_code in [driver["driver_code"] for driver in payload]


def test_an_unknown_driver_is_not_found(client, auth):
    assert client.get("/api/driver/999999", headers=auth).status_code == 404


def test_a_user_never_sees_another_users_drivers(client, api, credentials):
    api.driver(driver_name="DEL PRIMER USUARIO")

    other = {**credentials, "email": "otro@dyrtransportes.com"}
    client.post("/api/auth/sign-up", data=other)
    token = client.post(
        "/api/auth/log-in",
        data={"email": other["email"], "password": other["password"]},
    ).get_json()["token"]

    payload = client.get(
        "/api/drivers", headers={"Authorization": f"Bearer {token}"}
    ).get_json()

    assert payload == []


# ---------------------------------------------------------------------- routes


def test_create_and_read_a_route(client, auth, api):
    route_code = api.route()

    response = client.get(f"/api/route/{route_code}", headers=auth)

    assert response.status_code == 200
    assert response.get_json()["origin"] == "PUERTO CAACUPEMI"


def test_a_route_keeps_the_price_as_a_decimal(client, auth, api):
    route_code = api.route(price="1234.56", payroll_price="99.99")

    payload = client.get(f"/api/route/{route_code}", headers=auth).get_json()

    assert str(payload["price"]) == "1234.56"
    assert str(payload["payroll_price"]) == "99.99"


def test_a_route_rejects_a_negative_price(client, auth):
    response = client.post(
        "/api/route",
        json={
            "origin": "A",
            "destination": "B",
            "price": "-1",
            "payroll_price": "1",
        },
        headers=auth,
    )

    assert response.status_code >= 400


def test_update_and_soft_delete_a_route(client, auth, api, database_session):
    from sqlalchemy import select
    from models.route import Route

    route_code = api.route()
    client.put(
        f"/api/route/{route_code}",
        json={
            "origin": "OTRO ORIGEN",
            "destination": "CAMPO NUEVE",
            "price": "130.00",
            "payroll_price": "60.00",
        },
        headers=auth,
    )
    updated = client.get(f"/api/route/{route_code}", headers=auth).get_json()
    assert updated["origin"] == "OTRO ORIGEN"

    client.delete(f"/api/route/{route_code}", headers=auth)
    row = database_session.scalar(select(Route).where(Route.route_code == route_code))
    assert row.deleted is True


def test_a_deleted_route_is_out_of_the_listing(client, auth, api):
    route_code = api.route()
    client.delete(f"/api/route/{route_code}", headers=auth)

    payload = client.get("/api/routes", headers=auth).get_json()

    assert route_code not in [route["route_code"] for route in payload]


# -------------------------------------------------------------------- products


def test_create_and_read_a_product(client, auth, api):
    product_code = api.product(product_name="MAIZ")

    response = client.get(f"/api/product/{product_code}", headers=auth)

    assert response.status_code == 200
    assert response.get_json()["product_name"] == "MAIZ"


def test_a_product_needs_a_name(client, auth):
    response = client.post("/api/product", json={"product_name": ""}, headers=auth)

    assert response.status_code >= 400


def test_update_and_soft_delete_a_product(client, auth, api, database_session):
    from sqlalchemy import select
    from models.product import Product

    product_code = api.product()
    client.put(
        f"/api/product/{product_code}",
        json={"product_name": "TRIGO"},
        headers=auth,
    )
    updated = client.get(f"/api/product/{product_code}", headers=auth).get_json()
    assert updated["product_name"] == "TRIGO"

    client.delete(f"/api/product/{product_code}", headers=auth)
    row = database_session.scalar(
        select(Product).where(Product.product_code == product_code)
    )
    assert row.deleted is True


def test_a_deleted_product_is_out_of_the_listing(client, auth, api):
    product_code = api.product()
    client.delete(f"/api/product/{product_code}", headers=auth)

    payload = client.get("/api/products", headers=auth).get_json()

    assert product_code not in [product["product_code"] for product in payload]


def test_products_of_another_user_are_invisible(client, api, credentials):
    api.product()

    other = {**credentials, "email": "otro-producto@dyrtransportes.com"}
    client.post("/api/auth/sign-up", data=other)
    token = client.post(
        "/api/auth/log-in",
        data={"email": other["email"], "password": other["password"]},
    ).get_json()["token"]

    payload = client.get(
        "/api/products", headers={"Authorization": f"Bearer {token}"}
    ).get_json()

    assert payload == []
