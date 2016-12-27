import pytest
import asyncio
import logging

from aioreactive.testing import VirtualTimeEventLoop
from aioreactive.core import AsyncObservable, run, subscribe, AsyncStream, AnonymousAsyncObserver
from aioreactive.core.operators.pipe import pipe
from aioreactive.core.operators import pipe as op

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_producer_map():
    xs = AsyncObservable.from_iterable([1, 2, 3])
    result = []

    def mapper(value):
        return value * 10

    ys = xs | op.map(mapper)

    async def asend(value):
        result.append(value)

    await run(ys, AnonymousAsyncObserver(asend))
    assert result == [10, 20, 30]


@pytest.mark.asyncio
async def test_producer_simple_pipe():
    xs = AsyncObservable.from_iterable([1, 2, 3])
    result = []

    def mapper(value):
        return value * 10

    async def predicate(value):
        await asyncio.sleep(0.1)
        return value > 1

    ys = xs | op.filter(predicate) | op.map(mapper)

    async def asend(value):
        result.append(value)

    await run(ys, AnonymousAsyncObserver(asend))
    assert result == [20, 30]


@pytest.mark.asyncio
async def test_producer_complex_pipe():
    xs = AsyncObservable.from_iterable([1, 2, 3])
    result = []

    def mapper(value):
        return value * 10

    async def predicate(value):
        await asyncio.sleep(0.1)
        return value > 1

    async def long_running(value):
        return AsyncObservable.from_iterable([value])

    ys = (xs
          | op.filter(predicate)
          | op.map(mapper)
          | op.flat_map(long_running)
          )

    async with subscribe(ys) as stream:
        async for value in stream:
            result.append(value)

    assert result == [20, 30]


@pytest.mark.asyncio
async def test_producer_complex_pipe2():
    xs = AsyncObservable.from_iterable([1, 2, 3])
    result = []

    def mapper(value):
        return value * 10

    async def predicate(value):
        await asyncio.sleep(0.1)
        return value > 1

    async def long_running(value):
        return AsyncObservable.from_iterable([value])

    ys = pipe(xs,
              op.filter(predicate),
              op.map(mapper),
              op.flat_map(long_running)
              )

    async with subscribe(ys) as stream:
        async for value in stream:
            result.append(value)

    assert result == [20, 30]

@pytest.mark.asyncio
async def test_producer_async_iteration():
    xs = AsyncObservable.from_iterable([1, 2, 3])
    result = []

    stream = await subscribe(xs)
    async for x in stream:
        result.append(x)
    stream.cancel()

    assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_producer_async_iteration_aync_with():
    xs = AsyncObservable.from_iterable([1, 2, 3])
    result = []

    async with subscribe(xs) as stream:
        async for x in stream:
            result.append(x)

    assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_producer_async_iteration_inception():
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
    loop.run_until_complete(test_producer_async_iteration_inception())
    loop.close()
