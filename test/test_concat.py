import pytest
import asyncio
import logging

from aioreactive.core import run, FuncSink
from aioreactive.producer import Producer
from aioreactive.core.sources.from_iterable import from_iterable
from aioreactive.core.sources.concat import concat

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_concat_happy():
    xs = from_iterable(range(5))
    ys = from_iterable(range(5, 10))
    result = []

    async def asend(value):
        log.debug("test_merge_done:send: ", value)
        result.append(value)

    zs = concat(ys, xs)

    await run(zs, FuncSink(asend))
    assert result == list(range(10))


@pytest.mark.asyncio
async def test_concat_special_add():
    xs = Producer.from_iterable(range(5))
    ys = Producer.from_iterable(range(5, 10))
    result = []

    async def asend(value):
        log.debug("test_merge_done:send: ", value)
        result.append(value)

    zs = xs + ys

    await run(zs, FuncSink(asend))
    assert result == list(range(10))


@pytest.mark.asyncio
async def test_concat_special_iadd():
    xs = Producer.from_iterable(range(5))
    ys = Producer.from_iterable(range(5, 10))
    result = []

    async def asend(value):
        log.debug("test_merge_done:asend(%s)", value)
        result.append(value)

    xs += ys

    await run(xs, FuncSink(asend))
    assert result == list(range(10))

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_concat_happy())
    loop.close()
