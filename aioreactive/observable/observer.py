from abc import ABCMeta, abstractmethod

from aioreactive.abc import AsyncSink
from aioreactive.core.utils import noop


class Observer(metaclass=ABCMeta):
    @abstractmethod
    async def on_next(self, value):
        return NotImplemented

    @abstractmethod
    async def on_error(self, error):
        return NotImplemented

    @abstractmethod
    async def on_completed(self):
        return NotImplemented


class AnonymousObserver(Observer):
    """A chained AsyncSink."""

    def __init__(self, on_next=None, on_error=None, on_completed=None):
        self._on_next = on_next or noop
        self._on_error = on_error or noop
        self._on_completed = on_completed or noop

    async def on_next(self, value):
        await self._on_next(value)

    async def on_error(self, ex: Exception):
        await self._on_error(ex)

    async def on_completed(self):
        await self._on_completed()


class NoopObserver(Observer):
    async def on_next(self, value):
        pass

    async def on_error(self, ex):
        pass

    async def on_completed(self):
        pass


class SinkObserver(AsyncSink):
    """A chained Observer."""

    def __init__(self):
        self._obv = NoopObserver()

    async def send(self, value):
        await self._obv.on_next(value)

    async def throw(self, ex: Exception):
        await self._obv.on_error(ex)

    async def close(self):
        await self._obv.on_completed()

    async def __alisten__(self, obv: Observer) -> AsyncSink:
        self._obv = obv
        return self
