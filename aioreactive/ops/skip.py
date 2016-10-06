from typing import TypeVar

from aioreactive.core.futures import AsyncMultiFuture
from aioreactive.abc import AsyncSink, AsyncSource
from aioreactive.core import chain

T = TypeVar('T')


class Skip(AsyncSource):
    def __init__(self, count: int, source: AsyncSource):
        self._source = source
        self._count = count

    async def __alisten__(self, sink: AsyncSink):
        _sink = await chain(Skip.Sink(self), sink)
        return await chain(self._source, _sink)

    class Sink(AsyncMultiFuture):
        def __init__(self, source: "Skip"):
            super().__init__()
            self._count = source._count

        async def send(self, value: T):
            if self._count <= 0:
                await self._sink.send(value)
            else:
                self._count -= 1


def skip(count: int, source: AsyncSource) -> AsyncSource:
    """Skip the specified number of values.source

    Keyword arguments:
    count -- The number of elements to skip before returning the
        remaining values.

    Returns a source stream that contains the values that occur
    after the specified index in the input source stream.
    """

    return Skip(count, source)
