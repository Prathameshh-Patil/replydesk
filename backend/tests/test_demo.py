"""Live-demo safeguards: the daily ticket limit and the one-click demo login."""

import io

from app.core.settings import settings
from tests.test_tickets import MESSAGE, make_ticket


def import_csv(client, auth, rows):
    lines = ["customer_name,customer_email,subject,body"]
    lines += [f"Ravi,ravi@example.com,Subject {i},Body {i}" for i in range(rows)]
    file = io.BytesIO("\n".join(lines).encode())
    return client.post("/tickets/import", headers=auth, files={"file": ("t.csv", file)})


# ---- daily ticket limit ----


def test_no_limit_by_default(client):
    for _ in range(3):
        make_ticket(client)


def test_new_tickets_are_refused_once_the_daily_limit_is_reached(client, monkeypatch):
    monkeypatch.setattr(settings, "daily_ticket_limit", 2)
    make_ticket(client)
    make_ticket(client)
    r = client.post("/tickets", json=MESSAGE)
    assert r.status_code == 429
    assert "2 new messages a day" in r.json()["detail"]


def test_import_counts_towards_the_daily_limit(client, auth, monkeypatch):
    monkeypatch.setattr(settings, "daily_ticket_limit", 3)
    make_ticket(client)
    assert import_csv(client, auth, rows=3).status_code == 429  # 1 + 3 > 3: nothing saved
    assert import_csv(client, auth, rows=2).json()["created"] == 2
    assert client.post("/tickets", json=MESSAGE).status_code == 429


# ---- demo login ----


def test_demo_login_is_off_by_default(client, staff):
    assert client.post("/auth/demo").status_code == 404


def test_demo_login_gives_a_token_for_the_demo_account(client, staff, monkeypatch):
    monkeypatch.setattr(settings, "demo_email", "ASHA@example.com")
    r = client.post("/auth/demo")
    assert r.status_code == 200
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {r.json()['access_token']}"})
    assert me.json()["email"] == staff.email


def test_demo_login_fails_if_the_demo_account_does_not_exist(client, staff, monkeypatch):
    monkeypatch.setattr(settings, "demo_email", "nobody@example.com")
    assert client.post("/auth/demo").status_code == 404


# ---- hosted database URLs ----


def test_hosted_postgres_urls_get_the_psycopg_driver():
    from app.core.settings import Settings

    url = "postgresql://u:p@ep-x.neon.tech/db?sslmode=require"
    assert Settings(database_url=url).database_url == "postgresql+psycopg://" + url[13:]
    assert Settings(database_url="postgres://u:p@h/db").database_url.startswith(
        "postgresql+psycopg://"
    )


# ---- demo account on start-up ----


def test_demo_account_is_created_once(client, db, monkeypatch):
    from sqlalchemy import func, select

    from app.demo import ensure_demo_user
    from app.models import User

    monkeypatch.setattr(settings, "demo_email", "demo@replydesk.dev")
    ensure_demo_user()
    ensure_demo_user()  # a restart doesn't make a second one
    assert db.scalar(select(func.count()).select_from(User)) == 1
    assert client.post("/auth/demo").status_code == 200


def test_no_demo_account_without_demo_email(db):
    from sqlalchemy import func, select

    from app.demo import ensure_demo_user
    from app.models import User

    ensure_demo_user()
    assert db.scalar(select(func.count()).select_from(User)) == 0
