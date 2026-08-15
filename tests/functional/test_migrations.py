"""The alembic migrations on a database without the legacy tables.

The migrations copy data from the old database. A fresh install has none of
those tables and must still reach head instead of failing.
"""

import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.db

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ALEMBIC_INI = os.path.join(REPO_ROOT, "src", "migrations", "alembic.ini")

LEGACY_TABLES = [
    "precios",
    "palabras",
    "planillas",
    "cobranzas",
    "liquidaciones",
    "liquidacion_viajes",
    "liquidacion_gastos",
]


def run_alembic(*arguments, database: str):
    environment = {**os.environ, "DB_NAME": database}
    return subprocess.run(
        [sys.executable, "-m", "alembic", "-c", ALEMBIC_INI, *arguments],
        capture_output=True,
        check=False,
        cwd=REPO_ROOT,
        env=environment,
        timeout=300,
    )


@pytest.fixture
def empty_database(database_session):
    """A database of its own, with no tables at all."""
    from sqlalchemy import text

    name = "dyrtransportes_migrations_test"
    engine = database_session.get_bind()
    with engine.connect() as connection:
        connection.execute(text(f"DROP DATABASE IF EXISTS `{name}`"))
        connection.execute(text(f"CREATE DATABASE `{name}`"))

    yield name

    with engine.connect() as connection:
        connection.execute(text(f"DROP DATABASE IF EXISTS `{name}`"))


def test_migrations_reach_head_without_the_legacy_database(empty_database):
    result = run_alembic("upgrade", "head", database=empty_database)

    assert result.returncode == 0, result.stderr.decode()


def test_every_migration_reports_that_it_was_skipped(empty_database):
    result = run_alembic("upgrade", "head", database=empty_database)

    output = result.stdout.decode() + result.stderr.decode()
    assert output.count("skipping data migration") == 7


def test_the_current_revision_is_head_afterwards(empty_database):
    run_alembic("upgrade", "head", database=empty_database)
    result = run_alembic("current", database=empty_database)

    assert b"(head)" in result.stdout + result.stderr


def test_the_guard_names_the_tables_that_are_missing(empty_database):
    result = run_alembic("upgrade", "head", database=empty_database)

    output = result.stdout.decode() + result.stderr.decode()
    for table in LEGACY_TABLES:
        assert table in output, f"the guard should name {table}"


def test_running_the_migrations_twice_is_harmless(empty_database):
    first = run_alembic("upgrade", "head", database=empty_database)
    second = run_alembic("upgrade", "head", database=empty_database)

    assert first.returncode == 0
    assert second.returncode == 0, second.stderr.decode()
