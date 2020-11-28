"""Aioreactive module.

Contains the AsyncRx chained obserable that allows method chaining of all operators.

Also contains all operators as plain functions.

To use this module:

Example:
    >>> import aioreactive as rx
    >>> xs = rx.from_iterable([1, 2, 3])
    >>> ...

"""
from typing import Any, AsyncIterable, Awaitable, Callable, Iterable, Tuple, TypeVar, Union

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

    This class provides all operators as methods and supports
    method chaining.

    Example:
    >>> AsyncRx.from_iterable([1,2,3]).map(lambda x: x + 2).filter(lambda x: x < 3)

    All methods are lazy imported.
    """

    def __init__(self, source: AsyncObservable[TSource]) -> None:
        self._source = source

    async def subscribe_async(self, observer: AsyncObserver[TSource]) -> AsyncDisposable:
        """Subscribe to the async observable.

        Uses the given observer to subscribe asynchronously to the async
        observable.

        Args:
            observer: The async observer to subscribe.

        Returns:
            An async disposable that can be used to dispose the
            subscription.
        """
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
        >>> result = source[1:10]
        >>> result = source[1:-2]
        >>> result = source[1:-1:2]

        Args:
            self: Source to slice
            key: A slice object

        Returns:
            The sliced source stream.
        """

        from .filtering import slice as _slice

        if isinstance(key, slice):
            start, stop, step = key.start, key.stop, key.step
        else:
            start, stop, step = key, key + 1, 1

        return AsyncRx(pipe(self, _slice(start, stop, step)))

    @classmethod
    def create(cls, source: AsyncObservable[TSource]) -> "AsyncRx[TSource]":
        """Create `AsyncChainedObservable`.

        Helper method for creating an `AsyncChainedObservable` to the
        the generic type rightly inferred by Pylance (__init__ returns None).
        """
        return cls(source)

    @classmethod
    def empty(cls) -> "AsyncRx[TSource]":
        return AsyncRx(empty())

    @classmethod
    def from_iterable(cls, iter: Iterable[TSource]) -> "AsyncRx[TSource]":
        return AsyncRx(from_iterable(iter))

    @classmethod
    def from_async_iterable(cls, iter: AsyncIterable[TSource]) -> "AsyncObservable[TSource]":
        """Convert an async iterable to an async observable stream.

        Example:
            >>> xs = AsyncRx.from_async_iterable(async_iterable)

        Returns:
            The source stream whose elements are pulled from the given
            (async) iterable sequence.
        """

        return AsyncRx(from_async_iterable(iter))

    @classmethod
    def single(cls, value: TSource) -> "AsyncRx[TSource]":
        from .create import single

        return AsyncRx(single(value))

    def as_async_observable(self) -> AsyncObservable[TSource]:
        return AsyncAnonymousObservable(self.subscribe_async)

    def choose(self, chooser: Callable[[TSource], Option[TSource]]) -> AsyncObservable[TSource]:
        """Choose.

        Applies the given function to each element of the stream and returns
        the stream comprised of the results for each element where the
        function returns Some with some value.

        Args:
            chooser: A function to transform or filter the stream
                by returning `Some(value)` or `Nothing`.

        Returns:
            The filtered and/or transformed stream.
        """
        return AsyncRx(pipe(self, choose(chooser)))

    def choose_async(self, chooser: Callable[[TSource], Awaitable[Option[TSource]]]) -> AsyncObservable[TSource]:
        """Choose async.

        Applies the given async function to each element of the stream and
        returns the stream comprised of the results for each element where
        the function returns Some with some value.

        Args:
            chooser: A function to transform or filter the stream
                asynchronously by returning `Some(value)` or `Nothing`.

        Returns:
            The filtered and transformed stream.
        """
        return AsyncRx(pipe(self, choose_async(chooser)))

    def combine_latest(self, other: TOther) -> "AsyncRx[Tuple[TSource, TOther]]":
        from .combine import combine_latest

        return AsyncRx.create(pipe(self, combine_latest(other)))

    def concat(self, other: AsyncObservable[TSource]) -> AsyncObservable[TSource]:
        from .combine import concat_seq

        return concat_seq([self, other])

    def debounce(self, seconds: float) -> "AsyncRx[TSource]":
        """Debounce observable stream.

        Ignores values from an observable sequence which are followed by
        another value before the given timeout.

        Args:
            seconds (float): Number of seconds to debounce.

        Returns:
            The debounced stream.
        """

        from .timeshift import debounce

        return AsyncRx(pipe(self, debounce(seconds)))

    def delay(self, seconds: float) -> "AsyncRx[TSource]":
        from .timeshift import delay

        return AsyncRx(delay(seconds)(self))

    def distinct_until_changed(self) -> AsyncObservable[TSource]:
        from .filtering import distinct_until_changed

        return AsyncRx(distinct_until_changed(self))

    def filter(self, predicate: Callable[[TSource], bool]) -> "AsyncRx[TSource]":
        """Filter stream.

        Filters the elements of an observable sequence based on a predicate.
        Returns an observable sequence that contains elements from the input
        sequence that satisfy the condition.

        Args:
            predicate:
                A function to filter the stream by returning `True` to
                keep the item, or `False` to filter and remove the item.

        Returns:
            The filtered stream.
        """

        from .filtering import filter as _filter

        return AsyncRx(pipe(self, _filter(predicate)))

    def filteri(self, predicate: Callable[[TSource, int], bool]) -> AsyncObservable[TSource]:
        """Filter with index.

        Filters the elements of an observable sequence based on a predicate
        and incorporating the element's index on each element of the source.

        Args:
            predicate: Function to test each element.

        Returns:
            An observable sequence that contains elements from the input
            sequence that satisfy the condition.
        """
        return AsyncRx(pipe(self, filteri(predicate)))

    def filter_async(self, predicate: Callable[[TSource], Awaitable[bool]]) -> "AsyncRx[TSource]":
        from .filtering import filter_async

        return AsyncRx(pipe(self, filter_async(predicate)))

    def flat_map(self, selector: Callable[[TSource], AsyncObservable[TResult]]) -> "AsyncRx[TResult]":
        from .transform import flat_map

        return pipe(self, flat_map(selector), AsyncRx.create)

    def flat_map_async(self, selector: Callable[[TSource], Awaitable[AsyncObservable[TResult]]]) -> "AsyncRx[TResult]":
        from .transform import flat_map_async

        return pipe(self, flat_map_async(selector), AsyncRx.create)

    def flat_map_latest_async(
        self, mapper: Callable[[TSource], Awaitable[AsyncObservable[TResult]]]
    ) -> "AsyncRx[TResult]":
        """Flat map latest async.

        Asynchronosly transforms the items emitted by an source sequence
        into observable streams, and mirror those items emitted by the
        most-recently transformed observable sequence.

        Args:
            mapper: Function to transform each item into a new async
                observable.

        Returns:
            An async observable that only merges values from the latest
            async observable produced by the mapper.
        """
        return AsyncRx(pipe(self, flat_map_latest_async(mapper)))

    def map(self, selector: Callable[[TSource], TResult]) -> "AsyncRx[TResult]":
        from .transform import map

        return AsyncRx(pipe(self, map(selector), AsyncRx.create))

    def merge(self, other: AsyncObservable[TSource]) -> "AsyncRx[TSource]":
        from .combine import merge_inner
        from .create import of_seq

        source = of_seq([self, other])
        return pipe(source, merge_inner(0), AsyncRx.create)

    def skip(self, count: int) -> AsyncObservable[TSource]:
        """Skip items from start of the stream.

        Bypasses a specified number of elements in an observable sequence
        and then returns the remaining elements.

        Args:
            count: Items to skip

        Returns:
            Stream[TSource, TSource]: [description]
        """
        return AsyncRx(pipe(self, skip(count)))

    def skip_last(self, count: int) -> AsyncObservable[TSource]:
        """Bypasses a specified number of elements at the end of an
        observable sequence.

        This operator accumulates a queue with a length enough to store
        the first `count` elements. As more elements are received,
        elements are taken from the front of the queue and produced on
        the result sequence. This causes elements to be delayed.

        Args:
            count: Number of elements to bypass at the end of the
            source sequence.

        Returns:
            An observable sequence containing the source sequence
            elements except for the bypassed ones at the end.
        """
        return AsyncRx(pipe(self, skip_last(count)))

    def starfilter(self, predicate: Callable[..., bool]) -> AsyncObservable[Tuple[TSource, int]]:
        """Filter and spread the arguments to the predicate.

        Filters the elements of an observable sequence based on a predicate.
        Returns:
            An observable sequence that contains elements from the input
            sequence that satisfy the condition.
        """
        return AsyncRx.create(pipe(self, starfilter(predicate)))

    def starmap(self, mapper: Callable[..., TResult]) -> AsyncObservable[TResult]:
        """Map and spread the arguments to the mapper.

        Returns:
            An observable sequence whose elements are the result of
            invoking the mapper function on each element of the source.
        """

        return AsyncRx(pipe(self, starmap(mapper)))

    def take(self, count: int) -> AsyncObservable[TSource]:
        """Take the first elements from the stream.

        Returns a specified number of contiguous elements from the start of
        an observable sequence.

        Args:
            count Number of elements to take.

        Returns:
            An observable sequence that contains the specified number of
            elements from the start of the input sequence.
        """
        from .filtering import take

        return AsyncRx(pipe(self, take(count)))

    def take_last(self, count: int) -> AsyncObservable[TSource]:
        """Take last elements from stream.

        Returns a specified number of contiguous elements from the end of an
        observable sequence.

        Args:
            count: Number of elements to take.

        Returns:
            Stream[TSource, TSource]: [description]
        """
        from .filtering import take_last

        return AsyncRx(pipe(self, take_last(count)))

    def take_until(self, other: AsyncObservable[TResult]) -> AsyncObservable[TSource]:
        """Take elements until other.

        Returns the values from the source observable sequence until the
        other observable sequence produces a value.

        Args:
            other: The other async observable

        Returns:
            Stream[TSource, TSource]: [description]
        """
        from .filtering import take_until

        return AsyncRx(pipe(self, take_until(other)))

    def to_async_iterable(self) -> AsyncIterable[TSource]:
        from .leave import to_async_iterable

        return to_async_iterable(self)

    def with_latest_from(self, other: AsyncObservable[TOther]) -> "AsyncRx[Tuple[TSource, TOther]]":
        from .combine import with_latest_from

        return AsyncRx.create(pipe(self, with_latest_from(other)))


