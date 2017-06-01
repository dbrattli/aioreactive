from asyncio import Future, iscoroutinefunction
from typing import TypeVar, AsyncIterator, AsyncIterable
import logging

from .bases import AsyncObserverBase
from .utils import anoop

log = logging.getLogger(__name__)

T = TypeVar("T")


class AsyncIteratorObserver(AsyncObserverBase, AsyncIterator):

    def __init__(self) -> None:
        super().__init__()

        self._push = Future()  # type: Future
        self._pull = Future()  # type: Future

        self._awaiters = []  # type: List[Future]
        self._busy = False

    async def asend_core(self, value) -> None:
        log.debug("AsyncIteratorObserver:asend(%d)", value)

        await self._serialize_access()

        self._push.set_result(value)
        await self._wait_for_pull()

    async def athrow_core(self, err) -> None:
        await self._serialize_access()

        self._push.set_exception(err)
        await self._wait_for_pull()

    async def aclose_core(self) -> None:
        await self._serialize_access()

        self._push.set_exception(StopAsyncIteration)
        await self._wait_for_pull()

    async def _wait_for_pull(self) -> None:
        await self._pull
        self._pull = Future()
        self._busy = False

    async def _serialize_access(self):
        # Serialize producer event to the iterator
        while self._busy:
            fut = Future()
            self._awaiters.append(fut)
            await fut
            self._awaiters.remove(fut)

        self._busy = True

    async def wait_for_push(self):
            value = await self._push
            self._push = Future()
            self._pull.set_result(True)

            # Wake up any awaiters
            for awaiter in self._awaiters[:1]:
                awaiter.set_result(True)
            return value

    async def __anext__(self):
        return await self.wait_for_push()


class AsyncAnonymousObserver(AsyncObserverBase):
    """An anonymous AsyncObserver.

    Creates as sink where the implementation is provided by three
    optional and anonymous functions, asend, athrow and aclose. Used for
    listening to a source."""

    def __init__(self, asend=anoop, athrow=anoop, aclose=anoop) -> None:
        super().__init__()

        assert iscoroutinefunction(asend)
        self._send = asend

        assert iscoroutinefunction(athrow)
        self._throw = athrow

        assert iscoroutinefunction(aclose)
        self._close = aclose

    async def asend_core(self, value: T) -> None:
        await self._send(value)

    async def athrow_core(self, ex: Exception) -> None:
        await self._throw(ex)

    async def aclose_core(self) -> None:
        await self._close()


class AsyncNoopObserver(AsyncAnonymousObserver):
    """An no operation Async Observer."""

    def __init__(self, asend=anoop, athrow=anoop, aclose=anoop) -> None:
        super().__init__(asend, athrow, aclose)
