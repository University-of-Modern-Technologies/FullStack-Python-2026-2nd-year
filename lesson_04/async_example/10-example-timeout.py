import asyncio


async def slow_worker():
    print("Start long operation")
    await asyncio.sleep(2)
    print("Long operation done")


async def main():
    try:
        async with asyncio.timeout(1):
            await slow_worker()
    except TimeoutError:
        print("timeout with asyncio.timeout()")

    try:
        await asyncio.wait_for(slow_worker(), timeout=1)
    except TimeoutError:
        print("timeout with asyncio.wait_for()")

    print("End program")


if __name__ == "__main__":
    asyncio.run(main())
