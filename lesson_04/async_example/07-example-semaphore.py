import asyncio
from random import randint


async def worker(semaphore: asyncio.Semaphore, result: dict, name: str):
    print(f"{name} wait...")
    async with semaphore:
        print(f"Work {name}")
        delay = randint(1, 5)
        result[name] = delay
        await asyncio.sleep(delay / 10)


async def main():
    semaphore = asyncio.Semaphore(3)
    result = {}
    tasks = []
    for i in range(10):
        name = f"task-{i}"
        tasks.append(asyncio.create_task(worker(semaphore, result, name)))

    await asyncio.gather(*tasks)
    print(result)
    print("End program")


if __name__ == "__main__":
    asyncio.run(main())
