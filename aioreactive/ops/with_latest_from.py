from asyncio import iscoroutinefunction, Future
from typing import Callable, Awaitable, TypeVar

from aioreactive.abc import AsyncSink, AsyncSource
from aioreactive.core import Subscription, chain, chain_future
from aioreactive.core.futures import AsyncMultiFuture

T = TypeVar('T')


class WithLatestFrom(AsyncSource):
    def __init__(self, mapper, other: AsyncSource, source: AsyncSource):
        self._mapper = mapper
        self._other = other
        self._source = source

    async def __alisten__(self, sink: AsyncSink):
        _sink = await chain(WithLatestFrom.SourceSink(self), sink)
        sub = await chain(self._source, _sink)

        _other = WithLatestFrom.OtherSink(self, _sink)
        sub_other = await chain(self._other, _other)
        return chain_future(sub, sub_other)

    class SourceSink(AsyncMultiFuture):
        def __init__(self, source: "WithLatestFrom"):
            super().__init__()
            self._source = source
            self._latest = None
            self._has_latest = False

        async def send(self, value: T):
            if not self._has_latest:
                return

            try:
                result = self._source._mapper(value, self._latest)
            except Exception as error:
                await self._sink.throw(error)
            else:
                await self._sink.send(result)

        @property
        def latest(self):
            return self._latest

        @latest.setter
        def latest(self, value: T):
            self._latest = value
            self._has_latest = True

    class OtherSink(AsyncMultiFuture):
        def __init__(self, source: "WithLatestFrom", sink: "AsyncSink"):
            super().__init__()
            self._source = source
            self._sink = sink

        async def send(self, value: T):
            self._sink.latest = value

        async def close(self):
            pass


def with_latest_from(mapper: Callable, other: AsyncSource, source: AsyncSource) -> AsyncSource:
    """Merge with the latest value from source.

    Merges the specified source streams into one source source
    by using the mapper function only when the source stream produces
    a value.

    Returns the resulting source stream.
    """

    return WithLatestFrom(mapper, other, source)
