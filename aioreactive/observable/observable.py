from typing import Callable

from aioreactive.abc import AsyncSource
from aioreactive.core import listen
from aioreactive.producer import Producer

from .observer import Observer, SinkObserver


class Observable(Producer):
    """An Observable example class similar to RxPY.

    This class supports has all operators as methods.

    Subscribe is also a method.

    All methods are lazy imported.
    """

    def __init__(self, source: AsyncSource = None):
        super().__init__()
        self._source = source

    async def subscribe(self, obv: Observer):
        _sink = await SinkObserver().__alisten__(obv)
        return await listen(self, _sink)

    def __getitem__(self, key) -> "Observable":
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

        return Observable(super(Observable, self).__getitem__(key))

    def __add__(self, other) -> "Observable":
        """Pythonic version of concat

        Example:
        zs = xs + ys
        Returns self.concat(other)"""

        xs = super(Observable, self).__add__(other)
        return Observable(xs)

    def __iadd__(self, other):
        """Pythonic use of concat

        Example:
        xs += ys

        Returns self.concat(self, other)"""

        xs = super(Observable, self).__iadd__(other)
        return Observable(xs)

    @classmethod
    def from_iterable(cls, iter):
        return Observable(Producer.from_iterable(iter))

    @classmethod
    def just(cls, value) -> "Observable":
        return Observable(Producer.unit(value))

    @classmethod
    def empty(cls) -> "Observable":
        return Observable(Producer.empty())

    def debounce(self, seconds: float) -> "Observable":
        """Debounce observable source.

        Ignores values from a source stream which are followed by
        another value before seconds has elapsed.

        Example:
        partial = debounce(5) # 5 seconds

        Keyword arguments:
        seconds -- Duration of the throttle period for each value

        Returns partially applied function that takes a source sequence.
        """

        from aioreactive.ops.debounce import debounce
        return Observable(debounce(seconds, self))

    def delay(self, seconds: float) -> "Observable":
        from aioreactive.ops.delay import delay
        return Observable(delay(seconds, self))

    def where(self, predicate: Callable) -> "Observable":
        from aioreactive.ops.filter import filter
        return Observable(filter(predicate, self))

    def select_many(self, selector: Callable) -> "Observable":
        from aioreactive.ops.flat_map import flat_map
        return Observable(flat_map(selector, self))

    def select(self, selector: Callable) -> "Observable":
        from aioreactive.ops.map import map
        return Observable(map(selector, self))

    def merge(self, other: AsyncSource) -> "Observable":
        from aioreactive.ops.merge import merge
        return Observable(merge(other, self))

    def with_latest_from(self, mapper, other) -> "Observable":
        from aioreactive.ops.with_latest_from import with_latest_from
        return Observable(with_latest_from(mapper, other, self))
