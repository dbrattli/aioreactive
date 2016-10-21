import pytest
import asyncio

from aioreactive.testing import VirtualTimeEventLoop
from aioreactive.core.sources.from_iterable import from_iterable
from aioreactive.core.sources.filter import filter
from aioreactive.core import run, start, FuncSink, AsyncStream


class MyException(Exception):
    pass


@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_filter_happy():
    xs = from_iterable([1, 2, 3])
    result = []

    async def asend(value):
        result.append(value)

    async def predicate(value):
        await asyncio.sleep(0.1)
        return value > 1

    ys = filter(predicate, xs)
    value = await run(ys, FuncSink(asend))
    assert value == 3
    assert result == [2, 3]


@pytest.mark.asyncio
async def test_filter_predicate_throws():
    xs = from_iterable([1, 2, 3])
    err = MyException("err")
    result = []

    async def asend(value):
        result.append(value)

    async def predicate(value):
        await asyncio.sleep(0.1)
        raise err

    ys = filter(predicate, xs)

    with pytest.raises(MyException):
        await run(ys, FuncSink(asend))

    assert result == []
