from asyncio import iscoroutinefunction
from typing import Awaitable, Union, Callable, TypeVar

from aioreactive.core import AsyncObservable, AsyncObserver, AsyncSingleStream
from aioreactive.core import chain

T = TypeVar('T')


class FilterIndexed(AsyncObservable):

    def __init__(self, predicate: Union[Callable[[T, int], bool], Awaitable], source: AsyncObservable) -> None:
        """Filters the elements of the source stream based on a
        predicate function.
        """

        self._is_awaitable = iscoroutinefunction(predicate)
        self._predicate = predicate
        self._source = source

    async def __asubscribe__(self, sink: AsyncObserver) -> AsyncSingleStream:
        _observer = await chain(FilterIndexed.Sink(self), sink)
        return await chain(self._source, _observer)

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
                await self._observer.athrow(ex)
            else:
                if should_run:
                    await self._observer.asend(value)
                self._index += 1


def filteri(predicate: Union[Callable[[T, int], bool], Awaitable], source: AsyncObservable) -> AsyncObservable:
    return FilterIndexed(predicate, source)
