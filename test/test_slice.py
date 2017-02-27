import pytest
import logging

from aioreactive.core import AsyncObservable, run, subscribe, AsyncAnonymousObserver

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@pytest.mark.asyncio
async def test_slice_special():
    xs = AsyncObservable.from_iterable([1, 2, 3, 4, 5])
    values = []

    async def asend(value):
        values.append(value)

    ys = xs[1:-1]

    result = await run(ys, AsyncAnonymousObserver(asend))

    assert result == 4
    assert values == [2, 3, 4]


@pytest.mark.asyncio
async def test_slice_step():
    xs = AsyncObservable.from_iterable([1, 2, 3, 4, 5])
    values = []

    async def asend(value):
        values.append(value)

    ys = xs[::2]

    result = await run(ys, AsyncAnonymousObserver(asend))

    assert result == 5
    assert values == [1, 3, 5]
