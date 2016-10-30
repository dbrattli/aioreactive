from abc import ABCMeta, abstractmethod

from aioreactive.core import AsyncSink
from aioreactive.core.utils import anoop


class AsyncObserver(metaclass=ABCMeta):
    """An abstract async observer."""

    @abstractmethod
    async def on_next(self, value):
        return NotImplemented

    @abstractmethod
    async def on_error(self, error):
        return NotImplemented

    @abstractmethod
    async def on_completed(self):
        return NotImplemented


class AsyncAnonymousObserver(AsyncObserver):
    """An anonymous async observer."""

    def __init__(self, on_next=None, on_error=None, on_completed=None):
        self._on_next = on_next or anoop
        self._on_error = on_error or anoop
        self._on_completed = on_completed or anoop

    async def on_next(self, value):
        await self._on_next(value)

    async def on_error(self, ex: Exception):
        await self._on_error(ex)

    async def on_completed(self):
        await self._on_completed()


class AsyncNoopObserver(AsyncObserver):
    async def on_next(self, value):
        pass

    async def on_error(self, ex):
        pass

    async def on_completed(self):
        pass


class AsyncSinkObserver(AsyncSink):
    """A async sink that forwards to an async observer."""

    def __init__(self):
        self._obv = AsyncNoopObserver()

    async def asend(self, value):
        await self._obv.on_next(value)

    async def athrow(self, ex: Exception):
        await self._obv.on_error(ex)

    async def aclose(self):
        await self._obv.on_completed()

    async def __astart__(self, obv: AsyncObserver) -> AsyncSink:
        self._obv = obv
        return self
