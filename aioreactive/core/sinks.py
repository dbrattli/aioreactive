from asyncio import Future
from typing import TypeVar, AsyncIterator
import logging

from .typing import AsyncSink
from .utils import anoop

log = logging.getLogger(__name__)

T = TypeVar("T")


class AsyncIteratorSink(AsyncIterator, AsyncSink):
    """AsyncIterator that is also an AsyncSink.

    Uses for listening to an async source using an async iterator."""

    def __init__(self) -> None:
        super().__init__()
        self._future = Future()
        self._wait = Future()

    async def send(self, value) -> None:
        self._future.set_result(value)
        await self._pong()

    async def throw(self, err) -> None:
        self._future.set_exception(err)
        await self._pong()

    async def close(self) -> None:
        self._future.set_exception(StopAsyncIteration)
        await self._pong()

    async def __anext__(self):
        return await self._ping()

    async def _ping(self):
        value = await self._future
        self._future = Future()
        self._wait.set_result(True)
        return value

    async def _pong(self) -> None:
        await self._wait
        self._wait = Future()


class Listener(AsyncSink):
    """An anonymous AsyncSink.

    Creates as sink where the implementation is provided by three
    optional and anonymous functions, send, throw and close. Used for
    listening to asource."""

    def __init__(self, send=anoop, throw=anoop, close=anoop) -> None:
        super().__init__()
        self._send = send
        self._throw = throw
        self._close = close

    async def send(self, value: T):
        await self._send(value)

    async def throw(self, ex: Exception):
        await self._throw(ex)

    async def close(self):
        await self._close()
