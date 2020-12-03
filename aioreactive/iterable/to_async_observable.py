from typing import TypeVar, AsyncIterable

from aioreactive import AsyncObservable

TSource = TypeVar("TSource")


class ToAsyncObservable(AsyncIterable[TSource]):
    def __init__(self, source: AsyncIterable[TSource]) -> None:
        self._source = source


def to_async_observable(source: AsyncIterable[TSource]) -> AsyncObservable[TSource]:
    """Convert to async observable.

    Keyword arguments:
    source -- Async iterable to convert to async observable.

    Returns async observable"""

    return ToAsyncObservable(source)
