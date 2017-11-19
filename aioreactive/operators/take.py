from typing import TypeVar

from aioreactive.core import AsyncObserver, AsyncObservable, AsyncSingleStream
from aioreactive.core import AsyncDisposable, AsyncCompositeDisposable, chain

from .empty import empty

T = TypeVar('T')


class Take(AsyncObservable[T]):

    def __init__(self, count: int, source: AsyncObservable[T]) -> None:
        self._source = source
        self._count = count

    async def __asubscribe__(self, observer: AsyncObserver[T]) -> AsyncDisposable:
        sink = Take.Sink(self)  # type: AsyncSingleStream[T]
        down = await chain(sink, observer)
        up = await chain(self._source, sink)

        return AsyncCompositeDisposable(up, down)

    class Sink(AsyncSingleStream[T]):

        def __init__(self, source: "Take") -> None:
            super().__init__()
            self._count = source._count

        async def asend(self, value: T) -> None:
            if self._count > 0:
                self._count -= 1
                await self._observer.asend(value)

                if not self._count:
                    await self._observer.aclose()


def take(count: int, source: AsyncObservable[T]) -> AsyncObservable[T]:
    """Returns a specified number of contiguous elements from the start
    of the source stream.

    1 - take(5, source)
    2 - source | take(5)

    Keyword arguments:
    count -- The number of elements to return.

    Returns a source sequence that contains the specified number of
    elements from the start of the input sequence.
    """

    if count < 0:
        raise ValueError()

    if not count:
        return empty()

    return Take(count, source)
