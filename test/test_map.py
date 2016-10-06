import pytest
import asyncio
from asyncio import Future

from aioreactive.testing import VirtualTimeEventLoop
from aioreactive.ops.from_iterable import from_iterable
from aioreactive.ops.map import map
from aioreactive.core import run, listen, Listener, Stream


@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_map_happy():
    xs = from_iterable([1, 2, 3])
    values = []

    async def send(value):
        values.append(value)

    async def mapper(value):
        await asyncio.sleep(0.1)
        return value * 10

    ys = map(mapper, xs)

    result = await run(ys, Listener(send))

    assert result == 30
    assert values == [10, 20, 30]


@pytest.mark.asyncio
async def test_map_mapper_sync():
    xs = from_iterable([1, 2, 3])
    values = []

    async def send(value):
        values.append(value)

    def mapper(value):
        return value*10

    ys = map(mapper, xs)

    result = await run(ys, Listener(send))
    assert result == 30
    assert values == [10, 20, 30]


@pytest.mark.asyncio
async def test_map_mapper_throws():
    xs = from_iterable([1])
    exception = None
    error = Exception("ex")

    async def send(value):
        pass

    async def throw(ex):
        nonlocal exception
        exception = ex

    async def mapper(x):
        raise error

    ys = map(mapper, xs)

    try:
        await run(ys, Listener(send, throw))
    except Exception as ex:
        assert ex == error

    assert exception == error


@pytest.mark.asyncio
async def test_map_subscription_cancel():
    xs = Stream()
    result = []
    sub = None

    async def send(value):
        result.append(value)
        sub.cancel()
        await asyncio.sleep(0)

    async def mapper(value):
        return value*10

    ys = map(mapper, xs)
    with await listen(ys, Listener(send)) as sub:

        await xs.send(10)
        await asyncio.sleep(0)
        await xs.send(20)

    assert result == [100]
