import asyncio

import pytest

from triage.retry import with_retries


def test_retries_then_succeeds():
    calls = {"n": 0}

    async def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError
        return "ok"

    result = asyncio.run(with_retries(flaky, retryable=(ConnectionError,), base_delay=0))
    assert result == "ok"
    assert calls["n"] == 3


def test_gives_up_after_max_attempts():
    calls = {"n": 0}

    async def always_fails() -> str:
        calls["n"] += 1
        raise ConnectionError

    with pytest.raises(ConnectionError):
        asyncio.run(
            with_retries(
                always_fails, retryable=(ConnectionError,), max_attempts=3, base_delay=0
            )
        )
    assert calls["n"] == 3


def test_non_retryable_fails_immediately():
    calls = {"n": 0}

    async def bad() -> str:
        calls["n"] += 1
        raise ValueError

    with pytest.raises(ValueError):
        asyncio.run(with_retries(bad, retryable=(ConnectionError,), base_delay=0))
    assert calls["n"] == 1