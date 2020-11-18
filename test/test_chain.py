import asyncio
import logging

import pytest
from aioreactive import AsyncObservable, AsyncRx
from aioreactive.notification import OnCompleted, OnNext
from aioreactive.testing import AsyncTestObserver, VirtualTimeEventLoop, ca

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@pytest.yield_fixture()  # type: ignore
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_chain_map():
    xs = AsyncRx.from_iterable([1, 2, 3])

    def mapper(value: int) -> int:
        return value * 10

    ys = xs.map(mapper)

    obv: AsyncTestObserver[int] = AsyncTestObserver()
    await ys.subscribe_async(obv)
    await obv
    assert obv.values == [
        (0, OnNext(10)),
        (0, OnNext(20)),
        (0, OnNext(30)),
        (0, OnCompleted),
    ]


@pytest.mark.asyncio
async def test_chain_simple_pipe():
    xs = AsyncRx.from_iterable([1, 2, 3])

    def mapper(value: int) -> int:
        return value * 10

    async def predicate(value: int) -> bool:
        await asyncio.sleep(0.1)
        return value > 1

    ys = xs.filter_async(predicate).map(mapper)

    obv: AsyncTestObserver[int] = AsyncTestObserver()
    await ys.subscribe_async(obv)
    await obv

    assert obv.values == [
        (ca(0.2), OnNext(20)),
        (ca(0.3), OnNext(30)),
        (ca(0.3), OnCompleted),
    ]


@pytest.mark.asyncio
async def test_chain_complex_pipe():
    xs = AsyncRx.from_iterable([1, 2, 3])

    def mapper(value: int) -> int:
        return value * 10

    async def predicate(value: int) -> bool:
        await asyncio.sleep(0.1)
        return value > 1

    async def long_running(value: int) -> AsyncObservable[int]:
        return AsyncRx.from_iterable([value])

    ys = xs.filter_async(predicate).map(mapper).flat_map_async(long_running)

    obv: AsyncTestObserver[int] = AsyncTestObserver()
    await ys.subscribe_async(obv)
    await obv
    assert obv.values == [
        (ca(0.2), OnNext(20)),
        (ca(0.3), OnNext(30)),
        (ca(0.3), OnCompleted),
    ]
