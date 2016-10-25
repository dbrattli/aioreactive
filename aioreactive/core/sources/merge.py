import asyncio
import logging
from typing import Dict, TypeVar

from aioreactive.core import AsyncSingleStream
from aioreactive.core import AsyncSource, AsyncSink, chain

T = TypeVar('T')
log = logging.getLogger(__name__)


class Merge(AsyncSource):

    def __init__(self, source: AsyncSource) -> None:
        self._source = source

    async def __astart__(self, sink: AsyncSink) -> AsyncSingleStream:
        log.debug("Merge:__astart__()")
        _sink = await chain(Merge.Stream(self), sink)
        stream = await chain(self._source, _sink)
        stream.add_done_callback(_sink._done)
        return stream

    class Stream(AsyncSingleStream):

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
            log.debug("Merge.Stream:send(%s)" % stream)
            inner_sink = await chain(Merge.Stream.InnerStream(self), self._sink)  # type: AsyncSink
            inner_sub = await chain(stream, inner_sink)
            self._tasks[inner_sink] = asyncio.ensure_future(inner_sub)

        async def aclose(self) -> None:
            log.debug("Merge.Stream:aclose()")
            if len(self._tasks):
                self._is_stopped = True
                return

            log.debug("Closing merge ...")
            await super().aclose()

        class InnerStream(AsyncSingleStream):

            def __init__(self, sink) -> None:
                super().__init__()
                self._parent = sink
                self._tasks = sink._tasks

            async def aclose(self) -> None:
                log.debug("Merge.Stream.InnerStream:aclose()")
                if self in self._tasks:
                    del self._tasks[self]

                # Close when no more inner streams
                if len(self._tasks) or not self._parent._is_stopped:
                    return

                log.debug("Closing merge by inner ...")
                await super().aclose()


def merge(source: AsyncSource) -> AsyncSource:
    """Merges a source stream of source streams.

    Returns flattened source stream.
    """
    return Merge(source)
