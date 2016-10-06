import asyncio
import logging

from aioreactive.core.futures import AsyncMultiFuture
from aioreactive.abc import AsyncSource, AsyncSink
from aioreactive.core import chain

log = logging.getLogger(__name__)


class Merge(AsyncSource):
    def __init__(self, source: AsyncSource):
        self._source = source

    async def __alisten__(self, sink: AsyncSink):
        _sink = await chain(Merge.Sink(self), sink)
        sub = await chain(self._source, _sink)
        sub.add_done_callback(_sink.done)
        return sub

    class Sink(AsyncMultiFuture):
        def __init__(self, source: AsyncSource):
            super().__init__()
            self._tasks = {}
            self._is_stopped = False

        def done(self, sub=None):
            log.debug("Merge._:done()")
            for task in self._tasks.values():
                task.cancel()
            self._tasks = {}

        async def send(self, stream):
            log.debug("Merge._:send(%s)" % stream)
            inner_sink = await chain(Merge.Sink.Inner(self), self._sink)
            inner_sub = await chain(stream, inner_sink)
            self._tasks[inner_sink] = asyncio.ensure_future(inner_sub)

        async def close(self):
            log.debug("Merge._:close()")
            if len(self._tasks):
                self._is_stopped = True
                return

            await self._sink.close()

        class Inner(AsyncMultiFuture):
            def __init__(self, sink):
                super().__init__()
                self._parent = sink
                self._tasks = sink._tasks

            async def close(self):
                log.debug("Merge._.__:close()")
                if self in self._tasks:
                    del self._tasks[self]

                # Close when no more inner subscriptions
                if len(self._tasks) or not self._parent._is_stopped:
                    return

                await self._sink.close()


def merge(source: AsyncSource) -> AsyncSource:
    """Merges a source stream of source streams.

    Returns flattened source stream.
    """
    return Merge(source)
