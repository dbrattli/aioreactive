"""A collection of partially applied and lazy loaded operators."""

from functools import partial
from typing import AsyncIterable, Awaitable, Callable, Iterable, Tuple, TypeVar

from expression.core import Option

from .observables import AsyncObservable
from .types import Stream

TSource = TypeVar("TSource")
TResult = TypeVar("TResult")


def choose(chooser: Callable[[TSource], Option[TSource]]) -> Stream[TSource, TSource]:
    from .filter import choose

    return choose(chooser)


def choose_async(chooser: Callable[[TSource], Awaitable[Option[TSource]]]) -> Stream[TSource, TSource]:
    from .filter import choose_async

    return choose_async(chooser)


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


def catch(handler: Callable[[Exception], AsyncObservable[TSource]]) -> Stream[TSource, TSource]:
    from .transform import catch

    return catch(handler)


def delay(seconds: float) -> Callable[[AsyncObservable[TSource]], AsyncObservable[TSource]]:
    from aioreactive.operators.delay import delay

    return partial(delay, seconds)


def filter(predicate: Callable[[TSource], bool]) -> Callable[[AsyncObservable[TSource]], AsyncObservable[TSource]]:
    from .filter import filter

    return filter(predicate)


def filter_async(
    predicate: Callable[[TSource], Awaitable[bool]]
) -> Callable[[AsyncObservable[TSource]], AsyncObservable[TSource]]:
    from .filter import filter_async

    return filter_async(predicate)


def from_iterable(iterable: Iterable[TSource]) -> AsyncObservable[TSource]:
    """Convert an iterable to a source stream.

    1 - xs = from_iterable([1,2,3])

    Returns the source stream whose elements are pulled from the
    given (async) iterable sequence."""
    from .create import of_seq

    return of_seq(iterable)


def flat_map(mapper: Callable[[TSource], AsyncObservable[TResult]]) -> Stream[TSource, TResult]:
    from .transform import flat_map

    return flat_map(mapper)


def map(fn: Callable[[TSource], TResult]) -> Stream[TSource, TResult]:
    from .transform import map as _map

    return _map(fn)


def mapi_async(mapper: Callable[[Tuple[TSource, int]], Awaitable[TResult]]) -> Stream[TSource, TResult]:
    """Returns an observable sequence whose elements are the result of invoking the async mapper function by
    incorporating the element's index on each element of the source."""
    from .transform import map_async

    return map_async(mapper)


def mapi(mapper: Callable[[TSource, int], TResult]) -> Stream[TSource, TResult]:
    """Returns an observable sequence whose elements are the result of invoking the mapper function and incorporating
    the element's index on each element of the source."""
    from .transform import mapi

    return mapi(mapper)


def merge(other: AsyncObservable) -> Callable[[AsyncObservable], AsyncObservable]:
    from aioreactive.operators.merge import merge

    return partial(merge, other)


def with_latest_from(mapper: Callable, other: AsyncObservable) -> Callable[[AsyncObservable], AsyncObservable]:
    from aioreactive.operators.with_latest_from import with_latest_from

    return partial(with_latest_from, mapper, other)


def distinct_until_changed() -> Callable[[AsyncObservable], AsyncObservable]:
    from aioreactive.operators.distinct_until_changed import distinct_until_changed

    return partial(distinct_until_changed)


def retry(retry_count: int) -> Stream[TSource, TSource]:
    from .transform import retry

    return retry(retry_count)


def switch_latest() -> Stream[TSource, TSource]:
    from .transform import switch_latest

    return switch_latest


def to_async_iterable() -> Callable[[AsyncObservable], AsyncIterable]:
    from aioreactive.operators.to_async_iterable import to_async_iterable

    return partial(to_async_iterable)


def from_async_iterable(iter: Iterable[TSource]) -> "AsyncObservable[TSource]":
    from aioreactive.operators.from_async_iterable import from_async_iterable

    from .create import of

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