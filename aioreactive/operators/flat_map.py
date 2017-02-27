from typing import Union, Awaitable, Callable, TypeVar
from asyncio import iscoroutinefunction

from aioreactive.core import AsyncObserver, AsyncObservable
from aioreactive.core import AsyncSingleStream, chain
from aioreactive.core import AsyncDisposable, AsyncCompositeDisposable

from .switch_latest import switch_latest
from .merge import merge
from .map import map


T1 = TypeVar('T1')
T2 = TypeVar('T2')


class FlatMap(AsyncObservable[T2]):

    def __init__(self, mapper: Callable[[T1], AsyncObservable[T2]], source: AsyncObservable[T2]) -> None:
        self._source = source
        self._mapper = mapper

    async def __asubscribe__(self, observer: AsyncObserver) -> AsyncDisposable:
        sink = FlatMap.Sink(self)
        down = await chain(sink, observer)  # type: AsyncSingleStream
        up = await chain(self._source, sink)

        return AsyncCompositeDisposable(up, down)

    class Sink(AsyncSingleStream):

        def __init__(self, source: 'FlatMap') -> None:
            super().__init__()
            self._mapper = source._mapper

        async def asend_core(self, value: T1) -> None:
            try:
                result = await self._mapper(value)
            except Exception as err:
                await self._observer.athrow(err)
            else:
                await self._observer.asend(result)


def flat_map(amapper: Callable[[T1], AsyncObservable[T2]], source: AsyncObservable[T2]) -> AsyncObservable[T2]:
    """Project each element of a source stream into a new source stream
    and merges the resulting source streams back into a single source
    stream.

    xs = flat_map(lambda x: range(0, x), source)

    Keyword arguments:
    amapper -- An async transform function to apply to each element of
        the source stream.

    Returns a source stream whose elements are the result of
    invoking the one-to-many transform function on each element of the
    input source and then mapping each of those source elements and
    their corresponding source element to a result element."""

    assert iscoroutinefunction(amapper)

    xs = FlatMap(amapper, source)
    return merge(xs)


def flat_map_latest(amapper: Callable[[T1], AsyncObservable[T2]], source: AsyncObservable[T2]) -> AsyncObservable[T2]:
    assert iscoroutinefunction(amapper)

    xs = FlatMap(amapper, source)
    return switch_latest(xs)
