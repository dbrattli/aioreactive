"""Aioreactive module.

Contains the AsyncRx chained observable that allows method chaining of all operators.

Also contains all operators as plain functions.

To use this module:

Example:
    >>> import aioreactive as rx
    >>> xs = rx.from_iterable([1, 2, 3])
    >>> ...

"""

from __future__ import annotations

from collections.abc import AsyncIterable, Awaitable, Callable, Iterable
from typing import Any, TypeVar

from expression import Option, curry_flip, pipe
from expression.system.disposable import AsyncDisposable
from typing_extensions import TypeVarTuple, Unpack

from .observables import AsyncAnonymousObservable, AsyncIterableObservable
from .observers import (
    AsyncAnonymousObserver,
    AsyncAwaitableObserver,
    AsyncIteratorObserver,
    AsyncNotificationObserver,
)
from .subject import AsyncSingleSubject, AsyncSubject
from .subscription import run
from .types import AsyncObservable, AsyncObserver, CloseAsync, SendAsync, ThrowAsync


_A = TypeVar("_A")
_B = TypeVar("_B")
_C = TypeVar("_C")
_D = TypeVar("_D")
_V = TypeVarTuple("_V")
_TSource = TypeVar("_TSource")
_TResult = TypeVar("_TResult")
_TOther = TypeVar("_TOther")


