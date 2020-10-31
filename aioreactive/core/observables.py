from typing import Awaitable, Callable, Iterable, TypeVar

from fslash.system import AsyncDisposable

from .subscription import subscription
from .types import AsyncObservable, AsyncObserver

TSource = TypeVar("TSource")
TResult = TypeVar("TResult")
TError = TypeVar("TError")
T1 = TypeVar("T1")
T2 = TypeVar("T2")


class AsyncAnonymousObservable(AsyncObservable[TSource]):

    """An AsyncObservable that works with Python special methods.

    This class supports python special methods including pipe-forward
    using OR operator. All operators are provided as partially applied
    plain old functions
    """

    def __init__(self, subscribe: Callable[[AsyncObserver[TSource]], Awaitable[AsyncDisposable]]) -> None:
        self._subscribe = subscribe

    def subscribe_async(self, obv: AsyncObserver[TSource]) -> Awaitable:
        print("AsyncAnonymousObservable:subscribe")
        return subscription(self._subscribe, obv)

    def __getitem__(self, key) -> "AsyncObservable[TSource]":
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

         Return a sliced source stream."""

        from aioreactive.operators.slice import slice as _slice

        if isinstance(key, slice):
            start, stop, step = key.start, key.stop, key.step
        elif isinstance(key, int):
            start, stop, step = key, key + 1, 1
        else:
            raise TypeError("Invalid argument type.")

        return _slice(start, stop, step, self)


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

    async def subscribe_async(self, obv: AsyncObserver) -> AsyncDisposable:
        return await self._source.subscribe_async(obv)

    def __getitem__(self, key) -> "AsyncChainedObservable":
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
    def from_iterable(cls, iter):
        return AsyncChainedObservable(AsyncObservable.from_iterable(iter))

    @classmethod
    def just(cls, value) -> "AsyncChainedObservable":
        return AsyncChainedObservable(AsyncObservable.unit(value))

    @classmethod
    def empty(cls) -> "AsyncChainedObservable":
        return AsyncChainedObservable(AsyncObservable.empty())

    def debounce(self, seconds: float) -> "AsyncChainedObservable":
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

    def delay(self, seconds: float) -> "AsyncChainedObservable":
        from aioreactive.operators.delay import delay

        return AsyncChainedObservable(delay(seconds, self))

    def where(self, predicate: Callable) -> "AsyncChainedObservable":
        from aioreactive.operators.filter import filter

        return AsyncChainedObservable(filter(predicate, self))

    def select_many(self, selector: Callable) -> "AsyncChainedObservable":
        from aioreactive.operators.flat_map import flat_map

        return AsyncChainedObservable(flat_map(selector, self))

    def select(self, selector: Callable[[TSource], TResult]) -> "AsyncChainedObservable[TResult]":
        from aioreactive.operators.map import map

        mapping = map(selector)
        return AsyncChainedObservable(mapping(self))

    def merge(self, other: "AsyncChainedObservable") -> "AsyncChainedObservable":
        from aioreactive.operators.merge import merge

        return AsyncChainedObservable(merge(other, self))

    def with_latest_from(self, mapper, other) -> "AsyncChainedObservable":
        from aioreactive.operators.with_latest_from import with_latest_from

        return AsyncChainedObservable(with_latest_from(mapper, other, self))


def as_chained(source: AsyncObservable) -> AsyncChainedObservable:
    return AsyncChainedObservable(source)
