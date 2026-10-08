from pathlib import Path

MESSAGE = {
    "customer_name": "Rahul Mehta",
    "customer_email": "rahul@example.com",
    "subject": "Charged twice",
    "body": "Order PP-482913 was charged twice.",
}
SAMPLE_CSV = Path(__file__).parents[2] / "eval" / "emails.csv"


def make_ticket(client, **changes):
    r = client.post("/tickets", json={**MESSAGE, **changes})
    assert r.status_code == 201, r.text
    return r.json()


# ---- create ----


def test_customer_can_create_ticket_without_login(client):
    ticket = make_ticket(client)
    assert ticket["status"] == "new"  # the response is sent before the agents run
    assert ticket["category"] is None
    assert ticket["subject"] == "Charged twice"


def test_create_ticket_trims_whitespace(client):
    ticket = make_ticket(client, customer_name="  Rahul  ")
    assert ticket["customer_name"] == "Rahul"


def test_create_ticket_rejects_bad_input(client):
    assert client.post("/tickets", json={**MESSAGE, "body": "   "}).status_code == 422
    assert client.post("/tickets", json={**MESSAGE, "customer_email": "nope"}).status_code == 422
    assert client.post("/tickets", json={**MESSAGE, "body": "x" * 5001}).status_code == 422


# ---- list and detail ----


def test_listing_requires_login(client):
    assert client.get("/tickets").status_code == 401


def test_list_is_newest_first(client, auth):
    first, second = make_ticket(client, subject="first"), make_ticket(client, subject="second")
    ids = [t["id"] for t in client.get("/tickets", headers=auth).json()]
    assert ids == [second["id"], first["id"]]


def test_list_filters_by_status_category_and_urgency(client, auth, db):
    from app.models import Ticket, TicketStatus

    # Created directly in the database (no agents) so each ticket has exactly the values we set.
    a = Ticket(**MESSAGE)
    b = Ticket(**MESSAGE, category="billing", urgency="high", status=TicketStatus.APPROVED)
    db.add_all([a, b])
    db.commit()

    def ids(**params):
        return [t["id"] for t in client.get("/tickets", params=params, headers=auth).json()]

    assert ids(status="new") == [a.id]
    assert ids(status="approved") == [b.id]
    assert ids(category="billing") == [b.id]
    assert ids(urgency="high", category="billing") == [b.id]
    assert ids(urgency="low") == []
    assert client.get("/tickets", params={"status": "bogus"}, headers=auth).status_code == 422


def test_list_limit_and_offset(client, auth):
    for i in range(5):
        make_ticket(client, subject=f"t{i}")
    page = client.get("/tickets", params={"limit": 2, "offset": 1}, headers=auth).json()
    assert [t["subject"] for t in page] == ["t3", "t2"]


def test_ticket_detail_includes_agent_runs(client, auth, db):
    from app.models import AgentRun, Ticket

    ticket = Ticket(**MESSAGE)
    db.add(ticket)
    db.commit()
    db.add(
        AgentRun(
            ticket_id=ticket.id,
            agent_name="sorter",
            input="in",
            output="out",
            ok=True,
            duration_ms=120,
        )
    )
    db.commit()
    r = client.get(f"/tickets/{ticket.id}", headers=auth)
    assert r.status_code == 200
    runs = r.json()["agent_runs"]
    assert len(runs) == 1 and runs[0]["agent_name"] == "sorter" and runs[0]["duration_ms"] == 120


def test_ticket_detail_404_and_login_required(client, auth):
    assert client.get("/tickets/999", headers=auth).status_code == 404
    assert client.get("/tickets/1").status_code == 401


# ---- CSV import ----


def upload(client, auth, content: bytes):
    return client.post(
        "/tickets/import", files={"file": ("t.csv", content, "text/csv")}, headers=auth
    )


def test_import_the_60_sample_messages(client, auth):
    r = upload(client, auth, SAMPLE_CSV.read_bytes())
    assert r.status_code == 200
    assert r.json() == {"created": 60, "errors": []}
    assert len(client.get("/tickets", params={"limit": 200}, headers=auth).json()) == 60


def test_import_reports_bad_rows_and_saves_good_ones(client, auth):
    csv_text = (
        "customer_name,customer_email,subject,body\n"
        "Asha,asha@example.com,Hi,Where is my order?\n"
        "Bad,not-an-email,Hi,Hello\n"
        "Empty,e@example.com,Hi,\n"
    )
    r = upload(client, auth, csv_text.encode())
    assert r.json()["created"] == 1
    assert r.json()["errors"] == [
        {"row": 2, "error": "Invalid: customer_email"},
        {"row": 3, "error": "Invalid: body"},
    ]


def test_import_rejects_missing_columns(client, auth):
    r = upload(client, auth, b"name,email\nA,a@example.com\n")
    assert r.status_code == 400
    assert "customer_email" in r.json()["detail"]


def test_import_handles_excel_bom(client, auth):
    content = "﻿customer_name,customer_email,subject,body\nA,a@example.com,S,B\n".encode()
    assert upload(client, auth, content).json()["created"] == 1


def test_import_requires_login(client):
    r = client.post("/tickets/import", files={"file": ("t.csv", b"x", "text/csv")})
    assert r.status_code == 401
