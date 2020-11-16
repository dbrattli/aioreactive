"""Aioreactive module"""

from functools import partial
from typing import AsyncIterable, Awaitable, Callable, Iterable, Tuple, TypeVar, Union

from expression.core import Option, pipe
from expression.system.disposable import AsyncDisposable

from .observables import AsyncAnonymousObservable, AsyncIterableObservable, AsyncObservable
from .observers import AsyncAnonymousObserver, AsyncAwaitableObserver, AsyncIteratorObserver, AsyncNotificationObserver
from .subject import AsyncSingleSubject, AsyncSubject
from .subscription import run
from .types import AsyncObserver, Stream

TSource = TypeVar("TSource")
TResult = TypeVar("TResult")
TOther = TypeVar("TOther")


class AsyncRx(AsyncObservable[TSource]):
    """An AsyncObservable class similar to classic Rx.

    This class supports has all operators as methods and supports
    method chaining.

    Subscribe is also a method.

    All methods are lazy imported.
    """

    def __init__(self, source: AsyncObservable[TSource]) -> None:
        super().__init__()
        self._source = source

    @classmethod
    def create(cls, source: AsyncObservable[TSource]) -> "AsyncRx[TSource]":
        """Create `AsyncChainedObservable`.

        Helper method for creating an `AsyncChainedObservable` to the
        the generic type rightly inferred by Pylance (__init__ returns None).
        """
        return cls(source)

    async def subscribe_async(self, observer: AsyncObserver[TSource]) -> AsyncDisposable:
        return await self._source.subscribe_async(observer)

    def __getitem__(self, key: Union[slice, int]) -> "AsyncRx[TSource]":
        """Slices the given source stream using Python slice notation.
         The arguments to slice is start, stop and step given within
         brackets [] and separated with the ':' character. It is
         basically a wrapper around the operators skip(), skip_last(),
         take(), take_last() and filter().

         This marble diagram helps you remember how slices works with
         streams. Positive numbers is relative to the start of the
         events, while negative numbers are relative to the end
         (on_completed) of the stream.

         r---e---a---c---t---i---v---e---|
         0   1   2   3   4   5   6   7   8
        -8  -7  -6  -5  -4  -3  -2  -1

         Example:
         result = source[1:10]
         result = source[1:-2]
         result = source[1:-1:2]

         Keyword arguments:
         self -- Source to slice
         key -- Slice object

         Returne a sliced source stream."""

        return AsyncRx(super(AsyncRx, self).__getitem__(key))

    @classmethod
    def from_iterable(cls, iter: Iterable[TSource]) -> "AsyncRx[TSource]":
        from .create import of_seq

        return AsyncRx(of_seq(iter))

    @classmethod
    def empty(cls) -> "AsyncRx[TSource]":
        from .create import empty

        return AsyncRx(empty())

    @classmethod
    def single(cls, value: TSource) -> "AsyncRx[TSource]":
        from .create import single

        return AsyncRx(single(value))

    def combine_latest(self, other: TOther) -> "AsyncRx[Tuple[TSource, TOther]]":
        from .combine import combine_latest

        return pipe(self, combine_latest(other), AsyncRx.create)

    def concat(self, other: AsyncObservable[TSource]) -> AsyncObservable[TSource]:
        from .combine import concat_seq

        return concat_seq([self, other])

    def debounce(self, seconds: float) -> "AsyncRx[TSource]":
        """Debounce observable source.

        Ignores values from a source stream which are followed by
        another value before seconds has elapsed.

        Example:
        partial = debounce(5) # 5 seconds

        Keyword arguments:
        seconds -- Duration of the throttle period for each value

        Returns partially applied function that takes a source sequence.
        """

        from .timeshift import debounce

        return AsyncRx(pipe(self, debounce(seconds)))

    def delay(self, seconds: float) -> "AsyncRx[TSource]":
        from .timeshift import delay

        return AsyncRx(delay(seconds)(self))

    def distinct_until_changed(self) -> AsyncObservable[TSource]:
        from .filter import distinct_until_changed

        return distinct_until_changed(self)

    def filter(self, predicate: Callable[[TSource], TSource]) -> "AsyncRx[TSource]":
        from .filter import filter

        return pipe(self, filter(predicate), AsyncRx.create)

    def flat_map(self, selector: Callable[[TSource], AsyncObservable[TResult]]) -> "AsyncRx[TResult]":
        from .transform import flat_map

        return pipe(self, flat_map(selector), AsyncRx.create)

    def map(self, selector: Callable[[TSource], TResult]) -> "AsyncRx[TResult]":
        from .transform import map

        return pipe(self, map(selector), AsyncRx.create)

    def merge(self, other: AsyncObservable[TSource]) -> "AsyncRx[TSource]":
        from .combine import merge_inner
        from .create import of_seq

        source = of_seq([self, other])
        return pipe(source, merge_inner(0), AsyncRx.create)

    def to_async_iterable(self) -> AsyncIterable[TSource]:
        from .leave import to_async_iterable

        return to_async_iterable(self)

    def with_latest_from(self, other: AsyncObservable[TOther]) -> "AsyncRx[Tuple[TSource, TOther]]":
        from .combine import with_latest_from

        return AsyncRx(pipe(self, with_latest_from(other)))


