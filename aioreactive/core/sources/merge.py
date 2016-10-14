import asyncio
import logging
from typing import Dict, TypeVar

from aioreactive.core.futures import AsyncMultiFuture, Subscription
from aioreactive.core import AsyncSource, AsyncSink, chain

T = TypeVar('T')
log = logging.getLogger(__name__)


class Merge(AsyncSource):

    def __init__(self, source: AsyncSource) -> None:
        self._source = source

    async def __alisten__(self, sink: AsyncSink) -> Subscription:
        _sink = await chain(Merge.Sink(self), sink)
        sub = await chain(self._source, _sink)
        sub.add_done_callback(_sink._done)
        return sub

    class Sink(AsyncMultiFuture):

        def __init__(self, source: AsyncSource) -> None:
            super().__init__()
            self._tasks = {}  # type: Dict[AsyncSink[T], asyncio.Task]
            self._is_stopped = False

        def _done(self, sub=None) -> None:
            log.debug("Merge._:done()")
            for task in self._tasks.values():
                task.cancel()
            self._tasks = {}

        async def asend(self, stream: AsyncSource) -> None:
            log.debug("Merge._:send(%s)" % stream)
            inner_sink = await chain(Merge.Sink.Inner(self), self._sink)  # type: AsyncSink
            inner_sub = await chain(stream, inner_sink)
            self._tasks[inner_sink] = asyncio.ensure_future(inner_sub)

        async def aclose(self) -> None:
            log.debug("Merge._:close()")
            if len(self._tasks):
                self._is_stopped = True
                return

            await self._sink.aclose()

        class Inner(AsyncMultiFuture):

            def __init__(self, sink) -> None:
                super().__init__()
                self._parent = sink
                self._tasks = sink._tasks

            async def aclose(self) -> None:
                log.debug("Merge._.__:close()")
                if self in self._tasks:
                    del self._tasks[self]

                # Close when no more inner subscriptions
                if len(self._tasks) or not self._parent._is_stopped:
                    return

                await self._sink.aclose()


def merge(source: AsyncSource) -> AsyncSource:
    """Merges a source stream of source streams.

    Returns flattened source stream.
    """
    return Merge(source)
