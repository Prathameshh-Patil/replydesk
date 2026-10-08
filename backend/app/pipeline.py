"""The four steps that turn a new ticket into one ready for review, in plain code.

Agents only read and write language. The order of steps, saving, and every rule live here.

    sort -> extract -> draft -> check -> ready_for_review

Each step saves its result on the ticket before the next one starts, so if a step fails, the work
already done is kept, the ticket goes to `needs_manual`, and a rerun continues from that step.
"""

import json
import logging

from sqlalchemy.orm import Session

from app.agents import get_agent_client
from app.agents.runner import CallAgent, run_agent
from app.agents.schemas import CheckerOutput, DrafterOutput, ExtractorOutput, SorterOutput
from app.core.database import SessionLocal
from app.models import AgentRun, Ticket, TicketStatus

log = logging.getLogger(__name__)


class StepFailed(Exception):
    """An agent failed twice; the ticket needs a human."""


# ---- what each agent sees -------------------------------------------------------------------


def customer_message(ticket: Ticket) -> str:
    """Only the subject and body, never our own data about the customer (e.g. their email)."""
    return f"Subject: {ticket.subject}\nMessage:\n{ticket.body}"


def drafter_message(ticket: Ticket) -> str:
    return (
        f"Customer message:\n{customer_message(ticket)}\n\n"
        f"Category: {ticket.category}\n"
        f"Urgency: {ticket.urgency}\n"
        f"Extracted details: {json.dumps(ticket.extracted, ensure_ascii=False)}"
    )


def checker_message(ticket: Ticket) -> str:
    return f"Customer message:\n{customer_message(ticket)}\n\nDraft reply:\n{ticket.draft_reply}"


# ---- the four steps ---------------------------------------------------------------------------


def sort(db: Session, ticket: Ticket, call_agent: CallAgent) -> None:
    result = run_agent(db, ticket.id, "sorter", customer_message(ticket), SorterOutput, call_agent)
    if result is None:
        raise StepFailed("sorter")
    ticket.category, ticket.urgency = result.category, result.urgency


def extract(db: Session, ticket: Ticket, call_agent: CallAgent) -> None:
    message = customer_message(ticket)
    result = run_agent(db, ticket.id, "extractor", message, ExtractorOutput, call_agent)
    if result is None:
        raise StepFailed("extractor")
    details = result.model_dump()
    # Safety net in code: an order ID that isn't written in the message was made up. Drop it,
    # and note it on the agent run so the audit trail (and the eval) still shows it happened.
    order_id = details["order_id"]
    if order_id and order_id.lower() not in message.lower():
        details["order_id"] = None
        last_run = db.query(AgentRun).filter_by(ticket_id=ticket.id).order_by(AgentRun.id.desc())
        last_run.first().error = f"Dropped invented order_id {order_id!r} (not in the message)"
    ticket.extracted = details


def draft(db: Session, ticket: Ticket, call_agent: CallAgent) -> None:
    result = run_agent(db, ticket.id, "drafter", drafter_message(ticket), DrafterOutput, call_agent)
    if result is None:
        raise StepFailed("drafter")
    ticket.draft_reply = result.reply


def check(db: Session, ticket: Ticket, call_agent: CallAgent) -> None:
    result = run_agent(db, ticket.id, "checker", checker_message(ticket), CheckerOutput, call_agent)
    if result is None:
        raise StepFailed("checker")
    ticket.checker_ok, ticket.checker_problems = result.ok, result.problems


# Each step, and the ticket field that shows it is done. The order matters.
STEPS = [
    (sort, "category"),
    (extract, "extracted"),
    (draft, "draft_reply"),
    (check, "checker_ok"),
]


def run_pipeline(ticket_id: int, call_agent: CallAgent | None = None) -> None:
    """Run every step that hasn't been done yet. Runs in the background.

    Never raises: whatever goes wrong, the ticket ends in a clear status, not stuck "processing".
    """
    call_agent = call_agent or get_agent_client()
    with SessionLocal() as db:
        ticket = db.get(Ticket, ticket_id)
        if ticket is None:
            return
        try:
            ticket.status = TicketStatus.PROCESSING
            db.commit()
            for step, done_field in STEPS:
                if getattr(ticket, done_field) is None:  # skip steps a previous run finished
                    step(db, ticket, call_agent)
                    db.commit()  # save this step's result before the next step begins
            ticket.status = TicketStatus.READY_FOR_REVIEW  # even if the Checker found problems
            db.commit()
        except StepFailed:
            db.rollback()
            ticket.status = TicketStatus.NEEDS_MANUAL
            db.commit()
        except Exception:
            log.exception("Pipeline crashed for ticket %s", ticket_id)
            db.rollback()
            ticket.status = TicketStatus.NEEDS_MANUAL
            db.commit()


def reset_agent_results(ticket: Ticket) -> None:
    """Forget every agent result, so the next run starts again from the first step."""
    ticket.category = ticket.urgency = ticket.extracted = None
    ticket.draft_reply = ticket.checker_ok = ticket.checker_problems = None
