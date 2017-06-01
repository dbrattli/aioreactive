import pytest
import asyncio

from aioreactive.testing import VirtualTimeEventLoop
from aioreactive.operators import from_iterable, flat_map, unit
from aioreactive.core import AsyncStream, subscribe, run
from aioreactive.testing import AsyncAnonymousObserver


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

    obv = AsyncAnonymousObserver()
    await subscribe(ys, obv)
    await xs.asend(10)
    await xs.asend(20)
    await xs.aclose()

    await obv

    assert obv.values == [
        (0, 10),
        (0, 20),
        (0, )]


@pytest.mark.asyncio
async def test_flat_map_monad():
    m = unit(42)

    async def mapper(x):
        return unit(x * 10)

    a = await run(flat_map(mapper, m))
    b = await run(unit(420))
    assert a == b


@pytest.mark.asyncio
async def test_flat_map_monad_law_left_identity():
    # return x >>= f is the same thing as f x

    x = 3

    async def f(x):
        return unit(x + 100000)

    a = await run(flat_map(f, unit(x)))
    b = await run(await f(x))

    assert a == b


@pytest.mark.asyncio
async def test_flat_map_monad_law_right_identity():
    # m >>= return is no different than just m.

    m = unit("move on up")

    async def aunit(x):
        return unit(x)

    a = await run(flat_map(aunit, m))
    b = await run(m)

    assert a == b


@pytest.mark.asyncio
async def test_flat_map_monad_law_associativity():
    # (m >>= f) >>= g is just like doing m >>= (\x -> f x >>= g)

    m = unit(42)

    async def f(x):
        return unit(x + 1000)

    async def g(y):
        return unit(y * 333)

    async def h(x):
        return flat_map(g, await f(x))

    zs = flat_map(f, m)
    a = await run(flat_map(g, zs))

    b = await run(flat_map(h, m))

    assert a == b

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_flat_map_monad())
    loop.close()
