import asyncio
from typing import TypeVar, Generic, List

from aioreactive.core import AsyncSingleStream, AsyncObserver, AsyncObservable, chain
from aioreactive.core import AsyncCompositeDisposable, AsyncDisposable

T = TypeVar("T")


class Debounce(AsyncObservable[T], Generic[T]):

    def __init__(self, source: AsyncObservable[T], seconds: float) -> None:
        self._seconds = seconds
        self._source = source

    async def __asubscribe__(self, observer: AsyncObserver[T]) -> AsyncDisposable:
        """Start streaming."""

        tasks = []  # type: List[asyncio.Task]

        sink = Debounce.Stream(self, tasks)
        down = await chain(sink, observer)
        up = await chain(self._source, sink)

        def cancel(sub: asyncio.Future):
            for task in tasks:
                task.cancel()
        sink.add_done_callback(cancel)
        return AsyncCompositeDisposable(up, down)

    class Stream(AsyncSingleStream[T]):

        def __init__(self, source: 'Debounce[T]', tasks: List[asyncio.Task]) -> None:
            super().__init__()
            self._source = source
            self._tasks = tasks
            self._seconds = source._seconds

            self._value = None  # type: T
            self._has_value = False
            self._index = 0

        async def asend_core(self, value: T) -> None:
            self._has_value = True
            self._value = value
            self._index += 1

            async def _debouncer(value, current) -> None:
                await asyncio.sleep(self._seconds)
                if self._has_value and current == self._index:
                    self._has_value = False
                    value = self._value
                    await self._observer.asend(value)
                self._tasks.pop(0)

            task = asyncio.ensure_future(_debouncer(value, self._index))
            self._tasks.append(task)

        async def aclose_core(self) -> None:
            if self._has_value:
                self._has_value = False
                await self._observer.asend(self._value)
            await self._observer.aclose()


def debounce(seconds: float, source: AsyncObservable[T]) -> AsyncObservable[T]:
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
