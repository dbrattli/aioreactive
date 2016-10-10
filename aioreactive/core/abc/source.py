from abc import ABCMeta, abstractmethod


class Source(metaclass=ABCMeta):
    __slots__ = ()

    @abstractmethod
    def __listen__(self, sink):
        return NotImplemented


class AsyncSource(metaclass=ABCMeta):
    __slots__ = ()

    @abstractmethod
    async def __alisten__(self, sink):
        return NotImplemented
