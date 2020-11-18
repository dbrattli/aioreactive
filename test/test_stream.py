import asyncio
import logging
from typing import Optional

import aioreactive as rx
import pytest
from aioreactive.notification import OnCompleted, OnError, OnNext
from aioreactive.testing import AsyncTestSubject, AsyncTestObserver, VirtualTimeEventLoop
from expression.core import pipe
from expression.system.disposable import AsyncDisposable

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
async def test_stream_happy() -> None:
    xs: AsyncTestSubject[int] = AsyncTestSubject()

    obv = AsyncTestObserver()
    await xs.subscribe_async(obv)
    await xs.asend_later(1, 10)
    await xs.asend_later(1, 20)
    await xs.asend_later(1, 30)

    assert obv.values == [(1, OnNext(10)), (2, OnNext(20)), (3, OnNext(30))]


@pytest.mark.asyncio
async def test_stream_throws() -> None:
    ex = MyException("ex")
    xs: AsyncTestSubject[int] = AsyncTestSubject()

    obv = AsyncTestObserver()
    with pytest.raises(MyException):
        await xs.subscribe_async(obv)

        await xs.asend_later(1, 10)
        await xs.asend_later(1, 20)
        await xs.asend_later(1, 30)
        await xs.athrow_later(1, ex)
        await xs.asend_later(1, 40)

        await obv

    assert obv.values == [(1, OnNext(10)), (2, OnNext(20)), (3, OnNext(30)), (4, OnError(ex))]


@pytest.mark.asyncio
async def test_stream_send_after_close() -> None:
    xs: AsyncTestSubject[int] = AsyncTestSubject()

    obv = AsyncTestObserver()
    await xs.subscribe_async(obv)

    await xs.asend_later(1, 10)
    await xs.asend_later(1, 20)
    await xs.asend_later(1, 30)
    await xs.aclose_later(2)
    await xs.asend_later(1, 40)

    assert obv.values == [(1, OnNext(10)), (2, OnNext(20)), (3, OnNext(30)), (5, OnCompleted)]


@pytest.mark.asyncio
async def test_stream_cancel() -> None:
    xs: AsyncTestSubject[int] = AsyncTestSubject()
    subscription: Optional[AsyncDisposable] = None

    def mapper(value: int) -> int:
        return value * 10

    ys = pipe(xs, rx.map(mapper))

    obv = AsyncTestObserver()
    subscription = await ys.subscribe_async(obv)
    await xs.asend_later(1, 10)
    await subscription.dispose_async()
    await xs.asend_later(1, 20)

    assert obv.values == [(1, OnNext(100))]


@pytest.mark.asyncio
async def test_stream_cancel_asend() -> None:
    xs: AsyncTestSubject[int] = AsyncTestSubject()
    subscription: Optional[AsyncDisposable] = None

    async def asend(value: int) -> None:
        assert subscription is not None
        await subscription.dispose_async()
        await asyncio.sleep(0)

    def mapper(value: int) -> int:
        return value * 10

    ys = pipe(xs, rx.map(mapper))

    obv = AsyncTestObserver(asend)
    async with await ys.subscribe_async(obv) as sub:
        subscription = sub

        await xs.asend_later(1, 10)
        await xs.asend_later(1, 20)

    assert obv.values == [(1, OnNext(100))]


@pytest.mark.asyncio
async def test_stream_cancel_mapper():
    xs: AsyncTestSubject[int] = AsyncTestSubject()
    subscription: Optional[AsyncDisposable] = None

    def mapper(value: int) -> int:
        assert subscription is not None
        asyncio.ensure_future(subscription.dispose_async())
        return value * 10

    ys = pipe(xs, rx.map(mapper))

    obv: AsyncTestObserver[int] = AsyncTestObserver()
    async with await ys.subscribe_async(obv) as subscription:

        await xs.asend_later(100, 10)
        await xs.asend_later(100, 20)
        await xs.asend_later(100, 30)
        await xs.asend_later(100, 40)
        await xs.asend_later(100, 50)
        await xs.asend_later(100, 60)

    assert obv.values == [(100, OnNext(100))]


@pytest.mark.asyncio
async def test_stream_cancel_context():
    xs: AsyncTestSubject[int] = AsyncTestSubject()

    obv = AsyncTestObserver()
    async with await xs.subscribe_async(obv):
        pass

    await xs.asend_later(1, 10)
    await xs.asend_later(1, 20)

    assert obv.values == []
