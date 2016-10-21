import pytest
import logging

from aioreactive.core import run, start, FuncSink
from aioreactive.producer import Producer

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@pytest.mark.asyncio
async def test_slice_special():
    xs = Producer.from_iterable([1, 2, 3, 4, 5])
    values = []

    async def asend(value):
        values.append(value)

    ys = xs[1:-1]

    result = await run(ys, FuncSink(asend))

    assert result == 4
    assert values == [2, 3, 4]


@pytest.mark.asyncio
async def test_slice_step():
    xs = Producer.from_iterable([1, 2, 3, 4, 5])
    values = []

    async def asend(value):
        values.append(value)

    ys = xs[::2]

    result = await run(ys, FuncSink(asend))

    assert result == 5
    assert values == [1, 3, 5]
