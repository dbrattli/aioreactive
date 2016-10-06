import pytest
import asyncio

from aioreactive.testing import VirtualTimeEventLoop
from aioreactive.ops.debounce import debounce
from aioreactive.core import listen, Listener, Stream


@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_debounce():
    xs = Stream()
    result = []

    async def send(value):
        print("Send: %d" % value)
        nonlocal result
        result.append(value)

    ys = debounce(0.5, xs)
    sub = await listen(ys, Listener(send))
    await xs.send(1)
    await asyncio.sleep(0.6)
    await xs.send(2)
    await xs.close()
    await asyncio.sleep(0.6)
    await sub

    assert result == [1, 2]


@pytest.mark.asyncio
async def test_debounce_filter():
    xs = Stream()
    result = []

    async def send(value):
        print("Send: %d" % value)
        nonlocal result
        result.append(value)

    ys = debounce(0.5, xs)
    sub = await listen(ys, Listener(send))
    await xs.send(1)
    await asyncio.sleep(0.3)
    await xs.send(2)
    await xs.close()
    await asyncio.sleep(0.6)
    await sub

    assert result == [2]
