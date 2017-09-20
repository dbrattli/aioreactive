
from asyncio import Future
from typing import TypeVar, Generic
from abc import abstractmethod
import logging
from aioreactive.abc import Disposable
from .typing import AsyncObserver

log = logging.getLogger(__name__)

T = TypeVar('T')


class AsyncObserverBase(Future, AsyncObserver[T], Disposable, Generic[T]):

    """An async observer abstract base class.

    Both a future and async observer. The future resolves with the last
    value before the observer is closed. A close without any values sent
    is the same as cancelling the future."""

    def __init__(self) -> None:
        super().__init__()

        self._has_value = False
        self._last_value = None  # type: T

        self._is_stopped = False

    async def asend(self, value: T) -> None:
        log.debug("AsyncObserverBase:asend(%s)", value)

        if self._is_stopped:
            log.debug("Closed!!")
            return

        self._last_value = value
        self._has_value = True

        await self.asend_core(value)

    async def athrow(self, ex: Exception) -> None:
        if self._is_stopped:
            return

        self._is_stopped = True

        self.set_exception(ex)
        await self.athrow_core(ex)

    async def aclose(self) -> None:
        log.debug("AsyncObserverBase:aclose")

        if self._is_stopped:
            log.debug("Closed!!")
            return

        self._is_stopped = True

        if self._has_value:
            self.set_result(self._last_value)
        else:
            self.cancel()

        await self.aclose_core()

    def dispose(self) -> None:
        self._is_stopped = True

    @abstractmethod
    async def asend_core(self, value: T) -> None:
        return NotImplemented

    @abstractmethod
    async def athrow_core(self, error) -> None:
        return NotImplemented

    @abstractmethod
    async def aclose_core(self) -> None:
        return NotImplemented