class AsyncRx(AsyncObservable[_TSource]):
    """An AsyncObservable class similar to classic Rx.

    This class provides all operators as methods and supports
    method chaining.

    Example:
    >>> AsyncRx.from_iterable([1,2,3]).map(lambda x: x + 2).filter(lambda x: x < 3)

    All methods are lazy imported.
    """

    def __init__(self, source: AsyncObservable[_TSource]) -> None:
        self._source = source

    async def subscribe_async(
        self,
        send: SendAsync[_TSource] | AsyncObserver[_TSource] | None = None,
        throw: ThrowAsync | None = None,
        close: CloseAsync | None = None,
    ) -> AsyncDisposable:
        """Subscribe to the async observable.

        Uses the given observer to subscribe asynchronously to the async
        observable.

        Args:
            send: The async observer or the send function to subscribe.
            throw: The throw function to subscribe.
            close: The close function to subscribe.

        Returns:
            An async disposable that can be used to dispose the
            subscription.
        """
        observer = send if isinstance(send, AsyncObserver) else AsyncAnonymousObserver(send, throw, close)
        return await self._source.subscribe_async(observer)

    def __getitem__(self, key: slice | int) -> AsyncRx[_TSource]:
        """Slice observable.

        Slices the given source stream using Python slice notation.
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

        return AsyncRx(pipe(self, _slice(start, stop, step or 1)))

    @staticmethod
    def create(source: AsyncObservable[_TResult]) -> AsyncRx[_TResult]:
        """Create `AsyncChainedObservable`.

        Helper method for creating an `AsyncChainedObservable`.
        """
        return AsyncRx(source)

    @classmethod
    def empty(cls) -> AsyncRx[_TSource]:
        return AsyncRx(empty())

    @classmethod
    def from_iterable(cls, iter: Iterable[_TOther]) -> AsyncRx[_TOther]:
        return AsyncRx(from_iterable(iter))

    @staticmethod
    def from_async_iterable(iter: AsyncIterable[_TResult]) -> AsyncRx[_TResult]:
        """Convert an async iterable to an async observable stream.

        Example:
            >>> xs = AsyncRx.from_async_iterable(async_iterable)

        Returns:
            The source stream whose elements are pulled from the given
            (async) iterable sequence.
        """
        return AsyncRx(from_async_iterable(iter))

    @classmethod
    def single(cls, value: _TSource) -> AsyncRx[_TSource]:
        from .create import single

        return AsyncRx(single(value))

    def as_async_observable(self) -> AsyncObservable[_TSource]:
        return AsyncAnonymousObservable(self.subscribe_async)

    def choose(self, chooser: Callable[[_TSource], Option[_TSource]]) -> AsyncRx[_TSource]:
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

    def choose_async(self, chooser: Callable[[_TSource], Awaitable[Option[_TSource]]]) -> AsyncRx[_TSource]:
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

    def combine_latest(self, other: AsyncObservable[_TOther]) -> AsyncRx[tuple[_TSource, _TOther]]:
        from .combine import combine_latest

        xs = pipe(
            self,
            combine_latest(other),
        )
        return AsyncRx.create(xs)

    def concat(self, other: AsyncObservable[_TSource]) -> AsyncRx[_TSource]:
        from .combine import concat_seq

        return AsyncRx(concat_seq([self, other]))

    def debounce(self, seconds: float) -> AsyncRx[_TSource]:
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

    def delay(self, seconds: float) -> AsyncRx[_TSource]:
        from .timeshift import delay

        return AsyncRx(pipe(self, delay(seconds)))

    def distinct_until_changed(self) -> AsyncRx[_TSource]:
        from .filtering import distinct_until_changed

        return AsyncRx(distinct_until_changed(self))

    def filter(self, predicate: Callable[[_TSource], bool]) -> AsyncRx[_TSource]:
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

    def filteri(self, predicate: Callable[[_TSource, int], bool]) -> AsyncRx[_TSource]:
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

    def filter_async(self, predicate: Callable[[_TSource], Awaitable[bool]]) -> AsyncRx[_TSource]:
        from .filtering import filter_async

        return AsyncRx(pipe(self, filter_async(predicate)))

    def flat_map(self, selector: Callable[[_TSource], AsyncObservable[_TResult]]) -> AsyncRx[_TResult]:
        from .transform import flat_map

        return AsyncRx.create(pipe(self, flat_map(selector)))

    def flat_map_async(self, selector: Callable[[_TSource], Awaitable[AsyncObservable[_TResult]]]) -> AsyncRx[_TResult]:
        from .transform import flat_map_async

        return AsyncRx.create(pipe(self, flat_map_async(selector)))

    def flat_map_latest_async(
        self, mapper: Callable[[_TSource], Awaitable[AsyncObservable[_TResult]]]
    ) -> AsyncRx[_TResult]:
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

    def map(self, selector: Callable[[_TSource], _TResult]) -> AsyncRx[_TResult]:
        from .transform import map as map_

        return AsyncRx(pipe(self, map_(selector)))

    def merge(self, other: AsyncObservable[_TSource]) -> AsyncRx[_TSource]:
        from .combine import merge_inner
        from .create import of_seq

        source = of_seq([self, other])
        return pipe(
            source,
            merge_inner(0),
            AsyncRx.create,
        )

    def reduce(self, accumulator: Callable[[_TResult, _TSource], _TResult], initial: _TResult) -> AsyncRx[_TResult]:
        return pipe(self, reduce(accumulator, initial), AsyncRx[_TResult])

    def reduce_async(
        self,
        accumulator: Callable[[_TResult, _TSource], Awaitable[_TResult]],
        initial: _TResult,
    ) -> AsyncRx[_TResult]:
        return pipe(self, reduce_async(accumulator, initial), AsyncRx[_TResult])

    def skip(self, count: int) -> AsyncRx[_TSource]:
        """Skip items from start of the stream.

        Bypasses a specified number of elements in an observable sequence
        and then returns the remaining elements.

        Args:
            count: Items to skip

        Returns:
            Stream[TSource, TSource]: [description]
        """
        return AsyncRx(
            pipe(
                self,
                skip(count),
            )
        )

    def skip_last(self, count: int) -> AsyncRx[_TSource]:
        """Skip the last items of the observable sequencerm .

        Bypasses a specified number of elements at the end of an
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

    def starfilter(
        self: AsyncObservable[tuple[Unpack[_V]]], predicate: Callable[[Unpack[_V]], bool]
    ) -> AsyncRx[_TSource]:
        """Filter and spread the arguments to the predicate.

        Filters the elements of an observable sequence based on a predicate.

        Returns:
            An observable sequence that contains elements from the input
            sequence that satisfy the condition.
        """
        xs = pipe(self, starfilter(predicate))
        return AsyncRx.create(xs)

    def starmap(self: AsyncRx[tuple[Unpack[_V]]], mapper: Callable[[Unpack[_V]], _TResult]) -> AsyncRx[_TResult]:
        """Map and spread the arguments to the mapper.

        Returns:
            An observable sequence whose elements are the result of
            invoking the mapper function on each element of the source.
        """
        return AsyncRx(pipe(self, starmap(mapper)))

    def take(self, count: int) -> AsyncRx[_TSource]:
        """Take the first elements from the stream.

        Returns a specified number of contiguous elements from the start of
        an observable sequence.

        Args:
            count: Number of elements to take.

        Returns:
            An observable sequence that contains the specified number of
            elements from the start of the input sequence.
        """
        from .filtering import take

        return AsyncRx(pipe(self, take(count)))

    def take_last(self, count: int) -> AsyncRx[_TSource]:
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

    def take_until(self, other: AsyncObservable[Any]) -> AsyncRx[_TSource]:
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

    def to_async_iterable(self) -> AsyncIterable[_TSource]:
        from .leave import to_async_iterable

        return to_async_iterable(self)

    def with_latest_from(self, other: AsyncObservable[_TOther]) -> AsyncRx[tuple[_TSource, _TOther]]:
        from .combine import with_latest_from

        return AsyncRx.create(pipe(self, with_latest_from(other)))


