import pytest
import asyncio
import logging

from aioreactive.testing import VirtualTimeEventLoop
from aioreactive.core import subscribe
from aioreactive.operators import delay
from aioreactive.testing import AsyncStream, AsyncAnonymousObserver

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

    ys = delay(0.5, xs)
    obv = AsyncAnonymousObserver()
    async with subscribe(ys, obv):
        await xs.asend_later(0, 10)
        await xs.asend_later(1, 20)
        await xs.aclose_later(1)
        await obv

    assert obv.values == [
        (0.5, 10),
        (1.5, 20),
        (2.5,)
    ]


@pytest.mark.asyncio
async def test_delay_cancel_before_done():
    xs = AsyncStream()
    result = []

    async def asend(value):
        nonlocal result
        result.append(value)

    ys = delay(0.3, xs)
    async with subscribe(ys, AsyncAnonymousObserver(asend)):
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
        nonlocal result
        result.append(value)

    ys = delay(0.3, xs)
    await subscribe(ys, AsyncAnonymousObserver(asend))
    await xs.asend(10)
    await asyncio.sleep(1.5)
    await xs.asend(20)
    await xs.athrow(Exception('ex'))
    await asyncio.sleep(1)

    assert result == [10]
