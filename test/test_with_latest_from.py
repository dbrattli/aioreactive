import asyncio
import logging
from asyncio.exceptions import CancelledError
from typing import Tuple

import aioreactive as rx
import pytest
from aioreactive.notification import OnCompleted, OnNext
from aioreactive.testing import AsyncTestSubject, AsyncTestObserver, VirtualTimeEventLoop
from aioreactive.types import AsyncObservable, AsyncObserver
from expression.core import pipe

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@pytest.yield_fixture()  # type: ignore
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_withlatestfrom_never_never():
    xs: AsyncObservable[int] = rx.never()
    ys: AsyncObservable[int] = rx.never()
    result = []

    zs = pipe(xs, rx.with_latest_from(ys))

    obv: AsyncObserver[Tuple[int, int]] = AsyncTestObserver()
    await zs.subscribe_async(obv)
    await asyncio.sleep(1)

    assert result == []


@pytest.mark.asyncio
async def test_withlatestfrom_never_empty():
    xs: AsyncObservable[int] = rx.empty()
    ys: AsyncObservable[int] = rx.never()

    zs = pipe(xs, rx.with_latest_from(ys))

    obv: AsyncTestObserver[Tuple[int, int]] = AsyncTestObserver()
    with pytest.raises(CancelledError):
        await rx.run(zs, obv)

    assert obv.values == [(0, OnCompleted)]


@pytest.mark.asyncio
async def test_withlatestfrom_done():
    xs: AsyncTestSubject[int] = AsyncTestSubject()
    ys: AsyncTestSubject[int] = AsyncTestSubject()

    zs = pipe(xs, rx.with_latest_from(ys), rx.starmap(lambda x, y: x + y))

    obv: AsyncTestObserver[int] = AsyncTestObserver()
    async with await zs.subscribe_async(obv):
        await xs.asend(1)
        await ys.asend(2)
        await xs.asend(3)
        await xs.aclose()
        await obv

    assert obv.values == [(0, OnNext(5)), (0, OnCompleted)]


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_withlatestfrom_done())
    loop.close()
