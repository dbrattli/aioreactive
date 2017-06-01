import pytest
import asyncio
from asyncio import Future
import logging

from aioreactive.testing import VirtualTimeEventLoop
from aioreactive.operators.from_iterable import from_iterable
from aioreactive.operators import map
from aioreactive.core import run, subscribe, chain
from aioreactive.testing import AsyncStream, AsyncAnonymousObserver

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
async def test_stream_happy() -> None:
    xs = AsyncStream()

    obv = AsyncAnonymousObserver()
    await subscribe(xs, obv)
    await xs.asend_later(1, 10)
    await xs.asend_later(1, 20)
    await xs.asend_later(1, 30)

    assert obv.values == [
        (1, 10),
        (2, 20),
        (3, 30)
    ]


@pytest.mark.asyncio
async def test_stream_throws() -> None:
    ex = MyException("ex")
    xs = AsyncStream()

    obv = AsyncAnonymousObserver()
    with pytest.raises(MyException):
        await (xs > obv)

        await xs.asend_later(1, 10)
        await xs.asend_later(1, 20)
        await xs.asend_later(1, 30)
        await xs.athrow_later(1, ex)
        await xs.asend_later(1, 40)

        await obv

    assert obv.values == [
        (1, 10),
        (2, 20),
        (3, 30),
        (4, ex)
    ]


@pytest.mark.asyncio
async def test_stream_send_after_close() -> None:
    xs = AsyncStream()

    obv = AsyncAnonymousObserver()
    await subscribe(xs, obv)

    await xs.asend_later(1, 10)
    await xs.asend_later(1, 20)
    await xs.asend_later(1, 30)
    await xs.aclose_later(2)
    await xs.asend_later(1, 40)

    assert obv.values == [
        (1, 10),
        (2, 20),
        (3, 30),
        (5,)
    ]


@pytest.mark.asyncio
async def test_stream_cancel() -> None:
    xs = AsyncStream()
    subscription = None

    def mapper(value) -> int:
        return value * 10

    ys = map(mapper, xs)

    obv = AsyncAnonymousObserver()
    subscription = await subscribe(ys, obv)
    await xs.asend_later(1, 10)
    await subscription.adispose()
    await xs.asend_later(1, 20)

    assert obv.values == [(1, 100)]


@pytest.mark.asyncio
async def test_stream_cancel_asend() -> None:
    xs = AsyncStream()
    subscription = None

    async def asend(value) -> None:
        await subscription.adispose()
        await asyncio.sleep(0)

    def mapper(value) -> int:
        return value * 10

    ys = map(mapper, xs)

    obv = AsyncAnonymousObserver(asend)
    async with subscribe(ys, obv) as sub:
        subscription = sub

        await xs.asend_later(1, 10)
        await xs.asend_later(1, 20)

    assert obv.values == [(1, 100)]


@pytest.mark.asyncio
async def test_stream_cancel_mapper():
    xs = AsyncStream()
    subscription = None

    def mapper(value):
        asyncio.ensure_future(subscription.adispose())
        return value * 10

    ys = map(mapper, xs)

    obv = AsyncAnonymousObserver()
    async with subscribe(ys, obv) as subscription:

        await xs.asend_later(100, 10)
        await xs.asend_later(100, 20)
        await xs.asend_later(100, 30)
        await xs.asend_later(100, 40)
        await xs.asend_later(100, 50)
        await xs.asend_later(100, 60)

    assert obv.values == [(100, 100)]


@pytest.mark.asyncio
async def test_stream_cancel_context():
    xs = AsyncStream()

    obv = AsyncAnonymousObserver()
    async with subscribe(xs, obv):
        pass

    await xs.asend_later(1, 10)
    await xs.asend_later(1, 20)

    assert obv.values == []


@pytest.mark.asyncio
async def test_stream_chain_observer():
    xs = AsyncStream()

    obv = AsyncAnonymousObserver()
    await chain(xs, obv)

    await xs.asend_later(1, 10)
    await xs.asend_later(1, 20)

    assert obv.values == [
        (1, 10),
        (2, 20)
    ]
