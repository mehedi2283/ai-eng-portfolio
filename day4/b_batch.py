import asyncio
import logging
import time

from openai import AsyncOpenAI

from triage.config import Settings
from triage.loader import load_emails
from triage.models import Email
from triage.retry import with_retries

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("batch")

settings = Settings()
client = AsyncOpenAI(api_key=settings.openai_api_key, max_retries=0, timeout=20)


async def classify(email: Email, sem: asyncio.Semaphore) -> tuple[str, str]:
    async with sem:
        r = await with_retries(
            lambda: client.chat.completions.create(
                model=settings.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "Classify the email with one word: lead, support, spam, or other.",
                    },
                    {"role": "user", "content": f"Subject: {email.subject}\n\n{email.body}"},
                ],
            )
        )
    return email.subject, (r.choices[0].message.content or "").strip()


async def main() -> None:
    emails = load_emails("data/emails.json") * 4  # 20 calls
    sem = asyncio.Semaphore(10)
    start = time.perf_counter()
    results = await asyncio.gather(*(classify(e, sem) for e in emails), return_exceptions=True)

    ok = [r for r in results if not isinstance(r, BaseException)]
    failed = [r for r in results if isinstance(r, BaseException)]
    log.info("done in %.2fs: %d ok, %d failed", time.perf_counter() - start, len(ok), len(failed))
    for err in failed:
        log.error("failure: %s: %s", type(err).__name__, err)


asyncio.run(main())