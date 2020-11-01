"""A collection of partially applied and lazy loaded operators."""

from functools import partial
from typing import AsyncIterable, Callable, Iterable, TypeVar

from .observables import AsyncObservable

TSource = TypeVar("TSource")
TResult = TypeVar("TResult")


def debounce(seconds: float) -> Callable[[AsyncObservable[TSource]], AsyncObservable[TSource]]:
    """Debounce source stream.

    Ignores values from a source stream which are followed by
    another value before seconds has elapsed.

    Example:
    partial = debounce(5) # 5 seconds

    Keyword arguments:
    seconds -- Duration of the throttle period for each value

    Returns a partially applied function that takes a source stream to
    debounce."""

    from aioreactive.operators.debounce import debounce

    return partial(debounce, seconds)


def delay(seconds: float) -> Callable[[AsyncObservable[TSource]], AsyncObservable[TSource]]:
    from aioreactive.operators.delay import delay

    return partial(delay, seconds)


def filter(predicate: Callable[[TSource], bool]) -> Callable[[AsyncObservable[TSource]], AsyncObservable[TSource]]:
    from aioreactive.operators.filter import filter

    return partial(filter, predicate)


def from_iterable(iterable: Iterable[TSource]) -> AsyncObservable[TSource]:
    """Convert an iterable to a source stream.

    1 - xs = from_iterable([1,2,3])

    Returns the source stream whose elements are pulled from the
    given (async) iterable sequence."""
    from .create import of_seq

    return of_seq(iterable)


def flat_map(fn: Callable[[TSource], AsyncObservable]) -> Callable[[AsyncObservable], AsyncObservable]:
    from aioreactive.operators.flat_map import flat_map

    return partial(flat_map, fn)


def map(fn: Callable[[TSource], TResult]) -> Callable[[AsyncObservable[TSource]], AsyncObservable[TResult]]:
    from .transform import map as _map

    return _map(fn)


def merge(other: AsyncObservable) -> Callable[[AsyncObservable], AsyncObservable]:
    from aioreactive.operators.merge import merge

    return partial(merge, other)


def with_latest_from(mapper: Callable, other: AsyncObservable) -> Callable[[AsyncObservable], AsyncObservable]:
    from aioreactive.operators.with_latest_from import with_latest_from

    return partial(with_latest_from, mapper, other)


def distinct_until_changed() -> Callable[[AsyncObservable], AsyncObservable]:
    from aioreactive.operators.distinct_until_changed import distinct_until_changed

    return partial(distinct_until_changed)


def switch_latest() -> Callable[[AsyncObservable], AsyncObservable]:
    from aioreactive.operators.switch_latest import switch_latest

    return partial(switch_latest)


def to_async_iterable() -> Callable[[AsyncObservable], AsyncIterable]:
    from aioreactive.operators.to_async_iterable import to_async_iterable

    return partial(to_async_iterable)


def from_async_iterable(iter: Iterable[TSource]) -> "AsyncObservable[TSource]":
    from aioreactive.operators.from_async_iterable import from_async_iterable

    return AsyncChainedObservable(from_async_iterable(iter))


def single(value: TSource) -> "AsyncObservable[TSource]":
    from .create import single

    return single(value)


def empty() -> "AsyncObservable[TSource]":
    from .create import empty

    return empty()


def never() -> "AsyncObservable[TSource]":
    from .create import never

    return never()
