from asyncio import Future, ensure_future
from collections.abc import AsyncIterator, AsyncIterable
from typing import Callable
from functools import partial

from aioreactive.abc import AsyncSource, AsyncSink
from aioreactive.core import listen
from aioreactive import core


class Producer(AsyncSource, AsyncIterable):
    """An AsyncSource that works with Python special methods.

    This class supports python special methods including pipe-forward
    using OR operator. All operators are provided as partially applied
    plain old functions
    """

    def __init__(self, source: AsyncSource = None):
        self._source = source

    async def __alisten__(self, sink: AsyncSink):
        return await self._source.__alisten__(sink)

    def __or__(self, other: Callable[[AsyncSource], "Producer"]) -> "Producer":
        """Forward pipe."""
        return Producer(other(self))

    def __getitem__(self, key) -> AsyncSource:
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

        from aioreactive.ops.slice import slice as _slice

        if isinstance(key, slice):
            start, stop, step = key.start, key.stop, key.step
        elif isinstance(key, int):
            start, stop, step = key, key + 1, 1
        else:
            raise TypeError("Invalid argument type.")

        xs = _slice(start, stop, step, self)
        return Producer(xs)

    def __add__(self, other):
        """Pythonic version of concat

        Example:
        zs = xs + ys
        Returns self.concat(other)"""

        from aioreactive.ops.concat import concat
        return concat(other, self)

    def __iadd__(self, other):
        """Pythonic use of concat

        Example:
        xs += ys

        Returns self.concat(self, other)"""

        from aioreactive.ops.concat import concat
        return concat(other, self)

    async def __aiter__(self):
        """Iterate source stream asynchronously.

        Transforms the async source to an async iterable. The source
        will await for the iterator to pick up the value before
        continuing to avoid queuing values.
        """

        class Sink(AsyncSink, AsyncIterator):
            def __init__(self):
                super().__init__()
                self._future = Future()
                self._wait = Future()

            async def send(self, value):
                self._future.set_result(value)
                await self._pong()

            async def throw(self, err):
                self._future.set_exception(err)
                await self._pong()

            async def close(self):
                self._future.set_exception(StopAsyncIteration)
                await self._pong()

            async def __anext__(self):
                return await self._ping()

            async def _ping(self):
                value = await self._future
                self._future = Future()
                self._wait.set_result(True)
                return value

            async def _pong(self):
                await self._wait
                self._wait = Future()

        sink = Sink()
        await listen(self, sink)
        return sink

    @classmethod
    def from_iterable(cls, iter):
        from aioreactive.ops.from_iterable import from_iterable
        return Producer(from_iterable(iter))

    @classmethod
    def unit(cls, value):
        from aioreactive.ops.unit import unit
        return Producer(unit(value))

    @classmethod
    def empty(cls):
        from aioreactive.ops.empty import empty
        return Producer(empty())

    @classmethod
    def never(cls):
        from aioreactive.ops.never import never
        return Producer(never())


class Stream(core.Stream, Producer):
    pass
