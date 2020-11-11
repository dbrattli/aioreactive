import aioreactive as rx
import pytest
from aioreactive.notification import OnCompleted, OnNext
from aioreactive.testing import AsyncTestObserver, VirtualTimeEventLoop
from aioreactive.types import AsyncObservable
from expression.core import pipe


@pytest.yield_fixture()  # type: ignore
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_flap_map_done():
    xs: rx.AsyncSubject[int] = rx.AsyncSubject()

    def mapper(value: int) -> rx.AsyncObservable[int]:
        return rx.from_iterable([value])

    ys = pipe(xs, rx.flat_map(mapper))

    obv = AsyncTestObserver()
    await ys.subscribe_async(obv)

    await xs.asend(10)
    await xs.asend(20)
    await xs.aclose()
    await obv

    assert obv.values == [(0, OnNext(10)), (0, OnNext(20)), (0, OnCompleted)]


@pytest.mark.asyncio
async def test_flat_map_monad():
    m = rx.single(42)

    def mapper(x: int) -> AsyncObservable[int]:
        return rx.single(x * 10)

    a = await rx.run(pipe(m, rx.flat_map(mapper)))
    b = await rx.run(rx.single(420))

    assert a == b


@pytest.mark.asyncio
async def test_flat_map_monad_law_left_identity():
    # return x >>= f is the same thing as f x

    x = 3

    def f(x: int) -> AsyncObservable[int]:
        return rx.single(x + 100000)

    a = await rx.run(pipe(rx.single(x), rx.flat_map(f)))
    b = await rx.run(f(x))

    assert a == b


@pytest.mark.asyncio
async def test_flat_map_monad_law_right_identity():
    # m >>= return is no different than just m.

    m = rx.single("move on up")

    def mapper(x: str) -> AsyncObservable[str]:
        return rx.single(x)

    a = await rx.run(pipe(m, rx.flat_map(mapper)))
    b = await rx.run(m)

    assert a == b


@pytest.mark.asyncio
async def test_flat_map_monad_law_associativity():
    # (m >>= f) >>= g is just like doing m >>= (\x -> f x >>= g)

    m = rx.single(42)

    def f(x: int) -> AsyncObservable[int]:
        return rx.single(x + 1000)

    def g(y: int) -> AsyncObservable[int]:
        return rx.single(y * 333)

    def h(x: int) -> AsyncObservable[int]:
        return pipe(f(x), rx.flat_map(g))

    zs = pipe(m, rx.flat_map(f))
    a = await rx.run(pipe(zs, rx.flat_map(g)))

    b = await rx.run(pipe(m, rx.flat_map(h)))

    assert a == b


# if __name__ == "__main__":
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(test_flat_map_monad())
#     loop.close()
