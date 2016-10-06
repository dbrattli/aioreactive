import pytest
from asyncio import Future, CancelledError

from aioreactive.ops.take import take
from aioreactive.core import run, listen, Listener, Stream
from aioreactive.producer import Producer


@pytest.mark.asyncio
async def test_take_zero():
    xs = Producer.from_iterable([1, 2, 3, 4, 5])
    values = []

    async def send(value):
        values.append(value)

    ys = take(0, xs)

    with pytest.raises(CancelledError):
        await run(ys, Listener(send))

    assert values == []


@pytest.mark.asyncio
async def test_take_empty():
    xs = Producer.empty()
    values = []

    async def send(value):
        values.append(value)

    ys = take(42, xs)

    with pytest.raises(CancelledError):
        await run(ys, Listener(send))

    assert values == []


@pytest.mark.asyncio
async def test_take_negative():
    xs = Producer.from_iterable([1, 2, 3, 4, 5])
    values = []

    async def send(value):
        values.append(value)

    with pytest.raises(ValueError):
        take(-1, xs)


@pytest.mark.asyncio
async def test_take_normal():
    xs = Producer.from_iterable([1, 2, 3, 4, 5])
    values = []

    async def send(value):
        values.append(value)

    ys = take(2, xs)

    result = await run(ys, Listener(send))

    assert result == 2
    assert values == [1, 2]