def as_async_observable(source: AsyncObservable[TSource]) -> AsyncObservable[TSource]:
    return AsyncAnonymousObservable(source.subscribe_async)


def as_chained(source: AsyncObservable[TSource]) -> AsyncRx[TSource]:
    return AsyncRx(source)


def choose(chooser: Callable[[TSource], Option[TSource]]) -> Stream[TSource, TSource]:
    """Choose.

    Applies the given function to each element of the stream and returns
    the stream comprised of the results for each element where the
    function returns Some with some value.

    Args:
        chooser: A function to transform or filter the stream
            by returning `Some(value)` or `Nothing`.

    Returns:
        The filtered and/or transformed stream.
    """

    from .filtering import choose

    return choose(chooser)


def choose_async(chooser: Callable[[TSource], Awaitable[Option[TSource]]]) -> Stream[TSource, TSource]:
    """Choose async.

    Applies the given async function to each element of the stream and
    returns the stream comprised of the results for each element where
    the function returns Some with some value.

    Args:
        chooser: An async function to transform or filter the stream
            by returning `Some(value)` or `Nothing`.

    Returns:
        The filtered and/or transformed stream.
    """

    from .filtering import choose_async

    return choose_async(chooser)


def combine_latest(other: AsyncObservable[TOther]) -> Stream[TSource, Tuple[TSource, TOther]]:
    from .combine import combine_latest

    return pipe(combine_latest(other))


