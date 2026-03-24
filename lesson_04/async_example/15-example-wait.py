import asyncio
from concurrent.futures import ThreadPoolExecutor

import requests
from requests.exceptions import RequestException

from timing import async_timed

urls = [
    "https://github.com",
    "https://www.codewars.com",
    "https://rezka.cc/",
    "https://hltv.org/",
    "https://app.amplitude.com/",
    "https://www.youtube.com/",
    "https://tabletki.ua",
    "asdf",
    "ws://test.com",
    "https://stackoverflow.com/",
]


def get_preview(url: str) -> tuple[str, str] | None:
    try:
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        return url, res.text[:25]
    except RequestException:
        return (url, None)


async def run_wait(return_when) -> list[tuple[str, str] | None]:
    loop = asyncio.get_running_loop()

    with ThreadPoolExecutor(10) as pool:
        futures = [loop.run_in_executor(pool, get_preview, url) for url in urls]
        done, pending = await asyncio.wait(futures, return_when=return_when)
        print("\n--------------------------------")
        print(f"Return when: {return_when}")
        print("--------------------------------")
        print(f"Done: {len(done)}")
        print(f"Pending: {len(pending)}")

        if pending:
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
        return [task.result() for task in done]


@async_timed()
async def main_all_completed():
    return await run_wait(asyncio.ALL_COMPLETED)


@async_timed()
async def main_first_completed():
    return await run_wait(asyncio.FIRST_COMPLETED)


if __name__ == "__main__":
    all_result: list = asyncio.run(main_all_completed())
    print(all_result)

    first_result: list = asyncio.run(main_first_completed())
    print(first_result)
