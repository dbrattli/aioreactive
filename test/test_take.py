import pytest
import logging
from asyncio import Future, CancelledError

from aioreactive.core.sources.take import take
from aioreactive.core import run, start, FuncSink
from aioreactive.producer import Producer

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@pytest.mark.asyncio
async def test_take_zero():
    xs = Producer.from_iterable([1, 2, 3, 4, 5])
    values = []

    async def asend(value):
        values.append(value)

    ys = take(0, xs)

    with pytest.raises(CancelledError):
        await run(ys, FuncSink(asend))

    assert values == []


@pytest.mark.asyncio
async def test_take_empty():
    xs = Producer.empty()
    values = []

    async def asend(value):
        values.append(value)

    ys = take(42, xs)

    with pytest.raises(CancelledError):
        await run(ys, FuncSink(asend))

    assert values == []


@pytest.mark.asyncio
async def test_take_negative():
    xs = Producer.from_iterable([1, 2, 3, 4, 5])
    values = []

    async def asend(value):
        values.append(value)

    with pytest.raises(ValueError):
        take(-1, xs)


@pytest.mark.asyncio
async def test_take_normal():
    xs = Producer.from_iterable([1, 2, 3, 4, 5])
    values = []

    async def asend(value):
        values.append(value)

    ys = take(2, xs)

    result = await run(ys, FuncSink(asend))

    assert result == 2
    assert values == [1, 2]
