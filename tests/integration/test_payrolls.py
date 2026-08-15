"""Shipment payrolls (Planillas), driver payrolls (Liquidaciones) and expenses."""

import pytest

from helpers import http_date

pytestmark = pytest.mark.db


# ----------------------------------------------------------- shipment payrolls


def test_create_and_read_a_shipment_payroll(client, auth, api):
    payroll_code = api.shipment_payroll()

    response = client.get(f"/api/shipment-payroll/{payroll_code}", headers=auth)

    assert response.status_code == 200
    assert response.get_json()["collected"] is False


def test_a_shipment_payroll_needs_a_valid_date(client, auth):
    response = client.post(
        "/api/shipment-payroll", json={"payroll_timestamp": "2026-03-31"}, headers=auth
    )

    assert response.status_code >= 400


def test_list_shipment_payrolls_filters_by_year(client, auth, api):
    api.shipment_payroll(payroll_timestamp=http_date(15))
    api.shipment_payroll(payroll_timestamp=http_date(20, "Dec", 2025))

    of_2026 = client.get("/api/shipment-payrolls?year=2026", headers=auth).get_json()
    of_2025 = client.get("/api/shipment-payrolls?year=2025", headers=auth).get_json()
    every_year = client.get("/api/shipment-payrolls", headers=auth).get_json()

    assert len(of_2026) == 1
    assert len(of_2025) == 1
    assert len(every_year) == 2


def test_list_shipment_payrolls_rejects_a_year_that_is_not_a_number(client, auth):
    response = client.get("/api/shipment-payrolls?year=dos-mil", headers=auth)

    assert response.status_code == 400


def test_mark_a_shipment_payroll_as_collected(client, auth, api):
    payroll_code = api.shipment_payroll()

    response = client.patch(
        f"/api/shipment-payroll/{payroll_code}/collection-status",
        json={"collected": True},
        headers=auth,
    )

    assert response.status_code == 200
    updated = client.get(
        f"/api/shipment-payroll/{payroll_code}", headers=auth
    ).get_json()
    assert updated["collected"] is True
    assert updated["collection_timestamp"] is not None


def test_deleting_a_shipment_payroll_is_a_soft_delete(
    client, auth, api, database_session
):
    from sqlalchemy import select
    from models.shipment_payroll import ShipmentPayroll

    payroll_code = api.shipment_payroll()
    client.delete(f"/api/shipment-payroll/{payroll_code}", headers=auth)

    row = database_session.scalar(
        select(ShipmentPayroll).where(ShipmentPayroll.payroll_code == payroll_code)
    )
    assert row.deleted is True


def test_delete_several_shipment_payrolls_at_once(client, auth, api):
    first = api.shipment_payroll(payroll_timestamp=http_date(10))
    second = api.shipment_payroll(payroll_timestamp=http_date(11))

    response = client.delete(
        "/api/shipment-payrolls", json=[first, second], headers=auth
    )

    assert response.status_code == 200
    payload = client.get("/api/shipment-payrolls?year=2026", headers=auth).get_json()
    assert payload == []


# ------------------------------------------------------------- driver payrolls


def test_create_and_read_a_driver_payroll(client, auth, api):
    driver_code = api.driver()
    payroll_code = api.driver_payroll(driver_code)

    response = client.get(f"/api/driver-payroll/{payroll_code}", headers=auth)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["driver_code"] == driver_code
    assert payload["paid"] is False


def test_list_the_payrolls_of_a_driver(client, auth, api):
    driver_code = api.driver()
    api.driver_payroll(driver_code, payroll_timestamp=http_date(15))
    api.driver_payroll(driver_code, payroll_timestamp=http_date(20))

    response = client.get(f"/api/driver/{driver_code}/payrolls", headers=auth)

    assert response.status_code == 200
    assert len(response.get_json()) == 2


def test_mark_a_driver_payroll_as_paid(client, auth, api):
    driver_code = api.driver()
    payroll_code = api.driver_payroll(driver_code)

    response = client.patch(
        f"/api/driver-payroll/{payroll_code}/paid-status",
        json={"paid": True},
        headers=auth,
    )

    assert response.status_code == 200
    updated = client.get(f"/api/driver-payroll/{payroll_code}", headers=auth).get_json()
    assert updated["paid"] is True
    assert updated["paid_timestamp"] is not None


