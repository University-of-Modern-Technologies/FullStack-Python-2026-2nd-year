import asyncio


async def worker(index: int):
    print(f"Start task-{index}")
    await asyncio.sleep(1 + index * 0.2)
    print(f"End task-{index}")
    return index


async def main():
    tasks = [asyncio.create_task(worker(i), name=f"task-{i}") for i in range(5)]

    await asyncio.sleep(0.3)
    tasks[-1].cancel()

    for task in tasks:
        try:
            result = await task
            print(f"Result: {result}")
        except asyncio.CancelledError:
            print(f"{task.get_name()} cancelled")

    print("End program")


if __name__ == "__main__":
    asyncio.run(main())
