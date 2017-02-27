import asyncio
from typing import List

from aioreactive.core import AsyncSingleStream, AsyncObserver, AsyncObservable, chain
from aioreactive.core import AsyncDisposable, AsyncCompositeDisposable


class Delay(AsyncObservable):

    def __init__(self, source: AsyncObservable, seconds: float) -> None:
        self._seconds = seconds
        self._source = source

    async def __asubscribe__(self, observer: AsyncObserver) -> AsyncDisposable:
        tasks = []  # type: List[asyncio.Task]

        sink = Delay.Sink(self, tasks)
        down = await chain(sink, observer)
        up = await chain(self._source, sink)

        async def cancel():
            for task in tasks:
                task.cancel()
        return AsyncCompositeDisposable(up, down, AsyncDisposable(cancel))

    class Sink(AsyncSingleStream):

        def __init__(self, source, tasks) -> None:
            super().__init__()
            self._source = source
            self._tasks = tasks

        async def asend_core(self, value) -> None:
            async def _delay(value):
                await asyncio.sleep(self._source._seconds)
                await self._observer.asend(value)
                self._tasks.pop(0)

            task = asyncio.ensure_future(_delay(value))
            self._tasks.append(task)

        async def aclose_core(self) -> None:
            async def _delay():
                await asyncio.sleep(self._source._seconds)
                await self._observer.aclose()
                self._tasks.pop(0)

            task = asyncio.ensure_future(_delay())
            self._tasks.append(task)


def delay(seconds: float, source: AsyncObservable) -> AsyncObservable:
    """Time shifts the source stream by seconds. The relative time
    intervals between the values are preserved.

    xs = delay(5, source)

    Keyword arguments:
    seconds -- Relative time in seconds by which to shift the source
        stream.

    Returns time-shifted source stream.
    """

    return Delay(source, seconds)
