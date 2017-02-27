import pytest
import asyncio
import logging

from aioreactive.testing import VirtualTimeEventLoop
from aioreactive.core import AsyncObservable, run, subscribe, AsyncStream, AsyncAnonymousObserver, AsyncIterableObserver
from aioreactive.operators.pipe import pipe
from aioreactive.operators import pipe as op

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@pytest.yield_fixture()
def event_loop() -> None:
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_async_iteration() -> None:
    xs = AsyncObservable.from_iterable([1, 2, 3])
    result = []

    obv = AsyncIterableObserver()
    async with subscribe(xs, obv):
        async for x in obv:
            result.append(x)

    assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_async_comprehension() -> None:
    xs = AsyncObservable.from_iterable([1, 2, 3])

    obv = AsyncIterableObserver()
    async with subscribe(xs, obv):
        result = [x async for x in obv]

        assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_async_iteration_aync_with() -> None:
    xs = AsyncObservable.from_iterable([1, 2, 3])
    result = []

    obv = AsyncIterableObserver()
    async with subscribe(xs, obv):
        async for x in obv:
            result.append(x)

    assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_async_iteration_inception() -> None:
    # iterable to async source to async iterator to async source
    obv = AsyncIterableObserver()
    await subscribe(AsyncObservable.from_iterable([1, 2, 3]), obv)
    xs = AsyncObservable.from_iterable(obv)
    result = []

    obv = AsyncIterableObserver()
    async with subscribe(xs, obv):
        async for x in obv:
            result.append(x)

    assert result == [1, 2, 3]


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_async_iteration_inception())
    loop.close()
