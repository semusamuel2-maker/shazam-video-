"""Test fixtures. Uses a throwaway SQLite file so no Postgres is required."""
from __future__ import annotations

import os
import tempfile

# Must be set before any app module imports (engine is bound at import time).
_TMP_DB = os.path.join(tempfile.gettempdir(), "canre_test.sqlite3")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB}"
os.environ["ALLOW_ELECTRONIC_OUTREACH"] = "false"

import pytest  # noqa: E402

from app.db import Base, SessionLocal, engine  # noqa: E402


@pytest.fixture
def session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestClient(app)
