import asyncio
from functools import partial

import pytest
from aioreactive.testing import VirtualTimeEventLoop


@pytest.yield_fixture()  # type: ignore
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_sleep():
    loop = asyncio.get_event_loop()
    await asyncio.sleep(100)
    assert loop.time() == 100
    await asyncio.sleep(100)
    assert loop.time() == 200


@pytest.mark.asyncio
async def test_call_soon():
    result = []

    def action(value: int) -> None:
        result.append(value)

    loop = asyncio.get_event_loop()
    loop.call_soon(partial(action, 1))
    loop.call_soon(partial(action, 2))
    loop.call_soon(partial(action, 3))
    await asyncio.sleep(10)
    assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_call_later():
    result = []

    def action(value: int) -> None:
        result.append(value)

    loop = asyncio.get_event_loop()
    loop.call_later(10, partial(action, 1))
    loop.call_later(1, partial(action, 2))
    loop.call_later(5, partial(action, 3))
    await asyncio.sleep(10)
    assert result == [2, 3, 1]


@pytest.mark.asyncio
async def test_call_at():
    result = []

    def action(value: int) -> None:
        result.append(value)

    loop = asyncio.get_event_loop()
    loop.call_later(10, partial(action, 1))
    loop.call_later(1, partial(action, 2))
    loop.call_later(5, partial(action, 3))
    await asyncio.sleep(10)
    assert result == [2, 3, 1]


@pytest.mark.asyncio
async def test_cancel():
    result = []

    def action(value: int) -> None:
        result.append(value)

    loop = asyncio.get_event_loop()
    hdl = loop.call_later(10, partial(action, 1))
    loop.call_later(1, partial(action, 2))
    hdl.cancel()
    loop.call_later(5, partial(action, 3))
    await asyncio.sleep(10)
    assert result == [2, 3]
