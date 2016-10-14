import pytest
import asyncio

from aioreactive.testing import VirtualTimeEventLoop
from aioreactive.core.sources.from_iterable import from_iterable
from aioreactive.core.sources.flat_map import flat_map
from aioreactive.core.sources.unit import unit
from aioreactive.core import listen, Listener, Stream


@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_flap_map_done():
    xs = Stream()
    result = []

    async def send(value):
        nonlocal result
        result.append(value)

    async def mapper(value):
        return from_iterable([value])

    ys = flat_map(mapper, xs)
    sub = await listen(ys, Listener(send))
    await xs.send(10)
    await xs.send(20)

    await asyncio.sleep(0.6)

    assert result == [10, 20]


# def test_flat_map_monad(self):
#         m = unit(42)
#         f = lambda x: unit(x*10)

#         assert [async for m.bind(f) == unit(420)

#     def test_identity_monad_law_left_identity(self):
#         # return x >>= f is the same thing as f x

#         f = lambda x: unit(x+100000)
#         x = 3

#         self.assertEqual(
#             unit(x).bind(f),
#             f(x)
#         )

#     def test_identity_monad_law_right_identity(self):
#         # m >>= return is no different than just m.

#         m = unit("move on up")

#         self.assertEqual(
#             m.bind(unit),
#             m
#         )

#     def test_identity_monad_law_associativity(self):
#         # (m >>= f) >>= g is just like doing m >>= (\x -> f x >>= g)
#         m = unit(42)
#         f = lambda x: unit(x+1000)
#         g = lambda y: unit(y*42)

#         self.assertEqual(
#             m.bind(f).bind(g),
#             m.bind(lambda x: f(x).bind(g))
#         )
