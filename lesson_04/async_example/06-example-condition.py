import asyncio


ready = False


async def worker(condition: asyncio.Condition, name: str):
    global ready
    print(f"{name} waiting...")
    async with condition:
        await condition.wait_for(lambda: ready)
        print(f"{name} start working")


async def master(condition: asyncio.Condition):
    global ready
    print("Master work hard")
    await asyncio.sleep(1)
    async with condition:
        ready = True
        print("Master gives permission")
        condition.notify_all()


async def main():
    condition = asyncio.Condition()
    await asyncio.gather(
        worker(condition, "worker-1"),
        worker(condition, "worker-2"),
        master(condition),
    )
    print("End program")


if __name__ == "__main__":
    asyncio.run(main())
