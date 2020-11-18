import asyncio
from typing import Optional

import aioreactive as rx
import pytest
from aioreactive.notification import OnCompleted, OnError, OnNext
from aioreactive.testing import AsyncTestObserver, VirtualTimeEventLoop
from expression.system.disposable import AsyncDisposable


@pytest.yield_fixture()  # type:ignore
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_from_iterable_happy():
    xs = rx.from_iterable([1, 2, 3])

    obv: AsyncTestObserver[int] = AsyncTestObserver()
    await rx.run(xs, obv)
    assert obv.values == [
        (0, OnNext(1)),
        (0, OnNext(2)),
        (0, OnNext(3)),
        (0, OnCompleted),
    ]


@pytest.mark.asyncio
async def test_from_iterable_observer_throws():
    xs = rx.from_iterable([1, 2, 3])
    error = Exception("error")

    async def asend(value: int) -> None:
        raise error

    obv: AsyncTestObserver[int] = AsyncTestObserver(asend)
    await xs.subscribe_async(obv)

    with pytest.raises(Exception):
        await obv

    assert obv.values == [(0, OnNext(1)), (0, OnError(error))]


# @pytest.mark.asyncio
# async def test_from_iterable_close():
#     xs = rx.from_iterable(range(10))
#     sub: Optional[AsyncDisposable] = None

#     async def asend(value: int) -> None:
#         assert sub is not None
#         await sub.dispose_async()
#         await asyncio.sleep(0.1)

#     async def athrow(err: Exception) -> None:
#         print("Exception: ", err)

#     obv: AsyncTestObserver[int] = AsyncTestObserver(asend, athrow)
#     sub = await xs.subscribe_async(obv)

#     # with pytest.raises(asyncio.CancelledError):
#     await obv

#     assert obv.values == [(0, OnNext(0)), (0, OnCompleted)]
