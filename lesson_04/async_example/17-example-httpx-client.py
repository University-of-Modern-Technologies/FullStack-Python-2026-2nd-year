import sys
from datetime import datetime, timedelta

import asyncio
import httpx


class HttpError(Exception):
    pass


async def request(client: httpx.AsyncClient, url: str):
    try:
        response = await client.get(url)
        if response.status_code == 200:
            return response.json()
        raise HttpError(f"Error status: {response.status_code} for {url}")
    except (httpx.RequestError, httpx.InvalidURL, ValueError) as err:
        raise HttpError(f"Connection error: {url}. {err}") from err


async def main(index_day: int = 0):
    d = datetime.now() - timedelta(days=index_day)
    shift = d.strftime("%d.%m.%Y")
    url = f"https://api.privatbank.ua/p24api/exchange_rates?date={shift}"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            return await request(client, url)
    except HttpError as err:
        print(err)
        return None


if __name__ == "__main__":
    index_day = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    r = asyncio.run(main(index_day))
    print(r)
