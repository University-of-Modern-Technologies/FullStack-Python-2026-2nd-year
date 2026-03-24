import asyncio


async def worker(event: asyncio.Event, name: str):
    print(f"{name} waiting")
    await event.wait()
    print(f"{name} working")


async def master(event: asyncio.Event):
    print("Master is working")
    await asyncio.sleep(1.5)
    print("Master set event")
    event.set()


async def main():
    event = asyncio.Event()
    await asyncio.gather(
        worker(event, "worker-1"),
        worker(event, "worker-2"),
        worker(event, "worker-3"),
        master(event),
    )
    print("End program")


if __name__ == "__main__":
    asyncio.run(main())
