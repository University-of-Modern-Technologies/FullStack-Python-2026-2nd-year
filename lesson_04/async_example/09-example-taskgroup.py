import asyncio


async def worker(name: str, delay: float):
    print(f"Start {name}")
    await asyncio.sleep(delay)
    print(f"End {name}")
    return name


async def worker_error(name: str, delay: float):
    print(f"Start {name}")
    await asyncio.sleep(delay)
    raise RuntimeError(f"{name} failed")


async def main():
    try:
        async with asyncio.TaskGroup() as group:
            group.create_task(worker("task-1", 1))
            group.create_task(worker_error("task-2", 1.5))
            group.create_task(worker("task-3", 3))
            group.create_task(worker_error("task-4", 2.5))
    except* RuntimeError as errors:
        for err in errors.exceptions:
            print(f"Caught: {err}")

    print("End program")


if __name__ == "__main__":
    asyncio.run(main())
