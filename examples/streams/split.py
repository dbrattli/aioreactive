"""Example to show how to split a stream into two substreams."""
import asyncio

from expression.core import pipe

import aioreactive as rx


async def main():
    xs = rx.from_iterable(range(10))

    # Split into odds and evens
    evens = pipe(xs, rx.filter(lambda x: x % 2 == 0))
    odds = pipe(xs, rx.filter(lambda x: x % 2 == 1))

    async def mysink(value: int):
        print(value)

    await odds.subscribe_async(rx.AsyncAnonymousObserver(mysink))
    await evens.subscribe_async(rx.AsyncAnonymousObserver(mysink))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
