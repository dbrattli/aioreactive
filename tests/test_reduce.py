import asyncio

import pytest
from expression import pipe

import aioreactive as rx
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


def sync_sum(a: int, b: int) -> int:
    return a + b


async def async_sum(a: int, b: int) -> int:
    await asyncio.sleep(0.2)
    return a + b


@pytest.mark.asyncio(loop_scope="module")
async def test_reduce():
    xs = rx.from_iterable([1, 2, 3, 4])
    observer = AsyncTestObserver()
    ys = pipe(xs, rx.reduce(sync_sum, 0))
    await rx.run(ys, observer)

    values = list(map(lambda t: t[1], observer.values))
    assert values == [
        OnNext(10),
        OnCompleted(),
    ]


@pytest.mark.asyncio(loop_scope="module")
async def test_reduce_async():
    xs = rx.from_iterable([1, 2, 3, 4])
    observer = AsyncTestObserver()
    ys = pipe(xs, rx.reduce_async(async_sum, 0))

    await rx.run(ys, observer)

    values = list(map(lambda t: t[1], observer.values))
    assert values == [
        OnNext(10),
        OnCompleted(),
    ]