def debounce(seconds: float) -> Stream[TSource, TSource]:
    """Debounce source stream.

    Ignores values from a source stream which are followed by another
    value before seconds has elapsed.

    Example:
        >>> ys = pipe(xs, debounce(5)) # 5 seconds

    Args:
        seconds: Duration of the throttle period for each value

    Returns:
        A partially applied debounce function that takes the source
        observable to debounce.
    """

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


def distinct_until_changed(source: AsyncObservable[TSource]) -> AsyncObservable[TSource]:
    from .filtering import distinct_until_changed

    return distinct_until_changed(source)


def empty() -> "AsyncObservable[TSource]":
    from .create import empty

    return empty()


def filter(predicate: Callable[[TSource], bool]) -> Callable[[AsyncObservable[TSource]], AsyncObservable[TSource]]:
    """Filter stream.

    Filters the elements of an observable sequence based on a predicate.
    Returns an observable sequence that contains elements from the input
    sequence that satisfy the condition.

    Args:
        predicate:
            A function to filter the stream by returning `True` to
            keep the item, or `False` to filter and remove the item.

    Returns:
        The filtered stream.
    """
    from .filtering import filter as _filter

    return _filter(predicate)


def filteri(predicate: Callable[[TSource, int], bool]) -> Stream[TSource, TSource]:
    """Filter with index.

    Filters the elements of an observable sequence based on a predicate
    and incorporating the element's index on each element of the source.

    Args:
        predicate: Function to test each element.

    Returns:
        An observable sequence that contains elements from the input
        sequence that satisfy the condition.
    """
    from .filtering import filteri

    return filteri(predicate)


