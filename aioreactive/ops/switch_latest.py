import asyncio
import logging

from aioreactive.core.futures import AsyncMultiFuture
from aioreactive.abc import AsyncSource, AsyncSink
from aioreactive.core import chain

log = logging.getLogger(__name__)


class SwitchLatest(AsyncSource):
    def __init__(self, source: AsyncSource):
        self._source = source

    async def __alisten__(self, sink: AsyncSink):
        _sink = await chain(SwitchLatest.Sink(self), sink)
        sub = await chain(self._source, _sink)
        sub.add_done_callback(_sink.done)
        return sub

    class Sink(AsyncMultiFuture):
        def __init__(self, source: AsyncSource):
            self._task = None
            self._is_stopped = False
            self._latest = 0

        def done(self, sub=None):
            log.debug("SwitchLatest._:done()")
            if self._task:
                self._task.cancel()
                self._task = None
            self.latest = 0

        async def send(self, stream):
            log.debug("SwitchLatest._:send(%s)" % stream)
            inner_sink = await chain(SwitchLatest.Sink.Inner(self), self._sink)

            self._latest = id(inner_sink)
            inner_sub = chain(stream, inner_sink)
            self._task = asyncio.ensure_future(inner_sub)

        async def close(self):
            log.debug("SwitchLatest._:close()")

            if not self._latest:
                self._is_stopped = True
                await self._sink.close()

        class Inner(AsyncMultiFuture):
            def __init__(self, sink):
                self._parent = sink

            async def send(self, value):
                if self._parent._latest == id(self):
                    await self._sink.send(value)

            async def throw(self, error):
                if self._parent._latest == id(self):
                    await self._sink.throw(error)

            async def close(self):
                if self._parent._latest == id(self):
                    if self._parent._is_stopped:
                        await self._sink.close()


def switch_latest(source: AsyncSource) -> AsyncSource:
    """Switch to the latest source stream.

    Flattens a source stream of source streams into a source stream
    that only produces values from the most recent source stream.

    Returns a flattened source stream.
    """
    return SwitchLatest(source)
