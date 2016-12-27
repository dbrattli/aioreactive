from typing import Awaitable, Union, Callable, TypeVar

from aioreactive.core import AsyncObservable, AsyncObserver, chain
from aioreactive.core import AsyncSingleStream

T = TypeVar('T')


class Different:

    def __cmp__(self, other):
        return False


class DistinctUntilChanged(AsyncObservable):

    def __init__(self, source: AsyncObservable) -> None:
        self.source = source

    async def __asubscribe__(self, sink: AsyncObserver):
        _observer = await chain(DistinctUntilChanged.Sink(self), sink)
        return await chain(self.source, _observer)

    class Sink(AsyncSingleStream):

        def __init__(self, source: "DistinctUntilChanged") -> None:
            super().__init__()
            self._latest = Different()

        async def asend(self, value: T) -> None:
            if self._latest == value:
                return

            self._latest = value
            await self._observer.asend(value)


def distinct_until_changed(source: AsyncObservable) -> AsyncObservable:
    """Filters the source stream to have continously distict values.
    """
    return DistinctUntilChanged(source)
