from typing import TypeVar

from aioreactive.core import AsyncObservable, AsyncObserver, AsyncSingleSubject, chain
from fslash.system import AsyncCompositeDisposable, AsyncDisposable

TSource = TypeVar("TSource")


class Max(AsyncObservable[TSource]):
    def __init__(self, source: AsyncObservable) -> None:
        self._source = source

    async def __asubscribe__(self, observer: AsyncObserver[TSource]) -> AsyncDisposable:
        sink = Max.Stream()
        down = await chain(sink, observer)
        up = await chain(self._source, down)

        return AsyncCompositeDisposable(up, down)

    class Stream(AsyncSingleSubject[TSource]):
        def __init__(self) -> None:
            super().__init__()
            self._max: TSource = None

        async def asend_core(self, value: T) -> None:
            if value > self._max:
                self._max = value

        async def aclose_core(self) -> None:
            await super().asend_core(self._max)
            await super().aclose_core()


def max(source: AsyncObservable[TSource]) -> AsyncObservable[TSource]:
    """Project each item of the source stream.

    xs = max(source)

    Keyword arguments:
    source: Source to find max value from.

    Returns a stream with a single item that is the item with the
    maximum value from the source stream.
    """

    return Max(source)
