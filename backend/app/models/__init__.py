"""Importing the package registers every table with Base.metadata (needed by Alembic)."""

from app.models.agent_run import AgentRun
from app.models.ticket import Ticket, TicketStatus
from app.models.user import User

__all__ = ["AgentRun", "Ticket", "TicketStatus", "User"]
