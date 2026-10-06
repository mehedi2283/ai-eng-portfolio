import asyncio
import logging

from openai import AsyncOpenAI
from pydantic import ValidationError

from triage.models import Email, TriageResult
from triage.retry import with_retries

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You triage business emails. Reply with JSON only, with exactly these keys:
- category: one of "lead", "support", "spam", "other"
- urgency: one of "low", "medium", "high"
- summary: one sentence, max 200 characters
- needs_reply: true or false
- confidence: number from 0 to 1"""


class TriageError(Exception):
    """LLM replied, but the reply was not a valid TriageResult."""


async def triage_email(client: AsyncOpenAI, model: str, email: Email) -> TriageResult:
    r = await with_retries(
        lambda: client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"From: {email.sender}\nSubject: {email.subject}\n\n{email.body}"},
            ],
        )
    )
    content = r.choices[0].message.content or ""
    try:
        return TriageResult.model_validate_json(content)
    except ValidationError as e:
        log.error("invalid LLM output for %r: %s", email.subject, content[:200])
        raise TriageError(f"invalid output for {email.subject!r}") from e


async def triage_many(
    client: AsyncOpenAI, model: str, emails: list[Email], limit: int = 5
) -> list[TriageResult | BaseException]:
    sem = asyncio.Semaphore(limit)

    async def one(email: Email) -> TriageResult:
        async with sem:
            return await triage_email(client, model, email)

    return await asyncio.gather(*(one(e) for e in emails), return_exceptions=True)