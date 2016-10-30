import asyncio
from asyncio.locks import BoundedSemaphore
from typing import Dict, TypeVar
import logging

from aioreactive.core.utils import noopsink
from aioreactive.core import AsyncSingleStream
from aioreactive.core import AsyncSource, AsyncSink, chain, chain_future

T = TypeVar('T')
log = logging.getLogger(__name__)


class Merge(AsyncSource):

    def __init__(self, source: AsyncSource, max_concurrent: int) -> None:
        self._source = source
        self.max_concurrent = max_concurrent

    async def __astart__(self, sink: AsyncSink) -> AsyncSingleStream:
        log.debug("Merge:__astart__()")
        merge_stream = await chain(Merge.Stream(self, self.max_concurrent), sink)
        stream = await chain(self._source, merge_stream)
        chain_future(stream, merge_stream)
        return stream

    class Stream(AsyncSingleStream):

        def __init__(self, source: AsyncSource, max_concurrent: int) -> None:
            super().__init__()
            self._inner_streams = {}  # type: Dict[AsyncSink[T], AsyncSingleStream]
            self._sem = BoundedSemaphore(max_concurrent)
            self._is_closed = False

        def cancel(self, sub=None) -> None:
            log.debug("Merge.Stream:cancel()")
            super().cancel()

            # Use .values() so that no one modifies the dict while we
            # cancel the inner streams.
            for stream in self._inner_streams.values():
                if stream is not None:
                    stream.cancel()
            self._inner_streams = {}

        async def asend(self, stream: AsyncSource) -> None:
            log.debug("Merge.Stream:send(%s)" % stream)

            inner_stream = await chain(Merge.Stream.InnerStream(), self._sink)  # type: AsyncSink

            # Allocate entry to make sure no-one closes the merge before
            # we get to aquire the semaphore.
            self._inner_streams[inner_stream] = None
            await self._sem.acquire()

            def done(fut):
                self._inner_streams.pop(inner_stream, None)
                self._sem.release()

                if self._is_closed:
                    asyncio.ensure_future(self.aclose())

            inner_stream.add_done_callback(done)
            self._inner_streams[inner_stream] = await chain(stream, inner_stream)

        async def aclose(self) -> None:
            log.debug("Merge.Stream:aclose()")
            if len(self._inner_streams):
                self._is_closed = True
                return

            log.debug("Closing merge ...")
            await super().aclose()

        class InnerStream(AsyncSingleStream):

            async def aclose(self) -> None:
                log.debug("Merge.Stream.InnerStream:aclose()")

                # Unlink sink to avoid forwarding the close. This will
                # make the inner_stream complete, and the done callback
                # will take care of any cleanup.
                self._sink = noopsink
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
