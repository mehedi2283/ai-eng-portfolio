import asyncio
import logging
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

import openai

log = logging.getLogger(__name__)
T = TypeVar("T")

RETRYABLE: tuple[type[Exception], ...] = (
    openai.RateLimitError,
    openai.APITimeoutError,
    openai.APIConnectionError,
    openai.InternalServerError,
)


async def with_retries(
    fn: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retryable: tuple[type[Exception], ...] = RETRYABLE,
) -> T:
    for attempt in range(1, max_attempts + 1):
        try:
            return await fn()
        except retryable as e:
            if attempt == max_attempts:
                log.error("giving up after %d attempts: %s", attempt, e)
                raise
            delay = random.uniform(0, min(max_delay, base_delay * 2 ** (attempt - 1)))
            log.warning(
                "attempt %d failed (%s); retrying in %.2fs",
                attempt,
                type(e).__name__,
                delay,
            )
            await asyncio.sleep(delay)
    raise RuntimeError("unreachable")