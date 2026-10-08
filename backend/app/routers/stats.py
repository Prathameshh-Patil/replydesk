from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import AgentRun, Ticket, TicketStatus, User
from app.schemas.stats import Stats

router = APIRouter(tags=["stats"])

STEP_ORDER = ["sorter", "extractor", "drafter", "checker"]


def _share(part: int, whole: int) -> float | None:
    return round(part / whole, 3) if whole else None


@router.get("/stats", response_model=Stats)
def stats(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Stats:
    """A few numbers that show how the inbox and the agents are doing."""
    by_status = dict(db.execute(select(Ticket.status, func.count()).group_by(Ticket.status)).all())
    by_category = dict(
        db.execute(
            select(Ticket.category, func.count())
            .where(Ticket.category.is_not(None))
            .group_by(Ticket.category)
        ).all()
    )

    # Only approved tickets that had an AI draft count towards draft quality.
    approved_drafts = select(Ticket).where(
        Ticket.status == TicketStatus.APPROVED, Ticket.draft_reply.is_not(None)
    )
    approved = db.scalar(select(func.count()).select_from(approved_drafts.subquery()))
    unedited = db.scalar(
        select(func.count()).select_from(approved_drafts.where(Ticket.edited.is_(False)).subquery())
    )

    checked = db.scalar(select(func.count()).where(Ticket.checker_ok.is_not(None)))
    passed = db.scalar(select(func.count()).where(Ticket.checker_ok.is_(True)))

    averages = dict(
        db.execute(
            select(AgentRun.agent_name, func.avg(AgentRun.duration_ms))
            .where(AgentRun.ok.is_(True))
            .group_by(AgentRun.agent_name)
        ).all()
    )

    return Stats(
        total_tickets=sum(by_status.values()),
        by_status={s.value: by_status.get(s, 0) for s in TicketStatus},
        by_category=by_category,
        approved=approved,
        approved_without_edits=unedited,
        share_approved_without_edits=_share(unedited, approved),
        checked_drafts=checked,
        checker_pass_rate=_share(passed, checked),
        avg_ms_per_step={
            step: round(float(averages[step]), 1) for step in STEP_ORDER if step in averages
        },
    )
