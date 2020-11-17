import logging
from asyncio import CancelledError, Future

import aioreactive as rx
import pytest
from aioreactive.testing import AsyncTestObserver

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@pytest.mark.asyncio
async def test_take_zero() -> None:
    xs = rx.from_iterable([1, 2, 3, 4, 5])
    values = []

    async def asend(value) -> None:
        values.append(value)

    ys = take(0, xs)

    with pytest.raises(CancelledError):
        await run(ys, AsyncTestObserver(asend))

    assert values == []


@pytest.mark.asyncio
async def test_take_empty() -> None:
    xs = rx.empty()
    values = []

    async def asend(value) -> None:
        values.append(value)

    ys = take(42, xs)

    with pytest.raises(CancelledError):
        await run(ys, AsyncTestObserver(asend))

    assert values == []


@pytest.mark.asyncio
async def test_take_negative() -> None:
    xs = rx.from_iterable([1, 2, 3, 4, 5])
    values = []

    async def asend(value) -> None:
        values.append(value)

    with pytest.raises(ValueError):
        take(-1, xs)


@pytest.mark.asyncio
async def test_take_normal() -> None:
    xs = rx.from_iterable([1, 2, 3, 4, 5])
    values = []

    async def asend(value) -> None:
        values.append(value)

    ys = take(2, xs)

    result = await run(ys, AsyncTestObserver(asend))

    assert result == 2
    assert values == [1, 2]
