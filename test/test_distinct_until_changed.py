import pytest

from aioreactive.testing import VirtualTimeEventLoop
from aioreactive.core import run, subscribe
from aioreactive.operators import from_iterable, distinct_until_changed
from aioreactive.testing import AsyncAnonymousObserver


class MyException(Exception):
    pass


@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_distinct_until_changed_different():
    xs = from_iterable([1, 2, 3])

    obv = AsyncAnonymousObserver()
    ys = distinct_until_changed(xs)

    await run(ys, obv)
    assert obv.values == [
        (0, 1),
        (0, 2),
        (0, 3),
        (0, )]


@pytest.mark.asyncio
async def test_distinct_until_changed_changed():
    xs = from_iterable([1, 2, 2, 1, 3, 3, 1, 2, 2])

    obv = AsyncAnonymousObserver()
    ys = distinct_until_changed(xs)

    await run(ys, obv)
    assert obv.values == [
        (0, 1),
        (0, 2),
        (0, 1),
        (0, 3),
        (0, 1),
        (0, 2),
        (0, )]
