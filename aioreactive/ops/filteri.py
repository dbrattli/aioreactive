from asyncio import iscoroutinefunction
from typing import Awaitable, Union, Callable, TypeVar

from aioreactive.core.futures import AsyncMultiFuture
from aioreactive.abc import AsyncSource, AsyncSink
from aioreactive.core import chain

T = TypeVar('T')


class FilterIndexed(AsyncSource):
    def __init__(self, predicate: Union[Callable[[T, int], bool], Awaitable], source: AsyncSource):
        """Filters the elements of the source stream based on a
        predicate function.
        """

        self._is_awaitable = iscoroutinefunction(predicate)
        self._predicate = predicate
        self._source = source

    async def __alisten__(self, sink: AsyncSink):
        _sink = await chain(FilterIndexed.Sink(self), sink)
        return await chain(self._source, _sink)

    class Sink(AsyncMultiFuture):
        def __init__(self, source: "FilterIndexed"):
            super().__init__()
            self._is_awaitable = source._is_awaitable
            self._predicate = source._predicate
            self._index = 0

        async def send(self, value: T):
            try:
                should_run = await self._predicate(value, self._index) if self._is_awaitable else self._predicate(value, self._index)
            except Exception as ex:
                await self._sink.throw(ex)
            else:
                if should_run:
                    await self._sink.send(value)
                self._index += 1


def filteri(predicate: Union[Callable[[T, int], bool], Awaitable], source: AsyncSource) -> AsyncSource:
    return FilterIndexed(predicate, source)