def as_async_observable(source: AsyncObservable[_TSource]) -> AsyncObservable[_TSource]:
    return AsyncAnonymousObservable(source.subscribe_async)


def as_chained(source: AsyncObservable[_TSource]) -> AsyncRx[_TSource]:
    return AsyncRx(source)


def choose(
    chooser: Callable[[_TSource], Option[_TResult]],
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
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


def choose_async(
    chooser: Callable[[_TSource], Awaitable[Option[_TResult]]],
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
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


@curry_flip(1)
def combine_latest(
    source: AsyncObservable[_TSource], other: AsyncObservable[_TOther]
) -> AsyncObservable[tuple[_TSource, _TOther]]:
    from .combine import combine_latest

    return pipe(source, combine_latest(other))


def debounce(
    seconds: float,
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TSource]]:
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


def catch(
    handler: Callable[[Exception], AsyncObservable[_TSource]],
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TSource]]:
    from .transform import catch

    return catch(handler)


def concat(
    other: AsyncObservable[_TSource],
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TSource]]:
    """Concatenate observables.

    Concatenates an observable sequence with another observable
    sequence.
    """

    def _concat(source: AsyncObservable[_TSource]) -> AsyncObservable[_TSource]:
        from .combine import concat_seq

        return concat_seq([source, other])

    return _concat


def concat_seq(
    sources: Iterable[AsyncObservable[_TSource]],
) -> AsyncObservable[_TSource]:
    """Concatenates an iterable of observable sequences."""
    from .combine import concat_seq

    return concat_seq(sources)


def defer(factory: Callable[[], AsyncObservable[_TSource]]) -> AsyncObservable[_TSource]:
    """Defer observable.

    Returns an observable sequence that invokes the specified factory
    function whenever a new observer subscribes.
    """
    from .create import defer

    return defer(factory)


def delay(
    seconds: float,
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TSource]]:
    from .timeshift import delay

    return delay(seconds)


def distinct_until_changed(
    source: AsyncObservable[_TSource],
) -> AsyncObservable[_TSource]:
    from .filtering import distinct_until_changed

    return distinct_until_changed(source)


def empty() -> AsyncObservable[Any]:
    from .create import empty

    return empty()


def filter(predicate: Callable[[_TSource], bool]) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TSource]]:
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


def filteri(
    predicate: Callable[[_TSource, int], bool],
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TSource]]:
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
    predicate: Callable[[_TSource], Awaitable[bool]],
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TSource]]:
    from .filtering import filter_async

    return filter_async(predicate)


def from_async(worker: Awaitable[_TSource]) -> AsyncObservable[_TSource]:
    from .create import of_async

    return of_async(worker)


def from_iterable(iterable: Iterable[_TSource]) -> AsyncObservable[_TSource]:
    """Convert an iterable to a source stream.

    Example:
        >>> xs = from_iterable([1,2,3])

    Returns:
        The source stream whose elements are pulled from the given
        (async) iterable sequence.
    """
    from .create import of_seq

    return of_seq(iterable)


