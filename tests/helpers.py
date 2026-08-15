"""Helpers shared by the tests.

They live here and not in conftest.py because every directory has its own
conftest module and 'import conftest' resolves to whichever was imported first.
"""

TEST_API_KEY = "test-secret-key-that-is-long-enough-for-hs256"


def http_date(day: int, month: str = "Mar", year: int = 2026) -> str:
    """Date in the format the API parses, 'Day, DD Mon YYYY HH:MM:SS GMT'."""
    return f"Sun, {day:02d} {month} {year} 00:00:00 GMT"


def audit_triggers_installed(db_session) -> bool:
    """The *_audit tables are filled by the triggers of migrations/not-applied.

    They are not part of the applied migrations, so a fresh database has no
    audit trail at all and the tests covering it cannot run.
    """
    from sqlalchemy import text

    return bool(db_session.execute(text("SHOW TRIGGERS")).first())
