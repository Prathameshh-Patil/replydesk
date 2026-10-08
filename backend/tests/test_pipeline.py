"""The four-step pipeline: sort -> extract -> draft -> check, with retries, failures and reruns."""

import json

import pytest

from app.agents.client import AgentCallError
from app.agents.fake_client import FakeAgentClient
from app.agents.prompts import load_instructions
from app.models import AgentRun, Ticket, TicketStatus
from app.pipeline import run_pipeline

SORTED = json.dumps({"category": "billing", "urgency": "high", "reason": "Charged twice."})
EXTRACTED = json.dumps(
    {"customer_name": "Rahul", "order_id": "PP-482913", "product": None, "request": "refund it"}
)
DRAFTED = json.dumps({"reply": "Hi Rahul,\n\nWe've raised it.\n\nTeam Pixel & Plug"})
CHECK_OK = json.dumps({"ok": True, "problems": []})
CHECK_FAIL = json.dumps({"ok": False, "problems": ["Promises a refund (rule 4)."]})
BROKEN = "not json"
ALL_STEPS = ["sorter", "extractor", "drafter", "checker"]


def good(**overrides):
    """A fake client where every agent answers well, unless a test overrides one."""
    replies = {
        "sorter": [SORTED],
        "extractor": [EXTRACTED],
        "drafter": [DRAFTED],
        "checker": [CHECK_OK],
    }
    replies.update(overrides)
    return FakeAgentClient(**replies)


@pytest.fixture
def ticket(db):
    t = Ticket(
        customer_name="Rahul",
        customer_email="rahul@example.com",
        subject="Charged twice",
        body="Order PP-482913 was charged twice. - Rahul",
    )
    db.add(t)
    db.commit()
    return t


def reload(db, ticket):
    db.expire_all()
    return db.get(Ticket, ticket.id)


def runs(db, ticket):
    return db.query(AgentRun).filter_by(ticket_id=ticket.id).order_by(AgentRun.id).all()


# ---- happy path ------------------------------------------------------------------------------


def test_all_four_steps_run_in_order_and_fill_the_ticket(db, ticket):
    fake = good()
    run_pipeline(ticket.id, call_agent=fake)

    t = reload(db, ticket)
    assert t.status == TicketStatus.READY_FOR_REVIEW
    assert (t.category, t.urgency) == ("billing", "high")
    assert t.extracted == {
        "customer_name": "Rahul",
        "order_id": "PP-482913",
        "product": None,
        "request": "refund it",
    }
    assert t.draft_reply.startswith("Hi Rahul")
    assert t.checker_ok is True and t.checker_problems == []
    assert fake.agents_called() == ALL_STEPS
    assert [r.agent_name for r in runs(db, ticket)] == ALL_STEPS
    assert all(r.ok and r.duration_ms >= 0 for r in runs(db, ticket))


def test_each_agent_gets_the_right_input(db, ticket):
    fake = good()
    run_pipeline(ticket.id, call_agent=fake)
    inputs = dict(fake.calls)

    customer = "Subject: Charged twice\nMessage:\nOrder PP-482913 was charged twice. - Rahul"
    assert inputs["sorter"] == customer and inputs["extractor"] == customer
    assert "rahul@example.com" not in "".join(inputs.values())  # never our private data
    assert (
        "Category: billing" in inputs["drafter"] and '"order_id": "PP-482913"' in inputs["drafter"]
    )
    assert customer in inputs["checker"] and "Draft reply:\nHi Rahul" in inputs["checker"]


def test_checker_problems_still_reach_a_human(db, ticket):
    run_pipeline(ticket.id, call_agent=good(checker=[CHECK_FAIL]))
    t = reload(db, ticket)
    assert t.status == TicketStatus.READY_FOR_REVIEW
    assert t.checker_ok is False and t.checker_problems == ["Promises a refund (rule 4)."]


# ---- a failure at each step keeps earlier work -------------------------------------------------


@pytest.mark.parametrize(
    ("failing", "kept", "missing"),
    [
        ("sorter", [], ["category", "extracted", "draft_reply", "checker_ok"]),
        ("extractor", ["category"], ["extracted", "draft_reply", "checker_ok"]),
        ("drafter", ["category", "extracted"], ["draft_reply", "checker_ok"]),
        ("checker", ["category", "extracted", "draft_reply"], ["checker_ok"]),
    ],
)
def test_failure_at_each_step_keeps_earlier_results(db, ticket, failing, kept, missing):
    fake = good(**{failing: [BROKEN, BROKEN]})
    run_pipeline(ticket.id, call_agent=fake)

    t = reload(db, ticket)
    assert t.status == TicketStatus.NEEDS_MANUAL
    assert all(getattr(t, f) is not None for f in kept)
    assert all(getattr(t, f) is None for f in missing)
    # stopped at the failing step: it was tried twice, later steps never ran
    called = fake.agents_called()
    assert called.count(failing) == 2 and called[-1] == failing


@pytest.mark.parametrize("failing", ALL_STEPS)
def test_rerun_continues_from_the_failed_step(db, ticket, failing):
    run_pipeline(ticket.id, call_agent=good(**{failing: [BROKEN, BROKEN]}))
    assert reload(db, ticket).status == TicketStatus.NEEDS_MANUAL

    second = good()
    run_pipeline(ticket.id, call_agent=second)

    assert reload(db, ticket).status == TicketStatus.READY_FOR_REVIEW
    assert second.agents_called() == ALL_STEPS[ALL_STEPS.index(failing) :]


