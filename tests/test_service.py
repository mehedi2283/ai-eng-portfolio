import asyncio
import json

import httpx
import openai
import pytest

from fakes import FakeClient
from triage.models import Email, TriageResult
from triage.service import TriageError, triage_email, triage_many

EMAIL = Email(sender="john@acme.com", subject="Quote", body="Need pricing for 50 units")

GOOD = json.dumps(
    {
        "category": "lead",
        "urgency": "high",
        "summary": "Customer wants pricing for 50 units.",
        "needs_reply": True,
        "confidence": 0.9,
    }
)
BAD_CATEGORY = GOOD.replace('"lead"', '"banana"')


def test_valid_reply_becomes_triage_result():
    client = FakeClient([GOOD])
    result = asyncio.run(triage_email(client, "fake-model", EMAIL))
    assert isinstance(result, TriageResult)
    assert result.category == "lead"
    assert client.calls == 1


@pytest.mark.parametrize("reply", [BAD_CATEGORY, "not json at all"])
def test_invalid_reply_raises_triage_error(reply):
    client = FakeClient([reply])
    with pytest.raises(TriageError):
        asyncio.run(triage_email(client, "fake-model", EMAIL))
    assert client.calls == 1  # bad output is not retried


def test_transient_error_is_retried(monkeypatch):
    async def no_sleep(_):
        pass

    monkeypatch.setattr("triage.retry.asyncio.sleep", no_sleep)
    err = openai.APIConnectionError(request=httpx.Request("POST", "https://x"))
    client = FakeClient([err, err, GOOD])
    result = asyncio.run(triage_email(client, "fake-model", EMAIL))
    assert result.category == "lead"
    assert client.calls == 3


def test_one_bad_reply_does_not_kill_the_batch():
    client = FakeClient([GOOD, "garbage", GOOD])
    results = asyncio.run(triage_many(client, "fake-model", [EMAIL] * 3, limit=1))
    assert isinstance(results[0], TriageResult)
    assert isinstance(results[1], TriageError)
    assert isinstance(results[2], TriageResult)


def test_refusal_raises_triage_error():
    client = FakeClient([{"refusal": "I can't help with that."}])
    with pytest.raises(TriageError):
        asyncio.run(triage_email(client, "fake-model", EMAIL))