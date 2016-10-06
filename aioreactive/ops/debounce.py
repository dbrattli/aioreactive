import asyncio

from aioreactive.core.futures import AsyncMultiFuture
from aioreactive.abc import AsyncSink, AsyncSource
from aioreactive.core import chain


class Debounce(AsyncSource):
    def __init__(self, source: AsyncSource, seconds: float):
        self._seconds = seconds
        self._source = source

    async def __alisten__(self, sink: AsyncSink):
        tasks = []

        _sink = await chain(Debounce.Sink(self, tasks), sink)
        sub = await chain(self._source, _sink)

        def cancel(sub):
            for task in tasks:
                task.cancel()
        sub.add_done_callback(cancel)
        return sub

    class Sink(AsyncMultiFuture):
        def __init__(self, source, tasks):
            super().__init__()
            self._source = source
            self._tasks = tasks
            self._seconds = source._seconds

            self._value = None
            self._has_value = False
            self._index = 0

        async def send(self, value):
            self._has_value = True
            self._value = value
            self._index += 1

            async def _debouncer(value, current):
                await asyncio.sleep(self._seconds)
                if self._has_value and current == self._index:
                    self._has_value = False
                    value = self._value
                    await self._sink.send(value)
                self._tasks.pop(0)

            task = asyncio.ensure_future(_debouncer(value, self._index))
            self._tasks.append(task)

        async def close(self):
            if self._has_value:
                self._has_value = False
                await self._sink.send(self._value)
            await self._sink.close()


def debounce(seconds: float, source: AsyncSource) -> AsyncSource:
    """Debounce source stream.

    Ignores values from a source stream which are followed by
    another value before seconds has elapsed.

    Example:
    xs = debounce(5, source) # 5 seconds

    Keyword arguments:
    seconds -- Duration of the throttle period for each value.
    source -- Source stream to debounce.

    Returns the debounced source sequence."""

    return Debounce(source, seconds)
