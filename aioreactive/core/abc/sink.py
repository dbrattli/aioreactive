from abc import abstractmethod
from .source import Source, AsyncSource


class Sink(Source):
    """A synchronous sink."""

    __slots__ = ()

    @abstractmethod
    def send(self, value):
        return NotImplemented

    @abstractmethod
    def throw(self, error):
        return NotImplemented

    @abstractmethod
    def close(self):
        return NotImplemented

    def __start__(self, sink):
        return self


class AsyncSink(AsyncSource):
    """An asynchronous sink."""

    __slots__ = ()

    @abstractmethod
    async def asend(self, value):
        return NotImplemented

    @abstractmethod
    async def athrow(self, error):
        return NotImplemented

    @abstractmethod
    async def aclose(self):
        return NotImplemented

    async def __astart__(self, sink):
        return self
