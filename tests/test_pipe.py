import asyncio
import logging
from typing import Generator, List

import pytest
from expression.core import pipe
from pytest import approx

import aioreactive as rx
from aioreactive.notification import OnCompleted, OnNext
from aioreactive.testing import AsyncTestObserver, VirtualTimeEventLoop
from aioreactive.types import AsyncObservable

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@pytest.fixture()  # type: ignore
def event_loop() -> Generator[VirtualTimeEventLoop, None, None]:
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_pipe_map() -> None:
    xs = rx.from_iterable([1, 2, 3])

    def mapper(value: int) -> int:
        return value * 10

    ys = pipe(xs, rx.map(mapper))

    obv: AsyncTestObserver[int] = AsyncTestObserver()
    await rx.run(ys, obv)
    assert obv.values == [
        (0, OnNext(10)),
        (0, OnNext(20)),
        (0, OnNext(30)),
        (0, OnCompleted),
    ]


@pytest.mark.asyncio
async def test_pipe_simple_pipe() -> None:
    xs = rx.from_iterable([1, 2, 3])

    def mapper(value: int) -> int:
        return value * 10

    async def predicate(value: int) -> bool:
        await asyncio.sleep(0.1)
        return value > 1

    ys = pipe(xs, rx.filter_async(predicate), rx.map(mapper))

    obv: AsyncTestObserver[int] = AsyncTestObserver()
    await rx.run(ys, obv)
    assert obv.values == [
        (approx(0.2), OnNext(20)),
        (approx(0.3), OnNext(30)),
        (approx(0.3), OnCompleted),
    ]


@pytest.mark.asyncio
async def test_pipe_complex_pipe() -> None:
    xs = rx.from_iterable([1, 2, 3])
    result: List[int] = []

    def mapper(value: int) -> int:
        return value * 10

    async def predicate(value: int) -> bool:
        await asyncio.sleep(0.1)
        return value > 1

    def long_running(value: int) -> AsyncObservable[int]:
        return rx.from_iterable([value])

    ys = pipe(
        xs,
        rx.filter_async(predicate),
        rx.map(mapper),
        rx.flat_map(long_running),
        rx.to_async_iterable,
    )

    async for value in ys:
        result.append(value)

    assert result == [20, 30]
