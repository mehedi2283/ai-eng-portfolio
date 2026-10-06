import asyncio
import time


async def fake_call(name: str, seconds: float) -> str:
    await asyncio.sleep(seconds)
    return f"{name} done"


async def sequential() -> None:
    start = time.perf_counter()
    for i in range(5):
        await fake_call(f"task{i}", 1)
    print("sequential:", round(time.perf_counter() - start, 2), "s")


async def concurrent() -> None:
    start = time.perf_counter()
    await asyncio.gather(*(fake_call(f"task{i}", 1) for i in range(5)))
    print("gather:", round(time.perf_counter() - start, 2), "s")


asyncio.run(sequential())
asyncio.run(concurrent())