import asyncio
import logging

from triage.retry import with_retries

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

calls = 0


async def flaky() -> str:
    global calls
    calls += 1
    if calls < 3:
        raise ConnectionError("boom")
    return "ok"


async def main() -> None:
    print(await with_retries(flaky, retryable=(ConnectionError,), base_delay=0.5))


asyncio.run(main())