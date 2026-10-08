"""Call one agent, validate its JSON, retry once, and record every attempt in agent_runs."""

import time
from collections.abc import Callable

from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.agents.client import AgentCallError
from app.models import AgentRun

CallAgent = Callable[[str, str], str]  # (agent_name, message) -> reply text
MAX_ATTEMPTS = 2  # the first try plus one retry


def run_agent[T: BaseModel](
    db: Session,
    ticket_id: int,
    agent_name: str,
    message: str,
    schema: type[T],
    call_agent: CallAgent,
) -> T | None:
    """Return the validated output, or None if both attempts failed."""
    for _ in range(MAX_ATTEMPTS):
        started = time.perf_counter()
        reply, result, error = None, None, None
        try:
            reply = call_agent(agent_name, message)
            result = schema.model_validate_json(_strip_code_fences(reply))
        except AgentCallError as e:
            error = str(e)
        except ValidationError as e:
            error = "Invalid output: " + "; ".join(
                f"{'.'.join(map(str, err['loc'])) or 'json'}: {err['msg']}" for err in e.errors()
            )
        db.add(
            AgentRun(
                ticket_id=ticket_id,
                agent_name=agent_name,
                input=message,
                output=reply,
                ok=error is None,
                error=error,
                duration_ms=round((time.perf_counter() - started) * 1000),
            )
        )
        db.commit()  # saved immediately, so the audit trail survives a crash later on
        if result is not None:
            return result
    return None


def _strip_code_fences(text: str) -> str:
    """Models sometimes wrap JSON in ```json ... ```; the content is still the right shape."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.removesuffix("```").strip()
    return text
