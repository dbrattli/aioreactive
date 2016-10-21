from asyncio import iscoroutinefunction
from typing import Callable, Awaitable, Union, TypeVar, Generic

from aioreactive.core import AsyncSink, AsyncSource
from aioreactive.core import AsyncSingleStream, chain

T = TypeVar('T')


class Map(AsyncSource):

    def __init__(self, mapper: Union[Callable[[T], T], Awaitable[T]], source: AsyncSource) -> None:
        self._source = source
        self._mapper = mapper
        self._is_awaitable = iscoroutinefunction(mapper)

    async def __astart__(self, sink: AsyncSink) -> AsyncSingleStream:
        _sink = await chain(Map.Stream(self), sink)  # type: AsyncSingleStream
        return await chain(self._source, _sink)

    class Stream(AsyncSingleStream, Generic[T]):

        def __init__(self, source: "Map") -> None:
            super().__init__()

            self._is_awaitable = source._is_awaitable
            self._selector = source._mapper

        async def asend(self, value: T) -> None:
            try:
                result = await self._selector(value) if self._is_awaitable else self._selector(value)
            except Exception as err:
                await self._sink.athrow(err)
            else:
                await self._sink.asend(result)


def map(selector: Awaitable, source: AsyncSource) -> AsyncSource:
    """Project each item of the source stream.

    xs = map(lambda value: value * value, source)

    Keyword arguments:
    mapper: A transform function to apply to each source item.

    Returns an observable sequence whose elements are the result of
    invoking the mapper function on each element of source.
    """

    return Map(selector, source)
