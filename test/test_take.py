import pytest
import logging
from asyncio import Future, CancelledError

from aioreactive.core.operators.take import take
from aioreactive.core import AsyncObservable, run, subscribe, AnonymousAsyncObserver

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@pytest.mark.asyncio
async def test_take_zero():
    xs = AsyncObservable.from_iterable([1, 2, 3, 4, 5])
    values = []

    async def asend(value):
        values.append(value)

    ys = take(0, xs)

    with pytest.raises(CancelledError):
        await run(ys, AnonymousAsyncObserver(asend))

    assert values == []


@pytest.mark.asyncio
async def test_take_empty():
    xs = AsyncObservable.empty()
    values = []

    async def asend(value):
        values.append(value)

    ys = take(42, xs)

    with pytest.raises(CancelledError):
        await run(ys, AnonymousAsyncObserver(asend))

    assert values == []


@pytest.mark.asyncio
async def test_take_negative():
    xs = AsyncObservable.from_iterable([1, 2, 3, 4, 5])
    values = []

    async def asend(value):
        values.append(value)

    with pytest.raises(ValueError):
        take(-1, xs)


@pytest.mark.asyncio
async def test_take_normal():
    xs = AsyncObservable.from_iterable([1, 2, 3, 4, 5])
    values = []

    async def asend(value):
        values.append(value)

    ys = take(2, xs)

    result = await run(ys, AnonymousAsyncObserver(asend))

    assert result == 2
    assert values == [1, 2]
