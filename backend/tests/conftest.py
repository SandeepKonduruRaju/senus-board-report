"""
Shared pytest fixtures.

Points the app at an isolated temp-file SQLite database (set via
DATABASE_URL *before* any `app.*` module is imported, so database.py's
module-level `create_engine()` call picks it up naturally) and seeds it
using the same seed_db.seed() the real app uses — tests exercise the real
seeding logic, not a hand-rolled fixture that could drift from it.
"""
import os
import tempfile

import pytest

# Must run before any `from app...` import anywhere in the test session.
_tmp_db_fd, _tmp_db_path = tempfile.mkstemp(suffix=".db")
os.close(_tmp_db_fd)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db_path}"

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from data.seed_db import seed  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _seeded_database():
    seed()
    yield
    os.remove(_tmp_db_path)


@pytest.fixture()
def client():
    return TestClient(app)
