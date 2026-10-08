"""The ONLY file that knows how to talk to a language model.

Everything else calls `call_agent(agent_name, message) -> str`. To change provider or model,
change this file (or just the LLM_* settings); nothing else in the code base needs to know.

It speaks the OpenAI-compatible chat API. We use Gemini's; Ollama, Groq and others offer the
same API, so switching is a change of LLM_BASE_URL / LLM_MODEL / LLM_API_KEY in .env.
"""

import re
import time

import httpx2

from app.agents.prompts import load_instructions
from app.core.settings import settings

RATE_LIMIT_WAITS = 2  # how many times to wait and resend after "429 Too Many Requests"
MAX_WAIT_SECONDS = 60


class AgentCallError(Exception):
    """The model could not be reached or gave no usable answer (network, timeout, HTTP error)."""


def call_agent(agent_name: str, message: str) -> str:
    """Send `message` to the agent defined in agents/<agent_name>.md and return its reply text."""
    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": load_instructions(agent_name)},
            {"role": "user", "content": message},
        ],
        "temperature": 0,  # the same message should get the same answer
        "response_format": {"type": "json_object"},  # JSON mode: the reply must be valid JSON
        "reasoning_effort": settings.llm_reasoning_effort,
    }
    for attempt in range(RATE_LIMIT_WAITS + 1):
        try:
            response = httpx2.post(
                f"{settings.llm_base_url.rstrip('/')}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {settings.llm_api_key}"},
                timeout=settings.llm_timeout_seconds,
            )
        except httpx2.HTTPError as e:
            raise AgentCallError(f"{type(e).__name__}: {e}") from e

        # Rate limited: not the agent's fault, so wait as long as the provider asks and resend.
        # (A bad *answer* is retried by runner.py; this only handles "too many requests".)
        if response.status_code == 429 and attempt < RATE_LIMIT_WAITS:
            time.sleep(_seconds_to_wait(response))
            continue

        if response.status_code >= 400:
            raise AgentCallError(f"HTTP {response.status_code}: {response.text[:200]}")
        try:
            return response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as e:
            raise AgentCallError(f"Unexpected response format: {e}") from e
    raise AssertionError("unreachable")


def _seconds_to_wait(response) -> float:
    """Use the provider's hint (Retry-After header, or Gemini's "retry in 23.1s"), capped."""
    hint = response.headers.get("retry-after")
    if hint is None:
        match = re.search(r"retry in ([\d.]+)s", response.text)
        hint = match.group(1) if match else None
    try:
        seconds = float(hint) if hint is not None else 20.0
    except ValueError:
        seconds = 20.0
    return min(seconds + 1, MAX_WAIT_SECONDS)  # +1s margin so we land after the window resets
