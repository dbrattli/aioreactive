import asyncio
import logging
from asyncio import CancelledError

import pytest
from expression.core import pipe

import aioreactive as rx
from aioreactive.notification import OnCompleted, OnNext
from aioreactive.testing import AsyncTestObserver, VirtualTimeEventLoop
from aioreactive.types import AsyncObservable

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class EventLoopPolicy(asyncio.DefaultEventLoopPolicy):
    def get_event_loop(self) -> asyncio.AbstractEventLoop:
       return VirtualTimeEventLoop()

@pytest.fixture(scope="module")  # type: ignore
def event_loop_policy():
    return EventLoopPolicy()


@pytest.mark.asyncio(loop_scope="module")
async def test_take_zero() -> None:
    xs = rx.from_iterable([1, 2, 3, 4, 5])

    ys = pipe(xs, rx.take(0))

    obv: AsyncTestObserver[int] = AsyncTestObserver()
    with pytest.raises(CancelledError):
        await rx.run(ys, obv)

    assert obv.values == [(0, OnCompleted())]


@pytest.mark.asyncio(loop_scope="module")
async def test_take_empty() -> None:
    xs: AsyncObservable[int] = rx.empty()

    ys = pipe(xs, rx.take(42))

    obv: AsyncTestObserver[int] = AsyncTestObserver()
    with pytest.raises(CancelledError):
        await rx.run(ys, obv)

    assert obv.values == [(0, OnCompleted())]


@pytest.mark.asyncio(loop_scope="module")
async def test_take_negative() -> None:
    xs = rx.from_iterable([1, 2, 3, 4, 5])

    with pytest.raises(ValueError):
        pipe(xs, rx.take(-1))


@pytest.mark.asyncio(loop_scope="module")
async def test_take_normal() -> None:
    xs = rx.from_iterable([1, 2, 3, 4, 5])

    ys = pipe(xs, rx.take(2))

    obv: AsyncTestObserver[int] = AsyncTestObserver()
    result = await rx.run(ys, obv)

    assert result == 2
    assert obv.values == [(0, OnNext(1)), (0, OnNext(2)), (0, OnCompleted())]
