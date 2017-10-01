from typing import TypeVar

from aioreactive.abc import AsyncDisposable
from aioreactive.core import AsyncObservable, AsyncObserver, chain
from aioreactive.core import AsyncSingleStream, AsyncCompositeDisposable

T = TypeVar('T')


class Different:

    def __cmp__(self, other):
        return False


class DistinctUntilChanged(AsyncObservable):

    def __init__(self, source: AsyncObservable) -> None:
        self.source = source

    async def __asubscribe__(self, obv: AsyncObserver) -> AsyncDisposable:
        sink = DistinctUntilChanged.Sink()
        down = await chain(sink, obv)
        up = await chain(self.source, sink)
        return AsyncCompositeDisposable(up, down)

    class Sink(AsyncSingleStream):

        def __init__(self) -> None:
            super().__init__()
            self._latest = Different()

        async def asend_core(self, value: T) -> None:
            if self._latest == value:
                return

            self._latest = value
            await self._observer.asend(value)


def distinct_until_changed(source: AsyncObservable) -> AsyncObservable:
    """Filters the source stream to have continously distict values.
    """
    return DistinctUntilChanged(source)
