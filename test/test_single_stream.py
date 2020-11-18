import asyncio
import logging
from typing import Optional

import aioreactive as rx
import pytest
from aioreactive.notification import OnCompleted, OnError, OnNext
from aioreactive.testing import AsyncTestObserver, AsyncTestSingleSubject, VirtualTimeEventLoop
from aioreactive.types import AsyncObserver
from expression.core import pipe
from expression.system import AsyncDisposable, ObjectDisposedException

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class MyException(Exception):
    pass


@pytest.yield_fixture()  # type: ignore
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_stream_happy():
    xs: AsyncTestSingleSubject[int] = AsyncTestSingleSubject()

    sink = AsyncTestObserver()
    await xs.subscribe_async(sink)
    await xs.asend_later(1, 10)
    await xs.asend_later(1, 20)
    await xs.asend_later(1, 30)

    assert sink.values == [(1, OnNext(10)), (2, OnNext(20)), (3, OnNext(30))]


@pytest.mark.asyncio
async def test_stream_throws():
    ex = MyException("ex")
    xs: AsyncTestSingleSubject[int] = AsyncTestSingleSubject()

    sink = AsyncTestObserver()
    with pytest.raises(MyException):
        await xs.subscribe_async(sink)
        await xs.asend_later(1, 10)
        await xs.asend_later(1, 20)
        await xs.asend_later(1, 30)
        await xs.athrow_later(1, ex)
        await xs.asend_later(1, 40)
        await sink

    assert sink.values == [(1, OnNext(10)), (2, OnNext(20)), (3, OnNext(30)), (4, OnError(ex))]


@pytest.mark.asyncio
async def test_stream_send_after_close():
    xs: AsyncTestSingleSubject[int] = AsyncTestSingleSubject()

    sink = AsyncTestObserver()
    await xs.subscribe_async(sink)
    await xs.asend_later(1, 10)
    await xs.asend_later(1, 20)
    await xs.asend_later(1, 30)
    await xs.aclose_later(2)
    await xs.asend_later(1, 40)

    assert sink.values == [(1, OnNext(10)), (2, OnNext(20)), (3, OnNext(30)), (5, OnCompleted)]


@pytest.mark.asyncio
async def test_stream_cancel():
    xs: AsyncTestSingleSubject[int] = AsyncTestSingleSubject()
    sub = None

    def mapper(value: int) -> int:
        return value * 10

    ys = pipe(xs, rx.map(mapper))

    sink = AsyncTestObserver()
    sub = await ys.subscribe_async(sink)
    await xs.asend_later(1, 10)
    await sub.dispose_async()

    with pytest.raises(ObjectDisposedException):
        await xs.asend_later(1, 20)

    assert sink.values == [(1, OnNext(100))]


@pytest.mark.asyncio
async def test_stream_cancel_asend():
    xs: AsyncTestSingleSubject[int] = AsyncTestSingleSubject()
    sub: Optional[AsyncDisposable] = None

    async def asend(value: int) -> None:
        assert sub is not None
        await sub.dispose_async()
        await asyncio.sleep(0)

    def mapper(value: int) -> int:
        return value * 10

    ys = pipe(xs, rx.map(mapper))

    sink = AsyncTestObserver(asend)
    async with await ys.subscribe_async(sink) as sub:

        await xs.asend_later(1, 10)

        with pytest.raises(ObjectDisposedException):
            await xs.asend_later(1, 20)

    assert sink.values == [(1, OnNext(100))]


@pytest.mark.asyncio
async def test_stream_cancel_mapper():
    xs: AsyncTestSingleSubject[int] = AsyncTestSingleSubject()
    sub: Optional[AsyncDisposable] = None

    async def mapper(value: int) -> int:
        assert sub is not None
        await sub.dispose_async()

        await asyncio.sleep(0)
        return value * 10

    ys = pipe(xs, rx.map_async(mapper))

    sink: AsyncObserver[int] = AsyncTestObserver()
    async with await ys.subscribe_async(sink) as sub:

        await xs.asend_later(1, 10)
        with pytest.raises(ObjectDisposedException):
            await xs.asend_later(1, 20)

    assert sink.values == [(1, OnNext(100))]


@pytest.mark.asyncio
async def test_stream_cancel_context():
    xs: AsyncTestSingleSubject[int] = AsyncTestSingleSubject()

    sink = AsyncTestObserver()
    async with await xs.subscribe_async(sink):
        pass

    with pytest.raises(ObjectDisposedException):
        await xs.asend_later(1, 10)
        await xs.asend_later(1, 20)

    assert sink.values == []


@pytest.mark.asyncio
async def test_stream_cold_send():
    xs: AsyncTestSingleSubject[int] = AsyncTestSingleSubject()

    sink = AsyncTestObserver()

    async def asend(value: int) -> None:
        await xs.asend(value)

    asyncio.ensure_future(asend(42))
    await asyncio.sleep(10)

    async with await xs.subscribe_async(sink):
        await xs.asend_later(1, 20)

    assert sink.values == [(10, OnNext(42)), (11, OnNext(20))]


@pytest.mark.asyncio
async def test_stream_cold_throw():
    xs: AsyncTestSingleSubject[int] = AsyncTestSingleSubject()
    error = MyException()
    sink = AsyncTestObserver()

    async def athrow():
        await xs.athrow(error)

    asyncio.ensure_future(athrow())
    await asyncio.sleep(10)

    async with await xs.subscribe_async(sink):
        await xs.asend_later(1, 20)

    assert sink.values == [(10, OnError(error))]


@pytest.mark.asyncio
async def test_stream_cold_close():
    xs: AsyncTestSingleSubject[int] = AsyncTestSingleSubject()

    sink = AsyncTestObserver()

    async def aclose():
        await xs.aclose()

    asyncio.ensure_future(aclose())
    await asyncio.sleep(10)
    async with await xs.subscribe_async(sink):
        await xs.asend_later(1, 20)

    assert sink.values == [(10, OnCompleted)]
