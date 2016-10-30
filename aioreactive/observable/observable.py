from typing import Callable

from aioreactive.core import AsyncSource, start
from aioreactive.producer import Producer

from .observer import AsyncObserver, AsyncSinkObserver


class AsyncObservable(Producer):
    """An AsyncObservable example class similar to RxPY.

    This class supports has all operators as methods.

    Subscribe is also a method.

    All methods are lazy imported.
    """

    def __init__(self, source: AsyncSource = None):
        super().__init__()
        self._source = source

    async def subscribe(self, obv: AsyncObserver):
        _sink = await AsyncSinkObserver().__astart__(obv)
        return await start(self, _sink)

    def __getitem__(self, key) -> "AsyncObservable":
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

        return AsyncObservable(super(AsyncObservable, self).__getitem__(key))

    def __add__(self, other) -> "AsyncObservable":
        """Pythonic version of concat

        Example:
        zs = xs + ys
        Returns self.concat(other)"""

        xs = super(AsyncObservable, self).__add__(other)
        return AsyncObservable(xs)

    def __iadd__(self, other):
        """Pythonic use of concat

        Example:
        xs += ys

        Returns self.concat(self, other)"""

        xs = super(AsyncObservable, self).__iadd__(other)
        return AsyncObservable(xs)

    @classmethod
    def from_iterable(cls, iter):
        return AsyncObservable(Producer.from_iterable(iter))

    @classmethod
    def just(cls, value) -> "AsyncObservable":
        return AsyncObservable(Producer.unit(value))

    @classmethod
    def empty(cls) -> "AsyncObservable":
        return AsyncObservable(Producer.empty())

    def debounce(self, seconds: float) -> "AsyncObservable":
        """Debounce observable source.

        Ignores values from a source stream which are followed by
        another value before seconds has elapsed.

        Example:
        partial = debounce(5) # 5 seconds

        Keyword arguments:
        seconds -- Duration of the throttle period for each value

        Returns partially applied function that takes a source sequence.
        """

        from aioreactive.core.sources.debounce import debounce
        return AsyncObservable(debounce(seconds, self))

    def delay(self, seconds: float) -> "AsyncObservable":
        from aioreactive.core.sources.delay import delay
        return AsyncObservable(delay(seconds, self))

    def where(self, predicate: Callable) -> "AsyncObservable":
        from aioreactive.core.sources.filter import filter
        return AsyncObservable(filter(predicate, self))

    def select_many(self, selector: Callable) -> "AsyncObservable":
        from aioreactive.core.sources.flat_map import flat_map
        return AsyncObservable(flat_map(selector, self))

    def select(self, selector: Callable) -> "AsyncObservable":
        from aioreactive.core.sources.map import map
        return AsyncObservable(map(selector, self))

    def merge(self, other: AsyncSource) -> "AsyncObservable":
        from aioreactive.core.sources.merge import merge
        return AsyncObservable(merge(other, self))

    def with_latest_from(self, mapper, other) -> "AsyncObservable":
        from aioreactive.core.sources.with_latest_from import with_latest_from
        return AsyncObservable(with_latest_from(mapper, other, self))
