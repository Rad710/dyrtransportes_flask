"""Language negotiation and message lookup of utils/locale.py."""

import pytest

from flask import Flask

from utils.locale import get_locale
from utils.locale import get_message

MESSAGES = {
    "en": {"greeting": "Hello", "only_english": "English only"},
    "es": {"greeting": "Hola"},
}


def context(accept_language=None):
    app = Flask(__name__)
    headers = {"Accept-Language": accept_language} if accept_language else {}
    return app.test_request_context(headers=headers)


@pytest.mark.parametrize(
    "accept_language, expected",
    [
        ("es-ES,es;q=0.9", "es"),
        ("es", "es"),
        ("ES-py", "es"),
        ("en-US,en;q=0.9", "en"),
        ("fr-FR", "en"),
        ("", "en"),
        (None, "en"),
        (",", "en"),
    ],
)
def test_get_locale_reads_the_accept_language_header(accept_language, expected):
    with context(accept_language):
        assert get_locale() == expected


def test_get_message_translates_to_the_preferred_language():
    with context("es-ES,es"):
        assert get_message(MESSAGES, "greeting") == "Hola"

    with context("en-US,en"):
        assert get_message(MESSAGES, "greeting") == "Hello"


def test_get_message_falls_back_to_english_when_untranslated():
    with context("es-ES,es"):
        assert get_message(MESSAGES, "only_english") == "English only"


def test_get_message_returns_the_key_when_the_message_is_missing():
    with context("es-ES,es"):
        assert get_message(MESSAGES, "no_existe") == "no_existe"
