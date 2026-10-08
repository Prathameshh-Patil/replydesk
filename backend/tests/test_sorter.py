"""The Sorter path: pipeline -> runner -> (fake) client -> validated output -> database."""

import json

import pytest

from app.agents.client import AgentCallError
from app.agents.fake_client import FakeAgentClient
from app.models import AgentRun, Ticket, TicketStatus
from app.pipeline import run_pipeline

GOOD = json.dumps({"category": "billing", "urgency": "high", "reason": "Charged twice."})


@pytest.fixture
def ticket(db):
    t = Ticket(
        customer_name="Rahul",
        customer_email="rahul@example.com",
        subject="Charged twice",
        body="Order PP-482913 was charged twice.",
    )
    db.add(t)
    db.commit()
    return t


def reload(db, ticket):
    db.expire_all()
    return db.get(Ticket, ticket.id)


def runs(db, ticket):
    return db.query(AgentRun).filter_by(ticket_id=ticket.id).order_by(AgentRun.id).all()


def test_good_answer_sets_category_and_urgency(db, ticket):
    fake = FakeAgentClient(sorter=[GOOD])
    run_pipeline(ticket.id, call_agent=fake)

    t = reload(db, ticket)
    assert (t.category, t.urgency, t.status) == ("billing", "high", TicketStatus.READY_FOR_REVIEW)
    [run] = runs(db, ticket)
    assert run.agent_name == "sorter" and run.ok and run.error is None
    assert run.output == GOOD and run.duration_ms >= 0


def test_agent_sees_only_subject_and_body(db, ticket):
    fake = FakeAgentClient(sorter=[GOOD])
    run_pipeline(ticket.id, call_agent=fake)
    [(agent, message)] = fake.calls
    assert message == "Subject: Charged twice\nMessage:\nOrder PP-482913 was charged twice."
    assert "rahul@example.com" not in message


def test_bad_json_is_retried_once_then_needs_manual(db, ticket):
    fake = FakeAgentClient(sorter=["this is not json", '{"category": "billing"'])
    run_pipeline(ticket.id, call_agent=fake)

    t = reload(db, ticket)
    assert t.status == TicketStatus.NEEDS_MANUAL
    assert t.category is None
    assert len(fake.calls) == 2  # first try + exactly one retry
    first, second = runs(db, ticket)
    assert not first.ok and first.error.startswith("Invalid output")
    assert not second.ok and second.output == '{"category": "billing"'


def test_bad_then_good_succeeds_and_keeps_failed_attempt(db, ticket):
    fake = FakeAgentClient(sorter=["oops", GOOD])
    run_pipeline(ticket.id, call_agent=fake)

    assert reload(db, ticket).status == TicketStatus.READY_FOR_REVIEW
    assert [r.ok for r in runs(db, ticket)] == [False, True]


def test_value_outside_allowed_list_is_invalid(db, ticket):
    wrong = json.dumps({"category": "shipping", "urgency": "urgent", "reason": "x"})
    run_pipeline(ticket.id, call_agent=FakeAgentClient(sorter=[wrong, wrong]))

    assert reload(db, ticket).status == TicketStatus.NEEDS_MANUAL
    error = runs(db, ticket)[0].error
    assert "category" in error and "urgency" in error


def test_missing_field_is_invalid(db, ticket):
    no_reason = json.dumps({"category": "billing", "urgency": "high"})
    run_pipeline(ticket.id, call_agent=FakeAgentClient(sorter=[no_reason, no_reason]))
    assert "reason" in runs(db, ticket)[0].error


def test_network_error_is_retried_too(db, ticket):
    fake = FakeAgentClient(sorter=[AgentCallError("ReadTimeout: timed out"), GOOD])
    run_pipeline(ticket.id, call_agent=fake)

    assert reload(db, ticket).status == TicketStatus.READY_FOR_REVIEW
    first, _ = runs(db, ticket)
    assert first.output is None and first.error == "ReadTimeout: timed out"


def test_json_wrapped_in_code_fences_is_accepted(db, ticket):
    run_pipeline(ticket.id, call_agent=FakeAgentClient(sorter=[f"```json\n{GOOD}\n```"]))
    assert reload(db, ticket).category == "billing"


def test_unexpected_crash_marks_needs_manual_not_stuck(db, ticket):
    def broken(agent_name, message):
        raise RuntimeError("bug in our code")

    run_pipeline(ticket.id, call_agent=broken)
    assert reload(db, ticket).status == TicketStatus.NEEDS_MANUAL


def test_post_ticket_runs_sorter_in_background(client, auth):
    """End to end through the API, using the fake client (AGENT_CLIENT=fake in conftest)."""
    r = client.post(
        "/tickets",
        json={
            "customer_name": "A",
            "customer_email": "a@example.com",
            "subject": "Hi",
            "body": "Where is my order?",
        },
    )
    assert r.status_code == 201
    assert r.json()["status"] == "new"  # the response is sent before the agents run

    detail = client.get(f"/tickets/{r.json()['id']}", headers=auth).json()
    assert detail["status"] == "ready_for_review"
    assert detail["category"] == "other" and detail["urgency"] == "low"  # fake's default answer
    assert [run["agent_name"] for run in detail["agent_runs"]] == ["sorter"]


def test_import_can_skip_agents(client, auth):
    csv = b"customer_name,customer_email,subject,body\nA,a@example.com,S,B\n"
    client.post(
        "/tickets/import",
        params={"run_agents": "false"},
        files={"file": ("t.csv", csv, "text/csv")},
        headers=auth,
    )
    [t] = client.get("/tickets", headers=auth).json()
    assert t["status"] == "new"
