from asyncio import iscoroutinefunction, Future
from typing import Callable, Awaitable, TypeVar, Generic

from aioreactive.core.utils import noopobserver
from aioreactive.core import AsyncObserver, AsyncObservable
from aioreactive.core import AsyncSingleStream, chain
from aioreactive.core import AsyncCompositeDisposable, AsyncDisposable

T = TypeVar('T')
TT = TypeVar('TT')


class WithLatestFrom(AsyncObservable):

    def __init__(self, mapper, other: AsyncObservable, source: AsyncObservable) -> None:
        self._mapper = mapper
        self._other = other
        self._source = source

    async def __asubscribe__(self, observer: AsyncObserver) -> AsyncDisposable:
        sink = WithLatestFrom.SourceStream(self)
        down_source = await chain(sink, observer)
        up_source = await chain(self._source, sink)

        sink_other = WithLatestFrom.OtherStream(self, sink)
        up_other = await chain(self._other, sink_other)
        return AsyncCompositeDisposable(up_source, up_other, down_source)

    class SourceStream(AsyncSingleStream, Generic[TT]):

        def __init__(self, source: "WithLatestFrom") -> None:
            super().__init__()
            self._source = source
            self._latest = None  # type: TT
            self._has_latest = False

        async def asend_core(self, value: T) -> None:
            if not self._has_latest:
                return

            try:
                result = self._source._mapper(value, self._latest)
            except Exception as error:
                await self._observer.athrow(error)
            else:
                await self._observer.asend(result)

        @property
        def latest(self) -> TT:
            return self._latest

        @latest.setter
        def latest(self, value: TT):
            self._latest = value
            self._has_latest = True

    class OtherStream(AsyncSingleStream):

        def __init__(self, source: "WithLatestFrom", observer: "AsyncObserver") -> None:
            super().__init__()
            self._source = source
            self._observer = observer

        async def asend_core(self, value: T) -> None:
            self._observer.latest = value

        async def aclose_core(self) -> None:
            # Close must be ignored
            self.observer = noopobserver


def with_latest_from(mapper: Callable, other: AsyncObservable, source: AsyncObservable) -> AsyncObservable:
    """Merge with the latest value from source.

    Merges the specified source streams into one source source
    by using the mapper function only when the source stream produces
    a value.

    Returns the resulting source stream.
    """

    return WithLatestFrom(mapper, other, source)
