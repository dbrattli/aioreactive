from typing import Callable

from aioreactive.core import AsyncObservable, subscribe, AsyncObserver


class ChainedAsyncObservable(AsyncObservable):
    """An ChainedAsyncObservable example class similar to RxPY.

    This class supports has all operators as methods.

    Subscribe is also a method.

    All methods are lazy imported.
    """

    def __init__(self, source: AsyncObservable = None):
        super().__init__()
        self._source = source

    async def subscribe(self, obv: AsyncObserver):
        return await subscribe(self, obv)

    def __getitem__(self, key) -> 'ChainedAsyncObservable':
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

        return ChainedAsyncObservable(super(ChainedAsyncObservable, self).__getitem__(key))

    def __add__(self, other) -> 'ChainedAsyncObservable':
        """Pythonic version of concat

        Example:
        zs = xs + ys
        Returns self.concat(other)"""

        xs = super(ChainedAsyncObservable, self).__add__(other)
        return ChainedAsyncObservable(xs)

    def __iadd__(self, other):
        """Pythonic use of concat

        Example:
        xs += ys

        Returns self.concat(self, other)"""

        xs = super(ChainedAsyncObservable, self).__iadd__(other)
        return ChainedAsyncObservable(xs)

    @classmethod
    def from_iterable(cls, iter):
        return ChainedAsyncObservable(AsyncObservable.from_iterable(iter))

    @classmethod
    def just(cls, value) -> 'ChainedAsyncObservable':
        return ChainedAsyncObservable(AsyncObservable.unit(value))

    @classmethod
    def empty(cls) -> 'ChainedAsyncObservable':
        return ChainedAsyncObservable(AsyncObservable.empty())

    def debounce(self, seconds: float) -> 'ChainedAsyncObservable':
        """Debounce observable source.

        Ignores values from a source stream which are followed by
        another value before seconds has elapsed.

        Example:
        partial = debounce(5) # 5 seconds

        Keyword arguments:
        seconds -- Duration of the throttle period for each value

        Returns partially applied function that takes a source sequence.
        """

        from aioreactive.core.operators.debounce import debounce
        return ChainedAsyncObservable(debounce(seconds, self))

    def delay(self, seconds: float) -> 'ChainedAsyncObservable':
        from aioreactive.core.operators.delay import delay
        return ChainedAsyncObservable(delay(seconds, self))

    def where(self, predicate: Callable) -> 'ChainedAsyncObservable':
        from aioreactive.core.operators.filter import filter
        return ChainedAsyncObservable(filter(predicate, self))

    def select_many(self, selector: Callable) -> 'ChainedAsyncObservable':
        from aioreactive.core.operators.flat_map import flat_map
        return ChainedAsyncObservable(flat_map(selector, self))

    def select(self, selector: Callable) -> 'ChainedAsyncObservable':
        from aioreactive.core.operators.map import map
        return ChainedAsyncObservable(map(selector, self))

    def merge(self, other: 'ChainedAsyncObservable') -> 'ChainedAsyncObservable':
        from aioreactive.core.operators.merge import merge
        return ChainedAsyncObservable(merge(other, self))

    def with_latest_from(self, mapper, other) -> 'ChainedAsyncObservable':
        from aioreactive.core.operators.with_latest_from import with_latest_from
        return ChainedAsyncObservable(with_latest_from(mapper, other, self))


def chain(source: AsyncObservable) -> ChainedAsyncObservable:
    return ChainedAsyncObservable(source)
