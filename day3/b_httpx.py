import asyncio
import time

import httpx


async def fetch_title(client: httpx.AsyncClient, post_id: int) -> str:
    r = await client.get(f"https://jsonplaceholder.typicode.com/posts/{post_id}")
    r.raise_for_status()
    return r.json()["title"]


async def main() -> None:
    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=10) as client:
        titles = await asyncio.gather(*(fetch_title(client, i) for i in range(1, 11)))
    for t in titles:
        print("-", t[:60])
    print("10 requests:", round(time.perf_counter() - start, 2), "s")


asyncio.run(main())