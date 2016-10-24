from asyncio import iscoroutinefunction, Future
from typing import Callable, Awaitable, TypeVar

from aioreactive.core import AsyncSink, AsyncSource
from aioreactive.core import AsyncSingleStream, chain, chain_future

T = TypeVar('T')


class WithLatestFrom(AsyncSource):

    def __init__(self, mapper, other: AsyncSource, source: AsyncSource) -> None:
        self._mapper = mapper
        self._other = other
        self._source = source

    async def __astart__(self, sink: AsyncSink) -> AsyncSingleStream:
        _sink = await chain(WithLatestFrom.SourceStream(self), sink)
        sub = await chain(self._source, _sink)

        _other = WithLatestFrom.OtherStream(self, _sink)
        sub_other = await chain(self._other, _other)
        return chain_future(sub, sub_other)

    class SourceStream(AsyncSingleStream):

        def __init__(self, source: "WithLatestFrom") -> None:
            super().__init__()
            self._source = source
            self._latest = None  # type: T
            self._has_latest = False

        async def asend(self, value: T) -> None:
            if not self._has_latest:
                return

            try:
                result = self._source._mapper(value, self._latest)
            except Exception as error:
                await self._sink.athrow(error)
            else:
                await self._sink.asend(result)

        @property
        def latest(self) -> T:
            return self._latest

        @latest.setter
        def latest(self, value: T):
            self._latest = value
            self._has_latest = True

    class OtherStream(AsyncSingleStream):
        def __init__(self, source: "WithLatestFrom", sink: "AsyncSink") -> None:
            super().__init__()
            self._source = source
            self._sink = sink

        async def asend(self, value: T) -> None:
            self._sink.latest = value

        async def aclose(self):
            pass


def with_latest_from(mapper: Callable, other: AsyncSource, source: AsyncSource) -> AsyncSource:
    """Merge with the latest value from source.

    Merges the specified source streams into one source source
    by using the mapper function only when the source stream produces
    a value.

    Returns the resulting source stream.
    """

    return WithLatestFrom(mapper, other, source)