def test_the_paid_status_needs_the_field(client, auth, api):
    driver_code = api.driver()
    payroll_code = api.driver_payroll(driver_code)

    response = client.patch(
        f"/api/driver-payroll/{payroll_code}/paid-status", json={}, headers=auth
    )

    assert response.status_code >= 400


def test_deleting_a_driver_payroll_is_a_soft_delete(
    client, auth, api, database_session
):
    from sqlalchemy import select
    from models.driver_payroll import DriverPayroll

    driver_code = api.driver()
    payroll_code = api.driver_payroll(driver_code)
    client.delete(f"/api/driver-payroll/{payroll_code}", headers=auth)

    row = database_session.scalar(
        select(DriverPayroll).where(DriverPayroll.payroll_code == payroll_code)
    )
    assert row.deleted is True


def test_an_unknown_driver_payroll_is_not_found(client, auth):
    assert client.get("/api/driver-payroll/999999", headers=auth).status_code == 404


# ----------------------------------------------------------- shipment expenses


def test_create_and_read_an_expense(client, auth, full_payroll):
    response = client.get(
        f"/api/shipment-expense/{full_payroll['expense_code']}", headers=auth
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["reason"] == "GASOIL"
    assert str(payload["amount"]) == "100000"


def test_list_the_expenses_of_a_payroll(client, auth, api, full_payroll):
    api.shipment_expense(
        full_payroll["driver_payroll_code"], reason="PEAJE", amount="20000"
    )

    payload = client.get(
        f"/api/shipment-expenses?driver_payroll_code={full_payroll['driver_payroll_code']}",
        headers=auth,
    ).get_json()

    assert sorted(expense["reason"] for expense in payload) == ["GASOIL", "PEAJE"]


def test_an_expense_rejects_a_bad_date(client, auth, full_payroll):
    response = client.post(
        "/api/shipment-expense",
        json={
            "expense_date": "2026-03-01",
            "reason": "GASOIL",
            "amount": "1000",
            "receipt": "B-9",
            "driver_payroll_code": full_payroll["driver_payroll_code"],
        },
        headers=auth,
    )

    assert response.status_code >= 400


def test_update_an_expense(client, auth, full_payroll):
    expense_code = full_payroll["expense_code"]
    current = client.get(
        f"/api/shipment-expense/{expense_code}", headers=auth
    ).get_json()

    response = client.put(
        f"/api/shipment-expense/{expense_code}",
        json={**current, "reason": "PEAJE", "amount": "12345"},
        headers=auth,
    )

    assert response.status_code == 200
    updated = client.get(
        f"/api/shipment-expense/{expense_code}", headers=auth
    ).get_json()
    assert updated["reason"] == "PEAJE"
    assert str(updated["amount"]) == "12345"


def test_deleting_an_expense_is_a_soft_delete(
    client, auth, full_payroll, database_session
):
    from sqlalchemy import select
    from models.shipment_expense import ShipmentExpense

    expense_code = full_payroll["expense_code"]
    client.delete(f"/api/shipment-expense/{expense_code}", headers=auth)

    row = database_session.scalar(
        select(ShipmentExpense).where(ShipmentExpense.expense_code == expense_code)
    )
    assert row.deleted is True


def test_move_expenses_to_another_driver_payroll(client, auth, api, full_payroll):
    other_payroll = api.driver_payroll(
        full_payroll["driver_code"], payroll_timestamp=http_date(20)
    )

    response = client.patch(
        f"/api/shipment-expenses/change-driver-payroll?driver_payroll_code={other_payroll}",
        json=[full_payroll["expense_code"]],
        headers=auth,
    )

    assert response.status_code == 200
    moved = client.get(
        f"/api/shipment-expenses?driver_payroll_code={other_payroll}", headers=auth
    ).get_json()
    assert [item["expense_code"] for item in moved] == [full_payroll["expense_code"]]
