import asyncio
import logging

from openai import AsyncOpenAI

from triage.agent import run_agent
from triage.config import Settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpx2").setLevel(logging.WARNING)

s = Settings()
client = AsyncOpenAI(api_key=s.openai_api_key, max_retries=0, timeout=30)

QUESTIONS = [
    "Say hello in one short sentence.",
    "What is the status of order A-1002?",
    "Is john@acme.com a customer, and what is the status of his latest order?",
    "What is the status of order A-9999?",
    "Please cancel order A-1002.",
]


async def main() -> None:
    for q in QUESTIONS:
        print("\nQ:", q)
        print("A:", await run_agent(client, s.model_name, q))


asyncio.run(main())