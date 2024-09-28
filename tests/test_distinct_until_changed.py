import asyncio
import pytest
from expression.core import pipe

import aioreactive as rx
from aioreactive import AsyncRx
from aioreactive.notification import OnCompleted, OnNext
from aioreactive.testing import AsyncTestObserver, VirtualTimeEventLoop


class MyException(Exception):
    pass


class EventLoopPolicy(asyncio.DefaultEventLoopPolicy):
    def get_event_loop(self) -> asyncio.AbstractEventLoop:
       return VirtualTimeEventLoop()

@pytest.fixture(scope="module")  # type: ignore
def event_loop_policy():
    return EventLoopPolicy()


@pytest.mark.asyncio(loop_scope="module")
async def test_distinct_until_changed_different():
    xs = rx.from_iterable([1, 2, 3])

    obv: AsyncTestObserver[int] = AsyncTestObserver()
    ys = pipe(xs, rx.distinct_until_changed)

    await rx.run(ys, obv)
    assert obv.values == [
        (0, OnNext(1)),
        (0, OnNext(2)),
        (0, OnNext(3)),
        (0, OnCompleted()),
    ]


@pytest.mark.asyncio(loop_scope="module")
async def test_distinct_until_changed_changed():
    xs = AsyncRx.from_iterable([1, 2, 2, 1, 3, 3, 1, 2, 2])

    obv: AsyncTestObserver[int] = AsyncTestObserver()
    ys = xs.distinct_until_changed()

    await rx.run(ys, obv)
    assert obv.values == [
        (0, OnNext(1)),
        (0, OnNext(2)),
        (0, OnNext(1)),
        (0, OnNext(3)),
        (0, OnNext(1)),
        (0, OnNext(2)),
        (0, OnCompleted()),
    ]
