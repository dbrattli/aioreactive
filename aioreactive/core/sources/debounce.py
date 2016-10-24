import asyncio
from typing import TypeVar, Generic, List

from aioreactive.core import AsyncSingleStream, AsyncSink, AsyncSource, chain

T = TypeVar("T")


class Debounce(AsyncSource):

    def __init__(self, source: AsyncSource, seconds: float) -> None:
        self._seconds = seconds
        self._source = source

    async def __astart__(self, sink: AsyncSink) -> AsyncSingleStream:
        """Start streaming."""

        tasks = []  # type: List[asyncio.Task]

        _sink = await chain(Debounce.Stream(self, tasks), sink)
        sub = await chain(self._source, _sink)

        def cancel(sub):
            for task in tasks:
                task.cancel()
        sub.add_done_callback(cancel)
        return sub

    class Stream(AsyncSingleStream, Generic[T]):

        def __init__(self, source, tasks) -> None:
            super().__init__()
            self._source = source
            self._tasks = tasks
            self._seconds = source._seconds

            self._value = None  # type: T
            self._has_value = False
            self._index = 0

        async def asend(self, value: T) -> None:
            self._has_value = True
            self._value = value
            self._index += 1

            async def _debouncer(value, current) -> None:
                await asyncio.sleep(self._seconds)
                if self._has_value and current == self._index:
                    self._has_value = False
                    value = self._value
                    await self._sink.asend(value)
                self._tasks.pop(0)

            task = asyncio.ensure_future(_debouncer(value, self._index))
            self._tasks.append(task)

        async def aclose(self) -> None:
            if self._has_value:
                self._has_value = False
                await self._sink.asend(self._value)
            await self._sink.aclose()


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
