import pytest
import asyncio
from asyncio import Future

from aioreactive.testing import VirtualTimeEventLoop
from aioreactive.core.sources.from_iterable import from_iterable
from aioreactive.core.sources.map import map
from aioreactive.core import run, start, FuncSink, AsyncStream


@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_map_happy():
    xs = from_iterable([1, 2, 3])  # type: AsyncSource[int]
    values = []

    async def asend(value):
        values.append(value)

    async def mapper(value):
        await asyncio.sleep(0.1)
        return value * 10

    ys = map(mapper, xs)

    result = await run(ys, FuncSink(asend))

    assert result == 30
    assert values == [10, 20, 30]


@pytest.mark.asyncio
async def test_map_mapper_sync():
    xs = from_iterable([1, 2, 3])
    values = []

    async def asend(value):
        values.append(value)

    def mapper(value):
        return value * 10

    ys = map(mapper, xs)

    result = await run(ys, FuncSink(asend))
    assert result == 30
    assert values == [10, 20, 30]


@pytest.mark.asyncio
async def test_map_mapper_throws():
    xs = from_iterable([1])
    exception = None
    error = Exception("ex")

    async def asend(value):
        pass

    async def athrow(ex):
        nonlocal exception
        exception = ex

    async def mapper(x):
        raise error

    ys = map(mapper, xs)

    try:
        await run(ys, FuncSink(asend, athrow))
    except Exception as ex:
        assert ex == error

    assert exception == error


@pytest.mark.asyncio
async def test_map_subscription_cancel():
    xs = AsyncStream()
    result = []
    sub = None

    async def asend(value):
        result.append(value)
        sub.cancel()
        await asyncio.sleep(0)

    async def mapper(value):
        return value * 10

    ys = map(mapper, xs)
    async with start(ys, FuncSink(asend)) as sub:

        await xs.asend(10)
        await asyncio.sleep(0)
        await xs.asend(20)

    assert result == [100]
