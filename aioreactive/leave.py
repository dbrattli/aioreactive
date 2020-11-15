from typing import AsyncIterable, TypeVar

from .observables import AsyncIterableObservable, AsyncObservable

TSource = TypeVar("TSource")


def to_async_iterable(source: AsyncObservable[TSource]) -> AsyncIterable[TSource]:
    """Convert async observable to async iterable.

    Args:
        count: The number of elements to skip before returning the
            remaining values.

    Returns:
        A source stream that contains the values that occur
        after the specified index in the input source stream.
    """

    return AsyncIterableObservable(source)
