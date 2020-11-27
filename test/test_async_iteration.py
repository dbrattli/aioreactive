import asyncio
import logging

import aioreactive as rx
import pytest
from aioreactive.testing import VirtualTimeEventLoop

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@pytest.yield_fixture()  # type: ignore
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_async_iteration() -> None:
    xs = rx.from_iterable([1, 2, 3])
    result = []

    async for x in rx.to_async_iterable(xs):
        result.append(x)

    assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_async_comprehension() -> None:
    xs = rx.from_iterable([1, 2, 3])

    result = [x async for x in rx.to_async_iterable(xs)]

    assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_async_iteration_aync_with() -> None:
    xs = rx.from_iterable([1, 2, 3])
    result = []

    obv = rx.AsyncIteratorObserver(xs)
    async for x in obv:
        result.append(x)

    assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_async_iteration_inception() -> None:
    # iterable to async source to async iterator to async source
    xs = rx.from_iterable([1, 2, 3])
    obv = rx.AsyncIteratorObserver(xs)

    ys = rx.from_async_iterable(obv)
    result = []

    async for y in rx.to_async_iterable(ys):
        result.append(y)

    assert result == [1, 2, 3]
