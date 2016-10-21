from asyncio import Future, iscoroutinefunction
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
        self._push = Future()  # type: Future
        self._pull = Future()  # type: Future

    async def asend(self, value) -> None:
        log.debug("AsyncStreamIterator:asend(%d)" % value)
        self._push.set_result(value)
        await self._wait_for_pull()

    async def athrow(self, err) -> None:
        self._push.set_exception(err)
        await self._wait_for_pull()

    async def aclose(self) -> None:
        self._push.set_exception(StopAsyncIteration)
        await self._wait_for_pull()

    async def __anext__(self):
        return await self._wait_for_push()

    async def _wait_for_push(self):
        value = await self._push
        self._push = Future()
        self._pull.set_result(True)
        return value

    async def _wait_for_pull(self) -> None:
        await self._pull
        self._pull = Future()


class FuncSink(AsyncSink):
    """An anonymous AsyncSink.

    Creates as sink where the implementation is provided by three
    optional and anonymous functions, send, throw and close. Used for
    listening to asource."""

    def __init__(self, asend=anoop, athrow=anoop, aclose=anoop) -> None:
        super().__init__()

        assert iscoroutinefunction(asend)
        self._send = asend

        assert iscoroutinefunction(athrow)
        self._throw = athrow

        assert iscoroutinefunction(aclose)
        self._close = aclose

    async def asend(self, value: T):
        await self._send(value)

    async def athrow(self, ex: Exception):
        await self._throw(ex)

    async def aclose(self):
        await self._close()
