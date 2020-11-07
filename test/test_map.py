import asyncio
from typing import Optional, Tuple

import pytest
from aioreactive import asyncrx
from aioreactive.observables import AsyncObservable
from aioreactive.observers import AsyncAnonymousObserver, AsyncAwaitableObserver
from aioreactive.testing import AsyncSubject, VirtualTimeEventLoop
from aioreactive.types import AsyncObserver
from expression.core import pipe
from expression.system.disposable import AsyncDisposable


@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_map_works():
    xs: AsyncObservable[int] = asyncrx.from_iterable([1, 2, 3])
    values = []

    async def asend(value: int) -> None:
        values.append(value)

    def mapper(value: int) -> int:
        return value * 10

    ys = pipe(xs, asyncrx.map(mapper))

    obv: AsyncObserver[int] = AsyncAwaitableObserver(asend)
    async with await ys.subscribe_async(obv):
        result = await obv
        assert result == 30
        assert values == [10, 20, 30]


@pytest.mark.asyncio
async def test_map_mapper_throws():
    error = Exception("ex")
    exception = None

    xs = asyncrx.from_iterable([1])

    async def athrow(ex: Exception):
        nonlocal exception
        exception = ex

    def mapper(x: int):
        raise error

    ys = pipe(xs, asyncrx.map(mapper))

    obv = AsyncAwaitableObserver(athrow=athrow)

    await ys.subscribe_async(obv)

    try:
        await obv
    except Exception as ex:
        assert exception == ex
    else:
        assert False


@pytest.mark.asyncio
async def test_map_subscription_cancel():
    xs: AsyncSubject[int] = AsyncSubject()
    result = []
    sub: Optional[AsyncDisposable] = None

    def mapper(value: int) -> int:
        return value * 10

    ys = pipe(xs, asyncrx.map(mapper))

    async def asend(value: int) -> None:
        result.append(value)
        assert sub is not None
        await sub.dispose_async()
        await asyncio.sleep(0)

    async with await ys.subscribe_async(AsyncAnonymousObserver(asend)) as sub:
        await xs.asend(10)
        await asyncio.sleep(0)
        await xs.asend(20)

    assert result == [100]


@pytest.mark.asyncio
async def test_mapi_works():
    xs: AsyncObservable[int] = asyncrx.from_iterable([1, 2, 3])
    values = []

    async def asend(value: int) -> None:
        values.append(value)

    def mapper(value: Tuple[int, int]) -> int:
        (a, i) = value
        return a + i

    ys = pipe(xs, asyncrx.mapi(mapper))

    obv: AsyncObserver[int] = AsyncAwaitableObserver(asend)
    async with await ys.subscribe_async(obv):
        result = await obv
        assert result == 5
        assert values == [1, 3, 5]
