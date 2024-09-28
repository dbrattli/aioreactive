import asyncio
import logging
from typing import Awaitable, Optional

import pytest
from expression.system.disposable import AsyncDisposable
from pytest import approx

import aioreactive as rx
from aioreactive.notification import OnCompleted, OnError, OnNext
from aioreactive.testing import AsyncTestObserver, VirtualTimeEventLoop

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class EventLoopPolicy(asyncio.DefaultEventLoopPolicy):
    def get_event_loop(self) -> asyncio.AbstractEventLoop:
       return VirtualTimeEventLoop()

@pytest.fixture(scope="module")  # type: ignore
def event_loop_policy():
    return EventLoopPolicy()


@pytest.mark.asyncio(loop_scope="module")
async def test_unit_happy():
    xs = rx.single(42)

    obv: AsyncTestObserver[int] = AsyncTestObserver()
    await rx.run(xs, obv)
    assert obv.values == [(0, OnNext(42)), (0, OnCompleted())]


@pytest.mark.asyncio(loop_scope="module")
async def test_unit_observer_throws():
    error = Exception("error")
    xs = rx.single(42)

    async def asend(value: int) -> None:
        raise error

    obv = AsyncTestObserver(asend)
    await xs.subscribe_async(obv)

    try:
        await obv
    except Exception as ex:
        assert ex == error
    assert obv.values == [(0, OnNext(42)), (0, OnError(error))]


@pytest.mark.asyncio(loop_scope="module")
async def test_unit_close():
    xs = rx.single(42)
    sub: Optional[AsyncDisposable] = None

    async def asend(value: int) -> None:
        assert sub is not None
        await sub.dispose_async()
        await asyncio.sleep(0)

    obv: AsyncTestObserver[int] = AsyncTestObserver(asend)
    sub = await xs.subscribe_async(obv)

    await obv

    assert obv.values == [
        (0, OnNext(42)),
        (0, OnCompleted()),
    ]


@pytest.mark.asyncio(loop_scope="module")
async def test_unit_happy_resolved_future():
    fut: Awaitable[int] = asyncio.Future()
    xs = rx.from_async(fut)
    fut.set_result(42)

    obv: AsyncTestObserver[int] = AsyncTestObserver()
    await rx.run(xs, obv)
    assert obv.values == [
        (0, OnNext(42)),
        (0, OnCompleted()),
    ]


@pytest.mark.asyncio(loop_scope="module")
async def test_unit_happy_future_resolve():
    fut: Awaitable[int] = asyncio.Future()
    xs = rx.from_async(fut)

    obv: AsyncTestObserver[int] = AsyncTestObserver()
    async with await xs.subscribe_async(obv):
        fut.set_result(42)
        await obv

    assert obv.values == [
        (0, OnNext(42)),
        (0, OnCompleted()),
    ]


@pytest.mark.asyncio(loop_scope="module")
async def test_unit_future_exception():
    fut: Awaitable[int] = asyncio.Future()
    ex = Exception("ex")
    xs = rx.from_async(fut)

    obv: AsyncTestObserver[int] = AsyncTestObserver()
    async with await xs.subscribe_async(obv):
        fut.set_exception(ex)
        with pytest.raises(Exception):
            await obv
    assert obv.values == [(0, OnError(ex))]


@pytest.mark.asyncio(loop_scope="module")
async def test_unit_future_cancel():
    fut: Awaitable[int] = asyncio.Future()
    xs = rx.from_async(fut)

    obv = AsyncTestObserver()
    async with await xs.subscribe_async(obv):
        await asyncio.sleep(1)
        fut.cancel()
        with pytest.raises(asyncio.CancelledError):
            await obv

    assert obv.values == [(approx(1), OnCompleted())]
