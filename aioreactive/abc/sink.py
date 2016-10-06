from abc import abstractmethod
from .source import Source, AsyncSource


class Sink(Source):
    """A synchronous sink."""
    @abstractmethod
    def send(self, value):
        return NotImplemented

    @abstractmethod
    def throw(self, error):
        return NotImplemented

    @abstractmethod
    def close(self):
        return NotImplemented

    def __listen__(self, sink):
        return self


class AsyncSink(AsyncSource):
    """An asynchronous sink."""
    @abstractmethod
    async def send(self, value):
        return NotImplemented

    @abstractmethod
    async def throw(self, error):
        return NotImplemented

    @abstractmethod
    async def close(self):
        return NotImplemented

    async def __alisten__(self, sink):
        return self
