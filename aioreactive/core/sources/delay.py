import asyncio
from typing import List

from aioreactive.core.futures import AsyncMultiFuture
from aioreactive.core import Subscription, AsyncSink, AsyncSource, chain


class Delay(AsyncSource):

    def __init__(self, source: AsyncSource, seconds: float) -> None:
        self._seconds = seconds
        self._source = source

    async def __alisten__(self, sink: AsyncSink) -> Subscription:
        tasks = []  # type: List[asyncio.Task]

        _sink = await chain(Delay.Sink(self, tasks), sink)
        sub = await chain(self._source, _sink)

        def cancel(sub):
            for task in tasks:
                task.cancel()
        sub.add_done_callback(cancel)
        return sub

    class Sink(AsyncMultiFuture):

        def __init__(self, source, tasks) -> None:
            super().__init__()
            self._source = source
            self._tasks = tasks

        async def asend(self, value) -> None:
            async def _delay(value):
                await asyncio.sleep(self._source._seconds)
                await self._sink.asend(value)
                self._tasks.pop(0)

            task = asyncio.ensure_future(_delay(value))
            self._tasks.append(task)

        async def aclose(self) -> None:
            async def _delay():
                await asyncio.sleep(self._source._seconds)
                await self._sink.aclose()
                self._tasks.pop(0)

            task = asyncio.ensure_future(_delay())
            self._tasks.append(task)


def delay(seconds: float, source: AsyncSource) -> AsyncSource:
    """Time shifts the source stream by seconds. The relative time
    intervals between the values are preserved.

    xs = delay(5, source)

    Keyword arguments:
    seconds -- Relative time in seconds by which to shift the source
        stream.

    Returns time-shifted source stream.
    """

    return Delay(source, seconds)
