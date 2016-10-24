import asyncio
from typing import List

from aioreactive.core import AsyncSingleStream, AsyncSink, AsyncSource, chain


class Delay(AsyncSource):

    def __init__(self, source: AsyncSource, seconds: float) -> None:
        self._seconds = seconds
        self._source = source

    async def __astart__(self, sink: AsyncSink) -> AsyncSingleStream:
        tasks = []  # type: List[asyncio.Task]

        _sink = await chain(Delay.Stream(self, tasks), sink)
        stream = await chain(self._source, _sink)

        def cancel(sub):
            for task in tasks:
                task.cancel()
        stream.add_done_callback(cancel)
        return stream

    class Stream(AsyncSingleStream):

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
