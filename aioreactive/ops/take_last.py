from typing import TypeVar

from aioreactive.core.futures import AsyncMultiFuture
from aioreactive.abc import AsyncSink, AsyncSource
from aioreactive.core import chain


T = TypeVar('T')


class TakeLast(AsyncSource):
    def __init__(self, count: int, source: AsyncSource):
        self._source = source
        self._count = count

    async def __alisten__(self, sink: AsyncSink):
        return await chain(self._source, TakeLast._(sink, self))

    class _(AsyncMultiFuture):
        def __init__(self, sink: AsyncSink, source: "TakeLast"):
            super().__init__(sink)
            self._count = source._count
            self._q = []

        async def send(self, value: T):
            self._q.append(value)
            if len(self._q) > self._count:
                self._q.pop(0)

        async def close(self):
            while len(self._q):
                await self._sink.send(self._q.pop(0))
            await self._sink.close()


def take_last(count: int, source: AsyncSource) -> AsyncSource:
    """Return a specified number of contiguous elements from the end of
    a source sequence.

    Example:
    xs = take_last(5, source)

    Description:
    This operator accumulates a buffer with a length enough to store
    elements count elements. Upon completion of the source sequence,
    this buffer is drained on the result sequence. This causes the
    elements to be delayed.

    Keyword arguments:
    count -- Number of elements to take from the end of the source
        sequence.

    Returns a source sequence containing the specified number of
        elements from the end of the source sequence."""

    if count < 0:
        raise ValueError()

    return TakeLast(count, source)
