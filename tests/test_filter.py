import asyncio
from typing import Any, Generator

import pytest
from expression.core import pipe

import aioreactive as rx
from aioreactive.testing import VirtualTimeEventLoop


class MyException(Exception):
    pass


class EventLoopPolicy(asyncio.DefaultEventLoopPolicy):
    def get_event_loop(self) -> asyncio.AbstractEventLoop:
       return VirtualTimeEventLoop()

@pytest.fixture(scope="module")  # type: ignore
def event_loop_policy():
    return EventLoopPolicy()


@pytest.mark.asyncio(loop_scope="module")
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


@pytest.mark.asyncio(loop_scope="module")
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
