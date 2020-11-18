import logging

import aioreactive as rx
import pytest
from aioreactive.notification import OnCompleted, OnNext
from aioreactive.testing import AsyncTestObserver, AsyncTestSubject, VirtualTimeEventLoop
from aioreactive.types import AsyncObservable
from expression.core import pipe

logging.basicConfig(level=logging.DEBUG)


@pytest.yield_fixture()  # type: ignore
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_merge_done():
    xs: AsyncTestSubject[AsyncObservable[int]] = AsyncTestSubject()

    ys = pipe(xs, rx.merge_inner())

    obv = AsyncTestObserver()
    await ys.subscribe_async(obv)
    await xs.asend(rx.from_iterable([10]))
    await xs.asend(rx.from_iterable([20]))
    await xs.aclose()
    await obv

    assert obv.values == [(0, OnNext(10)), (0, OnNext(20)), (0, OnCompleted)]


@pytest.mark.asyncio
async def test_merge_streams():
    xs: AsyncTestSubject[AsyncObservable[int]] = AsyncTestSubject()
    s1: AsyncTestSubject[int] = AsyncTestSubject()
    s2: AsyncTestSubject[int] = AsyncTestSubject()

    ys = pipe(xs, rx.merge_inner())

    obv = AsyncTestObserver()
    await ys.subscribe_async(obv)
    await xs.asend(s1)
    await xs.asend(s2)

    await s1.asend_at(1, 10)
    await s1.asend_at(2, 20)
    await s1.asend_at(4, 30)
    await s1.aclose_at(6)

    await s2.asend_at(0, 40)
    await s2.asend_at(3, 50)
    await s2.asend_at(5, 60)
    await s2.aclose_at(6)

    await xs.aclose()
    await obv

    assert obv.values == [
        (0, OnNext(40)),
        (1, OnNext(10)),
        (2, OnNext(20)),
        (3, OnNext(50)),
        (4, OnNext(30)),
        (5, OnNext(60)),
        (6, OnCompleted),
    ]


@pytest.mark.asyncio
async def test_merge_streams_concat():
    s1: AsyncTestSubject[int] = AsyncTestSubject()
    s2 = rx.from_iterable([1, 2, 3])

    xs = rx.from_iterable([s1, s2])

    ys = pipe(xs, rx.merge_inner(1))

    obv = AsyncTestObserver()
    await ys.subscribe_async(obv)

    await s1.asend_at(1, 10)
    await s1.asend_at(2, 20)
    await s1.asend_at(4, 30)
    await s1.aclose_at(6)

    await obv

    assert obv.values == [
        (1, OnNext(10)),
        (2, OnNext(20)),
        (4, OnNext(30)),
        (6, OnNext(1)),
        (6, OnNext(2)),
        (6, OnNext(3)),
        (6, OnCompleted),
    ]
