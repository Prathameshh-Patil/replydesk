"""Human review: approve (with or without edits), reject, and the stats endpoint."""

import pytest

from app.models import AgentRun, Ticket, TicketStatus

DRAFT = "Hi Rahul,\n\nWe've raised a request.\n\nTeam Pixel & Plug"


@pytest.fixture
def make(db):
    """Create a ticket directly in the database in any state."""

    def _make(status=TicketStatus.READY_FOR_REVIEW, draft=DRAFT, **fields):
        t = Ticket(
            customer_name="Rahul",
            customer_email="r@example.com",
            subject="S",
            body="B",
            status=status,
            draft_reply=draft,
            **fields,
        )
        db.add(t)
        db.commit()
        return t

    return _make


def reload(db, ticket):
    db.expire_all()
    return db.get(Ticket, ticket.id)


# ---- approve -----------------------------------------------------------------------------------


def test_approve_without_edits_sends_the_draft(client, auth, db, make, staff):
    t = make()
    r = client.post(f"/tickets/{t.id}/approve", headers=auth)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "approved"
    assert body["final_reply"] == DRAFT and body["edited"] is False
    assert body["reviewed_by"] == staff.id and body["reviewed_at"] is not None


def test_approve_with_an_edited_reply(client, auth, make):
    t = make()
    edited = DRAFT.replace("raised a request", "raised a request for order PP-482913")
    body = client.post(
        f"/tickets/{t.id}/approve", json={"final_reply": edited}, headers=auth
    ).json()
    assert body["final_reply"] == edited and body["edited"] is True


def test_whitespace_only_changes_are_not_edits(client, auth, make):
    t = make()
    body = client.post(
        f"/tickets/{t.id}/approve", json={"final_reply": f"\n  {DRAFT}  \n"}, headers=auth
    ).json()
    assert body["edited"] is False


def test_needs_manual_ticket_can_be_approved_with_a_written_reply(client, auth, make):
    t = make(status=TicketStatus.NEEDS_MANUAL, draft=None)
    no_reply = client.post(f"/tickets/{t.id}/approve", headers=auth)
    assert no_reply.status_code == 422  # nothing to send

    body = client.post(
        f"/tickets/{t.id}/approve", json={"final_reply": "Hi, written by a human."}, headers=auth
    ).json()
    assert body["status"] == "approved" and body["edited"] is True


@pytest.mark.parametrize(
    "status",
    [TicketStatus.NEW, TicketStatus.PROCESSING, TicketStatus.APPROVED, TicketStatus.REJECTED],
)
def test_only_tickets_waiting_for_review_can_be_decided(client, auth, make, status):
    t = make(status=status)
    assert client.post(f"/tickets/{t.id}/approve", headers=auth).status_code == 409
    assert client.post(f"/tickets/{t.id}/reject", headers=auth).status_code == 409


def test_review_needs_login_and_an_existing_ticket(client, auth, make):
    t = make()
    assert client.post(f"/tickets/{t.id}/approve").status_code == 401
    assert client.post(f"/tickets/{t.id}/reject").status_code == 401
    assert client.post("/tickets/999/approve", headers=auth).status_code == 404


# ---- reject ------------------------------------------------------------------------------------


def test_reject_sends_nothing_and_can_be_rerun(client, auth, db, make, staff):
    t = make()
    body = client.post(f"/tickets/{t.id}/reject", headers=auth).json()
    assert body["status"] == "rejected" and body["final_reply"] is None
    assert body["reviewed_by"] == staff.id

    assert client.post(f"/tickets/{t.id}/rerun", headers=auth).status_code == 202
    t = reload(db, t)
    assert t.status == TicketStatus.READY_FOR_REVIEW  # a fresh draft from the (fake) agents
    assert t.reviewed_by is None and t.reviewed_at is None


# ---- stats -------------------------------------------------------------------------------------


def test_stats_on_an_empty_inbox(client, auth):
    s = client.get("/stats", headers=auth).json()
    assert s["total_tickets"] == 0
    assert s["by_status"]["new"] == 0
    assert s["share_approved_without_edits"] is None and s["checker_pass_rate"] is None
    assert s["avg_ms_per_step"] == {}


def test_stats_counts_and_shares(client, auth, db, make):
    a = make(category="billing", checker_ok=True)
    b = make(category="billing", checker_ok=True)
    c = make(category="refund", checker_ok=False)
    make(status=TicketStatus.NEEDS_MANUAL, draft=None, category="other")
    client.post(f"/tickets/{a.id}/approve", headers=auth)  # unedited
    client.post(f"/tickets/{b.id}/approve", json={"final_reply": "Rewritten."}, headers=auth)
    client.post(f"/tickets/{c.id}/reject", headers=auth)
    db.add_all(
        [
            AgentRun(ticket_id=a.id, agent_name="sorter", input="", ok=True, duration_ms=1000),
            AgentRun(ticket_id=b.id, agent_name="sorter", input="", ok=True, duration_ms=3000),
            AgentRun(ticket_id=b.id, agent_name="sorter", input="", ok=False, duration_ms=60000),
            AgentRun(ticket_id=a.id, agent_name="drafter", input="", ok=True, duration_ms=4000),
        ]
    )
    db.commit()

    s = client.get("/stats", headers=auth).json()
    assert s["total_tickets"] == 4
    assert s["by_status"]["approved"] == 2 and s["by_status"]["rejected"] == 1
    assert s["by_status"]["needs_manual"] == 1
    assert s["by_category"] == {"billing": 2, "refund": 1, "other": 1}
    assert s["approved"] == 2 and s["approved_without_edits"] == 1
    assert s["share_approved_without_edits"] == 0.5
    assert s["checked_drafts"] == 3 and s["checker_pass_rate"] == pytest.approx(0.667)
    # failed runs (the 60 s timeout) are left out of the averages
    assert s["avg_ms_per_step"] == {"sorter": 2000.0, "drafter": 4000.0}


def test_stats_requires_login(client):
    assert client.get("/stats").status_code == 401
