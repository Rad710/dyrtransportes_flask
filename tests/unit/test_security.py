"""Password hashing and the email/password rules of utils/security.py."""

import pytest

from utils.security import hash_password
from utils.security import validate_user_email
from utils.security import validate_user_password
from utils.security import verify_password


def test_hash_password_does_not_keep_the_password():
    hashed = hash_password("Test1234!")

    assert "Test1234!" not in hashed
    assert hashed != "Test1234!"


def test_hash_password_salts_every_hash():
    assert hash_password("Test1234!") != hash_password("Test1234!")


def test_verify_password_accepts_the_right_password():
    assert verify_password("Test1234!", hash_password("Test1234!"))


@pytest.mark.parametrize("wrong", ["test1234!", "Test1234", "", "otra-clave"])
def test_verify_password_rejects_the_wrong_password(wrong):
    assert not verify_password(wrong, hash_password("Test1234!"))


def test_verify_password_survives_a_malformed_stored_value():
    assert not verify_password("Test1234!", "no-es-un-hash")


@pytest.mark.parametrize(
    "email", ["user@dyrtransportes.com", "first.last@sub.domain.com", "a@b.co"]
)
def test_validate_user_email_accepts_valid_addresses(email):
    assert validate_user_email(email) is None


@pytest.mark.parametrize("email", ["", "sin-arroba", "@dominio.com", "user@", "a@b"])
def test_validate_user_email_rejects_invalid_addresses(email):
    assert validate_user_email(email) is not None


def test_validate_user_password_accepts_a_strong_password():
    assert validate_user_password("Test1234!") is None


@pytest.mark.parametrize("password", ["", "corta", "12345678"])
def test_validate_user_password_rejects_weak_passwords(password):
    assert validate_user_password(password) is not None
