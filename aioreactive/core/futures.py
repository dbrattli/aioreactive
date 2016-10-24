import logging
from asyncio import Future
from typing import TypeVar, Generic

from aioreactive.core.abc import Cancellable
from .typing import AsyncSink

log = logging.getLogger(__name__)

T = TypeVar('T')


class AsyncMultiFuture(Future, AsyncSink, Cancellable, Generic[T]):

    """An async multi-value future.

    Both a future and async sink. The future resolves with the last
    value before the sink is closed. A close without any values sent is
    the same as cancelling the future.
    """

    def __init__(self) -> None:
        super().__init__()

        self._has_result = False
        self._last_result = None  # type: T

    async def asend(self, value: T) -> None:
        self._last_result = value
        self._has_result = True

    async def athrow(self, ex: Exception) -> None:
        if self.done():
            return

        self.set_exception(ex)

    async def aclose(self) -> None:
        if self._has_result:
            self.set_result(self._last_result)
        else:
            self.cancel()


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
