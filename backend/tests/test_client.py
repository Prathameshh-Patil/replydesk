"""The real client, with the network replaced: checks what we send and how replies are read."""

import httpx2
import pytest

from app.agents import client
from app.agents.client import AgentCallError, call_agent

OK_BODY = {"choices": [{"message": {"content": '{"ok": true}'}}]}


class FakeResponse:
    def __init__(self, status: int, body, headers: dict | None = None, text: str | None = None):
        self.status_code, self._body = status, body
        self.headers = headers or {}
        self.text = text if text is not None else str(body)

    def json(self):
        return self._body


@pytest.fixture
def no_sleep(monkeypatch):
    slept = []
    monkeypatch.setattr(client.time, "sleep", slept.append)
    return slept


def replies(monkeypatch, *responses):
    queue = list(responses)
    monkeypatch.setattr(client.httpx2, "post", lambda *a, **k: queue.pop(0))
    return queue


def test_sends_instructions_as_system_prompt_and_returns_content(monkeypatch):
    sent = {}

    def fake_post(url, json, headers, timeout):
        sent.update(url=url, json=json)
        return FakeResponse(200, OK_BODY)

    monkeypatch.setattr(client.httpx2, "post", fake_post)
    assert call_agent("sorter", "Subject: hi\nMessage:\nhello") == '{"ok": true}'

    assert sent["url"].endswith("/chat/completions")
    system, user = sent["json"]["messages"]
    assert system["role"] == "system" and system["content"].startswith("You are the Sorter")
    assert user == {"role": "user", "content": "Subject: hi\nMessage:\nhello"}
    assert sent["json"]["temperature"] == 0
    assert sent["json"]["response_format"] == {"type": "json_object"}


def test_rate_limit_waits_as_asked_then_succeeds(monkeypatch, no_sleep):
    gemini_429 = FakeResponse(429, None, text="... Please retry in 23.17s. ...")
    replies(monkeypatch, gemini_429, FakeResponse(200, OK_BODY))
    assert call_agent("sorter", "x") == '{"ok": true}'
    assert no_sleep == [pytest.approx(24.17)]


def test_rate_limit_uses_retry_after_header_and_caps_the_wait(monkeypatch, no_sleep):
    replies(
        monkeypatch,
        FakeResponse(429, None, headers={"retry-after": "500"}),
        FakeResponse(200, OK_BODY),
    )
    call_agent("sorter", "x")
    assert no_sleep == [60]


def test_rate_limit_gives_up_after_two_waits(monkeypatch, no_sleep):
    limited = FakeResponse(429, None, text="slow down")
    replies(monkeypatch, limited, limited, limited)
    with pytest.raises(AgentCallError, match="HTTP 429"):
        call_agent("sorter", "x")
    assert len(no_sleep) == 2


@pytest.mark.parametrize(
    "response",
    [FakeResponse(500, {"error": "server"}), FakeResponse(200, {"unexpected": "shape"})],
)
def test_errors_become_agent_call_error(monkeypatch, no_sleep, response):
    replies(monkeypatch, response)
    with pytest.raises(AgentCallError):
        call_agent("sorter", "x")
    assert no_sleep == []  # only 429 waits; other errors go straight back to the runner


def test_timeout_becomes_agent_call_error(monkeypatch):
    def timeout(*a, **k):
        raise httpx2.ReadTimeout("timed out")

    monkeypatch.setattr(client.httpx2, "post", timeout)
    with pytest.raises(AgentCallError, match="ReadTimeout"):
        call_agent("sorter", "x")
