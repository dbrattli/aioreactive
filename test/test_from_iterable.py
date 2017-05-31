import pytest
import asyncio
from asyncio import Future

from aioreactive.operators.from_iterable import from_iterable
from aioreactive.core import run, subscribe, AsyncAnonymousObserver


@pytest.mark.asyncio
async def test_from_iterable_happy():
    xs = from_iterable([1, 2, 3])
    result = []

    async def asend(value):
        result.append(value)

    await run(xs, AsyncAnonymousObserver(asend))
    assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_from_iterable_observer_throws():
    xs = from_iterable([1, 2, 3])
    result = []

    async def asend(value):
        result.append(value)
        raise Exception()

    obv = AsyncAnonymousObserver(asend)
    await subscribe(xs, obv)

    try:
        await obv
    except Exception:
        pass
    assert result == [1]


@pytest.mark.asyncio
async def test_from_iterable_close():
    xs = from_iterable(range(100))
    result = []
    sub = None

    async def asend(value):
        result.append(value)
        await sub.adispose()
        await asyncio.sleep(0)

    obv = AsyncAnonymousObserver(asend)
    sub = await subscribe(xs, obv)

    try:
        await obv
    except asyncio.CancelledError:
        pass

    assert result == [0]
