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
        self._future = Future()  # type: Future
        self._wait = Future()  # type: Future

    async def asend(self, value) -> None:
        self._future.set_result(value)
        await self._pong()

    async def athrow(self, err) -> None:
        self._future.set_exception(err)
        await self._pong()

    async def aclose(self) -> None:
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

    def __init__(self, asend=anoop, athrow=anoop, aclose=anoop) -> None:
        super().__init__()
        self._send = asend
        self._throw = athrow
        self._close = aclose

    async def asend(self, value: T):
        await self._send(value)

    async def athrow(self, ex: Exception):
        await self._throw(ex)

    async def aclose(self):
        await self._close()
