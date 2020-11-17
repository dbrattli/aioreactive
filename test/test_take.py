import logging
from asyncio import CancelledError

import aioreactive as rx
import pytest
from aioreactive.notification import OnCompleted, OnNext
from aioreactive.testing import AsyncTestObserver, VirtualTimeEventLoop
from expression.core import pipe

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@pytest.yield_fixture()  # type:ignore
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_take_zero() -> None:
    xs = rx.from_iterable([1, 2, 3, 4, 5])

    ys = pipe(xs, rx.take(0))

    obv: AsyncTestObserver[int] = AsyncTestObserver()
    with pytest.raises(CancelledError):
        await rx.run(ys, obv)

    assert obv.values == [(0, OnCompleted)]


@pytest.mark.asyncio
async def test_take_empty() -> None:
    xs = rx.empty()

    ys = pipe(xs, rx.take(42))

    obv: AsyncTestObserver[int] = AsyncTestObserver()
    with pytest.raises(CancelledError):
        await rx.run(ys, obv)

    assert obv.values == [(0, OnCompleted)]


@pytest.mark.asyncio
async def test_take_negative() -> None:
    xs = rx.from_iterable([1, 2, 3, 4, 5])

    with pytest.raises(ValueError):
        pipe(xs, rx.take(-1))


@pytest.mark.asyncio
async def test_take_normal() -> None:
    xs = rx.from_iterable([1, 2, 3, 4, 5])

    ys = pipe(xs, rx.take(2))

    obv: AsyncTestObserver[int] = AsyncTestObserver()
    result = await rx.run(ys, obv)

    assert result == 2
    assert obv.values == [(0, OnNext(1)), (0, OnNext(2)), (0, OnCompleted)]
