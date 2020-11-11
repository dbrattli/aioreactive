import asyncio
from typing import Any, Generator

import aioreactive as rx
import pytest
from aioreactive.testing import VirtualTimeEventLoop
from expression.core import pipe


class MyException(Exception):
    pass


@pytest.yield_fixture()  # type:ignore
def event_loop() -> Generator[Any, Any, Any]:
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_filter_happy() -> None:
    xs = rx.from_iterable([1, 2, 3])
    result = []

    async def asend(value: int) -> None:
        result.append(value)

    async def predicate(value: int) -> bool:
        await asyncio.sleep(0.1)
        return value > 1

    ys = pipe(xs, rx.filter_async(predicate))
    value = await rx.run(ys, rx.AsyncAwaitableObserver(asend))
    assert value == 3
    assert result == [2, 3]


@pytest.mark.asyncio
async def test_filter_predicate_throws() -> None:
    xs = rx.from_iterable([1, 2, 3])
    err = MyException("err")
    result = []

    async def asend(value: int) -> None:
        result.append(value)

    async def predicate(value: int) -> bool:
        await asyncio.sleep(0.1)
        raise err

    ys = pipe(xs, rx.filter_async(predicate))

    with pytest.raises(MyException):
        await rx.run(ys, rx.AsyncAwaitableObserver(asend))

    assert result == []
