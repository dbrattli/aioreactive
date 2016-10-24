import logging
import pytest
import asyncio

from aioreactive.testing import VirtualTimeEventLoop
from aioreactive.core import AsyncStream, run, FuncSink, start
from aioreactive.core.sources.from_iterable import from_iterable
from aioreactive.core.sources.with_latest_from import with_latest_from
from aioreactive.core.sources.never import never
from aioreactive.core.sources.empty import empty

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_withlatestfrom_never_never():
    xs = never()
    ys = never()
    result = []

    async def asend(value):
        nonlocal result
        asyncio.sleep(0.1)
        result.append(value)

    zs = with_latest_from(lambda x, y: x + y, ys, xs)

    await start(zs, FuncSink(asend))
    await asyncio.sleep(1)

    assert result == []


@pytest.mark.asyncio
async def test_withlatestfrom_never_empty():
    xs = empty()
    ys = never()
    result = []

    async def asend(value):
        log.debug("test_withlatestfrom_never_empty:asend(%s)", value)
        nonlocal result
        asyncio.sleep(0.1)
        result.append(value)

    zs = with_latest_from(lambda x, y: x + y, ys, xs)

    try:
        await run(zs, FuncSink(asend))
    except asyncio.CancelledError:
        pass
    assert result == []


@pytest.mark.asyncio
async def test_withlatestfrom_done():
    xs = AsyncStream()
    ys = AsyncStream()
    result = []

    async def asend(value):
        log.debug("test_withlatestfrom_done:asend(%s)", value)
        nonlocal result
        asyncio.sleep(0.1)
        result.append(value)

    zs = with_latest_from(lambda x, y: x + y, ys, xs)

    sub = await start(zs, FuncSink(asend))
    await xs.asend(1)
    await ys.asend(2)
    await xs.asend(3)
    await xs.aclose()
    await sub

    assert result == [5]


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_withlatestfrom_done())
    loop.close()
