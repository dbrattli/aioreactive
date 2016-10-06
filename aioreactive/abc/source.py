from abc import ABCMeta, abstractmethod


class Source(metaclass=ABCMeta):
    @abstractmethod
    def __listen__(self, sink):
        return NotImplemented


class AsyncSource(metaclass=ABCMeta):
    @abstractmethod
    async def __alisten__(self, sink):
        return NotImplemented
