import asyncio
import logging

from openai import AsyncOpenAI

from triage.config import Settings
from triage.loader import load_emails
from triage.service import triage_many

logging.basicConfig(level=logging.INFO)
s = Settings()
client = AsyncOpenAI(api_key=s.openai_api_key, max_retries=0, timeout=20)
emails = load_emails("data/emails.json")
results = asyncio.run(triage_many(client, s.model_name, emails))
for e, r in zip(emails, results):
    print(e.subject, "->", r)



logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpx2").setLevel(logging.WARNING)