import pytest
import asyncio
import logging

from aioreactive.testing import VirtualTimeEventLoop
from aioreactive.core import AsyncObservable, run, subscribe, AsyncStream, AnonymousAsyncObserver
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

    stream = await subscribe(xs)
    async for x in stream:
        result.append(x)
    stream.cancel()

    assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_async_comprehension() -> None:
    xs = AsyncObservable.from_iterable([1, 2, 3])

    async with subscribe(xs) as stream:
        result = [x async for x in stream]

        assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_async_iteration_aync_with() -> None:
    xs = AsyncObservable.from_iterable([1, 2, 3])
    result = []

    async with subscribe(xs) as stream:
        async for x in stream:
            result.append(x)

    assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_async_iteration_inception() -> None:
    # iterable to async source to async iterator to async source
    ys = await subscribe(AsyncObservable.from_iterable([1, 2, 3]))
    xs = AsyncObservable.from_iterable(ys)
    result = []

    async with subscribe(xs) as stream:
        async for x in stream:
            result.append(x)

    assert result == [1, 2, 3]


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_async_iteration_inception())
    loop.close()
