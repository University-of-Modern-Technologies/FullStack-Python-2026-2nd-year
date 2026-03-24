import asyncio

from faker import Faker

from timing import async_timed

fake = Faker("uk-UA")  # en-GB

# Awaitable -> Coroutine
# Awaitable -> Future -> Task

"""
Awaitable
├── Coroutine
└── Future
    └── Task
"""


async def async_get_user_from_db(uuid: int, future: asyncio.Future):
    try:
        await asyncio.sleep(0.5)
        if not future.done():
            future.set_result(
                {"id": uuid, "username": fake.user_name(), "email": fake.email()}
            )
    except Exception as e:
        if not future.done():
            future.set_exception(e)


def make_request(uuid: int) -> asyncio.Future:
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    asyncio.create_task(async_get_user_from_db(uuid, future))
    return future


@async_timed("Перевірка future")
async def main():
    users = []
    for i in range(1, 6):
        users.append(make_request(i))

    print([user.done() for user in users])
    result = await asyncio.gather(*users)
    print([user.done() for user in users])
    return result


if __name__ == "__main__":
    users = asyncio.run(main())
    print(users)
