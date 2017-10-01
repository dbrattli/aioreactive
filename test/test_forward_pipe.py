import pytest
import asyncio
import logging

from aioreactive.testing import VirtualTimeEventLoop
from aioreactive.core import AsyncObservable, run, subscribe, AsyncStream, AsyncAnonymousObserver, Operators as _
from aioreactive.operators.pipe import pipe
from aioreactive.operators.to_async_iterable import to_async_iterable

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_forward_pipe_map() -> None:
    xs = AsyncObservable.from_iterable([1, 2, 3])
    result = []

    def mapper(value) -> int:
        return value * 10

    ys = xs | _.map(mapper)

    async def asend(value) -> None:
        result.append(value)

    await run(ys, AsyncAnonymousObserver(asend))
    assert result == [10, 20, 30]


@pytest.mark.asyncio
async def test_forward_pipe_simple_pipe() -> None:
    xs = AsyncObservable.from_iterable([1, 2, 3])
    result = []

    def mapper(value) -> int:
        return value * 10

    async def predicate(value) -> bool:
        await asyncio.sleep(0.1)
        return value > 1

    ys = xs | _.filter(predicate) | _.map(mapper)

    async def asend(value) -> None:
        result.append(value)

    await run(ys, AsyncAnonymousObserver(asend))
    assert result == [20, 30]


@pytest.mark.asyncio
async def test_forward_pipe_complex_pipe() -> None:
    xs = AsyncObservable.from_iterable([1, 2, 3])
    result = []

    def mapper(value) -> int:
        return value * 10

    async def predicate(value) -> bool:
        await asyncio.sleep(0.1)
        return value > 1

    async def long_running(value) -> AsyncObservable[int]:
        return AsyncObservable.from_iterable([value])

    ys = (xs
          | _.filter(predicate)
          | _.map(mapper)
          | _.flat_map(long_running)
          | _.to_async_iterable()
          )

    async for value in ys:
        result.append(value)

    assert result == [20, 30]
