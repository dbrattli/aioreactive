from asyncio import iscoroutinefunction
from typing import Callable, Awaitable, Union, TypeVar, Generic

from aioreactive.core import AsyncObserver, AsyncObservable
from aioreactive.core import AsyncSingleStream, chain

T = TypeVar('T')


class Max(AsyncObservable):

    def __init__(self, source: AsyncObservable) -> None:
        self._source = source

    async def __asubscribe__(self, sink: AsyncObserver) -> AsyncSingleStream:
        _observer = await chain(Max.Stream(self), sink)  # type: AsyncSingleStream
        return await chain(self._source, _observer)

    class Stream(AsyncSingleStream, Generic[T]):

        def __init__(self, source: "Max") -> None:
            super().__init__()
            self._max = None

        async def asend(self, value: T) -> None:
            if value > self._max:
                self._max = value

        async def close(self):
            await super().asend(self._max)
            await super().aclose()


def max(source: AsyncObservable) -> AsyncObservable:
    """Project each item of the source stream.

    xs = max(source)

    Keyword arguments:
    source: Source to find max value from.

    Returns a stream with a single item that is the item with the
    maximum value from the source stream.
    """

    return Map(selector, source)
