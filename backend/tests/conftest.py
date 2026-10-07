"""Shared test setup: a separate PostgreSQL test database, emptied before every test."""

import os

# Must be set before the app is imported, so the app connects to the test database.
# Always overwritten (never taken from DATABASE_URL): tests empty every table after each run,
# so they must never point at a real database.
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://replydesk:replydesk@localhost:5442/replydesk_test"
)
os.environ["ENVIRONMENT"] = "test"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User  # noqa: E402


def _create_test_database() -> None:
    """Create the test database if it doesn't exist (connects to the default 'postgres' db)."""
    url = make_url(os.environ["DATABASE_URL"])
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": url.database}
        )
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    admin.dispose()


@pytest.fixture(scope="session", autouse=True)
def database():
    _create_test_database()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_tables(database):
    """Every test starts with empty tables."""
    yield
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE agent_runs, tickets, users RESTART IDENTITY CASCADE"))


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def staff(db):
    """A staff user (password: correct-horse)."""
    user = User(name="Asha", email="asha@example.com", password_hash=hash_password("correct-horse"))
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def auth(client, staff):
    """Headers for a logged-in staff user."""
    r = client.post("/auth/login", data={"username": staff.email, "password": "correct-horse"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
