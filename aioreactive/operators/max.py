from typing import TypeVar

from aioreactive.core import AsyncObserver, AsyncObservable
from aioreactive.core import AsyncSingleStream, chain
from aioreactive.core import AsyncDisposable, AsyncCompositeDisposable

T = TypeVar('T')


class Max(AsyncObservable[T]):

    def __init__(self, source: AsyncObservable) -> None:
        self._source = source

    async def __asubscribe__(self, observer: AsyncObserver[T]) -> AsyncDisposable:
        sink = Max.Stream()  # type: AsyncSingleStream[T]
        down = await chain(sink, observer)
        up = await chain(self._source, down)

        return AsyncCompositeDisposable(up, down)

    class Stream(AsyncSingleStream[T]):

        def __init__(self) -> None:
            super().__init__()
            self._max = None  # type: T

        async def asend_core(self, value: T) -> None:
            if value > self._max:
                self._max = value

        async def aclose_core(self) -> None:
            await super().asend_core(self._max)
            await super().aclose_core()


def max(source: AsyncObservable[T]) -> AsyncObservable[T]:
    """Project each item of the source stream.

    xs = max(source)

    Keyword arguments:
    source: Source to find max value from.

    Returns a stream with a single item that is the item with the
    maximum value from the source stream.
    """

    return Max(source)
