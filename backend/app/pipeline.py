"""The steps that turn a new ticket into one ready for review, in plain code.

Agents only read and write language. The order of steps, saving, and every rule live here.
Phase 4: only the Sorter. Phase 5 adds Extractor, Drafter and Checker.
"""

import logging

from app.agents import get_agent_client
from app.agents.runner import CallAgent, run_agent
from app.agents.schemas import SorterOutput
from app.core.database import SessionLocal
from app.models import Ticket, TicketStatus

log = logging.getLogger(__name__)


def customer_message(ticket: Ticket) -> str:
    """What the agents see: only the subject and body, never our own data about the customer."""
    return f"Subject: {ticket.subject}\nMessage:\n{ticket.body}"


def run_pipeline(ticket_id: int, call_agent: CallAgent | None = None) -> None:
    """Runs in the background after a ticket is created.

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

            # Step 1: sort
            sorted_ = run_agent(
                db, ticket.id, "sorter", customer_message(ticket), SorterOutput, call_agent
            )
            if sorted_ is None:
                ticket.status = TicketStatus.NEEDS_MANUAL
                db.commit()
                return
            ticket.category, ticket.urgency = sorted_.category, sorted_.urgency
            # Until Phase 5 adds the other steps, a sorted ticket is ready for a human.
            ticket.status = TicketStatus.READY_FOR_REVIEW
            db.commit()
        except Exception:
            log.exception("Pipeline crashed for ticket %s", ticket_id)
            db.rollback()
            ticket.status = TicketStatus.NEEDS_MANUAL
            db.commit()
