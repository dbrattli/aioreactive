import pytest
import asyncio
import logging

from aioreactive.testing import VirtualTimeEventLoop
from aioreactive.core import subscribe, AsyncAnonymousObserver, AsyncStream
from aioreactive.operators import debounce

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_debounce():
    xs = AsyncStream()
    result = []

    async def asend(value):
        log.debug("test_debounce:asend(%s)", value)
        nonlocal result
        result.append(value)

    ys = debounce(0.5, xs)

    obv = AsyncAnonymousObserver(asend)
    sub = await subscribe(ys, obv)
    await xs.asend(1)
    await asyncio.sleep(0.6)
    await xs.asend(2)
    await xs.aclose()
    await asyncio.sleep(0.6)
    await obv

    assert result == [1, 2]


@pytest.mark.asyncio
async def test_debounce_filter():
    xs = AsyncStream()
    result = []

    async def asend(value):
        log.debug("test_debounce_filter:asend(%s)", value)
        nonlocal result
        result.append(value)

    ys = debounce(0.5, xs)
    obv = AsyncAnonymousObserver(asend)
    sub = await subscribe(ys, obv)
    await xs.asend(1)
    await asyncio.sleep(0.3)
    await xs.asend(2)
    await xs.aclose()
    await asyncio.sleep(0.6)
    await obv

    assert result == [2]
