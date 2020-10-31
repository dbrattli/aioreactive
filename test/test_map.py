import asyncio
from inspect import iscoroutinefunction

import pytest
from aioreactive.core import AsyncRx
from aioreactive.core.observables import AsyncObservable
from aioreactive.core.types import AsyncObserver
from aioreactive.testing import AsyncAnonymousObserver, AsyncSubject, VirtualTimeEventLoop
from fslash.core import pipe


@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_map_happy():
    xs: AsyncObservable[int] = AsyncRx.from_iterable([1, 2, 3])
    values = []

    async def asend(value):
        values.append(value)

    def mapper(value: int) -> int:
        return value * 10

    ys = pipe(xs, AsyncRx.map(mapper))

    assert iscoroutinefunction(asend)
    obv: AsyncObserver[int] = AsyncAnonymousObserver(asend)
    async with await ys.subscribe_async(obv):
        result = await obv
        assert result == 30
        assert values == [10, 20, 30]


# @pytest.mark.asyncio
# async def test_map_mapper_throws():
#     xs = AsyncRx.from_iterable([1])
#     exception = None
#     error = Exception("ex")

#     async def asend(value):
#         pass

#     async def athrow(ex):
#         nonlocal exception
#         exception = ex

#     def mapper(x):
#         raise error

#     ys = pipe(xs, AsyncRx.map(mapper))

#     try:
#         await ys.subscribe_async(AsyncAnonymousObserver(asend, athrow))
#     except Exception as ex:
#         assert ex == error

#     assert exception == error


# @pytest.mark.asyncio
# async def test_map_subscription_cancel():
#     xs = AsyncSubject()
#     result = []
#     sub = None

#     def mapper(value):
#         return value * 10

#     ys = pipe(xs, AsyncRx.map(mapper))

#     async def asend(value):
#         result.append(value)
#         await sub.adispose()
#         await asyncio.sleep(0)

#     async with ys.subscribe_async(AsyncAnonymousObserver(asend)) as sub:
#         await xs.asend(10)
#         await asyncio.sleep(0)
#         await xs.asend(20)

#     assert result == [100]
