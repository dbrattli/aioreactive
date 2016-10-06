import pytest
import asyncio
from asyncio import Future

from aioreactive.testing import VirtualTimeEventLoop
from aioreactive.ops.from_iterable import from_iterable
from aioreactive.ops.map import map
from aioreactive.core import run, listen
from aioreactive.testing import Stream, Listener


class MyException(Exception):
    pass


@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_stream_happy():
    xs = Stream()

    sink = Listener()
    await listen(xs, sink)
    await xs.send_later(1, 10)
    await xs.send_later(1, 20)
    await xs.send_later(1, 30)

    assert sink.values == [
        (1, 10),
        (2, 20),
        (3, 30)
    ]


@pytest.mark.asyncio
async def test_stream_throws():
    ex = MyException("ex")
    xs = Stream()

    sink = Listener()
    with pytest.raises(MyException):
        sub = await listen(xs, sink)
        await xs.send_later(1, 10)
        await xs.send_later(1, 20)
        await xs.send_later(1, 30)
        await xs.throw_later(1, ex)
        await xs.send_later(1, 40)
        await sub

    assert sink.values == [
        (1, 10),
        (2, 20),
        (3, 30),
        (4, ex)
    ]


@pytest.mark.asyncio
async def test_stream_send_after_close():
    xs = Stream()

    sink = Listener()
    await listen(xs, sink)
    await xs.send_later(1, 10)
    await xs.send_later(1, 20)
    await xs.send_later(1, 30)
    await xs.close_later(2)
    await xs.send_later(1, 40)

    assert sink.values == [
        (1, 10),
        (2, 20),
        (3, 30),
        (5,)
    ]


@pytest.mark.asyncio
async def test_stream_subscription_cancel():
    xs = Stream()
    sub = None

    async def mapper(value):
        return value * 10

    ys = map(mapper, xs)

    sink = Listener()
    sub = await listen(ys, sink)
    await xs.send_later(1, 10)
    sub.cancel()
    await xs.send_later(1, 20)

    assert sink.values == [(1, 100)]


@pytest.mark.asyncio
async def test_stream_subscription_cancel_mapper():
    xs = Stream()
    sub = None

    async def send(value):
        sub.cancel()
        await asyncio.sleep(0)

    async def mapper(value):
        return value * 10

    ys = map(mapper, xs)

    sink = Listener(send)
    with await listen(ys, sink) as sub:

        await xs.send_later(1, 10)
        await xs.send_later(1, 20)

    assert sink.values == [(1, 100)]
