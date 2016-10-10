import pytest
import asyncio

from aioreactive.testing import VirtualTimeEventLoop
from aioreactive.producer import Producer, ops
from aioreactive.core import run, listen, Stream, Listener


@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_producer_map():
    xs = Producer.from_iterable([1, 2, 3])
    result = []

    async def mapper(value):
        await asyncio.sleep(0.1)
        return value*10

    ys = xs | ops.map(mapper)

    async def send(value):
        result.append(value)

    await run(ys, Listener(send))
    assert result == [10, 20, 30]


@pytest.mark.asyncio
async def test_producer_simple_pipe():
    xs = Producer.from_iterable([1, 2, 3])
    result = []

    async def mapper(value):
        await asyncio.sleep(0.1)
        return value * 10

    async def predicate(value):
        await asyncio.sleep(0.1)
        return value > 1

    ys = xs | ops.filter(predicate) | ops.map(mapper)

    async def send(value):
        result.append(value)

    await run(ys, Listener(send))
    assert result == [20, 30]


@pytest.mark.asyncio
async def test_producer_complex_pipe():
    xs = Producer.from_iterable([1, 2, 3])
    result = []

    async def mapper(value):
        await asyncio.sleep(0.1)
        return value * 10

    async def predicate(value):
        await asyncio.sleep(0.1)
        return value > 1

    async def long_running(value):
        return Producer.from_iterable([value])

    ys = (xs
          | ops.filter(predicate)
          | ops.map(mapper)
          | ops.flat_map(long_running)
          )

    async for value in ys:
        result.append(value)

    assert result == [20, 30]


@pytest.mark.asyncio
async def test_producer_async_iteration():
    xs = Producer.from_iterable([1, 2, 3])
    result = []

    async for x in xs:
        result.append(x)

    assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_producer_async_iteration_inception():
    # iterable to async source to async iterator to async source
    xs = Producer.from_iterable(Producer.from_iterable([1, 2, 3]))
    result = []

    async for x in xs:
        result.append(x)

    assert result == [1, 2, 3]
