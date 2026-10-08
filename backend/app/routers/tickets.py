import csv
import io

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, UploadFile, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Ticket, TicketStatus, User
from app.pipeline import reset_agent_results, run_pipeline
from app.schemas.ticket import (
    ImportResult,
    ImportRowError,
    TicketCreate,
    TicketDetail,
    TicketOut,
)

router = APIRouter(prefix="/tickets", tags=["tickets"])

MAX_IMPORT_BYTES = 1_000_000
MAX_IMPORT_ROWS = 1000
REQUIRED_COLUMNS = {"customer_name", "customer_email", "subject", "body"}


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(
    data: TicketCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
) -> Ticket:
    """A new customer message. Public: customers don't log in.

    Returns immediately; the agents run in the background after the response is sent.
    """
    ticket = Ticket(**data.model_dump())
    db.add(ticket)
    db.commit()
    background_tasks.add_task(run_pipeline, ticket.id)
    return ticket


@router.post("/import", response_model=ImportResult)
def import_tickets(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    run_agents: bool = True,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ImportResult:
    """Upload a CSV with columns customer_name, customer_email, subject, body.

    Extra columns are ignored. Valid rows are saved; invalid rows are reported, not saved.
    With run_agents=true (default) every imported ticket then goes through the agents, one by one.
    """
    raw = file.file.read(MAX_IMPORT_BYTES + 1)
    if len(raw) > MAX_IMPORT_BYTES:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "File larger than 1 MB")
    try:
        text = raw.decode("utf-8-sig")  # utf-8-sig also handles Excel's invisible BOM marker
    except UnicodeDecodeError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File must be UTF-8 text") from None

    reader = csv.DictReader(io.StringIO(text))
    missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
    if missing:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"Missing columns: {', '.join(sorted(missing))}"
        )

    tickets, errors = [], []
    for row_number, row in enumerate(reader, start=1):
        if row_number > MAX_IMPORT_ROWS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"More than {MAX_IMPORT_ROWS} rows")
        try:
            data = TicketCreate.model_validate({c: row[c] or "" for c in REQUIRED_COLUMNS})
        except ValidationError as e:
            fields = ", ".join(str(err["loc"][0]) for err in e.errors())
            errors.append(ImportRowError(row=row_number, error=f"Invalid: {fields}"))
            continue
        tickets.append(Ticket(**data.model_dump()))

    # One transaction: either all valid rows are saved, or (on a crash) none are.
    db.add_all(tickets)
    db.commit()
    if run_agents:
        for ticket in tickets:
            background_tasks.add_task(run_pipeline, ticket.id)
    return ImportResult(created=len(tickets), errors=errors)


@router.get("", response_model=list[TicketOut])
def list_tickets(
    status: TicketStatus | None = None,
    category: str | None = None,
    urgency: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Ticket]:
    """Newest first, optionally filtered."""
    query = select(Ticket)
    if status:
        query = query.where(Ticket.status == status)
    if category:
        query = query.where(Ticket.category == category)
    if urgency:
        query = query.where(Ticket.urgency == urgency)
    # Rows imported together share the same created_at, so id breaks ties.
    query = query.order_by(Ticket.created_at.desc(), Ticket.id.desc()).limit(limit).offset(offset)
    return list(db.scalars(query))


@router.get("/{ticket_id}", response_model=TicketDetail)
def get_ticket(
    ticket_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> Ticket:
    """One ticket with every agent run (the audit trail)."""
    ticket = db.get(Ticket, ticket_id, options=[selectinload(Ticket.agent_runs)])
    if ticket is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ticket not found")
    return ticket


@router.post("/{ticket_id}/rerun", response_model=TicketOut, status_code=status.HTTP_202_ACCEPTED)
def rerun_ticket(
    ticket_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Ticket:
    """Run the agents again.

    - needs_manual: continue from the step that failed (finished steps are kept).
    - ready_for_review / rejected: start again from the first step.
    """
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ticket not found")
    if ticket.status in (TicketStatus.NEW, TicketStatus.PROCESSING):
        raise HTTPException(status.HTTP_409_CONFLICT, "The agents are already working on it")
    if ticket.status == TicketStatus.APPROVED:
        raise HTTPException(status.HTTP_409_CONFLICT, "Approved tickets can't be rerun")
    if ticket.status in (TicketStatus.READY_FOR_REVIEW, TicketStatus.REJECTED):
        reset_agent_results(ticket)
    ticket.status = TicketStatus.NEW
    db.commit()
    background_tasks.add_task(run_pipeline, ticket.id)
    return ticket
