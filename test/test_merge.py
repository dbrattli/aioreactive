import pytest
import asyncio

from aioreactive.core import listen
from aioreactive.ops.from_iterable import from_iterable
from aioreactive.ops.merge import merge
from aioreactive.testing import Stream, VirtualTimeEventLoop, Listener


@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_merge_done():
    xs = Stream()

    ys = merge(xs)

    sink = Listener()
    sub = await listen(ys, sink)
    await xs.send(from_iterable([10]))
    await xs.send(from_iterable([20]))
    await xs.close()
    await sub

    assert sink.values == [
        (0, 10),
        (0, 20),
        (0,)
    ]

@pytest.mark.asyncio
async def test_merge_streams():
    xs = Stream()
    s1 = Stream()
    s2 = Stream()

    ys = merge(xs)

    sink = Listener()
    sub = await listen(ys, sink)
    await xs.send(s1)
    await xs.send(s2)

    await s1.send_at(1, 10)
    await s1.send_at(2, 20)
    await s1.send_at(4, 30)
    await s1.close_at(6)

    await s2.send_at(0, 40)
    await s2.send_at(3, 50)
    await s2.send_at(5, 60)
    await s2.close_at(6)

    await xs.close()
    await sub

    assert sink.values == [
        (0, 40),
        (1, 10),
        (2, 20),
        (3, 50),
        (4, 30),
        (5, 60),
        (6,)
    ]


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_merge_streams())
    loop.close()
