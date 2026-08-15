"""Sign up, log in and the JWT the rest of the API depends on."""

import jwt
import pytest

from helpers import TEST_API_KEY as TEST_KEY

pytestmark = pytest.mark.db


def test_hello_world_needs_no_token(client):
    response = client.get("/api/hello-world")

    assert response.status_code == 200


def test_sign_up_creates_the_user(client, credentials):
    response = client.post("/api/auth/sign-up", data=credentials)

    assert response.status_code == 201


def test_sign_up_rejects_a_duplicated_email(client, credentials):
    client.post("/api/auth/sign-up", data=credentials)
    response = client.post("/api/auth/sign-up", data=credentials)

    assert response.status_code >= 400


@pytest.mark.parametrize("missing", ["name", "email", "password"])
def test_sign_up_requires_every_field(client, credentials, missing):
    del credentials[missing]
    response = client.post("/api/auth/sign-up", data=credentials)

    assert response.status_code >= 400


def test_sign_up_rejects_an_invalid_email(client, credentials):
    credentials["email"] = "no-es-un-email"
    response = client.post("/api/auth/sign-up", data=credentials)

    assert response.status_code >= 400


def test_sign_up_rejects_a_weak_password(client, credentials):
    credentials["password"] = "corta"
    response = client.post("/api/auth/sign-up", data=credentials)

    assert response.status_code >= 400


def test_log_in_returns_a_usable_token(client, credentials):
    client.post("/api/auth/sign-up", data=credentials)
    response = client.post(
        "/api/auth/log-in",
        data={"email": credentials["email"], "password": credentials["password"]},
    )

    assert response.status_code == 200
    token = response.get_json()["token"]
    claims = jwt.decode(token, TEST_KEY, algorithms=["HS256"])
    assert claims["user_id"]
    assert claims["exp"]


def test_log_in_rejects_a_wrong_password(client, credentials):
    client.post("/api/auth/sign-up", data=credentials)
    response = client.post(
        "/api/auth/log-in",
        data={"email": credentials["email"], "password": "OtraClave1!"},
    )

    assert response.status_code >= 400


def test_log_in_rejects_an_unknown_user(client):
    response = client.post(
        "/api/auth/log-in",
        data={"email": "no-existe@dyrtransportes.com", "password": "Test1234!"},
    )

    assert response.status_code >= 400


def test_remember_me_lasts_longer(client, credentials):
    client.post("/api/auth/sign-up", data=credentials)
    short = client.post(
        "/api/auth/log-in",
        data={"email": credentials["email"], "password": credentials["password"]},
    ).get_json()["token"]
    long = client.post(
        "/api/auth/log-in",
        data={
            "email": credentials["email"],
            "password": credentials["password"],
            "remember_me": "on",
        },
    ).get_json()["token"]

    short_exp = jwt.decode(short, TEST_KEY, algorithms=["HS256"])["exp"]
    long_exp = jwt.decode(long, TEST_KEY, algorithms=["HS256"])["exp"]
    assert long_exp > short_exp


def test_a_protected_endpoint_rejects_a_request_without_a_token(client):
    response = client.get("/api/drivers")

    assert response.status_code == 401


@pytest.mark.parametrize(
    "header",
    ["", "Bearer", "Bearer no-es-un-token", "Basic abc", "Bearer a.b.c"],
)
def test_a_protected_endpoint_rejects_a_malformed_token(client, header):
    response = client.get("/api/drivers", headers={"Authorization": header})

    assert response.status_code == 401


def test_a_token_signed_with_another_key_is_rejected(client):
    forged = jwt.encode({"user_id": "1", "email": "x@y.com"}, "otra-clave")
    response = client.get("/api/drivers", headers={"Authorization": f"Bearer {forged}"})

    assert response.status_code == 401


def test_a_valid_token_gets_through(client, auth):
    response = client.get("/api/drivers", headers=auth)

    assert response.status_code == 200
