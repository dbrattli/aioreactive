import pytest
import asyncio

from aioreactive.testing import VirtualTimeEventLoop
from aioreactive.core.sources.from_iterable import from_iterable
from aioreactive.core.sources.flat_map import flat_map
from aioreactive.core.sources.unit import unit
from aioreactive.core import AsyncStream, FuncSink, start, run


@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_flap_map_done():
    xs = AsyncStream()
    result = []

    async def asend(value):
        nonlocal result
        result.append(value)

    async def mapper(value):
        return from_iterable([value])

    ys = flat_map(mapper, xs)
    await start(ys, FuncSink(asend))
    await xs.asend(10)
    await xs.asend(20)

    await asyncio.sleep(0.6)

    assert result == [10, 20]


@pytest.mark.asyncio
async def test_flat_map_monad():
    m = unit(42)

    a = await run(flat_map(lambda x: unit(x * 10), m))
    b = await run(unit(420))
    assert a == b


@pytest.mark.asyncio
async def test_flat_map_monad_law_left_identity():
    # return x >>= f is the same thing as f x

    x = 3

    def f(x):
        return unit(x + 100000)

    a = await run(flat_map(f, unit(x)))
    b = await run(f(x))

    assert a == b


@pytest.mark.asyncio
async def test_flat_map_monad_law_right_identity():
    # m >>= return is no different than just m.

    m = unit("move on up")

    a = await run(flat_map(unit, m))
    b = await run(m)

    assert a == b


@pytest.mark.asyncio
async def test_flat_map_monad_law_associativity():
    # (m >>= f) >>= g is just like doing m >>= (\x -> f x >>= g)

    m = unit(42)

    def f(x):
        return unit(x + 1000)

    def g(y):
        return unit(y * 333)

    a = await run(flat_map(g, flat_map(f, m)))
    b = await run(flat_map(lambda x: flat_map(g, f(x)), m))

    assert a == b

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_flat_map_monad())
    loop.close()
