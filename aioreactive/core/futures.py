import logging
from asyncio import Future
from typing import TypeVar, Callable, Generic
from typing import AsyncIterable, AsyncIterator

from .typing import AsyncSink, AsyncSource
from .utils import noopsink
from .sinks import AsyncIteratorSink

log = logging.getLogger(__name__)

T = TypeVar('T')


class AsyncMultiFuture(Future, AsyncSink, Generic[T]):

    """An asynch multi-value future.

    Both a future and async sink. The future resolves with the last
    value before the sink is closed. A close without any values sent is
    the same as cancelling the future.
    """

    def __init__(self) -> None:
        Future.__init__(self)

        self._has_result = False
        self._last_result = None  # type: T

        self._sink = noopsink  # type: AsyncSink

    async def send(self, value: T):
        if self.done():
            return

        self._last_result = value
        self._has_result = True

        await self._sink.send(value)

    async def throw(self, ex: Exception) -> None:
        if self.done():
            return

        self.set_exception(ex)
        await self._sink.throw(ex)

    async def close(self) -> None:
        if self.done():
            return

        if self._has_result:
            self.set_result(self._last_result)
        else:
            self.cancel()

        await self._sink.close()

    async def __alisten__(self, sink: AsyncSink) -> "AsyncMultiFuture":
        self._sink = sink
        return self


class Subscription(AsyncMultiFuture, AsyncIterator):
    """Subscription class.

    A subscription is an async multi value future with a context
    manager.

    Unsubscribe -- To unsubscribe you need to call the cancel() method.
    """

    def __init__(self, cancel: Callable=None) -> None:
        super().__init__()

        if callable(cancel):
            self.add_done_callback(cancel)

    def __enter__(self):
        """Context management protocol."""
        return self

    def __exit__(self, type, value, traceback):
        """Context management protocol."""
        if not self.done():
            self.cancel()

    async def __aiter__(self) -> AsyncIterator:
        """Iterate source stream asynchronously.

        Transforms the async source to an async iterable. The source
        will await for the iterator to pick up the value before
        continuing to avoid queuing values.
        """

        _sink = AsyncIteratorSink()
        await chain(self, _sink)
        return _sink


async def chain(source, sink):
    """Chains an async sink with an async source.

    Performs the chaining done internally by most operators."""

    return await source.__alisten__(sink)


def chain_future(fut: Future, other: Future) -> Future:
    """Chains a future with other future.

    Returns the first future.
    """

    def done(fut):
        if other.done():
            return

        if fut.cancelled():
            other.cancel()
            return

        if fut.exception() is not None:
            other.set_exception(fut.exception())
            return

        other.set_result(fut.result())
    fut.add_done_callback(done)
    return fut
