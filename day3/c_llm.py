import asyncio
import time

from openai import AsyncOpenAI

from triage.config import Settings
from triage.loader import load_emails
from triage.models import Email

settings = Settings()
client = AsyncOpenAI(api_key=settings.openai_api_key)


async def classify(email: Email, sem: asyncio.Semaphore) -> tuple[str, str]:
    async with sem:
        r = await client.chat.completions.create(
            model=settings.model_name,
            messages=[
                {
                    "role": "system",
                    "content": "Classify the email with one word: lead, support, spam, or other.",
                },
                {"role": "user", "content": f"Subject: {email.subject}\n\n{email.body}"},
            ],
        )
    return email.subject, (r.choices[0].message.content or "").strip()


async def run(emails: list[Email], limit: int) -> float:
    sem = asyncio.Semaphore(limit)
    start = time.perf_counter()
    await asyncio.gather(*(classify(e, sem) for e in emails))
    return time.perf_counter() - start


async def main() -> None:
    emails = load_emails("data/emails.json") * 10  # 50 calls
    for limit in (1, 5, 20):
        elapsed = await run(emails, limit)
        print(f"limit={limit:<3} total={elapsed:.2f}s")


asyncio.run(main())