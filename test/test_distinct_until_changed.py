import aioreactive as rx
import pytest
from aioreactive import AsyncRx
from aioreactive.notification import OnCompleted, OnNext
from aioreactive.testing import AsyncTestObserver, VirtualTimeEventLoop
from expression.core import pipe


class MyException(Exception):
    pass


@pytest.yield_fixture()  # type: ignore
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_distinct_until_changed_different():
    xs = rx.from_iterable([1, 2, 3])

    obv: AsyncTestObserver[int] = AsyncTestObserver()
    ys = pipe(xs, rx.distinct_until_changed)

    await rx.run(ys, obv)
    assert obv.values == [(0, OnNext(1)), (0, OnNext(2)), (0, OnNext(3)), (0, OnCompleted)]


@pytest.mark.asyncio
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
        (0, OnCompleted),
    ]
