import asyncio
from time import sleep


def read_file_sync() -> str:
    with open(__file__, "r", encoding="utf-8") as file:
        sleep(0.5)  # Імітація блокуючої I/O операції
        return file.read(120)


async def main():
    print("Start main")

    file_part_task = asyncio.create_task(asyncio.to_thread(read_file_sync))

    print("Event loop is free while sync code works in threads...")
    file_part = await file_part_task

    print(file_part)
    print("End program")


if __name__ == "__main__":
    asyncio.run(main())
