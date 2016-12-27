from asyncio import Future, iscoroutinefunction
from asyncio.locks import Event
from typing import TypeVar, AsyncIterator
import logging

from .typing import AsyncObserver
from .utils import anoop

log = logging.getLogger(__name__)

T = TypeVar("T")


class AsyncIteratorObserver(AsyncIterator, AsyncObserver):
    """AsyncIterator that is also an AsyncObserver.

    Uses for listening to an async source using an async iterator."""

    def __init__(self) -> None:
        super().__init__()
        self._push = Future()  # type: Future
        self._pull = Future()  # type: Future

        self._awaiters = []  # type: List[Future]
        self._busy = False

    async def asend(self, value) -> None:
        log.debug("AsyncIteratorObserver:asend(%d)", value)
        #assert not self._push.done()

        await self._serialize_access()

        self._push.set_result(value)
        await self._wait_for_pull()

    async def athrow(self, err) -> None:
        await self._serialize_access()

        self._push.set_exception(err)
        await self._wait_for_pull()

    async def aclose(self) -> None:
        await self._serialize_access()

        self._push.set_exception(StopAsyncIteration)
        await self._wait_for_pull()

    async def __anext__(self):
        return await self._wait_for_push()

    async def _serialize_access(self):
        # Serialize producer event to the iterator
        while self._busy:
            fut = Future()
            self._awaiters.append(fut)
            await fut
            self._awaiters.remove(fut)

        self._busy = True

    async def _wait_for_push(self):
        value = await self._push
        self._push = Future()
        self._pull.set_result(True)

        # Wake up any awaiters
        for awaiter in self._awaiters[:1]:
            awaiter.set_result(True)
        return value

    async def _wait_for_pull(self) -> None:
        await self._pull
        self._pull = Future()
        self._busy = False


class AnonymousAsyncObserver(AsyncObserver):
    """An anonymous AsyncObserver.

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
