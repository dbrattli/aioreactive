import pytest
import asyncio
from typing import Generator

from aioreactive.testing import VirtualTimeEventLoop
from aioreactive.operators import from_iterable, filter
from aioreactive.core import run, subscribe, AsyncAnonymousObserver, AsyncStream


class MyException(Exception):
    pass


@pytest.yield_fixture()
def event_loop() -> Generator:
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_filter_happy() -> None:
    xs = from_iterable([1, 2, 3])
    result = []

    async def asend(value: int) -> None:
        result.append(value)

    async def predicate(value: int) -> bool:
        await asyncio.sleep(0.1)
        return value > 1

    ys = filter(predicate, xs)
    value = await run(ys, AsyncAnonymousObserver(asend))
    assert value == 3
    assert result == [2, 3]


@pytest.mark.asyncio
async def test_filter_predicate_throws() -> None:
    xs = from_iterable([1, 2, 3])
    err = MyException("err")
    result = []

    async def asend(value: int) -> None:
        result.append(value)

    async def predicate(value: int) -> bool:
        await asyncio.sleep(0.1)
        raise err

    ys = filter(predicate, xs)

    with pytest.raises(MyException):
        await run(ys, AsyncAnonymousObserver(asend))

    assert result == []
