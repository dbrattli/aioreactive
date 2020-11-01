import logging
from abc import abstractmethod
from asyncio import Future
from typing import Optional, TypeVar

from fslash.system import Disposable

from .types import AsyncObserver

log = logging.getLogger(__name__)

TSource = TypeVar("TSource")


class AsyncObserverBase(Future[TSource], AsyncObserver[TSource], Disposable):
    """An async observer abstract base class.

    Both a future and async observer. The future resolves with the last
    value before the observer is closed. A close without any values sent
    is the same as cancelling the future."""

    def __init__(self) -> None:
        super().__init__()

        self._has_value = False
        self._last_value: Optional[TSource] = None

        self._is_stopped = False

    async def asend(self, value: TSource) -> None:
        log.debug("AsyncObserverBase:asend(%s)", str(value))

        if self._is_stopped:
            log.debug("Closed!!")
            return

        self._last_value = value
        self._has_value = True

        await self.asend_core(value)

    async def athrow(self, error: Exception) -> None:
        if self._is_stopped:
            return

        self._is_stopped = True

        self.set_exception(error)
        await self.athrow_core(error)

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
    async def asend_core(self, value: TSource) -> None:
        return NotImplemented

    @abstractmethod
    async def athrow_core(self, error: Exception) -> None:
        return NotImplemented

    @abstractmethod
    async def aclose_core(self) -> None:
        return NotImplemented
