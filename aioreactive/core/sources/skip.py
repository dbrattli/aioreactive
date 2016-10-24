from typing import TypeVar

from aioreactive.core import AsyncSingleStream
from aioreactive.core import AsyncSink, AsyncSource, chain

T = TypeVar('T')


class Skip(AsyncSource):

    def __init__(self, count: int, source: AsyncSource) -> None:
        self._source = source
        self._count = count

    async def __astart__(self, sink: AsyncSink):
        _sink = await chain(Skip.Sink(self), sink)
        return await chain(self._source, _sink)

    class Sink(AsyncSingleStream):

        def __init__(self, source: "Skip") -> None:
            super().__init__()
            self._count = source._count

        async def asend(self, value: T):
            if self._count <= 0:
                await self._sink.asend(value)
            else:
                self._count -= 1


def skip(count: int, source: AsyncSource) -> AsyncSource:
    """Skip the specified number of values.

    Keyword arguments:
    count -- The number of elements to skip before returning the
        remaining values.

    Returns a source stream that contains the values that occur
    after the specified index in the input source stream.
    """

    return Skip(count, source)
