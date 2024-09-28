import asyncio
import logging

import pytest
from expression.core import pipe

import aioreactive as rx
from aioreactive.notification import OnCompleted, OnNext
from aioreactive.testing import (
    AsyncTestObserver,
    AsyncTestSubject,
    VirtualTimeEventLoop,
    ca,
)

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class EventLoopPolicy(asyncio.DefaultEventLoopPolicy):
    def get_event_loop(self) -> asyncio.AbstractEventLoop:
       return VirtualTimeEventLoop()

@pytest.fixture(scope="module")  # type: ignore
def event_loop_policy():
    return EventLoopPolicy()



@pytest.mark.asyncio(loop_scope="module")
async def test_debounce():
    xs: AsyncTestSubject[int] = AsyncTestSubject()

    ys = pipe(xs, rx.debounce(0.5))

    obv: AsyncTestObserver[int] = AsyncTestObserver()
    subscription = await ys.subscribe_async(obv)

    await xs.asend(1)  # 0 -> 0.5
    await asyncio.sleep(0.6)  # 0.6
    await xs.asend(2)  # 0.6 -> 1.1
    await asyncio.sleep(0.6)  # 1.2
    await xs.aclose()  # 1.2
    await asyncio.sleep(0.6)
    await obv

    assert obv.values == [
        (ca(0.5), OnNext(1)),
        (ca(1.1), OnNext(2)),
        (ca(1.2), OnCompleted()),
    ]

    await subscription.dispose_async()


@pytest.mark.asyncio(loop_scope="module")
async def test_debounce_filter():
    xs: AsyncTestSubject[int] = AsyncTestSubject()

    ys = pipe(xs, rx.debounce(0.5))
    obv: AsyncTestObserver[int] = AsyncTestObserver()
    subscription = await ys.subscribe_async(obv)

    await xs.asend(1)
    await asyncio.sleep(0.3)
    await xs.asend(2)
    await asyncio.sleep(0.6)
    await xs.aclose()
    await asyncio.sleep(0.6)
    await obv

    assert obv.values == [
        (ca(0.8), OnNext(2)),
        (ca(0.9), OnCompleted()),
    ]

    await subscription.dispose_async()
