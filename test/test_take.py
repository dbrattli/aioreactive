import pytest
import logging
from asyncio import Future, CancelledError

from aioreactive.operators.take import take
from aioreactive.core import AsyncObservable, run, subscribe, AsyncAnonymousObserver

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@pytest.mark.asyncio
async def test_take_zero() -> None:
    xs = AsyncObservable.from_iterable([1, 2, 3, 4, 5])
    values = []

    async def asend(value) -> None:
        values.append(value)

    ys = take(0, xs)

    with pytest.raises(CancelledError):
        await run(ys, AsyncAnonymousObserver(asend))

    assert values == []


@pytest.mark.asyncio
async def test_take_empty() -> None:
    xs = AsyncObservable.empty()
    values = []

    async def asend(value) -> None:
        values.append(value)

    ys = take(42, xs)

    with pytest.raises(CancelledError):
        await run(ys, AsyncAnonymousObserver(asend))

    assert values == []


@pytest.mark.asyncio
async def test_take_negative() -> None:
    xs = AsyncObservable.from_iterable([1, 2, 3, 4, 5])
    values = []

    async def asend(value) -> None:
        values.append(value)

    with pytest.raises(ValueError):
        take(-1, xs)


@pytest.mark.asyncio
async def test_take_normal() -> None:
    xs = AsyncObservable.from_iterable([1, 2, 3, 4, 5])
    values = []

    async def asend(value) -> None:
        values.append(value)

    ys = take(2, xs)

    result = await run(ys, AsyncAnonymousObserver(asend))

    assert result == 2
    assert values == [1, 2]
