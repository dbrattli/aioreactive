from asyncio import iscoroutinefunction
from typing import Callable, Awaitable, Union, TypeVar, Generic

from aioreactive.core import AsyncObserver, AsyncObservable
from aioreactive.core import AsyncSingleStream, chain

T = TypeVar('T')


class Scan(AsyncObservable):

    def __init__(self, function: Callable[[T], T], initializer: T, source: AsyncObservable) -> None:
        self._source = source
        self._function = function
        self._is_awaitable = iscoroutinefunction(function)

    async def __asubscribe__(self, sink: AsyncObserver) -> AsyncSingleStream:
        _observer = await chain(Scan.Stream(self), sink)  # type: AsyncSingleStream
        return await chain(self._source, _observer)

    class Stream(AsyncSingleStream, Generic[T]):

        def __init__(self, source: "Scan") -> None:
            super().__init__()

            self._is_awaitable = source._is_awaitable
            self._function = source._function

            self._has_value = False
            self._value = None

        async def asend(self, value: T) -> None:
            try:
                result = await self._function(value, value) if self._is_awaitable else self._selector(value)
            except Exception as err:
                await self._observer.athrow(err)
            else:
                await self._observer.asend(result)


def scan(function: Awaitable[T], initializer: T, source: AsyncObservable) -> AsyncObservable:
    """Project each item of the source stream.

    xs = map(lambda value: value * value, source)

    Keyword arguments:
    function: A transform function to apply to each source item.

    Returns an observable sequence whose elements are the result of
    invoking the mapper function on each element of source.
    """

    return Scan(function, initializer, source)
