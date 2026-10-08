"""The ONLY file that knows how to talk to a language model.

Everything else calls `call_agent(agent_name, message) -> str`. To change provider or model,
change this file (or just the LLM_* settings); nothing else in the code base needs to know.

It speaks the OpenAI-compatible chat API. We use Gemini's; Ollama, Groq and others offer the
same API, so switching is a change of LLM_BASE_URL / LLM_MODEL / LLM_API_KEY in .env.
"""

import httpx2

from app.agents.prompts import load_instructions
from app.core.settings import settings


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
    try:
        response = httpx2.post(
            f"{settings.llm_base_url.rstrip('/')}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
            timeout=settings.llm_timeout_seconds,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except httpx2.HTTPStatusError as e:
        raise AgentCallError(f"HTTP {e.response.status_code}: {e.response.text[:200]}") from e
    except httpx2.HTTPError as e:
        raise AgentCallError(f"{type(e).__name__}: {e}") from e
    except (KeyError, IndexError, TypeError, ValueError) as e:
        raise AgentCallError(f"Unexpected response format: {e}") from e
