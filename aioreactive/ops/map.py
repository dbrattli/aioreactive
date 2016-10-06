from asyncio import iscoroutinefunction
from typing import Callable, Awaitable, Union, TypeVar

from aioreactive.core.futures import AsyncMultiFuture
from aioreactive.abc import AsyncSink, AsyncSource
from aioreactive.core import chain

T = TypeVar('T')


class Map(AsyncSource):
    def __init__(self, mapper: Union[Callable[[T], T], Awaitable], source: AsyncSource):
        self._source = source
        self._mapper = mapper
        self._is_awaitable = iscoroutinefunction(mapper)

    async def __alisten__(self, sink: AsyncSink):
        _sink = await chain(Map.Sink(self), sink)
        return await chain(self._source, _sink)

    class Sink(AsyncMultiFuture):
        def __init__(self, source: "Map"):
            super().__init__()

            self._is_awaitable = source._is_awaitable
            self._selector = source._mapper

        async def send(self, value: T):
            try:
                result = await self._selector(value) if self._is_awaitable else self._selector(value)
            except Exception as err:
                await self._sink.throw(err)
            else:
                await self._sink.send(result)


def map(selector: Awaitable, source: AsyncSource) -> AsyncSource:
    """Project each item of the source stream.

    xs = map(lambda value: value * value, source)

    Keyword arguments:
    mapper: A transform function to apply to each source item.

    Returns an observable sequence whose elements are the result of
    invoking the mapper function on each element of source.
    """

    return Map(selector, source)
