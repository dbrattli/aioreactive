from typing import Awaitable, Union, Callable, TypeVar

from aioreactive.core import AsyncSource, AsyncSink, chain
from aioreactive.core import AsyncSingleStream

T = TypeVar('T')


class Different:

    def __cmp__(self, other):
        return False


class DistinctUntilChanged(AsyncSource):

    def __init__(self, source: AsyncSource) -> None:
        self.source = source

    async def __astart__(self, sink: AsyncSink):
        _sink = await chain(DistinctUntilChanged.Sink(self), sink)
        return await chain(self.source, _sink)

    class Sink(AsyncSingleStream):

        def __init__(self, source: "DistinctUntilChanged") -> None:
            super().__init__()
            self._latest = Different()

        async def asend(self, value: T) -> None:
            if self._latest == value:
                return

            self._latest = value
            await self._sink.asend(value)


def distinct_until_changed(source: AsyncSource) -> AsyncSource:
    """Filters the source stream to have continously distict values.
    """
    return DistinctUntilChanged(source)
