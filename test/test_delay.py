import pytest
import asyncio

from aioreactive.testing import VirtualTimeEventLoop
from aioreactive.ops.delay import delay
from aioreactive.core import listen
from aioreactive.testing import Stream, Listener


@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_delay_done():
    xs = Stream()

    async def mapper(value):
        return value * 10

    ys = delay(0.5, xs)
    lis = Listener()
    sub = await listen(ys, lis)
    await xs.send_later(0, 10)
    await xs.send_later(1, 20)
    await xs.close_later(1)
    await sub

    assert lis.values == [
        (0.5, 10),
        (1.5, 20),
        (2.5,)
    ]


@pytest.mark.asyncio
async def test_delay_cancel_before_done():
    xs = Stream()
    result = []

    async def send(value):
        print("Send: %d" % value)
        nonlocal result
        result.append(value)

    async def mapper(value):
        return value * 10

    ys = delay(0.3, xs)
    with await listen(ys, Listener(send)):
        await xs.send(10)
        await asyncio.sleep(1.5)
        await xs.send(20)

    await asyncio.sleep(1)
    assert result == [10]


@pytest.mark.asyncio
async def test_delay_throw():
    xs = Stream()
    result = []

    async def send(value):
        print("Send: %d" % value)
        nonlocal result
        result.append(value)

    async def mapper(value):
        return value * 10

    ys = delay(0.3, xs)
    await listen(ys, Listener(send))
    await xs.send(10)
    await asyncio.sleep(1.5)
    await xs.send(20)
    await xs.throw(Exception('ex'))
    await asyncio.sleep(1)

    assert result == [10]
