import asyncio
import logging

from aioreactive.core import AsyncSingleStream
from aioreactive.core import AsyncSource, AsyncSink, chain

log = logging.getLogger(__name__)


class SwitchLatest(AsyncSource):

    def __init__(self, source: AsyncSource) -> None:
        self._source = source

    async def __astart__(self, sink: AsyncSink):
        _sink = await chain(SwitchLatest.Sink(self), sink)
        sub = await chain(self._source, _sink)
        sub.add_done_callback(_sink.done)
        return sub

    class Sink(AsyncSingleStream):

        def __init__(self, source: AsyncSource) -> None:
            super().__init__()
            self._task = None  # type: asyncio.Task
            self._is_stopped = False
            self._latest = 0

        def done(self, sub=None) -> None:
            log.debug("SwitchLatest._:done()")
            if self._task:
                self._task.cancel()
                self._task = None
            self.latest = 0

        async def asend(self, stream) -> None:
            log.debug("SwitchLatest._:send(%s)" % stream)
            inner_sink = await chain(SwitchLatest.Sink.Inner(self), self._sink)

            self._latest = id(inner_sink)
            inner_sub = await chain(stream, inner_sink)
            self._task = asyncio.ensure_future(inner_sub)

        async def aclose(self) -> None:
            log.debug("SwitchLatest._:close()")

            if not self._latest:
                self._is_stopped = True
                await self._sink.aclose()

        class Inner(AsyncSingleStream):

            def __init__(self, sink) -> None:
                super().__init__()
                self._parent = sink

            async def asend(self, value) -> None:
                if self._parent._latest == id(self):
                    await self._sink.asend(value)

            async def athrow(self, error: Exception):
                if self._parent._latest == id(self):
                    await self._sink.athrow(error)

            async def aclose(self) -> None:
                if self._parent._latest == id(self):
                    if self._parent._is_stopped:
                        await self._sink.aclose()


def switch_latest(source: AsyncSource) -> AsyncSource:
    """Switch to the latest source stream.

    Flattens a source stream of source streams into a source stream
    that only produces values from the most recent source stream.

    Returns a flattened source stream.
    """
    return SwitchLatest(source)
