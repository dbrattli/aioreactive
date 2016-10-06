from asyncio import iscoroutinefunction
from typing import Awaitable, Union, Callable, TypeVar

from aioreactive.abc import AsyncSource, AsyncSink
from aioreactive.core.futures import AsyncMultiFuture
from aioreactive.core import chain

T = TypeVar('T')


class Filter(AsyncSource):
    def __init__(self, predicate: Union[Callable[[T], bool], Awaitable], source: AsyncSource):
        """Filters the elements of the source sequence based on a
        predicate function."""

        self._source = source
        self._predicate = predicate
        self._is_awaitable = iscoroutinefunction(predicate)

    async def __alisten__(self, sink: AsyncSink):
        _sink = await chain(Filter.Sink(self), sink)
        return await chain(self._source, _sink)

    class Sink(AsyncMultiFuture):

        def __init__(self, source: "Filter"):
            super().__init__()
            self._predicate = source._predicate
            self._is_awaitable = source._is_awaitable

        async def send(self, value: T):
            try:
                should_run = await self._predicate(value) if self._is_awaitable else self._predicate(value)
            except Exception as ex:
                await self._sink.throw(ex)
            else:
                if should_run:
                    await self._sink.send(value)


def filter(predicate: Awaitable[bool], source: AsyncSource) -> AsyncSource:
    """Filters the source stream.

    Filters the items of the source stream based on a predicate
    function."""
    return Filter(predicate, source)
