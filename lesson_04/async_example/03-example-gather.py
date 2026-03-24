import asyncio


async def worker(name: str, delay: float):
    print(f"Start {name}")
    await asyncio.sleep(delay)
    print(f"End {name}")
    return name


async def main():
    values = await asyncio.gather(
        worker("task-1", 0.6),
        worker("task-2", 0.2),
        worker("task-3", 0.4),
    )  #  Promise.all
    print(values)
    print("End program")


if __name__ == "__main__":
    asyncio.run(main())
