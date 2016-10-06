import pytest
import asyncio
from asyncio import Future

from aioreactive.ops.from_iterable import from_iterable
from aioreactive.core import run, listen, Listener


@pytest.mark.asyncio
async def test_from_iterable_happy():
    xs = from_iterable([1, 2, 3])
    result = []

    async def send(value):
        result.append(value)

    await run(xs, Listener(send))
    assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_from_iterable_sink_throws():
    xs = from_iterable([1, 2, 3])
    result = []

    def send(value):
        result.append(value)
        raise Exception()

    sub = await listen(xs, Listener(send))

    try:
        await sub
    except:
        pass
    assert result == [1]


@pytest.mark.asyncio
async def test_from_iterable_close():
    xs = from_iterable(range(100))
    result = []
    sub = None

    async def send(value):
        result.append(value)
        sub.cancel()
        await asyncio.sleep(0)

    sub = await listen(xs, Listener(send))

    try:
        await sub
    except asyncio.CancelledError:
        pass

    assert result == [0]