def flat_map(
    mapper: Callable[[_TSource], AsyncObservable[_TResult]],
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
    from .transform import flat_map

    return flat_map(mapper)


def flat_mapi(
    mapper: Callable[[_TSource, int], AsyncObservable[_TResult]],
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
    from .transform import flat_mapi

    return flat_mapi(mapper)


def flat_map_async(
    mapper: Callable[[_TSource], Awaitable[AsyncObservable[_TResult]]],
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
    """Flap map async.

    Asynchronously projects each element of an observable sequence into
    an observable sequence and merges the resulting observable sequences
    back into one observable sequence.

    Args:
        mapper: A transform function to apply to each element or an

    Returns:
        Stream[TSource, TResult]: [description]
    """
    from .transform import flat_map_async

    return flat_map_async(mapper)


def flat_map_latest_async(
    mapper: Callable[[_TSource], Awaitable[AsyncObservable[_TResult]]],
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
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


def from_async_iterable(iter: AsyncIterable[_TSource]) -> AsyncObservable[_TSource]:
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
    """Observable interval.

    Returns an observable sequence that triggers the increasing
    sequence starting with 0 after the given msecs, and the after each
    period.
    """
    from .create import interval

    return interval(seconds, period)


def map(fn: Callable[[_TSource], _TResult]) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
    from .transform import map as _map

    return _map(fn)


def map_async(
    mapper: Callable[[_TSource], Awaitable[_TResult]],
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
    """Map asynchrnously.

    Returns an observable sequence whose elements are the result of
    invoking the async mapper function on each element of the
    source.
    """
    from .transform import map_async as map_async_

    return map_async_(mapper)


def mapi_async(
    mapper: Callable[[_TSource, int], Awaitable[_TResult]],
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
    """Map indexed asynchronously.

    Returns an observable sequence whose elements are the result of
    invoking the async mapper function by incorporating the element's
    index on each element of the source.
    """
    from .transform import mapi_async

    return mapi_async(mapper)


def mapi(
    mapper: Callable[[_TSource, int], _TResult],
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
    """Map indexed.

    Returns an observable sequence whose elements are the result of
    invoking the mapper function and incorporating the element's index
    on each element of the source.
    """
    from .transform import mapi

    return mapi(mapper)


def merge(
    other: AsyncObservable[_TSource],
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TSource]]:
    from .create import of_seq

    def _(source: AsyncObservable[_TSource]) -> AsyncObservable[_TSource]:
        ret = pipe(
            of_seq([source, other]),
            merge_inner(),
        )
        return ret

    return _


def merge_inner(
    max_concurrent: int = 0,
) -> Callable[[AsyncObservable[AsyncObservable[_TSource]]], AsyncObservable[_TSource]]:
    def _merge_inner(
        source: AsyncObservable[AsyncObservable[_TSource]],
    ) -> AsyncObservable[_TSource]:
        from .combine import merge_inner

        return pipe(source, merge_inner(max_concurrent))

    return _merge_inner


def merge_seq(
    sources: Iterable[AsyncObservable[_TSource]],
) -> AsyncObservable[_TSource]:
    from .create import of_seq

    return pipe(
        of_seq(sources),
        merge_inner(),
    )


def never() -> AsyncObservable[Any]:
    from .create import never

    return never()


def of_async(workflow: Awaitable[_TSource]) -> AsyncObservable[_TSource]:
    from .create import of_async

    return of_async(workflow)


def reduce(
    accumulator: Callable[[_TResult, _TSource], _TResult],
    initial: _TResult,
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
    """The reduce operator.

    If an error occurs either in the accumulator or the source the subscription is disposed and the error is thrown.

    Args:
        accumulator: An accumulator function
        initial: The initial value

    Returns:
        The reduce operator function
    """
    from .transform import reduce as _reduce

    return _reduce(accumulator, initial)


def reduce_async(
    accumulator: Callable[[_TResult, _TSource], Awaitable[_TResult]],
    initial: _TResult,
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
    """The async reduce operator.

    See the `reduce` operator.

    Args:
        accumulator (Callable[[_TResult, _TSource], Awaitable[_TResult]]): An async accumulator function
        initial (_TResult): The initial value

    Returns:
        Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]: The operator function
    """
    from .transform import reduce_async as _reduce

    return _reduce(accumulator, initial)


def retry(
    retry_count: int,
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TSource]]:
    from .transform import retry

    return retry(retry_count)


def scan(
    accumulator: Callable[[_TResult, _TSource], _TResult],
    initial: _TResult,
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
    """The scan operator.

    This operator runs the accumulator for every value from the source with the current state. After every run, the new
    computed value is returned.

    Args:
        accumulator: An accumulator function.
        initial: The initial state.

    Returns:
        A single-value observable.
    """
    from .transform import scan as _scan

    return _scan(accumulator, initial)


def scan_async(
    accumulator: Callable[[_TResult, _TSource], Awaitable[_TResult]],
    initial: _TResult,
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
    """Async version of the scan operator.

    Args:
        accumulator: An async accumulator function.
        initial: The initial state.

    Returns:
        The scan operator.
    """
    from .transform import scan_async as _scan_async

    return _scan_async(accumulator, initial)


def subscribe_async(
    obv: AsyncObserver[_TSource],
) -> Callable[[AsyncObservable[_TSource]], Awaitable[AsyncDisposable]]:
    """A pipeable subscribe async.

    Example:
        >>> await pipe(xs, filter(predicate), subscribe_async)
    """
    from .subscription import subscribe_async

    return subscribe_async(obv)


def single(value: _TSource) -> AsyncObservable[_TSource]:
    from .create import single

    return single(value)


def skip(
    count: int,
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TSource]]:
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


def skip_last(
    count: int,
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TSource]]:
    """Skip the last items of the observable sequence.

    Bypasses a specified number of elements at the end of an
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


def starfilter(
    predicate: Callable[[Unpack[_V]], bool],
) -> Callable[[AsyncObservable[tuple[Unpack[_V]]]], AsyncObservable[Any]]:
    """Filter and spread the arguments to the predicate.

    Filters the elements of an observable sequence based on a predicate.

    Returns:
        An observable sequence that contains elements from the input
        sequence that satisfy the condition.
    """
    from .filtering import starfilter

    return starfilter(predicate)


def starmap(
    mapper: Callable[[Unpack[_V]], _TResult],
) -> Callable[[AsyncObservable[tuple[Unpack[_V]]]], AsyncObservable[_TResult]]:
    """Map and spread the arguments to the mapper.

    Returns an observable sequence whose elements are the result of
    invoking the mapper function on each element of the source.
    """
    from .transform import starmap

    return starmap(mapper)


def switch_latest() -> Callable[[AsyncObservable[AsyncObservable[_TSource]]], AsyncObservable[_TSource]]:
    from .transform import switch_latest as switch_latest_

    return switch_latest_


def take(
    count: int,
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TSource]]:
    """Take the first elements from the stream.

    Returns a specified number of contiguous elements from the start of
    an observable sequence.

    Args:
        count: Number of elements to take.

    Returns:
        An observable sequence that contains the specified number of
        elements from the start of the input stream.
    """
    from .filtering import take

    return take(count)


def take_last(
    count: int,
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TSource]]:
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


def take_until(
    other: AsyncObservable[Any],
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TSource]]:
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
    """Observable timer.

    Returns an observable sequence that triggers the value 0
    after the given duetime in milliseconds.
    """
    from .create import timer

    return timer(due_time)


def to_async_iterable(source: AsyncObservable[_TSource]) -> AsyncIterable[_TSource]:
    from .leave import to_async_iterable

    return to_async_iterable(source)


@curry_flip(1)
def with_latest_from(
    source: AsyncObservable[_TSource],
    other: AsyncObservable[_TOther],
) -> AsyncObservable[tuple[_TSource, _TOther]]:
    from .combine import with_latest_from

    return pipe(
        source,
        with_latest_from(other),
    )


__all__ = [
    "AsyncAnonymousObservable",
    "AsyncAnonymousObserver",
    "AsyncAwaitableObserver",
    "AsyncIteratorObserver",
    "AsyncIterableObservable",
    "AsyncNotificationObserver",
    "AsyncObservable",
    "AsyncObserver",
    "AsyncSingleSubject",
    "AsyncSubject",
    "AsyncDisposable",
    "catch",
    "choose",
    "choose_async",
    "combine_latest",
    "concat",
    "concat_seq",
    "delay",
    "empty",
    "filter",
    "filteri",
    "filter_async",
    "from_async",
    "from_iterable",
    "flat_map",
    "flat_mapi",
    "flat_map_async",
    "flat_map_latest_async",
    "map",
    "map_async",
    "merge",
    "merge_inner",
    "merge_seq",
    "never",
    "retry",
    "run",
    "scan",
    "scan_async",
    "single",
    "skip",
    "skip_last",
    "starfilter",
    "starmap",
    "switch_latest",
    "to_async_iterable",
    "take",
    "take_last",
    "pipe",
]
