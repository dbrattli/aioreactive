from typing import TypeVar, AsyncIterable, AsyncIterator, Generic

from aioreactive.core import AsyncSingleStream
from aioreactive.core import AsyncObserver, AsyncObservable, chain
from aioreactive.core import AsyncIteratorObserver

T = TypeVar('T')


class ToAsyncIterable(Generic[T], AsyncIterable[T]):

    def __init__(self, source: AsyncObservable) -> None:
        self._source = source

    async def __aiter__(self) -> AsyncIterator:
        """Iterate asynchronously.

        Transforms the async source to an async iterable. The source
        will await for the iterator to pick up the value before
        continuing to avoid queuing values.
        """

        _observer = AsyncIteratorObserver()
        await self._source.__asubscribe__(_observer)
        return _observer


def to_async_iterable(source: AsyncObservable) -> AsyncIterable:
    """Skip the specified number of values.

    Keyword arguments:
    count -- The number of elements to skip before returning the
        remaining values.

    Returns a source stream that contains the values that occur
    after the specified index in the input source stream.
    """

    return ToAsyncIterable(source)
