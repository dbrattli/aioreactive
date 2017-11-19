from asyncio import iscoroutinefunction
from typing import Callable, TypeVar

from aioreactive.abc import AsyncDisposable
from aioreactive.core import AsyncObserver, AsyncObservable
from aioreactive.core import AsyncSingleStream, chain, AsyncCompositeDisposable

T1 = TypeVar('T1')
T2 = TypeVar('T2')


class Map(AsyncObservable[T2]):

    def __init__(self, mapper: Callable[[T1], T2], source: AsyncObservable[T1]) -> None:
        self._source = source
        self._mapper = mapper

    async def __asubscribe__(self, observer: AsyncObserver[T2]) -> AsyncDisposable:
        sink = Map.Sink(self)  # type: AsyncSingleStream[T2]
        down = await chain(sink, observer)
        up = await chain(self._source, sink)   # type: AsyncDisposable

        return AsyncCompositeDisposable(up, down)

    class Sink(AsyncSingleStream[T2]):

        def __init__(self, source: "Map") -> None:
            super().__init__()
            self._mapper = source._mapper

        async def asend_core(self, value: T1) -> None:
            try:
                result = self._mapper(value)
            except Exception as err:
                await self._observer.athrow(err)
            else:
                await self._observer.asend(result)


def map(mapper: Callable[[T1], T2], source: AsyncObservable[T1]) -> AsyncObservable[T2]:
    """Project each item of the source observable.

    xs = map(lambda value: value * value, source)

    Keyword arguments:
    mapper: A transform function to apply to each source item.

    Returns an observable sequence whose elements are the result of
    invoking the mapper function on each element of source.
    """

    assert not iscoroutinefunction(mapper)

    return Map(mapper, source)
