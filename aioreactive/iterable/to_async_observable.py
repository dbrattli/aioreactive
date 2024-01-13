from collections.abc import AsyncIterable
from typing import TypeVar

from aioreactive import AsyncObservable, AsyncRx


TSource = TypeVar("TSource")


def to_async_observable(source: AsyncIterable[TSource]) -> AsyncObservable[TSource]:
    """Convert to async observable.

    Keyword Arguments:
    source: Async iterable to convert to async observable.

    Returns async observable
    """
    return AsyncRx.from_async_iterable(source)
