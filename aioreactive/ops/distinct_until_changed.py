from typing import Awaitable, Union, Callable, TypeVar

from aioreactive.abc import AsyncSource, AsyncSink
from aioreactive.core.futures import AsyncMultiFuture
from aioreactive.core import chain

T = TypeVar('T')


class Different:
    def __cmp__(self, other):
        return False


class DistinctUntilChanged(AsyncSource):
    def __init__(self, source: AsyncSource):
        self.source = source

    async def __alisten__(self, sink: AsyncSink):
        _sink = await chain(DistinctUntilChanged.Sink(self), sink)
        return await chain(self.source, _sink)

    class Sink(AsyncMultiFuture):
        def __init__(self, source: "DistinctUntilChanged"):
            super().__init__()
            self._latest = Different()

        async def send(self, value: T):
            if self._latest == value:
                return

            self._latest = value
            await self._sink.send(value)


def distinct_until_changed(source: AsyncSource) -> AsyncSource:
    """Filters the source stream to have continously distict values.
    """
    return DistinctUntilChanged(source)
