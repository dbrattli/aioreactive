import asyncio
from functools import partial

import pytest

from aioreactive.testing import VirtualTimeEventLoop


class EventLoopPolicy(asyncio.DefaultEventLoopPolicy):
    def get_event_loop(self) -> asyncio.AbstractEventLoop:
       return VirtualTimeEventLoop()

@pytest.fixture(scope="module")  # type: ignore
def event_loop_policy():
    return EventLoopPolicy()


@pytest.mark.asyncio(loop_scope="module")
async def test_sleep():
    loop = asyncio.get_event_loop()
    await asyncio.sleep(100)
    assert loop.time() == 100
    await asyncio.sleep(100)
    assert loop.time() == 200


@pytest.mark.asyncio(loop_scope="module")
async def test_call_soon():
    result: list[int] = []

    def action(value: int) -> None:
        result.append(value)

    loop = asyncio.get_event_loop()
    loop.call_soon(partial(action, 1))
    loop.call_soon(partial(action, 2))
    loop.call_soon(partial(action, 3))
    await asyncio.sleep(10)
    assert result == [1, 2, 3]


@pytest.mark.asyncio(loop_scope="module")
async def test_call_later():
    result: list[int] = []

    def action(value: int) -> None:
        result.append(value)

    loop = asyncio.get_event_loop()
    loop.call_later(10, partial(action, 1))
    loop.call_later(1, partial(action, 2))
    loop.call_later(5, partial(action, 3))
    await asyncio.sleep(10)
    assert result == [2, 3, 1]


@pytest.mark.asyncio(loop_scope="module")
async def test_call_at():
    result: list[int] = []

    def action(value: int) -> None:
        result.append(value)

    loop = asyncio.get_event_loop()
    loop.call_later(10, partial(action, 1))
    loop.call_later(1, partial(action, 2))
    loop.call_later(5, partial(action, 3))
    await asyncio.sleep(10)
    assert result == [2, 3, 1]


@pytest.mark.asyncio(loop_scope="module")
async def test_cancel():
    result: list[int] = []

    def action(value: int) -> None:
        result.append(value)

    loop = asyncio.get_event_loop()
    hdl = loop.call_later(10, partial(action, 1))
    loop.call_later(1, partial(action, 2))
    hdl.cancel()
    loop.call_later(5, partial(action, 3))
    await asyncio.sleep(10)
    assert result == [2, 3]
