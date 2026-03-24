import asyncio
from random import randint
from time import ctime


async def worker(barrier: asyncio.Barrier, name: str):
    print(f"Start {name}: {ctime()}")
    await asyncio.sleep(randint(1, 3) / 2)
    index = await barrier.wait()
    print(f"Barrier crossed {name}#{index}: {ctime()}")


async def main():
    barrier = asyncio.Barrier(4)
    tasks = [asyncio.create_task(worker(barrier, f"task-{i}")) for i in range(12)]
    await asyncio.gather(*tasks)
    print("End program")


if __name__ == "__main__":
    asyncio.run(main())
