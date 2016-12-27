"""Example to show how to split a stream into two substreams."""
import asyncio

from aioreactive.core import subscribe, AnonymousAsyncObserver

from aioreactive.core import AsyncObservable
from aioreactive.core.operators import pipe as op


async def main():
    xs = AsyncObservable.from_iterable(range(10))

    # Split into odds and evens
    odds = xs | op.filter(lambda x: x % 2 == 1)
    evens = xs | op.filter(lambda x: x % 2 == 0)

    async def mysink(value):
        print(value)

    await subscribe(odds, AnonymousAsyncObserver(mysink))
    await subscribe(evens, AnonymousAsyncObserver(mysink))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
