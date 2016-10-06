import pytest
import asyncio

from aioreactive.testing import VirtualTimeEventLoop
from aioreactive.ops.from_iterable import from_iterable
from aioreactive.ops.flat_map import flat_map
from aioreactive.core import listen, Listener, Stream


@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_flap_map_done():
    xs = Stream()
    result = []

    async def send(value):
        nonlocal result
        result.append(value)

    async def mapper(value):
        return from_iterable([value])

    ys = flat_map(mapper, xs)
    sub = await listen(ys, Listener(send))
    await xs.send(10)
    await xs.send(20)

    await asyncio.sleep(0.6)

    assert result == [10, 20]
