from typing import Callable, TypeVar

from aioreactive.core import AsyncSource, AsyncSink, AsyncSingleStream
from aioreactive import core

T = TypeVar('T')


class Producer(AsyncSource):
    """An AsyncSource that works with Python special methods.

    This class supports python special methods including pipe-forward
    using OR operator. All operators are provided as partially applied
    plain old functions
    """

    def __init__(self, source: AsyncSource = None):
        self._source = source

    async def __astart__(self, sink: AsyncSink) -> AsyncSingleStream:
        return await self._source.__astart__(sink)

    def __or__(self, other: Callable[[AsyncSource], "Producer"]) -> "Producer":
        """Forward pipe.

        Composes a producer with a partally applied operator.

        Returns a composed Producer.
        """
        return Producer(other(self))

    def __getitem__(self, key) -> "Producer":
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

        from aioreactive.core.sources.slice import slice as _slice

        if isinstance(key, slice):
            start, stop, step = key.start, key.stop, key.step
        elif isinstance(key, int):
            start, stop, step = key, key + 1, 1
        else:
            raise TypeError("Invalid argument type.")

        xs = _slice(start, stop, step, self)
        return Producer(xs)

    def __add__(self, other: AsyncSource) -> "Producer":
        """Pythonic version of concat

        Example:
        zs = xs + ys

        Returns concat(other, self)"""

        from aioreactive.core.sources.concat import concat
        return concat(other, self)

    def __iadd__(self, other):
        """Pythonic use of concat

        Example:
        xs += ys

        Returns self.concat(other, self)"""

        from aioreactive.core.sources.concat import concat
        return concat(other, self)

    @classmethod
    def from_iterable(cls, iter) -> "Producer":
        from aioreactive.core.sources.from_iterable import from_iterable
        return Producer(from_iterable(iter))

    @classmethod
    def unit(cls, value) -> "Producer":
        from aioreactive.core.sources.unit import unit
        return Producer(unit(value))

    @classmethod
    def empty(cls) -> "Producer":
        from aioreactive.core.sources.empty import empty
        return Producer(empty())

    @classmethod
    def never(cls) -> "Producer":
        from aioreactive.core.sources.never import never
        return Producer(never())


class AsyncStream(core.AsyncStream, Producer):
    pass
