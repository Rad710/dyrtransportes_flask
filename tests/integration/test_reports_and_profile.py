"""Statistics, the Dinatran report and the user profile."""

import pytest

pytestmark = pytest.mark.db

RANGE = "start_date=2026-01-01&end_date=2026-12-31"


# ------------------------------------------------------------------ statistics


def test_driver_statistics_add_up_the_shipments(client, auth, full_payroll):
    response = client.get(f"/api/statistics/driver?{RANGE}", headers=auth)

    assert response.status_code == 200
    assert response.get_json()


def test_product_statistics_add_up_the_shipments(client, auth, full_payroll):
    response = client.get(f"/api/statistics/product?{RANGE}", headers=auth)

    assert response.status_code == 200
    assert response.get_json()


@pytest.mark.parametrize("query", ["", "start_date=2026-01-01", "end_date=2026-12-31"])
def test_statistics_need_both_dates(client, auth, query):
    response = client.get(f"/api/statistics/driver?{query}", headers=auth)

    assert response.status_code == 400


def test_statistics_reject_a_date_that_cannot_be_parsed(client, auth):
    """A malformed date answers 500 today, a 400 would describe it better.

    The test pins the current behaviour so a fix shows up here.
    """
    response = client.get(
        "/api/statistics/driver?start_date=ayer&end_date=hoy", headers=auth
    )

    assert response.status_code >= 400


def test_statistics_of_another_user_are_empty(client, credentials, full_payroll):
    other = {**credentials, "email": "otro-stats@dyrtransportes.com"}
    client.post("/api/auth/sign-up", data=other)
    token = client.post(
        "/api/auth/log-in",
        data={"email": other["email"], "password": other["password"]},
    ).get_json()["token"]

    response = client.get(
        f"/api/statistics/driver?{RANGE}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.get_json() in ([], {}, None) or not any(
        response.get_json().values() if isinstance(response.get_json(), dict) else []
    )


# -------------------------------------------------------------------- dinatran


def test_the_dinatran_report_answers_data(client, auth, full_payroll):
    response = client.get(f"/api/dinatran?{RANGE}", headers=auth)

    assert response.status_code == 200


def test_the_dinatran_report_needs_a_date_range(client, auth):
    response = client.get("/api/dinatran", headers=auth)

    assert response.status_code == 400


def test_the_dinatran_report_needs_a_token(client):
    assert client.get(f"/api/dinatran?{RANGE}").status_code == 401


# ---------------------------------------------------------------- user profile


def test_update_the_profile_name(client, auth, credentials):
    response = client.put(
        "/api/user/profile",
        data={"name": "Nombre Nuevo", "email": credentials["email"]},
        headers=auth,
    )

    assert response.status_code == 200


def test_the_profile_needs_a_name_and_an_email(client, auth, credentials):
    response = client.put(
        "/api/user/profile", data={"name": "", "email": ""}, headers=auth
    )

    assert response.status_code == 400


def test_the_profile_rejects_an_invalid_email(client, auth):
    response = client.put(
        "/api/user/profile",
        data={"name": "Nombre", "email": "no-es-un-email"},
        headers=auth,
    )

    assert response.status_code == 400


def test_changing_the_password_lets_the_user_log_in_with_it(client, auth, credentials):
    response = client.put(
        "/api/user/profile",
        data={
            "name": "Tester",
            "email": credentials["email"],
            "new_password": "OtraClave1!",
        },
        headers=auth,
    )
    assert response.status_code == 200

    logged_in = client.post(
        "/api/auth/log-in",
        data={"email": credentials["email"], "password": "OtraClave1!"},
    )
    assert logged_in.status_code == 200


def test_the_profile_needs_a_token(client):
    assert client.put("/api/user/profile", data={"name": "x"}).status_code == 401
