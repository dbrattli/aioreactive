from asyncio import iscoroutinefunction
from typing import Awaitable, Union, Callable, TypeVar

from aioreactive.core import AsyncSource, AsyncSink, AsyncSingleStream
from aioreactive.core import chain

T = TypeVar('T')


class FilterIndexed(AsyncSource):

    def __init__(self, predicate: Union[Callable[[T, int], bool], Awaitable], source: AsyncSource) -> None:
        """Filters the elements of the source stream based on a
        predicate function.
        """

        self._is_awaitable = iscoroutinefunction(predicate)
        self._predicate = predicate
        self._source = source

    async def __astart__(self, sink: AsyncSink) -> AsyncSingleStream:
        _sink = await chain(FilterIndexed.Sink(self), sink)
        return await chain(self._source, _sink)

    class Sink(AsyncSingleStream):

        def __init__(self, source: "FilterIndexed") -> None:
            super().__init__()
            self._is_awaitable = source._is_awaitable
            self._predicate = source._predicate
            self._index = 0

        async def asend(self, value: T) -> None:
            try:
                should_run = await self._predicate(value, self._index) if self._is_awaitable else self._predicate(value, self._index)
            except Exception as ex:
                await self._sink.athrow(ex)
            else:
                if should_run:
                    await self._sink.asend(value)
                self._index += 1


def filteri(predicate: Union[Callable[[T, int], bool], Awaitable], source: AsyncSource) -> AsyncSource:
    return FilterIndexed(predicate, source)
