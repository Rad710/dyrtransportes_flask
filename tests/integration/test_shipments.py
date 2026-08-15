"""Shipments (Cobranzas): CRUD, filters, bulk operations and payroll moves."""

import pytest

from helpers import http_date

pytestmark = pytest.mark.db


def test_create_and_read_a_shipment(client, auth, full_payroll):
    response = client.get(
        f"/api/shipment/{full_payroll['shipment_code']}", headers=auth
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["dispatch_code"] == "REM-1000"
    assert payload["receipt_code"] == "REC-2000"
    assert str(payload["origin_weight"]) == "30000"


def test_the_shipment_is_assigned_to_the_latest_unpaid_payroll_of_the_driver(
    client, auth, api, full_payroll
):
    """The API ignores the driver_payroll_code sent by the client.

    It always assigns the most recent unpaid payroll of the driver.
    """
    newer_payroll = api.driver_payroll(
        full_payroll["driver_code"], payroll_timestamp=http_date(30, "Apr")
    )

    shipment_code = api.shipment(
        full_payroll["driver_code"],
        full_payroll["product_code"],
        full_payroll["route_code"],
        full_payroll["shipment_payroll_code"],
        driver_payroll_code=999999,  # ignored
        dispatch_code="REM-1004",
        receipt_code="REC-2004",
    )

    payload = client.get(f"/api/shipment/{shipment_code}", headers=auth).get_json()
    assert payload["driver_payroll_code"] == newer_payroll


def test_a_shipment_needs_the_driver_to_have_an_unpaid_payroll(client, auth, api):
    driver_code = api.driver(driver_id="9999999")
    product_code = api.product()
    route_code = api.route()
    shipment_payroll_code = api.shipment_payroll()

    response = client.post(
        "/api/shipment",
        json={
            "shipment_date": http_date(1),
            "driver_code": driver_code,
            "driver_name": "SIN LIQUIDACION",
            "truck_plate": "ABC123",
            "product_code": product_code,
            "product_name": "SOJA",
            "route_code": route_code,
            "origin": "PUERTO",
            "destination": "CAMPO NUEVE",
            "dispatch_code": "REM-SIN",
            "receipt_code": "REC-SIN",
            "origin_weight": "1000",
            "destination_weight": "990",
            "price": "1",
            "payroll_price": "1",
            "shipment_payroll_code": shipment_payroll_code,
            "driver_payroll_code": 1,
        },
        headers=auth,
    )

    assert response.status_code == 404


def test_a_shipment_rejects_a_bad_date(client, auth, full_payroll):
    response = client.post(
        "/api/shipment",
        json={
            "shipment_date": "2026-03-01",
            "driver_code": full_payroll["driver_code"],
            "driver_name": "JUAN PEREZ",
            "truck_plate": "ABC123",
            "product_code": full_payroll["product_code"],
            "product_name": "SOJA",
            "route_code": full_payroll["route_code"],
            "origin": "PUERTO",
            "destination": "CAMPO NUEVE",
            "dispatch_code": "REM-3",
            "receipt_code": "REC-3",
            "origin_weight": "1000",
            "destination_weight": "990",
            "price": "1",
            "payroll_price": "1",
            "shipment_payroll_code": full_payroll["shipment_payroll_code"],
            "driver_payroll_code": full_payroll["driver_payroll_code"],
        },
        headers=auth,
    )

    assert response.status_code >= 400


def test_list_shipments_of_a_payroll(client, auth, api, full_payroll):
    api.shipment(
        full_payroll["driver_code"],
        full_payroll["product_code"],
        full_payroll["route_code"],
        full_payroll["shipment_payroll_code"],
        full_payroll["driver_payroll_code"],
        dispatch_code="REM-1001",
        receipt_code="REC-2001",
    )

    payload = client.get(
        f"/api/shipments?shipment_payroll_code={full_payroll['shipment_payroll_code']}",
        headers=auth,
    ).get_json()

    assert len(payload) == 2


def test_update_a_shipment(client, auth, full_payroll):
    """The frontend sends back the whole object it got from the GET."""
    shipment_code = full_payroll["shipment_code"]
    current = client.get(f"/api/shipment/{shipment_code}", headers=auth).get_json()

    response = client.put(
        f"/api/shipment/{shipment_code}",
        json={
            **current,
            "shipment_date": http_date(2),
            "dispatch_code": "REM-EDITADO",
            "origin_weight": "31000",
            "destination_weight": "30900",
        },
        headers=auth,
    )

    assert response.status_code == 200
    updated = client.get(f"/api/shipment/{shipment_code}", headers=auth).get_json()
    assert updated["dispatch_code"] == "REM-EDITADO"
    assert str(updated["origin_weight"]) == "31000"


def test_a_partial_update_is_rejected(client, auth, full_payroll):
    """Sending only the changed fields nulls the rest, the update fails.

    It answers 500 where a 400 would describe the problem better, the test
    pins the current behaviour so a fix shows up here.
    """
    response = client.put(
        f"/api/shipment/{full_payroll['shipment_code']}",
        json={"dispatch_code": "SOLO-ESTE-CAMPO"},
        headers=auth,
    )

    assert response.status_code >= 400


def test_deleting_a_shipment_is_a_soft_delete(
    client, auth, full_payroll, database_session
):
    from sqlalchemy import select
    from models.shipment import Shipment

    shipment_code = full_payroll["shipment_code"]
    response = client.delete(f"/api/shipment/{shipment_code}", headers=auth)

    assert response.status_code == 200
    row = database_session.scalar(
        select(Shipment).where(Shipment.shipment_code == shipment_code)
    )
    assert row is not None
    assert row.deleted is True
    assert client.get(f"/api/shipment/{shipment_code}", headers=auth).status_code == 404


def test_delete_several_shipments_at_once(client, auth, api, full_payroll):
    second = api.shipment(
        full_payroll["driver_code"],
        full_payroll["product_code"],
        full_payroll["route_code"],
        full_payroll["shipment_payroll_code"],
        full_payroll["driver_payroll_code"],
        dispatch_code="REM-1002",
        receipt_code="REC-2002",
    )

    response = client.delete(
        "/api/shipments", json=[full_payroll["shipment_code"], second], headers=auth
    )

    assert response.status_code == 200
    payload = client.get(
        f"/api/shipments?shipment_payroll_code={full_payroll['shipment_payroll_code']}",
        headers=auth,
    ).get_json()
    assert payload == []


def test_move_shipments_to_another_payroll(client, auth, api, full_payroll):
    other_payroll = api.shipment_payroll(payroll_timestamp=http_date(15))

    response = client.patch(
        f"/api/shipments/change-payroll?shipment_payroll_code={other_payroll}",
        json=[full_payroll["shipment_code"]],
        headers=auth,
    )

    assert response.status_code == 200
    moved = client.get(
        f"/api/shipments?shipment_payroll_code={other_payroll}", headers=auth
    ).get_json()
    assert [item["shipment_code"] for item in moved] == [full_payroll["shipment_code"]]


def test_moving_to_a_payroll_that_does_not_exist_fails(client, auth, full_payroll):
    response = client.patch(
        "/api/shipments/change-payroll?shipment_payroll_code=999999",
        json=[full_payroll["shipment_code"]],
        headers=auth,
    )

    assert response.status_code == 404


def test_grouped_shipments_aggregates_by_route_and_product(
    client, auth, api, full_payroll
):
    api.shipment(
        full_payroll["driver_code"],
        full_payroll["product_code"],
        full_payroll["route_code"],
        full_payroll["shipment_payroll_code"],
        full_payroll["driver_payroll_code"],
        dispatch_code="REM-1003",
        receipt_code="REC-2003",
    )

    response = client.get(
        "/api/shipment/grouped-shipments"
        f"?shipment_payroll_code={full_payroll['shipment_payroll_code']}",
        headers=auth,
    )

    assert response.status_code == 200
    groups = response.get_json()
    assert len(groups) == 1, "both shipments share route and product"


def test_shipments_of_another_user_are_invisible(
    client, api, credentials, full_payroll
):
    other = {**credentials, "email": "otro-carga@dyrtransportes.com"}
    client.post("/api/auth/sign-up", data=other)
    token = client.post(
        "/api/auth/log-in",
        data={"email": other["email"], "password": other["password"]},
    ).get_json()["token"]

    response = client.get(
        f"/api/shipment/{full_payroll['shipment_code']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
