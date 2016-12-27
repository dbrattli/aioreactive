import pytest
import asyncio
import logging

from aioreactive.testing import VirtualTimeEventLoop
from aioreactive.core.operators.unit import unit
from aioreactive.core import run, subscribe
from aioreactive.testing import AnonymousAsyncObserver

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_unit_happy():
    xs = unit(42)
    result = []

    async def asend(value):
        result.append(value)

    await run(xs, AnonymousAsyncObserver(asend))
    assert result == [42]


@pytest.mark.asyncio
async def test_unit_observer_throws():
    error = Exception("error")
    xs = unit(42)
    result = []

    def asend(value):
        result.append(value)
        raise error

    sub = await subscribe(xs, AnonymousAsyncObserver(asend))

    try:
        await sub
    except Exception as ex:
        assert ex == error
    assert result == [42]


@pytest.mark.asyncio
async def test_unit_close():
    xs = unit(42)
    result = []
    sub = None

    async def asend(value):
        result.append(value)
        sub.cancel()
        await asyncio.sleep(0)

    sub = await subscribe(xs, AnonymousAsyncObserver(asend))

    try:
        await sub
    except asyncio.CancelledError:
        pass

    assert result == [42]


@pytest.mark.asyncio
async def test_unit_happy_resolved_future():
    fut = asyncio.Future()
    xs = unit(fut)
    fut.set_result(42)

    lis = AnonymousAsyncObserver()
    await run(xs, lis)
    assert lis.values == [(0, 42), (0, )]


@pytest.mark.asyncio
async def test_unit_happy_future_resolve():
    fut = asyncio.Future()
    xs = unit(fut)

    lis = AnonymousAsyncObserver()
    sub = await subscribe(xs, lis)
    fut.set_result(42)
    await sub
    assert lis.values == [(0, 42), (0, )]


@pytest.mark.asyncio
async def test_unit_future_exception():
    fut = asyncio.Future()
    ex = Exception("ex")
    xs = unit(fut)

    lis = AnonymousAsyncObserver()
    sub = await subscribe(xs, lis)
    fut.set_exception(ex)
    with pytest.raises(Exception):
        await sub
    assert lis.values == [(0, ex)]


@pytest.mark.asyncio
async def test_unit_future_cancel():
    fut = asyncio.Future()
    xs = unit(fut)

    lis = AnonymousAsyncObserver()
    sub = await subscribe(xs, lis)
    fut.cancel()
    with pytest.raises(asyncio.CancelledError):
        await sub
    assert lis.values == [(0,)]
