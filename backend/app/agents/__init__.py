"""Pick the real or the fake agent client, based on the AGENT_CLIENT setting."""

from app.agents.runner import CallAgent
from app.core.settings import settings


def get_agent_client() -> CallAgent:
    if settings.agent_client == "fake":
        from app.agents.fake_client import fake_call_agent

        return fake_call_agent
    from app.agents.client import call_agent

    return call_agent
