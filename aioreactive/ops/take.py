from typing import TypeVar

from aioreactive.core.futures import AsyncMultiFuture
from aioreactive.abc import AsyncSink, AsyncSource
from aioreactive.core import chain

from .empty import empty

T = TypeVar('T')


class Take(AsyncSource):
    def __init__(self, count: int, source: AsyncSource):
        self._source = source
        self._count = count

    async def __alisten__(self, sink: AsyncSink):
        _sink = await chain(Take.Sink(self), sink)
        return await chain(self._source, _sink)

    class Sink(AsyncMultiFuture):
        def __init__(self, source: "Take"):
            super().__init__()
            self._count = source._count

        async def send(self, value: T):
            if self._count > 0:
                self._count -= 1
                await self._sink.send(value)

                if not self._count:
                    await self._sink.close()


def take(count: int, source: AsyncSource) -> AsyncSource:
    """Returns a specified number of contiguous elements from the start
    of the source stream.

    1 - take(5, source)
    2 - source | take(5)

    Keyword arguments:
    count -- The number of elements to return.

    Returns a source sequence that contains the specified number of
    elements from the start of the input sequence.
    """

    if count < 0:
        raise ValueError()

    if not count:
        return empty()

    return Take(count, source)
