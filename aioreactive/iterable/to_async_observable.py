from typing import AsyncIterable, TypeVar

from aioreactive import AsyncObservable, AsyncRx

TSource = TypeVar("TSource")


def to_async_observable(source: AsyncIterable[TSource]) -> AsyncObservable[TSource]:
    """Convert to async observable.

    Keyword arguments:
    source -- Async iterable to convert to async observable.

    Returns async observable"""

    return AsyncRx.from_async_iterable(source)
