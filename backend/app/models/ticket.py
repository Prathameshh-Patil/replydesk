import enum
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# JSONB on PostgreSQL (stored as binary, can be queried); plain JSON elsewhere.
JSONType = JSON().with_variant(JSONB(), "postgresql")


class TicketStatus(enum.StrEnum):
    NEW = "new"  # just arrived, pipeline not started
    PROCESSING = "processing"  # agents are working on it
    READY_FOR_REVIEW = "ready_for_review"  # draft ready, waiting for a human
    NEEDS_MANUAL = "needs_manual"  # an agent failed twice; a human handles it from scratch
    APPROVED = "approved"  # human approved (reply counts as sent)
    REJECTED = "rejected"  # human rejected the draft


class Ticket(Base):
    """One customer message, plus everything the agents and the reviewer added to it."""

    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)

    # What the customer sent
    customer_name: Mapped[str] = mapped_column(String(100))
    customer_email: Mapped[str] = mapped_column(String(254))
    subject: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)

    status: Mapped[TicketStatus] = mapped_column(
        Enum(
            TicketStatus,
            native_enum=False,  # store as text, not a Postgres ENUM type (easier to change)
            create_constraint=True,  # but the database still rejects unknown values
            length=20,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=TicketStatus.NEW,
        index=True,
    )

    # Filled in by the agents (empty until they run)
    category: Mapped[str | None] = mapped_column(String(20), index=True)
    urgency: Mapped[str | None] = mapped_column(String(10), index=True)
    extracted: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    draft_reply: Mapped[str | None] = mapped_column(Text)
    checker_ok: Mapped[bool | None]
    checker_problems: Mapped[list[str] | None] = mapped_column(JSONType)

    # Filled in by the human reviewer
    final_reply: Mapped[str | None] = mapped_column(Text)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    agent_runs: Mapped[list["AgentRun"]] = relationship(  # noqa: F821
        back_populates="ticket", order_by="AgentRun.id", cascade="all, delete-orphan"
    )
