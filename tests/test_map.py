import asyncio
from typing import Optional

import pytest
from expression.core import pipe
from expression.system import AsyncDisposable

import aioreactive as rx
from aioreactive import AsyncObservable, AsyncObserver
from aioreactive.testing import VirtualTimeEventLoop


class EventLoopPolicy(asyncio.DefaultEventLoopPolicy):
    def get_event_loop(self) -> asyncio.AbstractEventLoop:
       return VirtualTimeEventLoop()

@pytest.fixture(scope="module")  # type: ignore
def event_loop_policy():
    return EventLoopPolicy()

@pytest.mark.asyncio(loop_scope="module")
async def test_map_works():
    xs: AsyncObservable[int] = rx.from_iterable([1, 2, 3])
    values: list[int] = []

    async def asend(value: int) -> None:
        values.append(value)

    def mapper(value: int) -> int:
        return value * 10

    ys = pipe(xs, rx.map(mapper))

    obv: AsyncObserver[int] = rx.AsyncAwaitableObserver(asend)
    async with await ys.subscribe_async(obv):
        result = await obv
        assert result == 30
        assert values == [10, 20, 30]


@pytest.mark.asyncio(loop_scope="module")
async def test_map_mapper_throws():
    error = Exception("ex")
    exception = None

    xs = rx.from_iterable([1])

    async def athrow(ex: Exception):
        nonlocal exception
        exception = ex

    def mapper(x: int):
        raise error

    ys = pipe(xs, rx.map(mapper))

    obv = rx.AsyncAwaitableObserver(athrow=athrow)

    await ys.subscribe_async(obv)

    try:
        await obv
    except Exception as ex:
        assert exception == ex
    else:
        assert False


@pytest.mark.asyncio(loop_scope="module")
async def test_map_subscription_cancel():
    xs: rx.AsyncSubject[int] = rx.AsyncSubject()
    sub: Optional[AsyncDisposable] = None
    result: list[int] = []

    def mapper(value: int) -> int:
        return value * 10

    ys = pipe(xs, rx.map(mapper))

    async def asend(value: int) -> None:
        result.append(value)
        assert sub is not None
        await sub.dispose_async()
        await asyncio.sleep(0)

    async with await ys.subscribe_async(rx.AsyncAnonymousObserver(asend)) as sub:
        await xs.asend(10)
        await asyncio.sleep(0)
        await xs.asend(20)

    assert result == [100]


@pytest.mark.asyncio(loop_scope="module")
async def test_mapi_works():
    xs: AsyncObservable[int] = rx.from_iterable([1, 2, 3])
    values: list[int] = []

    async def asend(value: int) -> None:
        values.append(value)

    def mapper(a: int, i: int) -> int:
        return a + i

    ys = pipe(xs, rx.mapi(mapper))

    obv: AsyncObserver[int] = rx.AsyncAwaitableObserver(asend)
    async with await ys.subscribe_async(obv):
        result = await obv
        assert result == 5
        assert values == [1, 3, 5]
