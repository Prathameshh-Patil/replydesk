"""A stand-in for client.call_agent: same signature, canned answers, no network, no cost.

Used by tests and by the demo/Playwright mode (AGENT_CLIENT=fake).
"""

import json

# What each agent answers when a test hasn't scripted anything else.
DEFAULT_REPLIES = {
    "sorter": json.dumps({"category": "other", "urgency": "low", "reason": "Fake sorter answer."}),
    "extractor": json.dumps(
        {"customer_name": None, "order_id": None, "product": None, "request": "fake request"}
    ),
    "drafter": json.dumps({"reply": "Hi there,\n\nThis is a fake draft.\n\nTeam Pixel & Plug"}),
    "checker": json.dumps({"ok": True, "problems": []}),
}


class FakeAgentClient:
    """Call it like call_agent. Script replies per agent:

    FakeAgentClient(sorter=["not json", '{"category": ...}'])
    """

    def __init__(self, **scripted: list[str | Exception]):
        self.scripted = {name: list(replies) for name, replies in scripted.items()}
        self.calls: list[tuple[str, str]] = []  # every (agent_name, message) received

    def __call__(self, agent_name: str, message: str) -> str:
        self.calls.append((agent_name, message))
        queue = self.scripted.get(agent_name)
        reply = queue.pop(0) if queue else DEFAULT_REPLIES[agent_name]
        if isinstance(reply, Exception):
            raise reply
        return reply

    def agents_called(self) -> list[str]:
        return [agent for agent, _ in self.calls]


fake_call_agent = FakeAgentClient()