# ---- retries and validation --------------------------------------------------------------------


def test_bad_json_is_retried_once_then_needs_manual(db, ticket):
    fake = FakeAgentClient(sorter=["this is not json", '{"category": "billing"'])
    run_pipeline(ticket.id, call_agent=fake)

    assert reload(db, ticket).status == TicketStatus.NEEDS_MANUAL
    assert fake.agents_called() == ["sorter", "sorter"]  # first try + exactly one retry
    first, second = runs(db, ticket)
    assert not first.ok and first.error.startswith("Invalid output")
    assert not second.ok and second.output == '{"category": "billing"'


def test_bad_then_good_succeeds_and_keeps_failed_attempt(db, ticket):
    run_pipeline(ticket.id, call_agent=good(sorter=["oops", SORTED]))
    assert reload(db, ticket).status == TicketStatus.READY_FOR_REVIEW
    assert [r.ok for r in runs(db, ticket)] == [False, True, True, True, True]


def test_value_outside_allowed_list_is_invalid(db, ticket):
    wrong = json.dumps({"category": "shipping", "urgency": "urgent", "reason": "x"})
    run_pipeline(ticket.id, call_agent=good(sorter=[wrong, wrong]))
    error = runs(db, ticket)[0].error
    assert "category" in error and "urgency" in error


def test_network_error_is_retried_too(db, ticket):
    fake = good(sorter=[AgentCallError("ReadTimeout: timed out"), SORTED])
    run_pipeline(ticket.id, call_agent=fake)
    assert reload(db, ticket).status == TicketStatus.READY_FOR_REVIEW
    assert runs(db, ticket)[0].error == "ReadTimeout: timed out"


def test_json_wrapped_in_code_fences_is_accepted(db, ticket):
    run_pipeline(ticket.id, call_agent=good(sorter=[f"```json\n{SORTED}\n```"]))
    assert reload(db, ticket).category == "billing"


def test_extractor_missing_details_must_be_null_not_absent(db, ticket):
    no_fields = json.dumps({"request": "refund"})
    run_pipeline(ticket.id, call_agent=good(extractor=[no_fields, no_fields]))
    assert "customer_name" in runs(db, ticket)[1].error


def test_invented_order_id_is_dropped_by_code(db, ticket):
    invented = json.dumps(
        {"customer_name": "Rahul", "order_id": "PP-999999", "product": None, "request": "refund"}
    )
    run_pipeline(ticket.id, call_agent=good(extractor=[invented]))

    t = reload(db, ticket)
    assert t.status == TicketStatus.READY_FOR_REVIEW
    assert t.extracted["order_id"] is None and t.extracted["customer_name"] == "Rahul"
    extractor_run = runs(db, ticket)[1]
    assert extractor_run.ok and "PP-999999" in extractor_run.output  # raw output kept for the eval
    assert "Dropped invented order_id" in extractor_run.error


@pytest.mark.parametrize(
    "answer", ['{"ok": true, "problems": ["x"]}', '{"ok": false, "problems": []}']
)
def test_inconsistent_checker_answer_is_invalid(db, ticket, answer):
    run_pipeline(ticket.id, call_agent=good(checker=[answer, answer]))
    assert reload(db, ticket).status == TicketStatus.NEEDS_MANUAL
    assert "problems" in runs(db, ticket)[-1].error


def test_unexpected_crash_marks_needs_manual_not_stuck(db, ticket):
    def broken(agent_name, message):
        raise RuntimeError("bug in our code")

    run_pipeline(ticket.id, call_agent=broken)
    assert reload(db, ticket).status == TicketStatus.NEEDS_MANUAL


# ---- prompts -----------------------------------------------------------------------------------


@pytest.mark.parametrize("agent", ALL_STEPS)
def test_every_agent_prompt_loads_with_examples(agent):
    prompt = load_instructions(agent)
    assert "EXAMPLES" in prompt and "{{GUIDELINES}}" not in prompt


@pytest.mark.parametrize("agent", ["drafter", "checker"])
def test_drafter_and_checker_get_the_guidelines(agent):
    assert "Pixel & Plug: reply guidelines" in load_instructions(agent)


# ---- through the API ---------------------------------------------------------------------------


def test_post_ticket_runs_all_four_agents_in_background(client, auth):
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
    assert detail["draft_reply"] and detail["checker_ok"] is True
    assert [run["agent_name"] for run in detail["agent_runs"]] == ALL_STEPS
    assert all(isinstance(run["duration_ms"], int) for run in detail["agent_runs"])


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


def test_rerun_endpoint(client, auth, db, ticket):
    def rerun():
        return client.post(f"/tickets/{ticket.id}/rerun", headers=auth)

    assert client.post(f"/tickets/{ticket.id}/rerun").status_code == 401
    assert client.post("/tickets/999/rerun", headers=auth).status_code == 404
    assert rerun().status_code == 409  # status "new": agents are already on it

    run_pipeline(ticket.id, call_agent=good(drafter=[BROKEN, BROKEN]))
    r = rerun()  # needs_manual -> continues from the drafter, using the fake client
    assert r.status_code == 202
    t = reload(db, ticket)
    assert t.status == TicketStatus.READY_FOR_REVIEW
    assert t.category == "billing"  # kept from the first run, not the fake's default "other"

    r = rerun()  # ready_for_review -> starts again from the sorter
    assert reload(db, ticket).category == "other"  # the fake client's default answer

    t = reload(db, ticket)
    t.status = TicketStatus.APPROVED
    db.commit()
    assert rerun().status_code == 409
