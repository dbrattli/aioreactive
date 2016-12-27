from typing import Callable, TypeVar, Generic

from .observers import AsyncObserver
from .typing import AsyncObservable as AsyncObservableGeneric
T = TypeVar('T')


class AsyncObservable(Generic[T], AsyncObservableGeneric[T]):
    """An AsyncObservable that works with Python special methods.

    This class supports python special methods including pipe-forward
    using OR operator. All operators are provided as partially applied
    plain old functions
    """

    def __init__(self, source: 'AsyncObservable' = None) -> None:
        self._source = source

    async def __asubscribe__(self, sink: AsyncObserver) -> 'AsyncSingleStream':
        return await self._source.__asubscribe__(sink)

    def __or__(self, other: Callable[['AsyncObservable'], 'AsyncObservable']) -> 'AsyncObservable':
        """Forward pipe.

        Composes an async observable with a partally applied operator.

        Returns a composed AsyncObservable.
        """
        return other(self)

    def __getitem__(self, key) -> 'AsyncObservable':
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

    def __add__(self, other: 'AsyncObservable') -> 'AsyncObservable':
        """Pythonic version of concat

        Example:
        zs = xs + ys

        Returns concat(other, self)"""

        from aioreactive.operators.concat import concat
        return concat(self, other)

    def __iadd__(self, other):
        """Pythonic use of concat

        Example:
        xs += ys

        Returns self.concat(other, self)"""

        from aioreactive.operators.concat import concat
        return concat(self, other)

    @classmethod
    def from_iterable(cls, iter) -> 'AsyncObservable':
        from aioreactive.operators.from_iterable import from_iterable
        return from_iterable(iter)

    @classmethod
    def unit(cls, value) -> 'AsyncObservable':
        from aioreactive.operators.unit import unit
        return unit(value)

    @classmethod
    def empty(cls) -> 'AsyncObservable':
        from aioreactive.operators.empty import empty
        return empty()

    @classmethod
    def never(cls) -> 'AsyncObservable':
        from aioreactive.operators.never import never
        return never()

