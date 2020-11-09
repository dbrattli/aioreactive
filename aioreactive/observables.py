import logging
from typing import Awaitable, Callable, Iterable, Tuple, TypeVar, Union

from expression.core import pipe
from expression.system import AsyncDisposable

from .types import AsyncObservable, AsyncObserver

TSource = TypeVar("TSource")
TResult = TypeVar("TResult")
TOther = TypeVar("TOther")
TError = TypeVar("TError")
T1 = TypeVar("T1")
T2 = TypeVar("T2")

log = logging.getLogger(__name__)


class AsyncAnonymousObservable(AsyncObservable[TSource]):

    """An AsyncObservable that works with Python special methods.

    This class supports python special methods including pipe-forward
    using OR operator. All operators are provided as partially applied
    plain old functions
    """

    def __init__(self, subscribe: Callable[[AsyncObserver[TSource]], Awaitable[AsyncDisposable]]) -> None:
        self._subscribe = subscribe

    async def subscribe_async(self, observer: AsyncObserver[TSource]) -> AsyncDisposable:
        log.debug("AsyncAnonymousObservable:subscribe_async(%s)", self._subscribe)
        return await self._subscribe(observer)


class AsyncChainedObservable(AsyncObservable[TSource]):
    """An AsyncChainedObservable example class similar to Rx.

    This class supports has all operators as methods and supports
    method chaining.

    Subscribe is also a method.

    All methods are lazy imported.
    """

    def __init__(self, source: AsyncObservable[TSource]) -> None:
        super().__init__()
        self._source = source

    @classmethod
    def create(cls, source: AsyncObservable[TSource]) -> "AsyncChainedObservable[TSource]":
        """Create `AsyncChainedObservable`.

        Helper method for creating an `AsyncChainedObservable` to the
        the generic type rightly inferred by Pylance (__init__ returns None).
        """
        return cls(source)

    async def subscribe_async(self, observer: AsyncObserver[TSource]) -> AsyncDisposable:
        return await self._source.subscribe_async(observer)

    def __getitem__(self, key: Union[slice, int]) -> "AsyncChainedObservable[TSource]":
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

        return AsyncChainedObservable(super(AsyncChainedObservable, self).__getitem__(key))

    @classmethod
    def from_iterable(cls, iter: Iterable[TSource]) -> "AsyncChainedObservable[TSource]":
        from .create import of_seq

        return AsyncChainedObservable(of_seq(iter))

    @classmethod
    def empty(cls) -> "AsyncChainedObservable[TSource]":
        from .create import empty

        return AsyncChainedObservable(empty())

    @classmethod
    def single(cls, value: TSource) -> "AsyncChainedObservable[TSource]":
        from .create import single

        return AsyncChainedObservable(single(value))

    def combine_latest(self, other: TOther) -> "AsyncChainedObservable[Tuple[TSource, TOther]]":
        from .combine import combine_latest

        return pipe(self, combine_latest(other), AsyncChainedObservable.create)

    def debounce(self, seconds: float) -> "AsyncChainedObservable[TSource]":
        """Debounce observable source.

        Ignores values from a source stream which are followed by
        another value before seconds has elapsed.

        Example:
        partial = debounce(5) # 5 seconds

        Keyword arguments:
        seconds -- Duration of the throttle period for each value

        Returns partially applied function that takes a source sequence.
        """

        from aioreactive.operators.debounce import debounce

        return AsyncChainedObservable(debounce(seconds, self))

    def delay(self, seconds: float) -> "AsyncChainedObservable[TSource]":
        from .timeshift import delay

        return AsyncChainedObservable(delay(seconds)(self))

    def where(self, predicate: Callable[[TSource], TSource]) -> "AsyncChainedObservable[TSource]":
        from .filter import filter

        return pipe(self, filter(predicate), AsyncChainedObservable.create)

    def select_many(self, selector: Callable[[TSource], AsyncObservable[TResult]]) -> "AsyncChainedObservable[TResult]":
        from .transform import flat_map

        return pipe(self, flat_map(selector), AsyncChainedObservable.create)

    def select(self, selector: Callable[[TSource], TResult]) -> "AsyncChainedObservable[TResult]":
        from .transform import map

        return pipe(self, map(selector), AsyncChainedObservable.create)

    def merge(self, other: AsyncObservable[TSource]) -> "AsyncChainedObservable[TSource]":
        from .combine import merge_inner
        from .create import of_seq

        source = of_seq([self, other])
        return pipe(source, merge_inner(0), AsyncChainedObservable.create)

    def with_latest_from(self, mapper, other) -> "AsyncChainedObservable":
        from aioreactive.operators.with_latest_from import with_latest_from

        return AsyncChainedObservable(with_latest_from(mapper, other, self))


def as_chained(source: AsyncObservable[TSource]) -> AsyncChainedObservable[TSource]:
    return AsyncChainedObservable(source)
