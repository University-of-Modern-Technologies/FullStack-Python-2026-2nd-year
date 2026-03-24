import asyncio
from random import randint


async def worker(name: str):
    delay = randint(1, 5) / 10
    await asyncio.sleep(delay)
    return f"{name} done in {delay:.1f}s"


async def main():
    tasks = [asyncio.create_task(worker(f"task-{i}")) for i in range(6)]
    for done_task in asyncio.as_completed(tasks):
        print(await done_task)

    print("End program")


if __name__ == "__main__":
    asyncio.run(main())
