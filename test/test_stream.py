import pytest
import asyncio
from asyncio import Future
import logging

from aioreactive.testing import VirtualTimeEventLoop
from aioreactive.operators.from_iterable import from_iterable
from aioreactive.operators.map import map
from aioreactive.core import run, subscribe, chain
from aioreactive.testing import AsyncStream, AnonymousAsyncObserver

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

    sink = AnonymousAsyncObserver()
    await subscribe(xs, sink)
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

    sink = AnonymousAsyncObserver()
    with pytest.raises(MyException):
        sub = await subscribe(xs, sink)
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

    sink = AnonymousAsyncObserver()
    await subscribe(xs, sink)
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
async def test_stream_cancel():
    xs = AsyncStream()
    stream = None

    def mapper(value):
        return value * 10

    ys = map(mapper, xs)

    sink = AnonymousAsyncObserver()
    stream = await subscribe(ys, sink)
    await xs.asend_later(1, 10)
    stream.cancel()
    await xs.asend_later(1, 20)

    assert sink.values == [(1, 100)]


@pytest.mark.asyncio
async def test_stream_cancel_asend():
    xs = AsyncStream()
    stream = None

    async def asend(value):
        stream.cancel()
        await asyncio.sleep(0)

    def mapper(value):
        return value * 10

    ys = map(mapper, xs)

    sink = AnonymousAsyncObserver(asend)
    async with subscribe(ys, sink) as stream:
        await xs.asend_later(1, 10)
        await xs.asend_later(1, 20)

    assert sink.values == [(1, 100)]


@pytest.mark.asyncio
async def test_stream_cancel_mapper():
    xs = AsyncStream()
    stream = None

    def mapper(value):
        stream.cancel()
        return value * 10

    ys = map(mapper, xs)

    sink = AnonymousAsyncObserver()
    async with subscribe(ys, sink) as stream:

        await xs.asend_later(1, 10)
        await xs.asend_later(1, 20)

    assert sink.values == []


@pytest.mark.asyncio
async def test_stream_cancel_context():
    xs = AsyncStream()

    sink = AnonymousAsyncObserver()
    with await subscribe(xs, sink):
        pass

    await xs.asend_later(1, 10)
    await xs.asend_later(1, 20)

    assert sink.values == []


@pytest.mark.asyncio
async def test_stream_chain_observer():
    xs = AsyncStream()

    sink = AnonymousAsyncObserver()
    await chain(xs, sink)

    await xs.asend_later(1, 10)
    await xs.asend_later(1, 20)

    assert sink.values == [
        (1, 10),
        (2, 20)
    ]
