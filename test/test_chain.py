import pytest
import asyncio
import logging

from aioreactive.testing import VirtualTimeEventLoop
from aioreactive.core import AsyncStream, AsyncAnonymousObserver, AsyncObservable

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_chain_map():
    xs = AsyncObservable.from_iterable([1, 2, 3])
    result = []

    def mapper(value):
        return value * 10

    ys = xs.select(mapper)

    async def on_next(value):
        result.append(value)

    obv = AsyncAnonymousObserver(on_next)
    sub = await ys.subscribe(obv)
    await obv
    assert result == [10, 20, 30]


@pytest.mark.asyncio
async def test_chain_simple_pipe():
    xs = AsyncObservable.from_iterable([1, 2, 3])
    result = []

    def mapper(value):
        return value * 10

    async def predicate(value) -> bool:
        await asyncio.sleep(0.1)
        return value > 1

    ys = xs.where(predicate).select(mapper)

    async def on_next(value) -> None:
        result.append(value)

    obv = AsyncAnonymousObserver(on_next)
    async with ys.subscribe(obv):
        await obv

    assert result == [20, 30]


@pytest.mark.asyncio
async def test_chain_complex_pipe():
    xs = AsyncObservable.from_iterable([1, 2, 3])
    result = []

    def mapper(value) -> int:
        return value * 10

    async def predicate(value) -> bool:
        await asyncio.sleep(0.1)
        return value > 1

    async def long_running(value) -> AsyncObservable:
        return AsyncObservable.from_iterable([value])

    ys = (xs
          .where(predicate)
          .select(mapper)
          .select_many(long_running))

    async def on_next(value):
        result.append(value)

    obv = AsyncAnonymousObserver(on_next)
    sub = await ys.subscribe(obv)
    await obv
    assert result == [20, 30]
