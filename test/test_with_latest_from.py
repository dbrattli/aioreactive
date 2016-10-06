import pytest
import asyncio

from aioreactive.testing import VirtualTimeEventLoop
from aioreactive.core import listen, run, Listener, Stream
from aioreactive.ops.from_iterable import from_iterable
from aioreactive.ops.with_latest_from import with_latest_from
from aioreactive.ops.never import never
from aioreactive.ops.empty import empty


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

    async def send(value):
        print("test_withlatestfrom_done:send: ", value)
        nonlocal result
        asyncio.sleep(0.1)
        result.append(value)

    zs = with_latest_from(lambda x, y: x + y, ys, xs)

    await listen(zs, Listener(send))
    await asyncio.sleep(1)

    assert result == []


@pytest.mark.asyncio
async def test_withlatestfrom_never_empty():
    xs = empty()
    ys = never()
    result = []

    async def send(value):
        print("test_withlatestfrom_done:send: ", value)
        nonlocal result
        asyncio.sleep(0.1)
        result.append(value)

    zs = with_latest_from(lambda x, y: x + y, ys, xs)

    try:
        await run(zs, Listener(send))
    except asyncio.CancelledError:
        pass
    assert result == []


@pytest.mark.asyncio
async def test_withlatestfrom_done():
    xs = Stream()
    ys = Stream()
    result = []

    async def send(value):
        print("test_withlatestfrom_done:send: ", value)
        nonlocal result
        asyncio.sleep(0.1)
        result.append(value)

    zs = with_latest_from(lambda x, y: x + y, ys, xs)

    sub = await listen(zs, Listener(send))
    await xs.send(1)
    await ys.send(2)
    await xs.send(3)
    await xs.close()
    await sub

    assert result == [5]


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_withlatestfrom_done())
    loop.close()
