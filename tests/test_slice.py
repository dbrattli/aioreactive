import asyncio
import logging

import pytest

import aioreactive as rx
from aioreactive import AsyncRx
from aioreactive.notification import OnCompleted, OnNext
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
async def test_slice_special():
    xs = AsyncRx.from_iterable([1, 2, 3, 4, 5])

    ys = xs[1:-1]

    obv: AsyncTestObserver[int] = AsyncTestObserver()
    result = await rx.run(ys, obv)

    assert result == 4
    assert obv.values == [
        (0, OnNext(2)),
        (0, OnNext(3)),
        (0, OnNext(4)),
        (0, OnCompleted()),
    ]


@pytest.mark.asyncio(loop_scope="module")
async def test_slice_step():
    xs = AsyncRx.from_iterable([1, 2, 3, 4, 5])

    ys = xs[::2]

    obv: AsyncTestObserver[int] = AsyncTestObserver()
    result = await rx.run(ys, obv)

    assert result == 5
    assert obv.values == [
        (0, OnNext(1)),
        (0, OnNext(3)),
        (0, OnNext(5)),
        (0, OnCompleted()),
    ]
