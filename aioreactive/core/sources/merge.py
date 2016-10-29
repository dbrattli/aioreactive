from asyncio.locks import BoundedSemaphore
import logging
from typing import Dict, TypeVar

from aioreactive.core import AsyncSingleStream
from aioreactive.core import AsyncSource, AsyncSink, chain

T = TypeVar('T')
log = logging.getLogger(__name__)


class Merge(AsyncSource):

    def __init__(self, source: AsyncSource, max_concurrent: int) -> None:
        self._source = source
        self.max_concurrent = max_concurrent

    async def __astart__(self, sink: AsyncSink) -> AsyncSingleStream:
        log.debug("Merge:__astart__()")
        _sink = await chain(Merge.Stream(self, self.max_concurrent), sink)
        stream = await chain(self._source, _sink)
        stream.add_done_callback(_sink._done)
        return stream

    class Stream(AsyncSingleStream):

        def __init__(self, source: AsyncSource, max_concurrent: int) -> None:
            super().__init__()
            self._streams = {}  # type: Dict[AsyncSink[T], AsyncSingleStream]
            self._is_stopped = False
            self._sem = BoundedSemaphore(max_concurrent)

        def _done(self, sub=None) -> None:
            log.debug("Merge._:done()")
            for stream in self._streams.values():
                if stream is not None:
                    stream.cancel()
            self._streams = {}

        async def asend(self, stream: AsyncSource) -> None:
            log.debug("Merge.Stream:send(%s)" % stream)

            inner_stream = await chain(Merge.Stream.InnerStream(self), self._sink)  # type: AsyncSink
            self._streams[inner_stream] = None

            def done(fut):
                print("DONE!")
                #self._sem.release()
            inner_stream.add_done_callback(done)

            await self._sem.acquire()
            self._streams[inner_stream] = await chain(stream, inner_stream)

        async def aclose(self) -> None:
            log.debug("Merge.Stream:aclose()")
            if len(self._streams):
                self._is_stopped = True
                return

            log.debug("Closing merge ...")
            await super().aclose()

        class InnerStream(AsyncSingleStream):

            def __init__(self, parent) -> None:
                super().__init__()
                self._parent = parent
                self._streams = parent._streams

            async def aclose(self) -> None:
                log.debug("Merge.Stream.InnerStream:aclose()")
                if self in self._streams:
                    del self._streams[self]

                self._parent._sem.release()

                # Close when no more inner streams
                if len(self._streams) or not self._parent._is_stopped:
                    return

                log.debug("Closing merge by inner ...")
                await super().aclose()


def merge(source: AsyncSource, max_concurrent: int=42) -> AsyncSource:
    """Merges a source stream of source streams.

    Keyword arguments:
    source -- source stream to merge.
    max_concurrent -- Max number of streams to process concurrently.
        Default value is 42. Setting this to 1 turns merge into concat.

    Returns flattened source stream.
    """
    return Merge(source, max_concurrent)
