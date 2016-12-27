from asyncio import iscoroutinefunction
from typing import Awaitable, Union, Callable, TypeVar

from aioreactive.core import AsyncObservable, AsyncObserver, chain
from aioreactive.core import AsyncSingleStream

T = TypeVar('T')


class Filter(AsyncObservable):

    def __init__(self, predicate: Union[Callable[[T], bool], Awaitable[bool]], source: AsyncObservable[T]) -> None:
        """Filters the elements of the source sequence based on a
        predicate function."""

        self._source = source
        self._predicate = predicate
        self._is_awaitable = iscoroutinefunction(predicate)

    async def __asubscribe__(self, sink: AsyncObserver):
        _observer = await chain(Filter.Sink(self), sink)
        return await chain(self._source, _observer)

    class Sink(AsyncSingleStream):

        def __init__(self, source: "Filter") -> None:
            super().__init__()
            self._predicate = source._predicate
            self._is_awaitable = source._is_awaitable

        async def asend(self, value: T) -> None:
            try:
                should_run = await self._predicate(value) if self._is_awaitable else self._predicate(value)
            except Exception as ex:
                await self._observer.athrow(ex)
            else:
                if should_run:
                    await self._observer.asend(value)


def filter(predicate: Union[Callable[[T], bool], Awaitable[bool]], source: AsyncObservable) -> AsyncObservable:
    """Filters the source stream.

    Filters the items of the source stream based on a predicate
    function.
    """
    return Filter(predicate, source)
