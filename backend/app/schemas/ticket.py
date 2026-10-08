"""Shapes of ticket data going into and out of the API. FastAPI validates against these."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models import TicketStatus


class TicketCreate(BaseModel):
    """A new customer message (from the form, the API, or one CSV row)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    customer_name: str = Field(min_length=1, max_length=100)
    # A light check (something@something.something); real validation would need email sending.
    customer_email: str = Field(max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=5000)


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_name: str
    customer_email: str
    subject: str
    body: str
    status: TicketStatus
    category: str | None
    urgency: str | None
    extracted: dict[str, Any] | None
    draft_reply: str | None
    checker_ok: bool | None
    checker_problems: list[str] | None
    final_reply: str | None
    edited: bool | None
    reviewed_by: int | None
    created_at: datetime
    reviewed_at: datetime | None


class AgentRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_name: str
    input: str
    output: str | None
    ok: bool
    error: str | None
    duration_ms: int
    created_at: datetime


class TicketDetail(TicketOut):
    agent_runs: list[AgentRunOut]


class ImportRowError(BaseModel):
    row: int  # 1 = first data row after the header
    error: str


class ImportResult(BaseModel):
    created: int
    errors: list[ImportRowError]


class ApproveRequest(BaseModel):
    """Leave final_reply empty to send the draft as it is; fill it in to send an edited reply."""

    final_reply: str | None = Field(default=None, max_length=5000)
