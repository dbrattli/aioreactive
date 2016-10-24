import pytest
import asyncio
import logging

from aioreactive.testing import VirtualTimeEventLoop
from aioreactive.core.sources.delay import delay
from aioreactive.core import start
from aioreactive.testing import AsyncStream, FuncSink

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_delay_done():
    xs = AsyncStream()

    async def mapper(value):
        return value * 10

    ys = delay(0.5, xs)
    lis = FuncSink()
    sub = await start(ys, lis)
    await xs.asend_later(0, 10)
    await xs.asend_later(1, 20)
    await xs.aclose_later(1)
    await sub

    assert lis.values == [
        (0.5, 10),
        (1.5, 20),
        (2.5,)
    ]


@pytest.mark.asyncio
async def test_delay_cancel_before_done():
    xs = AsyncStream()
    result = []

    async def asend(value):
        print("Send: %d" % value)
        nonlocal result
        result.append(value)

    async def mapper(value):
        return value * 10

    ys = delay(0.3, xs)
    async with start(ys, FuncSink(asend)):
        await xs.asend(10)
        await asyncio.sleep(1.5)
        await xs.asend(20)

    await asyncio.sleep(1)
    assert result == [10]


@pytest.mark.asyncio
async def test_delay_throw():
    xs = AsyncStream()
    result = []

    async def asend(value):
        print("Send: %d" % value)
        nonlocal result
        result.append(value)

    async def mapper(value):
        return value * 10

    ys = delay(0.3, xs)
    await start(ys, FuncSink(asend))
    await xs.asend(10)
    await asyncio.sleep(1.5)
    await xs.asend(20)
    await xs.athrow(Exception('ex'))
    await asyncio.sleep(1)

    assert result == [10]
