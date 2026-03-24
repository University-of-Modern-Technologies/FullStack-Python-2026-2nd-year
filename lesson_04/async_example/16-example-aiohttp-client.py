import aiohttp
import asyncio


class HttpError(Exception):
    pass


async def request(session: aiohttp.ClientSession, url: str):
    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                result = await resp.json()
                return result
            raise HttpError(f"Error status: {resp.status} for {url}")
    except (
        aiohttp.ClientConnectorError,
        aiohttp.InvalidURL,
        aiohttp.ContentTypeError,
    ) as err:
        raise HttpError(f"Connection error: {url}. {err}") from err


async def main():
    timeout = aiohttp.ClientTimeout(total=5)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            response = await request(
                session, "https://api.privatbank.ua/p24api/pubinfo?exchange&coursid=5"
            )
            return response
        except HttpError as err:
            print(err)
            return None


if __name__ == "__main__":
    r = asyncio.run(main())
    print(r)