def filter_async(
    predicate: Callable[[TSource], Awaitable[bool]]
) -> Callable[[AsyncObservable[TSource]], AsyncObservable[TSource]]:
    from .filtering import filter_async

    return filter_async(predicate)


def from_async(worker: Awaitable[TSource]) -> AsyncObservable[TSource]:
    from .create import of_async

    return of_async(worker)


def from_iterable(iterable: Iterable[TSource]) -> AsyncObservable[TSource]:
    """Convert an iterable to a source stream.

    Example:
        >>> xs = from_iterable([1,2,3])

    Returns:
        The source stream whose elements are pulled from the given
        (async) iterable sequence.
    """
    from .create import of_seq

    return of_seq(iterable)


def flat_map(mapper: Callable[[TSource], AsyncObservable[TResult]]) -> Stream[TSource, TResult]:
    from .transform import flat_map

    return flat_map(mapper)


def flat_mapi(mapper: Callable[[TSource, int], AsyncObservable[TResult]]) -> Stream[TSource, TResult]:
    from .transform import flat_mapi

    return flat_mapi(mapper)


def flat_map_async(mapper: Callable[[TSource], Awaitable[AsyncObservable[TResult]]]) -> Stream[TSource, TResult]:
    """Flap map async.

    Asynchronously projects each element of an observable sequence into
    an observable sequence and merges the resulting observable sequences
    back into one observable sequence.


    Args:
        mapperCallable ([type]): [description]
        Awaitable ([type]): [description]

    Returns:
        Stream[TSource, TResult]: [description]
    """
    from .transform import flat_map_async

    return flat_map_async(mapper)


def flat_map_latest_async(mapper: Callable[[TSource], Awaitable[AsyncObservable[TResult]]]) -> Stream[TSource, TResult]:
    """Flat map latest async.

    Asynchronosly transforms the items emitted by an source sequence
    into observable streams, and mirror those items emitted by the
    most-recently transformed observable sequence.

    Args:
        mapper (Callable[[TSource]): [description]
        Awaitable ([type]): [description]

    Returns:
        Stream[TSource, TResult]: [description]
    """
    from .transform import flat_map_latest_async

    return flat_map_latest_async(mapper)


def from_async_iterable(iter: AsyncIterable[TSource]) -> "AsyncObservable[TSource]":
    """Convert an async iterable to an async observable stream.

    Example:
        >>> xs = rx.from_async_iterable(async_iterable)

    Returns:
        The source stream whose elements are pulled from the given
        (async) iterable sequence.
    """
    from .create import of_async_iterable

    return AsyncRx(of_async_iterable(iter))


def interval(seconds: float, period: int) -> AsyncObservable[int]:
    """Returns an observable sequence that triggers the increasing
    sequence starting with 0 after the given msecs, and the after each
    period."""
    from .create import interval

    return interval(seconds, period)


def map(fn: Callable[[TSource], TResult]) -> Stream[TSource, TResult]:
    from .transform import map as _map

    return _map(fn)


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


def merge(other: AsyncObservable[TSource]) -> Stream[TSource, TSource]:
    from .create import of_seq

    def _(source: AsyncObservable[TSource]) -> AsyncObservable[TSource]:
        return pipe(of_seq([source, other]), merge_inner())

    return _


def merge_inner(max_concurrent: int = 0) -> Stream[AsyncObservable[TSource], TSource]:
    def _merge_inner(source: AsyncObservable[AsyncObservable[TSource]]) -> AsyncObservable[TSource]:
        from .combine import merge_inner

        return pipe(source, merge_inner(max_concurrent))

    return _merge_inner


