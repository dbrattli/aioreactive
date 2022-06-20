import asyncio

import pytest
from expression import pipe

from aioreactive import scan, scan_async
from aioreactive.notification import OnCompleted, OnNext
from aioreactive.testing import AsyncTestObserver, VirtualTimeEventLoop
from aioreactive.testing.subject import AsyncTestSingleSubject


class MyException(Exception):
    pass


@pytest.fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    try:
        yield loop
    finally:
        loop.close()


def sync_sum(a: int, b: int) -> int:
    return a + b


async def async_sum(a: int, b: int) -> int:
    await asyncio.sleep(0.2)
    return a + b


@pytest.mark.asyncio
async def test_scan():
    xs: AsyncTestSingleSubject[int] = AsyncTestSingleSubject()

    observer = AsyncTestObserver()
    await pipe(xs, scan(sync_sum, 0)).subscribe_async(observer)

    await xs.asend(1)
    await xs.asend(2)
    await xs.asend(3)

    await xs.asend(4)
    await xs.aclose()
    values = list(map(lambda t: t[1], observer.values))
    assert values == [
        OnNext(1),
        OnNext(3),
        OnNext(6),
        OnNext(10),
        OnCompleted,
    ]


@pytest.mark.asyncio
async def test_scan_async():
    xs: AsyncTestSingleSubject[int] = AsyncTestSingleSubject()

    observer = AsyncTestObserver()
    await pipe(xs, scan_async(async_sum, 0)).subscribe_async(observer)

    await xs.asend(1)
    await xs.asend(2)
    await xs.asend(3)
    await xs.asend(4)
    await xs.aclose()
    values = list(map(lambda t: t[1], observer.values))
    assert values == [
        OnNext(1),
        OnNext(3),
        OnNext(6),
        OnNext(10),
        OnCompleted,
    ]