def choose(chooser: Callable[[TSource], Option[TSource]]) -> Stream[TSource, TSource]:
    from .filter import choose

    return choose(chooser)


def choose_async(chooser: Callable[[TSource], Awaitable[Option[TSource]]]) -> Stream[TSource, TSource]:
    from .filter import choose_async

    return choose_async(chooser)


def combine_latest(other: AsyncObservable[TOther]) -> Stream[TSource, Tuple[TSource, TOther]]:
    from .combine import combine_latest

    return pipe(combine_latest(other))


def debounce(seconds: float) -> Stream[TSource, TSource]:
    """Debounce source stream.

    Ignores values from a source stream which are followed by another
    value before seconds has elapsed.

    Example:
    partial = debounce(5) # 5 seconds

    Keyword arguments:
    seconds -- Duration of the throttle period for each value

    Returns a partially applied function that takes a source stream to
    debounce."""

    from .timeshift import debounce

    return debounce(seconds)


def catch(handler: Callable[[Exception], AsyncObservable[TSource]]) -> Stream[TSource, TSource]:
    from .transform import catch

    return catch(handler)


def concat(other: AsyncObservable[TSource]) -> Stream[TSource, TSource]:
    """Concatenates an observable sequence with another observable
    sequence."""

    def _concat(source: AsyncObservable[TSource]) -> AsyncObservable[TSource]:
        from .combine import concat_seq

        return concat_seq([source, other])

    return _concat


def concat_seq(sources: Iterable[AsyncObservable[TSource]]) -> AsyncObservable[TSource]:
    """Concatenates an iterable of observable sequences."""

    from .combine import concat_seq

    return concat_seq(sources)


def defer(factory: Callable[[], AsyncObservable[TSource]]) -> AsyncObservable[TSource]:
    """Returns an observable sequence that invokes the specified factory
    function whenever a new observer subscribes."""
    from .create import defer

    return defer(factory)


def delay(seconds: float) -> Stream[TSource, TSource]:
    from .timeshift import delay

    return delay(seconds)