def merge_seq(sources: Iterable[AsyncObservable[TSource]]) -> AsyncObservable[TSource]:
    from .create import of_seq

    return pipe(of_seq(sources), merge_inner())


def never() -> "AsyncObservable[TSource]":
    from .create import never

    return never()


def of_async(workflow: Awaitable[TSource]) -> AsyncObservable[TSource]:
    from .create import of_async

    return of_async(workflow)


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


def single(value: TSource) -> "AsyncObservable[TSource]":
    from .create import single

    return single(value)


def skip(count: int) -> Stream[TSource, TSource]:
    """Skip items in the stream.

    Bypasses a specified number of elements in an observable sequence
    and then returns the remaining elements.

    Args:
        count (int): Items to skip

    Returns:
        The result stream with skipped items.
    """
    from .filtering import skip

    return skip(count)


def skip_last(count: int) -> Stream[TSource, TSource]:
    """Bypasses a specified number of elements at the end of an
    observable sequence.

    This operator accumulates a queue with a length enough to store
    the first `count` elements. As more elements are received,
    elements are taken from the front of the queue and produced on
    the result sequence. This causes elements to be delayed.

    Args:
        count: Number of elements to bypass at the end of the
        source sequence.

    Returns:
        An observable sequence containing the source sequence
        elements except for the bypassed ones at the end.
    """
    from .filtering import skip_last

    return skip_last(count)


def starfilter(predicate: Callable[..., bool]) -> Stream[TSource, Tuple[Any, ...]]:
    """Filter and spread the arguments to the predicate.

    Filters the elements of an observable sequence based on a predicate.
    Returns:
        An observable sequence that contains elements from the input
        sequence that satisfy the condition.
    """
    from .filtering import starfilter

    return starfilter(predicate)


def starmap(mapper: Callable[..., TResult]) -> Stream[TSource, TResult]:
    """Map and spread the arguments to the mapper.

    Returns an observable sequence whose elements are the result of
    invoking the mapper function on each element of the source."""

    from .transform import starmap

    return starmap(mapper)


def switch_latest() -> Stream[AsyncObservable[TSource], TSource]:
    from .transform import switch_latest

    return switch_latest


def take(count: int) -> Stream[TSource, TSource]:
    """Take the first elements from the stream.

    Returns a specified number of contiguous elements from the start of
    an observable sequence.

    Args:
        count Number of elements to take.

    Returns:
        An observable sequence that contains the specified number of
        elements from the start of the input stream.
    """
    from .filtering import take

    return take(count)


def take_last(count: int) -> Stream[TSource, TSource]:
    """Take last elements from stream.

    Returns a specified number of contiguous elements from the end of an
    observable sequence.

    Args:
        count: Number of elements to take.

    Returns:
        An observable stream that contains the specified number of
        elements from the end of the input stream.
    """
    from .filtering import take_last

    return take_last(count)


def take_until(other: AsyncObservable[TResult]) -> Stream[TSource, TSource]:
    """Take elements until other.

    Returns the values from the source observable sequence until the
    other observable sequence produces a value.

    Args:
        other: The other async observable

    Returns:
        Stream[TSource, TSource]: [description]
    """
    from .filtering import take_until

    return take_until(other)


def timer(due_time: float) -> AsyncObservable[int]:
    """Returns an observable sequence that triggers the value 0
    after the given duetime in milliseconds.
    """
    from .create import timer

    return timer(due_time)


def to_async_iterable(source: AsyncObservable[TSource]) -> AsyncIterable[TSource]:
    from .leave import to_async_iterable

    return to_async_iterable(source)


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
    "filteri",
    "filter_async",
    "from_async",
    "from_iterable",
    "flat_map",
    "flat_mapi",
    "flat_map_async",
    "flat_mapi_async",
    "flat_map_latest_async",
    "map",
    "map_async",
    "merge",
    "merge_inner",
    "merge_seq",
    "never",
    "retry",
    "run",
    "single",
    "skip",
    "skip_last",
    "starfilter",
    "starmap",
    "Stream",
    "switch_latest",
    "to_async_iterable",
    "take",
    "take_last",
]


# flake8: noqa
from ._version import get_versions

__version__ = get_versions()["version"]  # type: ignore

del get_versions
