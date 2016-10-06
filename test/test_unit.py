import pytest
import asyncio

from aioreactive.testing import VirtualTimeEventLoop
from aioreactive.ops.unit import unit
from aioreactive.core import run, listen
from aioreactive.testing import Listener


@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_unit_happy():
    xs = unit(42)
    result = []

    async def send(value):
        result.append(value)

    await run(xs, Listener(send))
    assert result == [42]


@pytest.mark.asyncio
async def test_unit_sink_throws():
    error = Exception("error")
    xs = unit(42)
    result = []

    def send(value):
        result.append(value)
        raise error

    sub = await listen(xs, Listener(send))

    try:
        await sub
    except Exception as ex:
        print("Error -----")
        assert ex == error
    assert result == [42]


@pytest.mark.asyncio
async def test_unit_close():
    xs = unit(42)
    result = []
    sub = None

    async def send(value):
        result.append(value)
        sub.cancel()
        await asyncio.sleep(0)

    sub = await listen(xs, Listener(send))

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

    lis = Listener()
    await run(xs, lis)
    assert lis.values == [(0, 42), (0, )]


@pytest.mark.asyncio
async def test_unit_happy_future_resolve():
    fut = asyncio.Future()
    xs = unit(fut)

    lis = Listener()
    sub = await listen(xs, lis)
    fut.set_result(42)
    await sub
    assert lis.values == [(0, 42), (0, )]


@pytest.mark.asyncio
async def test_unit_future_exception():
    fut = asyncio.Future()
    ex = Exception("ex")
    xs = unit(fut)

    lis = Listener()
    sub = await listen(xs, lis)
    fut.set_exception(ex)
    with pytest.raises(Exception):
        await sub
    assert lis.values == [(0, ex)]


@pytest.mark.asyncio
async def test_unit_future_cancel():
    fut = asyncio.Future()
    xs = unit(fut)

    lis = Listener()
    sub = await listen(xs, lis)
    fut.cancel()
    with pytest.raises(asyncio.CancelledError):
        await sub
    assert lis.values == [(0,)]
