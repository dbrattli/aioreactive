from typing import TypeVar, List

from aioreactive.core import AsyncSingleStream, AsyncSink, AsyncSource, chain

T = TypeVar('T')


class TakeLast(AsyncSource):

    def __init__(self, count: int, source: AsyncSource) -> None:
        self._source = source
        self._count = count

    async def __astart__(self, sink: AsyncSink) -> AsyncSingleStream:
        return await chain(self._source, TakeLast._(sink, self))

    class _(AsyncSingleStream):

        def __init__(self, sink: AsyncSink, source: "TakeLast") -> None:
            super().__init__()
            self._count = source._count
            self._q = []  # type: List[T]

        async def asend(self, value: T) -> None:
            self._q.append(value)
            if len(self._q) > self._count:
                self._q.pop(0)

        async def aclose(self) -> None:
            while len(self._q):
                await self._sink.asend(self._q.pop(0))
            await self._sink.aclose()


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
