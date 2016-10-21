import pytest
import asyncio
from asyncio import Future
import logging

from aioreactive.testing import VirtualTimeEventLoop
from aioreactive.core.sources.from_iterable import from_iterable
from aioreactive.core.sources.map import map
from aioreactive.core import run, start
from aioreactive.testing import AsyncStream, FuncSink

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class MyException(Exception):
    pass


@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_stream_happy():
    xs = AsyncStream()

    sink = FuncSink()
    await start(xs, sink)
    await xs.asend_later(1, 10)
    await xs.asend_later(1, 20)
    await xs.asend_later(1, 30)

    assert sink.values == [
        (1, 10),
        (2, 20),
        (3, 30)
    ]


@pytest.mark.asyncio
async def test_stream_throws():
    ex = MyException("ex")
    xs = AsyncStream()

    sink = FuncSink()
    with pytest.raises(MyException):
        sub = await start(xs, sink)
        await xs.asend_later(1, 10)
        await xs.asend_later(1, 20)
        await xs.asend_later(1, 30)
        await xs.athrow_later(1, ex)
        await xs.asend_later(1, 40)
        await sub

    assert sink.values == [
        (1, 10),
        (2, 20),
        (3, 30),
        (4, ex)
    ]


@pytest.mark.asyncio
async def test_stream_send_after_close():
    xs = AsyncStream()

    sink = FuncSink()
    await start(xs, sink)
    await xs.asend_later(1, 10)
    await xs.asend_later(1, 20)
    await xs.asend_later(1, 30)
    await xs.aclose_later(2)
    await xs.asend_later(1, 40)

    assert sink.values == [
        (1, 10),
        (2, 20),
        (3, 30),
        (5,)
    ]


@pytest.mark.asyncio
async def test_stream_subscription_cancel():
    xs = AsyncStream()
    sub = None

    async def mapper(value):
        return value * 10

    ys = map(mapper, xs)

    sink = FuncSink()
    sub = await start(ys, sink)
    await xs.asend_later(1, 10)
    sub.cancel()
    await xs.asend_later(1, 20)

    assert sink.values == [(1, 100)]


@pytest.mark.asyncio
async def test_stream_subscription_cancel_mapper():
    xs = AsyncStream()
    sub = None

    async def asend(value):
        sub.cancel()
        await asyncio.sleep(0)

    async def mapper(value):
        return value * 10

    ys = map(mapper, xs)

    sink = FuncSink(asend)
    async with start(ys, sink) as sub:

        await xs.asend_later(1, 10)
        await xs.asend_later(1, 20)

    assert sink.values == [(1, 100)]