def empty() -> "AsyncObservable[TSource]":
    from .create import empty

    return empty()


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

    Returns the source stream whose elements are pulled from the given
    (async) iterable sequence."""
    from .create import of_seq

    return of_seq(iterable)


def flat_map(mapper: Callable[[TSource], AsyncObservable[TResult]]) -> Stream[TSource, TResult]:
    from .transform import flat_map

    return flat_map(mapper)


def flat_mapi(mapper: Callable[[TSource, int], AsyncObservable[TResult]]) -> Stream[TSource, TResult]:
    from .transform import flat_mapi

    return flat_mapi(mapper)


def from_async_iterable(iter: Iterable[TSource]) -> "AsyncObservable[TSource]":
    from aioreactive.operators.from_async_iterable import from_async_iterable

    from .create import of

    return AsyncRx(from_async_iterable(iter))


def interval(seconds: float, period: int) -> AsyncObservable[int]:
    """Returns an observable sequence that triggers the increasing
    sequence starting with 0 after the given msecs, and the after each
    period."""
    from .create import interval

    return interval(seconds, period)


def map(fn: Callable[[TSource], TResult]) -> Stream[TSource, TResult]:
    from .transform import map as _map

    return _map(fn)


def starmap(mapper: Callable[..., TResult]) -> Stream[TSource, TResult]:
    """Map and spread the arguments to the mapper.

    Returns an observable sequence whose elements are the result of
    invoking the mapper function on each element of the source."""
    from .transform import starmap

    return starmap(mapper)


def map_async(mapper: Callable[[TSource], Awaitable[TResult]]) -> Stream[TSource, TResult]:
    """Map asynchrnously.

    Returns an observable sequence whose elements are the result of
    invoking the async mapper function on each element of the
    source."""
    from .transform import map_async

    return map_async(mapper)


def mapi_async(mapper: Callable[[TSource, int], Awaitable[TResult]]) -> Stream[TSource, TResult]:
    """Returns an observable sequence whose elements are the result of
    invoking the async mapper function by incorporating the element's
    index on each element of the source."""
    from .transform import mapi_async

    return mapi_async(mapper)


def mapi(mapper: Callable[[TSource, int], TResult]) -> Stream[TSource, TResult]:
    """Returns an observable sequence whose elements are the result of
    invoking the mapper function and incorporating the element's index
    on each element of the source."""
    from .transform import mapi

    return mapi(mapper)


def merge_inner(max_concurrent: int = 0) -> Stream[AsyncObservable[TSource], TSource]:
    def _merge_inner(source: AsyncObservable[AsyncObservable[TSource]]) -> AsyncObservable[TSource]:
        from .combine import merge_inner

        return pipe(source, merge_inner(max_concurrent))

    return _merge_inner


def merge(other: AsyncObservable[TSource]) -> Stream[TSource, TSource]:
    from .create import of_seq

    def _(source: AsyncObservable[TSource]) -> AsyncObservable[TSource]:
        return pipe(of_seq([source, other]), merge_inner)

    return _


def merge_seq(sources: Iterable[AsyncObservable[TSource]]) -> AsyncObservable[TSource]:
    from .create import of_seq

    return pipe(of_seq(sources), merge_inner)


def never() -> "AsyncObservable[TSource]":
    from .create import never

    return never()


def distinct_until_changed(source: AsyncObservable[TSource]) -> AsyncObservable[TSource]:
    from .filter import distinct_until_changed

    return distinct_until_changed(source)


def as_chained(source: AsyncObservable[TSource]) -> AsyncRx[TSource]:
    return AsyncRx(source)


def retry(retry_count: int) -> Stream[TSource, TSource]:
    from .transform import retry

    return retry(retry_count)


def subscribe_async(obv: AsyncObserver[TSource]) -> Callable[[AsyncObservable[TSource]], Awaitable[AsyncDisposable]]:
    """A pipeable subscribe async.

    Example:
        >>> await pipe(xs, filter(predicate), subscribe_async)
    """
    from .subscription import subscribe_async

    return subscribe_async(obv)


def switch_latest() -> Stream[TSource, TSource]:
    from .transform import switch_latest

    return switch_latest


def to_async_iterable(source: AsyncObservable[TSource]) -> AsyncIterable[TSource]:
    from .leave import to_async_iterable

    return to_async_iterable(source)


def single(value: TSource) -> "AsyncObservable[TSource]":
    from .create import single

    return single(value)


def timer(due_time: float) -> AsyncObservable[int]:
    """Returns an observable sequence that triggers the value 0
    after the given duetime in milliseconds."""
    from .create import timer

    return timer(due_time)


def with_latest_from(other: AsyncObservable[TOther]) -> Stream[TSource, Tuple[TSource, TOther]]:
    from .combine import with_latest_from

    return with_latest_from(other)


__all__ = [
    "AsyncAnonymousObservable",
    "AsyncAnonymousObserver",
    "AsyncAwaitableObserver",
    "AsyncIteratorObserver",
    "AsyncIterableObservable",
    "AsyncNotificationObserver",
    "AsyncObservable",
    "AsyncObserver",
    "asyncrx",
    "AsyncSingleSubject",
    "AsyncSubject",
    "catch",
    "choose",
    "choose_async",
    "combine_latest",
    "concat",
    "concat_seq" "delay",
    "empty",
    "filter",
    "filter_async",
    "from_iterable",
    "map",
    "map_async",
    "merge",
    "merge_inner",
    "merge_seq",
    "never",
    "retry",
    "run",
    "single",
    "Stream",
    "switch_latest",
    "to_async_iterable",
]
