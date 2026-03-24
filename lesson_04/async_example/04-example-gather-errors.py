import asyncio


async def worker(name: str, delay: float):
    await asyncio.sleep(delay)
    return f"{name} done"


async def worker_error(name: str, delay: float):
    await asyncio.sleep(delay)
    raise RuntimeError(f"{name} failed")


async def main():
    results = await asyncio.gather(
        worker("task-1", 0.5),
        worker_error("task-2", 0.2),
        worker("task-3", 0.3),
        return_exceptions=True,
    )
    print(results)
    print("End program")


if __name__ == "__main__":
    asyncio.run(main())
