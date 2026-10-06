import asyncio
import logging

from openai import AsyncOpenAI
from pydantic import ValidationError

from triage.models import Email, TriageResult
from triage.retry import with_retries

log = logging.getLogger(__name__)

SYSTEM_PROMPT = "You triage business emails. Fill in the requested fields accurately."


class TriageError(Exception):
    """LLM replied, but we could not get a valid TriageResult."""


async def triage_email(client: AsyncOpenAI, model: str, email: Email) -> TriageResult:
    try:
        r = await with_retries(
            lambda: client.chat.completions.parse(
                model=model,
                response_format=TriageResult,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"From: {email.sender}\nSubject: {email.subject}\n\n{email.body}",
                    },
                ],
            )
        )
    except ValidationError as e:
        log.error("invalid LLM output for %r: %s", email.subject, e)
        raise TriageError(f"invalid output for {email.subject!r}") from e

    msg = r.choices[0].message
    if msg.parsed is None:
        log.error("no parsed output for %r (refusal=%r)", email.subject, msg.refusal)
        raise TriageError(f"no output for {email.subject!r}: {msg.refusal}")
    return msg.parsed


async def triage_many(
    client: AsyncOpenAI, model: str, emails: list[Email], limit: int = 5
) -> list[TriageResult | BaseException]:
    sem = asyncio.Semaphore(limit)

    async def one(email: Email) -> TriageResult:
        async with sem:
            return await triage_email(client, model, email)

    return await asyncio.gather(*(one(e) for e in emails), return_exceptions=True)