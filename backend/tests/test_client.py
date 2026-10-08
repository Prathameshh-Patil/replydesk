"""The real client, with the network replaced: checks what we send and how replies are read."""

import httpx2
import pytest

from app.agents import client
from app.agents.client import AgentCallError, call_agent


class FakeResponse:
    def __init__(self, status: int, body):
        self.status_code, self._body = status, body
        self.text = str(body)
        self.request = httpx2.Request("POST", "http://test")

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx2.HTTPStatusError("error", request=self.request, response=self)


def test_sends_instructions_as_system_prompt_and_returns_content(monkeypatch):
    sent = {}

    def fake_post(url, json, headers, timeout):
        sent.update(url=url, json=json)
        return FakeResponse(200, {"choices": [{"message": {"content": '{"ok": true}'}}]})

    monkeypatch.setattr(client.httpx2, "post", fake_post)
    assert call_agent("sorter", "Subject: hi\nMessage:\nhello") == '{"ok": true}'

    assert sent["url"].endswith("/chat/completions")
    system, user = sent["json"]["messages"]
    assert system["role"] == "system" and system["content"].startswith("You are the Sorter")
    assert user == {"role": "user", "content": "Subject: hi\nMessage:\nhello"}
    assert sent["json"]["temperature"] == 0
    assert sent["json"]["response_format"] == {"type": "json_object"}


@pytest.mark.parametrize(
    "response",
    [FakeResponse(429, {"error": "rate limited"}), FakeResponse(200, {"unexpected": "shape"})],
)
def test_errors_become_agent_call_error(monkeypatch, response):
    monkeypatch.setattr(client.httpx2, "post", lambda *a, **k: response)
    with pytest.raises(AgentCallError):
        call_agent("sorter", "x")


def test_timeout_becomes_agent_call_error(monkeypatch):
    def timeout(*a, **k):
        raise httpx2.ReadTimeout("timed out")

    monkeypatch.setattr(client.httpx2, "post", timeout)
    with pytest.raises(AgentCallError, match="ReadTimeout"):
        call_agent("sorter", "x")
