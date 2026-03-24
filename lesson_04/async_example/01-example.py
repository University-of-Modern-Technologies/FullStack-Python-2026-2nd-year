import asyncio


async def worker(name: str):
    print(f"Start {name}")
    await asyncio.sleep(1)
    print(f"End {name}")


async def main():
    await worker("task-1")
    await worker("task-2")
    await worker("task-3")
    print("End program")


if __name__ == "__main__":
    asyncio.run(main())
