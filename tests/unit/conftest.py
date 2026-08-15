"""Unit tests touch no database, but the code under test reads the locale.

get_message() resolves the language from the Accept-Language header, so it
needs a request context even outside of a route. A bare Flask app provides it,
without importing the application and connecting to the database.
"""

import pytest

from flask import Flask


@pytest.fixture(autouse=True)
def spanish_request_context():
    app = Flask(__name__)
    with app.test_request_context(headers={"Accept-Language": "es-ES,es"}):
        yield


@pytest.fixture
def english_request_context():
    app = Flask(__name__)
    with app.test_request_context(headers={"Accept-Language": "en-US,en"}):
        yield
