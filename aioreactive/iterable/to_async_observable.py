from typing import TypeVar, AsyncIterable, AsyncIterator, Generic

from aioreactive.core import AsyncSingleStream
from aioreactive.core import AsyncObserver, AsyncObservable, chain

T = TypeVar('T')


class ToAsyncObservable(Generic[T], AsyncIterable[T]):

    def __init__(self, source: AsyncIterable) -> None:
        self._source = source


def to_async_observable(source: AsyncIterable) -> AsyncObservable:
    """Convert to async observable.

    Keyword arguments:
    source -- Async iterable to convert to async observable.

    Returns async observable"""

    return ToAsyncObservable(source)

