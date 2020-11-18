import asyncio
import logging

import aioreactive as rx
import pytest
from aioreactive.notification import OnCompleted, OnError, OnNext
from aioreactive.testing import AsyncTestObserver, AsyncTestSubject, VirtualTimeEventLoop, ca
from expression.core import pipe

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@pytest.yield_fixture()  # type:ignore
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_delay_done():
    xs: AsyncTestSubject[int] = AsyncTestSubject()

    ys = pipe(xs, rx.delay(1.0))
    obv = AsyncTestObserver()
    async with await ys.subscribe_async(obv):
        await xs.asend_later(0, 10)
        await xs.asend_later(1.0, 20)
        await xs.aclose_later(1.0)
        await obv

    assert obv.values == [
        (ca(1), OnNext(10)),
        (ca(2), OnNext(20)),
        (ca(3), OnCompleted),
    ]


@pytest.mark.asyncio
async def test_delay_cancel_before_done():
    xs: AsyncTestSubject[int] = AsyncTestSubject()

    ys = pipe(xs, rx.delay(0.3))
    obv = AsyncTestObserver()
    async with await ys.subscribe_async(obv):
        await xs.asend(10)
        await asyncio.sleep(1.5)
        await xs.asend(20)

    await asyncio.sleep(1)
    assert obv.values == [
        (ca(0.3), OnNext(10)),
    ]


@pytest.mark.asyncio
async def test_delay_throw():
    error = Exception("ex")
    xs: AsyncTestSubject[int] = AsyncTestSubject()

    ys = pipe(xs, rx.delay(0.3))

    obv = AsyncTestObserver()
    await ys.subscribe_async(obv)
    await xs.asend(10)
    await asyncio.sleep(1)
    await xs.asend(20)
    await xs.athrow(error)
    await asyncio.sleep(1)

    assert obv.values == [
        (ca(0.3), OnNext(10)),
        (ca(1.3), OnNext(20)),
        (ca(1.6), OnError(error)),
    ]
